import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for error from backend
        const errorParam = searchParams.get("error");
        if (errorParam) {
          setError(decodeURIComponent(errorParam));
          return;
        }

        // The backend OAuth callback should have set the tokens
        // Check if we have access_token in the response
        const accessToken = searchParams.get("access_token");
        const userId = searchParams.get("user_id");
        const totpRequired = searchParams.get("totp_required") === "true";

        if (accessToken && userId) {
          // Store tokens from URL params
          localStorage.setItem("access_token", accessToken);
          localStorage.setItem("user_id", userId);
          
          // Redirect to dashboard
          setTimeout(() => navigate("/dashboard"), 500);
        } else {
          // If no tokens in URL, the backend might have used cookies
          // Try to redirect to dashboard anyway
          setTimeout(() => navigate("/dashboard"), 500);
        }
      } catch (err) {
        setError(err.message || "OAuth callback failed");
      }
    };

    handleCallback();
  }, [navigate, searchParams]);

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 w-full max-w-sm mx-auto">
        {error ? (
          <>
            <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">
              Authentication Failed
            </h2>
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
              <p className="text-sm">{error}</p>
            </div>
            <button
              onClick={() => navigate("/login")}
              style={{ height: "38px" }}
              className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
            >
              Back to Login
            </button>
          </>
        ) : (
          <>
            <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">
              Signing you in...
            </h2>
            <p className="text-center text-sm text-[#4c739a]">
              Please wait while we complete your authentication.
            </p>
          </>
        )}
      </div>
    </MainLayout>
  );
}
