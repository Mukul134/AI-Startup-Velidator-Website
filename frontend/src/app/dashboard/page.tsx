'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { api } from '@/lib/api';
import { formatINR } from '@/lib/currency';
import { 
  Rocket,
  Plus, 
  History, 
  ChevronRight, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader2 
} from 'lucide-react';

interface Project {
  id: string;
  idea_title: string;
  idea_description: string;
  target_market: string;
  budget: number;
  customer_segment: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchHistory = async () => {
    try {
      setError(null);
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load validation history';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) {
        router.push('/auth');
      } else {
        fetchHistory();
      }
    });
  }, [router]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchHistory();
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: Project['status']) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full text-xs font-semibold">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Completed</span>
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center gap-1 bg-sky-500/10 border border-sky-500/20 text-sky-400 px-2 py-0.5 rounded-full text-xs font-semibold animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Processing</span>
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 bg-red-500/10 border border-red-500/20 text-red-400 px-2 py-0.5 rounded-full text-xs font-semibold">
            <XCircle className="w-3.5 h-3.5" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 bg-slate-500/10 border border-slate-500/20 text-slate-400 px-2 py-0.5 rounded-full text-xs font-semibold">
            <Clock className="w-3.5 h-3.5" />
            <span>Pending</span>
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-sky-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 py-12 px-6 max-w-6xl mx-auto w-full space-y-8">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <History className="text-sky-500 w-7 h-7" />
            <span>Validation History</span>
          </h1>
          <p className="text-slate-400 text-xs md:text-sm">
            Manage your submitted startup ideas and review their venture evaluations.
          </p>
        </div>
        
        <Link 
          href="/projects/new" 
          className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-5 py-2.5 rounded-xl text-sm flex items-center justify-center gap-1.5 shadow-lg shadow-sky-650/15 transition cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Validation</span>
        </Link>
      </div>

      {error && projects.length === 0 ? (
        <div className="glass-panel p-8 rounded-3xl border-slate-800 max-w-2xl mx-auto text-center space-y-3">
          <h3 className="text-lg font-bold text-white">Validation history unavailable</h3>
          <p className="text-sm text-slate-400">{error}</p>
          <p className="text-xs text-slate-500">
            If the backend was just started, refresh the page after the server finishes booting.
          </p>
        </div>
      ) : null}

      {/* Projects Grid */}
      {!error && projects.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-3xl border-slate-800 flex flex-col items-center justify-center gap-4 max-w-2xl mx-auto">
          <div className="bg-sky-500/10 border border-sky-500/20 text-sky-400 p-4 rounded-full">
            <Rocket className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">No validations created yet</h3>
            <p className="text-slate-400 text-xs max-w-sm mx-auto leading-relaxed">
              Submit your first startup idea to trigger our multi-agent validator and receive a VC readiness report.
            </p>
          </div>
          <div className="pt-2">
            <Link 
              href="/projects/new" 
              className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-6 py-2.5 rounded-xl text-xs transition cursor-pointer"
            >
              Start First Analysis
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-6">
          {projects.map((project) => (
            <div 
              key={project.id} 
              className="glass-panel p-6 rounded-2xl border-slate-800 hover:border-slate-700 transition flex flex-col justify-between gap-6"
            >
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base font-bold text-white line-clamp-1">{project.idea_title}</h3>
                  {getStatusBadge(project.status)}
                </div>
                
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                  {project.idea_description}
                </p>
                
                <div className="grid grid-cols-2 gap-4 text-[10px] text-slate-450 border-t border-slate-800/80 pt-3">
                  <div>
                    <span className="block font-semibold text-slate-500 uppercase">Target Market</span>
                    <span className="block font-medium text-slate-300 mt-0.5 truncate">{project.target_market}</span>
                  </div>
                  <div>
                    <span className="block font-semibold text-slate-500 uppercase">Budget Cap</span>
                    <span className="block font-medium text-slate-300 mt-0.5">{formatINR(project.budget)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-850 pt-4">
                <span className="text-[10px] text-slate-500">
                  Created {new Date(project.created_at).toLocaleDateString()}
                </span>
                
                <Link 
                  href={`/projects/${project.id}`} 
                  className="inline-flex items-center gap-1 text-xs font-bold text-sky-400 hover:text-sky-300 transition"
                >
                  <span>{project.status === 'completed' ? 'View Report' : 'Track Status'}</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
