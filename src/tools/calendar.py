"""Read-only ICS snapshots; no caller-controlled filesystem/remote URL reads."""
from datetime import date,datetime,time,timedelta,timezone
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
import hashlib
from icalendar import Calendar
import recurring_ical_events
from pydantic import Field,field_validator
from src.memory.repository import now
from .gateway import Arguments,Tool,ToolError

class CalendarImport(Arguments):
    label:str=Field(default='Personal calendar',min_length=1,max_length=100)
    content:str=Field(min_length=30,max_length=45000)
    timezone:str=Field(default='Asia/Calcutta',max_length=100)
    @field_validator('timezone')
    @classmethod
    def zone(cls,value):
        try:ZoneInfo(value)
        except (ZoneInfoNotFoundError,ValueError):raise ValueError('Unknown IANA timezone')
        return value
class CalendarRead(Arguments):
    start:str|None=None
    days:int=Field(default=7,ge=1,le=31)

class LocalCalendar:
    def __init__(self,repository):
        self.repository=repository
        with repository.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS calendar_snapshots (owner TEXT PRIMARY KEY,label TEXT NOT NULL,content TEXT NOT NULL,digest TEXT NOT NULL,imported_at TEXT NOT NULL,timezone TEXT NOT NULL)')
    @staticmethod
    def parse(content):
        if len(content.encode('utf-8'))>45000 or not content.lstrip().startswith('BEGIN:VCALENDAR'):
            raise ToolError('calendar_invalid','Use an ICS snapshot no larger than 45 KB')
        try:
            calendar=Calendar.from_ical(content)
            if len(list(calendar.walk()))>350:raise ValueError('Too many components')
            for event in calendar.walk('VEVENT'):
                if event.errors:raise ValueError('Calendar contains parsing errors')
                if not event.get('UID') or not event.get('DTSTART'):raise ValueError('Events require UID and DTSTART')
                for field in ('DTSTART','DTEND','RECURRENCE-ID'):
                    prop=event.get(field)
                    if prop and prop.params.get('TZID') and isinstance(prop.dt,datetime) and prop.dt.tzinfo is None:
                        raise ValueError('Unresolved event timezone')
                rules=event.get('RRULE')
                if rules:
                    if str(rules.get('FREQ',[''])[0]) not in {'DAILY','WEEKLY','MONTHLY','YEARLY'}:raise ValueError('Only daily or slower recurrence is supported')
                    for field,maximum in [('BYSECOND',1),('BYMINUTE',1),('BYHOUR',2),('BYDAY',7),('BYMONTHDAY',31),('BYMONTH',12),('BYSETPOS',7)]:
                        if len(rules.get(field,[]))>maximum:raise ValueError('Recurrence is too dense')
                    if int(rules.get('INTERVAL',[1])[0])<1:raise ValueError('Invalid recurrence interval')
                    if int(rules.get('COUNT',[1])[0])>10000:raise ValueError('Recurrence count exceeds budget')
                if event.get('EXRULE'):raise ValueError('EXRULE unsupported; use EXDATE')
            return calendar
        except ToolError:raise
        except Exception as exc:raise ToolError('calendar_invalid',str(exc)[:250]) from exc
    def import_snapshot(self,args,owner,db):
        self.parse(args.content)
        digest=hashlib.sha256(args.content.encode()).hexdigest();timestamp=now()
        db.execute('INSERT INTO calendar_snapshots VALUES (?,?,?,?,?,?) ON CONFLICT(owner) DO UPDATE SET label=excluded.label,content=excluded.content,digest=excluded.digest,imported_at=excluded.imported_at,timezone=excluded.timezone',(owner,args.label,args.content,digest,timestamp,args.timezone))
        return {'label':args.label,'digest':digest,'imported_at':timestamp,'timezone':args.timezone,'read_only':True,'source':'local_ics_snapshot'}
    def read(self,args,owner,db):
        with self.repository.transaction() as connection:
            row=connection.execute('SELECT * FROM calendar_snapshots WHERE owner=?',(owner,)).fetchone()
        if not row:return {'configured':False,'events':[],'note':'Import a local ICS snapshot in Tools first; availability is unknown.'}
        zone=ZoneInfo(row['timezone'])
        try:start_date=date.fromisoformat(args.start) if args.start else datetime.now(zone).date()
        except ValueError:raise ToolError('calendar_range','Start must be YYYY-MM-DD')
        start=datetime.combine(start_date,time.min,tzinfo=zone);end=start+timedelta(days=args.days)
        calendar=self.parse(row['content']);calendar['X-WR-TIMEZONE']=row['timezone']
        for event in calendar.walk('VEVENT'):
            if event.get('RRULE'):
                freq=str(event['RRULE'].get('FREQ',[''])[0])
                first=event['DTSTART'].dt
                year=first.year
                if (freq in {'DAILY','WEEKLY'} and year<start.year-10) or (freq=='MONTHLY' and year<start.year-100):
                    raise ToolError('calendar_range','This recurrence starts too far in the past; export a bounded calendar snapshot')
        try:instances=recurring_ical_events.of(calendar).between(start,end)
        except Exception as exc:raise ToolError('calendar_invalid','Could not expand recurrence') from exc
        events=[]
        def aware(value):
            if isinstance(value,datetime):return value.replace(tzinfo=zone) if value.tzinfo is None else value
            return datetime.combine(value,time.min,tzinfo=zone)
        for event in instances:
            if str(event.get('STATUS','')).upper()=='CANCELLED':continue
            first=event['DTSTART'].dt
            last=event['DTEND'].dt if event.get('DTEND') else first+(event.get('DURATION').dt if event.get('DURATION') else (timedelta(0) if isinstance(first,datetime) else timedelta(days=1)))
            if aware(first)>=end or (aware(last)<=start and aware(first)<start):continue
            events.append({'uid':str(event['UID'])[:200],'title':str(event.get('SUMMARY','Busy'))[:300],'start':aware(first).astimezone(zone).isoformat(),'end':aware(last).astimezone(zone).isoformat(),'all_day':not isinstance(first,datetime),'busy':str(event.get('TRANSP','OPAQUE')).upper()!='TRANSPARENT'})
        events.sort(key=lambda event:event['start'])
        age=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(row['imported_at'])).total_seconds())
        return {'configured':True,'source':'local_ics_snapshot','label':row['label'],'imported_at':row['imported_at'],'age_hours':round(age/3600,2),'stale':age>86400,'timezone':row['timezone'],'range_start':start.isoformat(),'range_end':end.isoformat(),'events':events[:200],'truncated':len(events)>200,'read_only':True,'note':'Snapshot only: events may have changed since export. Empty results do not prove availability.'}
    def tools(self):
        return [Tool('calendar.read','Read a bounded owner ICS calendar snapshot',CalendarRead,False,True,self.read),Tool('calendar.import','Replace the local ICS snapshot (never edits source calendar)',CalendarImport,True,True,self.import_snapshot)]
