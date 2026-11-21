export interface MemoryClaim {
  id: string; subject: string; predicate: string; value: string;
  source_id: string; source_kind?: string; source_content?: string;
  created_at: string; valid_to: string | null; verification: string;
  audiences: ('owner' | 'family' | 'friend' | 'professional')[];
  sensitivity: 'private' | 'shared'; cloud_allowed: boolean; state: string;
}
export type ClaimInput = Pick<MemoryClaim, 'subject' | 'predicate' | 'value' | 'audiences' | 'sensitivity' | 'cloud_allowed' | 'valid_to'>;
export interface MemoryStatus { backend: string; embedding_model: string; dimension: number; pending_events: number }
export interface MemoryGraph { nodes: string[]; edges: {source: string; relationship: string; target: string; claim_id: string}[] }
const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}/api/memory${path}`, { ...options, credentials: 'include', headers: {'Content-Type': 'application/json', ...options.headers} });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Memory request failed (${response.status})`);
  }
  return response.json();
}
export const memoryApi = {
  list: () => request<{claims: MemoryClaim[]; status: MemoryStatus}>(''),
  graph: () => request<MemoryGraph>('/graph'),
  detail: (id: string) => request<MemoryClaim>(`/${id}`),
  search: (query: string) => request<{claims: MemoryClaim[]}>(`/search?query=${encodeURIComponent(query)}`),
  add: (claim: ClaimInput) => request<{claim: MemoryClaim}>('', {method: 'POST', body: JSON.stringify(claim)}),
  correct: (id: string, claim: ClaimInput) => request<{claim: MemoryClaim}>(`/${id}`, {method: 'PUT', body: JSON.stringify(claim)}),
  forget: (id: string) => request<{retention_note: string}>(`/${id}`, {method: 'DELETE'}),
  export: () => request<object>('/export'),
  rebuild: () => request<MemoryStatus>('/rebuild', {method: 'POST'}),
};
