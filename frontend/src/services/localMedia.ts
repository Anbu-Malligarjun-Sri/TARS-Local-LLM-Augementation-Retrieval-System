const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function localMedia(path:string, options:RequestInit={}) {
  const response = await fetch(base+'/api/media/'+path,{...options, credentials:'include',cache:'no-store'});
  if (!response.ok) {
    const body=await response.json().catch(()=>({}));
    throw new Error(typeof body.detail==='string'?body.detail:'Local media request failed ('+response.status+').');
  }
  return response;
}

export function mediaJson(body:unknown):RequestInit {
  return {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
}
