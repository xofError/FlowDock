import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import SignUp from "./pages/SignUp.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import TwoFactorAuth from "./pages/TwoFactorAuth.jsx";
import PassRecovery from "./pages/PassRecovery.jsx";
import PassRecoveryVerify from "./pages/PassRecoveryVerify.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";

function App() {
  return (
    <Routes>
      {/* Redirect root to login */}
      <Route path="/" element={<Navigate to="/login" />} />

      {/* Public pages */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<SignUp />} />
      <Route path="/verify-email" element={<VerifyEmail />} />

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
