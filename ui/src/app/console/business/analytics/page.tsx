"use client";

import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { CloudOff, Loader2, Database } from "lucide-react";
import { api } from "@/lib/api/client";

const TARIFF_COLORS: Record<string, string> = { Std: '#0284c7', ToU: '#38bdf8' };
const FALLBACK_COLORS = ['#0284c7', '#38bdf8', '#0ea5e9', '#bae6fd'];

export default function AnalyticsPage() {
  const [goldStats, setGoldStats] = useState<any>(null);
  const [pipelineSummary, setPipelineSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [gold, pipeline] = await Promise.all([
          api.analytics.getGoldStats(),
          api.analytics.getPipelineSummary(),
        ]);
        setGoldStats(gold);
        setPipelineSummary(pipeline);
      } catch (e) {
        console.error("Failed to load analytics", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="flex h-64 items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-accent-blue" /></div>;
  }

  const tariffPieData = goldStats?.tariff_distribution
    ? Object.entries(goldStats.tariff_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const stageBarData = pipelineSummary?.stages
    ?.filter((s: any) => s.rows != null)
    .map((s: any) => ({
      name: s.name,
      rows: s.rows,
      rejected: s.rejected || 0,
    })) || [];

  const hasData = goldStats?.available;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-navy-900">Analytics</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real data from UK Power Networks SmartMeter Dataset · Gold Parquet Zone
          </p>
        </div>
      </div>

      {/* Gold Stats Summary */}
      {hasData && (
        <div className="grid grid-cols-5 gap-4">
          <StatCard label="Gold Rows" value={goldStats.total_rows?.toLocaleString()} />
          <StatCard label="Distinct Households" value={goldStats.distinct_households?.toLocaleString()} />
          <StatCard label="Tariff: Std" value={goldStats.tariff_distribution?.Std?.toLocaleString() || '0'} />
          <StatCard label="Tariff: ToU" value={goldStats.tariff_distribution?.ToU?.toLocaleString() || '0'} />
          <StatCard label="Source" value="UKPN" sub="uk_power_networks" />
        </div>
      )}

      {/* Date Range */}
      {hasData && goldStats.date_range?.from && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl px-5 py-3 text-sm text-slate-600">
          <span className="font-medium text-navy-900">Reading period: </span>
          {new Date(goldStats.date_range.from).toLocaleDateString()} — {new Date(goldStats.date_range.to).toLocaleDateString()}
          <span className="ml-4 text-slate-400 text-xs font-mono">source: {goldStats.storage_zone}</span>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">

        {/* Tariff Distribution Pie */}
        <div className="col-span-1 bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col h-[380px]">
          <h3 className="text-sm font-semibold text-navy-900 mb-1">Tariff Classification</h3>
          <p className="text-xs text-slate-400 mb-4">
            Real <code className="bg-slate-100 px-1 rounded">stdor_to_u</code> values from Gold zone
          </p>
          <div className="flex-1">
            {tariffPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={tariffPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {tariffPieData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={TARIFF_COLORS[entry.name] || FALLBACK_COLORS[index % FALLBACK_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-400">
                <Database className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-sm">No tariff data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Pipeline Row Count Comparison */}
        <div className="col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col h-[380px]">
          <h3 className="text-sm font-semibold text-navy-900 mb-1">Pipeline Row Counts by Stage</h3>
          <p className="text-xs text-slate-400 mb-4">
            Source → Raw → Standardized → Gold. Real values from PostgreSQL pipeline control plane.
          </p>
          <div className="flex-1">
            {stageBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stageBarData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                  <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                  <Bar dataKey="rows" name="Valid Rows" fill="#0284c7" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="rejected" name="Rejected" fill="#fca5a5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-400">
                <Database className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-sm">Run the ingestion pipeline to see data here</p>
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
}

function StatCard({ label, value, sub }: { label: string, value: string, sub?: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</div>
      <div className="mt-1 text-xl font-bold font-mono text-navy-900">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}
