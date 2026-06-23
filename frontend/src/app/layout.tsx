import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/navbar";

export const metadata: Metadata = {
  title: "Validator.AI | Venture-Grade Startup Validation Platform",
  description: "AI-powered multi-agent platform validating startup business concepts, market opportunity, CAC metrics, competitor SWOTS, and financials.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-slate-950 text-slate-50 selection:bg-sky-500/30 selection:text-sky-200">
      <body suppressHydrationWarning className="min-h-full flex flex-col grid-bg relative">
        {/* Glow Effects */}
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-radial-gradient animate-glow pointer-events-none z-0" />
        <div className="absolute bottom-[-15%] right-[-15%] w-[60%] h-[60%] bg-radial-gradient animate-glow pointer-events-none z-0" />
        
        {/* Core Layout Header */}
        <Navbar />
        
        {/* Main Content Area */}
        <main className="flex-1 flex flex-col z-10">
          {children}
        </main>
        
        {/* Footer */}
        <footer className="glass-panel border-t-0 border-x-0 py-8 px-6 text-center text-xs text-slate-500 z-10 mt-auto">
          <p>© {new Date().getFullYear()} Validator.AI platform. Built for founders and investors using LangGraph.</p>
        </footer>
      </body>
    </html>
  );
}
