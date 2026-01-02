import React, { useState } from "react";
import Header from "../layout/Header";
import Footer from "../layout/Footer";
import LegalModal from "../components/LegalModal";
import BackgroundImage from "../resources/images/background.jpg";
import SecurityIcon from "../resources/icons/security.svg";
import CloudIcon from "../resources/icons/cloud.svg";
import LockIcon from "../resources/icons/lock.svg";

export default function Home() {
  const [legalModal, setLegalModal] = useState(null); // "privacy" | "terms" | null

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <Header />

      {/* Hero Section with Background Image */}
      <section
        className="relative overflow-hidden flex-1"
        style={{
          backgroundImage: `url(${BackgroundImage})`,
          backgroundSize: "cover",
          backgroundPosition: "top left",
          backgroundRepeat: "no-repeat",
          backgroundAttachment: "fixed",
          minHeight: "90vh",
        }}
      >
        {/* Subtle Overlay for text readability */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.12)",
            zIndex: 1,
          }}
        />

        {/* Positioned top-left over the image */}
        <div
          className="relative z-10"
          style={{
            position: "absolute",
            top: "1rem",
            left: "1.25rem",
            maxWidth: "720px",
          }}
        >
          <h1
            style={{
              fontSize: "3rem",
              fontWeight: 900,
              color: "#ffffff",
              lineHeight: 1.1,
              margin: 0,
              textShadow: "0 4px 12px rgba(0,0,0,0.45)",
              letterSpacing: "-0.02em",
            }}
          >
            Secure Cloud Storage for Your
            <br />
            Peace of Mind
          </h1>
        </div>
      </section>

      {/* Key Features Section */}
      <section
        style={{
          paddingTop: "4rem",
          paddingBottom: "4rem",
          paddingLeft: "3rem",
          paddingRight: "3rem",
          backgroundColor: "#ffffff",
        }}
      >
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          {/* Section Title */}
          <h2
            style={{
              fontSize: "2rem",
              fontWeight: "700",
              color: "#0f172a",
              marginBottom: "0.5rem",
            }}
          >
            Key Features
          </h2>

          {/* Section Subtitle */}
          <p
            style={{
              fontSize: "0.875rem",
              color: "#64748b",
              marginBottom: "2rem",
            }}
          >
            FlowDock offers a range of features designed to enhance your cloud
            storage experience.
          </p>

          {/* Feature Cards Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "1.5rem",
            }}
          >
            {/* Card 1 */}
            <div
              style={{
                backgroundColor: "transparent",
                border: "1px solid #d1d5db",
                borderRadius: "12px",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <img src={SecurityIcon} alt="Security" style={{ width: 36, height: 36, marginBottom: 8 }} />
              <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 700, color: "#0f172a" }}>Advanced Security</h3>
              <p style={{ margin: 0, fontSize: "0.875rem", color: "#64748b" }}>
                Benefit from state-of-the-art encryption and multi-factor authentication to keep your data safe.
              </p>
            </div>

            {/* Card 2 */}
            <div
              style={{
                backgroundColor: "transparent",
                border: "1px solid #d1d5db",
                borderRadius: "12px",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <img src={CloudIcon} alt="Cloud" style={{ width: 36, height: 36, marginBottom: 8 }} />
              <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 700, color: "#0f172a" }}>Reliable Access</h3>
              <p style={{ margin: 0, fontSize: "0.875rem", color: "#64748b" }}>
                Access your files anytime, anywhere with our robust and reliable cloud infrastructure.
              </p>
            </div>

            {/* Card 3 */}
            <div
              style={{
                backgroundColor: "transparent",
                border: "1px solid #d1d5db",
                borderRadius: "12px",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <img src={LockIcon} alt="Lock" style={{ width: 36, height: 36, marginBottom: 8 }} />
              <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 700, color: "#0f172a" }}>Data Protection</h3>
              <p style={{ margin: 0, fontSize: "0.875rem", color: "#64748b" }}>
                We prioritize your data's integrity and confidentiality, ensuring it remains secure and private.
              </p>
            </div>
          </div>

          {/* Contact Us (left aligned with above) */}
          <div style={{ marginTop: "2rem", maxWidth: "1200px" }}>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.5rem" }}>Contact Us</h3>
            <p style={{ margin: 0, fontSize: "0.875rem", color: "#64748b" }}>
              For any inquiries or support, please reach out to us at <a href="mailto:support@flowdock.com" style={{ color: "#4c739a", textDecoration: "underline" }}>support@flowdock.com</a> or call us at 01132356656.
            </p>
          </div>
        </div>
      </section>

      {/* Legal Links Section (separate) */}
      <div
        style={{
          backgroundColor: "transparent",
          padding: "0.75rem",
          borderTop: "1px solid #e7edf3",
          textAlign: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
          }}
        >
          <button
            type="button"
            onClick={() => setLegalModal("privacy")}
            style={{
              background: "none",
              border: "none",
              color: "#4c739a",
              textDecoration: "underline",
              cursor: "pointer",
              padding: 0,
              fontSize: "0.75rem",
            }}
          >
            Privacy Policy
          </button>
          <span style={{ margin: "0 0.25rem" }}>•</span>
          <button
            type="button"
            onClick={() => setLegalModal("terms")}
            style={{
              background: "none",
              border: "none",
              color: "#4c739a",
              textDecoration: "underline",
              cursor: "pointer",
              padding: 0,
              fontSize: "0.75rem",
            }}
          >
            Terms of Service
          </button>
        </div>
      </div>

      {/* Footer */}
      <Footer />

      {/* Legal Modal */}
      <LegalModal
        type={legalModal}
        isOpen={legalModal !== null}
        onClose={() => setLegalModal(null)}
      />
    </div>
  );
}
