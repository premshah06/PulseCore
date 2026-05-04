import { render, screen } from "@testing-library/react"
import { LiveMetricChart } from "@/components/LiveMetricChart"
import type { AnomalyRecord } from "@/types"

const RECORD: AnomalyRecord = {
  id: 1,
  source_id: "host-01",
  domain: "infra",
  timestamp: "2024-06-01T12:00:00Z",
  anomaly_score: 0.92,
  confidence_tier: "auto_flag",
  is_anomaly: true,
  raw_label: -1,
  latency_ms: 2.1,
  detected_at: "2024-06-01T12:00:01Z",
}

describe("LiveMetricChart", () => {
  it("renders empty-state message when feed is empty", () => {
    render(<LiveMetricChart feed={[]} domain={null} />)
    expect(screen.getByText(/waiting for live data/i)).toBeInTheDocument()
  })

  it("does not throw with empty feed", () => {
    expect(() => render(<LiveMetricChart feed={[]} domain={null} />)).not.toThrow()
  })

  it("renders a chart when feed has data", () => {
    const { container } = render(
      <LiveMetricChart feed={[RECORD, { ...RECORD, id: 2, source_id: "host-02" }]} domain={null} />
    )
    // ResponsiveContainer renders a div wrapper; chart SVG is inside
    expect(container.firstChild).not.toBeNull()
    // No empty-state text
    expect(screen.queryByText(/waiting/i)).toBeNull()
  })

  it("filters by domain", () => {
    const ecomRecord: AnomalyRecord = {
      ...RECORD,
      id: 3,
      domain: "ecommerce",
      source_id: "shop-01",
    }
    render(<LiveMetricChart feed={[RECORD, ecomRecord]} domain="ecommerce" />)
    // With only 1 ecommerce record there are chart points — no empty state
    expect(screen.queryByText(/waiting/i)).toBeNull()
  })

  it("shows empty state when domain has no matching records", () => {
    render(<LiveMetricChart feed={[RECORD]} domain="iot" />)
    expect(screen.getByText(/waiting/i)).toBeInTheDocument()
  })
})
