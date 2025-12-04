import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layout/MainLayout.jsx";
import "../resources/fonts/fonts.css";

export default function PassRecovery() {
  const [email, setEmail] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email) return alert("Enter your email");
    alert(`Recovery email sent to ${email}`);
    navigate("/pass-recovery-verify");
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 font-custom">
        <h2 className="text-[#0D141B] text-2xl font-bold text-center">Password Recovery</h2>

        <p className="text-center text-sm text-[#4c739a] max-w-[280px] mx-auto">
          Enter your email and we will send you an activation code.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full h-14 rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none"
          />
          <button type="submit" className="h-14 w-full bg-[#1380EC] text-white rounded-lg font-bold">
            Send Code
          </button>
        </form>
      </div>
    </MainLayout>
  );
}
