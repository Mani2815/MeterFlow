import React, { useState } from 'react';
import { ArrowRight, Box, Zap } from 'lucide-react';

export function BatchVsCdc() {
  const [mode, setMode] = useState<'batch' | 'cdc'>('cdc');

  return (
    <section className="py-24 px-6 max-w-5xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight">Two Processing Paradigms</h2>
        <p className="mt-4 text-slate-600 text-lg">The platform supports both continuous streaming and scheduled batch workloads.</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
        
        {/* Toggle */}
        <div className="flex justify-center mb-12">
          <div className="bg-slate-100 p-1 rounded-lg inline-flex">
            <button 
              onClick={() => setMode('batch')}
              className={`px-6 py-2 rounded-md text-sm font-bold flex items-center gap-2 transition-all ${mode === 'batch' ? 'bg-white text-navy-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            >
              <Box className="w-4 h-4" /> Scheduled Batch
            </button>
            <button 
              onClick={() => setMode('cdc')}
              className={`px-6 py-2 rounded-md text-sm font-bold flex items-center gap-2 transition-all ${mode === 'cdc' ? 'bg-white text-navy-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            >
              <Zap className="w-4 h-4" /> Continuous CDC
            </button>
          </div>
        </div>

        {/* Visualization */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 font-mono text-xs font-bold text-slate-700 h-32 transition-all duration-300 relative">
          
          {mode === 'batch' ? (
            <div className="flex items-center gap-4 animate-in fade-in zoom-in duration-300">
              <Node>Source</Node> <ArrowRight className="text-slate-300" />
              <Node>Extract (Airflow)</Node> <ArrowRight className="text-slate-300" />
              <Node>Raw Storage (GCS)</Node> <ArrowRight className="text-slate-300" />
              <Node>Process (SQL)</Node> <ArrowRight className="text-slate-300" />
              <Node>Warehouse (BQ)</Node>
            </div>
          ) : (
            <div className="flex flex-wrap justify-center items-center gap-4 animate-in fade-in zoom-in duration-300">
              <Node>Source</Node> <ArrowRight className="text-accent-blue" />
              <Node>WAL Change</Node> <ArrowRight className="text-accent-blue" />
              <Node>Datastream</Node> <ArrowRight className="text-accent-blue" />
              <Node>GCS</Node> <ArrowRight className="text-accent-blue" />
              <Node>Pub/Sub</Node> <ArrowRight className="text-accent-blue" />
              <Node>Dataflow</Node> <ArrowRight className="text-accent-blue" />
              <Node>Warehouse</Node>
            </div>
          )}

        </div>

        {/* Explanation */}
        <div className="mt-12 max-w-2xl mx-auto text-center">
          <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl">
            {mode === 'batch' ? (
              <>
                <h4 className="text-lg font-bold text-navy-900 mb-2">Batch Processing</h4>
                <p className="text-slate-600">Best for scheduled historical runs, massive bulk ingestions, or integrating with legacy flat-file systems. Handled via Airflow orchestrating standard SQL MERGE statements.</p>
              </>
            ) : (
              <>
                <h4 className="text-lg font-bold text-navy-900 mb-2">CDC (Change Data Capture)</h4>
                <p className="text-slate-600">Best for continuously propagating source-system changes (INSERT, UPDATE, DELETE) in near real-time without locking operational databases. Facilitated by Datastream and Dataflow.</p>
              </>
            )}
          </div>
        </div>

      </div>
    </section>
  );
}

function Node({ children }: { children: React.ReactNode }) {
  return (
    <div className="px-4 py-2 bg-white border-2 border-slate-200 rounded-lg shadow-sm whitespace-nowrap">
      {children}
    </div>
  );
}
