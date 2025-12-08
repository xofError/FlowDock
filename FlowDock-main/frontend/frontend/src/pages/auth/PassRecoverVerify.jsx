import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";

export default function PassRecoverVerify() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email;

  useEffect(() => {
    // Mock: Auto-verify after 2 seconds and navigate to reset password
    if (email) {
      const timer = setTimeout(() => {
        navigate("/reset-password", { state: { email, token: "mock-reset-token" } });
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [email, navigate]);

  if (!email) {
    return (
      <MainLayout>
        <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
          <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">Error</h2>
          <p className="text-center text-red-600">Please request a password recovery first.</p>
          <Link to="/pass-recovery" className="text-center text-blue-600 underline">
            Back to Password Recovery
          </Link>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        <div className="text-center mb-4">
          <div className="text-5xl mb-4">✓</div>
          <h2 className="text-[#0D141B] text-[28px] font-bold" style={{ marginTop: "1.5cm" }}>Email verified!</h2>
        </div>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
          <p className="text-sm">
            Redirecting to reset password...
          </p>
        </div>

        <p className="text-center text-sm text-[#4c739a] px-2">
          You will be redirected to the password reset page shortly.
        </p>
      </div>
    </MainLayout>
  );
}
