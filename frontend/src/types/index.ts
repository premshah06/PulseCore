/**
 * TypeScript interfaces mirroring CONTRACTS.md exactly.
 * Phase 6 is the terminal consumer — these types must not diverge
 * from the Phase 5 OpenAPI schema without coordinating both sides.
 */

export type Domain = "infra" | "ecommerce" | "iot"
export type ConfidenceTier = "auto_flag" | "soft_alert" | "log_only"

// ── Phase 4 → Phase 5 ─────────────────────────────────────────────────────────

export interface AnomalyResult {
  source_id: string
  domain: Domain
  timestamp: string       // ISO-8601
  anomaly_score: number   // [0, 1]
  confidence_tier: ConfidenceTier
  is_anomaly: boolean
  raw_label: number       // 1 = normal, -1 = anomaly
  latency_ms: number
}

// ── Phase 5 REST API ──────────────────────────────────────────────────────────

export interface AnomalyRecord extends AnomalyResult {
  id: string
  detected_at: string     // ISO-8601
}

export interface AnomalyPage {
  items: AnomalyRecord[]
  total: number
  limit: number
}

export interface EventRecord {
  event_id: string
  source_id: string
  domain: Domain
  timestamp: string
  metrics: Record<string, number>
  metadata: Record<string, unknown>
}

export interface EventPage {
  items: EventRecord[]
  total: number
  limit: number
  offset: number
}

export interface DomainSummary {
  domain: Domain
  event_count: number
  anomaly_count: number
  auto_flag_count: number
  avg_anomaly_score: number | null
}

// ── Phase 5 → Phase 6: WebSocket LiveUpdate ───────────────────────────────────

export interface LiveUpdate {
  type: "anomaly"
  data: AnomalyRecord
}
