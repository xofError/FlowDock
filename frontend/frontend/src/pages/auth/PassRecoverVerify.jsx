import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";

export default function PassRecoverVerify() {
  const navigate = useNavigate();
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
          <div className="text-5xl mb-4">✓</div>
          <h2 className="text-[#0D141B] text-[28px] font-bold">Check your email</h2>
        </div>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
          <p className="text-sm">
            We've sent a password reset link to <strong>{email}</strong>
          </p>
        </div>

        <p className="text-center text-sm text-[#4c739a] px-2">
          Click the link in your email to reset your password. The link will expire in 15 minutes.
        </p>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
          <p className="text-xs text-gray-600 mb-2"><strong>Didn't receive the email?</strong></p>
          <ul className="text-xs text-gray-600 space-y-1">
            <li>• Check your spam or junk folder</li>
            <li>• Make sure you entered the correct email address</li>
            <li>• Try requesting another link below</li>
          </ul>
        </div>

        <Link 
          to="/pass-recovery" 
          className="text-center bg-[#1380EC] text-white rounded-lg font-bold py-2 px-4 transition-all hover:bg-blue-600"
        >
          Request another link
        </Link>

        <p className="text-center mt-4 text-sm">
          Remember your password?{" "}
          <Link to="/login" className="text-blue-600 underline">
            Sign In
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
