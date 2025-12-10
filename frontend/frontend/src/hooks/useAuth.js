/**
 * useAuth - Custom React hook for authentication
 * Manages login, logout, user state, and JWT tokens
 */

import { useState, useCallback, useEffect } from "react";
import api from "../services/api";

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    
    if (token) {
      setIsAuthenticated(true);
      // Don't auto-load user data on mount to avoid unnecessary API calls
    }
  }, []);

  const loadUser = useCallback(async (userId = null) => {
    try {
      const id = userId || localStorage.getItem("user_id");
      if (!id) {
        console.warn("No user ID available to load user data");
        return;
      }
      
      const userData = await api.getCurrentUser(id);
      setUser(userData);
    } catch (err) {
      console.error("Failed to load user", err);
      setError(err.message);
    }
  }, []);

  const login = useCallback(async (email, password, totpCode = null) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.login(email, password, totpCode);

      // If TOTP is required, don't store tokens - just return the response
      if (response.totp_required || !response.access_token) {
        return response;
      }

      // Store tokens only if login is successful (not TOTP required)
      api.setTokens(response.access_token, response.refresh_token);

      // Store user ID for later use
      localStorage.setItem("user_id", response.user_id);

      // Set authenticated state
      setIsAuthenticated(true);

      // Wrap user profile fetch in try-catch so login succeeds even if it fails
      try {
        const userData = await api.getCurrentUser(response.user_id);
        setUser(userData);
      } catch (profileErr) {
        console.warn("Could not load user profile immediately:", profileErr);
        // We do NOT throw here. Login succeeds even if profile load fails.
      }

      return response;
    } catch (err) {
      const errorMessage = err.message || "Login failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (email, fullName, password) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.register(email, fullName, password);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Registration failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyEmail = useCallback(async (email, token) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.verifyEmail(email, token);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Email verification failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const requestPasswordReset = useCallback(async (email) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.requestPasswordReset(email);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Password reset request failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const resetPassword = useCallback(async (email, token, newPassword) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.resetPassword(email, token, newPassword);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Password reset failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);

    try {
      await api.logout();
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem("user_id");
    } catch (err) {
      console.error("Logout error", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const setupTOTP = useCallback(async (email) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.setupTOTP(email);
      return response;
    } catch (err) {
      const errorMessage = err.message || "TOTP setup failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyTOTP = useCallback(async (email, code, totpSecret) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.verifyTOTP(email, code, totpSecret);
      return response;
    } catch (err) {
      const errorMessage = err.message || "TOTP verification failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const generatePasscode = useCallback(async (email) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.generatePasscode(email);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Failed to generate passcode";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const verifyPasscode = useCallback(async (email, code) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.verifyPasscode(email, code);
      
      // If response has tokens, set them and store user ID
      if (response.access_token) {
        api.setTokens(response.access_token, response.refresh_token);
        if (response.user_id) {
          localStorage.setItem("user_id", response.user_id);
        }
      }
      
      setIsAuthenticated(true);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Passcode verification failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const handleOAuthCallback = useCallback(async (accessToken, userId) => {
    try {
      // Store tokens in API and localStorage
      api.setTokens(accessToken, null); // refresh token is in HttpOnly cookie
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("user_id", userId);
      
      // Set authenticated state
      setIsAuthenticated(true);
      
      // Load user data
      const userData = await api.getCurrentUser(userId);
      setUser(userData);
      
      return userData;
    } catch (err) {
      const errorMessage = err.message || "OAuth setup failed";
      setError(errorMessage);
      throw err;
    }
  }, []);

  return {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    verifyEmail,
    requestPasswordReset,
    resetPassword,
    logout,
    loadUser,
    setupTOTP,
    verifyTOTP,
    generatePasscode,
    verifyPasscode,
    handleOAuthCallback,
  };
};

export default useAuth;
