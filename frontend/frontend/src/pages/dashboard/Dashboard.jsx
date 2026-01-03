import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Plus,
  ArrowUpDown,
  Filter,
  List,
  Grid,
  ChevronRight,
} from "lucide-react";
import DashboardIcon from "../../resources/icons/dashboard.svg";
import MyFilesIcon from "../../resources/icons/my_files.svg";
import SharedIcon from "../../resources/icons/shared.svg";
import TrashIcon from "../../resources/icons/trash.svg";
import SettingsIcon from "../../resources/icons/settings.svg";
import { useAuthContext } from "../../context/AuthContext";
import useFileOperations from "../../hooks/useFileOperations";
import TopNavBar from "../../layout/TopNavBar";
import FileDetailsModal from "../../components/FileDetailsModal";
import api from "../../services/api";

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, isAuthenticated, loading: authLoading } = useAuthContext();
  const {
    uploadProgress,
    uploadFile,
    downloadFile,
    deleteFile,
  } = useFileOperations();

  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  
  // Folder navigation state
  const [currentFolderId, setCurrentFolderId] = useState(null);
  const [folders, setFolders] = useState([]);
  const [currentFiles, setCurrentFiles] = useState([]); 
  const [folderLoading, setFolderLoading] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState([]);
  
  // UI state
  const [viewMode, setViewMode] = useState("list"); 
  const [sortOrder, setSortOrder] = useState("asc");
  const [filterType, setFilterType] = useState(null);
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showItemMenu, setShowItemMenu] = useState(null);
  const [showFileModal, setShowFileModal] = useState(false);
  const [error] = useState(null);
  
  // Storage quota (mock)
  const [storageUsed] = useState(12.5);
  const [storageTotal] = useState(100);

  // Combine for display
  const displayItems = [...folders, ...currentFiles];

  // Sorting
  let sortedItems = [...displayItems].sort((a, b) => {
    const aName = (a.name || a.filename || "").toLowerCase();
    const bName = (b.name || b.filename || "").toLowerCase();
    const comparison = aName.localeCompare(bName);
    return sortOrder === "asc" ? comparison : -comparison;
  });

  // Filtering
  if (filterType) {
    sortedItems = sortedItems.filter((item) => {
      if (item.type === "folder") return false;
      return item.type === filterType;
    });
  }

  // Calculate unique file types for filter menu
  const fileTypes = [...new Set(currentFiles.map((f) => f.type))].filter(Boolean);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate("/login", { replace: true });
      return;
    }
    if (user?.id) {
      loadFolders(null); // Load root on mount
    }
  }, [authLoading, isAuthenticated, user?.id, navigate]);

  const loadFolders = async (folderId = null) => {
    try {
      setFolderLoading(true);
      let response;

      if (folderId === null) {
        // [FIX] Load ROOT content using specific user endpoint (gets root files + folders)
        response = await api.getUserContent(user.id);
        
        setFolders((response.folders || []).map(f => ({
          ...f, type: "folder", id: f._id || f.folder_id || f.id, name: f.name,
        })));
        
        setCurrentFiles((response.files || []).map(f => ({
          ...f, type: "file", id: f._id || f.file_id || f.id, filename: f.filename || f.name,
        })));
        
        setBreadcrumbs([]);
      } else {
        // Load folder contents
        response = await api.getFolderContents(folderId);
        
        setFolders((response.subfolders || []).map(f => ({
          ...f, type: "folder", id: f._id || f.folder_id || f.id, name: f.name,
        })));
        
        setCurrentFiles((response.files || []).map(f => ({
          ...f, type: "file", id: f._id || f.file_id || f.id, filename: f.filename || f.name,
        })));
        
        setBreadcrumbs(response.breadcrumbs || []);
      }
    } catch (err) {
      console.error("Failed to load content:", err);
    } finally {
      setFolderLoading(false);
    }
  };

  const handleFolderClick = (folderId) => {
    setCurrentFolderId(folderId);
    loadFolders(folderId);
    setShowItemMenu(null);
  };

  const handleBreadcrumbClick = (folderId) => {
    setCurrentFolderId(folderId);
    loadFolders(folderId);
  };

  const handleCreateFolder = async () => {
    const name = prompt("Enter folder name:");
    if (!name) return;
    try {
      await api.createFolder(name, currentFolderId);
      await loadFolders(currentFolderId);
    } catch (err) {
      alert("Failed to create folder");
    }
  };

  const handleDeleteFolder = async (folderId) => {
    if (!confirm("Delete this folder and all its contents?")) return;
    try {
      await api.deleteFolder(folderId);
      await loadFolders(currentFolderId);
    } catch (err) {
      alert("Failed to delete folder");
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !user?.id) return;
    try {
      await uploadFile(user.id, file, null, currentFolderId);
      await loadFolders(currentFolderId);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (fileId) => {
    if (!confirm("Are you sure you want to delete this file?")) return;
    try {
      await deleteFile(fileId);
      await loadFolders(currentFolderId);
      setShowFileModal(false);
      setSelectedFile(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFolderSelect = async (e) => {
    const folderFiles = e.target.files;
    if (!folderFiles?.length || !user?.id) return;
    try {
      for (let file of folderFiles) {
        await uploadFile(user.id, file, null, currentFolderId);
      }
      await loadFolders(currentFolderId);
    } finally {
      if (folderInputRef.current) folderInputRef.current.value = "";
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleUploadFolderClick = () => {
    folderInputRef.current?.click();
  };

  const handleDownload = async (fileId, fileName) => {
    try {
      await downloadFile(fileId, fileName);
    } catch (err) {
      console.error("Download failed:", err);
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
        .files-table > .table-inner { padding: 0 0.5rem 0.5rem 0.5rem; }

        /* header and row separators */
        .files-table thead tr { border-bottom: 1px solid #e5e7eb; }
        .files-table tbody tr { border-bottom: 1px solid #e5e7eb; cursor: pointer; }
        .files-table tbody tr:hover { background-color: #f1f5f9 !important; }

        /* cell padding */
        .files-table th, .files-table td { padding-left: 1rem; padding-right: 1rem; }
        .files-table thead th { padding-top: 0.45rem; padding-bottom: 0.6rem; text-align: left; vertical-align: middle; }
        .files-table th:last-child, .files-table td:last-child { border-right: none; } 

        .col-muted { color: #64748b; }

        .files-table .table-inner table { width: 100%; }

        /* Grid view styles */
        .grid-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 1.5rem;
          width: 90%;
          margin-left: 0;
        }

        .grid-item {
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 1rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
          background: white;
        }

        .grid-item:hover {
          box-shadow: 0 4px 12px rgba(15,23,42,0.08);
          transform: translateY(-2px);
        }

        .grid-item-icon {
          width: 48px;
          height: 48px;
          margin: 0 auto 0.75rem;
          font-size: 2rem;
        }

        .grid-item-name {
          font-weight: 500;
          font-size: 0.875rem;
          color: #0f172a;
          word-break: break-word;
        }

        .grid-item-meta {
          font-size: 0.75rem;
          color: #64748b;
          margin-top: 0.5rem;
        }

        /* Breadcrumb styles */
        .breadcrumb {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
          font-size: 0.875rem;
          color: #64748b;
        }

        .breadcrumb-item {
          cursor: pointer;
          color: #2563eb;
        }

        .breadcrumb-item:hover {
          text-decoration: underline;
        }
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
      >
        <header className="mb-12">
          <h1 className="text-4xl font-bold text-slate-900">Dashboard</h1>
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
            <p className="text-3xl font-bold text-slate-900 mb-6">{storageUsed} / {storageTotal} GB</p>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${(storageUsed / storageTotal) * 100}%` }}></div>
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
            <p className="text-3xl font-bold text-blue-600">{displayItems.length}</p>
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
            <p className="text-3xl font-bold text-blue-600">{currentFiles.length}</p>
          </div>
        </div>

        {/* Breadcrumb Navigation */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <div className="breadcrumb content-width" style={{ marginBottom: "1rem" }}>
            <span 
              className="breadcrumb-item"
              onClick={() => handleBreadcrumbClick(null)}
            >
              Dashboard
            </span>
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={crumb.folder_id || idx}>
                <ChevronRight className="w-4 h-4" />
                <span 
                  className="breadcrumb-item"
                  onClick={() => handleBreadcrumbClick(crumb.folder_id)}
                >
                  {crumb.name}
                </span>
              </React.Fragment>
            ))}
          </div>
        )}

        {/* Search Bar */}
        <div className="search-wrapper" style={{ marginBottom: "0.3cm", display: "flex", alignItems: "center", gap: "0.25cm" }}>
          <Search className="w-5 h-5 text-slate-400 flex-shrink-0" />
          <input
            type="text"
            placeholder="Search"
            className="flex-1 bg-slate-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 outline-none placeholder:text-slate-400"
            style={{
              border: "1px solid #e5e7eb",
              padding: "0.35rem 0.75rem",
              height: "1.4rem",
              fontSize: "1rem"
            }}
          />
        </div>

        {/* Controls */}
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
            <button onClick={() => setViewMode("list")} className="transition" style={{ background: viewMode === "list" ? "#e5e7eb" : "none", border: "none", padding: "0.35rem", cursor: "pointer", borderRadius: "4px" }} title="List view">
              <List className="w-4 h-4" />
            </button>
            <button onClick={() => setViewMode("grid")} className="transition" style={{ background: viewMode === "grid" ? "#e5e7eb" : "none", border: "none", padding: "0.35rem", cursor: "pointer", borderRadius: "4px" }} title="Grid view">
              <Grid className="w-4 h-4" />
            </button>
          </div>

          <div className="upload-actions" style={{ display: "flex", gap: "0.6rem", justifyContent: "flex-end" }}>
            <button onClick={handleCreateFolder} className="force-upload-btn" aria-label="New Folder">
              <Plus className="w-4 h-4" />
              New Folder
            </button>
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

        {/* Contents Heading */}
        <h2 className="text-3xl font-bold text-slate-900 mb-8">Contents</h2>

        {/* List View */}
        {viewMode === "list" && (
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
                    <th className="text-sm font-semibold text-slate-700">Type</th>
                    <th className="text-sm font-semibold text-slate-700">Date</th>
                    <th className="text-sm font-semibold text-slate-700">Size</th>
                    <th className="text-sm font-semibold text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedItems.map((item, idx) => (
                    <tr 
                      key={item.id || idx} 
                      className="hover:bg-slate-50 transition-colors" 
                      onClick={() => {
                        if (item.type === "folder") {
                          handleFolderClick(item.id);
                        } else {
                          setSelectedItem(item);
                          setSelectedFile(item);
                          setShowFileModal(true);
                        }
                      }}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        setShowItemMenu(item.id === showItemMenu ? null : item.id);
                      }}
                      style={{
                        backgroundColor: selectedItem?.id === item.id ? "#f0f9ff" : "#ffffff",
                        height: "2.75rem",
                        cursor: item.type === "folder" ? "pointer" : "default",
                        position: "relative"
                      }}
                    >
                      <td className="text-sm font-medium text-slate-900">
                        {item.type === "folder" ? "📁 " : "📄 "}
                        {item.name || item.filename}
                      </td>
                      <td className="text-sm col-muted">{item.type === "folder" ? "Folder" : item.type || "File"}</td>
                      <td className="text-sm col-muted">{formatDateYYYYMMDD(item.created_at || item.uploaded_at)}</td>
                      <td className="text-sm col-muted">{item.type === "folder" ? "-" : formatFileSize(item.size)}</td>
                      <td className="text-sm" onClick={(e) => e.stopPropagation()} style={{ position: "sticky", right: 0, backgroundColor: selectedItem?.id === item.id ? "#e0f2fe" : "#ffffff", zIndex: 10 }}>
                        <div style={{ position: "relative", padding: "0.5rem" }}>
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowItemMenu(item.id === showItemMenu ? null : item.id);
                            }}
                            className="transition"
                            style={{ background: "none", border: "none", padding: "0.25rem 0.5rem", cursor: "pointer" }}
                            title="More options"
                          >
                            ⋮
                          </button>
                          {showItemMenu === item.id && (
                            <div style={{
                              position: "absolute",
                              right: 0,
                              top: "100%",
                              marginTop: 4,
                              background: "#fff",
                              border: "1px solid #e5e7eb",
                              borderRadius: 8,
                              boxShadow: "0 6px 18px rgba(15,23,42,0.08)",
                              zIndex: 9999,
                              minWidth: "120px"
                            }}>
                              {item.type === "file" && (
                                <>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDownload(item.id, item.filename);
                                      setShowItemMenu(null);
                                    }}
                                    className="w-full text-left px-4 py-2 hover:bg-slate-100 text-sm text-blue-600"
                                    style={{ border: "none", background: "none", cursor: "pointer" }}
                                  >
                                    Download
                                  </button>
                                  <div style={{ borderBottom: "1px solid #e5e7eb" }}></div>
                                </>
                              )}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (item.type === "folder") {
                                    handleDeleteFolder(item.id);
                                  } else {
                                    handleDelete(item.id);
                                  }
                                  setShowItemMenu(null);
                                }}
                                className="w-full text-left px-4 py-2 hover:bg-red-50 text-sm text-red-600"
                                style={{ border: "none", background: "none", cursor: "pointer" }}
                              >
                                Delete
                              </button>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Grid View */}
        {viewMode === "grid" && (
          <div className="grid-container" style={{ marginBottom: "2rem" }}>
            {sortedItems.map((item, idx) => (
              <div 
                key={item.id || idx}
                className="grid-item"
                onClick={() => {
                  if (item.type === "folder") {
                    handleFolderClick(item.id);
                  } else {
                    setSelectedItem(item);
                    setSelectedFile(item);
                    setShowFileModal(true);
                  }
                }}
              >
                <div className="grid-item-icon">
                  {item.type === "folder" ? "📁" : "📄"}
                </div>
                <div className="grid-item-name">{item.name || item.filename}</div>
                <div className="grid-item-meta">
                  {item.type === "folder" ? "Folder" : item.type || "File"}
                </div>
                {item.type !== "folder" && (
                  <div className="grid-item-meta">{formatFileSize(item.size)}</div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Upload Progress */}
        {uploadProgress > 0 && (
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

        {/* File Details Modal Component */}
        {showFileModal && selectedFile && (
          <FileDetailsModal
            file={selectedFile}
            onClose={() => {
              setShowFileModal(false);
              setSelectedFile(null);
            }}
            onDownload={(fileId, fileName) => {
              downloadFile(fileId, fileName);
              setShowFileModal(false);
              setSelectedFile(null);
            }}
            onDelete={(fileId) => {
              handleDelete(fileId);
              setShowFileModal(false);
              setSelectedFile(null);
            }}
            loading={folderLoading}
          />
        )}
      </main>
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
