export interface ToolDescriptor {name:string; description:string; write:boolean; private:boolean; schema:object}
export interface ToolRun {id:string; tool:string; state:string; result:Record<string,unknown>|null; error:string|null; created_at?:string}
export interface Grant {tool:string; active:number; expires:string}
export interface Project {id:string; name:string; notes:string; status:string; version:number}
export interface Task {id:string; project_id:string; title:string; notes:string; status:string; priority:string; due_at:string|null; version:number; project_name:string}
export interface Source {url:string; title:string; evidence:string; retrieved_at:string; source_type:string}
export interface CalendarResult {configured:boolean; label?:string; timezone?:string; imported_at?:string; age_hours?:number; stale?:boolean; note:string; events:{uid:string;title:string;start:string;end:string;all_day:boolean;busy:boolean}[]; truncated?:boolean}
const base=import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch(`${base}/api/tools${path}`,{...options,credentials:'include',headers:{'Content-Type':'application/json',...options.headers}});
 const body=await response.json();
 if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:body.detail?.message || `Tool request failed (${response.status})`);
 return body;
}
export const toolsApi={
 catalog:()=>request<{tools:ToolDescriptor[]}>(''),
 grants:()=>request<{grants:Grant[]}>('/grants'),
 grant:(tool:string,active:boolean)=>request<Grant>(`/grants/${encodeURIComponent(tool)}`,{method:'PUT',body:JSON.stringify({active})}),
 approve:(tool:string,args:Record<string,unknown>)=>request<{approval_id:string}>('/approvals',{method:'POST',body:JSON.stringify({tool,arguments:args})}),
 run:(tool:string,args:Record<string,unknown>,request_key:string,approval_id?:string)=>request<ToolRun>('/run',{method:'POST',body:JSON.stringify({tool,arguments:args,request_key,approval_id})}),
 runs:()=>request<{runs:ToolRun[]}>('/runs'),
 audit:()=>request<{events:{id:string;tool:string;action:string;detail:string;created_at:string}[]}>('/audit'),
};
