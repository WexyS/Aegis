import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis | Local AI Mission Control",
  description: "Local-first Mission Control for runtime truth, safe planning, and governed execution.",
};

import { DevOverlay } from "@/components/DevOverlay";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased custom-scrollbar">
        {children}
        <DevOverlay />
      </body>
    </html>
  );
}
