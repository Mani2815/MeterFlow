import React, { useState } from 'react';
import { Database } from 'lucide-react';

export function WarehouseSection() {
  const [activeTable, setActiveTable] = useState<string | null>(null);

  const tables: Record<string, any> = {
    dim_customer: { type: 'Dimension', desc: 'Descriptive context for customer demographics and contact info.', grain: '1 row per customer entity', fields: ['customer_sk', 'first_name', 'last_name', 'email'] },
    dim_meter: { type: 'Dimension', desc: 'Physical asset specifications and installation status.', grain: '1 row per physical meter', fields: ['meter_sk', 'serial_number', 'model', 'status'] },
    dim_location: { type: 'Dimension', desc: 'Geographic and postal boundaries for spatial analytics.', grain: '1 row per region/zip', fields: ['location_sk', 'city', 'state', 'postal_code'] },
    dim_date: { type: 'Dimension', desc: 'Standard calendar dimension.', grain: '1 row per day', fields: ['date_sk', 'full_date', 'year', 'month'] },
    fact_consumption: { type: 'Fact', desc: 'Aggregated daily/hourly usage derived from raw meter readings.', grain: '1 row per meter per day', fields: ['consumption_sk', 'meter_sk', 'account_sk', 'total_consumption'] },
    fact_billing: { type: 'Fact', desc: 'Financial invoice data generated for accounts.', grain: '1 row per issued bill', fields: ['bill_sk', 'account_sk', 'total_amount', 'issue_date'] },
    fact_payment: { type: 'Fact', desc: 'Transactions received against an account.', grain: '1 row per payment transaction', fields: ['payment_sk', 'account_sk', 'amount', 'method'] },
    fact_meter_reading: { type: 'Fact', desc: 'Raw measurement events from field devices.', grain: '1 row per reading event', fields: ['reading_sk', 'meter_sk', 'reading_value', 'timestamp'] }
  };

  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h2 className="text-3xl font-bold text-navy-900 tracking-tight">From Operational Data to an Analytical Model</h2>
        <p className="mt-4 text-slate-600 text-lg">A dimensional Star Schema optimized for high-performance BigQuery analytics.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-12 items-start">
        
        {/* Star Schema Interactive Diagram */}
        <div className="w-full lg:w-2/3 bg-slate-50 border border-slate-200 rounded-2xl p-8 relative min-h-[500px] flex items-center justify-center">
          
          <div className="relative w-[600px] h-[400px]">
            {/* Center Fact */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
              <TableNode id="fact_consumption" name="fact_consumption" type="Fact" active={activeTable} onHover={setActiveTable} />
            </div>

            {/* Surrounding Dimensions */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2">
              <TableNode id="dim_customer" name="dim_customer" type="Dimension" active={activeTable} onHover={setActiveTable} />
            </div>
            
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2">
              <TableNode id="dim_location" name="dim_location" type="Dimension" active={activeTable} onHover={setActiveTable} />
            </div>

            <div className="absolute top-1/2 left-0 -translate-y-1/2">
              <TableNode id="dim_meter" name="dim_meter" type="Dimension" active={activeTable} onHover={setActiveTable} />
            </div>

            <div className="absolute top-1/2 right-0 -translate-y-1/2">
              <TableNode id="dim_date" name="dim_date" type="Dimension" active={activeTable} onHover={setActiveTable} />
            </div>

            {/* Connecting Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
              {/* Vertical lines */}
              <line x1="300" y1="50" x2="300" y2="200" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
              <line x1="300" y1="350" x2="300" y2="200" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
              {/* Horizontal lines */}
              <line x1="120" y1="200" x2="300" y2="200" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
              <line x1="480" y1="200" x2="300" y2="200" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" />
            </svg>
          </div>

          <div className="absolute bottom-6 right-6 flex gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Other Facts:</span>
            {['fact_meter_reading', 'fact_billing', 'fact_payment'].map(f => (
              <span key={f} 
                onMouseEnter={() => setActiveTable(f)} 
                onMouseLeave={() => setActiveTable(null)}
                className={`text-[10px] font-mono cursor-help px-2 py-0.5 rounded transition-colors ${activeTable === f ? 'bg-accent-blue text-white' : 'bg-slate-200 text-slate-600'}`}>
                {f}
              </span>
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="w-full lg:w-1/3 bg-white border border-slate-200 rounded-2xl p-8 shadow-sm h-full min-h-[500px]">
          {activeTable ? (
            <div className="animate-in fade-in duration-200">
              <div className="flex items-center gap-2 mb-4">
                <Database className={`w-5 h-5 ${tables[activeTable].type === 'Fact' ? 'text-accent-blue' : 'text-emerald-500'}`} />
                <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{tables[activeTable].type}</span>
              </div>
              <h3 className="text-xl font-bold font-mono text-navy-900 mb-4">{activeTable}</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Purpose</div>
                  <p className="text-sm text-slate-700">{tables[activeTable].desc}</p>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Grain</div>
                  <p className="text-sm text-slate-700">{tables[activeTable].grain}</p>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Important Fields</div>
                  <div className="flex flex-col gap-1.5">
                    {tables[activeTable].fields.map((f: string) => (
                      <div key={f} className="text-xs font-mono bg-slate-50 border border-slate-100 px-3 py-1.5 rounded text-slate-600">
                        {f.includes('_sk') ? <span className="text-accent-blue mr-2">🔑</span> : <span className="mr-2">·</span>}
                        {f}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 opacity-60">
              <Database className="w-12 h-12 mb-4" />
              <p>Hover over a table in the star schema to view its design properties.</p>
            </div>
          )}
        </div>

      </div>
    </section>
  );
}

function TableNode({ id, name, type, active, onHover }: any) {
  const isActive = active === id;
  const isFact = type === 'Fact';
  return (
    <div 
      onMouseEnter={() => onHover(id)}
      onMouseLeave={() => onHover(null)}
      className={`px-4 py-3 rounded-lg border-2 font-mono text-sm font-bold cursor-help transition-all duration-300 shadow-sm ${
        isActive ? 'scale-110 z-20 ' + (isFact ? 'bg-blue-50 border-blue-400 text-blue-900' : 'bg-emerald-50 border-emerald-400 text-emerald-900') : 
        'bg-white border-slate-200 text-slate-700 hover:border-slate-300 z-10'
      }`}
    >
      {name}
    </div>
  );
}
