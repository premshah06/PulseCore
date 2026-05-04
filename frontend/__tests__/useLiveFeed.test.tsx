import { act, renderHook } from "@testing-library/react"
import { useLiveFeed } from "@/hooks/useLiveFeed"
import type { LiveUpdate } from "@/types"

// ── WebSocket mock ─────────────────────────────────────────────────────────────

let instances: MockWS[] = []

class MockWS {
  url: string
  onopen: (() => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    instances.push(this)
    // Simulate async open
    setTimeout(() => this.onopen?.(), 0)
  }

  close() { this.onclose?.() }
  send(_: string) {}
}

const ANOMALY_MSG: LiveUpdate = {
  type: "anomaly",
  data: {
    id: 1,
    source_id: "host-01",
    domain: "infra",
    timestamp: "2024-06-01T12:00:00Z",
    anomaly_score: 0.92,
    confidence_tier: "auto_flag",
    is_anomaly: true,
    raw_label: -1,
    latency_ms: 2.0,
    detected_at: "2024-06-01T12:00:01Z",
  },
}

// ── Setup / teardown ──────────────────────────────────────────────────────────

beforeEach(() => {
  instances = []
  jest.useFakeTimers()
  // @ts-expect-error — replace global WebSocket with mock
  global.WebSocket = MockWS
})

afterEach(() => {
  jest.useRealTimers()
  jest.clearAllMocks()
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useLiveFeed", () => {
  it("opens a WebSocket on mount", async () => {
    renderHook(() => useLiveFeed("infra"))
    await act(async () => { jest.runAllTimers() })
    expect(instances).toHaveLength(1)
    expect(instances[0].url).toContain("domain=infra")
  })

  it("sets connected=true after onopen", async () => {
    const { result } = renderHook(() => useLiveFeed("infra"))
    await act(async () => { jest.runAllTimers() })
    expect(result.current.connected).toBe(true)
  })

  it("appends incoming anomaly to feed", async () => {
    const { result } = renderHook(() => useLiveFeed("infra"))
    await act(async () => { jest.runAllTimers() })

    act(() => {
      instances[0].onmessage?.({ data: JSON.stringify(ANOMALY_MSG) })
    })

    expect(result.current.feed).toHaveLength(1)
    expect(result.current.feed[0].source_id).toBe("host-01")
  })

  it("reconnects after disconnect (backoff 1 s)", async () => {
    const { result } = renderHook(() => useLiveFeed("infra"))
    await act(async () => { jest.runAllTimers() })
    expect(result.current.connected).toBe(true)

    // Simulate disconnect
    act(() => { instances[0].close() })
    expect(result.current.connected).toBe(false)

    // Advance past first backoff (2^0 * 1000 = 1000 ms)
    await act(async () => { jest.advanceTimersByTime(1000) })
    await act(async () => { jest.runAllTimers() })

    // A second WebSocket should have been created
    expect(instances).toHaveLength(2)
  })

  it("sets connected=false after disconnect", async () => {
    const { result } = renderHook(() => useLiveFeed(null))
    await act(async () => { jest.runAllTimers() })
    act(() => { instances[0].close() })
    expect(result.current.connected).toBe(false)
  })

  it("omits domain param when domain is null", async () => {
    renderHook(() => useLiveFeed(null))
    await act(async () => { jest.runAllTimers() })
    expect(instances[0].url).not.toContain("domain=")
  })

  it("ignores malformed WebSocket messages", async () => {
    const { result } = renderHook(() => useLiveFeed("infra"))
    await act(async () => { jest.runAllTimers() })

    act(() => {
      instances[0].onmessage?.({ data: "not-json{{{" })
    })

    expect(result.current.feed).toHaveLength(0)
  })

  it("closes WebSocket on unmount", async () => {
    const { unmount } = renderHook(() => useLiveFeed("infra"))
    await act(async () => { jest.runAllTimers() })
    const ws = instances[0]
    const closeSpy = jest.spyOn(ws, "close")
    unmount()
    expect(closeSpy).toHaveBeenCalled()
  })
})
