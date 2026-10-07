"use client";

import { useState, useEffect } from "react";
import { Database, FileLineChart, Users, MapPin, Calendar, CreditCard, Activity } from "lucide-react";
import { api } from "@/lib/api/client";

export default function DataModelPage() {
  const [rowCount, setRowCount] = useState<string>("Not available");

  useEffect(() => {
    async function load() {
      try {
        const stats = await api.analytics.getGoldStats();
        if (stats && stats.total_rows !== undefined) {
          setRowCount(stats.total_rows.toLocaleString());
        }
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, []);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Core Data Model</h1>
        <p className="text-sm text-slate-500 mt-1">Interactive Star Schema visualization for Meter-to-Cash</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm h-[700px] relative overflow-hidden flex items-center justify-center bg-slate-50/50">
        
        {/* Central Fact */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
          <ModelNode title="fact_consumption" type="Fact" icon={Activity} color="border-emerald-400 bg-emerald-50 text-emerald-900" />
        </div>

        {/* Top Dimensions */}
        <div className="absolute top-[15%] left-1/2 transform -translate-x-1/2">
          <ModelNode title="dim_customer" type="Dimension" icon={Users} color="border-blue-300 bg-white" />
        </div>
        <div className="absolute top-[30%] left-[25%] transform -translate-x-1/2">
          <ModelNode title="dim_account" type="Dimension" icon={FileLineChart} color="border-blue-300 bg-white" />
        </div>
        
        {/* Side Dimensions */}
        <div className="absolute top-1/2 left-[15%] transform -translate-x-1/2 -translate-y-1/2">
          <ModelNode title="dim_meter" type="Dimension" icon={Database} color="border-blue-300 bg-white" />
        </div>
        <div className="absolute top-1/2 right-[15%] transform translate-x-1/2 -translate-y-1/2">
          <ModelNode title="dim_date" type="Dimension" icon={Calendar} color="border-blue-300 bg-white" />
        </div>

        {/* Bottom Dimensions */}
        <div className="absolute bottom-[20%] left-1/2 transform -translate-x-1/2">
          <ModelNode title="dim_location" type="Dimension" icon={MapPin} color="border-blue-300 bg-white" />
        </div>
        
        {/* Connecting Lines (Simulated SVG) */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
          <line x1="50%" y1="15%" x2="50%" y2="50%" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="25%" y1="30%" x2="50%" y2="50%" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="15%" y1="50%" x2="50%" y2="50%" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="85%" y1="50%" x2="50%" y2="50%" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
          <line x1="50%" y1="80%" x2="50%" y2="50%" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
        </svg>

        <div className="absolute bottom-6 right-6 bg-white p-4 rounded-xl border border-slate-200 shadow-lg w-72 z-20">
          <h3 className="text-sm font-bold text-navy-900 mb-2 border-b border-slate-100 pb-2">fact_consumption</h3>
          <p className="text-xs text-slate-600 mb-3">Grain: One row per meter per billing period.</p>
          <div className="space-y-1 text-xs font-mono text-slate-500">
            <div><span className="text-accent-blue">SK:</span> consumption_sk</div>
            <div><span className="text-amber-500">FK:</span> meter_sk</div>
            <div><span className="text-amber-500">FK:</span> account_sk</div>
            <div><span className="text-amber-500">FK:</span> date_sk</div>
          </div>
          <div className="mt-3 pt-2 border-t border-slate-100 text-xs font-medium text-navy-900">
            Rows: {rowCount}
          </div>
        </div>

      </div>
    </div>
  );
}

function ModelNode({ title, type, icon: Icon, color }: { title: string, type: string, icon: any, color: string }) {
  return (
    <div className={`w-48 p-3 rounded-xl border-2 shadow-sm flex items-center gap-3 cursor-pointer hover:shadow-md transition-shadow ${color}`}>
      <div className="p-2 bg-white/50 rounded-lg">
        <Icon className="w-5 h-5 opacity-80" />
      </div>
      <div>
        <div className="font-mono text-xs font-bold truncate">{title}</div>
        <div className="text-[10px] uppercase tracking-wider font-semibold opacity-70">{type}</div>
      </div>
    </div>
  );
}
