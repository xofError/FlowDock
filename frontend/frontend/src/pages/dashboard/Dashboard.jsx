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
  X,
  Calendar,
  Link,
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
import FolderShareModal from "../../components/FolderShareModal";
import api from "../../services/api";

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: null, label: "Public Links", to: "/public-links", lucideIcon: "Link" },
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
  const [searchQuery, setSearchQuery] = useState("");
  
  // Modal states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [showCreateFolderModal, setShowCreateFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [folderNameError, setFolderNameError] = useState("");
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");
  const [alertTitle, setAlertTitle] = useState("Notice");
  const [shareFile, setShareFile] = useState(null);
  const [shareEmail, setShareEmail] = useState("");
  const [shareExpiryDate, setShareExpiryDate] = useState("");
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [generatePublicLink, setGeneratePublicLink] = useState(false);
  const [maxDownloads, setMaxDownloads] = useState("");
  const [publicLinkPassword, setPublicLinkPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [dateError, setDateError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [publicLinks, setPublicLinks] = useState([]);
  const [linksLoading, setLinksLoading] = useState(false);
  const [shareError, setShareError] = useState("");
  const [shareLoading, setShareLoading] = useState(false);
  
  // Storage quota
  const [storageUsed, setStorageUsed] = useState(0);
  const [storageTotal, setStorageTotal] = useState(100);
  const [storageLoading, setStorageLoading] = useState(false);

  // Folder sharing state
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedFolderForShare, setSelectedFolderForShare] = useState(null);

  // Combine for display
  const displayItems = [...folders, ...currentFiles];

  // Sorting
  let sortedItems = [...displayItems].sort((a, b) => {
    const aName = (a.name || a.filename || "").toLowerCase();
    const bName = (b.name || b.filename || "").toLowerCase();
    const comparison = aName.localeCompare(bName);
    return sortOrder === "asc" ? comparison : -comparison;
  });

  // Filtering by type
  if (filterType) {
    sortedItems = sortedItems.filter((item) => {
      if (item.type === "folder") return false;
      return item.type === filterType;
    });
  }

  // Filtering by search query
  if (searchQuery.trim()) {
    const query = searchQuery.toLowerCase();
    sortedItems = sortedItems.filter((item) => {
      const name = (item.name || item.filename || "").toLowerCase();
      return name.includes(query);
    });
  }

  // Calculate unique file types for filter menu
  const fileTypes = [...new Set(currentFiles.map((f) => f.type))].filter(Boolean);

  useEffect(() => {
    console.log(`[Dashboard] Auth loading: ${authLoading}, isAuthenticated: ${isAuthenticated}, user: ${user?.id}`);
    if (authLoading) {
      console.log(`[Dashboard] Still loading auth`);
      return;
    }
    if (!isAuthenticated) {
      console.log(`[Dashboard] Not authenticated, redirecting to login`);
      navigate("/login", { replace: true });
      return;
    }
    console.log(`[Dashboard] Authenticated as ${user?.id}, loading folders and storage`);
    if (user?.id) {
      loadFolders(null); // Load root on mount
      loadUserStorage(user.id); // Fetch user storage
    }
  }, [authLoading, isAuthenticated, user?.id, navigate]);

  const loadUserStorage = async (userId) => {
    try {
      setStorageLoading(true);
      const userData = await api.getCurrentUser(userId);
      // Convert bytes to GB
      const usedGB = userData.storage_used ? (userData.storage_used / (1024 * 1024 * 1024)).toFixed(2) : 0;
      const limitGB = userData.storage_limit ? (userData.storage_limit / (1024 * 1024 * 1024)).toFixed(2) : 100;
      setStorageUsed(parseFloat(usedGB));
      setStorageTotal(parseFloat(limitGB));
    } catch (err) {
      console.error("Failed to load user storage:", err);
      // Keep default values if API fails
    } finally {
      setStorageLoading(false);
    }
  };

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
    setShowCreateFolderModal(true);
    setNewFolderName("");
    setFolderNameError("");
  };

  const handleConfirmCreateFolder = async () => {
    if (!newFolderName.trim()) {
      setFolderNameError("Folder name cannot be empty");
      return;
    }
    try {
      await api.createFolder(newFolderName.trim(), currentFolderId);
      await loadFolders(currentFolderId);
      setShowCreateFolderModal(false);
      setNewFolderName("");
    } catch (err) {
      setFolderNameError("Failed to create folder: " + err.message);
    }
  };

  const handleDeleteFolder = async (folderId) => {
    setDeleteTarget({ id: folderId, type: "folder" });
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.type === "folder") {
        await api.deleteFolder(deleteTarget.id);
      } else {
        await api.deleteFile(deleteTarget.id);
      }
      await loadFolders(currentFolderId);
      setShowDeleteModal(false);
      setDeleteTarget(null);
      setShowFileModal(false);
      setSelectedFile(null);
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Use user.id from state, fallback to localStorage
    const userId = user?.id || localStorage.getItem("user_id");
    if (!userId) {
      console.error("User ID not available for upload");
      return;
    }
    
    try {
      await uploadFile(userId, file, null, currentFolderId);
      await loadFolders(currentFolderId);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (fileId) => {
    setDeleteTarget({ id: fileId, type: "file" });
    setShowDeleteModal(true);
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateDate = (dateStr) => {
    if (!dateStr) return false;
    const dateRegex = /^(\d{2}|\d{4})\/\d{2}\/\d{2}$/;
    if (!dateRegex.test(dateStr)) return false;
    
    const parts = dateStr.split('/');
    let year = parseInt(parts[0]);
    const month = parseInt(parts[1]);
    const day = parseInt(parts[2]);
    
    if (parts[0].length === 2) {
      year += year < 50 ? 2000 : 1900;
    }
    
    const date = new Date(year, month - 1, day);
    return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
  };

  const handleCreateShareLink = async () => {
    // If generating public link, only expiry date is needed
    if (generatePublicLink) {
      let hasError = false;
      
      // Validate date (optional for public links)
      let expirationDate = null;
      if (shareExpiryDate) {
        if (!validateDate(shareExpiryDate)) {
          setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
          hasError = true;
        } else {
          setDateError("");
          // Parse date
          const parts = shareExpiryDate.split('/');
          let year = parseInt(parts[0]);
          const month = parseInt(parts[1]);
          const day = parseInt(parts[2]);
          
          if (parts[0].length === 2) {
            year += year < 50 ? 2000 : 1900;
          }
          
          expirationDate = new Date(year, month - 1, day).toISOString();
        }
      }
      
      if (hasError) return;

      try {
        setShareLoading(true);
        
        // Call API to create public link with optional password
        const response = await api.createShareLink(shareFile.id, expirationDate, publicLinkPassword || undefined);
        
        // Build link without port - use hostname only
        const baseUrl = `${window.location.protocol}//${window.location.hostname}`;
        const linkToken = response.short_code || response.token;
        const publicLink = `${baseUrl}/#/s/${linkToken}/access`;
        
        setSuccessMessage(`✓ Public link created:\n${publicLink}`);
        // Don't auto-close - let user copy the link
        // setTimeout(() => {
        //   setShareFile(null);
        //   setSuccessMessage("");
        //   setShareEmail("");
        //   setShareExpiryDate("");
        //   setMaxDownloads("");
        //   setGeneratePublicLink(false);
        // }, 4000);
      } catch (err) {
        console.error("Public link creation failed:", err);
        setEmailError("Failed to create public link: " + (err.message || "Unknown error"));
      } finally {
        setShareLoading(false);
      }
      return;
    }
    
    // Otherwise, share with email
    let hasError = false;
    
    if (!shareEmail) {
      setEmailError("Email is required");
      hasError = true;
    } else if (!validateEmail(shareEmail)) {
      setEmailError("Please enter a valid email address");
      hasError = true;
    } else {
      setEmailError("");
    }
    
    let expirationDate = null;
    if (shareExpiryDate) {
      if (!validateDate(shareExpiryDate)) {
        setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
        hasError = true;
      } else {
        setDateError("");
        const parts = shareExpiryDate.split('/');
        let year = parseInt(parts[0]);
        const month = parseInt(parts[1]);
        const day = parseInt(parts[2]);
        
        if (parts[0].length === 2) {
          year += year < 50 ? 2000 : 1900;
        }
        
        expirationDate = new Date(year, month - 1, day).toISOString();
      }
    }
    
    if (hasError) return;

    try {
      setShareLoading(true);
      
      await api.shareFileWithUser(shareFile.id, shareEmail, expirationDate);
      
      setSuccessMessage(`✓ File shared with ${shareEmail}`);
      setTimeout(() => {
        setShareFile(null);
        setSuccessMessage("");
        setShareEmail("");
        setShareExpiryDate("");
      }, 2500);
    } catch (err) {
      console.error("Share failed:", err);
      setEmailError("Failed to share file: " + (err.message || "Unknown error"));
    } finally {
      setShareLoading(false);
    }
  };

  const handleCalendarDateSelect = (day, month, year) => {
    const dateStr = `${String(year).slice(-2)}/${String(month + 1).padStart(2, '0')}/${String(day).padStart(2, '0')}`;
    setShareExpiryDate(dateStr);
    setShowCalendar(false);
  };

  const handleShareFile = async (file) => {
    setShareFile(file);
    setShareEmail("");
    setShareExpiryDate("");
    setGeneratePublicLink(false);
    setMaxDownloads("");
    setPublicLinkPassword("");
    setEmailError("");
    setDateError("");
    setSuccessMessage("");

    // Fetch existing public links for this file
    try {
      setLinksLoading(true);
      const links = await api.getFilePublicLinks(file.id);
      // Filter out inactive (deleted) links
      const activeLinks = (links || []).filter(link => link.active !== false);
      setPublicLinks(activeLinks);
    } catch (err) {
      console.error("Failed to fetch public links:", err);
      setPublicLinks([]);
    } finally {
      setLinksLoading(false);
    }
  };

  const handleShareFolder = (folder) => {
    setSelectedFolderForShare(folder);
    setShowShareModal(true);
    setShowItemMenu(null); // Close menu
  };

  const handleDeletePublicLink = async (linkId) => {
    try {
      await api.deletePublicLink(linkId);
      // Remove the deleted link from the list
      setPublicLinks(publicLinks.filter(link => link.id !== linkId));
      setSuccessMessage("✓ Public link deleted");
      setTimeout(() => setSuccessMessage(""), 2000);
    } catch (err) {
      console.error("Failed to delete public link:", err);
      setShareError("Failed to delete link: " + (err.message || "Unknown error"));
    }
  };

  const handleFolderSelect = async (e) => {
    const folderFiles = e.target.files;
    if (!folderFiles?.length || !user?.id) return;
    try {
      const formData = new FormData();
      
      // Add all files with their relative paths to preserve folder structure
      for (let file of folderFiles) {
        const relativePath = file.webkitRelativePath || file.name;
        formData.append("files", file, relativePath);
      }

      // Upload to folder upload endpoint to preserve folder structure
      const response = await fetch(
        `${import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001"}/media/upload-folder/${user.id}${
          currentFolderId ? `?parent_folder_id=${currentFolderId}` : ""
        }`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`Folder upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      setAlertMessage(
        `✓ Upload complete: ${result.files_uploaded} files uploaded${
          result.failed_files > 0 ? `, ${result.failed_files} failed` : ""
        }`
      );
      setAlertTitle("Upload Successful");
      setShowAlertModal(true);
      
      // Reload folder contents
      await loadFolders(currentFolderId);
    } catch (err) {
      console.error("Folder upload error:", err);
      setAlertMessage(`Upload failed: ${err.message}`);
      setAlertTitle("Upload Error");
      setShowAlertModal(true);
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

  const handleDownload = async (itemId, itemName, itemType = "file") => {
    try {
      if (itemType === "folder") {
        // Download folder as ZIP
        const response = await fetch(`/media/folders/${itemId}/download`, {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`
          }
        });
        
        if (!response.ok) {
          throw new Error(`Download failed: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${itemName}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Download file
        await downloadFile(itemId, itemName);
      }
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

  const CalendarPicker = ({ onDateSelect, currentDate }) => {
    const [pickerMonth, setPickerMonth] = useState(currentDate.getMonth());
    const [pickerYear, setPickerYear] = useState(currentDate.getFullYear());

    const daysInMonth = (month, year) => new Date(year, month + 1, 0).getDate();
    const firstDay = new Date(pickerYear, pickerMonth, 1).getDay();
    const days = Array.from({ length: daysInMonth(pickerMonth, pickerYear) }, (_, i) => i + 1);
    const weeks = [];
    let currentWeek = Array(firstDay).fill(null);

    days.forEach(day => {
      currentWeek.push(day);
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    });
    if (currentWeek.length > 0) weeks.push(currentWeek);

    return (
      <div style={{
        display: "flex",
        flexDirection: "column",
        width: "100%"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <button onClick={() => setPickerMonth(m => m === 0 ? 11 : m - 1)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "14px" }}>←</button>
          <span style={{ fontSize: "14px", fontWeight: 600 }}>
            {new Date(pickerYear, pickerMonth).toLocaleString('default', { month: 'long', year: 'numeric' })}
          </span>
          <button onClick={() => setPickerMonth(m => m === 11 ? 0 : m + 1)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "14px" }}>→</button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "4px" }}>
          {["S", "M", "T", "W", "T", "F", "S"].map(day => (
            <div key={day} style={{ textAlign: "center", fontSize: "12px", fontWeight: 600, color: "#64748b" }}>{day}</div>
          ))}
          {weeks.map((week, idx) => week.map((day, dayIdx) => (
            <button
              key={`${idx}-${dayIdx}`}
              onClick={() => day && onDateSelect(day, pickerMonth, pickerYear)}
              style={{
                padding: "6px",
                border: day ? "1px solid #e5e7eb" : "none",
                borderRadius: "4px",
                background: day ? "#fff" : "transparent",
                cursor: day ? "pointer" : "default",
                fontSize: "12px",
                color: day ? "#0f172a" : "transparent"
              }}
            >
              {day}
            </button>
          )))}
        </div>
      </div>
    );
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
        .files-table { border: 1px solid #e5e7eb; border-radius: 8px; overflow: visible; }
        .files-table > .table-inner { padding: 0 0.5rem 0.5rem 0.5rem; overflow-x: auto; overflow-y: visible; }

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
              {item.lucideIcon === "Link" ? (
                <Link 
                  style={{ 
                    width: "1.1rem", 
                    height: "1.1rem", 
                    flexShrink: 0,
                    color: "#64748b"
                  }} 
                />
              ) : (
                <img 
                  src={item.icon} 
                  alt="" 
                  style={{ 
                    width: "1.1rem", 
                    height: "1.1rem", 
                    flexShrink: 0,
                  }} 
                />
              )}
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
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
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
                        position: "relative",
                        zIndex: showItemMenu === item.id ? 50 : 1
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
                        <div style={{ display: "flex", gap: "0.35rem", justifyContent: "flex-end", padding: "0.4rem 0.5rem", alignItems: "center" }}>
                          {item.type === "folder" ? (
                            // Folder actions
                            <>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleShareFolder(item);
                                }}
                                style={{
                                  background: "#8b5cf6",
                                  color: "white",
                                  border: "none",
                                  padding: "0.4rem 0.65rem",
                                  borderRadius: "4px",
                                  cursor: "pointer",
                                  fontSize: "0.7rem",
                                  fontWeight: "500",
                                  transition: "all 0.2s",
                                  whiteSpace: "nowrap"
                                }}
                                onMouseEnter={(e) => e.target.style.background = "#7c3aed"}
                                onMouseLeave={(e) => e.target.style.background = "#8b5cf6"}
                                title="Share folder"
                              >
                                ⇄
                              </button>
                            </>
                          ) : (
                            // File actions
                            <>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDownload(item.id, item.filename || item.name, item.type);
                                }}
                                style={{
                                  background: "#3b82f6",
                                  color: "white",
                                  border: "none",
                                  padding: "0.4rem 0.65rem",
                                  borderRadius: "4px",
                                  cursor: "pointer",
                                  fontSize: "0.7rem",
                                  fontWeight: "500",
                                  transition: "all 0.2s",
                                  whiteSpace: "nowrap"
                                }}
                                onMouseEnter={(e) => e.target.style.background = "#2563eb"}
                                onMouseLeave={(e) => e.target.style.background = "#3b82f6"}
                                title="Download file"
                              >
                                ↓
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleShareFile(item);
                                }}
                                style={{
                                  background: "#8b5cf6",
                                  color: "white",
                                  border: "none",
                                  padding: "0.4rem 0.65rem",
                                  borderRadius: "4px",
                                  cursor: "pointer",
                                  fontSize: "0.7rem",
                                  fontWeight: "500",
                                  transition: "all 0.2s",
                                  whiteSpace: "nowrap"
                                }}
                                onMouseEnter={(e) => e.target.style.background = "#7c3aed"}
                                onMouseLeave={(e) => e.target.style.background = "#8b5cf6"}
                                title="Share file"
                              >
                                ⇄
                              </button>
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
                            }}
                            style={{
                              background: "#ef4444",
                              color: "white",
                              border: "none",
                              padding: "0.4rem 0.65rem",
                              borderRadius: "4px",
                              cursor: "pointer",
                              fontSize: "0.7rem",
                              fontWeight: "500",
                              transition: "all 0.2s",
                              whiteSpace: "nowrap"
                            }}
                            onMouseEnter={(e) => e.target.style.background = "#dc2626"}
                            onMouseLeave={(e) => e.target.style.background = "#ef4444"}
                            title={item.type === "folder" ? "Delete folder" : "Delete file"}
                          >
                            ✕
                          </button>
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
                style={{ position: "relative", paddingBottom: "2.5rem" }}
              >
                <div
                  onClick={() => {
                    if (item.type === "folder") {
                      handleFolderClick(item.id);
                    } else {
                      setSelectedItem(item);
                      setSelectedFile(item);
                      setShowFileModal(true);
                    }
                  }}
                  style={{ cursor: "pointer" }}
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
                
                {/* Action buttons for grid items */}
                <div style={{
                  position: "absolute",
                  bottom: "0.5rem",
                  left: "0.5rem",
                  right: "0.5rem",
                  display: "flex",
                  gap: "0.25rem",
                  justifyContent: "center",
                  alignItems: "center",
                  flexWrap: "wrap"
                }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(item.id, item.filename || item.name, item.type);
                    }}
                    style={{
                      background: "#3b82f6",
                      color: "white",
                      border: "none",
                      padding: "0.4rem 0.6rem",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      fontWeight: "500",
                      transition: "all 0.2s",
                      minWidth: "28px"
                    }}
                    onMouseEnter={(e) => e.target.style.background = "#2563eb"}
                    onMouseLeave={(e) => e.target.style.background = "#3b82f6"}
                    title="Download"
                  >
                    ↓
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleShareFile(item);
                    }}
                    style={{
                      background: "#8b5cf6",
                      color: "white",
                      border: "none",
                      padding: "0.4rem 0.6rem",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      fontWeight: "500",
                      transition: "all 0.2s",
                      minWidth: "28px"
                    }}
                    onMouseEnter={(e) => e.target.style.background = "#7c3aed"}
                    onMouseLeave={(e) => e.target.style.background = "#8b5cf6"}
                    title="Share"
                  >
                    ⇄
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (item.type === "folder") {
                        handleDeleteFolder(item.id);
                      } else {
                        handleDelete(item.id);
                      }
                    }}
                    style={{
                      background: "#ef4444",
                      color: "white",
                      border: "none",
                      padding: "0.4rem 0.6rem",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      fontWeight: "500",
                      transition: "all 0.2s",
                      minWidth: "28px"
                    }}
                    onMouseEnter={(e) => e.target.style.background = "#dc2626"}
                    onMouseLeave={(e) => e.target.style.background = "#ef4444"}
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Upload Progress Modal */}
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 10000
          }}>
            <div style={{
              background: "#fff",
              borderRadius: "12px",
              padding: "2rem",
              maxWidth: "450px",
              width: "90%",
              boxShadow: "0 20px 60px rgba(0, 0, 0, 0.2)"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#0f172a", margin: 0 }}>
                  Uploading Files
                </h2>
                <button
                  onClick={() => {}}
                  disabled
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "not-allowed",
                    opacity: 0.5,
                    fontSize: "1.5rem"
                  }}
                  title="Upload in progress..."
                >
                  ✕
                </button>
              </div>
              
              <div style={{ marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.875rem", color: "#64748b", fontWeight: 500 }}>Progress</span>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#2563eb" }}>
                    {Math.round(uploadProgress)}%
                  </span>
                </div>
                <div style={{
                  width: "100%",
                  height: "8px",
                  backgroundColor: "#e5e7eb",
                  borderRadius: "4px",
                  overflow: "hidden"
                }}>
                  <div
                    style={{
                      height: "100%",
                      backgroundColor: "#2563eb",
                      width: `${uploadProgress}%`,
                      transition: "width 0.3s ease",
                      borderRadius: "4px"
                    }}
                  />
                </div>
              </div>
              
              <p style={{ fontSize: "0.875rem", color: "#64748b", margin: 0, textAlign: "center" }}>
                Please wait while your files are being uploaded...
              </p>
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
            onShare={() => {
              handleShareFile(selectedFile);
              setShowFileModal(false);
            }}
            loading={folderLoading}
          />
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && deleteTarget && (
          <div style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999
          }} onClick={() => setShowDeleteModal(false)}>
            <div style={{
              background: "#fff",
              borderRadius: "8px",
              padding: "2rem",
              maxWidth: "400px",
              width: "90%",
              boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)"
            }} onClick={(e) => e.stopPropagation()}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#0f172a", marginBottom: "1rem" }}>
                Confirm Delete
              </h2>
              <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "1.5rem" }}>
                {deleteTarget.type === "folder"
                  ? "Are you sure you want to delete this folder and all its contents? This action cannot be undone."
                  : "Are you sure you want to delete this file? This action cannot be undone."}
              </p>
              <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
                <button
                  onClick={() => setShowDeleteModal(false)}
                  style={{
                    background: "#e5e7eb",
                    color: "#0f172a",
                    border: "none",
                    padding: "0.625rem 1.25rem",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontWeight: 500,
                    fontSize: "0.875rem",
                    transition: "background-color 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.background = "#d1d5db"}
                  onMouseLeave={(e) => e.target.style.background = "#e5e7eb"}
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDelete}
                  style={{
                    background: "#ef4444",
                    color: "#fff",
                    border: "none",
                    padding: "0.625rem 1.25rem",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontWeight: 500,
                    fontSize: "0.875rem",
                    transition: "background-color 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.background = "#dc2626"}
                  onMouseLeave={(e) => e.target.style.background = "#ef4444"}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Folder Modal */}
        {showCreateFolderModal && (
          <div style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999
          }} onClick={() => setShowCreateFolderModal(false)}>
            <div style={{
              background: "#fff",
              borderRadius: "8px",
              padding: "2rem",
              maxWidth: "400px",
              width: "90%",
              boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)"
            }} onClick={(e) => e.stopPropagation()}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#0f172a", marginBottom: "1rem" }}>
                Create New Folder
              </h2>
              <div style={{ marginBottom: "1.5rem" }}>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 500, color: "#374151", marginBottom: "0.5rem" }}>
                  Folder Name
                </label>
                <input
                  type="text"
                  placeholder="Enter folder name"
                  value={newFolderName}
                  onChange={(e) => {
                    setNewFolderName(e.target.value);
                    if (folderNameError) setFolderNameError("");
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleConfirmCreateFolder();
                    }
                  }}
                  style={{
                    width: "100%",
                    border: folderNameError ? "1px solid #dc2626" : "1px solid #d1d5db",
                    borderRadius: "6px",
                    padding: "0.625rem 0.875rem",
                    fontSize: "0.875rem",
                    boxSizing: "border-box",
                    outline: "none",
                    transition: "border-color 0.2s"
                  }}
                  onFocus={(e) => {
                    if (!folderNameError) e.target.style.borderColor = "#2563eb";
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = folderNameError ? "#dc2626" : "#d1d5db";
                  }}
                />
                {folderNameError && (
                  <p style={{ fontSize: "0.75rem", color: "#dc2626", marginTop: "0.25rem" }}>
                    {folderNameError}
                  </p>
                )}
              </div>
              <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
                <button
                  onClick={() => setShowCreateFolderModal(false)}
                  style={{
                    background: "#e5e7eb",
                    color: "#0f172a",
                    border: "none",
                    padding: "0.625rem 1.25rem",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontWeight: 500,
                    fontSize: "0.875rem",
                    transition: "background-color 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.background = "#d1d5db"}
                  onMouseLeave={(e) => e.target.style.background = "#e5e7eb"}
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmCreateFolder}
                  style={{
                    background: "#2563eb",
                    color: "#fff",
                    border: "none",
                    padding: "0.625rem 1.25rem",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontWeight: 500,
                    fontSize: "0.875rem",
                    transition: "background-color 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.background = "#1d4ed8"}
                  onMouseLeave={(e) => e.target.style.background = "#2563eb"}
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Hidden file input for single file upload */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelect}
        style={{ display: "none" }}
      />

      {/* Hidden folder input for folder upload */}
      <input
        ref={folderInputRef}
        type="file"
        webkitdirectory="true"
        mozdirectory="true"
        onChange={handleFolderSelect}
        style={{ display: "none" }}
      />

      {/* Share Modal */}
      {shareFile && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            overflow: "auto"
          }}
          onClick={() => setShareFile(null)}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "1.5rem",
              borderRadius: "8px",
              maxWidth: "500px",
              width: "90%",
              maxHeight: "90vh",
              overflow: "auto",
              margin: "auto",
              boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#0f172a", margin: 0 }}>
                Share "{shareFile.filename || shareFile.name || shareFile.id}"
              </h2>
              <button
                onClick={() => setShareFile(null)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 0
                }}
              >
                <X style={{ color: "#dc2626", width: "1.5rem", height: "1.5rem" }} />
              </button>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              {/* Email Input - Hidden when generating public link */}
              {!generatePublicLink && (
                <div style={{ marginBottom: "1rem", position: "relative" }}>
                  <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Email</label>
                  <input
                    type="email"
                    placeholder="Enter email"
                    value={shareEmail}
                    onChange={(e) => {
                      setShareEmail(e.target.value);
                      if (emailError) setEmailError("");
                    }}
                    style={{
                      width: "100%",
                      border: emailError ? "1px solid #dc2626" : "1px solid #d1d5db",
                      borderRadius: "6px",
                      padding: "0.5rem 0.75rem",
                      fontSize: "0.875rem",
                      background: "transparent",
                      outline: "none",
                      transition: "border-color 0.2s",
                      height: "2.5rem",
                      boxSizing: "border-box"
                    }}
                    disabled={shareLoading}
                  />
                  {emailError && <span style={{ color: "#dc2626", fontSize: "0.75rem", marginTop: "0.25rem", display: "block" }}>{emailError}</span>}
                </div>
              )}

              {/* Expiry Date Input */}
              <div style={{ marginBottom: "1rem", position: "relative" }}>
                <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Expiry Date</label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    placeholder="YY/MM/DD"
                    value={shareExpiryDate}
                    onChange={(e) => {
                      setShareExpiryDate(e.target.value);
                      if (dateError) setDateError("");
                    }}
                    style={{
                      width: "100%",
                      border: dateError ? "1px solid #dc2626" : "1px solid #d1d5db",
                      borderRadius: "6px",
                      padding: "0.5rem 0.75rem",
                      fontSize: "0.875rem",
                      background: "transparent",
                      outline: "none",
                      transition: "border-color 0.2s",
                      height: "2.5rem",
                      boxSizing: "border-box",
                      paddingRight: "2.5rem"
                    }}
                    disabled={shareLoading}
                  />
                  <button
                    onClick={() => setShowCalendar(!showCalendar)}
                    style={{
                      position: "absolute",
                      right: "0.75rem",
                      top: "50%",
                      transform: "translateY(-50%)",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center"
                    }}
                  >
                    <Calendar style={{ width: "18px", height: "18px", color: "#64748b" }} />
                  </button>
                  {showCalendar && (
                    <div style={{
                      position: "absolute",
                      top: "100%",
                      right: 0,
                      marginTop: "8px",
                      background: "#fff",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      padding: "12px",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                      zIndex: 200,
                      minWidth: "280px"
                    }}>
                      <CalendarPicker onDateSelect={handleCalendarDateSelect} currentDate={calendarDate} />
                    </div>
                  )}
                </div>
                {dateError && <span style={{ color: "#dc2626", fontSize: "0.75rem", marginTop: "0.25rem", display: "block" }}>{dateError}</span>}
              </div>

              {/* Generate Public Link Toggle */}
              <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label style={{ color: "#374151", fontSize: "0.875rem", fontWeight: 500, marginBottom: 0 }}>Generate public link</label>
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    width: "48px",
                    height: "24px",
                    background: generatePublicLink ? "#2563eb" : "#d1d5db",
                    borderRadius: "12px",
                    padding: "2px",
                    cursor: "pointer",
                    transition: "background 0.2s"
                  }}
                  onClick={() => setGeneratePublicLink(!generatePublicLink)}
                >
                  <div
                    style={{
                      width: "20px",
                      height: "20px",
                      background: "white",
                      borderRadius: "50%",
                      transition: "transform 0.2s",
                      transform: generatePublicLink ? "translateX(24px)" : "translateX(0)"
                    }}
                  ></div>
                </div>
              </div>

              {/* Max Downloads Input */}
              <div style={{ marginBottom: "1rem", position: "relative" }}>
                <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Max downloads</label>
                <input
                  type="number"
                  placeholder="Unlimited"
                  value={maxDownloads}
                  onChange={(e) => setMaxDownloads(e.target.value.replace(/[^0-9]/g, ""))}
                  min="1"
                  style={{
                    width: "100%",
                    border: "1px solid #d1d5db",
                    borderRadius: "6px",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.875rem",
                    background: "transparent",
                    outline: "none",
                    transition: "border-color 0.2s",
                    height: "2.5rem",
                    boxSizing: "border-box"
                  }}
                  disabled={shareLoading}
                />
              </div>

              {/* Password Input (only for public links) */}
              {generatePublicLink && (
                <div style={{ marginBottom: "1.5rem" }}>
                  <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Password (optional)</label>
                  <input
                    type="password"
                    placeholder="Leave empty for no password"
                    value={publicLinkPassword}
                    onChange={(e) => setPublicLinkPassword(e.target.value)}
                    style={{
                      width: "100%",
                      border: "1px solid #d1d5db",
                      borderRadius: "6px",
                      padding: "0.5rem 0.75rem",
                      fontSize: "0.875rem",
                      background: "transparent",
                      outline: "none",
                      transition: "border-color 0.2s",
                      height: "2.5rem",
                      boxSizing: "border-box"
                    }}
                    disabled={shareLoading}
                  />
                </div>
              )}

              {/* Create Share Link Button */}
              <button
                onClick={handleCreateShareLink}
                style={{
                  width: "100%",
                  padding: "0.5rem 1rem",
                  backgroundColor: "#2563eb",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  cursor: "pointer",
                  height: "2.5rem",
                  opacity: shareLoading ? 0.6 : 1,
                  pointerEvents: shareLoading ? "none" : "auto",
                  transition: "background-color 0.2s"
                }}
                disabled={shareLoading}
                onMouseEnter={(e) => !shareLoading && (e.target.style.backgroundColor = "#1d4ed8")}
                onMouseLeave={(e) => !shareLoading && (e.target.style.backgroundColor = "#2563eb")}
              >
                {shareLoading ? "Creating..." : generatePublicLink ? "Create public link" : "Create share link"}
              </button>

              {successMessage && (
                <div style={{
                  marginTop: "1rem",
                  padding: "0.75rem",
                  backgroundColor: "#dcfce7",
                  color: "#166534",
                  borderRadius: "6px",
                  fontSize: "0.875rem",
                  border: "1px solid #bbf7d0",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "0.75rem"
                }}>
                  <span style={{ flex: 1, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{successMessage}</span>
                  <button
                    onClick={() => {
                      const linkText = successMessage.split('\n')[1];
                      navigator.clipboard.writeText(linkText);
                      setSuccessMessage("✓ Link copied to clipboard!");
                      setTimeout(() => setSuccessMessage(""), 2000);
                    }}
                    style={{
                      padding: "0.4rem 0.8rem",
                      backgroundColor: "#bbf7d0",
                      color: "#166534",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      flexShrink: 0,
                      transition: "background-color 0.2s"
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = "#86efac"}
                    onMouseLeave={(e) => e.target.style.backgroundColor = "#bbf7d0"}
                  >
                    Copy
                  </button>
                </div>
              )}

              {/* Existing Public Links Section */}
              {linksLoading && (
                <div style={{
                  marginTop: "1.5rem",
                  padding: "1rem",
                  backgroundColor: "#f3f4f6",
                  borderRadius: "6px",
                  textAlign: "center",
                  color: "#64748b",
                  fontSize: "0.875rem"
                }}>
                  Loading links...
                </div>
              )}

              {!linksLoading && publicLinks.length > 0 && (
                <div style={{
                  marginTop: "1.5rem",
                  paddingTop: "1rem",
                  borderTop: "1px solid #e5e7eb"
                }}>
                  <h3 style={{
                    fontSize: "0.875rem",
                    fontWeight: 600,
                    color: "#374151",
                    marginBottom: "0.75rem",
                    margin: 0
                  }}>
                    Existing Public Links
                  </h3>
                  <div style={{
                    marginTop: "0.75rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                    maxHeight: "300px",
                    overflow: "auto"
                  }}>
                    {publicLinks.map((link) => {
                      const baseUrl = `${window.location.protocol}//${window.location.hostname}`;
                      const linkToken = link.short_code || link.token;
                      const fullLink = `${baseUrl}/#/s/${linkToken}/access`;
                      return (
                      <div
                        key={link.id}
                        style={{
                          padding: "0.75rem",
                          backgroundColor: "#f9fafb",
                          border: "1px solid #e5e7eb",
                          borderRadius: "6px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          fontSize: "0.75rem"
                        }}
                      >
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            color: "#0f172a",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            fontFamily: "monospace",
                            marginBottom: "0.25rem"
                          }}>
                            {fullLink}
                          </div>
                          <div style={{ color: "#64748b" }}>
                            Created: {new Date(link.created_at).toLocaleDateString()}
                            {link.expires_at && ` | Expires: ${new Date(link.expires_at).toLocaleDateString()}`}
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeletePublicLink(link.id)}
                          style={{
                            marginLeft: "0.5rem",
                            padding: "0.4rem 0.6rem",
                            backgroundColor: "#fee2e2",
                            color: "#dc2626",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer",
                            fontSize: "0.7rem",
                            fontWeight: 500,
                            whiteSpace: "nowrap",
                            transition: "all 0.2s"
                          }}
                          onMouseEnter={(e) => {
                            e.target.style.backgroundColor = "#fecaca";
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.backgroundColor = "#fee2e2";
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showAlertModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
          onClick={() => setShowAlertModal(false)}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "2rem",
              borderRadius: "8px",
              maxWidth: "400px",
              textAlign: "center",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0, marginBottom: "1rem", color: "#333" }}>
              {alertTitle}
            </h3>
            <p style={{ marginTop: 0, marginBottom: "1.5rem", color: "#666" }}>
              {alertMessage}
            </p>
            <button
              onClick={() => setShowAlertModal(false)}
              style={{
                padding: "0.75rem 1.5rem",
                backgroundColor: "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "1rem"
              }}
            >
              OK
            </button>
          </div>
        </div>
      )}

      {showShareModal && selectedFolderForShare && (
        <FolderShareModal
          folder={selectedFolderForShare}
          onClose={() => {
            setShowShareModal(false);
            setSelectedFolderForShare(null);
          }}
        />
      )}
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
