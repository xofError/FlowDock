import React from "react";
import TopNavBar from "../../layout/TopNavBar";

export default function Settings() {
  return (
    <TopNavBar>
      <div style={{ padding: 24 }}>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-slate-600 mt-2">Account and application settings.</p>
      </div>
    </TopNavBar>
  );
}
