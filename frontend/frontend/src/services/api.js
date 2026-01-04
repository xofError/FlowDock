/**
 * API Client for FlowDock Backend
 * Handles all HTTP requests to Auth Service and Media Service
 */

// API URLs Configuration
// ALWAYS use relative paths - let the browser make requests to the same origin
// The gateway (Nginx) will route them to the appropriate backend service
// This works for both local development and production deployments
const getApiUrls = () => {
  return {
    AUTH_API_URL: "",  // Relative paths: /auth/login, /auth/register, etc.
    MEDIA_API_URL: import.meta.env.VITE_MEDIA_API_URL || "/media",
  };
};

const { AUTH_API_URL, MEDIA_API_URL } = getApiUrls();

// Export URLs for use in other modules (like OAuth)
export { AUTH_API_URL, MEDIA_API_URL };

class APIClient {
  constructor() {
    this.authToken = localStorage.getItem("access_token");
    // Don't store refresh token - it's in HttpOnly cookie automatically
  }

  /**
   * Set authentication tokens
   */
  setTokens(accessToken, refreshToken = null) {
    this.authToken = accessToken;
    localStorage.setItem("access_token", accessToken);
    // Refresh token is in HttpOnly cookie - browser sends it automatically with credentials
  }

  /**
   * Clear authentication tokens
   */
  clearTokens() {
    this.authToken = null;
    localStorage.removeItem("access_token");
    // HttpOnly cookie will be cleared by server when refresh token expires
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

    // Include credentials for all requests (important for refresh token cookie)
    const fetchOptions = {
      ...options,
      headers,
      credentials: "include",
    };

    try {
      const response = await fetch(url, fetchOptions);

      // Handle 401 - try to refresh token
      if (response.status === 401) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          // Retry the original request with new token
          return this.request(url, options);
        } else {
          // Refresh failed, clear tokens
          this.clearTokens();
          window.location.href = "/#/login";
        }
      }

