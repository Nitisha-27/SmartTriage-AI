
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Activity,
  LayoutDashboard,
  ClipboardPlus,
  ClipboardCheck,
  Stethoscope,
  BarChart3,
  Settings,
  HeartPulse,
  LogOut,
} from "lucide-react";

import { useAuth } from "@/components/AuthProvider";

const navigation = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/",
    roles: ["admin", "supervisor", "doctor"],
  },
  {
    label: "Patient Intake",
    icon: ClipboardPlus,
    href: "/intake",
    roles: ["admin", "health_worker"],
  },
  {
    label: "Supervisor Review",
    icon: ClipboardCheck,
    href: "/supervisor",
    roles: ["admin", "supervisor"],
  },
  {
    label: "Doctor Queue",
    icon: Stethoscope,
    href: "/doctor",
    roles: ["admin", "doctor"],
  },
  {
    label: "Analytics",
    icon: BarChart3,
    href: "/analytics",
    roles: ["admin", "supervisor"],
  },
];

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  health_worker: "Health Worker",
  supervisor: "Supervisor",
  doctor: "Doctor",
};

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const visibleNavigation = navigation.filter((item) =>
    user ? item.roles.includes(user.role) : false
  );

  const initials = user?.full_name
    ? user.full_name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join("")
        .toUpperCase()
    : "ST";

  return (
    <aside className="fixed left-0 top-0 z-20 flex h-screen w-64 flex-col bg-[#14243A] text-white">

      {/* Branding */}
      <div className="flex items-center gap-3 border-b border-white/10 px-6 py-6">
        <div className="rounded-xl bg-blue-500 p-2">
          <HeartPulse size={25} />
        </div>

        <div>
          <h1 className="text-lg font-bold tracking-wide">
            SmartTriage
          </h1>
          <p className="text-xs text-slate-400">
            AI Healthcare Platform
          </p>
        </div>
      </div>

      {/* Role-based navigation */}
      <div className="px-5 pt-8">
        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
          Workspace
        </p>

        <nav className="space-y-2">
          {visibleNavigation.map((item) => {
            const Icon = item.icon;

            const active =
              pathname === item.href ||
              (item.href !== "/" &&
                pathname.startsWith(`${item.href}/`));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${
                  active
                    ? "bg-blue-600 font-semibold text-white shadow-lg shadow-blue-950/30"
                    : "text-slate-300 hover:bg-white/10 hover:text-white"
                }`}
              >
                <Icon size={19} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User profile and logout */}
      <div className="mt-auto border-t border-white/10 px-5 py-5">

        <div className="flex items-center gap-3 px-4 py-3 text-sm text-slate-300">
          <Settings size={19} />
          Settings
        </div>

        <div className="mt-3 flex items-center gap-3 rounded-lg bg-white/5 p-3">

          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-500 text-sm font-bold">
            {initials}
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">
              {user?.full_name || "Loading..."}
            </p>

            <p className="text-xs text-slate-400">
              {user ? ROLE_LABELS[user.role] : ""}
            </p>
          </div>

          <Activity
            className="shrink-0 text-emerald-400"
            size={16}
          />
        </div>

        <button
          type="button"
          onClick={logout}
          className="mt-3 flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-slate-300 transition hover:bg-red-500/10 hover:text-red-300"
        >
          <LogOut size={18} />
          Sign out
        </button>

      </div>
    </aside>
  );
}
