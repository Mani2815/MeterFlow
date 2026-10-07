"use client";

import { useEffect, useState } from "react";
import { Users, Droplet, Receipt, CreditCard, FileText, Home } from "lucide-react";

import { api } from "@/lib/api/client";

export default function MeterToCashPage() {
  const [metrics, setMetrics] = useState({
    customers: "--",
    accounts: "--",
    contracts: "--",
    servicePoints: "--",
    meters: "--"
  });

  useEffect(() => {
    async function fetchMasterData() {
      try {
        const [custs, accs, ctrs, sps, mtrs] = await Promise.all([
          api.masterData.getCustomers(),
          api.masterData.getAccounts(),
          api.masterData.getContracts(),
          api.masterData.getServicePoints(),
          api.masterData.getMeters()
        ]);

        setMetrics({
          customers: custs.length?.toString() || "0",
          accounts: accs.length?.toString() || "0",
          contracts: ctrs.length?.toString() || "0",
          servicePoints: sps.length?.toString() || "0",
          meters: mtrs.length?.toString() || "0"
        });
      } catch (err) {
        console.error("Failed to fetch master data", err);
      }
    }
    fetchMasterData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Meter-to-Cash Business Overview</h1>
        <p className="text-sm text-slate-500 mt-1">High-level financial and operational metrics</p>
      </div>

      {/* SYNTHETIC MASTER DATA LABEL */}
      <div className="bg-blue-50 border border-blue-200 text-blue-700 p-4 rounded-xl text-sm font-medium flex items-center">
        ENVIRONMENT: Synthetic Utility Master Data (Simulation). These entities are deterministically generated and do not represent real UKPN customer information.
      </div>

      {/* Business Flow Visualization */}
      <div className="flex justify-between items-center bg-white border border-slate-200 rounded-xl p-6 shadow-sm overflow-x-auto">
        <FlowStep icon={Users} label="Customers" value={metrics.customers} />
        <FlowArrow />
        <FlowStep icon={FileText} label="Contracts" value={metrics.contracts} />
        <FlowArrow />
        <FlowStep icon={Home} label="Service Points" value={metrics.servicePoints} />
        <FlowArrow />
        <FlowStep icon={Droplet} label="Meters" value={metrics.meters} />
      </div>

      {/* BILLING FIXTURE WARNING */}
      <div className="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-xl text-sm font-medium flex items-center mt-6">
        PHASE 12 (BILLING ENGINE) is pending. Financial metrics and billing workflows are currently unavailable.
      </div>

      <div className="bg-slate-50 border border-slate-200 text-slate-500 p-8 rounded-xl text-center shadow-sm">
        <h3 className="text-lg font-medium text-navy-900 mb-2">Billing engine not implemented</h3>
        <p className="text-sm">The underlying financial models and rating engine required to compute billed and collected revenue do not exist in this demo.</p>
      </div>


    </div>
  );
}

function FlowStep({ icon: Icon, label, value, highlight }: { icon: any, label: string, value: string, highlight?: boolean }) {
  return (
    <div className={`flex flex-col items-center justify-center p-4 min-w-[140px] rounded-xl ${highlight ? 'bg-blue-50 border border-blue-200' : ''}`}>
      <div className={`p-3 rounded-full mb-3 ${highlight ? 'bg-accent-blue text-white' : 'bg-slate-100 text-slate-500'}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</div>
      <div className={`text-xl font-bold font-mono mt-1 ${highlight ? 'text-accent-blue' : 'text-navy-900'}`}>{value}</div>
    </div>
  );
}

function FlowArrow() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="h-0.5 w-full bg-slate-200 mx-4 relative">
        <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-2 h-2 border-t-2 border-r-2 border-slate-300 rotate-45"></div>
      </div>
    </div>
  );
}


