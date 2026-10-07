"use client";

import { useEffect, useState } from "react";
import { Database, Link as LinkIcon, RefreshCw, Box, Activity } from "lucide-react";
import { api } from "@/lib/api/client";

export default function SourcesPage() {
  const [ingestionStatus, setIngestionStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.ingestion.getStatus();
        setIngestionStatus(data);
      } catch (err) {
        console.error("Failed to load ingestion status", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const sources = [
    { 
      name: "UK Power Networks SmartMeter Dataset", 
      db: "168 CSV Files (ZIP Archive)", 
      status: loading ? "LOADING" : (ingestionStatus?.status?.toUpperCase() || "NOT CONFIGURED"), 
      sync: loading || !ingestionStatus?.last_run ? "Never" : new Date(ingestionStatus.last_run).toLocaleString(), 
      records: loading ? "--" : (ingestionStatus?.total_rows?.toLocaleString() || "0"), 
      mode: "HTTPS Streaming", 
      schema: "UKPN dToU" 
    },
    // The previous mocked sources are kept as placeholders but clearly marked, or we can just show the real one.
    // The prompt asks to "Replace the relevant source-related UI with actual backend data... No production page may contain fake ingestion status".
    // I'll show only the real one.
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-navy-900">Data Sources</h1>
          <p className="text-sm text-slate-500 mt-1">Manage upstream operational systems and API connections</p>
        </div>
        <button 
          onClick={() => {
            api.ingestion.trigger("1", "test").then(() => {
              alert("Ingestion triggered (Test mode: 1st file)");
            });
          }}
          className="bg-primary text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-primary-hover flex items-center gap-2 text-sm"
        >
          <Activity className="w-4 h-4" /> Run Ingestion (Test)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {sources.map((s, idx) => (
          <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-100 rounded-lg text-slate-600">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-navy-900 text-sm">{s.name}</h3>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">{s.db}</p>
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${s.status === 'CONNECTED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                {s.status}
              </span>
            </div>
            
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500 flex items-center gap-2 text-xs"><RefreshCw className="w-3.5 h-3.5" /> Mode</span>
                <span className="font-medium text-navy-900 text-xs">{s.mode}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500 flex items-center gap-2 text-xs"><LinkIcon className="w-3.5 h-3.5" /> Last Sync</span>
                <span className="text-slate-600 text-xs">{s.sync}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500 flex items-center gap-2 text-xs"><Database className="w-3.5 h-3.5" /> Records Ingested</span>
                <span className="font-mono text-navy-900 font-medium text-xs">{s.records}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500 flex items-center gap-2 text-xs"><Box className="w-3.5 h-3.5" /> Schema</span>
                <span className="font-mono text-slate-600 bg-slate-100 px-1.5 rounded text-xs">{s.schema}</span>
              </div>
            </div>
            
            <div className="mt-5 pt-4 border-t border-slate-100 flex justify-end gap-2">
              <button className="text-xs font-medium text-slate-600 hover:text-navy-900 px-3 py-1.5 rounded hover:bg-slate-50">Settings</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
