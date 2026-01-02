import { Link, useNavigate, useLocation } from "react-router-dom";
import { Anchor } from "lucide-react";
import { useState } from "react";
import ReorderIcon from "../resources/icons/reorder.svg";

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();            // <- added
  const [loading, setLoading] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isHome = location.pathname === "/";  // true on home route

  const handleLogoClick = (e) => {
    e.preventDefault();
    navigate("/");
  };

  const handleSignIn = () => {
    setLoading(true);
    setTimeout(() => navigate("/login"), 250);
  };

  return (
    <header
      className="bg-white flex items-center"
      style={{ 
        paddingLeft: "1.2cm", 
        paddingRight: "2.5cm", 
        paddingTop: "3.84mm", 
        paddingBottom: "3.84mm", 
        borderBottom: "1px solid #d0d7e0",
        backgroundColor: "#ffffff"
      }}
    >
      <div className="max-w-4xl mx-auto px-4 w-full grid grid-cols-3 items-center container">
        {/* Left: logo + name */}
        <a
          href="/"
          onClick={handleLogoClick}
          className="flex items-center gap-3 col-start-1 hover:opacity-80"
          style={{ textDecoration: "none", cursor: "pointer" }}
        >
          <Anchor className="h-12 w-12" style={{ color: "#000000" }} />
          <span className="text-[#0d141b] font-black" style={{ fontSize: "28px", fontWeight: 900, lineHeight: "1" }}>FlowDock</span>
        </a>

        {/* Center: reserved slot (will stay centered if content added) */}
        <div className="col-start-2 text-center">
          {/* ...existing code... */}
        </div>

        {/* Right: Sign In (and mobile toggle placed to the right of it on small screens) */}
        <div className="col-start-3 flex justify-end items-center">
          <button
            onClick={handleSignIn}
            disabled={loading}
            style={{ opacity: loading ? 0.7 : 1, padding: "10px 24px", fontSize: "15px", borderRadius: "12px" }}
            className="bg-[#E7EDF3] text-[#0D141B] font-bold hover:bg-[#dce4ed] transition-all border border-[#d0d7e0]"
          >
            Sign In
          </button>

          {/* place the reorder (sidebar toggle) to the right of Sign In on mobile only */}
          {!isHome && (
            <button
              onClick={() => {
                setMobileOpen(true);
                try { window.dispatchEvent(new CustomEvent('toggleMobileSidebar')); } catch (e) { /* no-op */ }
              }}
              title="Toggle menu"
              aria-label="Toggle menu"
              className="sidebar-toggle-button"
              style={{ background: "none", border: "none", cursor: "pointer", padding: 0, marginLeft: "0.4rem" }}
            >
              <img src={ReorderIcon} alt="Menu" style={{ width: "1.6rem", height: "1.6rem" }} />
            </button>
          )}
        </div>
      </div>

      {/* Mobile menu overlay */}
      {mobileOpen && (
        <div className="mobile-menu" onClick={() => setMobileOpen(false)}>
          <div className="panel" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Anchor className="h-8 w-8" />
                <strong>FlowDock</strong>
              </div>
              <button onClick={() => setMobileOpen(false)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.2rem" }}>✕</button>
            </div>

            <nav style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <a href="/" onClick={(e) => { e.preventDefault(); setMobileOpen(false); navigate("/"); }} style={{ textDecoration: "none", color: "#0f172a" }}>Home</a>
              <a href="/features" onClick={(e) => { e.preventDefault(); setMobileOpen(false); navigate("/"); }} style={{ textDecoration: "none", color: "#0f172a" }}>Features</a>
              <a href="/help" onClick={(e) => { e.preventDefault(); setMobileOpen(false); navigate("/help"); }} style={{ textDecoration: "none", color: "#0f172a" }}>Help</a>

              <div style={{ marginTop: "1rem" }}>
                <button onClick={() => { setMobileOpen(false); navigate("/login"); }} style={{ width: "100%", padding: "0.6rem 1rem", borderRadius: 8, border: "1px solid #e5e7eb", background: "#fff" }}>Sign In</button>
              </div>
            </nav>
          </div>
        </div>
      )}
    </header>
  );
}