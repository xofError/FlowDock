import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import Button from "../../components/Button.jsx";
import { api } from "../../services/api.js";
import useAuth from "../../hooks/useAuth.js";

export default function PasscodeCheck() {
  const navigate = useNavigate();
  const location = useLocation();
  const initialEmail = location.state?.email || "";
  const nextTarget = location.state?.next || null;
  const { loadUser } = useAuth();

  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sentMessage, setSentMessage] = useState("");

  useEffect(() => {
    if (initialEmail) {
      setSentMessage(`A passcode was sent to ${initialEmail}`);
    }
  }, [initialEmail]);

  const handleChange = (index, val) => {
    if (!/^[0-9]?$/.test(val)) return;
    const newCode = [...code];
    newCode[index] = val ? val[0] : "";
    setCode(newCode);
    if (val && index < 5) {
      const next = document.getElementById(`pc-${index + 1}`);
      if (next) next.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      const prev = document.getElementById(`pc-${index - 1}`);
      if (prev) prev.focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    const joined = code.join("");
    if (joined.length !== 6) {
      setError("Please enter the complete 6-digit passcode");
      return;
    }
    try {
      setLoading(true);
      // Call backend verify-email endpoint which may return tokens when verifying sign-in passcode
      const response = await api.verifyEmail(initialEmail, joined);

      // If backend returned tokens, set them and load user
      if (response?.access_token) {
        api.setTokens(response.access_token, response.refresh_token);
        localStorage.setItem("access_token", response.access_token);
        if (response.user_id) {
          localStorage.setItem("user_id", response.user_id);
          try { await loadUser(response.user_id); } catch (_) { /* ignore */ }
        }
      }

      // Navigate to dashboard on success
      navigate("/dashboard");
    } catch (err) {
      setError(err?.message || "Verification failed");
      setCode(["", "", "", "", "", ""]);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = () => {
    setSentMessage(`We've resent a passcode to ${initialEmail || "your email"}`);
    // Optionally call an API to resend — omitted if backend doesn't expose endpoint
  };

  if (!initialEmail) {
    return (
      <MainLayout>
        <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
          <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">Missing Email</h2>
          <p className="text-center text-sm text-[#4c739a]">Please start from the sign-in with email form.</p>
          <div className="text-center mt-4">
            <Link to="/signin-email" className="text-blue-600 underline">Back to Sign In</Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">Enter Passcode</h2>

        {sentMessage && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
            <p className="text-sm">{sentMessage}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <p className="text-center text-sm text-[#4c739a] px-2">
          Enter the 6-digit passcode sent to <strong>{initialEmail}</strong>.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3 px-2">
          <div style={{ display: "flex", gap: 12, justifyContent: "center", marginTop: 12, marginBottom: 16 }}>
            {code.map((d, i) => (
              <input
                key={i}
                id={`pc-${i}`}
                type="text"
                inputMode="numeric"
                maxLength="1"
                value={d}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                disabled={loading}
                style={{ width: 50, height: 50, fontSize: 24 }}
                className="text-center rounded-lg bg-[#e7edf3] text-[#0d141b] font-bold focus:outline-none border-2 border-transparent focus:border-[#1380ec] disabled:opacity-50"
              />
            ))}
          </div>

          <Button type="submit" loading={loading} loadingText="Verifying..." disabled={loading}>
            Verify Passcode
          </Button>
        </form>

        <div className="text-center px-2" style={{ marginTop: 12 }}>
          <button onClick={handleResend} className="text-[#4c739a] underline text-sm">Resend Passcode</button>
        </div>
      </div>
    </MainLayout>
  );
}
