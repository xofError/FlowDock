import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import Button from "../../components/Button.jsx";
import useAuth from "../../hooks/useAuth.js";

export default function VerifyEmail() {
  const navigate = useNavigate();
  const location = useLocation();
  const { verifyEmail } = useAuth();

  // read optional email and next target passed via navigation state
  const initialEmail = location.state?.email || "";
  const nextTarget = location.state?.next || null;

  const [step, setStep] = useState(initialEmail ? "enter-code" : "enter-email");
  const [email, setEmail] = useState(initialEmail);
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sentMessage, setSentMessage] = useState("");

  useEffect(() => {
    if (initialEmail) {
      setSentMessage(`We've sent a verification code to ${initialEmail}`);
    }
  }, [initialEmail]);

  const handleSendCode = async (e) => {
    e?.preventDefault();
    setError(null);
    if (!email) {
      setError("Please enter your email");
      return;
    }
    try {
      setIsLoading(true);
      // mock sending code
      await new Promise((r) => setTimeout(r, 700));
      setSentMessage(`We've sent a verification code to ${email}`);
      setStep("enter-code");
    } catch (err) {
      setError(err.message || "Failed to send code");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e, index) => {
    const value = e.target.value.replace(/\D/, "");
    const newOtp = [...otp];
    newOtp[index] = value ? value[0] : "";
    setOtp(newOtp);
    if (index < 5 && value) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      if (prevInput) {
        prevInput.focus();
        const newOtp = [...otp];
        newOtp[index - 1] = "";
        setOtp(newOtp);
      }
    }
  };

  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    setError(null);
    const code = otp.join("");
    if (code.length !== 6) {
      setError("Please enter the complete 6-digit code");
      return;
    }

    try {
      setIsLoading(true);
      // call API to verify email (signup verification)
      await verifyEmail(email, code);

      // If caller requested dashboard (sign-in with passcode flow), navigate there
      if (nextTarget === "dashboard") {
        navigate("/dashboard");
        return;
      }

      // Otherwise for signup verification, proceed as before
      // If signup flow needs 2FA, the SignUp component handles navigation to /2fa after calling this page
      navigate("/login");
    } catch (err) {
      setError(err?.message || "Verification failed");
      setOtp(["", "", "", "", "", ""]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = () => {
    // Optionally implement resend; keep mocked for now
    setSentMessage(`We've resent a verification code to ${email}`);
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">Verify Email</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {sentMessage && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
            <p className="text-sm">{sentMessage}</p>
          </div>
        )}

        <form onSubmit={handleVerifySubmit} className="flex flex-col gap-3 px-2">
          <div style={{ display: "flex", gap: "12px", justifyContent: "center", marginTop: "12px", marginBottom: "16px" }}>
            {otp.map((digit, i) => (
              <input
                key={i}
                id={`otp-${i}`}
                type="text"
                maxLength="1"
                value={digit}
                onChange={(e) => handleChange(e, i)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                disabled={isLoading}
                style={{ width: "50px", height: "50px", fontSize: "24px" }}
                className="text-center rounded-lg bg-[#e7edf3] text-[#0d141b] font-bold focus:outline-none border-2 border-transparent focus:border-[#1380ec] disabled:opacity-50"
              />
            ))}
          </div>

          <Button type="submit" loading={isLoading} loadingText="Verifying..." disabled={isLoading}>
            Verify
          </Button>
        </form>
      </div>
    </MainLayout>
  );
}
