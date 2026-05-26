import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Confidence Map — AI Architecture & Delivery Intelligence",
  description:
    "A multi-agent platform that analyzes specifications, validates architecture, detects risks, and makes engineering reasoning visible.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="fixed top-2 left-2 z-50 px-4 py-2 bg-accent text-white rounded-md text-sm font-medium -translate-y-16 focus:translate-y-0 transition-transform"
          aria-label="Skip to main content"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
