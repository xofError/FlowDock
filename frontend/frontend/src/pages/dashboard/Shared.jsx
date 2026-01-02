import React from "react";
import TopNavBar from "../../layout/TopNavBar";

export default function Shared() {
  return (
    <TopNavBar>
      <div style={{ padding: 24 }}>
        <h1 className="text-2xl font-bold">Shared</h1>
        <p className="text-sm text-slate-600 mt-2">Files shared with you.</p>
      </div>
    </TopNavBar>
  );
}
