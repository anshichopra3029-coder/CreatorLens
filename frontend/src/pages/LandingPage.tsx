import { ArrowRight, BarChart3, Database, GitCompare, LineChart, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../components/common/Logo.tsx";

const FEATURES: { title: string; body: string; to: string; icon: LucideIcon }[] = [
  {
    title: "Performance Analytics",
    body: "See how many posts are in view, the average engagement rate, and the interactions behind it.",
    to: "/dashboard",
    icon: BarChart3,
  },
  {
    title: "Content Comparison",
    body: "Compare categories with one shared rate so a tutorial and a short clip are measured the same way.",
    to: "/analytics",
    icon: GitCompare,
  },
  {
    title: "Trend Analysis",
    body: "Follow the average engagement rate across weeks instead of judging the feed one post at a time.",
    to: "/analytics",
    icon: LineChart,
  },
  {
    title: "Future ML Insights",
    body: "A later phase may estimate engagement. This build has no trained model and will not invent a score.",
    to: "/predictions",
    icon: Sparkles,
  },
];

export function LandingPage() {
  useEffect(() => {
    document.title = "CreatorLens";
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex" aria-label="Landing">
            <a href="#features" className="hover:text-slate-900">Features</a>
            <a href="#how-it-works" className="hover:text-slate-900">How it works</a>
            <Link to="/dashboard" className="hover:text-slate-900">Dashboard</Link>
          </nav>
          <Link to="/dashboard" className="btn-primary">
            <span className="sm:hidden">Dashboard</span>
            <span className="hidden sm:inline">Explore Dashboard</span>
          </Link>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:items-center lg:py-24">
          <div>
            <p className="text-sm font-semibold text-indigo-700">Social performance, explained</p>
            <h1 className="mt-3 max-w-xl text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
              Turn Social Media Data Into Smarter Content Decisions.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-slate-600">
              Views, likes, comments, and shares are easy to collect and hard to compare. CreatorLens lines them up
              so you can see patterns without treating a single post as a rule.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/dashboard" className="btn-primary">
                Explore Dashboard
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <a href="#how-it-works" className="btn-secondary">
                How It Works
              </a>
            </div>
          </div>
          <div className="card p-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">What this phase shows</p>
            <ul className="mt-4 space-y-4 text-sm leading-6 text-slate-600">
              <li className="rounded-lg bg-slate-50 px-4 py-3">
                Dashboard, analytics, and insights use a built-in demo dataset. Every sample metric is labelled.
              </li>
              <li className="rounded-lg bg-slate-50 px-4 py-3">
                Upload checks a real CSV and reports columns and row count. The file is not saved or analyzed.
              </li>
              <li className="rounded-lg bg-slate-50 px-4 py-3">
                Predictions stay unavailable until a model is trained and evaluated. No score is fabricated.
              </li>
            </ul>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-white">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 sm:px-6 md:grid-cols-2">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">The problem</h2>
              <p className="mt-3 leading-7 text-slate-600">
                Creators can see individual numbers, but comparing many posts by hand is slow. It is easy to guess
                from a recent spike, or to mix rates that were calculated in different ways.
              </p>
            </div>
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">The approach</h2>
              <p className="mt-3 leading-7 text-slate-600">
                CreatorLens keeps one view-based engagement rate: (likes + comments + shares) / views × 100.
                Phase 1 demonstrates the workflow with demo data and a real upload check. Cleaning, saved datasets,
                and accounts come later.
              </p>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <h2 className="text-2xl font-semibold tracking-tight">Features</h2>
          <p className="mt-2 max-w-2xl text-slate-600">
            Each card opens the page that holds that part of the product. Demo screens say so in the interface.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <Link key={feature.title} to={feature.to} className="card p-5 transition hover:border-indigo-200">
                  <span className="inline-flex rounded-lg bg-indigo-50 p-2 text-indigo-700">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <h3 className="mt-4 text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{feature.body}</p>
                </Link>
              );
            })}
          </div>
        </section>

        <section id="how-it-works" className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
            <h2 className="text-2xl font-semibold tracking-tight">Dataset, analysis, insights</h2>
            <ol className="mt-8 grid gap-4 md:grid-cols-3">
              <li className="card p-5">
                <Database className="h-5 w-5 text-indigo-700" aria-hidden="true" />
                <p className="mt-4 text-sm font-semibold text-indigo-700">01 · Dataset</p>
                <h3 className="mt-1 font-semibold">Bring a CSV</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  The upload page checks the file type, size, and whether Pandas can read it. You get the filename,
                  size, row count, and column names.
                </p>
                <Link to="/upload" className="mt-4 inline-flex text-sm font-semibold text-indigo-700">
                  Open upload
                </Link>
              </li>
              <li className="card p-5">
                <BarChart3 className="h-5 w-5 text-indigo-700" aria-hidden="true" />
                <p className="mt-4 text-sm font-semibold text-indigo-700">02 · Analysis</p>
                <h3 className="mt-1 font-semibold">Review the demo figures</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Summary cards, the trend line, and category bars are calculated on the server from the demo file.
                  Filters on Analytics ask the API again.
                </p>
                <Link to="/analytics" className="mt-4 inline-flex text-sm font-semibold text-indigo-700">
                  Open analytics
                </Link>
              </li>
              <li className="card p-5">
                <LineChart className="h-5 w-5 text-indigo-700" aria-hidden="true" />
                <p className="mt-4 text-sm font-semibold text-indigo-700">03 · Insights</p>
                <h3 className="mt-1 font-semibold">Read the limits with the result</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Insight cards quote the demo calculation and say they are not causal. They do not change when you
                  upload a file in this phase.
                </p>
                <Link to="/insights" className="mt-4 inline-flex text-sm font-semibold text-indigo-700">
                  Open insights
                </Link>
              </li>
            </ol>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>CreatorLens · Phase 1 foundation. No sign-in and no saved datasets yet.</p>
          <nav className="flex gap-4" aria-label="Footer">
            <Link to="/dashboard" className="hover:text-slate-800">Dashboard</Link>
            <Link to="/upload" className="hover:text-slate-800">Upload</Link>
            <Link to="/predictions" className="hover:text-slate-800">Predictions</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
