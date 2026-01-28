import React, { useState } from 'react';
import { X, ShieldCheck, AlertCircle } from 'lucide-react';

// Tailwind color mapping (light mode defaults, can be extended for dark mode)
const colorMap = {
    // Backgrounds
    'bg-white': '#ffffff',
    'bg-slate-100': '#f1f5f9',
    'bg-slate-50': '#f8fafc',
    'bg-slate-900': '#0f172a',
    
    // Text colors
    'text-slate-900': '#0f172a',
    'text-slate-700': '#334155',
    'text-slate-600': '#475569',
    'text-slate-500': '#64748b',
    'text-slate-400': '#94a3b8',
    'text-slate-200': '#e2e8f0',
    
    // Border colors
    'border-slate-200': '#e5e7eb',
    'border-slate-300': '#cbd5e1',
    
    // Status colors
    'text-red-600': '#dc2626',
    'text-green-600': '#16a34a',
    'text-purple-600': '#8b5cf6',
    'text-blue-600': '#2563eb',
    'text-gray-600': '#64748b',
    'text-gray-400': '#9ca3af',
    
    // Button colors
    'btn-blue': '#2563eb',
    'btn-blue-hover': '#1d4ed8',
    'btn-purple': '#8b5cf6',
    'btn-purple-hover': '#7c3aed',
    'btn-red': '#ef4444',
    'btn-red-hover': '#dc2626',
    'btn-gray': '#e5e7eb',
    'btn-gray-hover': '#d1d5db',
};

