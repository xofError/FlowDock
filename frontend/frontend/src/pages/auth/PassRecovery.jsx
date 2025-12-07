import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";
import Button from "../../components/Button.jsx";

export default function PassRecovery() {
  const navigate = useNavigate();
  const { requestPasswordReset, loading: authLoading, error: authError } = useAuth();
  
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email) {
      setError("Please enter your email");
      return;
    }

    try {
      await requestPasswordReset(email);
      setSuccess(true);
      // Route to PassRecoveryVerify with email state
      setTimeout(() => navigate("/pass-recovery-verify", { state: { email } }), 2000);
    } catch (err) {
      setError(err.message || "Failed to send recovery email");
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        <h2 className="text-[#0D141B] text-[28px] font-bold text-center" style={{ marginTop: "1.5cm" }}>Password Recovery</h2>

        {(error || authError) && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error || authError}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">Recovery email sent! Redirecting...</p>
          </div>
        )}

        <p className="text-center text-sm text-[#4c739a] px-2">
          Enter your email and we will send you a reset code.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col px-2">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            disabled={authLoading}
            required
            style={{ height: "38px", marginTop: 12, marginBottom: "32px", borderRadius: "12px", paddingLeft: "16px" }}
            className="w-full rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none disabled:opacity-50"
          />
          <Button type="submit" loading={authLoading} loadingText="Sending..." disabled={authLoading}>
            Send Reset Code
          </Button>
        </form>

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
