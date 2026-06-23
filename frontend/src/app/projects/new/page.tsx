'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { api } from '@/lib/api';
import { 
  BarChart3, 
  ArrowLeft, 
  Sparkles,
  Loader2,
  DollarSign
} from 'lucide-react';
import Link from 'next/link';

export default function NewProject() {
  const [ideaTitle, setIdeaTitle] = useState('');
  const [ideaDescription, setIdeaDescription] = useState('');
  const [targetMarket, setTargetMarket] = useState('');
  const [budget, setBudget] = useState('');
  const [customerSegment, setCustomerSegment] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) router.push('/auth');
    });
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const parsedBudget = parseFloat(budget);
    if (isNaN(parsedBudget) || parsedBudget <= 0) {
      setErrorMsg('Please specify a positive budget capital amount.');
      setLoading(false);
      return;
    }

    try {
      const response = await api.createProject({
        idea_title: ideaTitle,
        idea_description: ideaDescription,
        target_market: targetMarket,
        budget: parsedBudget,
        customer_segment: customerSegment
      });
      
      // Redirect to tracking page
      router.push(`/projects/${response.id}`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to submit startup validation request.');
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 py-12 px-6 max-w-3xl mx-auto w-full space-y-6">
      <Link 
        href="/dashboard" 
        className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 hover:text-white transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Dashboard</span>
      </Link>

      <div className="space-y-1">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <BarChart3 className="text-sky-500 w-7 h-7" />
          <span>New Startup Validation</span>
        </h1>
        <p className="text-slate-400 text-xs md:text-sm">
          Submit your startup parameters to trigger our multi-agent audit pipelines.
        </p>
      </div>

      <div className="glass-panel p-8 rounded-3xl border-slate-800 relative overflow-hidden">
        {/* Glow Element */}
        <div className="absolute top-0 right-0 w-24 h-24 bg-sky-500/5 rounded-full blur-2xl pointer-events-none" />
        
        {errorMsg && (
          <div className="bg-red-950/40 border border-red-900/50 text-red-300 p-4 rounded-xl text-xs mb-6">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Startup Idea Title</label>
            <input 
              type="text" 
              required
              value={ideaTitle}
              onChange={(e) => setIdeaTitle(e.target.value)}
              placeholder="e.g. Automated AI Code Reviewer"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-600 focus:border-sky-500 focus:outline-none transition"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Idea Description</label>
            <textarea 
              required
              rows={4}
              value={ideaDescription}
              onChange={(e) => setIdeaDescription(e.target.value)}
              placeholder="Provide a detailed description of your product, value proposition, and technical components..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-600 focus:border-sky-500 focus:outline-none transition resize-none leading-relaxed"
            />
          </div>

          <div className="grid sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Target Market</label>
              <input 
                type="text" 
                required
                value={targetMarket}
                onChange={(e) => setTargetMarket(e.target.value)}
                placeholder="e.g. US Enterprise SaaS, Global Developers"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-600 focus:border-sky-500 focus:outline-none transition"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Available Budget Cap (INR)</label>
              <div className="relative">
                <DollarSign className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input 
                  type="number" 
                  required
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="50000"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-slate-600 focus:border-sky-500 focus:outline-none transition"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Intended Customer Segment</label>
            <input 
              type="text" 
              required
              value={customerSegment}
              onChange={(e) => setCustomerSegment(e.target.value)}
              placeholder="e.g. VP of Engineering at mid-sized SaaS startups"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-600 focus:border-sky-500 focus:outline-none transition"
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-sky-600 hover:bg-sky-500 disabled:bg-sky-850 disabled:text-sky-300 text-white font-bold py-4 rounded-xl text-sm transition shadow-lg shadow-sky-650/15 flex items-center justify-center gap-2 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Launching Validation Agents...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Start Multi-Agent Analysis</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
