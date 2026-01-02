import { Link, useNavigate } from "react-router-dom";
import { Anchor } from "lucide-react";
import { useState } from "react";

export default function Header() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

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
      <div className="max-w-4xl mx-auto px-4 w-full grid grid-cols-3 items-center">
        {/* Left: logo + name */}
        <div className="flex items-center gap-3 col-start-1">
          <Anchor className="h-12 w-12 text-slate-900" />
          <span className="text-[#0d141b] font-black" style={{ fontSize: "28px", fontWeight: 900, lineHeight: "1" }}>FlowDock</span>
        </div>

        {/* Center: reserved slot (will stay centered if content added) */}
        <div className="col-start-2 text-center">
          {/* ...existing code... */}
        </div>

        {/* Right: Sign In - aligned to the right column */}
        <div className="col-start-3 flex justify-end">
          <button
            onClick={handleSignIn}
            disabled={loading}
            style={{ opacity: loading ? 0.7 : 1, padding: "10px 24px", fontSize: "15px", borderRadius: "12px" }}
            className="bg-[#E7EDF3] text-[#0D141B] font-bold hover:bg-[#dce4ed] transition-all border border-[#d0d7e0]"
          >
            Sign In
          </button>
        </div>
      </div>
    </header>
  );
}