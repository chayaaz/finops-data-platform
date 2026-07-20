import { NavLink } from "react-router-dom";
import { clsx } from "clsx";
import { brandIcon as BrandIcon, navGroups } from "./nav";
import { useAuth } from "@/context/AuthContext";

export function Sidebar() {
  const { user } = useAuth();

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col bg-ink-950 text-slate-300">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
          <BrandIcon size={18} />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight text-white">FinOps Platform</p>
          <p className="text-[11px] text-slate-500">Financial Data Analysis</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-4">
        {navGroups.map((group) => {
          const items = group.items.filter((item) => !item.roles || (user && item.roles.includes(user.role)));
          if (items.length === 0) return null;
          return (
            <div key={group.title} className="mb-5">
              <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-600">
                {group.title}
              </p>
              <div className="space-y-0.5">
                {items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      clsx(
                        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-brand-600/15 text-white"
                          : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                      )
                    }
                  >
                    <item.icon size={16} />
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
