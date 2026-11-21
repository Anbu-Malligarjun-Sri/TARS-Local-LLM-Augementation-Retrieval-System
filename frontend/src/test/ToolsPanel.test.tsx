import { describe,it,expect,vi,afterEach } from 'vitest';
import { render,screen,fireEvent,cleanup } from '@testing-library/react';
import { ToolsPanel } from '../components/tools/ToolsPanel';
import { toolsApi } from '../services/toolsApi';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
describe('tool review boundary',()=>{
 it('does not mutate a project until the exact reviewed action is approved',async()=>{
  vi.spyOn(toolsApi,'grants').mockResolvedValue({grants:[]});
  vi.spyOn(toolsApi,'runs').mockResolvedValue({runs:[]});
  const approve=vi.spyOn(toolsApi,'approve').mockResolvedValue({approval_id:'approval-one'});
  const calls=vi.spyOn(toolsApi,'run').mockImplementation(async(tool)=>({id:'run-one',tool,state:'completed',error:null,result:tool==='projects.list'?{projects:[]}:tool==='tasks.list'?{tasks:[]}:{id:'project-one',name:'TARS'}}));
  render(<ToolsPanel/>);
  fireEvent.click(screen.getByRole('button',{name:'Tools & projects'}));
  await screen.findByText('No active projects yet.');
  fireEvent.change(screen.getByLabelText('Project name'),{target:{value:'TARS'}});
  fireEvent.change(screen.getByLabelText('Project notes'),{target:{value:'Personal intelligence'}});
  fireEvent.click(screen.getByRole('button',{name:'Review project'}));
  expect(screen.getByText('Review action: projects.create')).toBeInTheDocument();
  expect(approve).not.toHaveBeenCalled();
  expect(calls.mock.calls.filter(call=>call[0]==='projects.create')).toHaveLength(0);
  fireEvent.click(screen.getByRole('button',{name:'Approve and run'}));
  await screen.findByText('Action completed.');
  expect(approve).toHaveBeenCalledWith('projects.create',{name:'TARS',notes:'Personal intelligence'});
  expect(calls.mock.calls.filter(call=>call[0]==='projects.create')).toHaveLength(1);
 });
});
