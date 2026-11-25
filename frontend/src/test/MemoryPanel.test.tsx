import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, act } from '@testing-library/react';
import { MemoryPanel } from '../components/memory/MemoryPanel';
import { memoryApi, type MemoryClaim } from '../services/memoryApi';
const fact: MemoryClaim = {id:'fact-one',subject:'Me',predicate:'works_on',value:'TARS',source_id:'source-one',source_kind:'owner_assertion',source_content:'Owner supplied TARS project',created_at:'2026-11-21T00:00:00Z',valid_to:null,verification:'owner_asserted',audiences:['owner'],sensitivity:'private',cloud_allowed:false,state:'active'};
afterEach(()=>{cleanup();vi.restoreAllMocks();});
describe('personal memory controls',()=>{
  it('opens stored facts, exposes provenance and inspects directed relationships',async()=>{
    vi.spyOn(memoryApi,'list').mockResolvedValue({claims:[fact],status:{backend:'sqlite',embedding_model:'lexical-sha256-v1',dimension:128,pending_events:0}});
    vi.spyOn(memoryApi,'graph').mockResolvedValue({nodes:['Me','TARS'],edges:[{source:'Me',relationship:'works_on',target:'TARS',claim_id:'fact-one'}]});
    vi.spyOn(memoryApi,'detail').mockResolvedValue(fact);
    render(<MemoryPanel/>);
    fireEvent.click(screen.getByRole('button',{name:'Personal memory'}));
    await screen.findByText(/source source-one/);
    fireEvent.click(screen.getByRole('button',{name:'View source'}));
    await screen.findByText('Owner supplied TARS project');
    fireEvent.click(screen.getByRole('button',{name:/Relationships/}));
    expect(await screen.findByRole('table')).toHaveTextContent('works_on');
    expect(screen.getByRole('table')).toHaveTextContent('TARS');
    fireEvent.click(screen.getByRole('button',{name:'Focus TARS'}));
    fireEvent.click(screen.getByRole('button',{name:'Zoom in'}));
    expect(screen.getByText(/150%/)).toBeInTheDocument();
    await act(async()=>{fireEvent.click(screen.getByRole('button',{name:'Me → works_on → TARS'}));});
    expect(memoryApi.detail).toHaveBeenCalledWith(fact.id);
  });
});
