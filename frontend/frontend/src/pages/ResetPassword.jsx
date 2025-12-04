import { useState } from "react";
import { useNavigate } from "react-router-dom"; // <-- import
import MainLayout from "../layout/MainLayout.jsx";

export default function ResetPassword() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const navigate = useNavigate(); // <-- initialize

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!password || !confirmPassword) return alert("Fill both fields");
    if (password !== confirmPassword) return alert("Passwords do not match");

    alert("Password reset successfully!");
    navigate("/login"); // <-- redirect to Sign In
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 font-custom">
        <h2 className="text-[#0D141B] text-2xl font-bold text-center">Reset Password</h2>

        <p className="text-center text-sm text-[#4c739a] max-w-[280px] mx-auto">
          Enter your new password below.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="password"
            placeholder="New Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full h-14 rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none"
          />
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            className="w-full h-14 rounded-lg px-4 bg-[#e7edf3] text-[#0D141B] placeholder:text-[#4c739a] focus:outline-none border-none"
          />
          <button type="submit" className="h-14 w-full bg-[#1380EC] text-white rounded-lg font-bold">
            Reset Password
          </button>
        </form>
      </div>
    </MainLayout>
  );
}
