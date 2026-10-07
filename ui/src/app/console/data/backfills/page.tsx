"use client";

import { useState, useEffect } from "react";
import { Play, Filter, Plus, Loader2 } from "lucide-react";
import { api } from "@/lib/api/client";

export default function BackfillsPage() {
  const [backfills, setBackfills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.backfills.list();
        setBackfills(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-navy-900">Historical Backfills</h1>
          <p className="text-sm text-slate-500 mt-1">Safely reload historical data into the warehouse</p>
        </div>
        <button className="flex items-center gap-2 bg-accent-blue text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent-blue-hover transition-colors shadow-sm">
          <Plus className="w-4 h-4" />
          Create Backfill
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex gap-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-300 rounded hover:bg-slate-50">
            <Filter className="w-3.5 h-3.5" /> All Statuses
          </button>
        </div>
        <div className="overflow-x-auto min-h-[300px]">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-white border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 font-medium">Backfill ID</th>
                <th className="px-6 py-3 font-medium">Dataset</th>
                <th className="px-6 py-3 font-medium">Date Range</th>
                <th className="px-6 py-3 font-medium w-48">Progress</th>
                <th className="px-6 py-3 font-medium text-right">Records</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading && (
                <tr>
                  <td colSpan={7} className="h-64 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-accent-blue mx-auto" />
                  </td>
                </tr>
              )}
              {error && (
                <tr>
                  <td colSpan={7} className="h-64 text-center text-red-500">
                    Failed to load backfills: {error}
                  </td>
                </tr>
              )}
              {!loading && !error && backfills.map((bf) => (
                <tr key={bf.backfill_id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono text-xs font-medium text-navy-900">{bf.backfill_id}</td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-600">{bf.dataset}</td>
                  <td className="px-6 py-4 text-xs text-slate-500">
                    {new Date(bf.start_date).toISOString().split('T')[0]} <span className="text-slate-300 mx-1">→</span> {new Date(bf.end_date).toISOString().split('T')[0]}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-full bg-slate-200 rounded-full h-1.5">
                        <div 
                          className={`h-1.5 rounded-full ${bf.status === 'Failed' ? 'bg-red-500' : bf.status === 'Success' ? 'bg-emerald-500' : 'bg-blue-500'}`} 
                          style={{ width: `${bf.progress_pct}%` }}
                        ></div>
                      </div>
                      <span className="text-xs font-mono font-medium text-slate-600 w-8">{bf.progress_pct}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right font-mono text-xs font-medium text-navy-900">{bf.records_processed}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      bf.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 
                      bf.status === 'FAILED' ? 'bg-red-100 text-red-700 border border-red-200' : 
                      'bg-blue-100 text-blue-700 border border-blue-200'
                    }`}>
                      {bf.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-500">{new Date(bf.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
