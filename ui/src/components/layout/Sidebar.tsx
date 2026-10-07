"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  GitMerge, 
  Database, 
  ShieldCheck,
  History,
  Archive,
  BarChart3,
  Settings,
  Activity,
  Terminal,
  PlayCircle,
  DatabaseBackup,
  Layers,
  ServerCog
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Overview", href: "/console", icon: LayoutDashboard },
  { label: "Pipelines", icon: GitMerge, children: [
    { label: "All Pipelines", href: "/console/pipelines" },
    { label: "Runs", href: "/console/pipelines/runs" },
  ]},
  { label: "Data", icon: Database, children: [
    { label: "Sources", href: "/console/data/sources" },
    { label: "CDC / Events", href: "/console/data/cdc" },
    { label: "Data Quality", href: "/console/data/quality" },
    { label: "DLQ / Replay", href: "/console/data/dlq" },
    { label: "Backfills", href: "/console/data/backfills" },
  ]},
  { label: "Warehouse", icon: Archive, children: [
    { label: "Explorer", href: "/console/warehouse/explorer" },
    { label: "Data Model", href: "/console/warehouse/model" },
  ]},
  { label: "Business", icon: BarChart3, children: [
    { label: "Meter-to-Cash", href: "/console/business/meter-to-cash" },
    { label: "Analytics", href: "/console/business/analytics" },
  ]},
  { label: "Operations", icon: ServerCog, children: [
    { label: "Monitoring", href: "/console/operations/monitoring" },
    { label: "API / Control Plane", href: "/console/operations/api" },
  ]},
  { label: "Settings", href: "/console/settings", icon: Settings }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-slate-200 h-screen flex flex-col flex-shrink-0">
      <div className="h-14 flex items-center px-4 border-b border-slate-200">
        <div className="flex items-center gap-2 text-navy-900 font-bold text-sm tracking-tight">
          <DatabaseBackup className="w-5 h-5 text-accent-blue" />
          METER-TO-CASH
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
          {NAV_ITEMS.map((item) => (
            <div key={item.label}>
              {item.href ? (
                <Link 
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                    pathname === item.href 
                      ? "bg-slate-100 text-accent-blue" 
                      : "text-slate-600 hover:bg-slate-50 hover:text-navy-900"
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              ) : (
                <div className="mt-4 mb-1">
                  <div className="px-3 py-1 flex items-center gap-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </div>
                  <div className="space-y-1 mt-1">
                    {item.children?.map(child => (
                      <Link
                        key={child.label}
                        href={child.href}
                        className={cn(
                          "flex items-center pl-10 pr-3 py-1.5 text-sm font-medium rounded-md transition-colors",
                          pathname === child.href 
                            ? "bg-slate-100 text-accent-blue" 
                            : "text-slate-600 hover:bg-slate-50 hover:text-navy-900"
                        )}
                      >
                        {child.label}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
}
