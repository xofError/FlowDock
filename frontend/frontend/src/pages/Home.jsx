import React from "react";
import MainLayout from "../layout/MainLayout";

export default function Home() {
  return (
    <MainLayout hideSidebar={true}>
      <div className="min-h-screen">
        <div className="px-10 py-16">
          <div
            className="max-w-[960px] mx-auto rounded-lg p-8 bg-cover bg-center"
            style={{
              backgroundImage: 'linear-gradient(rgba(0,0,0,0.12), rgba(0,0,0,0.4)), url("/src/resources/background.jpg")',
            }}
          >
            <h1 className="text-white text-4xl font-black">Secure Cloud Storage for Your Peace of Mind</h1>
            <p className="text-white mt-3 max-w-xl">FlowDock provides a secure and reliable cloud storage solution. Experience seamless file management with advanced security features.</p>
            <div className="mt-6">
              <a href="/signup" className="inline-block bg-[#1380ec] text-white px-4 py-2 rounded">Get Started</a>
            </div>
          </div>

          <section className="mt-12 max-w-[960px] mx-auto">
            <h2 className="text-2xl font-bold text-[#0d141b] mb-4">Key Features</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 border rounded bg-white">
                <h3 className="font-bold">Advanced Security</h3>
                <p className="text-sm text-[#4c739a] mt-2">Encryption, MFA and more.</p>
              </div>
              <div className="p-4 border rounded bg-white">
                <h3 className="font-bold">Reliable Access</h3>
                <p className="text-sm text-[#4c739a] mt-2">Access your files anytime.</p>
              </div>
              <div className="p-4 border rounded bg-white">
                <h3 className="font-bold">Data Protection</h3>
                <p className="text-sm text-[#4c739a] mt-2">Privacy-first by design.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </MainLayout>
  );
}
