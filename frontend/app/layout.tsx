import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "InsureTrust AI — Fraud Detection Platform",
  description: "Real-time fraudulent insurance claim detection powered by multi-model AI ensemble, graph analytics, and IRDAI compliance engine.",
  keywords: "insurance fraud detection, AI, IRDAI, claims analysis, fraud ring detection",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gradient-mesh min-h-screen`}>
        <nav className="fixed top-0 left-0 right-0 z-50 glass-card rounded-none border-x-0 border-t-0 py-3 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/25">
              🛡️
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                InsureTrust AI
              </h1>
              <p className="text-xs text-gray-500">Fraud Detection Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <a href="/" className="text-sm text-gray-400 hover:text-blue-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5">
              Upload
            </a>
            <a href="/dashboard" className="text-sm text-gray-400 hover:text-blue-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5">
              Dashboard
            </a>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-xs text-green-400">System Active</span>
            </div>
          </div>
        </nav>
        <main className="pt-20 px-4 pb-8 max-w-[1440px] mx-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
