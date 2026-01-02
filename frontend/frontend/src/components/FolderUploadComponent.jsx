/**
 * FolderUploadComponent.jsx - Folder upload with drag & drop
 * Allows users to select a folder and upload all contents maintaining structure
 */

import { useState, useRef } from "react";
import { useAuthContext } from "../../context/AuthContext";
import useFileOperations from "../../hooks/useFileOperations";

export default function FolderUploadComponent({ onUploadComplete }) {
  const { user } = useAuthContext();
  const { uploadProgress, loading } = useFileOperations();
  
  const folderInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  /**
   * Handle folder input change
   * Extract all files maintaining folder structure
   */
  const handleFolderSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // Group files by folder structure
    const structure = groupFilesByStructure(files);
    setSelectedFiles(files);
    setUploadStatus(`Ready to upload ${files.length} files`);
  };

  /**
   * Group files maintaining folder structure
   */
  const groupFilesByStructure = (files) => {
    const structure = {};
    
    files.forEach((file) => {
      // Get folder path from webkitRelativePath
      const path = file.webkitRelativePath || file.name;
      const folderName = path.split("/")[0];
      
      if (!structure[folderName]) {
        structure[folderName] = [];
      }
      structure[folderName].push(file);
    });

    return structure;
  };

  /**
   * Upload folder contents
   */
  const handleFolderUpload = async () => {
    if (!selectedFiles.length || !user?.id) return;

    setUploading(true);
    setUploadStatus("Uploading...");

    try {
      const formData = new FormData();
      
      // Add all files with their relative paths
      selectedFiles.forEach((file) => {
        formData.append("files", file, file.webkitRelativePath || file.name);
      });

      const response = await fetch(
        `${process.env.REACT_APP_API_URL || "http://localhost:8001"}/media/files/upload-folder/${user.id}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("jwt_token")}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      setUploadStatus(
        `✅ Upload complete: ${result.files_uploaded} files uploaded${
          result.failed_files > 0 ? `, ${result.failed_files} failed` : ""
        }`
      );

      // Reset
      setSelectedFiles([]);
      folderInputRef.current.value = "";

      // Notify parent
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (err) {
      setUploadStatus(`❌ Upload failed: ${err.message}`);
      console.error("Folder upload error:", err);
    } finally {
      setUploading(false);
    }
  };

  /**
   * Handle drag & drop
   */
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const items = e.dataTransfer.items;
    if (!items) return;

    const files = [];
    const promises = [];

    // Process dropped items
    const processItems = async () => {
      for (let i = 0; i < items.length; i++) {
        if (items[i].kind === "file") {
          const entry = items[i].webkitGetAsEntry();
          if (entry?.isDirectory) {
            // Recursively get all files from folder
            await getAllFilesFromFolder(entry, "", files);
          } else {
            const file = items[i].getAsFile();
            if (file) files.push(file);
          }
        }
      }
      setSelectedFiles(files);
      setUploadStatus(`Ready to upload ${files.length} files`);
    };

    processItems().catch((err) => {
      console.error("Error processing dropped items:", err);
      setUploadStatus("❌ Error processing files");
    });
  };

  /**
   * Recursively get all files from a folder entry
   */
  const getAllFilesFromFolder = async (folder, path, fileList) => {
    const reader = folder.createReader();
    const entries = await new Promise((resolve, reject) => {
      reader.readEntries(resolve, reject);
    });

    for (const entry of entries) {
      const newPath = path ? `${path}/${entry.name}` : entry.name;
      if (entry.isDirectory) {
        await getAllFilesFromFolder(entry, newPath, fileList);
      } else if (entry.isFile) {
        const file = await new Promise((resolve, reject) => {
          entry.file(resolve, reject);
        });
        // Set webkitRelativePath for structure preservation
        Object.defineProperty(file, "webkitRelativePath", {
          value: newPath,
        });
        fileList.push(file);
      }
    }
  };

  /**
   * Render file tree
   */
  const renderFileTree = () => {
    if (selectedFiles.length === 0) return null;

    const structure = groupFilesByStructure(selectedFiles);

    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-3">Files to upload:</h3>
        {Object.entries(structure).map(([folder, files]) => (
          <div key={folder} className="mb-3">
            <div className="font-medium text-blue-600">📁 {folder}</div>
            <ul className="ml-4 text-sm text-gray-700">
              {files.map((file, idx) => (
                <li key={idx} className="flex items-center gap-2">
                  <span className="text-gray-400">├</span>
                  📄 {file.name} ({formatFileSize(file.size)})
                </li>
              ))}
            </ul>
          </div>
        ))}
        <div className="mt-2 p-2 bg-blue-50 text-sm text-blue-700 rounded">
          Total: {selectedFiles.length} files ({formatFileSize(
            selectedFiles.reduce((sum, f) => sum + f.size, 0)
          )})
        </div>
      </div>
    );
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          📁 Upload Folder
        </h2>

        {/* Drag & Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
            dragActive
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 bg-gray-50"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="text-5xl mb-4">📂</div>
          <p className="text-xl font-semibold text-gray-900 mb-2">
            Drag your folder here
          </p>
          <p className="text-gray-600 mb-6">
            or click to select a folder from your computer
          </p>

          {/* Hidden Folder Input */}
          <input
            ref={folderInputRef}
            type="file"
            webkitdirectory="true"
            mozdirectory="true"
            directory=""
            onChange={handleFolderSelect}
            className="hidden"
          />

          <button
            onClick={() => folderInputRef.current?.click()}
            disabled={uploading || loading}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading || loading ? "Processing..." : "Select Folder"}
          </button>
        </div>

        {/* File Tree */}
        {renderFileTree()}

        {/* Upload Status */}
        {uploadStatus && (
          <div className="mt-4 p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">
            {uploadStatus}
          </div>
        )}

        {/* Upload Progress */}
        {uploading && uploadProgress > 0 && (
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-700">Upload Progress</span>
              <span className="text-gray-900 font-semibold">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Upload Button */}
        {selectedFiles.length > 0 && !uploading && (
          <div className="mt-6 flex gap-4">
            <button
              onClick={handleFolderUpload}
              disabled={uploading || loading}
              className="flex-1 px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition disabled:opacity-50"
            >
              ✅ Upload {selectedFiles.length} Files
            </button>
            <button
              onClick={() => {
                setSelectedFiles([]);
                folderInputRef.current.value = "";
                setUploadStatus("");
              }}
              className="px-6 py-3 bg-gray-400 text-white font-semibold rounded-lg hover:bg-gray-500 transition"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

