"use client";

import { useState, useEffect } from "react";
import { AlertCircle, RotateCcw, Search, Eye, Loader2 } from "lucide-react";
import { api } from "@/lib/api/client";

export default function DLQPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);
  const [replaying, setReplaying] = useState(false);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      setLoading(true);
      const data = await api.dlq.list();
      setEvents(data);
      if (data.length > 0 && !selectedEvent) {
        setSelectedEvent(data[0]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleReplay() {
    if (!selectedEvent) return;
    try {
      setReplaying(true);
      await api.dlq.replay(selectedEvent.event_id);
      await load();
      alert(`Event ${selectedEvent.event_id} queued for replay.`);
    } catch (err: any) {
      alert(`Replay failed: ${err.message}`);
    } finally {
      setReplaying(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-navy-900">Dead Letter Queue</h1>
          <p className="text-sm text-slate-500 mt-1">Inspect, modify, and replay malformed events</p>
        </div>
        <button 
          disabled={!selectedEvent || replaying}
          onClick={handleReplay}
          className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
        >
          {replaying ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
          Replay Selected
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatusCard label="Pending" value={events.filter(e => e.status === 'PENDING').length.toString()} color="border-l-4 border-l-amber-500" />
        <StatusCard label="Processing" value={events.filter(e => e.status === 'PROCESSING').length.toString()} color="border-l-4 border-l-blue-500" />
        <StatusCard label="Resolved" value={events.filter(e => e.status === 'RESOLVED').length.toString()} color="border-l-4 border-l-emerald-500" />
        <StatusCard label="Failed (Max Retries)" value={events.filter(e => e.status === 'FAILED').length.toString()} color="border-l-4 border-l-red-500" />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex min-h-[600px]">
        {/* Left Table */}
        <div className="w-2/3 border-r border-slate-200 flex flex-col">
          <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/50">
             <div className="relative max-w-sm">
              <Search className="w-4 h-4 absolute left-3 top-2 text-slate-400" />
              <input 
                type="text" 
                placeholder="Search error messages or event IDs..." 
                className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
              />
            </div>
          </div>
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200 sticky top-0">
                <tr>
                  <th className="px-4 py-3 font-medium">Event ID</th>
                  <th className="px-4 py-3 font-medium">Dataset</th>
                  <th className="px-4 py-3 font-medium">Error Type</th>
                  <th className="px-4 py-3 font-medium text-center">Attempts</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {loading && (
                  <tr>
                    <td colSpan={5} className="h-64 text-center">
                      <Loader2 className="w-6 h-6 animate-spin text-accent-blue mx-auto" />
                    </td>
                  </tr>
                )}
                {error && (
                  <tr>
                    <td colSpan={5} className="h-64 text-center text-red-500">
                      Failed to load DLQ events: {error}
                    </td>
                  </tr>
                )}
                {!loading && !error && events.map((evt) => (
                  <tr 
                    key={evt.event_id} 
                    onClick={() => setSelectedEvent(evt)}
                    className={`hover:bg-slate-50 cursor-pointer ${selectedEvent?.event_id === evt.event_id ? 'bg-blue-50/30' : ''}`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-navy-900">{evt.event_id}</td>
                    <td className="px-4 py-3 text-slate-600 font-mono text-xs">{evt.dataset}</td>
                    <td className="px-4 py-3 text-slate-700 truncate max-w-[200px]">{evt.error_message}</td>
                    <td className="px-4 py-3 text-center font-mono text-xs">{evt.attempt_count}</td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        evt.status === 'PENDING' ? 'bg-amber-50 text-amber-600 border-amber-200' :
                        evt.status === 'PROCESSING' ? 'bg-blue-50 text-blue-600 border-blue-200' :
                        'bg-slate-100 text-slate-600 border-slate-200'
                      }`}>
                        {evt.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Detail Pane */}
        <div className="w-1/3 bg-slate-50 p-6 flex flex-col h-[600px] overflow-y-auto">
          {!selectedEvent ? (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
              Select an event to view details
            </div>
          ) : (
            <>
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="font-semibold text-navy-900 font-mono">{selectedEvent.event_id}</h3>
                  <p className="text-xs text-slate-500 mt-1">Created {new Date(selectedEvent.created_at).toLocaleString()} • Source: {selectedEvent.source}</p>
                </div>
                <div className="flex gap-2">
                  <button className="p-1.5 text-slate-400 hover:text-slate-700 bg-white rounded border border-slate-200 shadow-sm"><Eye className="w-4 h-4" /></button>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    {selectedEvent.error_type}
                  </h4>
                  <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg font-medium font-mono">
                    {selectedEvent.error_message}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Payload Reference</h4>
                  <pre className="bg-slate-900 text-slate-300 p-4 rounded-lg text-xs font-mono overflow-x-auto border border-slate-800 shadow-inner">
{selectedEvent.payload_reference}
                  </pre>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Actions</h4>
                  <div className="flex flex-col gap-2">
                    <button 
                      disabled={replaying}
                      onClick={handleReplay}
                      className="w-full bg-navy-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-navy-800 transition-colors disabled:opacity-50"
                    >
                      {replaying ? 'Replaying...' : 'Replay Event'}
                    </button>
                    <button className="w-full bg-white border border-slate-300 text-slate-700 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
                      Mark as Resolved (Ignore)
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusCard({ label, value, color }: { label: string, value: string, color: string }) {
  return (
    <div className={`bg-white border border-slate-200 rounded-xl p-4 shadow-sm ${color}`}>
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</div>
      <div className="mt-1 text-2xl font-bold font-mono text-navy-900">{value}</div>
    </div>
  );
}
