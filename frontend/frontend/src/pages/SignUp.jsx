import { useState } from "react";
import { Link } from "react-router-dom";
import "../resources/fonts/fonts.css";

// Inline MainLayout for consistency
function MainLayout({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="w-full max-w-[320px] p-8 bg-white rounded-2xl shadow-md">
        {children}
      </div>
    </div>
  );
}

export default function SignUp() {
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Account created for ${formData.email}`);
  };

  return (
    <MainLayout>
      <div className="flex flex-col gap-6 pb-6 font-custom">

        {/* Heading */}
        <h2 className="text-[#0d141b] text-[28px] font-bold leading-tight text-center pt-2">
          Create your account
        </h2>

        {/* Form */}
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <input
            name="name"
            type="text"
            placeholder="Name"
            value={formData.name}
            onChange={handleChange}
            className="w-full rounded-lg bg-[#e7edf3] h-14 px-4
                       text-[#0d141b] placeholder:text-[#4c739a]
                       text-base font-normal focus:outline-none border-none"
          />

          <input
            name="email"
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            className="w-full rounded-lg bg-[#e7edf3] h-14 px-4
                       text-[#0d141b] placeholder:text-[#4c739a]
                       text-base font-normal focus:outline-none border-none"
          />

          <input
            name="password"
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
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
              Create Account
            </button>

            <button
              type="button"
              className="h-14 w-full rounded-lg bg-[#E7EDF3] text-[#0D141B] text-lg font-bold"
            >
              Sign up with Google
            </button>
          </div>
        </form>

        {/* Sign In link */}
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
