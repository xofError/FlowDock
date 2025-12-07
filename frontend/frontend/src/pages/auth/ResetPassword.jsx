import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";
import Button from "../../components/Button.jsx";

export default function ResetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetPassword, loading: authLoading, error: authError } = useAuth();
  
  // Get token and email from state (multi-step flow) or URL query params (direct link from email)
  const stateToken = location.state?.token;
  const stateEmail = location.state?.email;
  
  const queryParams = new URLSearchParams(location.search);
  const queryToken = queryParams.get("token");
  const queryEmail = queryParams.get("email");
  
  const token = stateToken || queryToken;
  const email = stateEmail || queryEmail;

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!password || !confirmPassword) {
      setError("Please fill both fields");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      await resetPassword(email, token, password);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      setError(err.message || "Failed to reset password");
    }
  };

  if (!token || !email) {
    return (
      <MainLayout>
        <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
          <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">Error</h2>
          <p className="text-center text-red-600">Invalid reset link. Please request a new password recovery.</p>
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
        <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">Reset Password</h2>

        {(error || authError) && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error || authError}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">Password reset successfully! Redirecting to login...</p>
          </div>
        )}

        <p className="text-center text-sm text-[#4c739a] px-2">
          Enter your new password below.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col px-2">
          <input
            type="password"
            placeholder="New Password (min 6 characters)"
            value={password}
            onChange={e => setPassword(e.target.value)}
            disabled={authLoading}
            required
            style={{ height: "38px", marginTop: 12, marginBottom: "16px", borderRadius: "12px", paddingLeft: "16px" }}
            className="w-full rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none disabled:opacity-50"
          />
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            disabled={authLoading}
            required
            style={{ height: "38px", marginTop: 12, marginBottom: "32px", borderRadius: "12px", paddingLeft: "16px" }}
            className="w-full rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none disabled:opacity-50"
          />
          <Button type="submit" loading={authLoading} loadingText="Resetting..." disabled={authLoading}>
            Reset Password
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
