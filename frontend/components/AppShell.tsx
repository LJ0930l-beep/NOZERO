import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="side-rail">
        <Link href="/" className="brand-mark" aria-label="NOZEERO home">
          <span className="brand-dot" />
          <span>NO<br />ZERO</span>
        </Link>
        <nav className="primary-nav" aria-label="Primary navigation">
          <Link href="/" className="nav-link"><span>01</span>Today</Link>
          <Link href="/workout" className="nav-link"><span>02</span>Train</Link>
          <Link href="/analytics" className="nav-link"><span>03</span>Data</Link>
        </nav>
        <div className="rail-footer"><span className="status-pip" />Local first</div>
      </aside>
      <main className="main-stage">{children}</main>
    </div>
  );
}
