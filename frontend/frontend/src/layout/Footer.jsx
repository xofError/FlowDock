import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer
      className="bg-[#f5f7fb] mt-8 flex items-center"
      style={{ paddingLeft: "2.5cm", paddingRight: "2.5cm", paddingTop: "0.9cm", paddingBottom: "0.9cm", borderTop: "1px solid #e7edf3" }}
    >
      <div className="max-w-4xl mx-auto px-8 w-full grid grid-cols-3 items-center text-sm text-[#4c739a]">
        <div className="col-start-1">
          <Link to="/privacy" className="hover:underline">
            Privacy Policy
          </Link>
        </div>

        <div className="col-start-2 text-center">
          © FlowDock 2025, all rights reserved
        </div>

        <div className="col-start-3 flex justify-end">
          <Link to="/terms" className="hover:underline">
            Terms of Service
          </Link>
        </div>
      </div>
    </footer>
  );
}
