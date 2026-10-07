import React, { useState } from 'react';
import { ShieldAlert, ArrowRight, CheckCircle2, RotateCcw } from 'lucide-react';

export function DataQualityDemo() {
  const [step, setStep] = useState(0); 
  // 0: Initial, 1: Invalid Detected, 2: Routed to DLQ, 3: Replay Success

  return (
    <section className="py-24 px-6 bg-slate-50 border-t border-slate-200">
      <div className="max-w-5xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-navy-900 tracking-tight">What Happens When Data Is Wrong?</h2>
          <p className="mt-4 text-slate-600 text-lg">Interact with the validation pipeline to see how the Dead-Letter Queue safely handles malformed events without crashing the system.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8">
          
          {/* Controls */}
          <div className="flex justify-center mb-12">
            {step === 0 && (
              <button onClick={() => setStep(1)} className="bg-red-50 text-red-700 border border-red-200 px-6 py-3 rounded-lg text-sm font-bold hover:bg-red-100 transition-colors shadow-sm flex items-center gap-2">
                Simulate Invalid Record <ArrowRight className="w-4 h-4" />
              </button>
            )}
            {step === 2 && (
              <button onClick={() => setStep(3)} className="bg-navy-900 text-white px-6 py-3 rounded-lg text-sm font-bold hover:bg-navy-800 transition-colors shadow-sm flex items-center gap-2">
                Fix & Replay Event <RotateCcw className="w-4 h-4" />
              </button>
            )}
            {step === 3 && (
              <button onClick={() => setStep(0)} className="bg-slate-100 text-slate-700 border border-slate-200 px-6 py-3 rounded-lg text-sm font-bold hover:bg-slate-200 transition-colors shadow-sm">
                Reset Demo
              </button>
            )}
          </div>

          {/* Interactive Flow */}
          <div className="grid md:grid-cols-3 gap-8 items-start">
            
            {/* Input Node */}
            <div className="flex flex-col items-center">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Incoming Record</div>
              <pre className={`text-xs p-4 rounded-lg border w-full overflow-hidden transition-all ${
                step === 0 ? 'bg-slate-50 border-slate-200 text-slate-400' : 
                step === 3 ? 'bg-emerald-50 border-emerald-200 text-emerald-800' :
                'bg-red-50 border-red-200 text-red-800'
              }`}>
{step === 3 ? 
`{
  "meter_id": "MTR-921",
  "consumption_kwh": 4.2
}` : 
`{
  "meter_id": null,
  "consumption_kwh": -12.3
}`}
              </pre>
            </div>

            {/* Validation Node */}
            <div className="flex flex-col items-center relative">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Validation Engine</div>
              
              <div className={`w-full p-6 rounded-xl border-2 flex flex-col items-center text-center transition-all ${
                step === 0 ? 'border-slate-200 bg-white' : 
                step === 1 ? 'border-red-400 bg-red-50 shadow-lg scale-105' :
                step === 3 ? 'border-emerald-400 bg-emerald-50' :
                'border-slate-200 bg-white'
              }`}>
                {step === 0 ? (
                  <span className="text-slate-400 font-medium">Awaiting record...</span>
                ) : step === 1 ? (
                  <>
                    <ShieldAlert className="w-8 h-8 text-red-500 mb-2" />
                    <span className="font-bold text-red-900 text-sm mb-2">Validation Failed</span>
                    <ul className="text-left text-xs text-red-700 list-disc pl-4 space-y-1 w-full">
                      <li>meter_id is required</li>
                      <li>consumption_kwh cannot be negative</li>
                    </ul>
                    <button onClick={() => setStep(2)} className="mt-4 bg-red-600 text-white text-xs font-bold px-3 py-1.5 rounded hover:bg-red-700 w-full">Route to DLQ →</button>
                  </>
                ) : step === 2 ? (
                  <span className="text-slate-400 font-medium">Record routed to DLQ.</span>
                ) : (
                  <>
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mb-2" />
                    <span className="font-bold text-emerald-900 text-sm">Validation Passed</span>
                  </>
                )}
              </div>
            </div>

            {/* Output Nodes */}
            <div className="flex flex-col gap-6">
              <div className={`p-4 rounded-xl border-2 transition-all flex items-center justify-between ${
                step === 3 ? 'border-emerald-400 bg-emerald-50 shadow-md' : 'border-slate-200 bg-white opacity-50'
              }`}>
                <div>
                  <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">BigQuery</div>
                  <div className="font-bold text-navy-900">Warehouse</div>
                </div>
                {step === 3 && <CheckCircle2 className="w-6 h-6 text-emerald-500" />}
              </div>

              <div className={`p-4 rounded-xl border-2 transition-all flex flex-col justify-between ${
                step === 2 ? 'border-red-400 bg-red-50 shadow-md' : 'border-slate-200 bg-white opacity-50'
              }`}>
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">Inspection</div>
                    <div className="font-bold text-navy-900">Dead-Letter Queue</div>
                  </div>
                  {step === 2 && <ShieldAlert className="w-6 h-6 text-red-500" />}
                </div>
                {step === 2 && (
                  <div className="text-xs font-mono bg-red-100 text-red-800 p-2 rounded">
                    Status: PENDING REPLAY
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  );
}
