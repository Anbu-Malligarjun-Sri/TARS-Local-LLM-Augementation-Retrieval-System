import { describe, it, expect, vi, afterEach } from 'vitest';
import { memoryApi } from '../services/memoryApi';
afterEach(()=>vi.unstubAllGlobals());
describe('memory API boundary',()=>{
  it('sends a correction as authenticated structured data',async()=>{
    const fetch = vi.fn().mockResolvedValue({ok:true,json:async()=>({claim:{id:'new'}})});
    vi.stubGlobal('fetch',fetch);
    const body = {subject:'Me',predicate:'works_on',value:'TARS',audiences:['owner' as const],sensitivity:'private' as const,cloud_allowed:false,valid_to:null};
    await memoryApi.correct('old',body);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/memory/old'),expect.objectContaining({method:'PUT',credentials:'include',body:JSON.stringify(body)}));
  });
  it('surfaces permission failures without reporting a successful forget',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:401,json:async()=>({detail:'Pair device first'})}));
    await expect(memoryApi.forget('private')).rejects.toThrow('Pair device first');
  });
});
