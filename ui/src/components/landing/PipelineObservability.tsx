import React from 'react';
import { ArrowRight, Activity, CheckCircle, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

export function PipelineObservability() {
  return (
    <section className="py-24 px-6 max-w-7xl mx-auto border-t border-slate-800">
      <div className="flex flex-col md:flex-row gap-16 items-center">
        
        <div className="w-full md:w-1/2 space-y-6">
          <h2 className="text-3xl font-bold text-white tracking-tight">Know What Your Data Pipeline Is Doing</h2>
          <p className="text-lg text-slate-400">
            A reliable warehouse requires constant monitoring. Our operational control plane tracks processing latency, records processed, failures, DLQ volumes, and data-quality scores in real-time.
          </p>
          <div className="pt-4">
            <Link href="/console" className="inline-flex items-center gap-2 text-accent-blue font-bold hover:text-blue-400 transition-colors">
              Open Full Platform Console <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        <div className="w-full md:w-1/2 bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
          {/* Subtle grid bg */}
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 mix-blend-overlay"></div>
          
          <div className="relative z-10 space-y-6">
            <div className="flex justify-between items-center border-b border-slate-700 pb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-accent-blue" />
                <h3 className="font-bold text-white">Pipeline Health</h3>
              </div>
              <div className="text-xs font-mono text-slate-400">Live</div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                <span className="text-sm font-medium text-slate-300">Meter Reading CDC</span>
                <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">
                  <CheckCircle className="w-3.5 h-3.5" /> Healthy
                </span>
              </div>
              <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                <span className="text-sm font-medium text-slate-300">Billing Synchronization</span>
                <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">
                  <CheckCircle className="w-3.5 h-3.5" /> Healthy
                </span>
              </div>
              <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                <span className="text-sm font-medium text-slate-300">Daily Consumption Rollup</span>
                <span className="flex items-center gap-1.5 text-xs font-bold text-amber-400 bg-amber-400/10 px-2 py-1 rounded">
                  <AlertTriangle className="w-3.5 h-3.5" /> Warning
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-700">
              <div className="text-center">
                <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Latency</div>
                <div className="font-mono text-white">124ms</div>
              </div>
              <div className="text-center">
                <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Records</div>
                <div className="font-mono text-emerald-400">18.4M</div>
              </div>
              <div className="text-center">
                <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">DQ Fails</div>
                <div className="font-mono text-red-400">12</div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}
