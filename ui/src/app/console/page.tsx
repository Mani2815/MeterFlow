"use client";

import { useState, useEffect } from "react";
import { Activity, Database, CheckCircle, AlertTriangle, XCircle, Terminal, Loader2, ArrowDown, CloudOff } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from "@/lib/api/client";

export default function OverviewPage() {
  const [summary, setSummary] = useState<any>(null);
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [chartError, setChartError] = useState(false);
  const [pipelineSummary, setPipelineSummary] = useState<any>(null);
  const [goldStats, setGoldStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [dashData, pipeData] = await Promise.all([
          api.dashboard.getSummary(),
          api.processing.listRuns()
        ]);
        setSummary(dashData);
        setPipelines(pipeData.slice(0, 4));

        try {
          const [pipeSum, gold] = await Promise.all([
            api.analytics.getPipelineSummary(),
            api.analytics.getGoldStats(),
          ]);
          setPipelineSummary(pipeSum);
          setGoldStats(gold);
        } catch (e) {
          console.warn("Analytics unavailable:", e);
        }

        try {
          const consumptionData = await api.analytics.getDailyConsumption();
          setChartData(consumptionData);
        } catch (analyticsErr) {
          setChartError(true);
        }

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-accent-blue" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Data Platform Overview</h1>
        <p className="text-sm text-slate-500 mt-1">Utility Meter-to-Cash Cloud Data Platform · Source: UK Power Networks SmartMeter Dataset</p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard label="Records Processed" value={summary?.records_processed_today?.toLocaleString() || "0"} />
        <KpiCard label="Data Quality" value={`${summary?.quality_score}%`} isPositive />
        <KpiCard label="Failed Runs" value={summary?.failed_runs?.toString() || "0"} isNegative={summary?.failed_runs > 0} />
        <KpiCard label="DLQ Records" value={summary?.dlq_count?.toString() || "0"} isWarning={summary?.dlq_count > 0} />
      </div>

      {/* Data Journey */}
      {pipelineSummary && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50">
            <h2 className="text-sm font-semibold text-navy-900">Data Journey — UKPN Smart-Meter Dataset</h2>
            <p className="text-xs text-slate-500 mt-0.5">Real pipeline provenance from source to Gold zone</p>
          </div>
          <div className="flex items-stretch divide-x divide-slate-200 overflow-x-auto">
            {pipelineSummary.stages?.map((stage: any, i: number) => (
              <JourneyStage key={i} stage={stage} />
            ))}
          </div>
        </div>
      )}

      {/* Gold Stats */}
      {goldStats?.available && (
        <div className="grid grid-cols-5 gap-4">
          <KpiCard label="Gold Rows" value={goldStats.total_rows?.toLocaleString()} />
          <KpiCard label="Households" value={goldStats.distinct_households?.toLocaleString()} />
          <KpiCard label="Tariff: Std" value={goldStats.tariff_distribution?.Std?.toLocaleString() || "0"} />
          <KpiCard label="Tariff: ToU" value={goldStats.tariff_distribution?.ToU?.toLocaleString() || "0"} />
          <KpiCard label="Total kWh" value={goldStats.total_consumption_kwh?.toLocaleString()} />
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">

          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-sm font-semibold text-navy-900">Pipeline Runs</h2>
            </div>
            <div className="overflow-x-auto min-h-[200px]">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-5 py-3 font-medium">Pipeline</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Last Run</th>
                    <th className="px-5 py-3 font-medium">Rows</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {pipelines.map(p => (
                    <PipelineRow key={p.run_id} name={p.dataset} status={p.status} time={new Date(p.started_at).toLocaleTimeString()} duration={`${p.rows_processed?.toLocaleString() || 0} rows`} />
                  ))}
                  {pipelines.length === 0 && (
                    <tr><td colSpan={4} className="px-5 py-8 text-center text-slate-400 text-sm">No pipeline runs found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5">
            <h2 className="text-sm font-semibold text-navy-900 mb-1">Daily Consumption Analytics</h2>
            <p className="text-xs text-slate-400 mb-4">Local Gold Parquet Data</p>
            <div className="h-64 flex items-center justify-center">
              {chartError ? (
                <div className="text-center text-slate-400">
                  <CloudOff className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm font-medium">Analytics Unavailable</p>
                  <p className="text-xs mt-1 text-slate-400">Cannot load daily consumption data.</p>
                </div>
              ) : chartData.length === 0 ? (
                <div className="text-center text-slate-400">
                  <Database className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No data in warehouse</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dx={-10} tickFormatter={(val) => `${(val/1000).toFixed(0)}k`} />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                    <Line type="monotone" dataKey="consumption" name="Consumption (kWh)" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        <div className="col-span-1">
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm h-full">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-sm font-semibold text-navy-900">Recent Activity</h2>
            </div>
            <div className="p-5">
              <div className="space-y-6">
                {pipelines.map(p => (
                  <TimelineItem key={p.run_id} time={new Date(p.started_at).toLocaleTimeString()} text={`${p.rows_processed?.toLocaleString() || 0} records processed in ${p.dataset}`} type={p.status === 'SUCCESS' ? 'success' : 'warning'} />
                ))}
                {pipelines.length === 0 && (
                  <div className="text-sm text-slate-500 text-center py-4">No recent activity</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function JourneyStage({ stage }: { stage: any }) {
  const statusColors: Record<string, string> = {
    PASS: "text-emerald-600 bg-emerald-50 border-emerald-200",
    ACTIVE: "text-blue-600 bg-blue-50 border-blue-200",
    PENDING: "text-slate-500 bg-slate-50 border-slate-200",
    BLOCKED: "text-amber-600 bg-amber-50 border-amber-200",
  };
  const color = statusColors[stage.status] || statusColors.PENDING;

  return (
    <div className="flex-1 min-w-[180px] p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-navy-900 uppercase tracking-wider">{stage.name}</span>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${color}`}>{stage.status}</span>
      </div>
      {stage.rows != null && (
        <div className="text-2xl font-bold font-mono text-navy-900">{stage.rows.toLocaleString()}</div>
      )}
      {stage.rows != null && <div className="text-xs text-slate-400 mt-0.5">rows</div>}
      {stage.rejected != null && (
        <div className="text-xs text-slate-500 mt-2">Rejected: <span className="font-mono font-medium text-red-500">{stage.rejected}</span></div>
      )}
      {stage.quality_score != null && (
        <div className="text-xs text-slate-500">Quality: <span className="font-mono font-medium text-emerald-600">{stage.quality_score}%</span></div>
      )}
      {stage.format && <div className="text-xs text-slate-400 mt-2 font-mono">{stage.format}</div>}
      {stage.description && <div className="text-xs text-slate-400 mt-1 leading-relaxed">{stage.description}</div>}
    </div>
  );
}

function KpiCard({ label, value, isPositive, isNegative, isWarning }: { label: string, value: string, isPositive?: boolean, isNegative?: boolean, isWarning?: boolean }) {
  let valueColor = "text-navy-900";
  if (isPositive) valueColor = "text-emerald-600";
  if (isNegative) valueColor = "text-red-600";
  if (isWarning) valueColor = "text-amber-600";

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</div>
      <div className={`mt-2 text-2xl font-bold font-mono tracking-tight ${valueColor}`}>{value}</div>
    </div>
  );
}

function PipelineRow({ name, status, time, duration }: { name: string, status: string, time: string, duration: string }) {
  let Icon = CheckCircle;
  let statusColor = "text-emerald-600 bg-emerald-50 border-emerald-200";

  if (status === "Warning") {
    Icon = AlertTriangle;
    statusColor = "text-amber-600 bg-amber-50 border-amber-200";
  } else if (status === "FAILED") {
    Icon = XCircle;
    statusColor = "text-red-600 bg-red-50 border-red-200";
  } else if (status === "RUNNING") {
    Icon = Loader2;
    statusColor = "text-blue-600 bg-blue-50 border-blue-200";
  }

  return (
    <tr className="hover:bg-slate-50/50">
      <td className="px-5 py-3 font-medium text-navy-900">{name}</td>
      <td className="px-5 py-3">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium border ${statusColor}`}>
          <Icon className="w-3.5 h-3.5" />
          {status}
        </span>
      </td>
      <td className="px-5 py-3 text-slate-500">{time}</td>
      <td className="px-5 py-3 text-slate-500 font-mono text-xs">{duration}</td>
    </tr>
  );
}

function TimelineItem({ time, text, type }: { time: string, text: string, type: 'success' | 'warning' | 'info' }) {
  let dotColor = "bg-blue-500 border-blue-200";
  if (type === 'success') dotColor = "bg-emerald-500 border-emerald-200";
  if (type === 'warning') dotColor = "bg-amber-500 border-amber-200";

  return (
    <div className="relative pl-6">
      <div className={`absolute left-0 top-1.5 w-2 h-2 rounded-full border-2 ${dotColor} shadow-sm z-10`}></div>
      <div className="absolute left-1 top-3.5 bottom-[-1.5rem] w-px bg-slate-200 -z-0 last:hidden"></div>
      <div className="flex gap-3 text-sm">
        <div className="font-mono text-slate-400 text-xs mt-0.5">{time}</div>
        <div className="text-slate-700">{text}</div>
      </div>
    </div>
  );
}
