import React, { useState } from 'react';
import { X } from 'lucide-react';

const FileDetailsModal = ({ 
    file, 
    onClose, 
    onDownload, 
    onDelete,
    loading = false 
}) => {
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [showAlertModal, setShowAlertModal] = useState(false);
    const [alertMessage, setAlertMessage] = useState("");
    
    if (!file) return null;

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
                    background: "#fff",
                    borderRadius: "8px",
                    padding: "1.5rem",
                    maxWidth: "500px",
                    width: "90%",
                    boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)",
                    maxHeight: "90vh",
                    overflowY: "auto"
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
                        color: "#0f172a"
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
                        <X style={{ color: "#dc2626", width: "1.5rem", height: "1.5rem" }} />
                    </button>
                </div>

                {/* Info Section */}
                <div style={{ marginBottom: "1.5rem" }}>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Name:</span>
                        <span style={{ color: "#0f172a" }}>{file?.filename || file?.name || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Size:</span>
                        <span style={{ color: "#0f172a" }}>{file?.size || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Upload Date:</span>
                        <span style={{ color: "#0f172a" }}>{file?.uploadDate || file?.upload_date || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Owner:</span>
                        <span style={{ color: "#0f172a" }}>{file?.owner || "You"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>File Hash:</span>
                        <span style={{ color: "#0f172a", fontSize: "0.75rem", fontFamily: "monospace" }}>{file?.hash || "N/A"}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Encryption Status:</span>
                        <span style={{ color: "#0f172a" }}>{file?.encryption || (file?.encrypted ? "AES-256" : "None")}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #e5e7eb",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Download Count:</span>
                        <span style={{ color: "#0f172a" }}>{file?.downloads || 0}</span>
                    </div>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        fontSize: "0.875rem"
                    }}>
                        <span style={{ fontWeight: 500, color: "#64748b" }}>Last Accessed:</span>
                        <span style={{ color: "#0f172a" }}>{file?.lastAccessed || file?.last_accessed || "N/A"}</span>
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
                            backgroundColor: "#2563eb",
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
                        onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = "#1d4ed8")}
                        onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = "#2563eb")}
                        disabled={loading}
                    >
                        Download
                    </button>
                    <button
                        onClick={() => {
                            setAlertMessage("Share functionality is coming soon!");
                            setShowAlertModal(true);
                        }}
                        style={{
                            backgroundColor: "#8b5cf6",
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
                        onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = "#7c3aed")}
                        onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = "#8b5cf6")}
                        disabled={loading}
                    >
                        Share
                    </button>
                    <button
                        onClick={() => setShowDeleteConfirm(true)}
                        style={{
                            backgroundColor: "#ef4444",
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
                        onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = "#dc2626")}
                        onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = "#ef4444")}
                        disabled={loading}
                    >
                        Delete
                    </button>
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div 
                    style={{
                        position: "fixed",
                        inset: 0,
                        backgroundColor: "rgba(0, 0, 0, 0.7)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        zIndex: 10000
                    }}
                    onClick={() => setShowDeleteConfirm(false)}
                >
                    <div 
                        style={{
                            background: "#fff",
                            borderRadius: "8px",
                            padding: "2rem",
                            maxWidth: "400px",
                            width: "90%",
                            boxShadow: "0 20px 60px rgba(0, 0, 0, 0.3)"
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 style={{
                            fontSize: "1.25rem",
                            fontWeight: 600,
                            color: "#0f172a",
                            marginBottom: "1rem",
                            margin: "0 0 1rem 0"
                        }}>
                            Confirm Delete
                        </h3>
                        <p style={{
                            fontSize: "0.875rem",
                            color: "#64748b",
                            marginBottom: "1.5rem",
                            margin: "0 0 1.5rem 0"
                        }}>
                            Are you sure you want to delete "{file?.filename || file?.name}"? This action cannot be undone.
                        </p>
                        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
                            <button
                                onClick={() => setShowDeleteConfirm(false)}
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
                                onClick={() => {
                                    onDelete(file?.id || file?.file_id);
                                    onClose();
                                }}
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
                            backgroundColor: "white",
                            padding: "2rem",
                            borderRadius: "8px",
                            maxWidth: "400px",
                            textAlign: "center",
                            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <p style={{ marginTop: 0, marginBottom: "1.5rem", color: "#333" }}>
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
        </div>
    );
};

export default FileDetailsModal;

