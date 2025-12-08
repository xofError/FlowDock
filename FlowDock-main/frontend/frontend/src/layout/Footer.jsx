import { Link } from "react-router-dom";

export default function Footer() {
  const handleLinkClick = (e) => {
    e.preventDefault();
    // Mock: Assume backend success
    console.log("Navigation mocked for:", e.currentTarget.pathname);
  };

  return (
    <footer
      className="bg-[#f5f7fb] mt-8 flex items-center"
      style={{ paddingLeft: "2.5cm", paddingRight: "2.5cm", paddingTop: "3.84mm", paddingBottom: "3.84mm", borderTop: "1px solid #e7edf3" }}
    >
      <div className="max-w-4xl mx-auto px-8 w-full grid grid-cols-3 items-center text-sm text-[#4c739a]">
        <div className="col-start-1">
          <Link to="/privacy" onClick={handleLinkClick} className="hover:underline">
            Privacy Policy
          </Link>
        </div>

        <div className="col-start-2 text-center">
          © FlowDock 2025, all rights reserved
        </div>

        <div className="col-start-3 flex justify-end">
          <Link to="/terms" onClick={handleLinkClick} className="hover:underline">
            Terms of Service
          </Link>
        </div>
      </div>
    </footer>
  );
}
