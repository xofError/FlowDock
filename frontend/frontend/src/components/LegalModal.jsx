import React from "react";
import { X } from "lucide-react";

export default function LegalModal({ type, isOpen, onClose }) {
  if (!isOpen) return null;

  const privacyContent = {
    title: "Privacy Policy",
    sections: [
      {
        heading: "1. Information We Collect",
        content: "We collect information you provide directly to us, such as when you create an account, upload files, or contact us. This includes your name, email address, and file content. We also automatically collect certain information about your device and how you interact with our service."
      },
      {
        heading: "2. How We Use Your Information",
        content: "We use the information we collect to provide, maintain, and improve our services, process transactions, send you technical notices and support messages, and comply with legal obligations. We use your data to enhance security and prevent fraudulent activity."
      },
      {
        heading: "3. Data Security",
        content: "We implement industry-standard security measures to protect your information, including encryption of data in transit and at rest. However, no security system is impenetrable. We cannot guarantee absolute security of your information."
      },
      {
        heading: "4. Sharing of Information",
        content: "We do not sell, trade, or rent your personal information to third parties. We may share information with service providers who assist us in operating our website and conducting our business, subject to strict confidentiality agreements."
      },
      {
        heading: "5. Your Rights",
        content: "You have the right to access, update, or delete your personal information at any time by logging into your account or contacting us. You may also opt-out of receiving promotional communications from us."
      },
      {
        heading: "6. Cookies",
        content: "We use cookies and similar tracking technologies to enhance your experience. You can control cookie settings through your browser preferences. Some features may not function properly if cookies are disabled."
      },
      {
        heading: "7. Children's Privacy",
        content: "Our service is not intended for users under 13 years of age. We do not knowingly collect personal information from children under 13. If we become aware of such collection, we will take steps to delete such information."
      },
      {
        heading: "8. Contact Us",
        content: "If you have questions about this Privacy Policy, please contact us at privacy@flowdock.com. We will respond to your inquiry within 30 days."
      }
    ]
  };

  const termsContent = {
    title: "Terms of Service",
    sections: [
      {
        heading: "1. Acceptance of Terms",
        content: "By accessing and using FlowDock, you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service."
      },
      {
        heading: "2. Use License",
        content: "Permission is granted to temporarily download one copy of the materials (information or software) on FlowDock for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not: modify or copy the materials; use the materials for any commercial purpose or for any public display."
      },
      {
        heading: "3. Disclaimer",
        content: "The materials on FlowDock are provided on an 'as is' basis. FlowDock makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights."
      },
      {
        heading: "4. Limitations",
        content: "In no event shall FlowDock or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on FlowDock."
      },
      {
        heading: "5. Accuracy of Materials",
        content: "The materials appearing on FlowDock could include technical, typographical, or photographic errors. FlowDock does not warrant that any of the materials on its website are accurate, complete, or current. FlowDock may make changes to the materials contained on its website at any time without notice."
      },
      {
        heading: "6. User Accounts",
        content: "If you create an account on FlowDock, you are responsible for maintaining the confidentiality of your account information and password and for restricting access to your computer. You accept responsibility for all activities that occur under your account."
      },
      {
        heading: "7. Prohibited Conduct",
        content: "You agree not to access or use FlowDock for any purpose other than that for which we make the service available. The service may not be used in connection with any commercial endeavors except those specifically endorsed or approved by us."
      },
      {
        heading: "8. Termination",
        content: "FlowDock may terminate or suspend your account and access to the service immediately, without prior notice or liability, if you breach any of these Terms of Service. Upon termination, your right to use the service will immediately cease."
      },
      {
        heading: "9. Governing Law",
        content: "These terms and conditions are governed by and construed in accordance with the laws of the jurisdiction in which FlowDock operates, and you irrevocably submit to the exclusive jurisdiction of the courts in that location."
      },
      {
        heading: "10. Contact Information",
        content: "If you have any questions about these Terms of Service, please contact us at support@flowdock.com or visit our contact page."
      }
    ]
  };

  const content = type === "privacy" ? privacyContent : termsContent;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "#ffffff",
          borderRadius: "8px",
          maxWidth: "600px",
          width: "90%",
          maxHeight: "80vh",
          overflowY: "auto",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1.5rem",
            borderBottom: "1px solid #e5e7eb",
            position: "sticky",
            top: 0,
            backgroundColor: "#ffffff",
          }}
        >
          <h2 style={{ fontSize: "1.5rem", fontWeight: "600", color: "#0f172a", margin: 0 }}>
            {content.title}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: "0.5rem",
              display: "flex",
              alignItems: "center",
            }}
          >
            <X style={{ width: "1.5rem", height: "1.5rem", color: "#dc2626" }} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: "1.5rem" }}>
          {content.sections.map((section, idx) => (
            <div key={idx} style={{ marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "0.5rem" }}>
                {section.heading}
              </h3>
              <p style={{ fontSize: "0.875rem", color: "#64748b", lineHeight: "1.6", margin: 0 }}>
                {section.content}
              </p>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "1rem 1.5rem",
            borderTop: "1px solid #e5e7eb",
            display: "flex",
            justifyContent: "flex-end",
            gap: "0.5rem",
            position: "sticky",
            bottom: 0,
            backgroundColor: "#ffffff",
          }}
        >
          <button
            onClick={onClose}
            style={{
              backgroundColor: "#2563eb",
              color: "#ffffff",
              border: "none",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              fontSize: "0.875rem",
              fontWeight: "500",
              cursor: "pointer",
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
