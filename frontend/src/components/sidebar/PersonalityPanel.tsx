import { Smile, Eye, Lock } from 'lucide-react';
import { TarsSlider } from '@/components/ui/TarsSlider';
import { useTarsStore } from '@/store/tarsStore';

export function PersonalityPanel() {
  const { humor, honesty, discretion, setHumor, setHonesty, setDiscretion } = useTarsStore();

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h3 className="font-terminal text-xs uppercase tracking-widest text-tars-amber">
          Personality Matrix
        </h3>
        <p className="text-[10px] text-muted-foreground/60 font-terminal">
          Tone only. Truthfulness and access rules stay fixed.
        </p>
      </div>
      
      <div className="space-y-6">
        <TarsSlider
          label="Humor"
          value={humor}
          onChange={setHumor}
          icon={<Smile className="w-3.5 h-3.5" />}
          color="amber"
        />
        
        <TarsSlider
          label="Directness"
          value={honesty}
          onChange={setHonesty}
          icon={<Eye className="w-3.5 h-3.5" />}
          color="blue"
        />
        
        <TarsSlider
          label="Restraint"
          value={discretion}
          onChange={setDiscretion}
          icon={<Lock className="w-3.5 h-3.5" />}
          color="green"
        />
      </div>
      
      {/* Preset Configurations */}
      <div className="pt-4 border-t border-border space-y-2">
        <p className="font-terminal text-[10px] text-muted-foreground/50 uppercase tracking-widest mb-3">
          Quick Presets
        </p>
        <div className="grid grid-cols-3 gap-2">
          {[
            { name: 'COOPER', preset: 'cooper' as const },
            { name: 'BRAND', preset: 'brand' as const },
            { name: 'COMEDY', preset: 'comedy' as const },
            { name: 'MISSION', preset: 'mission' as const },
            { name: 'ANALYST', preset: 'analyst' as const },
            { name: 'CREATIVE', preset: 'creative' as const },
          ].map((item) => (
            <button
              key={item.name}
              onClick={() => useTarsStore.getState().applyPreset(item.preset)}
              className="px-2 py-2 font-terminal text-[9px] uppercase tracking-wider
                       bg-tars-dark border border-border rounded
                       hover:border-tars-amber/50 hover:bg-tars-silver
                       transition-all duration-200 mechanical-click
                       text-muted-foreground hover:text-tars-light"
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
