import React from 'react';
import { Activity, BookOpen, Code } from 'lucide-react';
import Link from 'next/link';

export function Footer() {
  return (
    <footer className="bg-navy-900 text-slate-300 py-12 px-6 border-t border-slate-800">
      <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-8 items-center">
        
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-white leading-tight">MeterFlow</div>
            </div>
          </div>
          <p className="text-sm text-slate-400">Utility Meter-to-Cash Cloud Data Platform</p>
        </div>

        <div className="flex flex-wrap md:justify-end gap-6 text-sm font-medium">
          <a href="#platform" className="hover:text-white transition-colors">Platform</a>
          <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
          <Link href="/console" className="text-accent-blue hover:text-blue-400 transition-colors">Console</Link>
          <a href="#" className="flex items-center gap-1 hover:text-white transition-colors"><Code className="w-4 h-4" /> GitHub</a>
          <a href="#" className="flex items-center gap-1 hover:text-white transition-colors"><BookOpen className="w-4 h-4" /> Docs</a>
        </div>

      </div>

      <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-slate-800 text-xs text-slate-500 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>&copy; 2026 MeterFlow Platform. All rights reserved.</div>
        <div className="font-mono bg-slate-800 px-3 py-1.5 rounded text-slate-400">
          Built with Python · GCP · Dataflow · Pub/Sub · BigQuery · PostgreSQL
        </div>
      </div>
    </footer>
  );
}
