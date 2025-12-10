import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/auth/Login.jsx";
import SignUp from "./pages/auth/SignUp.jsx";
import VerifyEmail from "./pages/auth/VerifyEmail.jsx";
import SignInEmail from "./pages/auth/SignInEmail.jsx";
import PasscodeCheck from "./pages/auth/PasscodeCheck.jsx";
import VerifyTOTP from "./pages/auth/VerifyTOTP.jsx";
import OAuthCallback from "./pages/auth/OAuthCallback.jsx";
import TwoFactorAuth from "./pages/auth/TwoFactorAuth.jsx";
import PassRecovery from "./pages/auth/PassRecovery.jsx";
import PassRecoveryVerify from "./pages/auth/PassRecoverVerify.jsx";
import ResetPassword from "./pages/auth/ResetPassword.jsx";
import AdminUserManagement from "./pages/AdminUserManagement.jsx";
import Dashboard from "./pages/dashboard/Dashboard.jsx";
import useAuth from "./hooks/useAuth.js";

// Simple Error Boundary to avoid blank page and show error details
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log to console — visible to developer
    console.error("Uncaught error in App:", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 32, fontFamily: "system-ui, sans-serif" }}>
          <h1 style={{ color: "#b91c1c" }}>Something went wrong</h1>
          <p>Check the browser console for details.</p>
          <details style={{ whiteSpace: "pre-wrap", marginTop: 8 }}>
            {this.state.error && String(this.state.error)}
            {"\n"}
            {this.state.errorInfo?.componentStack}
          </details>
          <button onClick={() => window.location.reload()} style={{ marginTop: 12, padding: "8px 12px" }}>
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Protected Route - checks if user is authenticated
function ProtectedRoute({ element }) {
  // rely on auth hook state (keeps single source of truth)
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return element;
}

function App() {
  useEffect(() => {
    // quick runtime check that App mounted in browser
    // Open browser console to see this message
    console.log("[App] mounted", { href: window.location.href });
  }, []);

  return (
    // Ensure Router context exists even if entry file didn't wrap
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          {/* Redirect root to login */}
          <Route path="/" element={<Navigate to="/login" />} />

          {/* Passcode check (sent from SignInEmail) */}
          <Route path="/passcode-check" element={<PasscodeCheck />} />

          {/* Simple email-only sign-in page */}
          <Route path="/signin-email" element={<SignInEmail />} />

          {/* Public pages */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/verify-totp" element={<VerifyTOTP />} />
          <Route path="/auth/callback" element={<OAuthCallback />} />

          {/* Password recovery flow */}
          <Route path="/pass-recovery" element={<PassRecovery />} />
          <Route path="/pass-recovery-verify" element={<PassRecoveryVerify />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          {/* Protected pages */}
          <Route path="/dashboard" element={<ProtectedRoute element={<Dashboard />} />} />
          <Route path="/admin/users" element={<ProtectedRoute element={<AdminUserManagement />} />} />

          {/* Two-Factor Authentication after signup */}
          <Route path="/2fa" element={<TwoFactorAuth />} />

          {/* Fallback route to avoid blank page when no route matches */}
          <Route path="*" element={<div style={{ padding: 20, textAlign: "center" }}>No route matched — app mounted</div>} />
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
