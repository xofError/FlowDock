import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";

export default function PassRecoverVerify() {
  const location = useLocation();
  const email = location.state?.email;

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
          <div className="text-5xl mb-4">📧</div>
          <h2 className="text-[#0D141B] text-[28px] font-bold" style={{ marginTop: "1.5cm" }}>Check your email</h2>
        </div>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
          <p className="text-sm font-semibold mb-2">Password reset link sent!</p>
          <p className="text-sm">
            We've sent a password reset link to <strong>{email}</strong>. 
            Click the link in the email to proceed with resetting your password.
          </p>
        </div>

        <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg">
          <p className="text-xs">
            💡 <strong>Tip:</strong> Check your spam folder if you don't see the email within a few minutes.
          </p>
        </div>

        <p className="text-center text-sm text-[#4c739a] px-2">
          <Link to="/pass-recovery" className="text-blue-600 underline hover:text-blue-800">
            Back to Password Recovery
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
