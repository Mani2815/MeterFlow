"use client";

import { useEffect, useState } from "react";
import { Folder, Database, Key, CloudOff, Loader2 } from "lucide-react";
import { api } from "@/lib/api/client";

export default function WarehouseExplorerPage() {
  const [goldStats, setGoldStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.analytics.getGoldStats().then(setGoldStats).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Warehouse Explorer</h1>
        <p className="text-sm text-slate-500 mt-1">Schema definitions and real dataset statistics from the Gold Parquet zone</p>
      </div>

      <div className="flex h-[680px] bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        {/* Left Sidebar */}
        <div className="w-64 border-r border-slate-200 flex flex-col bg-slate-50/50">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Storage Zones</h2>
          </div>
          <div className="p-3 overflow-y-auto space-y-4">
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-1 px-2">
                <Folder className="w-4 h-4" /> raw/smartmeter/
              </div>
              <div className="pl-6 space-y-0.5">
                <TableLink name="*.json (NDJSON)" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-1 px-2">
                <Folder className="w-4 h-4" /> standardized/smartmeter/
              </div>
              <div className="pl-6 space-y-0.5">
                <TableLink name="run_<id>.parquet" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-accent-blue mb-1 px-2">
                <Folder className="w-4 h-4 text-accent-blue" /> gold/smartmeter/
              </div>
              <div className="pl-6 space-y-0.5">
                <TableLink name="gold_<id>.parquet" active />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-1 px-2">
                <Folder className="w-4 h-4" /> bigquery/utility_analytics/
              </div>
              <div className="pl-6 space-y-0.5">
                <TableLink name="fact_meter_reading" disabled />
                <TableLink name="dim_tariff" disabled />
              </div>
            </div>
            <div className="mt-2 px-2">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-400 mb-1">
                <Folder className="w-4 h-4" /> postgres/synth_*
              </div>
              <div className="pl-6 space-y-0.5">
                <TableLink name="synth_customer" />
                <TableLink name="synth_account" />
                <TableLink name="synth_contract" />
                <TableLink name="synth_service_point" />
                <TableLink name="synth_meter" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-6 border-b border-slate-200 bg-white">
            <div className="flex items-center gap-3 mb-1">
              <Database className="w-6 h-6 text-slate-400" />
              <h2 className="text-xl font-semibold text-navy-900 font-mono">gold/smartmeter/gold_*.parquet</h2>
            </div>
            <p className="text-sm text-slate-500">
              UKPN SmartMeter Gold zone. One row per validated meter reading event. Partitioned by
              {" "}<code className="bg-slate-100 text-accent-blue px-1 py-0.5 rounded text-xs">event_timestamp</code>.
              Tariff field <code className="bg-slate-100 text-accent-blue px-1 py-0.5 rounded text-xs">stdor_to_u</code> preserved from source.
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-6 bg-slate-50 space-y-6">

            {/* Live Stats */}
            <div className="grid grid-cols-4 gap-4">
              {loading ? (
                <div className="col-span-4 flex justify-center py-6"><Loader2 className="w-6 h-6 animate-spin text-accent-blue" /></div>
              ) : goldStats?.available ? (
                <>
                  <StatCard label="Rows (Gold)" value={goldStats.total_rows?.toLocaleString()} live />
                  <StatCard label="Households" value={goldStats.distinct_households?.toLocaleString()} live />
                  <StatCard label="Tariff: Std" value={goldStats.tariff_distribution?.Std?.toLocaleString() || '0'} live />
                  <StatCard label="Tariff: ToU" value={goldStats.tariff_distribution?.ToU?.toLocaleString() || '0'} live />
                </>
              ) : (
                <div className="col-span-4 flex items-center gap-2 text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm">
                  <CloudOff className="w-5 h-5 flex-shrink-0" />
                  No Gold Parquet files found. Run the ingestion pipeline first.
                </div>
              )}
            </div>

            {/* Schema */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm">
              <div className="px-5 py-3 border-b border-slate-200">
                <h3 className="text-sm font-semibold text-navy-900">Schema — Gold Parquet</h3>
              </div>
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-5 py-3 font-medium">Column</th>
                    <th className="px-5 py-3 font-medium">Type</th>
                    <th className="px-5 py-3 font-medium">Nullable</th>
                    <th className="px-5 py-3 font-medium">Origin</th>
                    <th className="px-5 py-3 font-medium">Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  <SchemaRow name="meter_id" type="STRING" origin="Derived" desc="METER- prefix + LCLid suffix (synthetic)" />
                  <SchemaRow name="household_id" type="STRING" origin="UKPN (Real)" desc="LCLid — real source household identifier" isKey />
                  <SchemaRow name="event_timestamp" type="TIMESTAMP" origin="UKPN (Real)" desc="DateTime from source CSV (UTC)" />
                  <SchemaRow name="consumption_kwh" type="FLOAT64" origin="UKPN (Real)" desc="KWH/hh per half-hour reading" />
                  <SchemaRow name="stdor_to_u" type="STRING" nullable origin="UKPN (Real)" desc="Tariff class: Std or ToU. Preserved exactly from source stdorToU field." />
                  <SchemaRow name="source_system" type="STRING" origin="System" desc="Always: uk_power_networks" />
                  <SchemaRow name="processed_at" type="TIMESTAMP" origin="System" desc="Standardization timestamp" />
                  <SchemaRow name="ingestion_run_id" type="STRING" origin="System" desc="FK to IngestionRun.run_id" />
                  <SchemaRow name="standardize_run_id" type="STRING" origin="System" desc="FK to StandardizeRun.run_id" />
                </tbody>
              </table>
            </div>

            {/* BigQuery blocked notice */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-sm text-amber-700">
              <CloudOff className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">BigQuery load is blocked.</div>
                <div className="mt-1 text-xs text-amber-600">
                  The <code className="bg-amber-100 px-1 rounded">bq_loader.py</code> schema is configured and ready.
                  Authentication via GCP Application Default Credentials is required to load the Gold Parquet into BigQuery.
                  Target table: <code className="bg-amber-100 px-1 rounded">utility_analytics.fact_meter_reading</code>.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TableLink({ name, active, disabled }: { name: string, active?: boolean, disabled?: boolean }) {
  return (
    <div className={`px-2 py-1.5 text-xs font-mono cursor-pointer rounded-md flex items-center gap-2 ${
      active ? 'bg-blue-50 text-accent-blue font-semibold' :
      disabled ? 'text-slate-300' :
      'text-slate-600 hover:bg-slate-100'
    }`}>
      <Database className="w-3 h-3" />
      {name}
      {disabled && <span className="ml-auto text-[9px] text-slate-300 font-sans">BLOCKED</span>}
    </div>
  );
}

function SchemaRow({ name, type, isKey, nullable, origin, desc }: { name: string, type: string, isKey?: boolean, nullable?: boolean, origin: string, desc: string }) {
  const originColor = origin.startsWith('UKPN') ? 'text-emerald-600 bg-emerald-50 border-emerald-100' : 'text-slate-500 bg-slate-50 border-slate-100';
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-5 py-3 font-mono text-xs text-navy-900 font-medium">
        <span className="flex items-center gap-1.5">{name}{isKey && <Key className="w-3 h-3 text-amber-500" />}</span>
      </td>
      <td className="px-5 py-3 font-mono text-xs text-accent-blue">{type}</td>
      <td className="px-5 py-3 text-xs text-slate-400">{nullable ? 'YES' : 'NO'}</td>
      <td className="px-5 py-3">
        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${originColor}`}>{origin}</span>
      </td>
      <td className="px-5 py-3 text-slate-600 text-xs">{desc}</td>
    </tr>
  );
}

function StatCard({ label, value, live }: { label: string, value: string, live?: boolean }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-1">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</div>
        {live && <span className="text-[9px] text-emerald-600 bg-emerald-50 border border-emerald-100 px-1.5 rounded font-bold">LIVE</span>}
      </div>
      <div className="text-lg font-bold font-mono text-navy-900">{value}</div>
    </div>
  );
}
