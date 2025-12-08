import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { QRCodeSVG } from "qrcode.react";
import MainLayout from "../../layout/MainLayout.jsx";
import useAuth from "../../hooks/useAuth.js";
import Button from "../../components/Button.jsx";

export default function TwoFactorAuth() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setupTOTP, verifyTOTP, loading: authLoading, error: authError } = useAuth();
  
  const [email, setEmail] = useState("");
  const [step, setStep] = useState("setup"); // setup, qr, verify, or complete
  const [qrUri, setQrUri] = useState("");
  const [totpSecret, setTotpSecret] = useState("");
  const [totp, setTotp] = useState(Array(6).fill(""));
  const [error, setError] = useState(null);
  const [recoveryCodes, setRecoveryCodes] = useState([]);

  useEffect(() => {
    // Get email from navigation state or redirect back
    if (location.state?.email) {
      setEmail(location.state.email);
      handleSetupTOTP(location.state.email);
    } else {
      navigate("/signup");
    }
  }, [location.state, navigate]);

  const handleSetupTOTP = async (emailAddress) => {
    try {
      const response = await setupTOTP(emailAddress);
      setTotpSecret(response.totp_secret);
      setQrUri(response.totp_uri);
      setStep("qr");
    } catch (err) {
      setError(err.message || "Failed to setup TOTP");
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

  const handleVerifyTotp = async (e) => {
    e.preventDefault();
    setError(null);

    if (totp.some(d => d === "")) {
      setError("Please enter the complete 6-digit code");
      return;
    }

    try {
      const code = totp.join("");
      const response = await verifyTOTP(email, code, totpSecret);
      setRecoveryCodes(response.recovery_codes || []);
      setStep("complete");
      setTimeout(() => navigate("/login"), 3000);
    } catch (err) {
      setError(err.message || "Invalid TOTP code");
      setTotp(Array(6).fill(""));
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        
        {step === "setup" && (
          <>
            <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">
              Enable Two-Factor Authentication
            </h2>

            {(error || authError) && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
                <p className="text-sm">{error || authError}</p>
              </div>
            )}

            <p className="text-center text-sm text-[#4c739a] px-2">
              Scanning QR code...
            </p>
          </>
        )}

        {step === "qr" && (
          <>
            <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">
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

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                <strong>Can't scan?</strong> Enter this key manually in your authenticator app:
              </p>
              <p className="text-xs text-yellow-900 font-mono mt-2 break-all">
                {qrUri.match(/secret=([^&]*)/)?.[1] || ""}
              </p>
            </div>

            <Button
              type="button"
              onClick={() => setStep("verify")}
            >
              I've Scanned the QR Code
            </Button>
          </>
        )}

        {step === "verify" && (
          <>
            <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">
              Verify TOTP Code
            </h2>

            {(error || authError) && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
                <p className="text-sm">{error || authError}</p>
              </div>
            )}

            <p className="text-center text-sm text-[#4c739a] px-2">
              Enter the 6-digit code from your authenticator app.
            </p>

            <form onSubmit={handleVerifyTotp} className="flex flex-col gap-3 px-2">
              <div className="flex gap-2 justify-center">
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
                    className="rounded-lg bg-[#e7edf3] text-[#0d141b] text-center text-xl font-bold focus:outline-none border border-[#d0dce8] disabled:opacity-50"
                  />
                ))}
              </div>

              <Button
                  type="submit"
                  loading={authLoading}
                  loadingText="Verifying..."
                  disabled={authLoading}
              >
                Verify
              </Button>
            </form>

            <button
              onClick={() => {
                setStep("qr");
                setTotp(Array(6).fill(""));
              }}
              className="text-center text-blue-600 underline text-sm"
            >
              Back to QR Code
            </button>
          </>
        )}

        {step === "complete" && (
          <>
            <div className="text-center py-8">
              <div className="text-5xl mb-4">✓</div>
              <h2 className="text-[#0D141B] text-[28px] font-bold mb-4">Two-Factor Enabled!</h2>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800 mb-3">
                <strong>Save your recovery codes:</strong>
              </p>
              <div className="bg-white rounded p-3 font-mono text-xs space-y-1 max-h-40 overflow-y-auto">
                {recoveryCodes.map((code, i) => (
                  <div key={i} className="text-green-900">{code}</div>
                ))}
              </div>
              <p className="text-xs text-green-700 mt-2">
                Store these codes in a safe place. You can use them to recover your account if you lose access to your authenticator app.
              </p>
            </div>

            <p className="text-center text-sm text-[#4c739a] mt-4">
              Two-factor authentication is now enabled. You'll be asked for a code from your authenticator app on your next login.
            </p>

            <p className="text-center text-xs text-gray-600 mt-4">
              Redirecting to login in a few seconds...
            </p>
          </>
        )}
      </div>
    </MainLayout>
  );
}
