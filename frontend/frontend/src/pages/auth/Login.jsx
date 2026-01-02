import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import MainLayout from "../../layout/MainLayout.jsx";
import { useAuthContext } from "../../context/AuthContext.jsx";
import Button from "../../components/Button.jsx";
import GoogleIcon from "../../resources/icons/social-google-plus-svgrepo-com.svg";
import { AUTH_API_URL } from "../../services/api.js";

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuthContext();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Call the real login function which may return totp_required
      const response = await login(email, password, totpCode || null);

      // persist user (backend / login hook may already do this, but force here)
      try {
        const userToStore = response?.user || { email };
        if (typeof window !== "undefined" && userToStore) {
          localStorage.setItem("user", JSON.stringify(userToStore));
        }
      } catch (e) {
        // ignore storage errors
      }

      // If backend requires TOTP, navigate to the verify-TOTP page with credentials
      if (response?.totp_required) {
        navigate("/verify-totp", { state: { email, password } });
        return;
      }

      // Otherwise login succeeded (tokens stored by useAuth), go to dashboard
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // Redirect to backend OAuth login endpoint
    window.location.href = `${AUTH_API_URL}/auth/oauth/google/login`;
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-8 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        <div>
          <h2
            className="text-[#0d141b] text-[28px] font-bold leading-tight text-center"
            style={{ marginTop: "1.5cm" }}
          >
            Welcome back
          </h2>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Form */}
        <form className="flex flex-col gap-3 px-2" onSubmit={handleSignIn}>
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="email"
            style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
            className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
          />

          <input
            name="password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            autoComplete="current-password"
            style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
            className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
          />

          <input
            name="totpCode"
            type="text"
            placeholder="2FA Code (optional)"
            value={totpCode}
            onChange={(e) => setTotpCode(e.target.value.slice(0, 6))}
            disabled={isLoading}
            style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
            className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
            maxLength="6"
          />

          {/* Buttons with proper gap */}
          <div className="flex flex-col gap-3" style={{ marginTop: 24 }}>
            <Button type="submit" loading={isLoading} loadingText="Loading..." disabled={isLoading}>
              Sign In
            </Button>

            <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
              <Button 
                type="button"
                variant="secondary"
                loading={isLoading}
                loadingText="Redirecting..."
                onClick={handleGoogleSignIn}
                disabled={isLoading}
                className="flex items-center justify-center"
              >
                <span>Sign in with</span>
                <span style={{ marginLeft: "4px", marginRight: "4px" }}> </span>
                <img src={GoogleIcon} alt="Google" style={{ height: "18px", width: "18px" }} />
              </Button>

              <Button
                type="button"
                variant="secondary"
                loading={isLoading}
                loadingText="Redirecting..."
                onClick={() => navigate("/sign-in-email")}
                disabled={isLoading}
                className="flex items-center justify-center"
              >
                Sign In with Passcode
              </Button>
            </div>
          </div>
        </form>

        {/* Forgot password */}
        <div className="text-center" style={{ marginTop: "2mm" }}>
          <Link to="/pass-recovery" className="text-[#4c739a] text-sm underline">
            Forgot password?
          </Link>
        </div>

        {/* Sign Up link */}
        <p className="text-center text-sm">
          Don't have an account?{" "}
          <Link to="/signup" className="text-blue-600 underline">
            Sign Up
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
