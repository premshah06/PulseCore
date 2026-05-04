"use client"

import { motion } from "framer-motion"
import type { Domain } from "@/types"

const OPTIONS: { label: string; value: Domain | null; emoji: string }[] = [
  { label: "All",       value: null,        emoji: "⬡" },
  { label: "Infra",     value: "infra",     emoji: "⚡" },
  { label: "Ecommerce", value: "ecommerce", emoji: "◈" },
  { label: "IoT",       value: "iot",       emoji: "◎" },
]

interface Props {
  value: Domain | null
  onChange: (d: Domain | null) => void
}

export function DomainSelector({ value, onChange }: Props) {
  return (
    <div
      className="inline-flex p-1 rounded-2xl bg-white/[0.04] border border-white/[0.07]"
      role="tablist"
      aria-label="domain filter"
    >
      {OPTIONS.map((opt) => {
        const active = opt.value === value
        return (
          <motion.button
            key={opt.label}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.value)}
            whileHover={{ scale: active ? 1 : 1.03 }}
            whileTap={{ scale: 0.97 }}
            className={[
              "relative px-4 py-2 rounded-xl text-sm font-semibold transition-colors duration-150",
              active ? "text-white" : "text-slate-500 hover:text-slate-300",
            ].join(" ")}
          >
            {active && (
              <motion.span
                layoutId="domain-active"
                className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600
                           shadow-[0_0_20px_rgba(124,58,237,0.4)]"
                style={{ zIndex: -1 }}
                transition={{ type: "spring", stiffness: 400, damping: 32 }}
              />
            )}
            <span className="mr-1.5 text-[13px]">{opt.emoji}</span>
            {opt.label}
          </motion.button>
        )
      })}
    </div>
  )
}
