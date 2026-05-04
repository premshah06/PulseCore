import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { AnomalyPanel } from "@/components/AnomalyPanel"
import type { AnomalyRecord } from "@/types"

const base: Omit<AnomalyRecord, "id" | "confidence_tier" | "anomaly_score" | "is_anomaly" | "raw_label"> = {
  source_id: "host-01",
  domain: "infra",
  timestamp: "2024-06-01T12:00:00Z",
  detected_at: "2024-06-01T12:00:01Z",
  latency_ms: 2.5,
}

const AUTO_FLAG: AnomalyRecord = { ...base, id: 1, confidence_tier: "auto_flag", anomaly_score: 0.92, is_anomaly: true, raw_label: -1 }
const SOFT_ALERT: AnomalyRecord = { ...base, id: 2, source_id: "host-02", confidence_tier: "soft_alert", anomaly_score: 0.71, is_anomaly: false, raw_label: 1 }
const LOG_ONLY: AnomalyRecord = { ...base, id: 3, source_id: "host-03", confidence_tier: "log_only", anomaly_score: 0.30, is_anomaly: false, raw_label: 1 }

describe("AnomalyPanel", () => {
  describe("tier color coding", () => {
    it("renders AUTO FLAG badge for auto_flag tier", () => {
      render(<AnomalyPanel anomalies={[AUTO_FLAG]} domain={null} loading={false} />)
      expect(screen.getByText("AUTO FLAG")).toBeInTheDocument()
    })

    it("renders SOFT ALERT badge for soft_alert tier", () => {
      render(<AnomalyPanel anomalies={[SOFT_ALERT]} domain={null} loading={false} />)
      expect(screen.getByText("SOFT ALERT")).toBeInTheDocument()
    })

    it("renders LOG ONLY badge for log_only tier", () => {
      render(<AnomalyPanel anomalies={[LOG_ONLY]} domain={null} loading={false} />)
      expect(screen.getByText("LOG ONLY")).toBeInTheDocument()
    })

    it("auto_flag badge has red styling", () => {
      render(<AnomalyPanel anomalies={[AUTO_FLAG]} domain={null} loading={false} />)
      const badge = screen.getByText("AUTO FLAG")
      expect(badge.className).toMatch(/red/)
    })

    it("soft_alert badge has amber styling", () => {
      render(<AnomalyPanel anomalies={[SOFT_ALERT]} domain={null} loading={false} />)
      const badge = screen.getByText("SOFT ALERT")
      expect(badge.className).toMatch(/amber/)
    })

    it("log_only badge has slate styling", () => {
      render(<AnomalyPanel anomalies={[LOG_ONLY]} domain={null} loading={false} />)
      const badge = screen.getByText("LOG ONLY")
      expect(badge.className).toMatch(/slate/)
    })
  })

  describe("sorting", () => {
    it("renders highest-scoring anomaly first", () => {
      render(<AnomalyPanel anomalies={[LOG_ONLY, SOFT_ALERT, AUTO_FLAG]} domain={null} loading={false} />)
      const items = screen.getAllByRole("listitem")
      // First item should contain the auto_flag badge
      expect(items[0]).toHaveTextContent("AUTO FLAG")
    })
  })

  describe("expand on click", () => {
    it("shows details after clicking a row", async () => {
      render(<AnomalyPanel anomalies={[AUTO_FLAG]} domain={null} loading={false} />)
      const item = screen.getAllByRole("listitem")[0]
      await userEvent.click(item)
      expect(screen.getByText(/Raw label/i)).toBeInTheDocument()
    })

    it("collapses (aria-expanded=false) after clicking again", async () => {
      render(<AnomalyPanel anomalies={[AUTO_FLAG]} domain={null} loading={false} />)
      const item = screen.getAllByRole("listitem")[0]
      await userEvent.click(item)
      expect(item).toHaveAttribute("aria-expanded", "true")
      await userEvent.click(item)
      expect(item).toHaveAttribute("aria-expanded", "false")
    })
  })

  describe("empty / loading states", () => {
    it("shows loading skeletons while loading", () => {
      const { container } = render(
        <AnomalyPanel anomalies={[]} domain={null} loading={true} />
      )
      const pulses = container.querySelectorAll(".animate-pulse")
      expect(pulses.length).toBeGreaterThan(0)
    })

    it("shows no-anomalies message when empty", () => {
      render(<AnomalyPanel anomalies={[]} domain={null} loading={false} />)
      expect(screen.getByText(/no anomalies/i)).toBeInTheDocument()
    })
  })
})
