import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Terminal, 
  Settings, 
  History, 
  Plus, 
  Download,
  Volume2,
  VolumeX,
  Mic,
  Trash2,
  Smile,
  Shield,
  Zap,
  Moon,
  Command
} from 'lucide-react';
import { useTarsStore } from '@/store/tarsStore';
import { cn } from '@/lib/utils';

interface CommandItem {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  category: 'session' | 'settings' | 'audio' | 'preset';
  shortcut?: string;
}

export function CommandPalette() {
  const { 
    isCommandPaletteOpen, 
    setCommandPaletteOpen,
    toggleHistory,
    createNewSession,
    clearMessages,
    toggleMute,
    isMuted,
    toggleVoiceMode,
    isVoiceMode,
    applyPreset,
    exportCurrentChat
  } = useTarsStore();
  
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const commands: CommandItem[] = useMemo(() => [
    // Session commands
    {
      id: 'new-session',
      label: 'New Session',
      description: 'Start a fresh conversation',
      icon: <Plus className="w-4 h-4" />,
      action: () => { createNewSession(); setCommandPaletteOpen(false); },
      category: 'session',
      shortcut: '⌘N'
    },
    {
      id: 'view-history',
      label: 'View History',
      description: 'Browse past conversations',
      icon: <History className="w-4 h-4" />,
      action: () => { toggleHistory(); setCommandPaletteOpen(false); },
      category: 'session',
      shortcut: '⌘H'
    },
    {
      id: 'clear-chat',
      label: 'Clear Chat',
      description: 'Clear current conversation',
      icon: <Trash2 className="w-4 h-4" />,
      action: () => { clearMessages(); setCommandPaletteOpen(false); },
      category: 'session',
    },
    {
      id: 'export-chat',
      label: 'Export Chat',
      description: 'Download current conversation',
      icon: <Download className="w-4 h-4" />,
      action: () => {
        const data = exportCurrentChat();
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tars-chat-export.json';
        a.click();
        URL.revokeObjectURL(url);
        setCommandPaletteOpen(false);
      },
      category: 'session',
    },
    
    // Audio commands
    {
      id: 'toggle-mute',
      label: isMuted ? 'Unmute Audio' : 'Mute Audio',
      description: 'Toggle audio output',
      icon: isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />,
      action: () => { toggleMute(); setCommandPaletteOpen(false); },
      category: 'audio',
      shortcut: '⌘M'
    },
    {
      id: 'toggle-voice',
      label: isVoiceMode ? 'Close Voice Settings' : 'Open Voice Settings',
      description: 'Review speech consent and language; microphone starts separately',
      icon: <Mic className="w-4 h-4" />,
      action: () => { toggleVoiceMode(); setCommandPaletteOpen(false); },
      category: 'audio',
    },
    
    // Presets
    {
      id: 'preset-cooper',
      label: 'Preset: Cooper',
      description: 'Balanced personality - Humor 75%, Honesty 90%',
      icon: <Smile className="w-4 h-4" />,
      action: () => { applyPreset('cooper'); setCommandPaletteOpen(false); },
      category: 'preset',
    },
    {
      id: 'preset-mission',
      label: 'Preset: Mission Critical',
      description: 'Serious mode - Low humor, max honesty',
      icon: <Shield className="w-4 h-4" />,
      action: () => { applyPreset('mission'); setCommandPaletteOpen(false); },
      category: 'preset',
    },
    {
      id: 'preset-analyst',
      label: 'Preset: Analyst',
      description: 'Detailed, thorough responses',
      icon: <Terminal className="w-4 h-4" />,
      action: () => { applyPreset('analyst'); setCommandPaletteOpen(false); },
      category: 'preset',
    },
    {
      id: 'preset-creative',
      label: 'Preset: Creative',
      description: 'Playful, imaginative responses',
      icon: <Zap className="w-4 h-4" />,
      action: () => { applyPreset('creative'); setCommandPaletteOpen(false); },
      category: 'preset',
    },
  ], [isMuted, isVoiceMode, createNewSession, toggleHistory, clearMessages, toggleMute, toggleVoiceMode, applyPreset, exportCurrentChat, setCommandPaletteOpen]);

  const filteredCommands = useMemo(() => {
    if (!search) return commands;
    const searchLower = search.toLowerCase();
    return commands.filter(
      cmd => 
        cmd.label.toLowerCase().includes(searchLower) ||
        cmd.description.toLowerCase().includes(searchLower)
    );
  }, [commands, search]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isCommandPaletteOpen) {
        // Open with Cmd/Ctrl + K
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
          e.preventDefault();
          setCommandPaletteOpen(true);
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(i => (i + 1) % filteredCommands.length);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(i => (i - 1 + filteredCommands.length) % filteredCommands.length);
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            filteredCommands[selectedIndex].action();
          }
          break;
        case 'Escape':
          e.preventDefault();
          setCommandPaletteOpen(false);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, filteredCommands, selectedIndex, setCommandPaletteOpen]);

  // Reset on open
  useEffect(() => {
    if (isCommandPaletteOpen) {
      setSearch('');
      setSelectedIndex(0);
    }
  }, [isCommandPaletteOpen]);

  return (
    <AnimatePresence>
      {isCommandPaletteOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setCommandPaletteOpen(false)}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
          />
          
          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
              "fixed left-1/2 top-[20%] -translate-x-1/2 z-50",
              "w-full max-w-lg",
              "bg-tars-dark border border-border rounded-lg",
              "shadow-2xl shadow-black/50 overflow-hidden"
            )}
          >
            {/* Search Input */}
            <div className="flex items-center gap-3 p-4 border-b border-border">
              <Search className="w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setSelectedIndex(0); }}
                placeholder="Search commands..."
                className="flex-1 bg-transparent font-terminal text-sm text-tars-light placeholder:text-muted-foreground/50 focus:outline-none"
                autoFocus
              />
              <div className="flex items-center gap-1 px-2 py-1 rounded bg-tars-silver text-muted-foreground">
                <Command className="w-3 h-3" />
                <span className="font-terminal text-[10px]">K</span>
              </div>
            </div>
            
            {/* Commands List */}
            <div className="max-h-80 overflow-y-auto p-2">
              {filteredCommands.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="font-terminal text-sm text-muted-foreground/50">
                    No commands found
                  </p>
                </div>
              ) : (
                filteredCommands.map((cmd, index) => (
                  <button
                    key={cmd.id}
                    onClick={cmd.action}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={cn(
                      "w-full flex items-center gap-3 p-3 rounded transition-all",
                      index === selectedIndex
                        ? "bg-tars-silver text-tars-light"
                        : "text-muted-foreground hover:bg-tars-silver/50"
                    )}
                  >
                    <div className={cn(
                      "p-2 rounded",
                      index === selectedIndex ? "bg-tars-amber/20 text-tars-amber" : "bg-tars-dark"
                    )}>
                      {cmd.icon}
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-terminal text-xs">{cmd.label}</p>
                      <p className="font-terminal text-[10px] text-muted-foreground/60">{cmd.description}</p>
                    </div>
                    {cmd.shortcut && (
                      <span className="font-terminal text-[10px] text-muted-foreground/40 px-2 py-1 bg-tars-dark rounded">
                        {cmd.shortcut}
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
            
            {/* Footer Hint */}
            <div className="flex items-center justify-between px-4 py-2 border-t border-border bg-tars-dark/50">
              <div className="flex items-center gap-4 font-terminal text-[10px] text-muted-foreground/50">
                <span>↑↓ Navigate</span>
                <span>↵ Select</span>
                <span>Esc Close</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
