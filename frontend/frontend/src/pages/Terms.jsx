import React from "react";
import MainLayout from "../layout/MainLayout";

export default function Terms() {
  return (
    <MainLayout hideSidebar={true}>
      <div className="max-w-[900px] mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-4">Terms of Service</h1>
        <p className="text-[#4c739a] mb-3">
          This page contains the Terms of Service. Replace this placeholder with your full terms.
        </p>
        <p className="text-sm text-[#4c739a]">
          Example sections: Use of Service, Account responsibilities, Intellectual Property, Limitations of liability, Governing law.
        </p>
      </div>
    </MainLayout>
  );
}
