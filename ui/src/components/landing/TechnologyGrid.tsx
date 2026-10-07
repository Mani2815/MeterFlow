import React, { useState } from 'react';
import { Cloud, Server, Database, Code2, Activity, PlaySquare, Terminal, HardDrive, Network, Waves, RefreshCw, Cpu, Workflow } from 'lucide-react';

export function TechnologyGrid() {
  const [activeTech, setActiveTech] = useState<string | null>(null);

  const technologies = [
    { id: 'python', icon: Terminal, name: 'Python', role: 'Core Logic & Orchestration', why: 'Industry standard for data engineering. Powers our FastAPI control plane and Airflow DAGs.', usedFor: 'Backend API, DAGs, Scripts' },
    { id: 'sql', icon: Database, name: 'SQL', role: 'Data Transformation', why: 'Idempotent, readable, and highly optimized for analytical processing within BigQuery.', usedFor: 'MERGE statements, Validations' },
    { id: 'gcs', icon: HardDrive, name: 'Cloud Storage', role: 'Data Lake Landing Zone', why: 'Cheap, durable object storage providing an immutable historical record before processing.', usedFor: 'Raw event storage, Backfill source' },
    { id: 'pubsub', icon: Network, name: 'Pub/Sub', role: 'Message Broker', why: 'Provides massive scalability and decoupled shock-absorption for bursty utility meter events.', usedFor: 'Event streaming, Decoupling' },
    { id: 'dataflow', icon: Waves, name: 'Dataflow', role: 'Distributed Data Processing', why: 'Exactly-once semantics and serverless scaling for validating and enriching incoming data in real-time.', usedFor: 'Parsing, Validation, DLQ Routing' },
    { id: 'datastream', icon: RefreshCw, name: 'Datastream', role: 'Change Data Capture (CDC)', why: 'Replicates transactional databases to the data platform without placing load on operational systems.', usedFor: 'Log tailing, Incremental ingest' },
    { id: 'bigquery', icon: Database, name: 'BigQuery', role: 'Analytical Data Warehouse', why: 'Petabyte-scale, serverless OLAP database optimized for star schemas and dimensional querying.', usedFor: 'Core Facts, Dimensions, Analytics' },
    { id: 'cloudrun', icon: Cpu, name: 'Cloud Run', role: 'Serverless Compute', why: 'Scales our operational control plane to zero when idle, but handles immense burst traffic.', usedFor: 'Control Plane API Hosting' },
    { id: 'airflow', icon: Workflow, name: 'Airflow', role: 'Batch Orchestration', why: 'Robust DAG execution with native dependency management, retries, and alerting.', usedFor: 'Daily Batch, Backfill orchestration' },
    { id: 'postgres', icon: Server, name: 'PostgreSQL', role: 'Operational Database', why: 'ACID-compliant transactional store for managing pipeline state, not analytical data.', usedFor: 'Pipeline Metadata, DLQ State' },
  ];

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto border-t border-slate-800">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-white tracking-tight">Why These Technologies?</h2>
        <p className="mt-4 text-slate-400 text-lg">Every component in the architecture was selected to maximize reliability and developer velocity.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-12">
        
        {/* Tech Grid */}
        <div className="w-full lg:w-3/5 grid grid-cols-2 md:grid-cols-3 gap-4">
          {technologies.map(tech => (
            <div 
              key={tech.id}
              onClick={() => setActiveTech(tech.id)}
              className={`px-4 py-4 rounded-xl border flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-300 ${
                activeTech === tech.id ? 'bg-blue-900/50 border-accent-blue shadow-[0_0_15px_rgba(37,99,235,0.3)]' : 
                'bg-slate-800 border-slate-700 hover:border-slate-500'
              }`}
            >
              <tech.icon className={`w-6 h-6 ${activeTech === tech.id ? 'text-accent-blue' : 'text-slate-400'}`} />
              <div className={`font-bold ${activeTech === tech.id ? 'text-white' : 'text-slate-300'}`}>{tech.name}</div>
            </div>
          ))}
        </div>

        {/* Tech Details Panel */}
        <div className="w-full lg:w-2/5 bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-xl min-h-[350px]">
          {activeTech ? (
            <div className="animate-in fade-in duration-200">
              <div className="text-xs font-bold text-accent-blue tracking-widest uppercase mb-1">Technology</div>
              <h3 className="text-3xl font-bold text-white mb-6">{technologies.find(t => t.id === activeTech)?.name}</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Role</div>
                  <p className="text-slate-200">{technologies.find(t => t.id === activeTech)?.role}</p>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Why We Chose It</div>
                  <p className="text-slate-200 leading-relaxed">{technologies.find(t => t.id === activeTech)?.why}</p>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Used For</div>
                  <div className="inline-block bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-md text-sm text-emerald-400 font-mono">
                    {technologies.find(t => t.id === activeTech)?.usedFor}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
              <Cloud className="w-12 h-12 mb-4 opacity-50" />
              <p>Select a technology from the grid to understand its specific architectural role.</p>
            </div>
          )}
        </div>

      </div>
    </section>
  );
}
