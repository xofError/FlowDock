import React from "react";
import { useNavigate } from "react-router-dom";
import TopNavBar from "../../layout/TopNavBar";
import DashboardIcon from "../../resources/icons/dashboard.svg";
import MyFilesIcon from "../../resources/icons/my_files.svg";
import SharedIcon from "../../resources/icons/shared.svg";
import TrashIcon from "../../resources/icons/trash.svg";
import SettingsIcon from "../../resources/icons/settings.svg";

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

export default function Trash() {
  const routerNavigate = useNavigate();

  return (
    <TopNavBar>
      <style>{`
        .sidebar-btn {
          display: flex;
          align-items: center;
          justify-content: flex-start;
          width: 100%;
          gap: 0.3cm;
          height: 2rem;
          font-size: 0.875rem;
          padding: 0.5rem 0.8rem;
          border-radius: 0.5rem;
          outline: none;
          border: none;
          background-color: transparent;
          color: #64748b;
          font-weight: 400;
          transition: all 0.2s ease;
          cursor: pointer;
          margin-bottom: 0.6rem;
        }
        .sidebar-btn:hover {
          background-color: #f1f5f9;
        }
        .sidebar-btn.active {
          background-color: #e2e8f0;
          color: #0f172a;
          font-weight: 500;
        }
      `}</style>

      {/* Sidebar */}
      <aside 
        style={{ 
          width: "calc(100vw * 5 / 17 * 0.75 * 0.85)",
          backgroundColor: "#ffffff",
          paddingLeft: "1cm",
          paddingRight: "1.5rem",
          paddingTop: "1.5rem",
          paddingBottom: "1.5rem",
          display: "flex",
          flexDirection: "column",
          flexShrink: 0,
        }}
      >
        <nav style={{ flex: 1 }}>
          {navItems.map((item, idx) => (
            <button
              key={idx}
              className={`sidebar-btn ${idx === 3 ? "active" : ""}`}
              onClick={() => routerNavigate(item.to)}
            >
              <img 
                src={item.icon} 
                alt="" 
                style={{ width: "1.1rem", height: "1.1rem", flexShrink: 0 }} 
              />
              <span style={{ fontSize: "0.875rem" }}>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main 
        style={{ 
          flex: 1, 
          paddingLeft: "3rem", 
          paddingRight: "3rem", 
          paddingTop: "2.5rem", 
          paddingBottom: "2.5rem", 
          overflowY: "auto", 
          backgroundColor: "#ffffff" 
        }}
      >
        <h1 className="text-2xl font-bold">Trash</h1>
        <p className="text-sm text-slate-600 mt-2">Deleted files are kept here temporarily.</p>
      </main>
    </TopNavBar>
  );
}
