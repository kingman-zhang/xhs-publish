import { NavLink, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand-panel">
            <div className="brand-badge">红</div>
            <div>
              <div className="brand-title">小红书文案管理</div>
              <div className="brand-subtitle">Content Publishing Desk</div>
            </div>
          </div>
          <nav className="nav-stack">
            <NavLink end to="/" className="nav-link">
              文案列表
            </NavLink>
            <NavLink to="/notes/new" className="nav-link">
              新建文案
            </NavLink>
          </nav>
        </div>
        <div className="sidebar-note">
          手机扫码后会进入移动预览页，再手动点“发布到小红书”。
        </div>
      </aside>
      <main className="page-main">
        <Outlet />
      </main>
    </div>
  );
}
