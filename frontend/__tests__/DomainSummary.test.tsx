import { render, screen } from "@testing-library/react"
import { DomainSummary } from "@/components/DomainSummary"
import type { DomainSummary as DS } from "@/types"

// AnimatedCounter uses requestAnimationFrame which doesn't run to completion in jsdom.
// Mock it to render the final value immediately.
jest.mock("@/components/AnimatedCounter", () => ({
  AnimatedCounter: ({
    value,
    formatter,
  }: {
    value: number
    formatter?: (n: number) => string
  }) => <>{formatter ? formatter(value) : value.toLocaleString()}</>,
}))

const INFRA: DS = {
  domain: "infra",
  event_count: 8900,
  anomaly_count: 42,
  auto_flag_count: 11,
  avg_anomaly_score: 0.84,
}

const ECOM: DS = {
  domain: "ecommerce",
  event_count: 3200,
  anomaly_count: 14,
  auto_flag_count: 3,
  avg_anomaly_score: 0.71,
}

const IOT: DS = {
  domain: "iot",
  event_count: 5400,
  anomaly_count: 28,
  auto_flag_count: 7,
  avg_anomaly_score: 0.78,
}

describe("DomainSummary", () => {
  describe("single domain", () => {
    it("shows event count for infra", () => {
      render(<DomainSummary summaries={[INFRA]} domain="infra" loading={false} />)
      expect(screen.getByText("8,900")).toBeInTheDocument()
    })

    it("shows anomaly rate for infra", () => {
      render(<DomainSummary summaries={[INFRA]} domain="infra" loading={false} />)
      // 42 / 8900 * 100 = 0.47%
      expect(screen.getByText(/0\.47%/)).toBeInTheDocument()
    })

    it("shows avg score for infra", () => {
      render(<DomainSummary summaries={[INFRA]} domain="infra" loading={false} />)
      expect(screen.getByText("0.840")).toBeInTheDocument()
    })
  })

  describe("all domains aggregated", () => {
    it("sums event counts across all domains", () => {
      render(<DomainSummary summaries={[INFRA, ECOM, IOT]} domain={null} loading={false} />)
      // 8900 + 3200 + 5400 = 17500
      expect(screen.getByText("17,500")).toBeInTheDocument()
    })

    it("calculates anomaly rate across all domains", () => {
      render(<DomainSummary summaries={[INFRA, ECOM, IOT]} domain={null} loading={false} />)
      // (42 + 14 + 28) / 17500 * 100 = 0.48%
      expect(screen.getByText(/0\.48%/)).toBeInTheDocument()
    })
  })

  describe("loading state", () => {
    it("renders skeleton placeholders while loading", () => {
      const { container } = render(
        <DomainSummary summaries={[]} domain={null} loading={true} />
      )
      const pulses = container.querySelectorAll(".animate-pulse")
      expect(pulses.length).toBeGreaterThan(0)
    })
  })

  describe("empty state", () => {
    it("shows em-dashes when no summaries", () => {
      render(<DomainSummary summaries={[]} domain={null} loading={false} />)
      const dashes = screen.getAllByText("—")
      expect(dashes.length).toBeGreaterThan(0)
    })
  })

  describe("null avg_anomaly_score", () => {
    it("renders em-dash for null average score", () => {
      const noScore = { ...INFRA, avg_anomaly_score: null }
      render(<DomainSummary summaries={[noScore]} domain="infra" loading={false} />)
      expect(screen.getByText("—")).toBeInTheDocument()
    })
  })
})
