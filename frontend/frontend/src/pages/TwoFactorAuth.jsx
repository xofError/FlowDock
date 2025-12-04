import { QRCodeCanvas } from "qrcode.react";
import MainLayout from "../layout/MainLayout.jsx";

export default function TwoFactorAuth() {
  // This comes from your backend
  const qrLink = "otpauth://totp/MyApp:user@email.com?secret=ABC123&issuer=MyApp";

  return (
    <MainLayout>
      <div className="flex flex-col gap-4 font-custom items-center text-center">

        <h2 className="text-[#0D141B] text-2xl font-bold">
          Two-Factor Authentication
        </h2>

        <p className="text-sm text-[#4c739a] max-w-[280px] mx-auto leading-relaxed">
          Two-factor authentication (2FA) adds an extra layer of security to your account.
        </p>

        <p className="text-sm text-[#4c739a] max-w-[280px] mx-auto leading-relaxed">
          Scan the QR code below using Google Authenticator or Authy.
        </p>

        {/* QR CODE */}
        <div className="p-4 bg-white rounded-xl shadow mt-4">
          <QRCodeCanvas value={qrLink} size={180} />
        </div>

      </div>
    </MainLayout>
  );
}
