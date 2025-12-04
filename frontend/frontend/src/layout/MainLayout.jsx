import React from "react";

// src/layout/MainLayout.jsx

export default function MainLayout({ children }) {
  return (
    <div className="min-h-screen w-full bg-slate-100 flex justify-center">
      {/* Medium-width container, top-aligned, NOT vertically centered */}
      <div className="w-full max-w-md p-8 mt-20 bg-white rounded-2xl shadow-md">
        {children}
      </div>
    </div>
  );
}
