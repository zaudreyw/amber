import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GEOS Agent Dashboard",
  description: "Inspect transcripts and monitor running GEOS agent simulations."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
