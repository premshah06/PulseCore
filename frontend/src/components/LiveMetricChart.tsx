"use client"

import { useMemo } from "react"
import { motion } from "framer-motion"
import {
  CartesianGrid, Legend, Line, LineChart,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts"
import type { AnomalyRecord, Domain } from "@/types"

const PALETTE = [
  "#818cf8", "#34d399", "#f472b6", "#fb923c",
  "#38bdf8", "#a78bfa", "#facc15", "#f87171",
]

interface ChartPoint { t: string; [src: string]: number | string }

interface Props { feed: AnomalyRecord[]; domain: Domain | null }

function fmt(iso: string) {
  try { return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) }
  catch { return iso }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomDot = (props: any) => {
  const { cx, cy, value } = props
  if (value === undefined) return null
  const color = value > 0.85 ? "#ef4444" : value >= 0.6 ? "#f59e0b" : "#818cf8"
  return <circle cx={cx} cy={cy} r={3} fill={color} stroke="none" opacity={0.9} />
}

export function LiveMetricChart({ feed, domain }: Props) {
  const { points, sources } = useMemo(() => {
    const filtered = domain ? feed.filter((r) => r.domain === domain) : feed
    const sources  = Array.from(new Set(filtered.map((r) => r.source_id))).slice(0, 8)
    const byTime   = new Map<string, ChartPoint>()

    for (const r of [...filtered].reverse()) {
      const t = fmt(r.timestamp)
      if (!byTime.has(t)) byTime.set(t, { t })
      byTime.get(t)![r.source_id] = r.anomaly_score
    }

    return { points: Array.from(byTime.values()), sources }
  }, [feed, domain])

  if (points.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-52 gap-4">
        {/* Scanning radar animation */}
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border border-violet-500/20" />
          <div className="absolute inset-2 rounded-full border border-violet-500/15" />
          <div className="absolute inset-4 rounded-full border border-violet-500/10" />
          <motion.div
            className="absolute inset-0 rounded-full border-t-2 border-violet-500/60"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          />
        </div>
        <p className="text-sm text-slate-500">Waiting for live data…</p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="h-64 w-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 6, right: 20, bottom: 4, left: 0 }}>
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          <CartesianGrid
            strokeDasharray="1 6"
            stroke="rgba(255,255,255,0.05)"
            vertical={false}
          />
          <XAxis
            dataKey="t"
            tick={{ fill: "#475569", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[0, 1]}
            ticks={[0, 0.25, 0.5, 0.6, 0.75, 0.85, 1]}
            tick={{ fill: "#475569", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={28}
          />
          <Tooltip
            contentStyle={{
              background: "rgba(2,8,23,0.95)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 10,
              fontSize: 11,
              color: "#e2e8f0",
              boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
            }}
            labelStyle={{ color: "#64748b", marginBottom: 4 }}
            cursor={{ stroke: "rgba(255,255,255,0.08)" }}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#64748b", paddingTop: 8 }}
            iconType="circle"
            iconSize={8}
          />
          <ReferenceLine
            y={0.85}
            stroke="rgba(239,68,68,0.4)"
            strokeDasharray="3 4"
            strokeWidth={1}
            label={{ value: "0.85", fill: "rgba(239,68,68,0.6)", fontSize: 9, position: "insideTopRight" }}
          />
          <ReferenceLine
            y={0.60}
            stroke="rgba(245,158,11,0.35)"
            strokeDasharray="3 4"
            strokeWidth={1}
            label={{ value: "0.60", fill: "rgba(245,158,11,0.6)", fontSize: 9, position: "insideTopRight" }}
          />

          {sources.map((src, i) => (
            <Line
              key={src}
              type="monotone"
              dataKey={src}
              name={src}
              stroke={PALETTE[i % PALETTE.length]}
              strokeWidth={1.5}
              dot={<CustomDot />}
              activeDot={{ r: 5, strokeWidth: 0, filter: "url(#glow)" }}
              isAnimationActive={false}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  )
}
