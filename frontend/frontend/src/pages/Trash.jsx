import React, { useState } from "react";
import TopNavBar from "../layout/TopNavBar";

export default function Trash() {
  const [items, setItems] = useState([
    { id: 1, name: "Old Presentation.pptx", size: "5.8 MB", deleted: "2024-07-01" },
    { id: 2, name: "Draft.docx", size: "1.2 MB", deleted: "2024-06-28" },
  ]);

  const recover = (id) => {
    // stub - implement real API
    setItems(items.filter(i => i.id !== id));
    alert("Recovered (stub)");
  };
  const purge = (id) => {
    if (!confirm("Delete permanently?")) return;
    setItems(items.filter(i => i.id !== id));
    alert("Deleted permanently (stub)");
  };

  return (
    <TopNavBar>
      <div className="max-w-[1000px] mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold mb-4">Trash</h1>
        <p className="text-sm text-slate-600 mt-2">Deleted files are kept here temporarily.</p>
        <div className="bg-white border rounded">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Deleted</th>
                <th className="text-left px-4 py-3">Size</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(it => (
                <tr key={it.id} className="border-t">
                  <td className="px-4 py-3">{it.name}</td>
                  <td className="px-4 py-3 text-[#4c739a]">{it.deleted}</td>
                  <td className="px-4 py-3 text-[#4c739a]">{it.size}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3">
                      <button onClick={() => recover(it.id)} className="text-blue-600">Recover</button>
                      <button onClick={() => purge(it.id)} className="text-red-600">Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan="4" className="px-4 py-6 text-center text-[#4c739a]">Trash is empty</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </TopNavBar>
  );
}
