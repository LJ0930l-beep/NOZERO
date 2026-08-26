import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NO ZERO — 安静而可靠的训练",
  description: "本地优先、安全优先的室内训练系统。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
