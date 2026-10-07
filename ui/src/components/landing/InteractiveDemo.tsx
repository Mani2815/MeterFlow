import React, { useState } from 'react';
import { Play, CheckCircle2, XCircle, AlertCircle, RefreshCw } from 'lucide-react';

type DemoState = 'idle' | 'valid' | 'invalid' | 'duplicate' | 'cdc';

export function InteractiveDemo() {
  const [state, setState] = useState<DemoState>('idle');
  const [isAnimating, setIsAnimating] = useState(false);

  const triggerEvent = (type: DemoState) => {
    if (isAnimating) return;
    setIsAnimating(true);
    setState(type);
    
    // Reset animation after 2.5s
    setTimeout(() => {
      setIsAnimating(false);
    }, 2500);
  };

  return (
    <section className="py-24 px-6 bg-slate-900 text-white border-t border-slate-800">
      <div className="max-w-5xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight">Explore the Pipeline</h2>
          <p className="mt-4 text-slate-400 text-lg">Send test events through the simulated ingestion engine to observe pipeline behavior.</p>
        </div>

        <div className="grid md:grid-cols-4 gap-8">
          
          {/* Controls */}
          <div className="flex flex-col gap-3">
            <button 
              disabled={isAnimating}
              onClick={() => triggerEvent('valid')}
              className="bg-slate-800 border border-slate-700 text-slate-200 px-4 py-3 rounded-lg text-sm font-bold hover:bg-slate-700 transition-colors text-left flex justify-between items-center disabled:opacity-50"
            >
              Send Valid Event <Play className="w-4 h-4 text-emerald-400" />
            </button>
            <button 
              disabled={isAnimating}
              onClick={() => triggerEvent('invalid')}
              className="bg-slate-800 border border-slate-700 text-slate-200 px-4 py-3 rounded-lg text-sm font-bold hover:bg-slate-700 transition-colors text-left flex justify-between items-center disabled:opacity-50"
            >
              Send Invalid Event <XCircle className="w-4 h-4 text-red-400" />
            </button>
            <button 
              disabled={isAnimating}
              onClick={() => triggerEvent('duplicate')}
              className="bg-slate-800 border border-slate-700 text-slate-200 px-4 py-3 rounded-lg text-sm font-bold hover:bg-slate-700 transition-colors text-left flex justify-between items-center disabled:opacity-50"
            >
              Send Duplicate <AlertCircle className="w-4 h-4 text-amber-400" />
            </button>
            <button 
              disabled={isAnimating}
              onClick={() => triggerEvent('cdc')}
              className="bg-slate-800 border border-slate-700 text-slate-200 px-4 py-3 rounded-lg text-sm font-bold hover:bg-slate-700 transition-colors text-left flex justify-between items-center disabled:opacity-50"
            >
              Trigger CDC Update <RefreshCw className="w-4 h-4 text-blue-400" />
            </button>
          </div>

          {/* Visualization */}
          <div className="md:col-span-3 bg-slate-950 border border-slate-800 rounded-xl p-8 flex flex-col items-center justify-center relative overflow-hidden min-h-[300px]">
            
            {state === 'idle' ? (
              <div className="text-slate-500 text-center">
                <Play className="w-12 h-12 mx-auto mb-4 opacity-20" />
                <p>Click an event button to simulate pipeline ingestion.</p>
              </div>
            ) : (
              <div className="w-full max-w-lg">
                
                {/* Pipeline Visual */}
                <div className="flex justify-between items-center relative z-10 font-mono text-xs font-bold text-slate-300">
                  <div className="bg-slate-800 px-3 py-2 rounded">Source</div>
                  <div className="h-px bg-slate-700 flex-1 mx-2"></div>
                  
                  {state === 'cdc' ? (
                    <div className="bg-slate-800 px-3 py-2 rounded text-blue-400">Datastream</div>
                  ) : (
                    <div className="bg-slate-800 px-3 py-2 rounded">Pub/Sub</div>
                  )}

                  <div className="h-px bg-slate-700 flex-1 mx-2"></div>
                  <div className={`bg-slate-800 px-3 py-2 rounded ${state === 'invalid' ? 'text-red-400' : 'text-emerald-400'}`}>Dataflow</div>
                  <div className="h-px bg-slate-700 flex-1 mx-2"></div>
                  
                  {state === 'invalid' ? (
                    <div className="bg-red-900/50 border border-red-500/50 text-red-400 px-3 py-2 rounded">DLQ</div>
                  ) : (
                    <div className="bg-emerald-900/50 border border-emerald-500/50 text-emerald-400 px-3 py-2 rounded">BigQuery</div>
                  )}
                </div>

                {/* Animated Particle */}
                <div className={`absolute top-[48px] left-[10%] w-3 h-3 rounded-full shadow-[0_0_10px_currentColor] z-20 ${
                  state === 'invalid' ? 'bg-red-500 text-red-500 animate-[flowRight_2s_ease-out_forwards]' : 
                  state === 'duplicate' ? 'bg-amber-500 text-amber-500 animate-[flowHalf_1.5s_ease-out_forwards]' :
                  'bg-emerald-500 text-emerald-500 animate-[flowRight_2s_ease-out_forwards]'
                }`}>
                  <style>{`
                    @keyframes flowRight {
                      0% { left: 10%; opacity: 1; }
                      100% { left: 88%; opacity: 0; }
                    }
                    @keyframes flowHalf {
                      0% { left: 10%; opacity: 1; }
                      100% { left: 60%; opacity: 0; }
                    }
                  `}</style>
                </div>

                {/* Result Message */}
                <div className="mt-16 text-center animate-in fade-in slide-in-from-bottom-4 duration-500 delay-1000">
                  {state === 'valid' && <div className="text-emerald-400 font-bold bg-emerald-400/10 inline-block px-4 py-2 rounded">Processed successfully</div>}
                  {state === 'invalid' && <div className="text-red-400 font-bold bg-red-400/10 inline-block px-4 py-2 rounded">Validation failed — sent to DLQ</div>}
                  {state === 'duplicate' && <div className="text-amber-400 font-bold bg-amber-400/10 inline-block px-4 py-2 rounded">Duplicate detected — skipped (MERGE)</div>}
                  {state === 'cdc' && <div className="text-blue-400 font-bold bg-blue-400/10 inline-block px-4 py-2 rounded">UPDATE event captured and processed</div>}
                </div>

              </div>
            )}

          </div>

        </div>
      </div>
    </section>
  );
}
