import { useState } from "react";
import MainLayout from "../layout/MainLayout.jsx";
import "../resources/fonts/fonts.css";

export default function VerifyEmail() {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);

  const handleChange = (e, index) => {
    const value = e.target.value.replace(/\D/, "");
    const newOtp = [...otp];
    newOtp[index] = value ? value[0] : "";
    setOtp(newOtp);

    if (index < 5 && value) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`OTP entered: ${otp.join("")}`);
  };

  const handleResend = () => {
    alert("Activation email resent!");
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 font-custom">

        <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-2">
          Verify Email
        </h2>

        <p className="text-center text-sm text-[#4c739a] max-w-[320px] mx-auto leading-relaxed">
          We've sent an email with an activation <br />
          code. Please enter the 6-digit code below.
        </p>

        <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
          <div className="flex justify-center gap-3 mt-2">
            {otp.map((digit, i) => (
              <input
                key={i}
                id={`otp-${i}`}
                type="text"
                maxLength="1"
                value={digit}
                onChange={e => handleChange(e, i)}
                className="w-14 h-14 text-center rounded-lg bg-[#e7edf3] text-[#0d141b] text-lg font-bold focus:outline-none"
              />
            ))}
          </div>

          <button
            type="submit"
            className="h-14 w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold mt-6"
          >
            Verify
          </button>
        </form>

        <div className="text-center mt-4">
          <button
            onClick={handleResend}
            className="text-blue-600 underline text-sm"
          >
            Resend Email
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
