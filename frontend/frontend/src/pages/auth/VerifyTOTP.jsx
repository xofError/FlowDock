import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";

export default function VerifyTOTP() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loading: authLoading, error: authError } = useAuth();
  
  const [totp, setTotp] = useState(Array(6).fill(""));
  const [error, setError] = useState(null);

  // Get email and password from navigation state
  const { email, password } = location.state || {};

  // Redirect to login if no credentials passed
  if (!email || !password) {
    return (
      <MainLayout>
        <div className="flex flex-col gap-6 pb-10 w-full max-w-sm mx-auto">
          <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">
            Session Expired
          </h2>
          <p className="text-center text-sm text-[#4c739a]">
            Please log in again.
          </p>
          <button
            onClick={() => navigate("/login")}
            style={{ height: "38px" }}
            className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
          >
            Back to Login
          </button>
        </div>
      </MainLayout>
    );
  }

  const handleTotpChange = (index, value) => {
    if (!/^[0-9]?$/.test(value)) return;
    
    const newTotp = [...totp];
    newTotp[index] = value;
    setTotp(newTotp);

    if (index < 5 && value) {
      const nextInput = document.getElementById(`totp-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleTotpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !totp[index] && index > 0) {
      const prevInput = document.getElementById(`totp-${index - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (totp.some(d => d === "")) {
      setError("Please enter the complete 6-digit code");
      return;
    }

    try {
      // Login with email, password, and TOTP code
      await login(email, password, totp.join(""));
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid TOTP code. Please try again.");
      setTotp(Array(6).fill("")); // Clear input on error
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 w-full max-w-sm mx-auto">
        
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
          Enter Authentication Code
        </h2>

        {(error || authError) && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error || authError}</p>
          </div>
        )}

        <p className="text-center text-sm text-[#4c739a] px-2">
          Enter the 6-digit code from your authenticator app.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col px-2">
          <div className="flex gap-2 justify-center mb-8">
            {totp.map((digit, index) => (
              <input
                key={index}
                id={`totp-${index}`}
                type="text"
                value={digit}
                onChange={(e) => handleTotpChange(index, e.target.value)}
                onKeyDown={(e) => handleTotpKeyDown(index, e)}
                disabled={authLoading}
                maxLength="1"
                style={{ height: "48px", width: "48px" }}
                className="rounded-lg bg-[#e7edf3] text-[#0d141b] text-center text-xl font-bold focus:outline-none border-none disabled:opacity-50"
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={authLoading}
            style={{ height: "38px", opacity: authLoading ? 0.7 : 1 }}
            className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
          >
            {authLoading ? "Verifying..." : "Verify"}
          </button>
        </form>

        <button
          onClick={() => navigate("/login")}
          className="text-center text-blue-600 underline text-sm mt-4"
        >
          Back to Login
        </button>
      </div>
    </MainLayout>
  );
}
