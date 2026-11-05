
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
} from "lucide-react";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/" },
  { label: "Patient Intake", icon: ClipboardPlus, href: "/intake" },
  { label: "Supervisor Review", icon: ClipboardCheck, href: "/supervisor" },
  { label: "Doctor Queue", icon: Stethoscope, href: "/doctor" },
  { label: "Analytics", icon: BarChart3, href: "/analytics" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-20 flex h-screen w-64 flex-col bg-[#14243A] text-white">
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

      <div className="px-5 pt-8">
        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
          Workspace
        </p>

        <nav className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;

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

      <div className="mt-auto border-t border-white/10 px-5 py-5">
        <div className="flex items-center gap-3 rounded-lg px-4 py-3 text-sm text-slate-300">
          <Settings size={19} />
          Settings
        </div>

        <div className="mt-5 flex items-center gap-3 rounded-lg bg-white/5 p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500 text-sm font-bold">
            ST
          </div>

          <div>
            <p className="text-sm font-medium">Administrator</p>
            <p className="text-xs text-slate-400">Demo workspace</p>
          </div>

          <Activity className="ml-auto text-emerald-400" size={16} />
        </div>
      </div>
    </aside>
  );
}
