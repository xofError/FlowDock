import React, { useEffect, useState } from "react";
import MainLayout from "../layout/MainLayout";
import { useAuthContext } from "../context/AuthContext.jsx";

export default function Settings() {
  const { user } = useAuthContext();
  const [tab, setTab] = useState("profile");

  useEffect(() => {
    const hash = (window.location.hash || "").replace("#", "");
    if (hash) setTab(hash);
  }, []);

  // sample storage breakdown
  const total = 100 * 1024; // MB for display
  const usedMB = 12.5 * 1024;
  const breakdown = [
    { label: "Documents", mb: 2.5 * 1024 },
    { label: "Images", mb: 4 * 1024 },
    { label: "Videos", mb: 6 * 1024 },
  ];

  return (
    <MainLayout>
      <div className="max-w-[1000px] mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold text-[#0d141b] mb-4">Settings</h1>

        <div className="flex gap-4">
          <aside className="w-44">
            <nav className="flex flex-col gap-2">
              <button className={`text-left p-2 rounded ${tab==="profile" ? "bg-[#e7edf3]" : ""}`} onClick={() => setTab("profile")}>Profile</button>
              <button className={`text-left p-2 rounded ${tab==="storage" ? "bg-[#e7edf3]" : ""}`} onClick={() => setTab("storage")}>Storage</button>
              <button className={`text-left p-2 rounded ${tab==="security" ? "bg-[#e7edf3]" : ""}`} onClick={() => setTab("security")}>Security</button>
            </nav>
          </aside>

          <section className="flex-1 bg-white border rounded p-4">
            {tab === "profile" && (
              <div>
                <h2 className="text-lg font-semibold mb-3">Profile</h2>
                <div className="grid grid-cols-2 gap-3">
                  <div><div className="text-sm text-[#4c739a]">Name</div><div className="text-[#0d141b]">{user?.full_name || `${user?.first_name || ""} ${user?.last_name || ""}`}</div></div>
                  <div><div className="text-sm text-[#4c739a]">Email</div><div className="text-[#0d141b]">{user?.email || "—"}</div></div>
                  <div><div className="text-sm text-[#4c739a]">Phone</div><div className="text-[#0d141b]">{user?.phone || user?.mobile || "—"}</div></div>
                </div>
                <div className="mt-4">
                  <button onClick={() => window.location.hash = "#profile" || null} className="bg-[#1380ec] text-white px-3 py-2 rounded" onClick={() => window.location.href = "/settings#profile"}>Edit Profile</button>
                </div>
              </div>
            )}

            {tab === "storage" && (
              <div>
                <h2 className="text-lg font-semibold mb-3">Storage</h2>
                <div className="mb-3 text-sm text-[#4c739a]">Used { (usedMB/1024).toFixed(1) } GB of { (total/1024).toFixed(0) } GB</div>
                <div className="w-full bg-[#e6eef8] rounded h-4 overflow-hidden mb-4">
                  <div className="h-4 bg-[#1380ec]" style={{ width: `${Math.min(100, (usedMB/total)*100)}%` }}></div>
                </div>

                <div className="grid gap-2">
                  {breakdown.map((b) => (
                    <div key={b.label} className="flex justify-between text-sm">
                      <div>{b.label}</div>
                      <div className="text-[#4c739a]">{(b.mb/1024).toFixed(2)} GB</div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 text-xs text-[#4c739a]">Free plan limit: { (total/1024).toFixed(0) } GB</div>
              </div>
            )}

            {tab === "security" && (
              <div>
                <h2 className="text-lg font-semibold mb-3">Security</h2>

                <div className="mb-4">
                  <h3 className="font-medium">Change password</h3>
                  <form className="flex flex-col gap-2 max-w-sm mt-2" onSubmit={(e)=>{ e.preventDefault(); alert("Change password action (stub)"); }}>
                    <input type="password" placeholder="Current password" className="h-10 border rounded px-3" />
                    <input type="password" placeholder="New password" className="h-10 border rounded px-3" />
                    <input type="password" placeholder="Confirm new password" className="h-10 border rounded px-3" />
                    <button className="mt-2 bg-[#1380ec] text-white px-3 py-2 rounded w-32">Change</button>
                  </form>
                </div>

                <div>
                  <h3 className="font-medium mb-2">Trusted devices & sessions</h3>
                  <div className="space-y-2">
                    {/* sample sessions */}
                    {[
                      { id: 1, device: "Chrome on Windows", ip: "192.0.2.1", last: "2024-07-27" },
                      { id: 2, device: "iPhone", ip: "198.51.100.5", last: "2024-07-20" },
                    ].map(s => (
                      <div key={s.id} className="flex items-center justify-between border rounded p-2">
                        <div>
                          <div className="text-sm">{s.device}</div>
                          <div className="text-xs text-[#4c739a]">{s.ip} • last: {s.last}</div>
                        </div>
                        <div className="flex flex-col gap-2">
                          <button className="text-sm text-red-600" onClick={() => alert("Sign out action (stub)")}>Sign out</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </MainLayout>
  );
}
