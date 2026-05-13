import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Aegis | Autonomous AI Mission Control",
  description: "Enterprise-grade autonomous execution runtime interface.",
};

import { DevOverlay } from "@/components/DevOverlay";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} antialiased custom-scrollbar`}>
        {children}
        <DevOverlay />
      </body>
    </html>
  );
}
