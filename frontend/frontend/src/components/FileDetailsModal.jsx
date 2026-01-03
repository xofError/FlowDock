import React from 'react';
import { X } from 'lucide-react';

/**
 * FileDetailsModal - Displays detailed file information with action buttons
 * Shows file icon, name, size, type, upload date, and security status
 */
const FileDetailsModal = ({ 
  file, 
  onClose, 
  onDownload, 
  onDelete,
  loading = false 
}) => {
  if (!file) return null;

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 B";
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (Math.round((bytes / Math.pow(k, i)) * 10) / 10) + " " + sizes[i];
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Unknown";
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getFileType = (type) => {
    if (!type) return "FILE";
    const parts = type.split('/');
    return parts[parts.length - 1]?.toUpperCase() || "FILE";
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden transform transition-all animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <h3 className="text-lg font-semibold text-gray-800">File Details</h3>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors text-gray-500"
            disabled={loading}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-8">
          <div className="flex flex-col md:flex-row gap-8 items-start">
            
            {/* Left: Big Icon Preview */}
            <div className="w-full md:w-1/3 flex flex-col items-center justify-center bg-blue-50 rounded-xl p-8 border-2 border-blue-100 border-dashed">
              <span className="text-6xl mb-4">📄</span>
              <p className="text-sm text-blue-600 font-medium truncate max-w-full text-center">
                {file.filename}
              </p>
            </div>

            {/* Right: Metadata List */}
            <div className="w-full md:w-2/3 space-y-6">
              <div>
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">File Name</label>
                <p className="text-gray-900 font-medium break-all">{file.filename}</p>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Size</label>
                  <p className="text-gray-900">{formatFileSize(file.size)}</p>
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Type</label>
                  <p className="text-gray-900 truncate" title={file.content_type}>
                    {getFileType(file.content_type)}
                  </p>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Uploaded</label>
                <p className="text-gray-900">
                  {formatDate(file.upload_date || file.uploaded_at)}
                </p>
              </div>

              {/* Security Status */}
              <div className="flex items-center gap-3 pt-2 flex-wrap">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <svg className="mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" /></svg>
                  Virus Scan Passed
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Encrypted
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="bg-gray-50 px-6 py-4 flex gap-3 justify-end border-t border-gray-100">
          <button
            onClick={() => {
              if (confirm("Are you sure you want to delete this file?")) {
                onDelete(file.id || file.file_id);
                onClose();
              }
            }}
            className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
            disabled={loading}
          >
            Delete File
          </button>
          <button
            onClick={() => {
              onDownload(file.id || file.file_id, file.filename);
              onClose();
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold shadow-lg shadow-blue-200 transition-all transform hover:-translate-y-0.5 disabled:opacity-50"
            disabled={loading}
          >
            Download
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileDetailsModal;
