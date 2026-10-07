"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, ArrowUpRight, CheckCircle2, ShieldCheck, XCircle, Loader2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from "@/lib/api/client";


export default function DataQualityPage() {
  const [summary, setSummary] = useState<any>(null);
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [data, issuesData, qRuns] = await Promise.all([
          api.quality.getSummary(),
          api.quality.getIssues(),
          api.analytics.getPipelineSummary(),
        ]);
        setSummary(data);
        setIssues(issuesData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="flex h-64 items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-accent-blue" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Data Quality</h1>
        <p className="text-sm text-slate-500 mt-1">Monitor the integrity and reliability of the data warehouse</p>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-center items-center text-center">
          <ShieldCheck className="w-12 h-12 text-emerald-500 mb-4" />
          <div className="text-sm font-medium text-slate-500 uppercase tracking-wide">Overall Score</div>
          <div className="text-5xl font-bold font-mono text-navy-900 mt-2">{summary?.overall_score ?? 0}%</div>
          <div className="text-xs text-emerald-600 font-medium flex items-center mt-3 bg-emerald-50 px-2 py-1 rounded-md">
            <ArrowUpRight className="w-3 h-3 mr-1" />
            0.2% vs last week
          </div>
        </div>

        <div className="col-span-3 bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex">
          <div className="w-1/3 border-r border-slate-200 p-6 flex flex-col justify-center space-y-4">
            <DimensionScore name="Completeness" score={`${summary?.completeness ?? 0}%`} />
            <DimensionScore name="Validity" score={`${summary?.validity ?? 0}%`} />
            <DimensionScore name="Uniqueness" score={`${summary?.uniqueness ?? 0}%`} />
            <DimensionScore name="Consistency" score={`${summary?.consistency ?? 0}%`} />
            <DimensionScore name="Timeliness" score={`${summary?.timeliness ?? 0}%`} />
          </div>
          <div className="w-2/3 p-6">
            <h3 className="text-sm font-semibold text-navy-900 mb-2">Quality Dimensions</h3>
            <p className="text-xs text-slate-400 mb-4">Scores are aggregated from all pipeline quality runs stored in PostgreSQL.</p>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                <div className="text-xs text-slate-500 uppercase tracking-wider">Source</div>
                <div className="text-sm font-semibold text-navy-900 mt-1">UK Power Networks UKPN</div>
                <div className="text-xs text-slate-400 mt-0.5">SmartMeter London Households</div>
              </div>
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                <div className="text-xs text-slate-500 uppercase tracking-wider">DQ Engine</div>
                <div className="text-sm font-semibold text-navy-900 mt-1">Pandas + PostgreSQL</div>
                <div className="text-xs text-slate-400 mt-0.5">quality.py / DataQualityRun table</div>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-4 italic">Quality metrics are derived directly from the PostgreSQL control plane.</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200">
          <h2 className="text-base font-semibold text-navy-900">Active Quality Issues</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 font-medium">Error Type</th>
                <th className="px-6 py-3 font-medium">Dataset</th>
                <th className="px-6 py-3 font-medium">Error Message</th>
                <th className="px-6 py-3 font-medium">Event ID</th>
                <th className="px-6 py-3 font-medium">Timestamp</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {issues.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-500">No active quality issues detected.</td>
                </tr>
              )}
              {issues.map((issue, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-medium text-navy-900">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                      {issue.error_type}
                    </div>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-600">{issue.dataset}</td>
                  <td className="px-6 py-4 text-sm text-slate-700 truncate max-w-[200px]" title={issue.error_message}>{issue.error_message}</td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-500 truncate max-w-[150px]">{issue.event_id}</td>
                  <td className="px-6 py-4 text-slate-500 text-xs">{new Date(issue.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded border border-slate-200">
                      {issue.status}
                    </span>
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

function DimensionScore({ name, score }: { name: string, score: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-slate-600">{name}</span>
      <span className="text-sm font-mono font-medium text-navy-900">{score}</span>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  let colors = "bg-slate-100 text-slate-700 border-slate-200";
  if (severity === "Critical") colors = "bg-red-50 text-red-700 border-red-200 font-bold";
  if (severity === "High") colors = "bg-orange-50 text-orange-700 border-orange-200";
  if (severity === "Medium") colors = "bg-amber-50 text-amber-700 border-amber-200";

  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs border ${colors}`}>
      {severity}
    </span>
  );
}
