import React, { useState } from 'react';
import { Users, Database, FileText, CreditCard, ArrowRight } from 'lucide-react';

export function ProblemSection() {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  const sources = [
    { id: 'customer', icon: Users, name: 'Customer System', desc: 'Customer, account and service information.' },
    { id: 'meter', icon: Database, name: 'Meter System', desc: 'Meter registrations, readings and telemetry.' },
    { id: 'billing', icon: FileText, name: 'Billing System', desc: 'Consumption, invoices and billing transactions.' },
    { id: 'payment', icon: CreditCard, name: 'Payment System', desc: 'Payments, collections and outstanding balances.' },
  ];

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight">Utility Data Is Distributed Across Systems</h2>
        <p className="mt-4 text-slate-600 text-lg">Operational data exists in silos. To make reliable business decisions, it must be unified into a single analytical foundation.</p>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16">
        
        {/* Source Nodes */}
        <div className="flex flex-col gap-4 w-full md:w-64">
          {sources.map((s) => (
            <div 
              key={s.id}
              onMouseEnter={() => setActiveNode(s.id)}
              onMouseLeave={() => setActiveNode(null)}
              className={`flex items-start gap-4 p-4 rounded-xl border transition-all cursor-default ${
                activeNode === s.id ? 'border-accent-blue bg-blue-50 shadow-md' : 'border-slate-200 bg-white hover:border-slate-300'
              }`}
            >
              <div className={`p-2 rounded-lg ${activeNode === s.id ? 'bg-accent-blue text-white' : 'bg-slate-100 text-slate-600'}`}>
                <s.icon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-navy-900 text-sm">{s.name}</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Connections & Target */}
        <div className="hidden md:flex flex-col items-center justify-center relative w-32 h-64">
          {sources.map((s, idx) => (
            <svg key={s.id} className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: activeNode === s.id ? 10 : 0 }}>
              <path 
                d={`M 0 ${20 + (idx * 75)} C 60 ${20 + (idx * 75)}, 60 128, 128 128`} 
                fill="none" 
                stroke={activeNode === s.id ? '#2563eb' : '#e2e8f0'} 
                strokeWidth={activeNode === s.id ? '3' : '2'}
                strokeDasharray={activeNode === s.id ? '4 4' : 'none'}
                className={activeNode === s.id ? 'animate-[dash_1s_linear_infinite]' : ''}
              />
            </svg>
          ))}
          <style>{`
            @keyframes dash {
              to { stroke-dashoffset: -8; }
            }
          `}</style>
        </div>

        {/* Target Node */}
        <div className={`flex flex-col items-center justify-center p-8 rounded-2xl border-2 transition-all w-full md:w-64 ${
          activeNode ? 'border-accent-blue bg-blue-50 shadow-lg scale-105' : 'border-slate-200 bg-white'
        }`}>
          <Database className={`w-12 h-12 mb-4 ${activeNode ? 'text-accent-blue' : 'text-slate-400'}`} />
          <h3 className="font-bold text-navy-900 text-lg">Data Platform</h3>
          <p className="text-sm text-center text-slate-500 mt-2">Unified Dimensional Warehouse</p>
        </div>

      </div>
    </section>
  );
}
