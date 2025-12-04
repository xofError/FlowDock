import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layout/MainLayout.jsx";

export default function VerifyEmail() {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      if (prevInput) {
        prevInput.focus();
        const newOtp = [...otp];
        newOtp[index - 1] = "";
        setOtp(newOtp);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    console.log(`OTP entered: ${otp.join("")}`);
    setTimeout(() => {
      setIsLoading(false);
      navigate("/login");
    }, 2000);
  };

  const handleResend = () => {
    console.log("Activation email resent!");
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-10 w-full max-w-sm mx-auto">
        <h2 className="text-[#0d141b] text-[28px] font-bold text-center pt-4">
          Verify Email
        </h2>

        <p className="text-center text-sm text-[#4c739a] leading-relaxed">
          We've sent an email with an activation code. Please enter the 6-digit
          code below.
        </p>

        <form className="flex flex-col gap-6 px-2" onSubmit={handleSubmit}>
          <div
            style={{
              display: "flex",
              gap: "12px",
              justifyContent: "center",
              marginBottom: "16px",
            }}
          >
            {otp.map((digit, i) => (
              <input
                key={i}
                id={`otp-${i}`}
                type="text"
                maxLength="1"
                value={digit}
                onChange={(e) => handleChange(e, i)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                disabled={isLoading}
                style={{ width: "50px", height: "50px", fontSize: "24px" }}
                className="text-center rounded-lg bg-[#e7edf3] text-[#0d141b] font-bold focus:outline-none border-2 border-transparent focus:border-[#1380ec] disabled:opacity-50"
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{ height: "38px", opacity: isLoading ? 0.7 : 1 }}
            className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
          >
            {isLoading ? "Verifying..." : "Verify"}
          </button>
        </form>

        <div className="text-center px-2">
          <button
            onClick={handleResend}
            className="text-[#4c739a] underline text-sm"
          >
            Resend Email
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
