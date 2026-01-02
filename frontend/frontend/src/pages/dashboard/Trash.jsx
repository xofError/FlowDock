import React from "react";
import TopNavBar from "../../layout/TopNavBar";

export default function Trash() {
  return (
    <TopNavBar>
      <div style={{ padding: 24 }}>
        <h1 className="text-2xl font-bold">Trash</h1>
        <p className="text-sm text-slate-600 mt-2">Deleted files are kept here temporarily.</p>
      </div>
    </TopNavBar>
  );
}
