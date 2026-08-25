import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NOZEERO — training, without the noise",
  description: "A local-first, safety-first indoor training system.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