const FileDetailsModal = ({ 
    file, 
    onClose, 
    onDownload, 
    onDelete,
    onShare,
    loading = false 
}) => {
    const [showAlertModal, setShowAlertModal] = useState(false);
    const [alertMessage, setAlertMessage] = useState("");
    
    if (!file) return null;

    // Extract hash and scan status from metadata
    const fileHash = file?.metadata?.sha256 || file?.metadata?.hash || file?.hash || null;
    const scanStatus = file?.metadata?.scan_status || file?.scan_status || "unknown";
    const isInfected = file?.is_infected || false;
    
    // Debug logging
    if (process.env.NODE_ENV === 'development') {
        console.log("[FileDetailsModal] File object:", file);
        console.log("[FileDetailsModal] Hash:", fileHash);
        console.log("[FileDetailsModal] Scan status:", scanStatus);
    }

    return (
        <div 
            style={{
                position: "fixed",
                inset: 0,
                backgroundColor: "rgba(0, 0, 0, 0.5)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 9999
            }}
            onClick={onClose}
        >
            <div 
                style={{
                    background: colorMap['bg-white'],
                    borderRadius: "8px",
                    padding: "1.5rem",
                    maxWidth: "500px",
                    width: "90%",
                    boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)",
                    maxHeight: "90vh",
                    overflowY: "auto",
                    color: colorMap['text-slate-900']
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "1rem"
                }}>
                    <h2 style={{
                        fontSize: "1.25rem",
                        fontWeight: 600,
                        color: colorMap['text-slate-900']
                    }}>File Details</h2>
                    <button 
                        onClick={onClose}
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
                        <X style={{ color: colorMap['text-red-600'], width: "1.5rem", height: "1.5rem" }} />
                    </button>
                </div>

                {/* Info Section */}
                <div style={{ marginBottom: "1.5rem" }}>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Name:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.filename || file?.name || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Size:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.size || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Upload Date:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.uploadDate || file?.upload_date || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Owner:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.owner || "You"}</span>
                    </div>

                    {/* Security Scan Status */}
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Security Scan:</span>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                            {isInfected ? (
                                <>
                                    <AlertCircle style={{ width: "1rem", height: "1rem", color: colorMap['text-red-600'] }} />
                                    <span style={{ color: colorMap['text-red-600'], fontWeight: 600 }}>Infected</span>
                                </>
                            ) : scanStatus === "clean" ? (
                                <>
                                    <ShieldCheck style={{ width: "1rem", height: "1rem", color: colorMap['text-green-600'] }} />
                                    <span style={{ color: colorMap['text-green-600'], fontWeight: 600 }}>Clean</span>
                                </>
                            ) : scanStatus === "skipped" ? (
                                <span style={{ color: colorMap['text-purple-600'], fontSize: "0.75rem" }}>Not Scanned</span>
                            ) : (
                                <span style={{ color: colorMap['text-slate-500'], fontSize: "0.75rem" }}>—</span>
                            )}
                        </div>
                    </div>

                    {/* SHA-256 Hash */}
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem",
                        flexDirection: fileHash ? "column" : "row"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>SHA-256 Hash:</span>
                        {fileHash ? (
                            <div style={{
                                marginTop: fileHash ? "0.5rem" : 0,
                                padding: "0.5rem",
                                backgroundColor: colorMap['bg-slate-50'],
                                borderRadius: "4px",
                                border: `1px solid ${colorMap['border-slate-300']}`,
                                fontFamily: "monospace",
                                fontSize: "0.7rem",
                                wordBreak: "break-all",
                                maxHeight: "4rem",
                                overflowY: "auto",
                                userSelect: "all",
                                cursor: "text",
                                color: colorMap['text-slate-700']
                            }}>
                                {fileHash}
                            </div>
                        ) : (
                            <span style={{ color: colorMap['text-gray-400'] }}>Calculating...</span>
                        )}
                    </div>

                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>File Hash (Legacy):</span>
                        <span style={{ color: colorMap['text-slate-900'], fontSize: "0.75rem", fontFamily: "monospace" }}>{file?.hash || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Encryption Status:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.encryption || (file?.encrypted ? "AES-256" : "None")}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: `1px solid ${colorMap['border-slate-200']}`,
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Download Count:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.downloads || 0}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: colorMap['text-slate-500'] }}>Last Accessed:</span>
                        <span style={{ color: colorMap['text-slate-900'] }}>{file?.lastAccessed || file?.last_accessed || "N/A"}</span>
                    </div>
                </div>

                {/* Buttons */}
                <div style={{
                    display: "flex",
                    gap: "0.5rem",
                    justifyContent: "flex-end"
                }}>
                    <button
                        onClick={() => {
                            onDownload(file?.id || file?.file_id, file?.filename || file?.name);
                            onClose();
                        }}
                        style={{
                            backgroundColor: colorMap['btn-blue'],
                            color: "#fff",
                            border: "none",
                            padding: "0.5rem 1rem",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontWeight: 500,
                            fontSize: "0.875rem",
                            transition: "background-color 0.2s",
                            opacity: loading ? 0.6 : 1,
                            pointerEvents: loading ? "none" : "auto"
                        }}
                        onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = colorMap['btn-blue-hover'])}
                        onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = colorMap['btn-blue'])}
                        disabled={loading}
                    >
                        Download
                    </button>
                    <button
                        onClick={() => {
                            if (onShare) {
                                onShare();
                            } else {
                                setAlertMessage("Share functionality is not available!");
                                setShowAlertModal(true);
                            }
                        }}
                        style={{
                            backgroundColor: colorMap['btn-purple'],
                            color: "#fff",
                            border: "none",
                            padding: "0.5rem 1rem",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontWeight: 500,
                            fontSize: "0.875rem",
                            transition: "background-color 0.2s",
                            opacity: loading ? 0.6 : 1,
                            pointerEvents: loading ? "none" : "auto"
                        }}
                        onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = colorMap['btn-purple-hover'])}
                        onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = colorMap['btn-purple'])}
                        disabled={loading}
                    >
                        Share
                    </button>
                    <button
                        onClick={() => onDelete(file?.id || file?.file_id)}
                        style={{
                            backgroundColor: colorMap['btn-red'],
                            color: "#fff",
                            border: "none",
                            padding: "0.5rem 1rem",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontWeight: 500,
                            fontSize: "0.875rem",
                            transition: "background-color 0.2s",
                            opacity: loading ? 0.6 : 1,
                            pointerEvents: loading ? "none" : "auto"
                        }}
                        onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = colorMap['btn-red-hover'])}
                        onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = colorMap['btn-red'])}
                        disabled={loading}
                    >
                        Delete
                    </button>
                </div>
            </div>

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
                        zIndex: 10000
                    }}
                    onClick={() => setShowAlertModal(false)}
                >
                    <div
                        style={{
                            backgroundColor: colorMap['bg-white'],
                            padding: "2rem",
                            borderRadius: "8px",
                            maxWidth: "400px",
                            textAlign: "center",
                            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <p style={{ margin: "0 0 1.5rem 0", color: colorMap['text-slate-700'] }}>
                            {alertMessage}
                        </p>
                        <button
                            onClick={() => setShowAlertModal(false)}
                            style={{
                                padding: "0.75rem 1.5rem",
                                backgroundColor: colorMap['btn-blue'],
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
        </div>
    );
};

export default FileDetailsModal;

