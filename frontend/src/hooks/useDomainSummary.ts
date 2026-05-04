"use client"

import { useEffect, useState } from "react"
import { fetchDomainSummary } from "@/lib/api"
import type { Domain, DomainSummary } from "@/types"

export function useDomainSummary(domain: Domain | null): {
  summaries: DomainSummary[]
  loading: boolean
} {
  const [summaries, setSummaries] = useState<DomainSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetchDomainSummary(domain)
      .then(setSummaries)
      .catch(() => setSummaries([]))
      .finally(() => setLoading(false))
  }, [domain])

  return { summaries, loading }
}
