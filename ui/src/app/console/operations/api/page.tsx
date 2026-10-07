"use client";

import { Terminal, Send, Check } from "lucide-react";

export default function ApiPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">API / Control Plane</h1>
        <p className="text-sm text-slate-500 mt-1">FastAPI developer interface for programmatic pipeline control</p>
      </div>

      <div className="flex h-[700px] bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        {/* Left Nav */}
        <div className="w-64 border-r border-slate-200 bg-slate-50">
          <div className="p-4 border-b border-slate-200 font-semibold text-sm text-navy-900">
            Endpoints
          </div>
          <nav className="p-2 space-y-1">
            <EndpointLink method="GET" path="/health" />
            <EndpointLink method="POST" path="/ingestion/run" />
            <EndpointLink method="GET" path="/runs/:id" />
            <EndpointLink method="POST" path="/backfill" active />
            <EndpointLink method="GET" path="/quality/latest" />
            <EndpointLink method="POST" path="/dlq/replay" />
          </nav>
        </div>

        {/* Right Content */}
        <div className="flex-1 flex flex-col">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center bg-white">
            <div className="flex items-center gap-3 font-mono">
              <span className="bg-blue-100 text-blue-700 font-bold px-2 py-1 rounded text-sm">POST</span>
              <span className="text-lg text-navy-900 font-semibold">/backfill</span>
            </div>
            <button className="flex items-center gap-2 bg-navy-900 text-white px-4 py-2 rounded text-sm font-medium hover:bg-navy-800">
              <Send className="w-4 h-4" />
              Test Endpoint
            </button>
          </div>

          <div className="p-6 overflow-y-auto bg-white flex-1 space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-navy-900 mb-2">Description</h3>
              <p className="text-sm text-slate-600">Triggers an idempotent historical backfill job for a given dataset and date range. The operation is asynchronous and returns a Run ID for tracking.</p>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-navy-900 mb-2">Request Body <span className="text-xs font-normal text-slate-500 ml-2">application/json</span></h3>
              <pre className="bg-slate-900 text-slate-300 p-4 rounded-xl text-sm font-mono overflow-x-auto border border-slate-800">
{`{
  "table": "meter_readings",
  "start_date": "2020-01-01",
  "end_date": "2020-12-31"
}`}
              </pre>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-navy-900 mb-2">Response <span className="text-xs font-normal text-slate-500 ml-2">200 OK</span></h3>
              <pre className="bg-slate-900 text-slate-300 p-4 rounded-xl text-sm font-mono overflow-x-auto border border-slate-800">
{`{
  "run_id": "bf_48a9b21f-8c31-4d92-9e1b",
  "status": "STARTED",
  "message": "Backfill queued"
}`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EndpointLink({ method, path, active }: { method: string, path: string, active?: boolean }) {
  let methodColor = "text-slate-500";
  if (method === "GET") methodColor = "text-emerald-600";
  if (method === "POST") methodColor = "text-blue-600";

  return (
    <div className={`px-3 py-2 rounded-md text-sm font-mono cursor-pointer flex gap-3 ${active ? 'bg-white shadow-sm border border-slate-200' : 'hover:bg-slate-100 border border-transparent'}`}>
      <span className={`w-10 font-bold ${methodColor}`}>{method}</span>
      <span className={`${active ? 'text-navy-900 font-semibold' : 'text-slate-600'}`}>{path}</span>
    </div>
  );
}
