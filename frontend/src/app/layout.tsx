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
  description: "报价员登录后查看本厂零件图",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="zh-CN" className={`${notoSansSc.variable} h-full`}>
      <body className="min-h-full bg-stone-100 font-sans text-stone-900 antialiased">
        {children}
      </body>
    </html>
  );
}
