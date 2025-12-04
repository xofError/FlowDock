import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layout/MainLayout.jsx";

export default function PassRecoveryVerify() {
  const [otp, setOtp] = useState(Array(6).fill(""));
  const navigate = useNavigate();

  const handleChange = (index, value) => {
    if (/^[0-9]?$/.test(value)) {
      const newOtp = [...otp];
      newOtp[index] = value;
      setOtp(newOtp);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (otp.some(d => d === "")) return alert("Complete the 6-digit code");
    alert(`OTP verified: ${otp.join("")}`);
    navigate("/reset-password");
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 font-custom">
        <h2 className="text-[#0D141B] text-2xl font-bold text-center">Verify Email</h2>

        <p className="text-center text-sm text-[#4c739a] max-w-[280px] mx-auto">
          We've sent an email with an activation code.<br/>
          Please enter the 6-digit code below.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-6 items-center">
          <div className="flex gap-2">
            {otp.map((digit, i) => (
              <input
                key={i}
                type="text"
                value={digit}
                onChange={e => handleChange(i, e.target.value)}
                className="w-12 h-12 text-center rounded-lg border border-gray-300 text-lg focus:outline-none"
              />
            ))}
          </div>
          <button type="submit" className="h-12 w-full bg-[#1380EC] text-white rounded-lg font-bold">
            Verify
          </button>
        </form>

        <div className="text-center mt-2">
          <button className="text-blue-600 underline text-sm">
            Resend Email
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
