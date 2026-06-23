from typing import Optional

PRICING_TIERS = [
    {
        "code": "founder_basic",
        "name": "Founder Basic",
        "price_inr": 0,
        "period": "month",
        "description": "Ideal for testing early pre-seed micro-concepts.",
        "features": [
            "Create up to 3 startup validation reports",
            "Access to Market Research Agent node data",
            "Competitor analysis profiling (up to 2 competitors)",
            "Standard LangGraph node execution speeds",
            "Web report viewer access",
        ],
        "cta": "Get Started Free",
        "popular": False,
        "is_enterprise": False,
    },
    {
        "code": "founder_pro",
        "name": "Founder Pro",
        "price_inr": 3999,
        "period": "month",
        "description": "Perfect for active founders and startup accelerators.",
        "features": [
            "Unlimited startup validation runs",
            "Activate all 7 audit agents",
            "Deep competitor analysis (up to 5 competitors)",
            "Premium PDF exports + custom formatting styles",
            "3-Year financial projection spreadsheets",
            "Detailed VC-grade feedback checklists",
            "Operational regulatory risk audits",
        ],
        "cta": "Upgrade to Pro",
        "popular": True,
        "is_enterprise": False,
    },
    {
        "code": "venture_partner",
        "name": "Venture Partner",
        "price_inr": 15999,
        "period": "month",
        "description": "Designed for VC analysts, angels, and corporate incubators.",
        "features": [
            "Includes everything in Pro plan",
            "Bulk analysis submission API endpoints",
            "Custom investor persona tuning tools",
            "Priority workflow execution speeds",
            "Enterprise-grade storage and admin controls",
            "Dedicated onboarding support",
            "1-on-1 VC prompt engineering alignment sessions",
        ],
        "cta": "Contact Sales",
        "popular": False,
        "is_enterprise": True,
    },
]


def get_pricing_tiers():
    return PRICING_TIERS


def get_tier_by_code(code: str) -> Optional[dict]:
    for tier in PRICING_TIERS:
        if tier["code"] == code:
            return tier
    return None
