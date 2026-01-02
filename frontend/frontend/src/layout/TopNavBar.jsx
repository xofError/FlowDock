import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Anchor } from "lucide-react";
import PersonIcon from "../resources/icons/person.svg";
import QuestionMarkIcon from "../resources/icons/question_mark.svg";
import { useAuthContext } from "../context/AuthContext";

export default function TopNavBar({ children }) {
  const { isAuthenticated, user, logout } = useAuthContext();
  // load persisted user as fallback so UI still shows after refresh
  const storedUserJson = typeof window !== "undefined" ? localStorage.getItem("user") : null;
  const storedUser = storedUserJson ? JSON.parse(storedUserJson) : null;
  const profileUser = user || storedUser;
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);

  useEffect(() => {
    function onDocClick(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) setProfileOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const handleLogoClick = (e) => {
    e.preventDefault();
    if (isAuthenticated) navigate("/dashboard");
    else navigate("/");
  };

  const handleHelp = (e) => {
    e.preventDefault();
    navigate("/help");
  };

  const handleProfileClick = (e) => {
    e.preventDefault();
    navigate("/profile");
  };

  const handleLogout = async () => {
    try { if (logout) await logout(); } catch (e) { /* ignore */ }
    // clear persisted user
    try { if (typeof window !== "undefined") localStorage.removeItem("user"); } catch (e) {}
    setProfileOpen(false);
    navigate("/login");
  };

  return (
    <div className="flex flex-col min-h-screen" style={{ overflowX: "hidden" }}>
      {/* Top Nav Bar */}
      <nav
        className="w-full bg-white flex items-center"
        style={{
          paddingLeft: "1.2cm",
          paddingRight: "2.5cm",
          paddingTop: "1.5mm",
          paddingBottom: "1.5mm",
          backgroundColor: "#ffffff",
          height: "calc(100vh / 13 * 0.55)",
          marginTop: "4mm", // added slight vertical gap from top of monitor
        }}
      >
        <div className="w-full flex items-center justify-between">
          {/* Left: logo + name */}
          <a
            href="/"
            onClick={handleLogoClick}
            className="flex items-center gap-3 hover:opacity-80"
            style={{ textDecoration: "none" }}
          >
            <Anchor className="h-7 w-7" style={{ color: "#000000" }} />
            <span
              className="text-[#0d141b] font-black"
              style={{
                fontSize: "24px",
                fontWeight: 900,
                lineHeight: "1",
              }}
            >
              FlowDock
            </span>
          </a>

          {/* Right: Two icon buttons + profile dropdown */}
          <div ref={profileRef} className="flex items-center" style={{ gap: "0.35cm", marginLeft: "auto", marginRight: "3.8cm", position: "relative" }}>
            <button
              onClick={handleHelp}
              title="Help"
              className="hover:opacity-70 transition"
              style={{ background: "none", border: "none", cursor: "pointer", padding: "0", display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              <img src={QuestionMarkIcon} alt="Help" style={{ width: "1.95rem", height: "1.95rem" }} />
            </button>

            <button
              onClick={() => setProfileOpen((s) => !s)}
              title="Profile"
              className="hover:opacity-70 transition"
              style={{ background: "none", border: "none", cursor: "pointer", padding: "0", display: "flex", alignItems: "center", justifyContent: "center" }}
            >
              <img src={PersonIcon} alt="Profile" style={{ width: "1.95rem", height: "1.95rem" }} />
            </button>

            {profileOpen && (
              <div style={{
                position: "absolute",
                right: 0,
                top: "calc(100% + 6px)",
                background: "#ffffff",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
                boxShadow: "0 8px 24px rgba(15,23,42,0.12)",
                padding: "0.5rem",
                minWidth: 220,
                zIndex: 50
              }}>
                <div style={{ padding: "0.5rem 0.75rem", borderBottom: "1px solid #eef2f6" }}>
                  <div style={{ fontWeight: 600 }}>{profileUser?.name || profileUser?.email?.split('@')?.[0] || "User"}</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>{profileUser?.email || ""}</div>
                </div>
                <div style={{ padding: "0.5rem 0.75rem", textAlign: "right" }}>
                  <button onClick={handleLogout} style={{ background: "#fff", border: "1px solid #e5e7eb", padding: "0.4rem 0.75rem", borderRadius: 6, cursor: "pointer" }}>
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Content below nav */}
      <div className="flex flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
