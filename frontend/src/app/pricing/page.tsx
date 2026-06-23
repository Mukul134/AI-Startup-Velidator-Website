'use client';

import { useEffect, useState } from 'react';
import { Check, CreditCard, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { formatINR } from '@/lib/currency';
import { loadRazorpayScript } from '@/lib/razorpay';
import { supabase } from '@/lib/supabase';

interface PricingTier {
  code: string;
  name: string;
  price_inr: number;
  period: string;
  description: string;
  features: string[];
  cta: string;
  popular: boolean;
  is_enterprise: boolean;
}

export default function Pricing() {
  const [tiers, setTiers] = useState<PricingTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingCode, setProcessingCode] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    api.getPricing()
      .then(setTiers)
      .catch((err: Error) => setErrorMsg(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleCheckout = async (tier: PricingTier) => {
    setErrorMsg(null);

    if (tier.price_inr === 0) {
      router.push('/auth');
      return;
    }

    if (tier.is_enterprise) {
      window.open('mailto:sales@validator.ai?subject=Venture Partner Plan Inquiry', '_self');
      return;
    }

    setProcessingCode(tier.code);

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.push('/auth');
        return;
      }

      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded || !window.Razorpay) {
        throw new Error('Unable to load Razorpay checkout.');
      }

      const order = await api.createPaymentOrder(tier.code);
      const razorpay = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: order.merchant_name,
        description: order.description,
        order_id: order.order_id,
        prefill: {
          name: user.user_metadata?.full_name || '',
          email: user.email || '',
        },
        theme: {
          color: '#0284c7',
        },
        handler: async (response: {
          razorpay_order_id: string;
          razorpay_payment_id: string;
          razorpay_signature: string;
        }) => {
          await api.verifyPayment({
            payment_record_id: order.payment_record_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          router.push('/dashboard');
        },
      });

      razorpay.on('payment.failed', () => {
        setErrorMsg('Payment failed. Please try again.');
        setProcessingCode(null);
      });

      razorpay.open();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to start payment.');
    } finally {
      setProcessingCode(null);
    }
  };

  return (
    <div className="flex-1 py-16 px-6 max-w-6xl mx-auto w-full space-y-12 flex flex-col justify-center">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-1.5 bg-sky-500/10 border border-sky-500/30 text-sky-400 px-3 py-1 rounded-full text-xs font-semibold tracking-wide">
          <CreditCard className="w-3.5 h-3.5" />
          <span>Flexible Plans for Bold Ideas</span>
        </div>
        <h1 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight leading-none">
          Simple, Transparent <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-teal-400">Pricing</span>
        </h1>
        <p className="text-slate-400 text-xs md:text-sm max-w-md mx-auto">
          Start for free and validate early ideas, then upgrade for full VC reports and financial spreadsheets.
        </p>
      </div>

      {errorMsg && (
        <div className="mx-auto max-w-2xl rounded-2xl border border-red-900/50 bg-red-950/30 p-4 text-sm text-red-300">
          {errorMsg}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        {tiers.map((tier, idx) => (
          <div 
            key={idx} 
            className={`glass-panel p-8 rounded-3xl border-slate-800 flex flex-col justify-between gap-8 relative overflow-hidden transition hover:shadow-2xl ${
              tier.popular ? 'border-sky-500/40 shadow-xl shadow-sky-500/5 bg-radial-gradient' : ''
            }`}
          >
            {tier.popular && (
              <div className="absolute top-4 right-4 bg-sky-500 text-white font-extrabold text-[9px] px-2 py-0.5 rounded-full uppercase tracking-wider">
                Most Popular
              </div>
            )}
            
            <div className="space-y-6">
              <div className="space-y-2">
                <h3 className="text-base font-extrabold text-white uppercase tracking-wider">{tier.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-white">{tier.price_inr === 0 ? 'Free' : formatINR(tier.price_inr)}</span>
                  {tier.period && <span className="text-slate-500 text-xs font-semibold">/{tier.period}</span>}
                </div>
                <p className="text-xs text-slate-400 leading-normal">{tier.description}</p>
              </div>

              <div className="h-[1px] bg-slate-800" />

              <ul className="space-y-3.5">
                {tier.features.map((feature, i) => (
                  <li key={i} className="text-xs text-slate-350 flex items-start gap-2.5 leading-snug">
                    <Check className="w-4 h-4 text-sky-500 shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="pt-2">
              <button 
                type="button"
                onClick={() => handleCheckout(tier)}
                disabled={processingCode === tier.code || loading}
                className={`w-full text-center font-bold py-3.5 rounded-xl text-xs flex items-center justify-center transition cursor-pointer ${
                  tier.popular 
                    ? 'bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-650/15' 
                    : 'glass-panel text-slate-300 hover:text-white border-slate-700 hover:border-slate-600'
                }`}
              >
                {processingCode === tier.code ? <Loader2 className="h-4 w-4 animate-spin" /> : tier.cta}
              </button>
            </div>
          </div>
        ))}
      </div>

      {loading && (
        <div className="flex justify-center text-slate-400">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      )}
    </div>
  );
}
