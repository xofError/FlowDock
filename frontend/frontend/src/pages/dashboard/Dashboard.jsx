/**
 * Dashboard.jsx - Example Dashboard component
 * Shows how to use useFileOperations and useAuth hooks
 */

import { useEffect, useRef } from "react";
import { useAuthContext } from "../../context/AuthContext";
import useFileOperations from "../../hooks/useFileOperations";
import MainLayout from "../../layout/MainLayout";

export default function Dashboard() {
  const { user, logout } = useAuthContext();
  const {
    files,
    loading,
    error,
    uploadProgress,
    uploadFile,
    downloadFile,
    getUserFiles,
    deleteFile,
  } = useFileOperations();

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user?.id) {
      loadFiles();
    }
  }, [user]);

  const loadFiles = async () => {
    try {
      await getUserFiles(user.id);
    } catch (err) {
      console.error("Failed to load files:", err);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !user?.id) return;

    try {
      await uploadFile(user.id, file);
      await loadFiles(); // Refresh list
    } catch (err) {
      console.error("Upload failed:", err);
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDownload = async (fileId, fileName) => {
    try {
      await downloadFile(fileId, fileName);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  const handleDelete = async (fileId) => {
    if (!confirm("Are you sure you want to delete this file?")) return;

    try {
      await deleteFile(fileId);
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <MainLayout>
      <div className="min-h-screen bg-gray-50 p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome, {user?.full_name || "User"}!
            </h1>
            <p className="text-gray-600 mt-2">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            Logout
          </button>
        </div>

        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Upload File</h2>

          <button
            onClick={handleUploadClick}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? "Uploading..." : "Choose File"}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            disabled={loading}
          />

          {loading && uploadProgress > 0 && (
            <div className="mt-4">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Upload Progress</span>
                <span className="text-sm text-gray-600">{Math.round(uploadProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Files List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Your Files</h2>
          </div>

          {loading && files.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-600">
              <p>Loading files...</p>
            </div>
          ) : files.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-600">
              <p>No files uploaded yet. Start by uploading your first file!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      File Name
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Uploaded
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-medium text-gray-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file) => (
                    <tr key={file.id} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{file.filename}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {formatFileSize(file.size)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(file.uploaded_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleDownload(file.id, file.filename)}
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            Download
                          </button>
                          <button
                            onClick={() => handleDelete(file.id)}
                            className="text-red-600 hover:text-red-800 font-medium"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}

/**
 * Format bytes to human-readable file size
 */
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}
