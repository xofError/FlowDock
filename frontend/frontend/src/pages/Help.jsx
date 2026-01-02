import React from "react";
import Header from "../layout/Header";
import Footer from "../layout/Footer";
import HelpHeader from "./help/Header";

export default function Help() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="container" style={{ flex: 1, padding: "2rem 0" }}>
        <HelpHeader title="Help" subtitle="If you need assistance, check the documentation or contact support." />

        <section style={{ marginTop: "1.25rem", maxWidth: 920 }}>
          <p style={{ color: "#64748b", marginBottom: "1rem" }}>
            For immediate support contact:{" "}
            <a href="mailto:flowdockproduction@gmail.com" style={{ color: "#2563eb" }}>
              flowdockproduction@gmail.com
            </a>
          </p>

          <h2 style={{ fontSize: "1.125rem", fontWeight: 700, color: "#0f172a" }}>Quick Resources</h2>
          <ul style={{ color: "#64748b", marginTop: "0.5rem", lineHeight: 1.6 }}>
            <li>Getting started guide</li>
            <li>Account & billing</li>
            <li>Security & privacy</li>
          </ul>

          <div style={{ marginTop: "1.5rem", color: "#64748b" }}>
            If you can't find what you need here, email support.
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
