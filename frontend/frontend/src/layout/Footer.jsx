import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer
      className="bg-[#f5f7fb] mt-8 flex items-center justify-center"
      style={{ 
        paddingLeft: "2.5cm", 
        paddingRight: "2.5cm", 
        paddingTop: "1.92mm", 
        paddingBottom: "1.92mm", 
        borderTop: "1px solid #e7edf3",
        minHeight: "30px",
        marginTop: "3rem"
      }}
    >
      <div className="text-sm text-[#4c739a]" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        © FlowDock 2026, all rights reserved
      </div>
    </footer>
  );
}
