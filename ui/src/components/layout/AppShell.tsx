import { Sidebar } from "./Sidebar";
import { Topnav } from "./Topnav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topnav />
        {process.env.NEXT_PUBLIC_DATA_MODE === "demo" && (
          <div className="bg-amber-100 text-amber-800 text-xs font-medium py-2 px-4 text-center border-b border-amber-200">
            Demo snapshot generated from validated Gold data
          </div>
        )}
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
