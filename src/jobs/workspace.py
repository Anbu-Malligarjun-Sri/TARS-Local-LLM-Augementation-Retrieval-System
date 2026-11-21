"""Filtered independent source snapshots; source repositories are never mutated."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,stat,subprocess,difflib

BLOCKED={'.git','.runtime','.codex','.agents','.aws','.ssh','.venv','venv','node_modules','dist','build','data','__pycache__','datasets questions and answers of tars'}
EXTENSIONS={'.py','.ts','.tsx','.js','.jsx','.json','.toml','.yaml','.yml','.md','.txt','.html','.css','.ini','.cfg','.mjs','.cjs','.rs','.go','.java','.c','.cpp','.h','.cs','.ps1','.sh'}
class JobError(Exception):pass

def safe_relative(value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value or any(ord(c)<32 for c in value):raise JobError('Invalid relative source path')
    path=PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or value.startswith('/') or any(part.endswith((' ','.')) for part in path.parts):raise JobError('Path traversal or ambiguous path denied')
    return path.as_posix()

def allowed(value):
    path=PurePosixPath(value)
    return not any(p.lower() in BLOCKED or p.lower().startswith('.env') for p in path.parts) and path.name.lower() not in {'agents.md','claude.md','.npmrc','.pypirc','auth.json','credentials.json'} and path.suffix.lower() in EXTENSIONS

def no_links(path,root):
    if not path.is_relative_to(root):raise JobError('Path escapes approved root')
    current=root
    for part in path.relative_to(root).parts:
        current=current/part
        info=current.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):raise JobError('Symlinks and reparse points are not allowed')

def digest(data):return hashlib.sha256(data).hexdigest()

def git_env():
    return {**{k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')},'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_TERMINAL_PROMPT':'0'}

def git(root,*args):
    env=git_env()
    result=subprocess.run(['git','-c','core.fsmonitor=false','-C',str(root),*args],capture_output=True,timeout=20,env=env)
    if result.returncode:raise JobError('Git source inspection failed')
    return result.stdout

def snapshot(source,job_dir,selected):
    source=Path(source).resolve();job_dir=Path(job_dir).resolve()
    paths=[safe_relative(p) for p in selected]
    if len(paths)>30:raise JobError('Select at most 30 source paths')
    candidates=git(source,'ls-files','--cached','--others','--exclude-standard','-z').decode('utf-8').split('\0')
    files=[];total=0
    for candidate in sorted(set(candidates)):
        if not candidate:continue
        relative=safe_relative(candidate)
        if not any(relative==p or relative.startswith(p+'/') or p=='.' for p in paths):continue
        if not allowed(relative):continue
        path=source/relative
        if not path.exists():continue
        no_links(path,source)
        if not path.is_file():continue
        size=path.stat().st_size
        if size>400000:raise JobError(f'Source file exceeds 400 KB: {relative}')
        data=path.read_bytes()
        try:data.decode('utf-8-sig')
        except UnicodeDecodeError:continue
        if b'\0' in data:continue
        if b'-----BEGIN PRIVATE KEY-----' in data or b'-----BEGIN RSA PRIVATE KEY-----' in data:raise JobError(f'Private key material excluded: {relative}')
        total+=len(data)
        if total>4000000 or len(files)>=250:raise JobError('Snapshot exceeds 250 files / 4 MB; select a narrower scope')
        for folder in ('workspace','baseline'):
            target=job_dir/folder/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        files.append({'path':relative,'sha256':digest(data),'bytes':len(data)})
    if not files:raise JobError('No eligible source files found')
    manifest={'files':files,'total_bytes':total,'head':git(source,'rev-parse','HEAD').decode().strip(),'dirty':bool(git(source,'status','--porcelain'))}
    encoded=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    (job_dir/'manifest.json').write_bytes(encoded)
    # Independent Git metadata contains only the approved copy, never source objects.
    subprocess.run(['git','-c','core.hooksPath='+os.devnull,'init','--template=','-q',str(job_dir/'workspace')],check=True,capture_output=True,timeout=10,env=git_env())
    return manifest,digest(encoded)

def verify_snapshot(job_dir,manifest):
    workspace=Path(job_dir)/'workspace'
    for item in manifest['files']:
        path=workspace/item['path'];no_links(path,workspace)
        if not path.is_file() or digest(path.read_bytes())!=item['sha256']:raise JobError('Approved snapshot changed; create a new job')
    actual=set()
    for directory,dirs,names in os.walk(workspace,followlinks=False):
        dirs[:]=[d for d in dirs if d!='.git']
        for d in dirs:no_links(Path(directory)/d,workspace)
        for name in names:
            path=Path(directory)/name;no_links(path,workspace);actual.add(path.relative_to(workspace).as_posix())
    if actual!={f['path'] for f in manifest['files']}:raise JobError('Unapproved snapshot files appeared')

def artifacts(job_dir,manifest):
    job_dir=Path(job_dir);workspace=job_dir/'workspace';base=job_dir/'baseline'
    before={item['path'] for item in manifest['files']};after=set()
    for directory,dirs,names in os.walk(workspace,followlinks=False):
        dirs[:]=[d for d in dirs if d not in {'.git','__pycache__','.pytest_cache'}]
        for d in dirs:no_links(Path(directory)/d,workspace)
        for name in names:
            path=Path(directory)/name;no_links(path,workspace)
            relative=path.relative_to(workspace).as_posix()
            if not allowed(relative):raise JobError(f'Agent produced an excluded file: {relative}')
            if path.stat().st_size>400000:raise JobError('Changed file exceeds artifact budget')
            after.add(relative)
    changes=[];patch=[]
    for relative in sorted(before|after):
        original=(base/relative).read_bytes() if relative in before else b''
        current=(workspace/relative).read_bytes() if relative in after else b''
        if original==current:continue
        if b'\0' in current:raise JobError('Binary output is unsupported')
        try:old=original.decode('utf-8-sig');new=current.decode('utf-8-sig')
        except UnicodeDecodeError:raise JobError('Non-UTF8 output is unsupported')
        changes.append({'path':relative,'status':'added' if relative not in before else 'deleted' if relative not in after else 'modified','before_sha256':digest(original),'after_sha256':digest(current)})
        for line in difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+relative if relative in before else '/dev/null',tofile='b/'+relative if relative in after else '/dev/null'):
            patch.append(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n')
    text=''.join(patch)
    if len(changes)>50 or len(text.encode())>1000000:raise JobError('Diff exceeds 50 changed files / 1 MB')
    folder=job_dir/'artifacts';folder.mkdir(exist_ok=True)
    (folder/'changes.patch').write_text(text,encoding='utf-8',newline='\n')
    return {'changed_files':changes,'patch':text}
