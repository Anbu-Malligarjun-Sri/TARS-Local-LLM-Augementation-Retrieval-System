import { Zap, FileText, Shield, Heart, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TarsSlider } from '@/components/ui/TarsSlider';
import { useTarsStore } from '@/store/tarsStore';
import { cn } from '@/lib/utils';

export function ExtendedSettingsPanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const { 
    responseSpeed, 
    verbosity, 
    cautionLevel, 
    trustLevel,
    setResponseSpeed,
    setVerbosity,
    setCautionLevel,
    setTrustLevel
  } = useTarsStore();

  return (
    <div className="space-y-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center justify-between p-2 rounded",
          "hover:bg-tars-silver transition-colors",
          "border border-transparent hover:border-border"
        )}
      >
        <div className="space-y-0.5">
          <h3 className="font-terminal text-xs uppercase tracking-widest text-tars-blue text-left">
            Extended Parameters
          </h3>
          <p className="text-[10px] text-muted-foreground/60 font-terminal text-left">
            Advanced behavioral tuning
          </p>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        )}
      </button>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <fieldset disabled className="space-y-5 pt-2 opacity-50"><legend>These parameters are not supported yet.</legend>
              <TarsSlider
                label="Response Speed"
                value={responseSpeed}
                onChange={setResponseSpeed}
                icon={<Zap className="w-3.5 h-3.5" />}
                color="amber"
                minLabel="Thoughtful"
                maxLabel="Rapid"
              />
              
              <TarsSlider
                label="Verbosity"
                value={verbosity}
                onChange={setVerbosity}
                icon={<FileText className="w-3.5 h-3.5" />}
                color="blue"
                minLabel="Terse"
                maxLabel="Detailed"
              />
              
              <TarsSlider
                label="Caution Level"
                value={cautionLevel}
                onChange={setCautionLevel}
                icon={<Shield className="w-3.5 h-3.5" />}
                color="green"
                minLabel="Bold"
                maxLabel="Careful"
              />
              
              <TarsSlider
                label="Trust Level"
                value={trustLevel}
                onChange={setTrustLevel}
                icon={<Heart className="w-3.5 h-3.5" />}
                color="amber"
                minLabel="Skeptical"
                maxLabel="Trusting"
              />
            </fieldset>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
