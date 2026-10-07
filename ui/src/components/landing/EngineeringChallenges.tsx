import React, { useState } from 'react';
import { Settings2, GitBranch, ShieldAlert, AlertOctagon, RotateCcw, Shuffle } from 'lucide-react';

export function EngineeringChallenges() {
  const cards = [
    {
      id: 'incremental',
      icon: Settings2,
      title: 'Incremental Ingestion',
      desc: 'Process new and changed records without repeatedly reprocessing the entire source.',
      problem: 'Full table scans on multi-terabyte datasets cause database lockups and severe cost overhead.',
      approach: 'Idempotent SQL MERGE statements tracking source_updated_at watermarks.',
      result: 'Ingestion time reduced from hours to seconds; costs minimized.'
    },
    {
      id: 'cdc',
      icon: GitBranch,
      title: 'Change Data Capture (CDC)',
      desc: 'Capture INSERT, UPDATE and DELETE changes from operational systems.',
      problem: 'Batch extracts miss intermediate state changes and soft-deletes.',
      approach: 'Google Datastream tailing the PostgreSQL Write-Ahead Log (WAL) into Pub/Sub.',
      result: 'Real-time state propagation without impacting operational database performance.'
    },
    {
      id: 'quality',
      icon: ShieldAlert,
      title: 'Data Quality Validation',
      desc: 'Validate schema, completeness, validity, uniqueness and business rules.',
      problem: 'Garbage in, garbage out. Bad data silently corrupts BI reports.',
      approach: 'Declarative YAML rules validated in-stream by Dataflow before hitting BigQuery.',
      result: '99.9% data reliability; malformed data is halted instantly.'
    },
    {
      id: 'dlq',
      icon: AlertOctagon,
      title: 'Dead-Letter Processing',
      desc: 'Quarantine failed records instead of silently dropping them.',
      problem: 'Failing a pipeline over one bad record halts the company. Dropping it causes data loss.',
      approach: 'Side-outputs in Dataflow route failures to a dedicated BigQuery DLQ table with full JSON payloads preserved.',
      result: 'Pipelines stay green; bad data is safely isolated for inspection.'
    },
    {
      id: 'backfills',
      icon: RotateCcw,
      title: 'Historical Backfills',
      desc: 'Reprocess historical periods safely using isolated, idempotent jobs.',
      problem: 'Backfilling data often creates duplicates or messes up production metrics.',
      approach: 'Isolated backfill_id injected into Airflow context; ROW_NUMBER() window functions enforce deduplication during MERGE.',
      result: 'Risk-free retroactive data correction.'
    },
    {
      id: 'schema',
      icon: Shuffle,
      title: 'Schema Evolution',
      desc: 'Detect and manage compatible and incompatible source changes.',
      problem: 'Upstream engineers adding columns breaks fragile downstream ETLs.',
      approach: 'ALLOW_FIELD_ADDITION enabled for safe changes; destructive changes trapped by strict schema registry in Dataflow.',
      result: 'Zero silent corruption.'
    }
  ];

  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-white tracking-tight">Built Around Real Data Engineering Problems</h2>
        <p className="mt-4 text-slate-400 text-lg">We didn't just build a happy path. The platform is designed for failure, evolution, and scale.</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map(c => (
          <div 
            key={c.id} 
            className="bg-slate-800 border border-slate-700 rounded-xl p-6 cursor-pointer hover:border-accent-blue transition-all group"
            onClick={() => setExpanded(expanded === c.id ? null : c.id)}
            onMouseLeave={() => setExpanded(null)}
          >
            <c.icon className="w-8 h-8 text-accent-blue mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-lg font-bold text-white mb-2">{c.title}</h3>
            
            <div className={`text-slate-400 text-sm overflow-hidden transition-all duration-300 ${expanded === c.id ? 'h-0 opacity-0 mb-0' : 'h-16 opacity-100 mb-4'}`}>
              {c.desc}
            </div>

            <div className={`overflow-hidden transition-all duration-300 flex flex-col gap-3 ${expanded === c.id ? 'max-h-96 opacity-100 mt-4' : 'max-h-0 opacity-0'}`}>
              <div>
                <span className="text-xs font-bold text-red-400 uppercase tracking-wider block mb-1">Problem</span>
                <p className="text-sm text-slate-300">{c.problem}</p>
              </div>
              <div>
                <span className="text-xs font-bold text-blue-400 uppercase tracking-wider block mb-1">Approach</span>
                <p className="text-sm text-slate-300">{c.approach}</p>
              </div>
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block mb-1">Result</span>
                <p className="text-sm text-slate-300">{c.result}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
