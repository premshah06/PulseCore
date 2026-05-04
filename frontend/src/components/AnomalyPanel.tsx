"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import type { AnomalyRecord, ConfidenceTier, Domain } from "@/types"

const TIER_CFG: Record<
  ConfidenceTier,
  { border: string; badge: string; dot: string; glow: string; label: string }
> = {
  auto_flag: {
    border: "border-l-red-500",
    badge:  "bg-red-500/15 text-red-300 ring-1 ring-red-500/30",
    dot:    "bg-red-400 shadow-[0_0_8px_rgba(239,68,68,0.8)]",
    glow:   "hover:shadow-[0_0_30px_rgba(239,68,68,0.08)]",
    label:  "AUTO FLAG",
  },
  soft_alert: {
    border: "border-l-amber-400",
    badge:  "bg-amber-400/15 text-amber-300 ring-1 ring-amber-400/30",
    dot:    "bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)]",
    glow:   "hover:shadow-[0_0_30px_rgba(245,158,11,0.06)]",
    label:  "SOFT ALERT",
  },
  log_only: {
    border: "border-l-slate-600",
    badge:  "bg-slate-700/50 text-slate-400 ring-1 ring-slate-600/30",
    dot:    "bg-slate-500",
    glow:   "",
    label:  "LOG ONLY",
  },
}

const SCORE_COLOR = (s: number) =>
  s > 0.85 ? "#ef4444" : s >= 0.6 ? "#f59e0b" : "#475569"

interface Props {
  anomalies: AnomalyRecord[]
  domain: Domain | null
  loading: boolean
}

export function AnomalyPanel({ anomalies, domain, loading }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  const sorted = [...(domain ? anomalies.filter((a) => a.domain === domain) : anomalies)]
    .sort((a, b) => b.anomaly_score - a.anomaly_score)

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: [0.4, 0.7, 0.4] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.15 }}
            className="h-16 rounded-xl bg-white/[0.03] border border-white/[0.05] animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (sorted.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-20 gap-3"
      >
        <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <p className="text-sm text-slate-500">No anomalies detected</p>
      </motion.div>
    )
  }

  return (
    <ul className="space-y-2" role="list">
      <AnimatePresence initial={false}>
        {sorted.map((a, idx) => {
          const cfg   = TIER_CFG[a.confidence_tier]
          const isOpen = expanded === a.id

          return (
            <motion.li
              key={a.id}
              layout
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              transition={{ duration: 0.28, delay: idx < 8 ? idx * 0.03 : 0 }}
              aria-expanded={isOpen}
              className={[
                "rounded-xl border-l-4 border border-white/[0.05]",
                "bg-white/[0.02] transition-all duration-200 cursor-pointer select-none",
                cfg.border, cfg.glow,
              ].join(" ")}
              onClick={() => setExpanded(isOpen ? null : a.id)}
            >
              {/* ── Collapsed row ───────────────────────────── */}
              <div className="px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  {/* Left */}
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 pulse-dot ${cfg.dot}`} />
                    <span className="text-sm font-semibold text-slate-200 truncate">
                      {a.source_id}
                    </span>
                    <span className="text-[11px] text-slate-600 font-medium">{a.domain}</span>
                  </div>
                  {/* Right */}
                  <div className="flex items-center gap-2.5 flex-shrink-0">
                    <span className="text-sm font-mono font-bold text-slate-300 tabular-nums">
                      {a.anomaly_score.toFixed(3)}
                    </span>
                    <span className={`text-[9px] font-black px-2 py-[3px] rounded-full tracking-wider ${cfg.badge}`}>
                      {cfg.label}
                    </span>
                    <motion.span
                      animate={{ rotate: isOpen ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                      className="text-slate-600 text-[10px]"
                    >
                      ▼
                    </motion.span>
                  </div>
                </div>

                {/* Score bar */}
                <div className="mt-2 h-[3px] w-full bg-white/[0.05] rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: SCORE_COLOR(a.anomaly_score) }}
                    initial={{ width: 0 }}
                    animate={{ width: `${a.anomaly_score * 100}%` }}
                    transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
                  />
                </div>
              </div>

              {/* ── Expanded detail ──────────────────────────── */}
              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.22 }}
                    className="overflow-hidden"
                  >
                    <dl className="mx-4 mb-3 grid grid-cols-2 gap-x-8 gap-y-1.5 text-xs border-t border-white/[0.05] pt-3">
                      {[
                        ["Detected at", new Date(a.detected_at).toLocaleString()],
                        ["Event time",  new Date(a.timestamp).toLocaleString()],
                        ["Raw label",   a.raw_label === -1 ? "−1 (anomaly)" : "1 (normal)"],
                        ["Inference",   `${a.latency_ms.toFixed(2)} ms`],
                      ].map(([k, v]) => (
                        <div key={String(k)}>
                          <dt className="text-slate-600">{k}</dt>
                          <dd className="text-slate-300 font-medium">{v}</dd>
                        </div>
                      ))}
                    </dl>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.li>
          )
        })}
      </AnimatePresence>
    </ul>
  )
}
