import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Plus,
  ArrowUpDown,
  Filter,
  List,
  Grid,
} from "lucide-react";
import DashboardIcon from "../../resources/icons/dashboard.svg";
import MyFilesIcon from "../../resources/icons/my_files.svg";
import SharedIcon from "../../resources/icons/shared.svg";
import TrashIcon from "../../resources/icons/trash.svg";
import SettingsIcon from "../../resources/icons/settings.svg";
import { useAuthContext } from "../../context/AuthContext";
import useFileOperations from "../../hooks/useFileOperations";
import TopNavBar from "../../layout/TopNavBar";

// Sample files with consistent 1 decimal sizes
const SAMPLE_FILES = [
  { id: 1, filename: "Document 1", uploaded_at: "2025-08-15", size: 2621440, type: "PDF" },
  { id: 2, filename: "Image 1", uploaded_at: "2025-08-10", size: 1258291, type: "JPG" },
  { id: 3, filename: "Spreadsheet 1", uploaded_at: "2025-08-05", size: 3250176, type: "XLSX" },
  { id: 4, filename: "Presentation 1", uploaded_at: "2025-07-20", size: 6082560, type: "PPTX" },
  { id: 5, filename: "Video 1", uploaded_at: "2025-07-10", size: 15925248, type: "MP4" },
];

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuthContext();
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
  const folderInputRef = useRef(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");
  const [filterType, setFilterType] = useState(null);
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  let displayFiles = files.length > 0 ? files : SAMPLE_FILES;

  // Apply sorting
  displayFiles = [...displayFiles].sort((a, b) => {
    const comparison = a.filename.localeCompare(b.filename);
    return sortOrder === "asc" ? comparison : -comparison;
  });

  // Apply filtering
  if (filterType) {
    displayFiles = displayFiles.filter((f) => f.type === filterType);
  }
  // Apply search (only when user presses Enter)
  if (appliedSearch && appliedSearch.length > 0) {
    const q = appliedSearch.toLowerCase();
    displayFiles = displayFiles.filter((f) => (f.filename || "").toLowerCase().includes(q));
  }

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login", { replace: true });
      return;
    }
    if (user?.id) {
      loadFiles();
    }
  }, [user, isAuthenticated, navigate]);

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
      await loadFiles();
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
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
      await loadFiles();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleUploadFolderClick = () => {
    folderInputRef.current?.click();
  };

  const handleFolderSelect = async (e) => {
    const folderFiles = e.target.files;
    if (!folderFiles?.length || !user?.id) return;
    try {
      for (let file of folderFiles) {
        await uploadFile(user.id, file);
      }
      await loadFiles();
    } catch (err) {
      console.error("Folder upload failed:", err);
    } finally {
      if (folderInputRef.current) folderInputRef.current.value = "";
    }
  };

  const handleSort = () => {
    setSortOrder(sortOrder === "asc" ? "desc" : "asc");
  };

  const handleFilterToggle = () => {
    setShowFilterMenu(!showFilterMenu);
  };

  const handleFilterSelect = (type) => {
    setFilterType(filterType === type ? null : type);
    setShowFilterMenu(false);
  };

  const fileTypes = [...new Set(SAMPLE_FILES.map((f) => f.type))];

  return (
    <TopNavBar>
      {/* force CSS for upload buttons / alignment */}
      <style>{`
        .force-upload-btn{
          background-color: #2563eb !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: 8px !important;
          padding: 0.55rem 1.25rem !important;
          display: inline-flex !important;
          align-items: center !important;
          gap: 0.5rem !important;
          font-size: 0.98rem !important;
          font-weight: 500 !important;
          cursor: pointer !important;
        }
        .controls-wrapper {
          width: 90%;
          max-width: 90%;
          margin-left: 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .search-wrapper {
          width: 90%;
          max-width: 90%;
          margin-left: 0;
        }

        /* ensure table aligns with search/controls width */
        .content-width { width: 90%; max-width: 90%; margin-left: 0; }

        /* table container and inner spacing */
        .files-table { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
        /* remove top padding so header is at top; keep left/right/bottom padding for gap */
        .files-table > .table-inner { padding: 0 0.5rem 0.5rem 0.5rem; }

        /* header and row separators */
        .files-table thead tr { border-bottom: 1px solid #e5e7eb; }
        .files-table tbody tr { border-bottom: 1px solid #e5e7eb; }

        /* cell padding */
        .files-table th, .files-table td { padding-left: 1rem; padding-right: 1rem; }
        /* move header text a bit down and align left to match rows */
        .files-table thead th { padding-top: 0.45rem; padding-bottom: 0.6rem; text-align: left; vertical-align: middle; }

        .files-table th:last-child, .files-table td:last-child { border-right: none; } 

        .col-muted { color: #64748b; } /* gray for Date/Size/Type cells */

        /* make the actual table stretch to the wrapper width */
        .files-table .table-inner table { width: 100%; }
      `}</style>

      <aside 
        className="flex flex-col bg-white flex-shrink-0"
        style={{ 
          width: "calc(100vw * 5 / 17 * 0.75 * 0.85)",
          backgroundColor: "#ffffff",
          paddingLeft: "1cm",
          paddingRight: "1.5rem",
          paddingTop: "1.5rem",
          paddingBottom: "1.5rem",
        }}
      >
        <nav className="flex-1 space-y-0">
          {navItems.map((item, idx) => (
            <button
              key={idx}
              onClick={() => navigate(item.to)}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-start",
                width: "100%",
                gap: "0.3cm",
                height: "2rem",
                fontSize: "0.875rem",
                padding: "0.5rem 0.8rem",
                borderRadius: "0.5rem",
                outline: "none",
                border: "none",
                backgroundColor: idx === 0 ? "#e2e8f0" : "transparent",
                color: idx === 0 ? "#0f172a" : "#64748b",
                fontWeight: idx === 0 ? "500" : "400",
                transition: "all 0.2s ease",
                cursor: "pointer",
                marginBottom: idx < navItems.length - 1 ? "0.6rem" : "0",
              }}
            >
              <img 
                src={item.icon} 
                alt="" 
                style={{ 
                  width: "1.1rem", 
                  height: "1.1rem", 
                  flexShrink: 0,
                }} 
              />
              <span style={{ fontSize: "0.875rem" }}>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main 
        className="flex-1 px-12 py-10 overflow-y-auto bg-white"
        style={{ /* width: "calc(100vw * 12 / 17)" */ }}
      >
        <header className="mb-12" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h1 className="text-4xl font-bold text-slate-900">Dashboard</h1>
          {/* Temporary button to preview PublicLink page design */}
          <button
            onClick={() => navigate("/share/demo-link-id")}
            style={{
              backgroundColor: "#8b5cf6",
              color: "#ffffff",
              border: "none",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              fontSize: "0.875rem",
              cursor: "pointer",
              marginRight: "3.8cm",
            }}
          >
            Preview Public Link Page
          </button>
        </header>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-3 mb-16" style={{ gap: "0.3cm", marginBottom: "0.3cm", maxWidth: "90%" }}>
          <div 
            className="rounded-lg bg-white"
            style={{ 
              backgroundColor: "#ffffff",
              border: "1px solid #d1d5db",
              borderRadius: "0.75rem",
              padding: "1.5rem"
            }}
          >
            <p className="text-slate-600 text-sm font-medium mb-3">Total used storage</p>
            <p className="text-3xl font-bold text-slate-900 mb-6">12.5 / 100 GB</p>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: "12.5%" }}></div>
            </div>
          </div>

          <div 
            className="rounded-lg bg-white"
            style={{ 
              backgroundColor: "#ffffff",
              border: "1px solid #d1d5db",
              borderRadius: "0.75rem",
              padding: "1.5rem"
            }}
          >
            <p className="text-slate-600 text-sm font-medium mb-3">Number of files/folders</p>
            <p className="text-3xl font-bold text-blue-600">247</p>
          </div>

          <div 
            className="rounded-lg bg-white"
            style={{ 
              backgroundColor: "#ffffff",
              border: "1px solid #d1d5db",
              borderRadius: "0.75rem",
              padding: "1.5rem"
            }}
          >
            <p className="text-slate-600 text-sm font-medium mb-3">Recent uploads</p>
            <p className="text-3xl font-bold text-blue-600">5</p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="search-wrapper" style={{ marginBottom: "0.3cm", display: "flex", alignItems: "center", gap: "0.25cm" }}>
          <Search className="w-5 h-5 text-slate-400 flex-shrink-0" />
          <input
            type="text"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                setAppliedSearch(searchQuery.trim());
              }
            }}
            className="flex-1 bg-slate-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 outline-none placeholder:text-slate-400"
            style={{
              border: "1px solid #e5e7eb",
              padding: "0.35rem 0.75rem",
              height: "1.4rem",
              fontSize: "1rem"
            }}
          />
        </div>

        {/* Controls (same width as search so upload buttons right edge aligns) */}
        <div className="controls-wrapper" style={{ marginBottom: "1rem" }}>
          <div className="flex items-center" style={{ gap: "0.5rem" }}>
            <button onClick={handleSort} className="transition" style={{ background: "none", border: "none", padding: "0.35rem", cursor: "pointer" }} title="Sort">
              <ArrowUpDown className="w-4 h-4" />
            </button>
            <div style={{ position: "relative" }}>
              <button onClick={handleFilterToggle} className="transition" style={{ background: "none", border: "none", padding: "0.35rem", cursor: "pointer" }} title="Filter">
                <Filter className="w-4 h-4" />
              </button>
              {showFilterMenu && (
                <div style={{ position: "absolute", top: "100%", left: 0, marginTop: 8, background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, boxShadow: "0 6px 18px rgba(15,23,42,0.08)", zIndex: 20 }}>
                  <button onClick={() => handleFilterSelect(null)} className="w-full text-left px-4 py-2 hover:bg-slate-100">All</button>
                  {fileTypes.map((type) => (
                    <button key={type} onClick={() => handleFilterSelect(type)} className={`w-full text-left px-4 py-2 hover:bg-slate-100 ${filterType === type ? "bg-blue-50 text-blue-600" : ""}`}>{type}</button>
                  ))}
                </div>
              )}
            </div>
            <button className="transition" style={{ background: "none", border: "none", padding: "0.35rem", cursor: "pointer" }}><List className="w-4 h-4" /></button>
            <button className="transition" style={{ background: "none", border: "none", padding: "0.35rem", cursor: "pointer" }}><Grid className="w-4 h-4" /></button>
          </div>

          <div className="upload-actions" style={{ display: "flex", gap: "0.6rem", justifyContent: "flex-end" }}>
            <button onClick={handleUploadClick} className="force-upload-btn" aria-label="Upload File">
              <Plus className="w-4 h-4" />
              Upload File
            </button>
            <button onClick={handleUploadFolderClick} className="force-upload-btn" aria-label="Upload Folder">
              <Plus className="w-4 h-4" />
              Upload Folder
            </button>
          </div>
        </div>

        {/* Files Heading */}
        <h2 className="text-3xl font-bold text-slate-900 mb-8">Files</h2>

        {/* Files Table */}
        <div className="files-table content-width mb-8" style={{ backgroundColor: "#ffffff" }}>
          {error && !/not\s*found/i.test(String(error)) && (
            <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-4">
              <p className="text-sm">{error}</p>
            </div>
          )}

          <div className="table-inner overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50">
                  <th className="text-sm font-semibold text-slate-700">Name</th>
                  <th className="text-sm font-semibold text-slate-700">Date</th>
                  <th className="text-sm font-semibold text-slate-700">Size</th>
                  <th className="text-sm font-semibold text-slate-700">Type</th>
                </tr>
              </thead>
              <tbody>
                {displayFiles.map((f, idx) => (
                  <tr key={f.id || idx} className="hover:bg-slate-50 transition-colors" style={{ backgroundColor: "#ffffff", height: "2.75rem", borderBottom: idx === displayFiles.length - 1 ? "none" : "1px solid #e5e7eb" }}>
                    <td className="text-sm font-medium text-slate-900">{f.filename}</td>
                    <td className="text-sm col-muted">{formatDateYYYYMMDD(f.uploaded_at)}</td>
                    <td className="text-sm col-muted">{formatFileSize(f.size)}</td>
                    <td className="text-sm col-muted">{f.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {uploadProgress > 0 && loading && (
          <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex justify-between mb-3">
              <span className="text-sm font-medium text-blue-900">Upload Progress</span>
              <span className="text-sm font-medium text-blue-700">{Math.round(uploadProgress)}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        )}
      </main>

      <input ref={fileInputRef} type="file" onChange={handleFileSelect} className="hidden" disabled={loading} />
      <input
        ref={folderInputRef}
        type="file"
        onChange={handleFolderSelect}
        className="hidden"
        disabled={loading}
        webkitdirectory="true"
        mozdirectory="true"
      />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
      `}</style>
    </TopNavBar>
  );
}

function formatFileSize(bytes) {
  if (!bytes) return "";
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (Math.round((bytes / Math.pow(k, i)) * 10) / 10) + " " + sizes[i];
}

function formatDateYYYYMMDD(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}
