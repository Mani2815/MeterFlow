import React from 'react';
import { Check } from 'lucide-react';

export function CredibilitySection() {
  const characteristics = [
    "Incremental ingestion",
    "CDC (Change Data Capture)",
    "Data quality validation",
    "Idempotent processing",
    "DLQ + replay",
    "Isolated backfills",
    "Schema evolution handling",
    "Dimensional modeling",
    "Serverless cloud deployment",
    "Pipeline observability"
  ];

  return (
    <section className="py-24 px-6 max-w-5xl mx-auto border-t border-slate-200">
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-12 text-center">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight mb-4">Built as an End-to-End Data Engineering System</h2>
        <p className="text-slate-600 text-lg mb-12 max-w-2xl mx-auto">
          This platform was engineered to satisfy strict, production-grade requirements for data reliability, scalability, and operational observability.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-y-6 gap-x-4 text-left">
          {characteristics.map((char, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <Check className="w-5 h-5 text-emerald-500 shrink-0" />
              <span className="text-sm font-bold text-slate-700 leading-tight">{char}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
