import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/auth/Login.jsx";
import SignUp from "./pages/auth/SignUp.jsx";
import VerifyEmail from "./pages/auth/VerifyEmail.jsx";
import VerifyTOTP from "./pages/auth/VerifyTOTP.jsx";
import TwoFactorAuth from "./pages/auth/TwoFactorAuth.jsx";
import PassRecovery from "./pages/auth/PassRecovery.jsx";
import PassRecoveryVerify from "./pages/auth/PassRecoverVerify.jsx";
import ResetPassword from "./pages/auth/ResetPassword.jsx";

function App() {
  return (
    <Routes>
      {/* Redirect root to login */}
      <Route path="/" element={<Navigate to="/login" />} />

      {/* Public pages */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/verify-totp" element={<VerifyTOTP />} />

      {/* Password recovery flow */}
      <Route path="/pass-recovery" element={<PassRecovery />} />
      <Route path="/pass-recovery-verify" element={<PassRecoveryVerify />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Two-Factor Authentication after signup */}
      <Route path="/2fa" element={<TwoFactorAuth />} />
    </Routes>
  );
}

export default App;
