import { LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const roleLabels: Record<string, string> = {
  admin: "Administrator",
  finance_manager: "Finance Manager",
  analyst: "Analyst",
  auditor: "Auditor",
};

export function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-16 shrink-0 items-center justify-end gap-4 border-b border-slate-200 bg-white px-6">
      <div className="text-right">
        <p className="text-sm font-semibold text-slate-800">{user?.full_name}</p>
        <p className="text-xs text-slate-500">{user ? roleLabels[user.role] : ""}</p>
      </div>
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
        {user?.full_name.slice(0, 1).toUpperCase()}
      </div>
      <button
        onClick={logout}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        title="Sign out"
      >
        <LogOut size={17} />
      </button>
    </header>
  );
}
