"use client"

import { motion } from "framer-motion"
import { AnimatedCounter } from "@/components/AnimatedCounter"
import type { Domain, DomainSummary as DS } from "@/types"

const DOMAIN_COLORS: Record<string, string> = {
  infra:     "from-violet-500/20 to-violet-500/0",
  ecommerce: "from-sky-500/20 to-sky-500/0",
  iot:       "from-emerald-500/20 to-emerald-500/0",
}

interface CardProps {
  label: string
  value: number
  formatter?: (n: number) => string
  sub: string
  gradient: string
  delay?: number
}

function StatCard({ label, value, formatter, sub, gradient, delay = 0 }: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.97 }}
      whileInView={{ opacity: 1, y: 0, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-2xl border border-white/[0.07] p-5 bg-white/[0.025]"
    >
      {/* Top gradient accent */}
      <div className={`absolute inset-x-0 top-0 h-px bg-gradient-to-r ${gradient}`} />
      {/* Subtle inner glow */}
      <div className={`absolute inset-0 bg-gradient-to-b ${gradient} opacity-30 pointer-events-none`} />

      <p className="relative text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 mb-2">
        {label}
      </p>
      <p className="relative text-3xl font-black text-white leading-none tabular-nums">
        <AnimatedCounter value={value} formatter={formatter} />
      </p>
      <p className="relative text-xs text-slate-600 mt-2">{sub}</p>
    </motion.div>
  )
}

interface Props {
  summaries: DS[]
  domain: Domain | null
  loading: boolean
}

export function DomainSummary({ summaries, domain, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="rounded-2xl border border-white/[0.06] h-28 bg-white/[0.02] animate-pulse" />
        ))}
      </div>
    )
  }

  const rows = domain ? summaries.filter((s) => s.domain === domain) : summaries
  const grad = domain ? (DOMAIN_COLORS[domain] ?? "from-violet-500/20 to-violet-500/0") : "from-violet-500/20 to-indigo-500/0"

  if (rows.length === 0) {
    return (
      <div className="grid grid-cols-3 gap-4" data-testid="domain-summary">
        {["Total Events", "Anomaly Rate", "Avg Score"].map((l) => (
          <div key={l} className="rounded-2xl border border-white/[0.06] p-5 bg-white/[0.025]">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 mb-2">{l}</p>
            <p className="text-3xl font-black text-slate-700">—</p>
          </div>
        ))}
      </div>
    )
  }

  const totalEvents    = rows.reduce((a, r) => a + r.event_count, 0)
  const totalAnomalies = rows.reduce((a, r) => a + r.anomaly_count, 0)
  const rateRaw        = totalEvents > 0 ? (totalAnomalies / totalEvents) * 100 : 0
  const validScores    = rows.filter((r) => r.avg_anomaly_score !== null)
  const avgScoreRaw    = validScores.length > 0
    ? validScores.reduce((a, r) => a + (r.avg_anomaly_score ?? 0), 0) / validScores.length
    : 0

  return (
    <div className="grid grid-cols-3 gap-4" data-testid="domain-summary">
      <StatCard
        label="Total Events"
        value={totalEvents}
        sub={domain ?? "all domains"}
        gradient={grad}
        delay={0}
      />
      <StatCard
        label="Anomaly Rate"
        value={Math.round(rateRaw * 100)}
        formatter={(n) => (n / 100).toFixed(2) + "%"}
        sub={`${totalAnomalies.toLocaleString()} anomalies detected`}
        gradient={grad}
        delay={0.06}
      />
      <StatCard
        label="Avg Score"
        value={Math.round(avgScoreRaw * 1000)}
        formatter={(n) => (n === 0 ? "—" : (n / 1000).toFixed(3))}
        sub="mean anomaly score"
        gradient={grad}
        delay={0.12}
      />
    </div>
  )
}
