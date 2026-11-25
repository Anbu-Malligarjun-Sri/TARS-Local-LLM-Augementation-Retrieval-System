import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from 'lucide-react';
import { useTarsStore } from '@/store/tarsStore';
import { TerminalMessage } from './TerminalMessage';
import { CommandInput } from './CommandInput';

export function ChatTerminal() {
  const { messages, status } = useTarsStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const follow = useRef(true);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const pane = scrollRef.current;
    if (pane && follow.current) pane.scrollTop = pane.scrollHeight;
  }, [messages, status]);

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Terminal Header - Fixed */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-border bg-tars-dark/50">
        <div className="flex items-center gap-3">
          <Terminal className="w-4 h-4 text-tars-amber" />
          <span className="font-terminal text-xs uppercase tracking-widest text-muted-foreground">
            TARS INTERFACE v2.0
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-terminal text-[10px] text-muted-foreground/50">
            SESSION: {new Date().toISOString().split('T')[0]}
          </span>
        </div>
      </div>
      
      {/* Messages Area - Scrollable */}
      <div 
        ref={scrollRef}
        onScroll={({currentTarget: pane}) => { follow.current = pane.scrollHeight - pane.clientHeight - pane.scrollTop < 80; }}
        className="flex-1 overscroll-contain overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent min-h-0"
      >
        {messages.length === 0 ? (
          <WelcomeScreen />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <TerminalMessage key={message.id} message={message} />
            ))}
          </AnimatePresence>
        )}
        
        {/* Thinking indicator */}
        {status === 'thinking' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="font-terminal text-sm text-muted-foreground flex items-center gap-2"
          >
            <span>[{new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}]</span>
            <span className="text-tars-amber uppercase text-[10px] tracking-wider">TARS</span>
            <motion.span
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, repeat: Infinity }}
              className="text-tars-amber"
            >
              Processing query...
            </motion.span>
          </motion.div>
        )}
        
        
      </div>
      
      {/* Input Area - Fixed at bottom */}
      <div className="flex-shrink-0 p-4 border-t border-border bg-tars-dark/30">
        <CommandInput />
      </div>
    </div>
  );
}

function WelcomeScreen() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center py-12">
      {/* TARS ASCII Art */}
      <pre className="font-terminal text-[10px] leading-tight text-tars-amber/60 mb-8">
{`
╔═══════════════════════════════════════════╗
║                                           ║
║     ████████╗ █████╗ ██████╗ ███████╗     ║
║     ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝     ║
║        ██║   ███████║██████╔╝███████╗     ║
║        ██║   ██╔══██║██╔══██╗╚════██║     ║
║        ██║   ██║  ██║██║  ██║███████║     ║
║        ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝     ║
║                                           ║
║         TACTICAL ASSISTANT ROBOT          ║
║              SYSTEM v2.0                  ║
║                                           ║
╚═══════════════════════════════════════════╝
`}
      </pre>
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="space-y-4 max-w-md"
      >
        <p className="font-terminal text-sm text-muted-foreground">
          Connection established. All systems nominal.
        </p>
        <p className="font-terminal text-xs text-muted-foreground/60">
          Adjust personality parameters using the control panel.
          <br />
          Type a command or enable voice mode to begin.
        </p>
      </motion.div>
      

    </div>
  );
}
