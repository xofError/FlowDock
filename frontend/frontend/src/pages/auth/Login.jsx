import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [totpRequired, setTotpRequired] = useState(false);
  const [totpCode, setTotpCode] = useState("");

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await login(email, password, totpRequired ? totpCode : null);
      
      if (totpRequired && totpCode) {
        // TOTP verified, redirect to dashboard
        navigate("/dashboard");
      } else if (response.totp_required) {
        // TOTP required, show input for code (don't redirect yet)
        setTotpRequired(true);
        setPassword(""); // Clear password field
      } else {
        // Login successful, redirect
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    console.log("Google Sign In clicked - not implemented yet");
    // TODO: Implement actual OAuth
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-8 pb-10 w-full max-w-sm mx-auto">

        {/* Heading */}
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
          Welcome back
        </h2>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Form */}
        <form className="flex flex-col px-2" onSubmit={handleSignIn}>
          {!totpRequired ? (
            <>
              <input
                name="email"
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                style={{ height: "38px", marginBottom: "16px" }}
                className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
              />

              <input
                name="password"
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                style={{ height: "38px", marginBottom: "32px" }}
                className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
              />
            </>
          ) : (
            <input
              name="totpCode"
              type="text"
              placeholder="Enter 6-digit code"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.slice(0, 6))}
              required
              disabled={isLoading}
              style={{ height: "38px", marginBottom: "32px" }}
              className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
              maxLength="6"
            />
          )}

          {/* Buttons with proper gap */}
          <div className="flex flex-col">
            <button
              type="submit"
              disabled={isLoading}
              style={{ height: "38px", marginBottom: "16px", opacity: isLoading ? 0.7 : 1 }}
              className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
            >
              {isLoading ? "Loading..." : totpRequired ? "Verify Code" : "Sign In"}
            </button>

            {!totpRequired && (
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={isLoading}
                style={{ height: "38px" }}
                className="w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold flex items-center justify-center transition-all"
              >
                Sign in with Google
              </button>
            )}
          </div>
        </form>

        {/* Forgot password */}
        <div className="text-center mt-3">
          <Link to="/pass-recovery" className="text-[#4c739a] text-sm underline">
            Forgot password?
          </Link>
        </div>

        {/* Sign Up link */}
        <p className="text-center mt-4 text-sm">
          Don't have an account?{" "}
          <Link to="/signup" className="text-blue-600 underline">
            Sign Up
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
