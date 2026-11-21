import { Activity, MessageSquare, Clock, Cpu, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTarsStore } from '@/store/tarsStore';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

export function MissionStats() {
  const { totalMessages, totalSessions, messages, status } = useTarsStore();
  const [uptime, setUptime] = useState('00:00:00');
  const cpuLoad = 0;

  // Simulated uptime counter
  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      const hours = Math.floor(elapsed / 3600000);
      const minutes = Math.floor((elapsed % 3600000) / 60000);
      const seconds = Math.floor((elapsed % 60000) / 1000);
      setUptime(
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      );
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { 
      icon: MessageSquare, 
      label: 'Messages', 
      value: totalMessages.toString(),
      color: 'text-tars-amber' 
    },
    { 
      icon: Clock, 
      label: 'Session Time', 
      value: uptime,
      color: 'text-tars-blue' 
    },
    { 
      icon: BarChart3, 
      label: 'Sessions', 
      value: totalSessions.toString(),
      color: 'text-tars-green' 
    },
    { 
      icon: Cpu, 
      label: 'CPU Load', 
      value: 'Unavailable',
      color: cpuLoad > 60 ? 'text-tars-amber' : 'text-tars-green' 
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Activity className="w-3.5 h-3.5 text-tars-green" />
        <h3 className="font-terminal text-xs uppercase tracking-widest text-tars-green">
          Mission Stats
        </h3>
      </div>
      
      <div className="grid grid-cols-2 gap-2">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={cn(
              "p-2.5 rounded border border-border bg-tars-dark/50",
              "hover:border-tars-amber/20 transition-colors"
            )}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <stat.icon className={cn("w-3 h-3", stat.color)} />
              <span className="font-terminal text-[9px] uppercase tracking-wider text-muted-foreground/60">
                {stat.label}
              </span>
            </div>
            <p className={cn("font-terminal text-sm", stat.color)}>
              {stat.value}
            </p>
          </motion.div>
        ))}
      </div>
      
      {/* Current Session Info */}
      <div className="pt-3 border-t border-border">
        <div className="flex items-center justify-between">
          <span className="font-terminal text-[10px] text-muted-foreground/50 uppercase tracking-wider">
            Current Session
          </span>
          <span className="font-terminal text-[10px] text-tars-light">
            {messages.length} msgs
          </span>
        </div>
        
        {/* Memory bar */}
        <div className="mt-2 h-1.5 bg-tars-dark rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-tars-amber to-tars-amber-dim"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min((messages.length / 100) * 100, 100)}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="font-terminal text-[8px] text-muted-foreground/40">0</span>
          <span className="font-terminal text-[8px] text-muted-foreground/40">100 msg limit</span>
        </div>
      </div>
    </div>
  );
}