      // Handle other errors
      if (!response.ok) {
        let error = {};
        try {
          error = await response.json();
        } catch (e) {
          // Response wasn't JSON
          error = { detail: response.statusText };
        }
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Provide better error context
      let errorMsg = error.message;
      if (!errorMsg) {
        if (typeof error === 'object' && error !== null) {
          errorMsg = JSON.stringify(error);
        } else {
          errorMsg = error.toString();
        }
      }
      console.error(`API Error: ${url}`, { errorMsg, url, options });
      throw new Error(errorMsg);
    }
  }

  /**
   * Refresh access token using refresh token (in HttpOnly cookie)
   */
  async refreshAccessToken() {
    try {
      const response = await fetch(`${AUTH_API_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Browser automatically sends HttpOnly cookie
        body: JSON.stringify({}), // No need to send token - it's in the cookie
      });

      if (response.ok) {
        const data = await response.json();
        this.setTokens(data.access_token);
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
  async setupTOTP(email) {
    return this.request(`${AUTH_API_URL}/auth/totp/setup`, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  /**
   * Verify TOTP code
   * @param {string} email - User email
   * @param {string} code - 6-digit TOTP code
   * @param {string} [totpSecret] - TOTP secret (required for setup, optional for login verification)
   */
  async verifyTOTP(email, code, totpSecret) {
    const body = { email, code };
    if (totpSecret) {
      body.totp_secret = totpSecret;
    }
    return this.request(`${AUTH_API_URL}/auth/totp/verify`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  /**
   * Generate passcode for magic link sign-in
   */
  async generatePasscode(email) {
    return this.request(`${AUTH_API_URL}/auth/generate-passcode`, {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  /**
   * Verify passcode and authenticate
   */
  async verifyPasscode(email, code) {
    return this.request(`${AUTH_API_URL}/auth/verify-passcode`, {
      method: "POST",
      body: JSON.stringify({ email, code }),
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

    return fetch(`${MEDIA_API_URL}/upload/${userId}`, {
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
    const response = await fetch(`${MEDIA_API_URL}/download/${fileId}`, {
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
    return this.request(`${MEDIA_API_URL}/user/${userId}/files`, {
      method: "GET",
    });
  }

  /**
   * Get file metadata
   */
  async getFileMetadata(fileId) {
    return this.request(`${MEDIA_API_URL}/files/${fileId}/metadata`, {
      method: "GET",
    });
  }

  /**
   * Delete file
   */
  async deleteFile(fileId) {
    return this.request(`${MEDIA_API_URL}/files/${fileId}`, {
      method: "DELETE",
    });
  }

  /**
   * Share file with user by email
   */
  async shareFileWithUser(fileId, targetEmail, expiresAt = null) {
    return this.request(`${MEDIA_API_URL}/share/user`, {
      method: "POST",
      body: JSON.stringify({
        file_id: fileId,
        target_email: targetEmail,
        permission: "read",
        expires_at: expiresAt,
      }),
    });
  }

  /**
   * Share folder with user by email
   */
  async shareFolderWithUser(folderId, targetEmails, permission = "read") {
    const targets = Array.isArray(targetEmails) ? targetEmails : [targetEmails];
    return this.request(`${MEDIA_API_URL}/folders/${folderId}/share`, {
      method: "POST",
      body: JSON.stringify({
        targets,
        permission,
        cascade: true,
      }),
    });
  }

  /**
   * Revoke file share
   */
  async revokeFileShare(shareId) {
    return this.request(`${MEDIA_API_URL}/shares/${shareId}`, {
      method: "DELETE",
    });
  }

  /**
   * Create share link
   */
  async createShareLink(fileId, expiresIn = null, password = null) {
    return this.request(`${MEDIA_API_URL}/share/link`, {
      method: "POST",
      body: JSON.stringify({
        file_id: fileId,
        expires_in: expiresIn,
        password: password,
      }),
    });
  }

  /**
   * Get files shared with me
   */
  async getSharedWithMe(userId) {
    return this.request(`${MEDIA_API_URL}/users/${userId}/files/shared-with-me`, {
      method: "GET",
    });
  }

  /**
   * Get files shared by me
   */
  async getSharedByMe(userId) {
    return this.request(`${MEDIA_API_URL}/users/${userId}/files/shared-by-me`, {
      method: "GET",
    });
  }

  /**
   * Access shared link
   */
  async accessSharedLink(token) {
    return this.request(`${MEDIA_API_URL}/s/${token}/access`, {
      method: "POST",
    });
  }

  /**
   * Get public links for a user
   */
  async getUserPublicLinks(userId) {
    return this.request(`${MEDIA_API_URL}/users/${userId}/public-links`, {
      method: "GET",
    });
  }

  /**
   * Get public links for a specific file
   */
  async getFilePublicLinks(fileId) {
    return this.request(`${MEDIA_API_URL}/files/${fileId}/public-links`, {
      method: "GET",
    });
  }

  /**
   * Delete a public link
   */
  async deletePublicLink(linkId) {
    return this.request(`${MEDIA_API_URL}/share-links/${linkId}`, {
      method: "DELETE",
    });
  }

  /**
   * Download public file
   */
  async downloadPublicFile(fileId) {
    const response = await fetch(`${MEDIA_API_URL}/public-download/${fileId}`);

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    return response.blob();
  }

  // =====================================================
  // FOLDER OPERATIONS
  // =====================================================

  /**
   * Get folder contents (files and subfolders)
   */
  async getFolderContents(folderId) {
    // Get contents of a specific folder (files + subfolders)
    // folderId must be a valid MongoDB ObjectId, not null/undefined
    if (!folderId) {
      throw new Error("folderId is required for getFolderContents. Use listRootFolders() for root.");
    }
    
    return this.request(`${MEDIA_API_URL}/folders/${folderId}/contents`, {
      method: "GET",
    });
  }

  /**
   * List folders (root if parent_id omitted, or children of a parent)
   */
  async listFolders(parentId = null) {
    const url = parentId
      ? `${MEDIA_API_URL}/folders?parent_id=${parentId}`
      : `${MEDIA_API_URL}/folders`;
    
    return this.request(url, {
      method: "GET",
    });
  }

  /**
   * Create a new folder
   */
  async createFolder(name, parentId = null) {
    return this.request(`${MEDIA_API_URL}/folders`, {
      method: "POST",
      body: JSON.stringify({
        name,
        parent_id: parentId,
      }),
    });
  }

  /**
   * Delete a folder
   */
  async deleteFolder(folderId) {
    return this.request(`${MEDIA_API_URL}/folders/${folderId}`, {
      method: "DELETE",
    });
  }

  /**
   * Rename a folder
   */
  async renameFolder(folderId, newName) {
    return this.request(`${MEDIA_API_URL}/folders/${folderId}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: newName,
      }),
    });
  }

  /**
   * Get folder information
   */
  async getFolderInfo(folderId) {
    return this.request(`${MEDIA_API_URL}/folders/${folderId}`, {
      method: "GET",
    });
  }

  /**
   * Get all user content (folders and files at root level)
   */
  async getUserContent(userId) {
    return this.request(`${MEDIA_API_URL}/user/${userId}/content`, {
      method: "GET",
    });
  }
}

// Export singleton instance
export const api = new APIClient();

export default api;
