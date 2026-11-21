"""Finite subprocess execution with cancellation and Windows job-tree cleanup."""
import ctypes,os,subprocess,threading,queue,time
from ctypes import wintypes
from .workspace import JobError

class ProcessLimit(JobError):pass

class ProcessTree:
    def __init__(self,process):
        self.process=process;self.handle=None
        if os.name=='nt':
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.CreateJobObjectW.restype=wintypes.HANDLE
            kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
            kernel.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
            kernel.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
            kernel.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
            kernel.CloseHandle.argtypes=[wintypes.HANDLE]
            class Basic(ctypes.Structure):
                _fields_=[('a',ctypes.c_int64),('b',ctypes.c_int64),('flags',wintypes.DWORD),('min',ctypes.c_size_t),('max',ctypes.c_size_t),('active',wintypes.DWORD),('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
            class IO(ctypes.Structure):_fields_=[(name,ctypes.c_uint64) for name in ['r','w','o','rb','wb','ob']]
            class Extended(ctypes.Structure):_fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
            self.kernel=kernel;self.handle=kernel.CreateJobObjectW(None,None)
            info=Extended();info.basic.flags=0x2000
            if not self.handle or not kernel.SetInformationJobObject(self.handle,9,ctypes.byref(info),ctypes.sizeof(info)) or not kernel.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(process._handle))):
                process.kill()
                if self.handle:kernel.CloseHandle(self.handle)
                raise ProcessLimit('Cannot establish bounded process-tree lifetime')
    def close(self):
        if self.handle:
            self.kernel.TerminateJobObject(self.handle,1);self.kernel.CloseHandle(self.handle);self.handle=None
        elif self.process.poll() is None:
            if os.name!='nt':
                import signal
                os.killpg(self.process.pid,signal.SIGKILL)
            else:self.process.kill()


def bounded(argv,cwd,env,timeout,cancel=lambda:None,input_text='',on_line=None,max_output=2000000):
    flags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    process=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=flags,start_new_session=os.name!='nt')
    tree=ProcessTree(process);chunks=queue.Queue(maxsize=128);stop=threading.Event()
    def reader():
        try:
            while not stop.is_set():
                data=process.stdout.read1(4096)
                if not data:break
                while not stop.is_set():
                    try:chunks.put(data,timeout=.1);break
                    except queue.Full:continue
        finally:
            try:chunks.put_nowait(None)
            except queue.Full:pass
    def writer():
        try:process.stdin.write(input_text.encode('utf-8'));process.stdin.close()
        except (OSError,BrokenPipeError):pass
    threading.Thread(target=reader,daemon=True).start();threading.Thread(target=writer,daemon=True).start()
    start=time.monotonic();output=bytearray();pending=b'';done=False
    try:
        while True:
            reason=cancel()
            if reason:raise ProcessLimit(reason)
            if time.monotonic()-start>timeout:raise ProcessLimit('deadline_exceeded')
            try:data=chunks.get(timeout=.15)
            except queue.Empty:
                if process.poll() is not None and not chunks.qsize():break
                continue
            if data is None:done=True
            else:
                output.extend(data);pending+=data
                if len(output)>max_output:raise ProcessLimit('output_budget_exceeded')
                while b'\n' in pending:
                    line,pending=pending.split(b'\n',1)
                    if on_line:on_line(line.decode('utf-8',errors='replace'))
            if done and process.poll() is not None:break
        if pending and on_line:on_line(pending.decode('utf-8',errors='replace'))
        return {'exit_code':process.wait(timeout=3),'output':output.decode('utf-8',errors='replace'),'seconds':round(time.monotonic()-start,2)}
    finally:
        stop.set();tree.close()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill()
