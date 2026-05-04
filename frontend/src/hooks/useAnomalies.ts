"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { fetchAnomalies } from "@/lib/api"
import type { AnomalyRecord, ConfidenceTier } from "@/types"

const POLL_MS = 10_000

export interface AnomaliesResult {
  anomalies: AnomalyRecord[]
  loading: boolean
  error: string | null
}

export function useAnomalies(tier: ConfidenceTier | null): AnomaliesResult {
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const load = useCallback(async () => {
    try {
      const page = await fetchAnomalies(tier)
      setAnomalies(page.items)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "fetch failed")
    } finally {
      setLoading(false)
    }
  }, [tier])

  useEffect(() => {
    void load()
    intervalRef.current = setInterval(() => void load(), POLL_MS)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [load])

  return { anomalies, loading, error }
}
