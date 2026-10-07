import React from 'react';
import { ArrowRight, Database, Play, CheckCircle } from 'lucide-react';
import Link from 'next/link';

export function Hero() {
  return (
    <section className="pt-24 pb-16 px-6 max-w-7xl mx-auto">
      <div className="grid md:grid-cols-2 gap-12 items-center">
        <div className="space-y-6">
          <div className="inline-block px-3 py-1 rounded-full border border-blue-200 bg-blue-50 text-blue-700 text-xs font-bold tracking-widest uppercase">
            Cloud Data Engineering for Utilities
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold text-navy-900 tracking-tight leading-[1.1]">
            From Meter Readings to Actionable <span className="text-accent-blue">Utility Intelligence.</span>
          </h1>
          <p className="text-lg text-slate-600 max-w-lg leading-relaxed">
            Build a reliable cloud data platform that ingests utility operational data, processes changes and events, validates data quality, and serves an analytical warehouse for meter-to-cash operations.
          </p>
          <div className="flex gap-4 pt-4">
            <Link href="/console" className="bg-navy-900 text-white px-6 py-3 rounded-lg text-sm font-semibold hover:bg-navy-800 transition-colors shadow-md flex items-center gap-2">
              Explore the Platform <ArrowRight className="w-4 h-4" />
            </Link>
            <a href="#data-flow" className="bg-white border border-slate-300 text-slate-700 px-6 py-3 rounded-lg text-sm font-semibold hover:bg-slate-50 transition-colors shadow-sm flex items-center gap-2">
              See How Data Flows <Play className="w-4 h-4" />
            </a>
          </div>
        </div>
        
        {/* Animated Pipeline Viz */}
        <div className="relative h-[400px] bg-slate-50 border border-slate-200 rounded-2xl p-8 flex flex-col justify-between overflow-hidden shadow-inner group">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5"></div>
          
          <Stage name="UTILITY SYSTEMS" desc="Source operational databases (PostgreSQL, APIs)." />
          <Connector />
          <Stage name="INGESTION" desc="CDC (Datastream) and API extraction to Cloud Storage." />
          <Connector />
          <Stage name="PROCESSING" desc="Pub/Sub & Dataflow process, validate and transform." />
          <Connector />
          <Stage name="DATA QUALITY" desc="Validates schema and rules. Invalid routed to DLQ." />
          <Connector />
          <Stage name="BIGQUERY" desc="Analytical warehouse containing dimensional models." />
          
          {/* Animated dot */}
          <div className="absolute left-[calc(50%-6px)] top-12 w-3 h-3 bg-accent-blue rounded-full shadow-[0_0_10px_rgba(37,99,235,0.8)] animate-pulse" 
               style={{ animation: 'flowDown 4s infinite linear' }}>
            <style>{`
              @keyframes flowDown {
                0% { transform: translateY(0); opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { transform: translateY(320px); opacity: 0; }
              }
            `}</style>
          </div>
        </div>
      </div>
    </section>
  );
}

function Stage({ name, desc }: { name: string, desc: string }) {
  return (
    <div className="relative z-10 w-full max-w-[240px] mx-auto bg-white border border-slate-200 rounded-lg py-2 px-4 text-center shadow-sm cursor-help group/stage transition-all hover:border-accent-blue hover:shadow-md">
      <div className="text-xs font-bold text-navy-900 tracking-wider">{name}</div>
      
      <div className="absolute left-full ml-4 top-1/2 -translate-y-1/2 w-48 bg-navy-900 text-white text-xs p-3 rounded-lg opacity-0 invisible group-hover/stage:opacity-100 group-hover/stage:visible transition-all z-20 text-left shadow-xl pointer-events-none">
        <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-navy-900 rotate-45"></div>
        {desc}
      </div>
    </div>
  );
}

function Connector() {
  return (
    <div className="h-4 w-px bg-slate-300 mx-auto relative z-0"></div>
  );
}
