import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer
      className="bg-[#f5f7fb] mt-8 flex flex-col items-center justify-center"
      style={{ 
        paddingLeft: "2.5cm", 
        paddingRight: "2.5cm", 
        paddingTop: "1.5rem", 
        paddingBottom: "1.5rem", 
        borderTop: "1px solid #e7edf3",
        minHeight: "auto"
      }}
    >
      {/* Copyright Section */}
      <div className="text-sm text-[#4c739a]" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        © FlowDock 2026, all rights reserved
      </div>
    </footer>
  );
}
