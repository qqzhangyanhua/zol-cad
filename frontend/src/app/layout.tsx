import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Noto_Sans_SC } from "next/font/google";

import "./globals.css";

const notoSansSc = Noto_Sans_SC({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-noto-sans-sc",
});

export const metadata: Metadata = {
  title: "机加工报价辅助",
  description: "报价员上传并查看本厂零件图",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="zh-CN" className={`${notoSansSc.variable} h-full`}>
      <body className="min-h-full glass-shell font-sans text-slate-800 antialiased selection:bg-blue-100 selection:text-blue-900">
        {children}
      </body>
    </html>
  );
}
