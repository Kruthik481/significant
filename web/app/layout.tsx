import type { Metadata } from "next";
import { Caveat, JetBrains_Mono, Source_Serif_4 } from "next/font/google";
import "./globals.css";

const serif = Source_Serif_4({ variable: "--font-source-serif", subsets: ["latin"], weight: ["400", "600", "700"] });
const mono = JetBrains_Mono({ variable: "--font-mono-data", subsets: ["latin"], weight: ["400", "600"] });
const pen = Caveat({ variable: "--font-pen", subsets: ["latin"], weight: ["600"] });

export const metadata: Metadata = {
  title: "Significant — A/B test analyzer",
  description: "Upload an experiment and get a readout you can defend: significance, CUPED, sample-ratio checks and always-valid sequential testing.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${serif.variable} ${mono.variable} ${pen.variable} h-full antialiased`}>
      <body className="min-h-full">{children}</body>
    </html>
  );
}
