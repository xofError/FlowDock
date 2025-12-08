import React from "react";

export default function AdminUserManagement() {
  return (
    <div className="relative flex min-h-screen flex-col bg-[#fafafa] font-sans">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-[#d0dce8] bg-white px-4">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-[#0d141b]">FlowDock</span>
        </div>

        <nav className="flex items-center gap-6 text-sm text-[#4c739a]">
          <a href="#" className="hover:text-[#0d141b]">Overview</a>
          <a href="#" className="text-[#0d141b] font-medium hover:text-[#0d141b]">Users</a>
          <a href="#" className="hover:text-[#0d141b]">Teams</a>
          <a href="#" className="hover:text-[#0d141b]">Roles</a>
          <a href="#" className="hover:text-[#0d141b]">Permissions</a>
          <a href="#" className="hover:text-[#0d141b]">Audit Log</a>
          <a href="#" className="hover:text-[#0d141b]">Settings</a>
        </nav>

        <div className="flex items-center gap-4">
          <button className="rounded-full bg-[#1380ec] p-2"></button>
          <div className="h-8 w-8 rounded-full bg-[#e7edf3]"></div>
        </div>
      </header>

      {/* Page Body */}
      <main className="flex flex-1 flex-col gap-10 px-8 py-10">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-[#0d141b]">User Management</h1>
            <p className="text-[#4c739a]">Manage and monitor all users in the system.</p>
          </div>
          <button className="flex items-center gap-2 rounded-full bg-[#1380ec] px-4 py-2 text-white hover:bg-blue-600 transition-all">
            + Add User
          </button>
        </div>

        <div className="flex items-center gap-6">
          <button className="rounded-full bg-[#1380ec] px-3 py-1 text-white">All Users</button>
          <button className="rounded-full bg-[#e7edf3] px-3 py-1 text-[#0d141b] hover:bg-[#dce4ed]">Active</button>
          <button className="rounded-full bg-[#e7edf3] px-3 py-1 text-[#0d141b] hover:bg-[#dce4ed]">Inactive</button>
        </div>

        <div className="rounded-xl border border-[#d0dce8] bg-white p-0">
          <table className="w-full table-auto text-left text-sm text-[#4c739a]">
            <thead className="border-b bg-[#f5f7fb] text-xs font-semibold uppercase text-[#4c739a]">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4].map((row) => (
                <tr key={row} className="border-b last:border-none hover:bg-[#f5f7fb]">
                  <td className="px-4 py-4 text-[#0d141b]">User {row}</td>
                  <td className="px-4 py-4">user{row}@flowdock.com</td>
                  <td className="px-4 py-4 text-[#0d141b]">Admin</td>
                  <td className="px-4 py-4">
                    <span className="rounded-full bg-[#e7edf3] px-2 py-1 text-[#0d141b]">Active</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
