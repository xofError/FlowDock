import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import { useAuthContext } from "../../context/AuthContext.jsx";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const { handleOAuthCallback } = useAuthContext();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for error from backend
        const errorParam = searchParams.get("error");
        if (errorParam) {
          setError(decodeURIComponent(errorParam));
          setIsProcessing(false);
          return;
        }

        // Extract tokens from URL parameters
        const accessToken = searchParams.get("access_token");
        const userId = searchParams.get("user_id");

        if (accessToken && userId) {
          // Use the OAuth callback handler
          await handleOAuthCallback(accessToken, userId);
          
          // Redirect to dashboard
          setTimeout(() => {
            navigate("/dashboard", { replace: true });
          }, 300);
        } else {
          setError("No authentication tokens received from OAuth provider");
          setIsProcessing(false);
        }
      } catch (err) {
        console.error("OAuth callback error:", err);
        setError(err.message || "OAuth callback processing failed");
        setIsProcessing(false);
      }
    };

    handleCallback();
  }, [navigate, searchParams, handleOAuthCallback]);

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
        ) : isProcessing ? (
          <>
            <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">
              Signing you in...
            </h2>
            <p className="text-center text-sm text-[#4c739a]">
              Please wait while we complete your authentication.
            </p>
          </>
        ) : null}
      </div>
    </MainLayout>
  );
}
