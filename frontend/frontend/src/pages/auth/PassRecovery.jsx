import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../../layout/MainLayout.jsx";

export default function PassRecovery() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email) return alert("Enter your email");

    setIsLoading(true);
    console.log(`Recovery email sent to ${email}`);
    setTimeout(() => {
      setIsLoading(false);
      navigate("/pass-recovery-verify");
    }, 2000);
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 w-full max-w-sm mx-auto">
        <h2 className="text-[#0D141B] text-[28px] font-bold text-center pt-4">Password Recovery</h2>

        <p className="text-center text-sm text-[#4c739a] px-2">
          Enter your email and we will send you an activation code.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col px-2">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            disabled={isLoading}
            style={{ height: "38px", marginBottom: "32px" }}
            className="w-full rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading}
            style={{ height: "38px", opacity: isLoading ? 0.7 : 1 }}
            className="w-full bg-[#1380EC] text-white rounded-lg font-bold flex items-center justify-center transition-all"
          >
            {isLoading ? "Sending..." : "Send Code"}
          </button>
        </form>
      </div>
    </MainLayout>
  );
}
