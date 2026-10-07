import React, { useState } from 'react';
import { Database, Server, Cloud, ShieldCheck, ArrowRight, XCircle } from 'lucide-react';

type NodeId = 'source' | 'api' | 'postgres' | 'datastream' | 'gcs' | 'pubsub' | 'dataflow' | 'bigquery' | 'dlq' | 'analytics';

export function ArchitectureSection() {
  const [activeNode, setActiveNode] = useState<NodeId | null>(null);

  const nodeInfo: Record<NodeId, string> = {
    source: "Operational utility databases generating real-time transactions.",
    api: "REST API endpoints capturing external meter events.",
    postgres: "Operational Control Plane database for pipeline metadata and states.",
    datastream: "Serverless Change Data Capture (CDC) replicating PostgreSQL WAL to Cloud Storage.",
    gcs: "Durable raw/landing layer preserving source data for replay and backfills.",
    pubsub: "Decouples event notification from downstream processing.",
    dataflow: "Processes, validates, deduplicates and enriches incoming records using Apache Beam.",
    bigquery: "Analytical warehouse containing dimensional utility data models.",
    dlq: "Dead Letter Queue safely isolating malformed records for inspection and API-driven replay.",
    analytics: "BI tools and internal dashboards serving business users.",
  };

  return (
    <section className="py-24 px-6 max-w-6xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight">How the Platform Works</h2>
        <p className="mt-4 text-slate-600 text-lg">A cloud-native pipeline from operational systems to analytical intelligence.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-12 items-center">
        {/* Architecture Diagram */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-8 shadow-sm font-mono text-xs text-center relative">
          
          <div className="flex justify-center mb-8">
            <ArchNode id="source" label="SOURCE SYSTEMS" active={activeNode} onHover={setActiveNode} />
          </div>

          <div className="flex justify-center gap-16 mb-8 relative">
            <ArchNode id="api" label="REST APIs" active={activeNode} onHover={setActiveNode} />
            <ArchNode id="postgres" label="PostgreSQL" active={activeNode} onHover={setActiveNode} />
            
            {/* Connecting lines */}
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 50% 0 L 25% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
              <path d="M 50% 0 L 75% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
            </svg>
          </div>

          <div className="flex justify-center gap-16 mb-8 relative">
            <div className="w-[120px] invisible"></div> {/* Spacer for API side */}
            <ArchNode id="datastream" label="Datastream" active={activeNode} onHover={setActiveNode} />
            
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 75% 0 L 75% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
            </svg>
          </div>

          <div className="flex justify-center mb-8 relative">
            <ArchNode id="gcs" label="Cloud Storage" active={activeNode} onHover={setActiveNode} />
            
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 25% 0 L 50% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
              <path d="M 75% 0 L 50% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
            </svg>
          </div>

          <div className="flex justify-center mb-8 relative">
            <ArchNode id="pubsub" label="Pub/Sub" active={activeNode} onHover={setActiveNode} />
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 50% 0 L 50% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
            </svg>
          </div>

          <div className="flex justify-center mb-8 relative">
            <ArchNode id="dataflow" label="Dataflow" active={activeNode} onHover={setActiveNode} />
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 50% 0 L 50% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
            </svg>
          </div>

          <div className="flex justify-center gap-16 mb-8 relative">
            <ArchNode id="bigquery" label="BigQuery (Valid)" active={activeNode} onHover={setActiveNode} highlightColor="bg-emerald-50 border-emerald-300 text-emerald-800" />
            <ArchNode id="dlq" label="DLQ (Invalid)" active={activeNode} onHover={setActiveNode} highlightColor="bg-red-50 border-red-300 text-red-800" />
            
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 50% 0 L 25% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
              <path d="M 50% 0 L 75% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" strokeDasharray="4 4" />
            </svg>
          </div>

          <div className="flex justify-center gap-16 mb-8 relative">
            <ArchNode id="analytics" label="Analytics" active={activeNode} onHover={setActiveNode} />
            <div className="w-[120px] text-[10px] text-slate-400 font-sans border border-dashed border-slate-300 rounded flex flex-col items-center justify-center p-2 cursor-not-allowed">
               API Replay →
            </div>
            
            <svg className="absolute top-[-32px] w-full h-8 pointer-events-none" style={{ zIndex: 0 }}>
              <path d="M 25% 0 L 25% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" />
              <path d="M 75% 0 L 75% 32" fill="none" stroke="#e2e8f0" strokeWidth="2" strokeDasharray="4 4" />
            </svg>
          </div>

        </div>

        {/* Info Panel */}
        <div className="bg-navy-900 text-white rounded-2xl p-8 h-full flex flex-col justify-center shadow-lg">
          {activeNode ? (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="text-accent-blue font-mono text-xs font-bold tracking-widest uppercase mb-2">Component Detail</div>
              <h3 className="text-2xl font-bold mb-4">{document.getElementById(`node-${activeNode}`)?.innerText || activeNode}</h3>
              <p className="text-slate-300 leading-relaxed text-lg">{nodeInfo[activeNode]}</p>
            </div>
          ) : (
            <div className="text-center text-slate-400">
              <Server className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Hover over any component in the architecture diagram to see how it fits into the platform.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ArchNode({ id, label, active, onHover, highlightColor = 'bg-blue-50 border-blue-400 text-blue-900 shadow-md' }: { id: NodeId, label: string, active: NodeId | null, onHover: (id: NodeId | null) => void, highlightColor?: string }) {
  const isActive = active === id;
  return (
    <div 
      id={`node-${id}`}
      onMouseEnter={() => onHover(id)}
      onMouseLeave={() => onHover(null)}
      className={`w-[140px] px-2 py-3 rounded-lg border-2 font-bold cursor-help transition-all duration-300 z-10 ${
        isActive ? highlightColor + ' scale-110' : 'bg-white border-slate-300 text-slate-700 hover:border-slate-400'
      }`}
    >
      {label}
    </div>
  );
}
