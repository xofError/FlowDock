import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";

export default function SignUp() {
  const navigate = useNavigate();
  const { register, verifyEmail, loading: authLoading, error: authError } = useAuth();

  const [step, setStep] = useState("form"); // form, verify, or complete
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
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
      setStep("complete");
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setError(err.message || "Verification failed");
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
                style={{ height: "38px", marginBottom: "32px" }}
                className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
              />

              <div className="flex flex-col gap-2">
                <button
                  type="submit"
                  disabled={authLoading}
                  style={{ height: "38px", marginBottom: "16px", opacity: authLoading ? 0.7 : 1 }}
                  className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
                >
                  {authLoading ? "Creating Account..." : "Sign Up"}
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
  //             style={{ height: "38px", opacity: isGoogleLoading ? 0.7 : 1 }}
  //             className="w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold flex items-center justify-center transition-all"
  //           >
  //             {isGoogleLoading ? "Signing Up..." : "Sign up with Google"}
  //           </button>
  //         </div>
  //       </form>

  //       <p className="text-center mt-4 text-sm">
  //         Already have an account?{" "}
  //         <Link to="/login" className="text-blue-600 underline">
  //           Sign In
  //         </Link>
  //       </p>
  //     </div>
  //   </MainLayout>
  // );
}
