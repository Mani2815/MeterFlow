import React, { useState, useEffect } from 'react';
import { Database, Activity, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';

export function DataJourney() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      title: "A reading is generated",
      content: (
        <pre className="text-xs text-emerald-400 bg-slate-900 p-4 rounded-lg">
MTR-20841{'\n'}
2026-10-06 10:42:31{'\n'}
consumption_kwh: 4.82
        </pre>
      )
    },
    {
      title: "The event is ingested",
      content: (
        <div className="flex flex-col items-center gap-2 text-sm font-mono text-slate-300">
          <div className="bg-slate-800 px-4 py-2 rounded border border-slate-700">PostgreSQL / API</div>
          <ArrowRight className="rotate-90 text-slate-500" />
          <div className="bg-slate-800 px-4 py-2 rounded border border-slate-700">Cloud Storage</div>
        </div>
      )
    },
    {
      title: "The change is distributed",
      content: (
        <div className="bg-blue-900/30 border border-blue-500/30 text-blue-300 px-6 py-4 rounded-lg text-center font-bold font-mono tracking-widest">
          PUB/SUB TOPIC
        </div>
      )
    },
    {
      title: "The data is processed",
      content: (
        <div className="flex gap-2 justify-center flex-wrap">
          {['Parse', 'Validate', 'Deduplicate', 'Enrich', 'Normalize'].map(t => (
            <span key={t} className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-mono">{t}</span>
          ))}
        </div>
      )
    },
    {
      title: "Quality is checked",
      content: (
        <div className="space-y-2 text-sm font-mono text-emerald-400">
          <div><CheckCircle2 className="w-4 h-4 inline mr-2" />meter_id present</div>
          <div><CheckCircle2 className="w-4 h-4 inline mr-2" />timestamp valid</div>
          <div><CheckCircle2 className="w-4 h-4 inline mr-2" />consumption valid</div>
          <div><CheckCircle2 className="w-4 h-4 inline mr-2" />duplicate check passed</div>
        </div>
      )
    },
    {
      title: "The warehouse is updated",
      content: (
        <div className="flex items-center gap-4 bg-slate-800 p-4 rounded-lg border border-slate-700">
          <Database className="text-accent-blue" />
          <span className="font-mono text-white font-bold">fact_meter_reading</span>
        </div>
      )
    },
    {
      title: "Business analytics are updated",
      content: (
        <div className="grid grid-cols-2 gap-2 text-center text-xs font-bold text-slate-300 uppercase tracking-widest">
          <div className="bg-slate-800 py-2 rounded border border-slate-700">Daily Consumption</div>
          <div className="bg-slate-800 py-2 rounded border border-slate-700">Billing</div>
          <div className="bg-slate-800 py-2 rounded border border-slate-700">Payments</div>
          <div className="bg-slate-800 py-2 rounded border border-slate-700">Regional Usage</div>
        </div>
      )
    }
  ];

  // A simple IntersectionObserver-like logic based on scroll to update active step
  useEffect(() => {
    const handleScroll = () => {
      const container = document.getElementById('journey-container');
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const scrollPercent = Math.max(0, Math.min(1, Math.abs(rect.top) / (rect.height - window.innerHeight)));
      
      if (rect.top <= window.innerHeight / 2 && rect.bottom >= window.innerHeight / 2) {
        const step = Math.floor(scrollPercent * steps.length);
        setActiveStep(Math.min(step, steps.length - 1));
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <section className="py-24 bg-white" id="journey-container">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-navy-900 tracking-tight">Follow a Meter Reading Through the Platform</h2>
          <p className="mt-4 text-slate-600 text-lg">Scroll to see how a single data event is transformed into business value.</p>
        </div>

        <div className="flex flex-col md:flex-row gap-12 relative min-h-[800px]">
          
          {/* Scroll Steps (Left) */}
          <div className="w-full md:w-1/2 flex flex-col justify-between py-12 relative">
            <div className="absolute left-6 top-16 bottom-16 w-1 bg-slate-100 rounded-full"></div>
            {steps.map((step, idx) => (
              <div 
                key={idx} 
                className={`pl-16 relative py-4 transition-all duration-500 ${activeStep === idx ? 'opacity-100 scale-105' : 'opacity-30'}`}
              >
                <div className={`absolute left-[20px] top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-4 transition-colors ${activeStep === idx ? 'bg-accent-blue border-blue-200' : 'bg-slate-300 border-white'}`}></div>
                <div className="text-xs font-bold text-accent-blue tracking-widest uppercase mb-1">Step {idx + 1}</div>
                <h3 className="text-xl font-bold text-navy-900">{step.title}</h3>
              </div>
            ))}
          </div>

          {/* Sticky Visualizer (Right) */}
          <div className="w-full md:w-1/2 relative">
            <div className="sticky top-32 bg-slate-950 rounded-2xl p-8 min-h-[400px] flex flex-col justify-center shadow-2xl border border-slate-800 overflow-hidden">
               {/* Terminal styling */}
               <div className="absolute top-0 left-0 w-full h-8 bg-slate-900 border-b border-slate-800 flex items-center px-4 gap-2">
                 <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50"></div>
                 <div className="w-2.5 h-2.5 rounded-full bg-amber-500/20 border border-amber-500/50"></div>
                 <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50"></div>
               </div>
               
               <div className="pt-8">
                 {steps.map((step, idx) => (
                    <div 
                      key={idx}
                      className={`transition-all duration-500 absolute left-8 right-8 top-1/2 -translate-y-1/2 ${
                        activeStep === idx ? 'opacity-100 translate-y-0 visible' : 
                        activeStep > idx ? 'opacity-0 -translate-y-8 invisible' : 'opacity-0 translate-y-8 invisible'
                      }`}
                    >
                      {step.content}
                    </div>
                 ))}
               </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
