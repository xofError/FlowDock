import React, { useState } from 'react';
import { X, Calendar } from 'lucide-react';

const ShareModal = ({ 
    item, 
    onClose, 
    onShare,
    loading = false 
}) => {
    const [shareEmail, setShareEmail] = useState("");
    const [shareExpiryDate, setShareExpiryDate] = useState("");
    const [showCalendar, setShowCalendar] = useState(false);
    const [calendarDate, setCalendarDate] = useState(new Date());
    const [emailError, setEmailError] = useState("");
    const [dateError, setDateError] = useState("");

    if (!item) return null;

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

    const parseDate = (dateStr) => {
        const parts = dateStr.split('/');
        let year = parseInt(parts[0]);
        const month = parseInt(parts[1]);
        const day = parseInt(parts[2]);
        
        if (parts[0].length === 2) {
            year += year < 50 ? 2000 : 1900;
        }
        
        return new Date(year, month - 1, day).toISOString();
    };

    const handleCalendarDateSelect = (day, month, year) => {
        const dateStr = `${String(year).slice(-2)}/${String(month + 1).padStart(2, '0')}/${String(day).padStart(2, '0')}`;
        setShareExpiryDate(dateStr);
        setShowCalendar(false);
    };

    const handleShare = async () => {
        let hasError = false;
        
        // Validate email
        if (!shareEmail) {
            setEmailError("Email is required");
            hasError = true;
        } else if (!validateEmail(shareEmail)) {
            setEmailError("Please enter a valid email address");
            hasError = true;
        } else {
            setEmailError("");
        }
        
        // Validate date (optional)
        let expirationDate = null;
        if (shareExpiryDate) {
            if (!validateDate(shareExpiryDate)) {
                setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
                hasError = true;
            } else {
                setDateError("");
                expirationDate = parseDate(shareExpiryDate);
            }
        }
        
        if (hasError) return;

        if (onShare) {
            await onShare(shareEmail, expirationDate);
            setShareEmail("");
            setShareExpiryDate("");
        }
    };

    const CalendarPicker = ({ onDateSelect, currentDate }) => {
        const [pickerMonth, setPickerMonth] = useState(currentDate.getMonth());
        const [pickerYear, setPickerYear] = useState(currentDate.getFullYear());
        
        const daysInMonth = (month, year) => new Date(year, month + 1, 0).getDate();
        const firstDayOfMonth = new Date(pickerYear, pickerMonth, 1).getDay();
        const days = [];
        
        for (let i = 0; i < firstDayOfMonth; i++) {
            days.push(null);
        }
        for (let i = 1; i <= daysInMonth(pickerMonth, pickerYear); i++) {
            days.push(i);
        }
        
        return (
            <div style={{
                position: "absolute",
                top: "100%",
                left: 0,
                backgroundColor: "#ffffff",
                border: "1px solid #d1d5db",
                borderRadius: "6px",
                padding: "1rem",
                marginTop: "0.5rem",
                zIndex: 100,
                minWidth: "300px",
                boxShadow: "0 10px 25px rgba(0, 0, 0, 0.1)"
            }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <button onClick={() => setPickerMonth(m => m === 0 ? 11 : m - 1)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.25rem" }}>
                        ←
                    </button>
                    <span style={{ fontWeight: "600", fontSize: "0.875rem" }}>
                        {new Date(pickerYear, pickerMonth).toLocaleString('default', { month: 'long', year: 'numeric' })}
                    </span>
                    <button onClick={() => setPickerMonth(m => m === 11 ? 0 : m + 1)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.25rem" }}>
                        →
                    </button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "0.5rem", marginBottom: "1rem" }}>
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} style={{ textAlign: "center", fontSize: "0.75rem", fontWeight: "600", color: "#9ca3af" }}>
                            {day}
                        </div>
                    ))}
                    {days.map((day, index) => (
                        <button
                            key={index}
                            onClick={() => day && onDateSelect(day, pickerMonth, pickerYear)}
                            style={{
                                padding: "0.5rem",
                                border: "1px solid #e5e7eb",
                                backgroundColor: day ? "#ffffff" : "#f9fafb",
                                borderRadius: "4px",
                                cursor: day ? "pointer" : "default",
                                fontSize: "0.875rem",
                                color: day ? "#0f172a" : "#d1d5db"
                            }}
                            disabled={!day}
                        >
                            {day}
                        </button>
                    ))}
                </div>
            </div>
        );
    };

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
                        color: "#0f172a",
                        margin: 0
                    }}>
                        Share "{item.name}"
                    </h2>
                    <button 
                        onClick={onClose}
                        style={{
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            padding: "0.5rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center"
                        }}
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Form */}
                <div style={{ marginBottom: "1.5rem" }}>
                    {/* Email Input */}
                    <div style={{ marginBottom: "1.5rem" }}>
                        <label style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontSize: "0.875rem",
                            fontWeight: 500,
                            color: "#374151"
                        }}>
                            Email Address
                        </label>
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
                                padding: "0.75rem",
                                border: `1px solid ${emailError ? "#ef4444" : "#d1d5db"}`,
                                borderRadius: "6px",
                                fontSize: "1rem",
                                boxSizing: "border-box",
                                fontFamily: "inherit"
                            }}
                            disabled={loading}
                        />
                        {emailError && <span style={{ color: "#ef4444", fontSize: "0.875rem", marginTop: "0.25rem", display: "block" }}>{emailError}</span>}
                    </div>

                    {/* Expiry Date Input */}
                    <div style={{ marginBottom: "1.5rem" }}>
                        <label style={{
                            display: "block",
                            marginBottom: "0.5rem",
                            fontSize: "0.875rem",
                            fontWeight: 500,
                            color: "#374151"
                        }}>
                            Expiry Date (Optional)
                        </label>
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
                                    padding: "0.75rem",
                                    paddingRight: "2.5rem",
                                    border: `1px solid ${dateError ? "#ef4444" : "#d1d5db"}`,
                                    borderRadius: "6px",
                                    fontSize: "1rem",
                                    boxSizing: "border-box",
                                    fontFamily: "inherit"
                                }}
                                disabled={loading}
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
                                    padding: "0.25rem",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center"
                                }}
                            >
                                <Calendar size={18} style={{ color: "#64748b" }} />
                            </button>
                            {showCalendar && <CalendarPicker onDateSelect={handleCalendarDateSelect} currentDate={calendarDate} />}
                        </div>
                        {dateError && <span style={{ color: "#ef4444", fontSize: "0.875rem", marginTop: "0.25rem", display: "block" }}>{dateError}</span>}
                    </div>
                </div>

                {/* Buttons */}
                <div style={{
                    display: "flex",
                    gap: "1rem",
                    justifyContent: "flex-end"
                }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: "0.75rem 1.5rem",
                            backgroundColor: "#e5e7eb",
                            border: "none",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontSize: "1rem",
                            fontWeight: 500,
                            opacity: loading ? 0.6 : 1,
                            pointerEvents: loading ? "none" : "auto"
                        }}
                        disabled={loading}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleShare}
                        style={{
                            padding: "0.75rem 1.5rem",
                            backgroundColor: "#8b5cf6",
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontSize: "1rem",
                            fontWeight: 500,
                            opacity: loading ? 0.6 : 1,
                            pointerEvents: loading ? "none" : "auto"
                        }}
                        disabled={loading}
                    >
                        {loading ? "Sharing..." : "Share"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ShareModal;
