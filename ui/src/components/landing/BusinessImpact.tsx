import React from 'react';
import { ArrowDown, TrendingUp, Receipt, CreditCard, Map } from 'lucide-react';

export function BusinessImpact() {
  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight">One Platform. One View of Meter-to-Cash.</h2>
        <p className="mt-4 text-slate-600 text-lg">
          The platform transforms fragmented operational data into a consistent analytical foundation for utility decision-making.
        </p>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-12 mb-16">
        <Node text="Meters" />
        <ArrowDown className="md:-rotate-90 text-slate-300 w-6 h-6" />
        <Node text="Consumption" />
        <ArrowDown className="md:-rotate-90 text-slate-300 w-6 h-6" />
        <Node text="Billing" />
        <ArrowDown className="md:-rotate-90 text-slate-300 w-6 h-6" />
        <Node text="Payments" />
        <ArrowDown className="md:-rotate-90 text-slate-300 w-6 h-6" />
        <div className="px-6 py-3 bg-navy-900 text-white font-bold rounded-lg shadow-lg">
          Utility Intelligence
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard icon={TrendingUp} title="Consumption Trends" desc="Forecast load and analyze daily usage patterns per service point." />
        <MetricCard icon={Receipt} title="Billing Performance" desc="Reconcile expected physical consumption against issued financial invoices." />
        <MetricCard icon={CreditCard} title="Payment Collection" desc="Track outstanding balances and optimize collection analytics." />
        <MetricCard icon={Map} title="Regional Usage" desc="Perform spatial analytics on usage distributed across zip codes and cities." />
      </div>

    </section>
  );
}

function Node({ text }: { text: string }) {
  return (
    <div className="px-6 py-3 bg-white border border-slate-200 text-slate-700 font-bold rounded-lg shadow-sm">
      {text}
    </div>
  );
}

function MetricCard({ icon: Icon, title, desc }: any) {
  return (
    <div className="bg-slate-50 border border-slate-200 p-6 rounded-xl text-center flex flex-col items-center">
      <div className="p-3 bg-white border border-slate-200 rounded-full mb-4 text-accent-blue shadow-sm">
        <Icon className="w-6 h-6" />
      </div>
      <h4 className="font-bold text-navy-900 mb-2">{title}</h4>
      <p className="text-sm text-slate-600">{desc}</p>
    </div>
  );
}
