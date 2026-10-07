import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api/client';
import { Activity, Database, AlertCircle, Loader2 } from 'lucide-react';

export function StatusStrip() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const [dashData, qualityData] = await Promise.all([
          api.dashboard.getSummary(),
          api.quality.getSummary()
        ]);
        setData({ dash: dashData, quality: qualityData });
      } catch (err) {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    fetchStatus();
  }, []);

  return (
    <div className="border-y border-slate-200 bg-slate-50 py-3">
      <div className="max-w-7xl mx-auto px-6 flex flex-wrap items-center justify-between gap-4 text-sm">
        
        <div className="flex items-center gap-2 font-medium">
          {error ? (
            <><div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div><span className="text-amber-700">Demo environment / Live services not connected</span></>
          ) : loading ? (
            <><Loader2 className="w-3.5 h-3.5 animate-spin text-slate-400" /><span className="text-slate-500">Connecting...</span></>
          ) : (
            <><div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div><span className="text-emerald-700">Platform Operational</span></>
          )}
        </div>

        <div className="flex items-center gap-8 text-slate-600 font-mono text-xs">
          <div className="flex flex-col">
            <span className="text-slate-400 uppercase tracking-widest text-[10px] font-sans font-bold">Pipelines</span>
            <span>{error || loading ? '--' : (data?.dash?.active_sources || 0)} Active</span>
          </div>
          <div className="flex flex-col">
            <span className="text-slate-400 uppercase tracking-widest text-[10px] font-sans font-bold">Data Quality</span>
            <span>{error || loading ? '--' : `${data?.quality?.overall_score || data?.dash?.quality_score || 0}%`}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-slate-400 uppercase tracking-widest text-[10px] font-sans font-bold">DLQ Events</span>
            <span>{error || loading ? '--' : (data?.dash?.dlq_count || 0)}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-slate-400 uppercase tracking-widest text-[10px] font-sans font-bold">Last Sync</span>
            <span>{error || loading ? '--' : 'Just now'}</span>
          </div>
        </div>

      </div>
    </div>
  );
}
