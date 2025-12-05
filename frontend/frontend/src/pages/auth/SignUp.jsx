import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";

export default function SignUp() {
  const navigate = useNavigate();
  const { register, verifyEmail, setupTOTP, verifyTOTP, loading: authLoading, error: authError } = useAuth();

  const [step, setStep] = useState("form"); // form, verify, complete, or setup2fa
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [enable2FA, setEnable2FA] = useState(false);
  const [verificationCode, setVerificationCode] = useState(["", "", "", "", "", ""]);
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);
  const [qrUri, setQrUri] = useState("");
  const [totp, setTotp] = useState(Array(6).fill(""));
  
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
      
      // Check if user enabled 2FA
      if (enable2FA) {
        // Setup 2FA QR code
        const response = await setupTOTP(email);
        setQrUri(response.totp_uri);
        setStep("setup2fa");
      } else {
        setStep("complete");
        setTimeout(() => navigate("/login"), 2000);
      }
    } catch (err) {
      setError(err.message || "Verification failed");
    }
  };

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

  const handle2FAVerify = async (e) => {
    e.preventDefault();
    setError(null);

    if (totp.some(d => d === "")) {
      setError("Please enter the complete 6-digit code");
      return;
    }

    try {
      await verifyTOTP(email, totp.join(""));
      setStep("complete");
      setTimeout(() => navigate("/login"), 2000);
    } catch (error) {
      setError(error.message || "Verification failed");
    }
  };



  return (
    <MainLayout>
      <div className="flex flex-col gap-8 pb-10 w-full max-w-sm mx-auto">

        {step === "form" && (
          <>
            <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
              Create your account
            </h2>

            {(error || authError) && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
                <p className="text-sm">{error || authError}</p>
              </div>
            )}

            <form className="flex flex-col px-2" onSubmit={handleSubmit}>
              <input
                name="name"
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={handleChange}
                disabled={authLoading}
                required
                style={{ height: "38px", marginBottom: "16px" }}
                className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
              />
              <input
                name="email"
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={handleChange}
                disabled={authLoading}
                required
                style={{ height: "38px", marginBottom: "16px" }}
                className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
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
                style={{ height: "38px", marginBottom: "16px" }}
                className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
              />

              <label className="flex items-center gap-2 mb-8 text-sm">
                <input
                  type="checkbox"
                  checked={enable2FA}
                  onChange={(e) => setEnable2FA(e.target.checked)}
                  disabled={authLoading}
                  className="w-4 h-4"
                />
                <span className="text-[#0d141b]">Enable two-factor authentication (optional)</span>
              </label>

              <div className="flex flex-col gap-2">
                <button
                  type="submit"
                  disabled={authLoading}
                  style={{ height: "38px", marginBottom: "16px", opacity: authLoading ? 0.7 : 1 }}
                  className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
                >
                  {authLoading ? "Creating Account..." : "Sign Up"}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    window.location.href = `${import.meta.env.VITE_AUTH_API_URL}/auth/oauth/google/login`;
                  }}
                  disabled={authLoading}
                  style={{ height: "38px" }}
                  className="w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold flex items-center justify-center transition-all"
                >
                  Sign up with Google
                </button>
              </div>
            </form>

            <p className="text-center mt-4 text-sm">
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

            <form className="flex flex-col px-2" onSubmit={handleVerifyEmail}>
              <div className="flex gap-2 justify-center mb-8">
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
                {authLoading ? "Verifying..." : "Verify Email"}
              </button>
            </form>
          </>
        )}

        {step === "setup2fa" && (
          <>
            <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
              Scan QR Code
            </h2>

            <p className="text-center text-sm text-[#4c739a] px-2">
              Use your authenticator app to scan this QR code.
            </p>

            <div className="flex justify-center py-4">
              <div className="border-2 border-[#e7edf3] rounded-lg p-2 bg-white">
                <QRCodeSVG 
                  value={qrUri} 
                  size={250}
                  level="H"
                  includeMargin={true}
                />
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 mx-2">
              <p className="text-xs text-yellow-800">
                <strong>Can't scan?</strong> Enter this key manually in your authenticator app:
              </p>
              <p className="text-xs text-yellow-900 font-mono mt-2 break-all">
                {qrUri.match(/secret=([^&]*)/)?.[1] || ""}
              </p>
            </div>

            <form onSubmit={handle2FAVerify} className="flex flex-col px-2">
              {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4" role="alert">
                  <p className="text-sm">{error}</p>
                </div>
              )}

              <p className="text-center text-sm text-[#4c739a] mb-4">
                Enter the 6-digit code from your authenticator app:
              </p>

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
                {authLoading ? "Verifying..." : "Verify & Complete"}
              </button>
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

