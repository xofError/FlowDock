import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Folder,
  Users,
  Trash2,
  Settings,
  Anchor,
} from "lucide-react";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/my-files", label: "My Files", icon: Folder },
  { to: "/shared", label: "Shared", icon: Users },
  { to: "/trash", label: "Trash", icon: Trash2 },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function LeftNavBar({ children }) {
  return (
    <div className="flex w-full bg-white font-sans text-slate-800">
      <aside
        className="flex flex-col bg-white flex-shrink-0"
        style={{
          width: "calc(100vw * 5 / 17 * 0.75)",
          backgroundColor: "#ffffff",
          paddingLeft: "1.5rem",
          paddingRight: "1.5rem",
          paddingTop: "1.5rem",
          paddingBottom: "1.5rem",
        }}
      >
        <div className="flex items-center gap-2 mb-10 px-2">
          <Anchor className="w-6 h-6 text-slate-900" />
          <span className="text-xl font-bold tracking-tight">FlowDock</span>
        </div>

        <nav className="flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  isActive ? "nav-link-active" : "nav-link"
                }
                style={({ isActive }) => ({
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "flex-start",
                  width: "100%",
                  gap: "0.2cm",
                  height: "1.5rem",
                  fontSize: "0.39rem",
                  padding: "0.3rem 1rem",
                  borderRadius: "0.5rem",
                  outline: "none",
                  border: "none",
                  backgroundColor: isActive ? "#e2e8f0" : "transparent",
                  color: isActive ? "#0f172a" : "#64748b",
                  fontWeight: isActive ? "500" : "400",
                  transition: "all 0.2s ease",
                  cursor: "pointer",
                  textDecoration: "none",
                })}
              >
                <Icon
                  style={{
                    width: "0.75rem",
                    height: "0.75rem",
                    flexShrink: 0,
                    marginRight: "0.1cm",
                  }}
                />
                <span style={{ fontSize: "0.6rem" }}>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <main
        className="flex-1 p-6 overflow-y-auto"
        style={{ width: "calc(100vw * 12 / 17)" }}
      >
        {children}
      </main>
    </div>
  );
}
