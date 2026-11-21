import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Mic, MicOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTarsStore } from '@/store/tarsStore';
import { useTarsChat } from '@/hooks/useTarsChat';
import { VoiceVisualizer } from '@/components/ui/VoiceVisualizer';

export function CommandInput() {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const { isVoiceMode, toggleVoiceMode, setStatus, status } = useTarsStore();
  const { sendMessage, cancelTurn } = useTarsChat();
  
  const isListening = status === 'listening';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    // Send message via real API
    sendMessage(input.trim());
    setInput('');
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      setStatus('idle');
    } else {
      setStatus('listening');
    }
    toggleVoiceMode();
  };

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className="relative">
      {/* Voice Visualizer */}
      {isVoiceMode && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="mb-4 flex justify-center"
        >
          <VoiceVisualizer isActive={isListening} />
        </motion.div>
      )}
      
      {/* Input Container */}
      <form onSubmit={handleSubmit} className="relative">
        <div className={cn(
          "flex items-center gap-2 p-3",
          "bg-tars-dark border border-border rounded",
          "focus-within:border-tars-amber/50 focus-within:shadow-[0_0_20px_rgba(255,157,0,0.1)]",
          "transition-all duration-200"
        )}>
          {/* Prompt Symbol */}
          <span className="font-terminal text-tars-amber text-sm select-none">
            {'>'}
          </span>
          
          {/* Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isVoiceMode ? "Voice mode active..." : "Enter command..."}
            disabled={isVoiceMode}
            className={cn(
              "flex-1 bg-transparent border-none outline-none",
              "font-terminal text-sm text-tars-light placeholder:text-muted-foreground/50",
              isVoiceMode && "opacity-50"
            )}
          />
          
          {/* Cursor */}
          {!input && !isVoiceMode && (
            <motion.span
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.6, repeat: Infinity }}
              className="w-2 h-4 bg-tars-amber"
            />
          )}
          
          {/* Voice Toggle */}
          <button
            type="button"
            disabled
            title="Browser voice is planned for Phase 5"
            onClick={handleVoiceToggle}
            className={cn(
              "p-2 rounded transition-all duration-200 mechanical-click",
              isVoiceMode 
                ? "bg-tars-amber/20 text-tars-amber" 
                : "hover:bg-tars-silver text-muted-foreground hover:text-tars-light"
            )}
          >
            {isVoiceMode ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
          </button>
          
          {/* Send Button */}
          <button
            type="submit"
            disabled={!input.trim() || isVoiceMode}
            className={cn(
              "p-2 rounded transition-all duration-200 mechanical-click",
              input.trim() && !isVoiceMode
                ? "bg-tars-amber text-tars-black hover:bg-tars-amber/90"
                : "bg-tars-silver text-muted-foreground cursor-not-allowed"
            )}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        
        {status !== 'idle' && <button type="button" onClick={cancelTurn}>Stop response</button>}
      {/* Input hint */}
        <div className="flex justify-between mt-2 px-1">
          <span className="font-terminal text-[10px] text-muted-foreground/50">
            PRESS ENTER TO TRANSMIT
          </span>
          <span className="font-terminal text-[10px] text-muted-foreground/50">
            {input.length}/500
          </span>
        </div>
      </form>
    </div>
  );
}
