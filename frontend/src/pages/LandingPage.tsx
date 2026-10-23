import { ArrowRight, BarChart3, Database, GitCompare, LineChart, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../components/common/Logo.tsx";

const FEATURES: { title: string; body: string; to: string; icon: LucideIcon }[] = [
  {
    title: "Performance Analytics",
    body: "See your posts at a glance: how many there are, how much people like and comment, and which ones stand out.",
    to: "/dashboard",
    icon: BarChart3,
  },
  {
    title: "Content Comparison",
    body: "Compare types of content fairly, so a long tutorial and a short clip are judged the same way.",
    to: "/analytics",
    icon: GitCompare,
  },
  {
    title: "Trend Analysis",
    body: "See how engagement changes week by week, instead of judging everything by one post.",
    to: "/analytics",
    icon: LineChart,
  },
  {
    title: "Predictions",
    body: "Estimate how a planned post might do, and forecast a video's views once a few counts are saved. Every estimate shows how sure it is.",
    to: "/predictions",
    icon: Sparkles,
  },
];

export function LandingPage() {
  useEffect(() => {
    document.title = "CreatorLens";
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden text-[#16182B]">
      <div className="pointer-events-none absolute -left-16 top-44 hidden h-36 w-36 rounded-full bg-[#EF9620] sm:block" aria-hidden="true" />
      <div className="pointer-events-none absolute -left-10 bottom-16 hidden h-52 w-52 rounded-full border-[26px] border-[#C3B9FB] md:block" aria-hidden="true" />
      <div className="pointer-events-none absolute right-[8%] top-28 hidden h-24 w-24 rounded-full border-[16px] border-[#EF9620] lg:block" aria-hidden="true" />
      <div className="pointer-events-none absolute -right-8 bottom-24 hidden h-44 w-44 rounded-full border-[22px] border-[#2AD4C8] md:block" aria-hidden="true" />

      <header className="sticky top-0 z-30 px-4 pt-4 sm:px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-full border border-white/80 bg-gradient-to-r from-white/95 via-[#f4f0ff]/95 to-[#e9fffb]/95 px-4 py-2.5 shadow-[0_10px_30px_rgba(41,22,225,0.08)] backdrop-blur sm:px-5">
          <Logo />
          <nav className="hidden items-center gap-6 text-sm font-medium text-[#4D535D] md:flex" aria-label="Landing">
            <a href="#features" className="transition hover:text-[#2916E1]">Features</a>
            <a href="#how-it-works" className="transition hover:text-[#2916E1]">How it works</a>
            <Link to="/dashboard" className="transition hover:text-[#2916E1]">Dashboard</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/dashboard" className="btn-primary">
              <span className="sm:hidden">Dashboard</span>
              <span className="hidden sm:inline">Explore Dashboard</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <section className="mx-auto max-w-6xl px-4 pb-6 pt-8 sm:px-6 lg:pt-12">
          <div className="relative overflow-hidden rounded-[2.25rem] bg-gradient-to-br from-[#8B74F0] via-[#5848D2] to-[#14B8A6] px-6 py-10 text-white shadow-[0_30px_70px_rgba(88,72,210,0.35)] sm:px-10 sm:py-14 lg:px-14">
            <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-white/10" aria-hidden="true" />
            <div className="pointer-events-none absolute bottom-6 left-[42%] h-20 w-20 rounded-full bg-[#2AD4C8]/35" aria-hidden="true" />
            <div className="relative grid items-center gap-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <div>
                <p className="text-sm font-semibold text-white/80">Social performance, explained</p>
                <h1 className="mt-3 max-w-xl text-4xl font-normal leading-[1.15] tracking-normal sm:text-5xl lg:text-[3.4rem]">
                  Turn Social Media Data Into Smarter Content Decisions.
                </h1>
                <p className="mt-5 max-w-xl text-base leading-7 text-white/85 sm:text-lg">
                  Views, likes, comments, and shares are easy to collect and hard to compare. CreatorLens lines them up
                  so you can see patterns without treating a single post as a rule.
                </p>
                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                  <Link to="/dashboard" className="btn-teal">
                    Explore Dashboard
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </Link>
                  <a
                    href="#how-it-works"
                    className="inline-flex items-center justify-center rounded-full bg-white/15 px-5 py-2.5 text-sm font-semibold text-white ring-1 ring-white/35 transition hover:bg-white/25"
                  >
                    How It Works
                  </a>
                </div>
              </div>
              <div className="rounded-[1.75rem] bg-gradient-to-br from-white via-[#f7f4ff] to-[#f3fffc] p-6 text-[#16182B] shadow-[0_18px_40px_rgba(22,24,43,0.16)]">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#EF9620]">What you can do today</p>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-[#4D535D]">
                  <li className="rounded-2xl bg-[#F7F7FB] px-4 py-3">
                    Upload a CSV, PDF, or Word file. It's saved and analysed, and you can ask questions about it.
                  </li>
                  <li className="rounded-2xl bg-[#F7F7FB] px-4 py-3">
                    Paste a public YouTube link to get a plain-language check-up, a friendly roast, and tips for next time.
                  </li>
                  <li className="rounded-2xl bg-[#F7F7FB] px-4 py-3">
                    Predict a planned post's engagement, and forecast a video's views once you have a few saved counts.
                    We never make up a number.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-4 px-4 py-10 sm:px-6 md:grid-cols-2">
          <article className="card p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5848D2]">The problem</p>
            <h2 className="mt-3 text-2xl font-normal tracking-normal sm:text-3xl">Numbers are easy. Comparing them is not.</h2>
            <p className="mt-3 leading-7 text-[#4D535D]">
              You can see the numbers for each post, but comparing lots of posts by hand is slow. It's easy to
              jump to conclusions from one lucky spike, or to compare numbers that were worked out differently.
            </p>
          </article>
          <article className="card p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#EF9620]">The approach</p>
            <h2 className="mt-3 text-2xl font-normal tracking-normal sm:text-3xl">One measurement for every post.</h2>
            <p className="mt-3 leading-7 text-[#4D535D]">
              CreatorLens measures every post the same way: how many people liked, commented, or shared compared
              with how many viewed. Try it with the built-in demo data, or upload your own file and it's saved for
              you. Sign-in is paused for now, so your work is saved on this computer.
            </p>
          </article>
        </section>

        <section id="features" className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#5848D2]">Features</p>
          <h2 className="mt-2 max-w-xl text-3xl font-normal tracking-normal sm:text-4xl">See the work, then open it.</h2>
          <p className="mt-3 max-w-2xl text-[#4D535D]">
            Click a card to open that part of the app. Pages that show demo data are clearly marked.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <Link
                  key={feature.title}
                  to={feature.to}
                  className="card p-6 transition hover:-translate-y-0.5 hover:shadow-[0_20px_44px_rgba(41,22,225,0.12)]"
                >
                  <span className="inline-flex rounded-2xl bg-[#F3F0FF] p-3 text-[#2916E1]">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <h3 className="mt-4 text-lg font-normal">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#4D535D]">{feature.body}</p>
                </Link>
              );
            })}
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <div className="relative overflow-hidden rounded-[2.25rem] bg-gradient-to-br from-[#7A5CFF] via-[#2916E1] to-[#EF9620] px-6 py-10 text-white shadow-[0_24px_60px_rgba(41,22,225,0.28)] sm:px-10 sm:py-12">
            <div className="pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full bg-white/10" aria-hidden="true" />
            <div className="pointer-events-none absolute bottom-0 left-1/3 h-24 w-24 rounded-full bg-[#2AD4C8]/30" aria-hidden="true" />
            <h2 className="relative text-3xl font-normal tracking-normal sm:text-4xl">Dataset, analysis, insights</h2>
            <ol className="relative mt-8 grid gap-4 md:grid-cols-3">
              <li className="rounded-[1.5rem] bg-gradient-to-br from-white via-[#f7f4ff] to-[#fff8ee] p-5 text-[#16182B] shadow-lg">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#EF9620] text-[#1a1206]">
                  <Database className="h-5 w-5" aria-hidden="true" />
                </span>
                <p className="mt-4 text-sm font-semibold text-[#5848D2]">01 · Dataset</p>
                <h3 className="mt-1 font-bold">Bring your data</h3>
                <p className="mt-2 text-sm leading-6 text-[#4D535D]">
                  Upload a CSV of your posts, or a PDF or Word file. We check it, save it, and work out the numbers
                  for you.
                </p>
                <Link to="/upload" className="mt-4 inline-flex text-sm font-semibold text-[#2916E1]">
                  Open upload
                </Link>
              </li>
              <li className="rounded-[1.5rem] bg-gradient-to-br from-white via-[#f7f4ff] to-[#fff8ee] p-5 text-[#16182B] shadow-lg">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#2AD4C8] text-[#102422]">
                  <BarChart3 className="h-5 w-5" aria-hidden="true" />
                </span>
                <p className="mt-4 text-sm font-semibold text-[#5848D2]">02 · Analysis</p>
                <h3 className="mt-1 font-bold">See the results</h3>
                <p className="mt-2 text-sm leading-6 text-[#4D535D]">
                  Summary cards, a trend line, and category charts show how your posts are doing. Until you open
                  one of your own files, they show demo data.
                </p>
                <Link to="/analytics" className="mt-4 inline-flex text-sm font-semibold text-[#2916E1]">
                  Open analytics
                </Link>
              </li>
              <li className="rounded-[1.5rem] bg-gradient-to-br from-white via-[#f7f4ff] to-[#fff8ee] p-5 text-[#16182B] shadow-lg">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#F3F0FF] text-[#2916E1]">
                  <LineChart className="h-5 w-5" aria-hidden="true" />
                </span>
                <p className="mt-4 text-sm font-semibold text-[#5848D2]">03 · Insights</p>
                <h3 className="mt-1 font-bold">Get honest takeaways</h3>
                <p className="mt-2 text-sm leading-6 text-[#4D535D]">
                  Each insight tells you what the numbers show and what they can't prove, so you know how much to
                  trust it.
                </p>
                <Link to="/insights" className="mt-4 inline-flex text-sm font-semibold text-[#2916E1]">
                  Open insights
                </Link>
              </li>
            </ol>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-[#e4e2ee]/80">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-[#4D535D] sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>CreatorLens · Your uploads and analyses are saved on this computer. Sign-in is paused for now.</p>
          <nav className="flex gap-4 font-semibold" aria-label="Footer">
            <Link to="/dashboard" className="hover:text-[#2916E1]">Dashboard</Link>
            <Link to="/upload" className="hover:text-[#2916E1]">Upload</Link>
            <Link to="/predictions" className="hover:text-[#2916E1]">Predictions</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
