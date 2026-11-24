import { CodingJobsPanel } from '@/components/jobs/CodingJobsPanel';
import { ToolsPanel } from '@/components/tools/ToolsPanel';
import { MemoryPanel } from '@/components/memory/MemoryPanel';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Settings, Volume2, VolumeX, History, Command, Keyboard } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { useTarsStore } from '@/store/tarsStore';
import { PersonalityPanel } from './PersonalityPanel';
import { ExtendedSettingsPanel } from './ExtendedSettingsPanel';
import { SystemStatus } from './SystemStatus';
import { MissionStats } from './MissionStats';

export function MonolithSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { isMuted, toggleMute, toggleHistory, toggleCommandPalette } = useTarsStore();

  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 56 : 300 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        "relative h-full min-h-0 shrink-0 flex flex-col",
        "bg-gradient-sidebar border-r border-border",
        "noise-overlay"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!isCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2"
          >
            <div className="w-6 h-6 bg-tars-amber/20 rounded flex items-center justify-center">
              <div className="w-3 h-3 bg-tars-amber rounded-sm" />
            </div>
            <span className="font-terminal text-xs uppercase tracking-widest text-tars-light">
              TARS
            </span>
          </motion.div>
        )}
        
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-tars-silver rounded transition-colors mechanical-click"
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-muted-foreground" />
          )}
        </button>
      </div>
      
      {/* Content */}
      {!isCollapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex-1 min-h-0 overscroll-contain overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
        >
          <MemoryPanel />
          <ToolsPanel />
          <CodingJobsPanel />
          <PersonalityPanel />
          <ExtendedSettingsPanel />
          <SystemStatus />
          <MissionStats />
        </motion.div>
      )}
      
      {/* Collapsed State Icons */}
      {isCollapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex-1 flex flex-col items-center py-4 gap-2"
        >
          <button 
            onClick={() => setIsCollapsed(false)}
            className="p-2 hover:bg-tars-silver rounded transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4 text-muted-foreground" />
          </button>
          <button 
            onClick={toggleHistory}
            className="p-2 hover:bg-tars-silver rounded transition-colors"
            title="History"
          >
            <History className="w-4 h-4 text-muted-foreground" />
          </button>
          <button 
            onClick={toggleCommandPalette}
            className="p-2 hover:bg-tars-silver rounded transition-colors"
            title="Commands (⌘K)"
          >
            <Command className="w-4 h-4 text-muted-foreground" />
          </button>
        </motion.div>
      )}
      
      {/* Footer */}
      <div className="p-4 border-t border-border space-y-2">
        {!isCollapsed && (
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={toggleHistory}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 p-2 rounded transition-colors mechanical-click",
                "text-muted-foreground hover:text-tars-light hover:bg-tars-silver"
              )}
            >
              <History className="w-4 h-4" />
              <span className="font-terminal text-[10px] uppercase tracking-wider">History</span>
            </button>
            <button
              onClick={toggleCommandPalette}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 p-2 rounded transition-colors mechanical-click",
                "text-muted-foreground hover:text-tars-light hover:bg-tars-silver"
              )}
            >
              <Command className="w-4 h-4" />
              <span className="font-terminal text-[10px] uppercase tracking-wider">⌘K</span>
            </button>
          </div>
        )}
        
        <button
          onClick={toggleMute}
          className={cn(
            "w-full flex items-center gap-2 p-2 rounded transition-colors mechanical-click",
            isMuted ? "text-tars-red" : "text-muted-foreground hover:text-tars-light",
            "hover:bg-tars-silver"
          )}
        >
          {isMuted ? (
            <VolumeX className="w-4 h-4" />
          ) : (
            <Volume2 className="w-4 h-4" />
          )}
          {!isCollapsed && (
            <span className="font-terminal text-[10px] uppercase tracking-wider">
              {isMuted ? 'MUTED' : 'AUDIO'}
            </span>
          )}
        </button>
      </div>
      
      {/* Decorative Edge */}
      <div className="absolute right-0 top-0 bottom-0 w-px bg-gradient-to-b from-tars-amber/20 via-transparent to-tars-amber/20" />
    </motion.aside>
  );
}
