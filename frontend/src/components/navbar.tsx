'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { User } from '@supabase/supabase-js';
import { Rocket, BarChart3, LogOut, CreditCard, LayoutDashboard } from 'lucide-react';

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/');
  };

  return (
    <nav className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight text-white hover:opacity-90">
        <Rocket className="text-sky-500 w-6 h-6" />
        <span>Validator<span className="text-sky-400">.AI</span></span>
      </Link>
      
      <div className="flex items-center gap-6">
        {user ? (
          <>
            <Link href="/dashboard" className="flex items-center gap-1.5 text-sm font-medium text-slate-300 hover:text-white transition">
              <LayoutDashboard className="w-4 h-4 text-sky-400" />
              <span>Dashboard</span>
            </Link>
            <Link href="/projects/new" className="flex items-center gap-1.5 text-sm font-medium text-slate-300 hover:text-white transition">
              <BarChart3 className="w-4 h-4 text-sky-400" />
              <span>New Analysis</span>
            </Link>
            <Link href="/pricing" className="flex items-center gap-1.5 text-sm font-medium text-slate-300 hover:text-white transition">
              <CreditCard className="w-4 h-4 text-sky-400" />
              <span>Pricing</span>
            </Link>
            <div className="h-4 w-[1px] bg-slate-700" />
            <span className="text-xs text-slate-400 hidden sm:inline max-w-[150px] truncate">
              {user.email}
            </span>
            <button 
              onClick={handleLogout} 
              className="flex items-center gap-1.5 bg-slate-800 hover:bg-red-950 text-slate-300 hover:text-red-400 px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-700 hover:border-red-900 transition cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Log Out</span>
            </button>
          </>
        ) : (
          <>
            <Link href="/pricing" className="text-sm font-medium text-slate-300 hover:text-white transition">
              Pricing
            </Link>
            <Link 
              href="/auth" 
              className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-lg shadow-sky-650/20 transition cursor-pointer"
            >
              Get Started
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
