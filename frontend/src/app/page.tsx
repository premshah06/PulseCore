"use client"

import { useRef, useState } from "react"
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion"
import { DomainSelector } from "@/components/DomainSelector"
import { LiveMetricChart } from "@/components/LiveMetricChart"
import { AnomalyPanel } from "@/components/AnomalyPanel"
import { DomainSummary } from "@/components/DomainSummary"
import { AnimatedCounter } from "@/components/AnimatedCounter"
import { useLiveFeed } from "@/hooks/useLiveFeed"
import { useAnomalies } from "@/hooks/useAnomalies"
import { useDomainSummary } from "@/hooks/useDomainSummary"
import type { Domain } from "@/types"

/* ── Helpers ──────────────────────────────────────────────────────── */

function LiveBadge({ connected }: { connected: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                 bg-white/[0.04] border border-white/[0.07] text-xs text-slate-400"
    >
      <span
        className={[
          "w-1.5 h-1.5 rounded-full",
          connected
            ? "bg-emerald-400 pulse-dot shadow-[0_0_6px_#34d399]"
            : "bg-slate-600",
        ].join(" ")}
      />
      {connected ? "Live feed active" : "Reconnecting…"}
    </motion.div>
  )
}

function SectionHeading({
  eyebrow,
  title,
  sub,
}: {
  eyebrow: string
  title: string
  sub?: string
}) {
  return (
    <div className="mb-5">
      <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-violet-400/70 mb-1">
        {eyebrow}
      </p>
      <h2 className="text-lg font-bold text-slate-200 leading-snug">{title}</h2>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  )
}

function GlassSection({
  children,
  className = "",
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      className={`glass p-6 ${className}`}
    >
      {children}
    </motion.div>
  )
}

/* ── Page ─────────────────────────────────────────────────────────── */

