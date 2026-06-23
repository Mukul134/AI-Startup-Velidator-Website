-- Enable UUID generator
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Custom Types & Enums
CREATE TYPE project_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE threat_level_type AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE investment_verdict_type AS ENUM ('invest', 'watch', 'pass');
CREATE TYPE risk_level_type AS ENUM ('low', 'medium', 'high', 'critical');

-- 1. Users Profile Table (Mirrors Supabase auth.users)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Startup Projects Table
CREATE TABLE public.startup_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    idea_title VARCHAR(255) NOT NULL,
    idea_description TEXT NOT NULL,
    target_market VARCHAR(255) NOT NULL,
    budget NUMERIC(12, 2) NOT NULL CHECK (budget >= 0),
    customer_segment VARCHAR(255) NOT NULL,
    status project_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Reports Table
CREATE TABLE public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL UNIQUE REFERENCES public.startup_projects(id) ON DELETE CASCADE,
    executive_summary TEXT,
    overall_score INTEGER CHECK (overall_score BETWEEN 0 AND 100),
    pdf_report_url TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Competitor Analysis Table
CREATE TABLE public.competitor_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.startup_projects(id) ON DELETE CASCADE,
    competitor_name VARCHAR(255) NOT NULL,
    market_share NUMERIC(5, 2) CHECK (market_share BETWEEN 0 AND 100),
    strengths TEXT[] DEFAULT '{}'::TEXT[],
    weaknesses TEXT[] DEFAULT '{}'::TEXT[],
    threat_level threat_level_type NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Customer Personas Table
CREATE TABLE public.customer_personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.startup_projects(id) ON DELETE CASCADE,
    persona_name VARCHAR(255) NOT NULL,
    demographics JSONB NOT NULL DEFAULT '{}'::JSONB,
    pain_points TEXT[] DEFAULT '{}'::TEXT[],
    buying_behavior TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Investor Reviews Table
CREATE TABLE public.investor_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.startup_projects(id) ON DELETE CASCADE,
    investor_persona_name VARCHAR(255) NOT NULL,
    investment_verdict investment_verdict_type NOT NULL DEFAULT 'pass',
    feedback_details TEXT NOT NULL,
    investment_score INTEGER CHECK (investment_score BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Risk Assessments Table
CREATE TABLE public.risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.startup_projects(id) ON DELETE CASCADE,
    risk_category VARCHAR(100) NOT NULL,
    risk_description TEXT NOT NULL,
    probability risk_level_type NOT NULL,
    impact risk_level_type NOT NULL,
    mitigation_strategy TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. Revenue Predictions Table
CREATE TABLE public.revenue_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.startup_projects(id) ON DELETE CASCADE,
    year INTEGER NOT NULL CHECK (year >= 1),
    projected_revenue NUMERIC(15, 2) NOT NULL CHECK (projected_revenue >= 0),
    projected_growth_rate NUMERIC(5, 2) DEFAULT 0.00,
    assumptions TEXT[] DEFAULT '{}'::TEXT[],
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE (project_id, year)
);

-- Indexes for projects search and sorting
CREATE INDEX idx_startup_projects_user_id ON public.startup_projects(user_id);
CREATE INDEX idx_startup_projects_status ON public.startup_projects(status);
CREATE INDEX idx_startup_projects_created_at ON public.startup_projects(created_at DESC);

-- Unique/FK Index for report lookup
CREATE INDEX idx_reports_project_id ON public.reports(project_id);

-- Indexes for sub-agent data lookups
CREATE INDEX idx_competitor_analysis_project_id ON public.competitor_analysis(project_id);
CREATE INDEX idx_customer_personas_project_id ON public.customer_personas(project_id);
CREATE INDEX idx_investor_reviews_project_id ON public.investor_reviews(project_id);
CREATE INDEX idx_risk_assessments_project_id ON public.risk_assessments(project_id);
CREATE INDEX idx_revenue_predictions_project_id ON public.revenue_predictions(project_id);

-- GIN (Generalized Inverted Index) on demographics JSONB for unstructured fields querying
CREATE INDEX idx_customer_personas_demographics ON public.customer_personas USING gin (demographics);

-- Create the trigger function for auto-mirroring auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Attach the trigger to auth.users
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION public.set_current_timestamp_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    new.updated_at = timezone('utc'::text, now());
    RETURN new;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();
CREATE TRIGGER set_projects_updated_at BEFORE UPDATE ON public.startup_projects FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();
CREATE TRIGGER set_reports_updated_at BEFORE UPDATE ON public.reports FOR EACH ROW EXECUTE FUNCTION public.set_current_timestamp_updated_at();

-- Enable RLS across all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.startup_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.competitor_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customer_personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investor_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.revenue_predictions ENABLE ROW LEVEL SECURITY;

-- 1. Users Policies
CREATE POLICY "Users can view their own profile." ON public.users 
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile." ON public.users 
    FOR UPDATE USING (auth.uid() = id);

-- 2. Startup Projects Policies
CREATE POLICY "Users can CRUD their own projects" ON public.startup_projects
    FOR ALL USING (auth.uid() = user_id);

-- 3. Reports Policies
CREATE POLICY "Users can view reports for owned projects" ON public.reports
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.startup_projects
            WHERE public.startup_projects.id = reports.project_id
            AND public.startup_projects.user_id = auth.uid()
        )
    );

-- 4. Competitor Analysis Policies
CREATE POLICY "Users can view competitor analysis for owned projects" ON public.competitor_analysis
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.startup_projects
            WHERE public.startup_projects.id = competitor_analysis.project_id
            AND public.startup_projects.user_id = auth.uid()
        )
    );

-- 5. Customer Personas Policies
CREATE POLICY "Users can view customer personas for owned projects" ON public.customer_personas
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.startup_projects
            WHERE public.startup_projects.id = customer_personas.project_id
            AND public.startup_projects.user_id = auth.uid()
        )
    );

-- 6. Investor Reviews Policies
CREATE POLICY "Users can view investor reviews for owned projects" ON public.investor_reviews
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.startup_projects
            WHERE public.startup_projects.id = investor_reviews.project_id
            AND public.startup_projects.user_id = auth.uid()
        )
    );

-- 7. Risk Assessments Policies
CREATE POLICY "Users can view risk assessments for owned projects" ON public.risk_assessments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.startup_projects
            WHERE public.startup_projects.id = risk_assessments.project_id
            AND public.startup_projects.user_id = auth.uid()
        )
    );

-- 8. Revenue Predictions Policies
CREATE POLICY "Users can view revenue predictions for owned projects" ON public.revenue_predictions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.startup_projects
            WHERE public.startup_projects.id = revenue_predictions.project_id
            AND public.startup_projects.user_id = auth.uid()
        )
    );
