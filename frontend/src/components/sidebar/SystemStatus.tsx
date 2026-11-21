import { Wifi, Database, Cpu, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useTarsStore } from '@/store/tarsStore';
import { CueLight } from '@/components/ui/CueLight';

export function SystemStatus() {
  const { status, isConnected, humor, honesty, discretion } = useTarsStore();

  const systems = [
    {
      icon: Wifi,
      label: 'NETWORK',
      status: isConnected ? 'ONLINE' : 'OFFLINE',
      ok: isConnected
    },
    {
      icon: Database,
      label: 'RAG DB',
      status: 'NOT PROBED',
      ok: false
    },
    {
      icon: Cpu,
      label: 'LLM',
      status: 'NOT PROBED',
      ok: false
    },
  ];

  return (
    <div className="space-y-6">
      {/* Main Status */}
      <div className="space-y-3">
        <h3 className="font-terminal text-xs uppercase tracking-widest text-tars-amber">
          System Status
        </h3>
        <CueLight status={status} />
      </div>

      {/* System Indicators */}
      <div className="space-y-2">
        {systems.map((system) => (
          <div
            key={system.label}
            className="flex items-center justify-between py-2 px-3 bg-tars-dark/50 rounded border border-border/50"
          >
            <div className="flex items-center gap-2">
              <system.icon className="w-3 h-3 text-muted-foreground" />
              <span className="font-terminal text-[10px] uppercase tracking-wider text-muted-foreground">
                {system.label}
              </span>
            </div>
            <span className={cn(
              "font-terminal text-[10px] uppercase",
              system.ok ? "text-tars-green" : "text-tars-red"
            )}>
              {system.status}
            </span>
          </div>
        ))}
      </div>

      {/* Current Config Display */}
      <div className="pt-4 border-t border-border">
        <p className="font-terminal text-[10px] text-muted-foreground/50 uppercase tracking-widest mb-3">
          Active Configuration
        </p>
        <div className="bg-tars-dark rounded border border-border p-3 font-terminal text-[10px] text-muted-foreground space-y-1">
          <div className="flex justify-between">
            <span>HUMOR</span>
            <span className="text-tars-amber">{humor}%</span>
          </div>
          <div className="flex justify-between">
            <span>HONESTY</span>
            <span className="text-tars-blue">{honesty}%</span>
          </div>
          <div className="flex justify-between">
            <span>DISCRETION</span>
            <span className="text-tars-green">{discretion}%</span>
          </div>
        </div>
      </div>

      {/* Heartbeat Animation */}
      <div className="flex items-center gap-2">
        <Activity className="w-3 h-3 text-tars-amber" />
        <div className="flex-1 h-4 relative overflow-hidden rounded bg-tars-dark border border-border/50">
          <motion.div
            className="absolute inset-y-0 left-0 w-full bg-gradient-to-r from-transparent via-tars-amber/30 to-transparent"
            animate={{ x: ['-100%', '100%'] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
        </div>
      </div>
    </div>
  );
}