export default function Page() {
  const [domain, setDomain] = useState<Domain | null>(null)
  const heroRef = useRef<HTMLDivElement>(null)

  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  })
  const heroY       = useTransform(scrollYProgress, [0, 1], ["0%", "22%"])
  const heroOpacity = useTransform(scrollYProgress, [0, 0.75], [1, 0])

  const { feed, connected }          = useLiveFeed(domain)
  const { anomalies, loading: aL }   = useAnomalies(null)
  const { summaries, loading: sL }   = useDomainSummary(domain)

  const totalAutoFlags = anomalies.filter((a) => a.confidence_tier === "auto_flag").length

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#020817]">

      {/* ── Background grid + orbs ─────────────────────────────────── */}
      <div className="fixed inset-0 bg-grid opacity-100 pointer-events-none" />
      <div className="orb w-[700px] h-[500px] bg-violet-700/10 -top-32 -left-40 fixed" />
      <div className="orb orb-delay w-[600px] h-[400px] bg-indigo-600/8 top-20 -right-32 fixed" />
      <div className="orb w-[400px] h-[300px] bg-sky-600/6 bottom-40 left-1/3 fixed" />
      {/* Bottom fade */}
      <div className="fixed bottom-0 inset-x-0 h-32 bg-gradient-to-t from-[#020817] to-transparent pointer-events-none z-10" />

      {/* ── Top status strip ──────────────────────────────────────── */}
      <div className="relative z-20 border-b border-white/[0.05] bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6 h-10 flex items-center justify-between">
          <div className="flex items-center gap-6 text-[11px] text-slate-600">
            <span className="font-semibold text-slate-400">PULSECORE</span>
            <span>·</span>
            <span>3 domains</span>
            <span>·</span>
            <span>
              <AnimatedCounter value={anomalies.length} /> records loaded
            </span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-slate-600">
            {totalAutoFlags > 0 && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-red-400 font-semibold"
              >
                {totalAutoFlags} auto-flag{totalAutoFlags !== 1 ? "s" : ""}
              </motion.span>
            )}
            <LiveBadge connected={connected} />
          </div>
        </div>
      </div>

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <div
        ref={heroRef}
        className="relative z-10 pt-20 pb-16 px-6"
        style={{ minHeight: "42vh" }}
      >
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="max-w-6xl mx-auto"
        >
          {/* Eyebrow */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-wrap items-center gap-3 mb-7"
          >
            <span className="inline-flex items-center gap-1.5 text-[10px] font-black uppercase
                             tracking-[0.22em] text-violet-400 bg-violet-400/8 border
                             border-violet-400/20 px-3 py-1.5 rounded-full">
              <span className="w-1 h-1 rounded-full bg-violet-400 pulse-dot" />
              Real-time · Anomaly Intelligence
            </span>
            <LiveBadge connected={connected} />
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.08 }}
            className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tighter
                       text-white leading-[0.95] mb-5"
          >
            Detect anomalies
            <br />
            <span className="gradient-text">before they cascade.</span>
          </motion.h1>

          {/* Sub */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.18 }}
            className="text-slate-400 text-lg max-w-2xl leading-relaxed mb-10"
          >
            IsolationForest models trained per domain, exported to ONNX, scored in
            &lt;5 ms — streamed live via WebSocket to this dashboard.
          </motion.p>

          {/* Domain selector */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.26 }}
          >
            <DomainSelector value={domain} onChange={setDomain} />
          </motion.div>

          {/* Floating stat pills */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="flex flex-wrap gap-3 mt-8"
          >
            {[
              { label: "Domains", value: "3" },
              { label: "Inference", value: "< 5 ms" },
              { label: "Model", value: "IsolationForest" },
              { label: "Transport", value: "ONNX + WebSocket" },
              { label: "Tests", value: "478 passing" },
            ].map((pill, i) => (
              <motion.div
                key={pill.label}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + i * 0.06 }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full
                           bg-white/[0.03] border border-white/[0.06] text-[11px]"
              >
                <span className="text-slate-500">{pill.label}</span>
                <span className="text-slate-300 font-semibold">{pill.value}</span>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* ── Scroll arrow ──────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="relative z-10 flex justify-center pb-6"
      >
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="text-slate-700 text-lg"
        >
          ↓
        </motion.div>
      </motion.div>

      {/* ── Main sections ─────────────────────────────────────────── */}
      <main className="relative z-10 max-w-6xl mx-auto px-6 pb-32 space-y-6">

        {/* Stats */}
        <section>
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
          >
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-600 mb-4">
              Domain Overview
            </p>
          </motion.div>
          <DomainSummary summaries={summaries} domain={domain} loading={sL} />
        </section>

        {/* Live chart */}
        <GlassSection>
          <SectionHeading
            eyebrow="Live Feed"
            title="Anomaly scores — real-time"
            sub={`${feed.length} events buffered · up to 60 points per source`}
          />
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2 text-[11px] text-slate-600">
              <span className="w-3 h-px bg-red-400/60" />
              <span>auto_flag ≥ 0.85</span>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-slate-600">
              <span className="w-3 h-px bg-amber-400/60" />
              <span>soft_alert ≥ 0.60</span>
            </div>
            <div className="ml-auto">
              <LiveBadge connected={connected} />
            </div>
          </div>
          <LiveMetricChart feed={feed} domain={domain} />
        </GlassSection>

        {/* Anomaly feed */}
        <GlassSection>
          <div className="flex items-start justify-between mb-5">
            <SectionHeading
              eyebrow="Anomaly Feed"
              title="Ranked by score — descending"
              sub="Polls REST API every 10 s · click any row to expand"
            />
            <AnimatePresence>
              {totalAutoFlags > 0 && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full
                             bg-red-500/10 border border-red-500/20 text-xs text-red-300"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 pulse-dot" />
                  {totalAutoFlags} critical
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <AnomalyPanel anomalies={anomalies} domain={domain} loading={aL} />
        </GlassSection>

        {/* Architecture callout */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-40px" }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="rounded-2xl border border-white/[0.06] overflow-hidden"
        >
          <div className="px-6 py-5 bg-gradient-to-r from-violet-900/20 via-indigo-900/10 to-transparent
                          border-b border-white/[0.05]">
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-violet-400/60 mb-1">
              Architecture
            </p>
            <h3 className="text-base font-bold text-slate-300">How data flows to this screen</h3>
          </div>
          <div className="px-6 py-5 grid grid-cols-2 sm:grid-cols-5 gap-px bg-white/[0.04]">
            {[
              { n: "1", label: "Kafka",       sub: "pulse.events topic",    color: "text-orange-400" },
              { n: "2", label: "Consumer",    sub: "Rolling 60 s windows",  color: "text-sky-400"    },
              { n: "3", label: "IsolationForest", sub: "3 ONNX models",     color: "text-violet-400" },
              { n: "4", label: "Sidecar",     sub: "< 5 ms inference",      color: "text-pink-400"   },
              { n: "5", label: "Dashboard",   sub: "WebSocket push ← You",  color: "text-emerald-400"},
            ].map((step) => (
              <div key={step.n} className="bg-[#020817] px-4 py-4">
                <span className={`text-[10px] font-black ${step.color} opacity-60`}>0{step.n}</span>
                <p className="text-sm font-bold text-slate-300 mt-0.5">{step.label}</p>
                <p className="text-[10px] text-slate-600 mt-0.5">{step.sub}</p>
              </div>
            ))}
          </div>
        </motion.div>

      </main>
    </div>
  )
}
