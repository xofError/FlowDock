import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Login from "./pages/auth/Login.jsx";
import SignUp from "./pages/auth/SignUp.jsx";
import VerifyEmail from "./pages/auth/VerifyEmail.jsx";
import VerifyTOTP from "./pages/auth/VerifyTOTP.jsx";
import OAuthCallback from "./pages/auth/OAuthCallback.jsx";
import TwoFactorAuth from "./pages/auth/TwoFactorAuth.jsx";
import PassRecovery from "./pages/auth/PassRecovery.jsx";
import PassRecoveryVerify from "./pages/auth/PassRecoverVerify.jsx";
import ResetPassword from "./pages/auth/ResetPassword.jsx";
import SignInEmail from "./pages/auth/SignInEmail.jsx";
import PasscodeCheck from "./pages/auth/PasscodeCheck.jsx";
import AdminUserManagement from "./pages/AdminUserManagement.jsx";
import Dashboard from "./pages/dashboard/Dashboard.jsx";
import MyFiles from "./pages/dashboard/MyFiles.jsx";
import Shared from "./pages/dashboard/Shared.jsx";
import PublicLinks from "./pages/dashboard/PublicLinks.jsx";
import Trash from "./pages/dashboard/Trash.jsx";
import Settings from "./pages/dashboard/Settings.jsx";
import PublicLink from "./pages/PublicLink.jsx";
import NotFound from "./pages/NotFound.jsx";
import Help from "./pages/Help.jsx"; // << added import
import { useAuthContext } from "./context/AuthContext.jsx";

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

// Protected Route - checks if user is authenticated via context
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthContext();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  const { isAuthenticated } = useAuthContext();

  useEffect(() => {
    // quick runtime check that App mounted in browser
    // Open browser console to see this message
    console.log("[App] mounted", { href: window.location.href });
  }, []);

  return (
    <ErrorBoundary>
      <Routes>
        {/* Home page (public) */}
        <Route path="/" element={<Home />} />

        {/* Public pages (redirect to dashboard if already authenticated) */}
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/signup" element={isAuthenticated ? <Navigate to="/dashboard" /> : <SignUp />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/verify-totp" element={<VerifyTOTP />} />
        <Route path="/auth/callback" element={<OAuthCallback />} />

        {/* Passcode/Magic link sign-in flow */}
        <Route path="/sign-in-email" element={<SignInEmail />} />
        <Route path="/passcode-check" element={<PasscodeCheck />} />

        {/* Password recovery flow */}
        <Route path="/pass-recovery" element={<PassRecovery />} />
        <Route path="/pass-recovery-verify" element={<PassRecoveryVerify />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Help page used by TopNavBar */}
        <Route path="/help" element={<Help />} />

        {/* Protected pages */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/my-files" element={<ProtectedRoute><MyFiles /></ProtectedRoute>} />
        <Route path="/shared" element={<ProtectedRoute><Shared /></ProtectedRoute>} />
        <Route path="/public-links" element={<ProtectedRoute><PublicLinks /></ProtectedRoute>} />
        <Route path="/trash" element={<ProtectedRoute><Trash /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute><AdminUserManagement /></ProtectedRoute>} />

        {/* Two-Factor Authentication after signup */}
        <Route path="/2fa" element={<TwoFactorAuth />} />

        {/* Public link sharing (no auth required) */}
        <Route path="/s/:token/access" element={<PublicLink />} />

        {/* 404 Not Found - must be last */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
