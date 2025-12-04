import { Link } from "react-router-dom";
import "../resources/fonts/fonts.css";

// Inline MainLayout for clarity
function MainLayout({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="w-full max-w-[320px] p-8 bg-white rounded-2xl shadow-md">
        {children}
      </div>
    </div>
  );
}

export default function Login() {
  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-6 font-custom">

        {/* Heading */}
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-2">
          Welcome back
        </h2>

        {/* Form */}
        <form className="flex flex-col gap-4" onSubmit={(e) => e.preventDefault()}>
          <input
            name="email"
            type="email"
            placeholder="Email"
            className="w-full rounded-lg bg-[#e7edf3] h-14 px-4
                       text-[#0d141b] placeholder:text-[#4c739a]
                       text-base font-normal focus:outline-none border-none"
          />

          <input
            name="password"
            type="password"
            placeholder="Password"
            className="w-full rounded-lg bg-[#e7edf3] h-14 px-4
                       text-[#0d141b] placeholder:text-[#4c739a]
                       text-base font-normal focus:outline-none border-none"
          />

          <input
            name="twofactor"
            type="text"
            placeholder="2FA Code (if enabled)"
            className="w-full rounded-lg bg-[#e7edf3] h-14 px-4
                       text-[#0d141b] placeholder:text-[#4c739a]
                       text-base font-normal focus:outline-none border-none"
          />

          {/* Buttons */}
          <div className="flex flex-col gap-3 mt-2">
            <button
              type="submit"
              className="h-14 w-full rounded-lg bg-[#1380ec] text-white text-lg font-bold"
            >
              Sign In
            </button>

            <button
              type="button"
              className="h-14 w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold"
            >
              Sign in with Google
            </button>
          </div>
        </form>

        {/* Forgot password */}
        <div className="text-center mt-3">
          <a href="#" className="text-[#4c739a] text-sm underline cursor-pointer">
            Forgot password?
          </a>
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
