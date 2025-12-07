// Run dev server (PowerShell):
// cd D:\tch4x\4xC\FlowDock-main\FlowDock-main\frontend\frontend
// npm install autoprefixer postcss tailwindcss
// npm install
// npm run dev
// If you still see postcss/autoprefixer errors, create/move postcss.config.cjs to this frontend directory with:
// module.exports = { plugins: { tailwindcss: {}, autoprefixer: {}, } }

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";
import Button from "../../components/Button.jsx";
import GoogleIcon from "../../resources/icons/social-google-plus-svgrepo-com.svg";
import { AUTH_API_URL } from "../../services/api.js";

export default function SignUp() {
  const navigate = useNavigate();
  const { register, verifyEmail, loading: authLoading, error: authError } = useAuth();

  const [step, setStep] = useState("form"); // form, verify, complete
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [enable2FA, setEnable2FA] = useState(false);
  const [verificationCode, setVerificationCode] = useState(["", "", "", "", "", ""]);
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.name || !formData.email || !formData.password) {
      setError("Please fill all fields");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    try {
      await register(formData.email, formData.name, formData.password);
      setEmail(formData.email);
      setStep("verify"); // Go to email verification
    } catch (err) {
      setError(err.message || "Registration failed");
    }
  };

  const handleOtpChange = (index, value) => {
    if (value.length > 1) return;
    if (!/^[0-9]?$/.test(value)) return;
    
    const newCode = [...verificationCode];
    newCode[index] = value;
    setVerificationCode(newCode);
    
    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !verificationCode[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleVerifyEmail = async (e) => {
    e.preventDefault();
    setError(null);

    const code = verificationCode.join("");
    if (code.length !== 6) {
      setError("Please enter the complete 6-digit code");
      return;
    }

    try {
      await verifyEmail(email, code);
      
      // Check if user enabled 2FA during signup
      if (enable2FA) {
        // Navigate to 2FA setup page with email (TwoFactorAuth.jsx will handle the rest)
        navigate("/setup-2fa", { state: { email } });
      } else {
        // No 2FA: show complete and redirect to login
        setStep("complete");
        setTimeout(() => navigate("/login"), 2000);
      }
    } catch (err) {
      setError(err.message || "Verification failed");
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-8 pb-10 justify-center" style={{ width: "360px", margin: "0 auto" }}>
        {step === "form" && (
          <>
            <div>
              <h2
                className="text-[#0d141b] text-[28px] font-bold leading-tight text-center"
                style={{ marginTop: "1.5cm" }}
              >
                Create your account
              </h2>
            </div>

            {(error || authError) && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
                <p className="text-sm">{error || authError}</p>
              </div>
            )}

            <form className="flex flex-col gap-3 px-2" onSubmit={handleSubmit}>
              <input
                name="name"
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={handleChange}
                disabled={authLoading}
                required
                style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
                className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
              />
              <input
                name="email"
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleChange}
                disabled={authLoading}
                required
                style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
                className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
              />
              <input
                name="password"
                type="password"
                placeholder="Password (min 6 characters)"
                value={formData.password}
                onChange={handleChange}
                disabled={authLoading}
                required
                minLength={6}
                style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
                className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
              />

              <label className="flex items-center gap-2 text-sm pt-2 whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={enable2FA}
                  onChange={(e) => setEnable2FA(e.target.checked)}
                  disabled={authLoading}
                  className="w-4 h-4"
                />
                <span className="text-[#0d141b] whitespace-nowrap">Enable two-factor authentication (optional)</span>
              </label>

              <div className="flex flex-col gap-3" style={{ marginTop: 24 }}>
                <Button type="submit" loading={authLoading} loadingText="Creating Account..." disabled={authLoading}>
                  Sign Up
                </Button>

                <div style={{ marginTop: "12px" }}>
                  <Button 
                    type="button"
                    variant="secondary"
                    loading={authLoading}
                    loadingText="Redirecting..."
                    onClick={() => {
                      window.location.href = `${AUTH_API_URL}/auth/oauth/google/login;
                    }}
                    disabled={authLoading}
                    className="flex items-center justify-center"
                  >
                    <span>Sign up with</span>
                    <span style={{ marginLeft: "4px", marginRight: "4px" }}> </span>
                    <img src={GoogleIcon} alt="Google" style={{ height: "18px", width: "18px" }} />
                  </Button>
                </div>
              </div>
            </form>

            <p className="text-center text-sm">
              Already have an account?{" "}
              <Link to="/login" className="text-blue-600 underline">
                Sign In
              </Link>
            </p>
          </>
        )}

        {step === "verify" && (
          <>
            <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
              Verify your email
            </h2>

            {(error || authError) && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
                <p className="text-sm">{error || authError}</p>
              </div>
            )}

            <p className="text-center text-gray-600 px-4">
              We sent a verification code to <strong>{email}</strong>
            </p>

            <form className="flex flex-col gap-3 px-2" onSubmit={handleVerifyEmail}>
              <div className="flex gap-2 justify-center mb-4">
                {verificationCode.map((digit, index) => (
                  <input
                    key={index}
                    id={`otp-${index}`}
                    type="text"
                    value={digit}
                    onChange={(e) => handleOtpChange(index, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(index, e)}
                    disabled={authLoading}
                    maxLength="1"
                    style={{ height: "48px", width: "48px", borderRadius: "12px", paddingLeft: "4px" }}
                    className="rounded-lg bg-[#e7edf3] text-[#0d141b] text-center text-xl font-bold focus:outline-none border border-[#d0dce8] disabled:opacity-50"
                  />
                ))}
              </div>

              <Button type="submit" loading={authLoading} loadingText="Verifying..." disabled={authLoading}>
                Verify Email
              </Button>
            </form>
          </>
        )}

        {step === "complete" && (
          <div className="text-center py-8">
            <div className="mb-4 text-4xl">✓</div>
            <h2 className="text-[#0d141b] text-[28px] font-bold mb-4">Account created!</h2>
            <p className="text-gray-600 mb-4">Your account has been verified. Redirecting to login...</p>
          </div>
        )}
      </div>
    </MainLayout>
  );
}

