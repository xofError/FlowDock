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

    // auto-focus next input
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

        {/* Heading */}
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-2">
          Verify Email
        </h2>

        {/* Description */}
        <p className="text-center text-sm text-[#4c739a] max-w-[280px] mx-auto">
          We've sent an email with an activation code.
          <br />
          Please enter the 6-digit code below.
        </p>

        {/* OTP Form */}
        <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
          <div className="flex justify-center gap-3">
            {otp.map((digit, i) => (
              <input
                key={i}
                id={`otp-${i}`}
                type="text"
                maxLength="1"
                value={digit}
                onChange={(e) => handleChange(e, i)}
                className="w-14 h-14 text-center rounded-lg border bg-[#e7edf3] text-[#0d141b] text-lg font-bold focus:outline-none"
              />
            ))}
          </div>

          <button
            type="submit"
            className="h-14 w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold mt-4"
          >
            Verify
          </button>
        </form>

        {/* Resend Email */}
        <div className="text-center mt-3">
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
