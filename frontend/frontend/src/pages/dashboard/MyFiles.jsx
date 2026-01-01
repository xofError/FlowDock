import React, { useState } from "react";
import MainLayout from "../../layout/MainLayout";

export default function MyFiles() {
  const sample = [
    { id: 1, name: "Project Proposal.pdf", owner: "Sophia Clark", size: 2.5 * 1024 * 1024, modified: "2024-07-26", type: "PDF" },
    { id: 2, name: "Vacation Photos.zip", owner: "Sophia Clark", size: 150 * 1024 * 1024, modified: "2024-07-20", type: "ZIP" },
    { id: 3, name: "Client Meeting Notes.docx", owner: "Sophia Clark", size: 1.2 * 1024 * 1024, modified: "2024-07-15", type: "DOCX" },
  ];

  const [selected, setSelected] = useState(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);

  const openDetails = (f) => { setSelected(f); setPanelOpen(true); };
  const closeAll = () => { setPanelOpen(false); setShareOpen(false); setSelected(null); };

  return (
    <MainLayout hideSidebar={panelOpen}>
      <div className="max-w-[1100px] mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-[#0d141b]">My Files</h1>
          <div className="flex gap-2">
            <button className="bg-[#e7edf3] px-3 py-2 rounded">All Files</button>
            <button className="bg-[#e7edf3] px-3 py-2 rounded">Documents</button>
          </div>
        </div>

        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-sm text-[#0d141b]">Name</th>
                <th className="px-4 py-3 text-left text-sm text-[#4c739a]">Owner</th>
                <th className="px-4 py-3 text-left text-sm text-[#4c739a]">Last Modified</th>
                <th className="px-4 py-3 text-left text-sm text-[#4c739a]">Size</th>
                <th className="px-4 py-3 text-sm text-[#4c739a]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sample.map(f => (
                <tr key={f.id} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-3 cursor-pointer text-[#0d141b]" onClick={() => openDetails(f)}>{f.name}</td>
                  <td className="px-4 py-3 text-[#4c739a]">{f.owner}</td>
                  <td className="px-4 py-3 text-[#4c739a]">{f.modified}</td>
                  <td className="px-4 py-3 text-[#4c739a]">{(f.size/(1024*1024)).toFixed(1)} MB</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-3">
                      <button className="text-blue-600">Download</button>
                      <button onClick={() => { setSelected(f); setShareOpen(true); setPanelOpen(true); }} className="text-[#0d141b]">Share</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* slide-in details */}
        <div className={`fixed top-16 right-0 h-[calc(100%-64px)] w-[360px] bg-white border-l z-40 transition-transform ${panelOpen ? "translate-x-0" : "translate-x-full"}`}>
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="font-bold text-[#0d141b]">File Details</h2>
            <button onClick={closeAll} className="text-[#4c739a]">X</button>
          </div>
          {selected ? (
            <div className="p-4">
              <p className="text-[#0d141b] font-medium mb-2">{selected.name}</p>
              <div className="grid grid-cols-2 gap-y-3 gap-x-6">
                <div className="text-sm text-[#4c739a]">Type</div><div className="text-sm text-[#0d141b]">{selected.type}</div>
                <div className="text-sm text-[#4c739a]">Size</div><div className="text-sm text-[#0d141b]">{(selected.size/(1024*1024)).toFixed(1)} MB</div>
                <div className="text-sm text-[#4c739a]">Modified</div><div className="text-sm text-[#0d141b]">{selected.modified}</div>
              </div>
              <div className="mt-6 flex gap-2">
                <button className="flex-1 bg-[#1380ec] text-white h-10 rounded">Download</button>
                <button onClick={() => setShareOpen(true)} className="flex-1 border h-10 rounded">Share</button>
              </div>
            </div>
          ) : (
            <div className="p-4 text-[#4c739a]">No file selected</div>
          )}
        </div>

        {/* share modal */}
        {shareOpen && (
          <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold">Share "{selected?.name}"</h3>
                <button onClick={() => setShareOpen(false)} className="text-[#4c739a]">X</button>
              </div>
              <div>
                <input placeholder="Email" className="w-full border border-[#cfdbe7] h-12 rounded px-3" />
                <div className="mt-4 flex justify-end gap-2">
                  <button onClick={() => setShareOpen(false)} className="px-3 py-2">Cancel</button>
                  <button onClick={() => setShareOpen(false)} className="px-3 py-2 bg-[#1380ec] text-white rounded">Create link</button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
