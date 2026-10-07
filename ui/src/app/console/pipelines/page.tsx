"use client";

import { useState, useEffect } from "react";
import { PlayCircle, Plus, CheckCircle, AlertTriangle, XCircle, Search, Loader2 } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api/client";

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.processing.listRuns();
        setPipelines(data);
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
          <h1 className="text-2xl font-semibold text-navy-900">Pipelines</h1>
          <p className="text-sm text-slate-500 mt-1">Manage and monitor data integration workflows</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
            <PlayCircle className="w-4 h-4" />
            Run Pipeline
          </button>
          <button className="flex items-center gap-2 bg-accent-blue text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent-blue-hover transition-colors shadow-sm">
            <Plus className="w-4 h-4" />
            Create Pipeline
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search pipelines..." 
              className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            />
          </div>
        </div>
        <div className="overflow-x-auto min-h-[300px]">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-5 py-3 font-medium">Pipeline Run ID</th>
                <th className="px-5 py-3 font-medium">Dataset</th>
                <th className="px-5 py-3 font-medium">Source → Standardized</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Processed At</th>
                <th className="px-5 py-3 font-medium text-right">Rows</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 relative">
              {loading && (
                <tr>
                  <td colSpan={6} className="h-64 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-accent-blue mx-auto" />
                  </td>
                </tr>
              )}
              {error && (
                <tr>
                  <td colSpan={6} className="h-64 text-center text-red-500">
                    Failed to load pipelines: {error}
                  </td>
                </tr>
              )}
              {!loading && !error && pipelines.map((p) => (
                <tr key={p.run_id} className="hover:bg-slate-50 transition-colors group">
                  <td className="px-5 py-4 font-medium text-navy-900 font-mono text-xs max-w-[150px] truncate">
                    {p.run_id}
                  </td>
                  <td className="px-5 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                      {p.dataset}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-600 text-xs font-mono truncate max-w-[250px]">
                    {p.source_file.split('/').pop()} <span className="text-slate-400">→</span> Parquet
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-5 py-4 text-slate-500 font-mono text-xs">{new Date(p.started_at).toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-mono text-navy-900">
                    {p.rows_processed.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  let Icon = CheckCircle;
  let statusColor = "text-emerald-700 bg-emerald-50 border-emerald-200";
  
  if (status === "RUNNING") {
    Icon = Loader2;
    statusColor = "text-blue-700 bg-blue-50 border-blue-200";
  } else if (status === "FAILED") {
    Icon = XCircle;
    statusColor = "text-red-700 bg-red-50 border-red-200";
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium border ${statusColor}`}>
      <Icon className={`w-3.5 h-3.5 ${status === 'RUNNING' ? 'animate-spin' : ''}`} />
      {status}
    </span>
  );
}
