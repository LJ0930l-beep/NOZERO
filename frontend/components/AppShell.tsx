import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="side-rail">
        <Link href="/" className="brand-mark" aria-label="NO ZERO 首页">
          <span className="brand-dot" />
          <span>NO<br />ZERO</span>
        </Link>
        <nav className="primary-nav" aria-label="主导航">
          <Link href="/" className="nav-link"><span>01</span>今日</Link>
          <Link href="/workout" className="nav-link"><span>02</span>训练</Link>
          <Link href="/analytics" className="nav-link"><span>03</span>数据</Link>
        </nav>
        <div className="rail-footer"><span className="status-pip" />本地优先</div>
      </aside>
      <main className="main-stage">{children}</main>
    </div>
  );
}
