"""Public HTTPS text access with DNS pinning and bounded extraction."""
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin,urlunsplit,quote
import http.client
import ipaddress
import socket
import ssl
import time
from defusedxml import ElementTree
from pydantic import Field
from src.memory.repository import now
from .gateway import Arguments,Tool,ToolError

MAX_BYTES=600000

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.title=[];self.hidden=0;self.in_title=False
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style','noscript','svg','nav','footer'}:self.hidden+=1
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag in {'script','style','noscript','svg','nav','footer'}:self.hidden=max(0,self.hidden-1)
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title.append(data)
        if not self.hidden and data.strip():self.parts.append(data.strip())

@dataclass
class WebResponse:
    url:str
    content:bytes
    content_type:str
    retrieved_at:str

class PublicWeb:
    def __init__(self,resolver=socket.getaddrinfo,connector=None):
        self.resolver=resolver
        self.connector=connector or self._connection

    def validate(self,url):
        if len(url)>4000 or any(ord(c)<32 for c in url):raise ToolError('url_denied','Invalid URL')
        parts=urlsplit(url)
        try:port=parts.port
        except ValueError:raise ToolError('url_denied','Invalid URL port')
        if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or port not in {None,443}:
            raise ToolError('url_denied','Use public HTTPS URLs without credentials or custom ports')
        host=parts.hostname.encode('idna').decode('ascii').lower().rstrip('.')
        if host in {'localhost'} or host.endswith(('.local','.localhost','.internal')):
            raise ToolError('url_denied','Private hosts are not allowed')
        try:addresses=sorted({item[4][0] for item in self.resolver(host,443,type=socket.SOCK_STREAM)})
        except OSError:raise ToolError('dns_failed','Could not resolve the public source')
        def allowed(ip):
            address=ipaddress.ip_address(ip)
            if not address.is_global:return False
            if address.version==6 and (address.ipv4_mapped or address.sixtofour or address.teredo or address in ipaddress.ip_network('64:ff9b::/96')):return False
            return True
        if not addresses or any(not allowed(ip) for ip in addresses):
            raise ToolError('url_denied','Private, reserved or mixed DNS addresses are blocked')
        return parts,host,addresses[0]

    @staticmethod
    def _connection(host,ip,timeout):
        class PinnedHTTPS(http.client.HTTPSConnection):
            def connect(self):
                self.sock=socket.create_connection((ip,443),timeout=self.timeout)
                self.sock=self._context.wrap_socket(self.sock,server_hostname=host)
        return PinnedHTTPS(host,443,timeout=timeout,context=ssl.create_default_context())

    def fetch(self,url):
        deadline=time.monotonic()+12
        for _ in range(4):
            parts,host,ip=self.validate(url)
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ToolError('fetch_timeout','Source request exceeded its deadline')
            connection=self.connector(host,ip,min(6,remaining))
            try:
                path=urlunsplit(('', '', parts.path or '/',parts.query,''))
                connection.request('GET',path,headers={'User-Agent':'TARS-Personal-Assistant/1.0','Accept':'text/html,text/plain,application/rss+xml,application/xml','Accept-Encoding':'identity','Host':host})
                response=connection.getresponse()
                if response.status in {301,302,303,307,308}:
                    location=response.getheader('Location')
                    if not location:raise ToolError('fetch_failed','Source redirect has no destination')
                    url=urljoin(url,location)
                    continue
                if response.status!=200:raise ToolError('fetch_failed',f'Source returned HTTP {response.status}')
                content_type=(response.getheader('Content-Type') or '').lower().split(';')[0]
                if content_type not in {'text/html','text/plain','application/rss+xml','application/xml','text/xml','application/xhtml+xml'}:
                    raise ToolError('content_denied','Only text, HTML and XML sources are supported')
                if response.getheader('Content-Encoding') not in {None,'identity'}:
                    raise ToolError('content_denied','Compressed source responses are unsupported')
                chunks=[];size=0
                while True:
                    if time.monotonic()>deadline:raise ToolError('fetch_timeout','Source deadline exceeded')
                    chunk=response.read1(min(16384,MAX_BYTES-size+1))
                    if not chunk:break
                    size+=len(chunk)
                    if size>MAX_BYTES:raise ToolError('content_limit','Source is too large')
                    chunks.append(chunk)
                return WebResponse(url,b''.join(chunks),content_type,now())
            except (OSError,http.client.HTTPException) as exc:
                raise ToolError('fetch_failed','Could not securely retrieve source') from exc
            finally:connection.close()
        raise ToolError('redirect_limit','Too many source redirects')

    def page(self,url):
        response=self.fetch(url)
        parser=TextParser()
        text=response.content.decode('utf-8',errors='replace')
        if 'html' in response.content_type:
            parser.feed(text)
            text=' '.join(parser.parts)
        return {'url':response.url,'title':' '.join(parser.title)[:300] or response.url,'retrieved_at':response.retrieved_at,
                'evidence':text[:14000],'truncated':len(text)>14000,'source_type':'public_web','trust':'untrusted_reference'}

    def search(self,query):
        # Public RSS search is key-free but upstream availability is not guaranteed.
        response=self.fetch('https://www.bing.com/search?format=rss&q='+quote(query))
        try:root=ElementTree.fromstring(response.content)
        except Exception as exc:raise ToolError('search_unavailable','Search provider did not return a usable feed; try a direct URL') from exc
        results=[]
        for item in root.findall('.//item')[:5]:
            url=item.findtext('link','')
            try:self.validate(url)
            except ToolError:continue
            results.append({'url':url,'title':item.findtext('title','')[:300],
                            'evidence':item.findtext('description','')[:1600],
                            'retrieved_at':response.retrieved_at,'published_at':item.findtext('pubDate'),'source_type':'search_snippet','trust':'untrusted_reference'})
        if not results:raise ToolError('search_unavailable','No usable search results; try fetching a direct public URL')
        return {'query':query,'provider':'bing_public_rss','sources':results,'note':'Search snippets are leads, not verified page contents.'}

class SearchArgs(Arguments):
    query:str=Field(min_length=2,max_length=500)
class FetchArgs(Arguments):
    url:str=Field(min_length=10,max_length=4000)

def web_tools(web):
    return [Tool('web.search','Search the public web; sends only your explicit query',SearchArgs,False,False,lambda args,owner,db:web.search(args.query)),
            Tool('web.fetch','Read a public HTTPS page as untrusted source material',FetchArgs,False,False,lambda args,owner,db:{'sources':[web.page(args.url)]})]
