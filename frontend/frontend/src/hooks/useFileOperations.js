/**
 * useFileOperations - Custom React hook for file operations
 * Handles file uploads, downloads, sharing, and metadata
 */

import { useState, useCallback } from "react";
import api from "../services/api";

export const useFileOperations = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Upload file
   */
  const uploadFile = useCallback(async (userId, file, onProgress = null) => {
    setLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append("file", file);

      // Use XMLHttpRequest to track progress
      const xhr = new XMLHttpRequest();

      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            setUploadProgress(percentComplete);
            if (onProgress) onProgress(percentComplete);
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            setUploadProgress(100);
            resolve(response);
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`));
          }
        });

        xhr.addEventListener("error", () => {
          reject(new Error("Upload failed"));
        });

        xhr.open(
          "POST",
          `${import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001"}/media/upload/${userId}`
        );
        const token = localStorage.getItem("access_token");
        if (token) {
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        }

        xhr.send(formData);
      });
    } catch (err) {
      const errorMessage = err.message || "Upload failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  }, []);

  /**
   * Download file
   */
  const downloadFile = useCallback(async (fileId, fileName) => {
    setLoading(true);
    setError(null);

    try {
      const blob = await api.downloadFile(fileId);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName || "download";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage = err.message || "Download failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get user's files
   */
  const getUserFiles = useCallback(async (userId) => {
    setLoading(true);
    setError(null);

    try {
      const userFiles = await api.getUserFiles(userId);
      setFiles(userFiles);
      return userFiles;
    } catch (err) {
      const errorMessage = err.message || "Failed to fetch files";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Delete file
   */
  const deleteFile = useCallback(async (fileId) => {
    setLoading(true);
    setError(null);

    try {
      await api.deleteFile(fileId);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (err) {
      const errorMessage = err.message || "Delete failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Share file with user
   */
  const shareWithUser = useCallback(async (fileId, userId, permission = "view") => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.shareFileWithUser(fileId, userId, permission);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Share failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Create share link
   */
  const createShareLink = useCallback(async (fileId, expiresIn = null) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.createShareLink(fileId, expiresIn);
      return response;
    } catch (err) {
      const errorMessage = err.message || "Link creation failed";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get files shared with me
   */
  const getSharedWithMe = useCallback(async (userId) => {
    setLoading(true);
    setError(null);

    try {
      const sharedFiles = await api.getSharedWithMe(userId);
      return sharedFiles;
    } catch (err) {
      const errorMessage = err.message || "Failed to fetch shared files";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get files shared by me
   */
  const getSharedByMe = useCallback(async (userId) => {
    setLoading(true);
    setError(null);

    try {
      const sharedFiles = await api.getSharedByMe(userId);
      return sharedFiles;
    } catch (err) {
      const errorMessage = err.message || "Failed to fetch shared files";
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    files,
    loading,
    error,
    uploadProgress,
    uploadFile,
    downloadFile,
    getUserFiles,
    deleteFile,
    shareWithUser,
    createShareLink,
    getSharedWithMe,
    getSharedByMe,
  };
};

export default useFileOperations;
