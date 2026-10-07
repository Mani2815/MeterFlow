import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';

export function MeterToCashFlow() {
  const steps = [
    { id: 'customer', title: 'Customer', detail: 'A customer profile is created in the CRM.' },
    { id: 'account', title: 'Account', detail: 'Financial account linking the customer to services.' },
    { id: 'service', title: 'Service', detail: 'Active utility service contract.' },
    { id: 'meter', title: 'Meter', detail: 'Physical asset measuring consumption.' },
    { id: 'reading', title: 'Reading', detail: 'Recorded consumption data becomes the operational input for downstream processes.' },
    { id: 'consumption', title: 'Consumption', detail: 'Aggregated raw readings into billable periods.' },
    { id: 'bill', title: 'Bill', detail: 'Validated consumption is transformed into billable information.' },
    { id: 'payment', title: 'Payment', detail: 'Billing outcomes continue into payment and collection analytics.' },
  ];

  const [activeStep, setActiveStep] = useState(0);

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto bg-white border-t border-slate-100">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight">What is Meter-to-Cash?</h2>
        <p className="mt-4 text-slate-600 text-lg">The fundamental lifecycle of a utility provider. Every node in this chain generates data that our platform must unify.</p>
      </div>

      <div className="relative">
        <div className="flex justify-between items-center overflow-x-auto pb-8 hide-scrollbar">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <div 
                className="flex flex-col items-center gap-3 cursor-pointer group shrink-0"
                onClick={() => setActiveStep(idx)}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 shadow-sm ${
                  activeStep === idx ? 'bg-navy-900 text-white scale-110' : 
                  activeStep > idx ? 'bg-accent-blue text-white' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                }`}>
                  {idx + 1}
                </div>
                <div className={`text-xs font-semibold uppercase tracking-wider transition-colors ${
                  activeStep === idx ? 'text-navy-900' : 'text-slate-500'
                }`}>
                  {step.title}
                </div>
              </div>
              
              {idx < steps.length - 1 && (
                <div className="flex-1 min-w-[32px] max-w-[64px] mx-2 h-0.5 relative">
                  <div className="absolute inset-0 bg-slate-200"></div>
                  <div className="absolute inset-y-0 left-0 bg-accent-blue transition-all duration-500" style={{ width: activeStep > idx ? '100%' : '0%' }}></div>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Detail Panel */}
        <div className="mt-8 bg-slate-50 border border-slate-200 rounded-xl p-8 text-center max-w-2xl mx-auto shadow-sm transform transition-all duration-300">
          <h3 className="text-xl font-bold text-navy-900 mb-2">{steps[activeStep].title}</h3>
          <p className="text-slate-600 leading-relaxed">{steps[activeStep].detail}</p>
        </div>
      </div>
    </section>
  );
}
