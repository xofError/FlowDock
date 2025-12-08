export default function Button({
  children,
  variant = "primary",
  type = "button",
  disabled = false,
  loading = false,
  loadingText = "Loading...",
  onClick,
  className = "",
  style = {},
  ...props
}) {
  const isDisabled = disabled || loading;
  const baseStyle = { height: style.height ?? 44, opacity: isDisabled ? 0.7 : 1, borderRadius: "12px", ...style };

  const variants = {
    primary: "bg-[#1380ec] text-white",
    secondary: "bg-[#E7EDF3] text-[#0D141B]",
  };

  return (
    <button
      type={type}
      disabled={isDisabled}
      aria-busy={loading ? "true" : "false"}
      onClick={onClick}
      style={baseStyle}
      className={`w-full rounded-lg text-base font-bold flex items-center justify-center transition-all ${variants[variant]} ${className}`}
      {...props}
    >
      {loading ? loadingText : children}
    </button>
  );
}
