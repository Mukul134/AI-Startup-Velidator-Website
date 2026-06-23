import { supabase } from './supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/backend';

async function getHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const headers = await getHeaders();
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  });
  
  if (!response.ok) {
    const errText = await response.text();
    let errData;
    try {
      errData = JSON.parse(errText);
    } catch {
      errData = { detail: errText };
    }
    throw new Error(errData.detail || 'API request failed');
  }
  
  if (response.status === 202) {
    return response.json(); // returns project run info
  }
  
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

export async function fetchPublicApi(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

  if (!response.ok) {
    const errText = await response.text();
    let errData;
    try {
      errData = JSON.parse(errText);
    } catch {
      errData = { detail: errText };
    }
    throw new Error(errData.detail || 'Public API request failed');
  }

  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  getPricing: () => fetchPublicApi('/public/pricing'),
  getOverview: () => fetchPublicApi('/public/overview'),
  getProjects: () => fetchApi('/projects/'),
  getProject: (id: string) => fetchApi(`/projects/${id}`),
  getReport: (id: string) => fetchApi(`/projects/${id}/report`),
  createPaymentOrder: (plan_code: string) =>
    fetchApi('/payments/order', {
      method: 'POST',
      body: JSON.stringify({ plan_code }),
    }),
  verifyPayment: (data: {
    payment_record_id: string;
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) =>
    fetchApi('/payments/verify', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  createProject: (data: {
    idea_title: string;
    idea_description: string;
    target_market: string;
    budget: number;
    customer_segment: string;
  }) => fetchApi('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
};
