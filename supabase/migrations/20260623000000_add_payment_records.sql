CREATE TYPE payment_status_type AS ENUM ('created', 'paid', 'failed');

CREATE TABLE public.payment_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    plan_code VARCHAR(100) NOT NULL,
    amount_inr INTEGER NOT NULL CHECK (amount_inr >= 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    status payment_status_type NOT NULL DEFAULT 'created',
    razorpay_order_id VARCHAR(255) NOT NULL UNIQUE,
    razorpay_payment_id VARCHAR(255),
    razorpay_signature TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX idx_payment_records_user_id ON public.payment_records(user_id);
CREATE INDEX idx_payment_records_payment_id ON public.payment_records(razorpay_payment_id);

ALTER TABLE public.payment_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own payment records" ON public.payment_records
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own payment records" ON public.payment_records
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own payment records" ON public.payment_records
    FOR UPDATE USING (auth.uid() = user_id);

CREATE TRIGGER set_payment_records_updated_at
    BEFORE UPDATE ON public.payment_records
    FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();
