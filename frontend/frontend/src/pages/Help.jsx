import React from "react";
import MainLayout from "../layout/MainLayout";

export default function Help() {
  return (
    <MainLayout hideSidebar={true}>
      <div className="max-w-[900px] mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-[#0d141b] mb-4">Help & Documentation</h1>
        <p className="text-[#4c739a] mb-6">This is a placeholder help page. Add FAQs, guides and links here.</p>

        <section className="grid gap-4">
          <div className="p-4 border rounded bg-white">
            <h3 className="font-semibold">Getting started</h3>
            <p className="text-sm text-[#4c739a] mt-2">Create an account, upload files and manage sharing.</p>
          </div>

          <div className="p-4 border rounded bg-white">
            <h3 className="font-semibold">Sharing files</h3>
            <p className="text-sm text-[#4c739a] mt-2">Use the share button to create links, set expiry and permissions.</p>
          </div>
        </section>
      </div>
    </MainLayout>
  );
}
