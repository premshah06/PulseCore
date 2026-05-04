"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { WS_URL } from "@/lib/api"
import type { AnomalyRecord, Domain, LiveUpdate } from "@/types"

const MAX_RETRIES = 5
const MAX_FEED_SIZE = 60

export interface LiveFeedResult {
  feed: AnomalyRecord[]
  connected: boolean
}

export function useLiveFeed(domain: Domain | null): LiveFeedResult {
  const [feed, setFeed] = useState<AnomalyRecord[]>([])
  const [connected, setConnected] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // connect is recreated when domain changes; useEffect re-runs, cleaning up old WS.
  const connect = useCallback(() => {
    const url = domain ? `${WS_URL}/ws?domain=${domain}` : `${WS_URL}/ws`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retryRef.current = 0
    }

    ws.onmessage = (ev: MessageEvent<string>) => {
      try {
        const msg = JSON.parse(ev.data) as LiveUpdate
        if (msg.type === "anomaly") {
          setFeed((prev) => [msg.data, ...prev].slice(0, MAX_FEED_SIZE))
        }
      } catch {
        // malformed frame — ignore
      }
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onclose = () => {
      setConnected(false)
      if (retryRef.current < MAX_RETRIES) {
        const delay = Math.pow(2, retryRef.current) * 1000
        retryRef.current += 1
        timerRef.current = setTimeout(connect, delay)
      }
    }
  }, [domain])

  useEffect(() => {
    retryRef.current = 0
    connect()
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { feed, connected }
}
