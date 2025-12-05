/**
 * API Client for FlowDock Backend
 * Handles all HTTP requests to Auth Service and Media Service
 */

// Get API URLs from environment variables (set in docker-compose.yml)
const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL || "http://localhost:8000";
const MEDIA_API_URL = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001";

// For Traefik routing:
// const AUTH_API_URL = "http://localhost/auth";
// const MEDIA_API_URL = "http://localhost/media";

class APIClient {
  constructor() {
    this.authToken = localStorage.getItem("access_token");
    this.refreshToken = localStorage.getItem("refresh_token");
  }

  /**
   * Set authentication tokens
   */
  setTokens(accessToken, refreshToken = null) {
    this.authToken = accessToken;
    localStorage.setItem("access_token", accessToken);

    if (refreshToken) {
      this.refreshToken = refreshToken;
      localStorage.setItem("refresh_token", refreshToken);
    }
  }

  /**
   * Clear authentication tokens
   */
  clearTokens() {
    this.authToken = null;
    this.refreshToken = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  /**
   * Generic fetch wrapper with error handling
   */
  async request(url, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    // Add authorization token if available
    if (this.authToken) {
      headers["Authorization"] = `Bearer ${this.authToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 - try to refresh token
      if (response.status === 401 && this.refreshToken) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          // Retry the original request with new token
          return this.request(url, options);
        } else {
          // Refresh failed, clear tokens
          this.clearTokens();
          window.location.href = "/login";
        }
      }

      // Handle other errors
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error: ${url}`, error);
      throw error;
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken() {
    if (!this.refreshToken) return false;

    try {
      const response = await fetch(`${AUTH_API_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.setTokens(data.access_token, this.refreshToken);
        return true;
      }

      return false;
    } catch (error) {
      console.error("Token refresh failed", error);
      return false;
    }
  }

  // =====================================================
  // AUTH SERVICE ENDPOINTS
  // =====================================================

  /**
   * User Registration
   */
  async register(email, fullName, password) {
    return this.request(`${AUTH_API_URL}/auth/register`, {
      method: "POST",
      body: JSON.stringify({
        email,
        full_name: fullName,
        password,
      }),
    });
  }

  /**
   * Verify email with OTP
   */
  async verifyEmail(email, token) {
    return this.request(`${AUTH_API_URL}/auth/verify-email`, {
      method: "POST",
      body: JSON.stringify({ email, token }),
    });
  }

  /**
   * User Login
   */
  async login(email, password, totpCode = null) {
    const body = { email, password };
    if (totpCode) {
      body.totp_code = totpCode;
    }

    return this.request(`${AUTH_API_URL}/auth/login`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  /**
   * User Logout
   */
  async logout() {
    try {
      await this.request(`${AUTH_API_URL}/auth/logout`, {
        method: "POST",
      });
    } finally {
      this.clearTokens();
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email) {
    return this.request(`${AUTH_API_URL}/auth/forgot-password`, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  /**
   * Reset password with token
   */
  async resetPassword(email, token, newPassword) {
    return this.request(`${AUTH_API_URL}/auth/reset-password`, {
      method: "POST",
      body: JSON.stringify({ email, token, new_password: newPassword }),
    });
  }

  /**
   * Setup TOTP (2FA)
   */
  async setupTOTP() {
    return this.request(`${AUTH_API_URL}/auth/totp/setup`, {
      method: "POST",
    });
  }

  /**
   * Verify TOTP code
   */
  async verifyTOTP(token) {
    return this.request(`${AUTH_API_URL}/auth/totp/verify`, {
      method: "POST",
      body: JSON.stringify({ totp_code: token }),
    });
  }

  /**
   * Get current user info
   */
  async getCurrentUser(userId) {
    return this.request(`${AUTH_API_URL}/api/users/${userId}`, {
      method: "GET",
    });
  }

  /**
   * Get user by email
   */
  async getUserByEmail(email) {
    return this.request(`${AUTH_API_URL}/api/users/by-email/${email}`, {
      method: "GET",
    });
  }

  // =====================================================
  // MEDIA SERVICE ENDPOINTS
  // =====================================================

  /**
   * Upload file
   */
  async uploadFile(userId, file) {
    const formData = new FormData();
    formData.append("file", file);

    return fetch(`${MEDIA_API_URL}/media/upload/${userId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.authToken}`,
      },
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      return res.json();
    });
  }

  /**
   * Download file
   */
  async downloadFile(fileId) {
    const response = await fetch(`${MEDIA_API_URL}/media/download/${fileId}`, {
      headers: {
        Authorization: `Bearer ${this.authToken}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    return response.blob();
  }

  /**
   * Get user's files
   */
  async getUserFiles(userId) {
    return this.request(`${MEDIA_API_URL}/media/user/${userId}/files`, {
      method: "GET",
    });
  }

  /**
   * Get file metadata
   */
  async getFileMetadata(fileId) {
    return this.request(`${MEDIA_API_URL}/media/files/${fileId}/metadata`, {
      method: "GET",
    });
  }

  /**
   * Delete file
   */
  async deleteFile(fileId) {
    return this.request(`${MEDIA_API_URL}/media/files/${fileId}`, {
      method: "DELETE",
    });
  }

  /**
   * Share file with user
   */
  async shareFileWithUser(fileId, targetUserId, permission = "view") {
    return this.request(`${MEDIA_API_URL}/media/share/user`, {
      method: "POST",
      body: JSON.stringify({
        file_id: fileId,
        target_user_id: targetUserId,
        permission,
      }),
    });
  }

  /**
   * Create share link
   */
  async createShareLink(fileId, expiresIn = null) {
    return this.request(`${MEDIA_API_URL}/media/share/link`, {
      method: "POST",
      body: JSON.stringify({
        file_id: fileId,
        expires_in: expiresIn,
      }),
    });
  }

  /**
   * Get files shared with me
   */
  async getSharedWithMe(userId) {
    return this.request(`${MEDIA_API_URL}/media/users/${userId}/files/shared-with-me`, {
      method: "GET",
    });
  }

  /**
   * Get files shared by me
   */
  async getSharedByMe(userId) {
    return this.request(`${MEDIA_API_URL}/media/users/${userId}/files/shared-by-me`, {
      method: "GET",
    });
  }

  /**
   * Access shared link
   */
  async accessSharedLink(token) {
    return this.request(`${MEDIA_API_URL}/media/s/${token}/access`, {
      method: "POST",
    });
  }

  /**
   * Download public file
   */
  async downloadPublicFile(fileId) {
    const response = await fetch(`${MEDIA_API_URL}/media/public-download/${fileId}`);

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    return response.blob();
  }
}

// Export singleton instance
export const api = new APIClient();

export default api;
