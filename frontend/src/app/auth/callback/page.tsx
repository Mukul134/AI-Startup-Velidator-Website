'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { supabase } from '@/lib/supabase';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState('Completing sign-in...');

  useEffect(() => {
    const finalizeAuth = async () => {
      const code = searchParams.get('code');
      const errorDescription = searchParams.get('error_description');
      const error = searchParams.get('error');

      if (error || errorDescription) {
        const reason = errorDescription || error || 'Authentication callback failed.';
        router.replace(`/auth?error=${encodeURIComponent(reason)}`);
        return;
      }

      if (!code) {
        router.replace('/auth');
        return;
      }

      const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

      if (exchangeError) {
        router.replace(`/auth?error=${encodeURIComponent(exchangeError.message)}`);
        return;
      }

      setMessage('Redirecting to dashboard...');
      router.replace('/dashboard');
    };

    finalizeAuth();
  }, [router, searchParams]);

  return (
    <div className="flex-1 flex items-center justify-center px-6">
      <div className="glass-panel border-slate-800 rounded-3xl p-8 text-center max-w-md w-full space-y-4">
        <Loader2 className="w-8 h-8 text-sky-500 animate-spin mx-auto" />
        <h1 className="text-xl font-bold text-white">Authorizing account</h1>
        <p className="text-sm text-slate-400">{message}</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={null}>
      <AuthCallbackContent />
    </Suspense>
  );
}
