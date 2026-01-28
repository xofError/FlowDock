import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";
import Button from "../../components/Button.jsx";

export default function VerifyTOTP() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, loading: authLoading, error: authError } = useAuth();
  const navigationInitiated = useRef(false);
  
  const [totp, setTotp] = useState(Array(6).fill(""));
  const [error, setError] = useState(null);

  // Get email and password from navigation state
  const { email, password } = location.state || {};

  // Watch for authentication success and navigate
  useEffect(() => {
    if (isAuthenticated && navigationInitiated.current) {
      console.log("[VerifyTOTP] isAuthenticated is now true, navigating to dashboard");
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Redirect to login if no credentials passed
  if (!email || !password) {
    return (
      <MainLayout>
        <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
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
      console.log(`[VerifyTOTP] Submitting TOTP code for ${email}`);
      const response = await login(email, password, totp.join(""));
      
      console.log(`[VerifyTOTP] Login response:`, response);
      console.log(`[VerifyTOTP] access_token present: ${!!response?.access_token}`);
      console.log(`[VerifyTOTP] totp_required: ${response?.totp_required}`);
      
      // Check if login was successful (should have access_token and not totp_required)
      if (!response || response.totp_required || !response.access_token) {
        console.error(`[VerifyTOTP] Login failed - missing access_token or totp_required is true`);
        setError("Invalid TOTP code. Please try again.");
        setTotp(Array(6).fill("")); // Clear input on error
        return;
      }
      
      // Login successful - set flag and wait for useEffect to trigger navigation when isAuthenticated updates
      console.log(`[VerifyTOTP] Login successful, waiting for state update`);
      navigationInitiated.current = true;
    } catch (err) {
      console.error(`[VerifyTOTP] Error during login:`, err);
      setError(err.message || "Invalid TOTP code. Please try again.");
      setTotp(Array(6).fill("")); // Clear input on error
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center" style={{ marginTop: "1.5cm" }}>
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
          <div className="flex gap-2 justify-center" style={{ gap: "3mm", marginTop: "24px", marginBottom: "24px" }}>
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
                style={{ height: "48px", width: "48px", borderRadius: "12px", paddingLeft: "4px" }}
                className="rounded-lg bg-[#e7edf3] text-[#0d141b] text-center text-xl font-bold focus:outline-none border border-[#d0dce8] disabled:opacity-50"
              />
            ))}
          </div>

          <Button type="submit" loading={authLoading} loadingText="Verifying..." disabled={authLoading}>
            Verify
          </Button>
        </form>
      </div>
    </MainLayout>
  );
}
