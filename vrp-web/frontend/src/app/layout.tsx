import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VRP Optimizer",
  description: "Vehicle Routing Problem Solver with Ontology-based Modeling",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
