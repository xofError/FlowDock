import React from "react";
import MainLayout from "../layout/MainLayout";

export default function Privacy() {
  return (
    <MainLayout hideSidebar={true}>
      <div className="max-w-[900px] mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold mb-4">Privacy Policy</h1>
        <p className="text-[#4c739a] mb-3">
          This page contains the Privacy Policy. Replace this placeholder with your detailed privacy practices.
        </p>
        <p className="text-sm text-[#4c739a]">
          Example sections: Data collected, Purpose of processing, Cookies, Data retention, User rights, Contact.
        </p>
      </div>
    </MainLayout>
  );
}
