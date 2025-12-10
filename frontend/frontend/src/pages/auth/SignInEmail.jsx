import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";
import Button from "../../components/Button.jsx";
import { useAuthContext } from "../../context/AuthContext.jsx";

export default function SignInEmail() {
  const navigate = useNavigate();
  const { generatePasscode, error: authError } = useAuthContext();
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!email) {
      setError("Please enter your email");
      return;
    }
    setLoading(true);
    try {
      // Generate passcode via useAuth hook
      await generatePasscode(email);
      // Navigate to passcode check page
      navigate("/passcode-check", { state: { email, next: "dashboard" } });
    } catch (err) {
      setError(authError || err?.message || "Failed to send sign-in code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 justify-center" style={{ width: "320px", margin: "0 auto" }}>
        <h2 className="text-[#0d141b] text-[28px] font-bold text-center" style={{ marginTop: "1.5cm" }}>
          Sign In with Email
        </h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg" role="alert">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3 px-2">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            autoComplete="email"
            style={{ height: "44px", marginTop: 12, borderRadius: "12px", paddingLeft: "16px" }}
            className="rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border border-[#d0dce8] disabled:opacity-50"
          />

          <div className="flex flex-col gap-3" style={{ marginTop: 24 }}>
            <Button type="submit" loading={loading} loadingText="Sending..." disabled={loading}>
              Send Sign-in Code
            </Button>
          </div>
        </form>
      </div>
    </MainLayout>
  );
}
