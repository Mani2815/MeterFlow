"use client";

import { Terminal, Database, FileJson, ArrowRight, Play, RefreshCw, XCircle } from "lucide-react";

export default function PipelineDetailPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-navy-900">Meter Reading Ingestion</h1>
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium px-2 py-1 rounded-md">Healthy</span>
          </div>
          <p className="text-sm text-slate-500 mt-1 font-mono text-xs">ID: pipe_mtr_ingest_01 • Last execution: 2 min ago</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-3 py-1.5 rounded text-sm font-medium hover:bg-slate-50">
            <FileJson className="w-4 h-4" />
            Config
          </button>
          <button className="flex items-center gap-2 bg-accent-blue text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-accent-blue-hover">
            <Play className="w-4 h-4" />
            Trigger
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-8">Pipeline Topology</h2>
        
        {/* Visual DAG Simulation */}
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          
          <DagNode name="PostgreSQL" sub="utility_db" icon={Database} status="success" />
          <DagEdge />
          <DagNode name="Datastream" sub="cdc_stream_01" icon={RefreshCw} status="success" />
          <DagEdge />
          <DagNode name="Pub/Sub" sub="meter_topic" icon={ArrowRight} status="success" />
          
          <div className="flex flex-col items-center">
            <div className="h-12 w-px bg-slate-300 border-l-2 border-dashed border-slate-300"></div>
            <DagNode name="Dataflow" sub="parse_normalize" icon={Terminal} status="active" />
            <div className="flex w-full items-start">
              <div className="w-1/2 h-16 border-l-2 border-b-2 border-dashed border-slate-300 rounded-bl-xl"></div>
              <div className="w-1/2 h-16 border-r-2 border-b-2 border-dashed border-slate-300 rounded-br-xl"></div>
            </div>
            <div className="flex justify-between w-full mt-4 px-8 space-x-12">
              <DagNode name="DLQ" sub="quality.dlq" icon={XCircle} status="warning" compact />
              <DagNode name="BigQuery" sub="stg_meters" icon={Database} status="success" compact />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-900 rounded-xl overflow-hidden shadow-sm border border-slate-800 flex flex-col h-96">
          <div className="px-4 py-3 bg-slate-800 border-b border-slate-700 flex justify-between items-center">
            <div className="flex items-center gap-2 text-slate-300 text-sm font-medium font-mono">
              <Terminal className="w-4 h-4" />
              stdout
            </div>
          </div>
          <div className="p-4 font-mono text-xs text-slate-300 space-y-2 overflow-y-auto flex-1">
            <LogLine time="10:42:11" level="INFO" text="Pipeline started manually by usr_admin" />
            <LogLine time="10:42:13" level="INFO" text="Connecting to PostgreSQL logical replication slot..." />
            <LogLine time="10:42:18" level="INFO" text="Extracted 12,842 CDC events in window [10:35, 10:40]" />
            <LogLine time="10:42:21" level="INFO" text="Validating payload schemas against registry v1.4" />
            <LogLine time="10:42:23" level="WARN" text="12 records failed validation (Missing meter_id), routing to DLQ" color="text-amber-400" />
            <LogLine time="10:42:28" level="INFO" text="12,830 records successfully written to stg_meter_readings" />
            <LogLine time="10:42:29" level="INFO" text="Pipeline completed. Run ID: RUN-20261006-1042" color="text-emerald-400" />
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-96 flex flex-col">
          <div className="px-5 py-4 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-navy-900">Run History</h2>
          </div>
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 sticky top-0">
                <tr>
                  <th className="px-5 py-3 font-medium">Run ID</th>
                  <th className="px-5 py-3 font-medium">Started</th>
                  <th className="px-5 py-3 font-medium text-right">Records</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                <RunRow id="RUN-20261006-1042" time="10:42" records="12.8k" status="Success" />
                <RunRow id="RUN-20261006-1035" time="10:35" records="14.2k" status="Success" />
                <RunRow id="RUN-20261006-1030" time="10:30" records="0" status="Failed" />
                <RunRow id="RUN-20261006-1025" time="10:25" records="11.1k" status="Success" />
                <RunRow id="RUN-20261006-1020" time="10:20" records="13.4k" status="Success" />
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function DagNode({ name, sub, icon: Icon, status, compact }: { name: string, sub: string, icon: any, status: 'success'|'active'|'warning', compact?: boolean }) {
  let colors = "bg-white border-slate-200 text-slate-700";
  let iconColor = "text-slate-500";
  
  if (status === 'active') {
    colors = "bg-blue-50 border-blue-400 text-blue-900 shadow-md ring-2 ring-blue-100";
    iconColor = "text-blue-600";
  } else if (status === 'warning') {
    colors = "bg-amber-50 border-amber-300 text-amber-900";
    iconColor = "text-amber-600";
  } else if (status === 'success') {
    iconColor = "text-emerald-500";
  }

  if (compact) {
    return (
      <div className={`flex flex-col items-center justify-center border rounded-lg p-3 w-28 text-center ${colors}`}>
        <Icon className={`w-5 h-5 mb-1 ${iconColor}`} />
        <div className="font-semibold text-xs">{name}</div>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-4 border rounded-xl p-4 w-48 shadow-sm ${colors}`}>
      <div className={`p-2 rounded-lg bg-slate-100 ${status === 'active' ? 'bg-blue-100' : ''}`}>
        <Icon className={`w-5 h-5 ${iconColor}`} />
      </div>
      <div>
        <div className="font-semibold text-sm">{name}</div>
        <div className="text-xs text-slate-500 font-mono mt-0.5 truncate w-24">{sub}</div>
      </div>
    </div>
  );
}

function DagEdge() {
  return <div className="h-0.5 w-12 bg-slate-300 flex-shrink-0"></div>;
}

function LogLine({ time, level, text, color = "text-slate-300" }: { time: string, level: string, text: string, color?: string }) {
  let levelColor = "text-blue-400";
  if (level === "WARN") levelColor = "text-amber-400";
  if (level === "ERROR") levelColor = "text-red-400";
  
  return (
    <div className="flex gap-4">
      <span className="text-slate-500">{time}</span>
      <span className={`w-10 ${levelColor}`}>{level}</span>
      <span className={color}>{text}</span>
    </div>
  );
}

function RunRow({ id, time, records, status }: { id: string, time: string, records: string, status: string }) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-5 py-3 font-mono text-xs text-slate-700">{id}</td>
      <td className="px-5 py-3 text-slate-500 text-xs">{time}</td>
      <td className="px-5 py-3 text-right font-mono text-xs font-medium text-navy-900">{records}</td>
      <td className="px-5 py-3">
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
          status === 'Success' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
        }`}>
          {status}
        </span>
      </td>
    </tr>
  );
}
