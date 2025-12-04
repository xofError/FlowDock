import { Link } from "react-router-dom";
import { useState } from "react";
import MainLayout from "../layout/MainLayout.jsx";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleSignIn = (e) => {
    e.preventDefault();
    setIsLoading(true);
    console.log("Sign In clicked", { email, password });
    // Simulate backend delay
    setTimeout(() => setIsLoading(false), 2000);
  };

  const handleGoogleSignIn = () => {
    setIsGoogleLoading(true);
    console.log("Google Sign In clicked");
    // Simulate backend delay
    setTimeout(() => setIsGoogleLoading(false), 2000);
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-8 pb-10 w-full max-w-sm mx-auto">

        {/* Heading */}
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-4">
          Welcome back
        </h2>

        {/* Form */}
        <form className="flex flex-col px-2" onSubmit={handleSignIn}>
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading || isGoogleLoading}
            style={{ height: "38px", marginBottom: "16px" }}
            className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
          />

          <input
            name="password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading || isGoogleLoading}
            style={{ height: "38px", marginBottom: "32px" }}
            className="w-full rounded-lg bg-[#e7edf3] px-4 text-[#0d141b] placeholder:text-[#4c739a] text-base focus:outline-none border-none disabled:opacity-50"
          />

          {/* Buttons with proper gap */}
          <div className="flex flex-col">
            <button
              type="submit"
              disabled={isLoading || isGoogleLoading}
              style={{ height: "38px", marginBottom: "16px", opacity: isLoading ? 0.7 : 1 }}
              className="w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold flex items-center justify-center transition-all"
            >
              {isLoading ? "Signing In..." : "Sign In"}
            </button>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={isLoading || isGoogleLoading}
              style={{ height: "38px", opacity: isGoogleLoading ? 0.7 : 1 }}
              className="w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold flex items-center justify-center transition-all"
            >
              {isGoogleLoading ? "Signing In..." : "Sign in with Google"}
            </button>
          </div>
        </form>

        {/* Forgot password */}
        <div className="text-center mt-3">
          <Link to="/pass-recovery" className="text-[#4c739a] text-sm underline">
            Forgot password?
          </Link>
        </div>

        {/* Sign Up link */}
        <p className="text-center mt-4 text-sm">
          Don't have an account?{" "}
          <Link to="/signup" className="text-blue-600 underline">
            Sign Up
          </Link>
        </p>
      </div>
    </MainLayout>
  );
}
