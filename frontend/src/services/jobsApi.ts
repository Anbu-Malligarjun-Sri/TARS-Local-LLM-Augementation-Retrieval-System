export interface CodingSpec {repository:string;objective:string;paths:string[];checks:string[];timeout_seconds:number;token_budget:number;adapter?:string;provider?:string}
export interface CodingJob {id:string;state:string;spec:CodingSpec;manifest:{files:{path:string;sha256:string;bytes:number}[];head:string;dirty:boolean;total_bytes:number};approval_digest:string;error:string|null;cancel_requested:number;heartbeat:string|null;created_at:string;result:{changed_files?:{path:string;status:string}[];patch?:string;checks?:{profile:string;exit_code:number;output:string;seconds?:number}[];checks_passed?:boolean|null;agent?:{exit_code:number;usage?:Record<string,number>;model?:string};sandbox?:{available:boolean;evidence:string};limitations?:string[]}|null}
export interface CodingCapabilities {adapter:string;cloud_enabled:boolean;codex_installed:boolean;repositories:{id:string;label:string}[];checks:string[];note:string}
const base=import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
async function request<T>(path:string,options:RequestInit={}):Promise<T>{const response=await fetch(`${base}/api/jobs${path}`,{...options,credentials:'include',headers:{'Content-Type':'application/json',...options.headers}});const body=await response.json();if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:body.detail?.message || `Job request failed (${response.status})`);return body;}
export const jobsApi={
 capabilities:()=>request<CodingCapabilities>('/capabilities'),list:()=>request<{jobs:CodingJob[]}>(''),
 create:(spec:CodingSpec,request_key:string)=>request<CodingJob>('',{method:'POST',body:JSON.stringify({...spec,request_key})}),
 get:(id:string)=>request<CodingJob>(`/${id}`),
 approve:(job:CodingJob)=>request<CodingJob>(`/${job.id}/approve`,{method:'POST',body:JSON.stringify({approval_digest:job.approval_digest})}),
 cancel:(id:string)=>request<CodingJob>(`/${id}/cancel`,{method:'POST'}),
 source:(id:string,path:string)=>request<{content:string}>(`/${id}/source?path=${encodeURIComponent(path)}`),
 preflight:()=>request<{available:boolean;evidence:string}>('/preflight',{method:'POST'}),
};
