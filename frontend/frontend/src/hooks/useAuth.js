/**
 * useAuth - Custom React hook for authentication
 * Manages login, logout, user state, and JWT tokens
 */

import { useState, useCallback, useEffect } from "react";
import api from "../services/api";

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Start as true to block rendering
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("access_token");
        console.log(`[useAuth] Checking auth on mount, token present: ${!!token}`);
        
        if (token) {
          console.log(`[useAuth] Token found, setting isAuthenticated = true`);
          setIsAuthenticated(true);
          // Optionally load user data if needed
          const userId = localStorage.getItem("user_id");
          if (userId) {
            try {
              const userData = await api.getCurrentUser(userId);
              // Ensure user object has id field
              if (userData && !userData.id) {
                userData.id = userId;
              }
              console.log(`[useAuth] Loaded user data on mount:`, userData);
              setUser(userData);
            } catch (err) {
              console.warn("[useAuth] Could not load user profile:", err);
              // Fallback: create minimal user object with ID from localStorage
              setUser({ id: userId });
            }
          }
        } else {
          console.log(`[useAuth] No token found, setting isAuthenticated = false`);
          setIsAuthenticated(false);
        }
      } catch (err) {
        console.error("[useAuth] Auth check failed:", err);
        setIsAuthenticated(false);
      } finally {
        console.log(`[useAuth] Auth check complete`);
        setLoading(false); // Auth check is complete
      }
    };

    checkAuth();
  }, []);

  const loadUser = useCallback(async (userId = null) => {
    try {
      const id = userId || localStorage.getItem("user_id");
      if (!id) {
        console.warn("No user ID available to load user data");
        return;
      }
      
      const userData = await api.getCurrentUser(id);
      // Ensure user object has id field
      if (userData && !userData.id) {
        userData.id = id;
      }
      setUser(userData);
    } catch (err) {
      console.error("Failed to load user", err);
      setError(err.message);
      // Fallback: create minimal user object with ID
      const id = userId || localStorage.getItem("user_id");
      if (id) {
        setUser({ id });
      }
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const userId = localStorage.getItem("user_id");
    if (userId) {
      await loadUser(userId);
    }
  }, [loadUser]);

  const login = useCallback(async (email, password, totpCode = null) => {
    setLoading(true);
    setError(null);

    try {
      console.log(`[useAuth] Logging in ${email} with TOTP: ${!!totpCode}`);
      const response = await api.login(email, password, totpCode);
      
      console.log(`[useAuth] Login API response:`, response);

      // If TOTP is required, don't store tokens - just return the response
      if (response.totp_required || !response.access_token) {
        console.log(`[useAuth] TOTP required or no access_token, returning response without storing tokens`);
        return response;
      }

      // Store tokens only if login is successful (not TOTP required)
      console.log(`[useAuth] Storing tokens for ${email}`);
      api.setTokens(response.access_token, response.refresh_token);

      // Store user ID for later use
      localStorage.setItem("user_id", response.user_id);

      // Set authenticated state
      console.log(`[useAuth] Setting isAuthenticated to true`);
      setIsAuthenticated(true);

      // Wrap user profile fetch in try-catch so login succeeds even if it fails
      try {
        console.log(`[useAuth] Fetching user profile for ${response.user_id}`);
        const userData = await api.getCurrentUser(response.user_id);
        console.log(`[useAuth] User profile loaded:`, userData);
        // Ensure user object has id field
        if (userData && !userData.id) {
          userData.id = response.user_id;
        }
        setUser(userData);
      } catch (profileErr) {
        console.warn("[useAuth] Could not load user profile immediately:", profileErr);
        // Fallback: create minimal user object with ID from response
        setUser({ id: response.user_id });
      }

      console.log(`[useAuth] Login complete for ${email}`);
      return response;
    } catch (err) {
      console.error(`[useAuth] Login error:`, err);
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
    refreshUser,
    setupTOTP,
    verifyTOTP,
    generatePasscode,
    verifyPasscode,
    handleOAuthCallback,
  };
};

export default useAuth;
