'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { 
  ShieldCheck, 
  TrendingUp, 
  Users, 
  Coins, 
  AlertTriangle, 
  Sparkles, 
  FileCheck,
  ChevronRight,
  Activity,
  FileBarChart,
  Trophy
} from 'lucide-react';
import { api } from '@/lib/api';

interface OverviewStats {
  total_projects: number;
  completed_reports: number;
  active_founders: number;
  average_score: number;
}

export default function Home() {
  const [stats, setStats] = useState<OverviewStats | null>(null);

  useEffect(() => {
    api.getOverview().then(setStats).catch(() => null);
  }, []);

  const agents = [
    { name: "Market Research Agent", desc: "Estimates TAM, SAM, SOM sizing and identifies segment CAGR tailwinds.", icon: TrendingUp },
    { name: "Competitor Intelligence Agent", desc: "Catalogs market competitor pricing, feature configurations, and SWOT sheets.", icon: ShieldCheck },
    { name: "Customer Persona Agent", desc: "Creates 10 diverse synthetic customer profiles capturing ICP pain points.", icon: Users },
    { name: "VC Investor Agent", desc: "Audits business defensibility, operational risks, and delivers VC grade scores.", icon: FileCheck },
    { name: "Financial Projection Agent", desc: "Models a 3-year recurring revenue ARR/MRR cash flow and break-even targets.", icon: Coins },
    { name: "Vulnerability Risk Agent", desc: "Scrutinizes compliance, technical limits, and legal constraints.", icon: AlertTriangle }
  ];

  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center max-w-3xl space-y-6">
        <div className="inline-flex items-center gap-1.5 bg-sky-500/10 border border-sky-500/30 text-sky-400 px-3 py-1 rounded-full text-xs font-semibold tracking-wide">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Venture Validation Orchestrated by LangGraph</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight leading-[1.1]">
          Validate Your Startup Idea with <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-teal-400">Multi-Agent AI</span>
        </h1>
        
        <p className="text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
          Get a professional Venture Capital-grade validation analysis. Our network of 7 specialized AI agents dissects your market size, competitor SWOTS, customer behaviors, risks, and forecasts in minutes.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link 
            href="/auth" 
            className="w-full sm:w-auto bg-sky-600 hover:bg-sky-500 text-white font-semibold px-8 py-3.5 rounded-xl shadow-lg shadow-sky-650/15 flex items-center justify-center gap-2 transition cursor-pointer"
          >
            <span>Analyze My Concept</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
          <Link 
            href="/pricing" 
            className="w-full sm:w-auto glass-panel hover:bg-slate-900 text-slate-300 hover:text-white font-semibold px-8 py-3.5 rounded-xl transition cursor-pointer border-slate-700"
          >
            View Pricing Plans
          </Link>
        </div>
      </div>

      <div className="mt-14 grid w-full max-w-4xl grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: 'Ideas Reviewed', value: stats?.total_projects ?? 'Live', icon: Activity },
          { label: 'Reports Generated', value: stats?.completed_reports ?? 'Live', icon: FileBarChart },
          { label: 'Active Founders', value: stats?.active_founders ?? 'Growing', icon: Users },
          { label: 'Avg. Validation Score', value: stats ? `${stats.average_score}/100` : 'Tracked', icon: Trophy },
        ].map((item) => (
          <div key={item.label} className="glass-panel rounded-2xl border-slate-800 p-4 text-left">
            <item.icon className="mb-3 h-4 w-4 text-sky-400" />
            <div className="text-lg font-extrabold text-white">{item.value}</div>
            <div className="text-[11px] uppercase tracking-wide text-slate-500">{item.label}</div>
          </div>
        ))}
      </div>

      {/* Agents Feature Grid */}
      <div className="mt-32 space-y-10 w-full">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Our Automated Expert Board
          </h2>
          <p className="text-slate-400 text-sm max-w-lg mx-auto">
            Seven discrete sub-agents working together in a compiled state graph to deliver granular validation.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent, i) => (
            <div key={i} className="glass-panel p-6 rounded-2xl flex flex-col gap-4 border-slate-800 hover:border-slate-700 hover:shadow-lg hover:shadow-sky-500/5 transition">
              <div className="bg-sky-500/10 border border-sky-500/20 text-sky-400 p-3 rounded-xl w-fit">
                <agent.icon className="w-5 h-5" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-white leading-snug">{agent.name}</h3>
                <p className="text-xs text-slate-400 leading-normal">{agent.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trust Quote / Pitch */}
      <div className="mt-32 glass-panel p-8 md:p-12 rounded-3xl w-full border-slate-800 bg-radial-gradient text-center max-w-4xl space-y-4">
        <h3 className="text-xl md:text-2xl font-bold text-white">Save Weeks of Research and Pivot Immediately</h3>
        <p className="text-slate-400 text-sm max-w-xl mx-auto leading-relaxed">
          Stop writing static business validation templates. Let our validator run financial modeling, pricing structures, and risk assessments dynamically in a single multi-agent pipeline.
        </p>
        <div className="pt-2">
          <Link 
            href="/auth" 
            className="inline-flex bg-sky-600 hover:bg-sky-500 text-white text-sm font-bold px-6 py-2.5 rounded-xl transition cursor-pointer"
          >
            Create Free Account
          </Link>
        </div>
      </div>
    </div>
  );
}
