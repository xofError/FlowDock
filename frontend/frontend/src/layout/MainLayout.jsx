// src/layout/MainLayout.jsx
import React from "react";

export default function MainLayout({ children }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="w-full max-w-[320px] p-8 bg-white rounded-2xl shadow-md">
        {children}
      </div>
    </div>
  );
}
