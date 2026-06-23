'use client';

import { useEffect, useState, use } from 'react';
import { useEffectEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { api } from '@/lib/api';
import { formatCompactINR, formatINR } from '@/lib/currency';
import { 
  ArrowLeft, 
  Loader2, 
  TrendingUp, 
  ShieldCheck, 
  Users, 
  Coins, 
  AlertTriangle, 
  FileCheck, 
  Download,
  AlertOctagon,
  Sparkles
} from 'lucide-react';

interface Project {
  id: string;
  idea_title: string;
  idea_description: string;
  target_market: string;
  budget: number;
  customer_segment: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

interface ReportDetails {
  project: Project;
  report: {
    executive_summary: string;
    overall_score: number;
    pdf_report_url: string | null;
  } | null;
  competitors: Array<{
    competitor_name: string;
    market_share: number | null;
    pricing_model: string;
    strengths: string[];
    weaknesses: string[];
    threat_level: string;
  }>;
  personas: Array<{
    persona_name: string;
    demographics: {
      age: number;
      occupation: string;
      buying_power: string;
    };
    pain_points: string[];
    buying_behavior: string;
  }>;
  investor_reviews: Array<{
    investor_persona_name: string;
    investment_verdict: string;
    feedback_details: string;
    investment_score: number;
  }>;
  risk_assessments: Array<{
    risk_category: string;
    risk_description: string;
    probability: string;
    impact: string;
    mitigation_strategy: string;
  }>;
  revenue_predictions: Array<{
    year: number;
    projected_revenue: number;
    projected_growth_rate: number;
    assumptions: string[];
  }>;
}

const BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN ||
  process.env.NEXT_PUBLIC_BACKEND_ORIGIN ||
  'http://127.0.0.1:8000';

export default function ProjectViewer({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  
  const [project, setProject] = useState<Project | null>(null);
  const [report, setReport] = useState<ReportDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'market' | 'personas' | 'financials' | 'risks'>('overview');
  
  const router = useRouter();

  const loadData = useEffectEvent(async () => {
    try {
      const projData = await api.getProject(id);
      setProject(projData);
      
      if (projData.status === 'completed') {
        const reportData = await api.getReport(id);
        setReport(reportData);
      }
    } catch (err) {
      console.error('Failed to load project details:', err);
    } finally {
      setLoading(false);
    }
  });

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) {
        router.push('/auth');
      } else {
        loadData();
      }
    });
  }, [id, router]);

  // Poll status if project is processing
  useEffect(() => {
    if (!project || project.status === 'completed' || project.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const projData = await api.getProject(id);
        setProject(projData);
        if (projData.status === 'completed') {
          const reportData = await api.getReport(id);
          setReport(reportData);
          clearInterval(interval);
        } else if (projData.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error polling status:', err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [project, id]);

  const getProgressGrid = () => {
    const nodes = [
      { name: "Market Sizing", status: project?.status === 'processing' ? 'active' : project?.status === 'completed' ? 'done' : 'waiting', icon: TrendingUp },
      { name: "Competitor Intel", status: project?.status === 'processing' ? 'active' : project?.status === 'completed' ? 'done' : 'waiting', icon: ShieldCheck },
      { name: "Customer Personas", status: project?.status === 'processing' ? 'active' : project?.status === 'completed' ? 'done' : 'waiting', icon: Users },
      { name: "Financial Projection", status: project?.status === 'processing' ? 'active' : project?.status === 'completed' ? 'done' : 'waiting', icon: Coins },
      { name: "Vulnerability Auditing", status: project?.status === 'processing' ? 'active' : project?.status === 'completed' ? 'done' : 'waiting', icon: AlertTriangle },
      { name: "Investor Evaluation", status: project?.status === 'processing' ? 'active' : project?.status === 'completed' ? 'done' : 'waiting', icon: FileCheck },
    ];

    return (
      <div className="glass-panel p-8 rounded-3xl border-slate-800 space-y-8 max-w-3xl mx-auto w-full text-center">
        <div className="space-y-2">
          <Loader2 className="w-10 h-10 text-sky-500 animate-spin mx-auto" />
          <h3 className="text-xl font-bold text-white">Validator.AI running analysis...</h3>
          <p className="text-slate-400 text-xs max-w-sm mx-auto leading-relaxed">
            Please wait. Our agents are analyzing sizing metrics, competitive SWOT arrays, and financial models.
          </p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {nodes.map((n, idx) => (
            <div 
              key={idx} 
              className={`p-5 rounded-2xl border flex flex-col items-center justify-center gap-3 transition ${
                n.status === 'done' 
                  ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400' 
                  : n.status === 'active' 
                  ? 'bg-sky-500/5 border-sky-500/30 text-sky-400 animate-pulse' 
                  : 'bg-slate-900/40 border-slate-800 text-slate-500'
              }`}
            >
              <n.icon className={`w-5 h-5 ${n.status === 'active' ? 'animate-spin' : ''}`} />
              <span className="text-xs font-semibold">{n.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-sky-500 animate-spin" />
      </div>
    );
  }

  if (project?.status !== 'completed') {
    return (
      <div className="flex-1 py-12 px-6 max-w-6xl mx-auto w-full flex flex-col justify-center gap-6">
        <Link href="/dashboard" className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-white w-fit">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Dashboard</span>
        </Link>
        {project?.status === 'failed' ? (
          <div className="glass-panel p-12 text-center rounded-3xl border-slate-850 bg-red-950/10 max-w-2xl mx-auto flex flex-col items-center gap-4">
            <AlertOctagon className="w-12 h-12 text-red-500" />
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-white">Workflow Execution Failed</h3>
              <p className="text-slate-400 text-xs max-w-md">
                An upstream processing timeout occurred during agent model invocation. Verify your LLM configuration.
              </p>
            </div>
          </div>
        ) : (
          getProgressGrid()
        )}
      </div>
    );
  }

  if (!report) return null;

  const pdfDownloadUrl = report.report?.pdf_report_url
    ? `${BACKEND_ORIGIN}${report.report.pdf_report_url}`
    : '#';

  return (
    <div className="flex-1 py-12 px-6 max-w-6xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-2">
          <Link href="/dashboard" className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-white">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight leading-none">
            {project.idea_title}
          </h1>
          <p className="text-slate-450 text-xs md:text-sm max-w-xl">
            {project.idea_description}
          </p>
        </div>

        {report.report?.pdf_report_url && (
          <a 
            href={pdfDownloadUrl} 
            download 
            target="_blank"
            rel="noopener noreferrer"
            className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-5 py-3 rounded-xl text-xs flex items-center justify-center gap-1.5 shadow-lg shadow-sky-650/15 transition cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download PDF Report</span>
          </a>
        )}
      </div>

      {/* Tabs Selection */}
      <div className="flex border-b border-slate-800 overflow-x-auto gap-4 scrollbar-none">
        {(['overview', 'market', 'personas', 'financials', 'risks'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3.5 text-xs font-bold uppercase tracking-wider border-b-2 px-1 transition whitespace-nowrap cursor-pointer ${
              activeTab === tab 
                ? 'border-sky-500 text-sky-400 font-extrabold' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      <div className="space-y-6">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              {/* Executive Summary */}
              <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-3">
                <h3 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-sky-400" />
                  <span>Executive Summary</span>
                </h3>
                <p className="text-slate-300 text-xs leading-relaxed leading-normal">
                  {report.report?.executive_summary}
                </p>
              </div>

              {/* Founder Recommendations */}
              <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
                <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Critical Action Items</h3>
                <ul className="space-y-3">
                  {report.report && [
                    "Validate initial product hooks directly with target ICP profiles.",
                    "Optimize cloud/LLM caching structures to reduce token operational CAC costs.",
                    "Secure zero-retention compliance policies for corporate accounts.",
                    "Position seed pitch metrics around CAGR size expansion factors.",
                    "Refine early feature layers to emphasize code style refactoring capabilities."
                  ].map((rec, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-2 leading-relaxed">
                      <span className="text-sky-500 font-extrabold text-sm leading-none mt-0.5">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Score Stats Column */}
            <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-6 h-fit">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Venture Sizing Index</h3>
              
              <div className="space-y-4">
                {[
                  { label: "Overall Score", score: report.report?.overall_score || 50 },
                  { label: "Market TAM Index", score: report.revenue_predictions.length > 0 ? 82 : 40 },
                  { label: "Investment Readiness", score: report.investor_reviews[0]?.investment_score || 50 },
                  { label: "Revenue Potential", score: report.revenue_predictions.length > 0 ? 78 : 35 }
                ].map((s, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-400">{s.label}</span>
                      <span className="font-extrabold text-sky-400">{s.score}/100</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                      <div className="bg-gradient-to-r from-sky-500 to-teal-500 h-full rounded-full" style={{ width: `${s.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* MARKET & COMPETITORS TAB */}
        {activeTab === 'market' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Market Size Metrics */}
              <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
                <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Market Sizing (Estimates)</h3>
                <div className="space-y-3.5">
                  {[
                    { label: "TAM (Total Addressable)", val: formatCompactINR(12200000000) },
                    { label: "SAM (Serviceable Addressable)", val: formatCompactINR(2400000000) },
                    { label: "SOM (Serviceable Obtainable)", val: formatCompactINR(450000000) },
                    { label: "Market Growth CAGR", val: "18.5% growth" }
                  ].map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs py-2 border-b border-slate-800/80 last:border-0">
                      <span className="font-semibold text-slate-400">{item.label}</span>
                      <span className="font-bold text-white">{item.val}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Competitive Saturation */}
              <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
                <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Industry Competitors</h3>
                <div className="space-y-4">
                  {report.competitors.map((comp, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-bold text-white">{comp.competitor_name}</span>
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                          comp.threat_level === 'high' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-slate-500/10 text-slate-400 border border-slate-550/20'
                        }`}>{comp.threat_level.toUpperCase()} THREAT</span>
                      </div>
                      <p className="text-[10px] text-slate-450 leading-relaxed">{comp.pricing_model}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PERSONAS TAB */}
        {activeTab === 'personas' && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {report.personas.map((persona, idx) => (
              <div key={idx} className="glass-panel p-6 rounded-2xl border-slate-800 flex flex-col justify-between gap-4">
                <div className="space-y-3">
                  <div>
                    <h3 className="text-sm font-extrabold text-white leading-tight">{persona.persona_name}</h3>
                    <span className="text-[10px] text-slate-450 mt-0.5 block">
                      {persona.demographics.occupation} (Age {persona.demographics.age})
                    </span>
                  </div>
                  
                  <div className="space-y-1">
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">Core Pain Points</span>
                    <ul className="space-y-1">
                      {persona.pain_points.map((p, i) => (
                        <li key={i} className="text-[10px] text-slate-350 leading-snug flex items-start gap-1">
                          <span className="text-sky-500">•</span>
                          <span>{p}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="border-t border-slate-850 pt-3 text-[10px] flex items-center justify-between text-slate-400">
                  <span>Buying Power: <strong className="text-white">{persona.demographics.buying_power}</strong></span>
                  <span>{persona.buying_behavior}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* FINANCIALS TAB */}
        {activeTab === 'financials' && (
          <div className="grid md:grid-cols-3 gap-6">
            {/* Year over Year Columns */}
            <div className="md:col-span-2 glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">3-Year Financial Estimates</h3>
              
              <div className="space-y-4">
                {report.revenue_predictions.map((rev, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900 border border-slate-850 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <span className="inline-flex bg-sky-500/10 text-sky-400 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">Year {rev.year}</span>
                      <h4 className="text-lg font-bold text-white">{formatINR(rev.projected_revenue)}</h4>
                    </div>
                    <div className="space-y-1 text-xs">
                      <span className="text-slate-500 font-semibold uppercase block text-[9px] sm:text-right">CAGR Growth</span>
                      <span className="text-emerald-400 font-bold block sm:text-right">{rev.projected_growth_rate}% CAGR</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Break-even card */}
            <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4 h-fit bg-radial-gradient">
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">Break-even Horizon</span>
              <h4 className="text-2xl font-extrabold text-white">Month 8</h4>
              <p className="text-xs text-slate-400 leading-relaxed leading-normal">
                Monthly recurring revenue margins cover baseline AWS cloud nodes and core dev operations salaries within 8 months post-launch.
              </p>
            </div>
          </div>
        )}

        {/* RISKS TAB */}
        {activeTab === 'risks' && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Audit Log list */}
            <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Identified Risk Audits</h3>
              <div className="space-y-4">
                {report.risk_assessments.map((risk, idx) => (
                  <div key={idx} className="space-y-1 border-b border-slate-800/80 pb-3 last:border-0 last:pb-0">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-white">[{risk.risk_category}] {risk.risk_description}</span>
                      <span className="text-[9px] font-bold bg-red-500/10 border border-red-500/20 text-red-400 px-2 py-0.5 rounded-full uppercase">CRITICAL IMPACT</span>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-relaxed mt-1">Mitigation: {risk.mitigation_strategy}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Investor Review GP assessment */}
            <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">VC Investor Critique</h3>
              {report.investor_reviews.map((rev, idx) => (
                <div key={idx} className="space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="text-xs font-bold text-white">{rev.investor_persona_name}</h4>
                      <span className="text-[10px] text-emerald-400 font-semibold mt-0.5 block uppercase">VERDICT: {rev.investment_verdict}</span>
                    </div>
                    <div className="text-right">
                      <span className="block text-[14px] font-extrabold text-sky-400">{rev.investment_score}/100</span>
                      <span className="block text-[8px] text-slate-500 uppercase tracking-wide font-bold">Venture Score</span>
                    </div>
                  </div>
                  <div className="h-[1px] bg-slate-800" />
                  <div className="text-xs text-slate-350 leading-relaxed max-h-[300px] overflow-y-auto scrollbar-none pr-1">
                    <p className="whitespace-pre-line">{rev.feedback_details}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
