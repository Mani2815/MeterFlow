import { Bell, User, CheckCircle2, Cloud } from "lucide-react";

export function Topnav() {
  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="bg-slate-100 text-slate-700 text-xs font-mono font-bold px-2 py-1 rounded border border-slate-200">
            DEV
          </span>
          <div className="flex items-center gap-1 text-xs text-slate-500 font-medium">
            <Cloud className="w-3 h-3" />
            us-central1
          </div>
        </div>
        <div className="h-4 w-px bg-slate-300"></div>
        <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600">
          <CheckCircle2 className="w-4 h-4" />
          Platform Healthy
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative cursor-pointer text-slate-500 hover:text-slate-700">
          <Bell className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        </div>
        <div className="h-8 w-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  );
}
