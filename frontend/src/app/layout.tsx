import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "PulseCore — Real-time Anomaly Dashboard",
  description: "Live telemetry anomaly detection across infra, ecommerce, and IoT domains.",
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full">{children}</body>
    </html>
  )
}
