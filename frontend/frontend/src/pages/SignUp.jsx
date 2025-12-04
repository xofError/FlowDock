import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import MainLayout from "../layout/MainLayout.jsx";

export default function SignUp() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [enable2FA, setEnable2FA] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!formData.name || !formData.email || !formData.password) {
      alert("Please fill all fields");
      return;
    }

    setIsLoading(true);
    // Simulate backend delay
    setTimeout(() => {
      setIsLoading(false);
      if (enable2FA) {
        navigate("/2fa");
      } else {
        navigate("/verify-email");
      }
    }, 2000);
  };

  const handleGoogleSignUp = () => {
    setIsGoogleLoading(true);
    console.log("Google Sign Up clicked");
    setTimeout(() => setIsGoogleLoading(false), 2000);
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-8 pb-10 w-full max-w-sm mx-auto">

        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
          Create your account
        </h2>

        <form className="flex flex-col px-2" onSubmit={handleSubmit}>
          <input
            name="name"
            type="text"
            placeholder="Name"
            value={formData.name}
            onChange={handleChange}
            disabled={isLoading || isGoogleLoading}
            style={{ height: "38px", marginBottom: "16px" }}
            className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
          />
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            disabled={isLoading || isGoogleLoading}
            style={{ height: "38px", marginBottom: "16px" }}
            className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
          />
          <input
            name="password"
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            disabled={isLoading || isGoogleLoading}
            style={{ height: "38px", marginBottom: "16px" }}
            className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
          />

          {/* 2FA toggle */}
          <label
            // moved spacing to inline styles to ensure it is applied
            style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "24px", fontSize: "0.875rem" }}
          >
            <input
              type="checkbox"
              checked={enable2FA}
              onChange={() => setEnable2FA(prev => !prev)}
              disabled={isLoading || isGoogleLoading}
              // keep size as pixels so styles are explicit
              style={{ width: 20, height: 20 }}
            />
            Enable Two-Factor Authentication
          </label>

          <div className="flex flex-col">
            <button
              type="submit"
              disabled={isLoading || isGoogleLoading}
              style={{ height: "38px", marginBottom: "16px", opacity: isLoading ? 0.7 : 1 }}
              className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
            >
              {isLoading ? "Creating Account..." : "Sign Up"}
            </button>

            <button
              type="button"
              onClick={handleGoogleSignUp}
              disabled={isLoading || isGoogleLoading}
              style={{ height: "38px", opacity: isGoogleLoading ? 0.7 : 1 }}
              className="w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold flex items-center justify-center transition-all"
            >
              {isGoogleLoading ? "Signing Up..." : "Sign up with Google"}
            </button>
          </div>
        </form>

        <p className="text-center mt-4 text-sm">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-600 underline">
            Sign In
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
