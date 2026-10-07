"use client";

import React, { useEffect } from 'react';
import Link from 'next/link';
import { ArrowRight, Activity, Database, CheckCircle, ShieldAlert, Cpu, Server, Lock, BarChart3, LayoutDashboard, Search } from 'lucide-react';
import { Hero } from '@/components/landing/Hero';
import { StatusStrip } from '@/components/landing/StatusStrip';
import { ProblemSection } from '@/components/landing/ProblemSection';
import { MeterToCashFlow } from '@/components/landing/MeterToCashFlow';
import { ArchitectureSection } from '@/components/landing/ArchitectureSection';
import { DataJourney } from '@/components/landing/DataJourney';
import { EngineeringChallenges } from '@/components/landing/EngineeringChallenges';
import { DataQualityDemo } from '@/components/landing/DataQualityDemo';
import { WarehouseSection } from '@/components/landing/WarehouseSection';
import { TechnologyGrid } from '@/components/landing/TechnologyGrid';
import { BatchVsCdc } from '@/components/landing/BatchVsCdc';
import { PipelineObservability } from '@/components/landing/PipelineObservability';
import { BusinessImpact } from '@/components/landing/BusinessImpact';
import { InteractiveDemo } from '@/components/landing/InteractiveDemo';
import { CredibilitySection } from '@/components/landing/CredibilitySection';
import { Footer } from '@/components/landing/Footer';

export default function LandingPage() {
  // Smooth scroll handler
  useEffect(() => {
    const handleNavClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'A' && target.getAttribute('href')?.startsWith('#')) {
        e.preventDefault();
        const id = target.getAttribute('href')?.substring(1);
        const element = document.getElementById(id!);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
        }
      }
    };
    document.addEventListener('click', handleNavClick);
    return () => document.removeEventListener('click', handleNavClick);
  }, []);

  return (
    <div className="min-h-screen bg-[#FDFDFD] text-slate-900 font-sans selection:bg-accent-blue/20 selection:text-navy-900 overflow-x-hidden">
      
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/90 backdrop-blur-md border-b border-slate-200 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-navy-900 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-navy-900 leading-tight">MeterFlow</div>
              <div className="text-[10px] text-slate-500 font-medium uppercase tracking-widest leading-tight">Utility Data Platform</div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#platform" className="hover:text-accent-blue transition-colors">Platform</a>
            <a href="#architecture" className="hover:text-accent-blue transition-colors">Architecture</a>
            <a href="#data-flow" className="hover:text-accent-blue transition-colors">Data Flow</a>
            <a href="#about" className="hover:text-accent-blue transition-colors">About</a>
          </div>
          <Link href="/console" className="flex items-center gap-2 bg-navy-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-navy-800 transition-colors shadow-sm">
            Open Console <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      <main className="pt-16">
        <Hero />
        <StatusStrip />
        
        <div id="platform">
          <ProblemSection />
          <MeterToCashFlow />
        </div>

        <div id="architecture" className="bg-slate-50 border-y border-slate-200">
          <ArchitectureSection />
          <BatchVsCdc />
          <WarehouseSection />
        </div>

        <div id="data-flow">
          <DataJourney />
          <DataQualityDemo />
          <InteractiveDemo />
        </div>

        <div className="bg-slate-900 text-white">
          <EngineeringChallenges />
          <TechnologyGrid />
          <PipelineObservability />
        </div>

        <div id="about">
          <BusinessImpact />
          <CredibilitySection />
        </div>

        {/* CTA */}
        <section className="py-24 bg-accent-blue text-white text-center px-6">
          <div className="max-w-3xl mx-auto space-y-6">
            <h2 className="text-4xl font-bold tracking-tight">See the Data Platform in Action</h2>
            <p className="text-blue-100 text-lg">Explore pipeline runs, CDC events, data quality, backfills, the analytical warehouse and meter-to-cash insights.</p>
            <div className="flex justify-center gap-4 pt-4">
              <Link href="/console" className="bg-white text-accent-blue px-6 py-3 rounded-lg text-sm font-bold hover:bg-slate-50 transition-colors shadow-sm flex items-center gap-2">
                Open Platform Console <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#architecture" className="bg-blue-600 border border-blue-500 text-white px-6 py-3 rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors shadow-sm">
                View Architecture
              </a>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
