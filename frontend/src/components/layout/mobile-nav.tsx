import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LayoutDashboard, FileText, Users, Package, Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";
import {
  Truck,
  Warehouse,
  HardHat,
  BookOpen,
  Bell,
  BarChart3,
  Settings,
  Shield,
  X,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

const mainTabs = [
  { path: "/", icon: LayoutDashboard, labelKey: "nav.dashboard" },
  { path: "/documents", icon: FileText, labelKey: "nav.documents" },
  { path: "/clients", icon: Users, labelKey: "nav.clients" },
  { path: "/products", icon: Package, labelKey: "nav.products" },
];

const menuItems = [
  { path: "/suppliers", icon: Truck, labelKey: "nav.suppliers" },
  { path: "/inventory", icon: Warehouse, labelKey: "nav.inventory" },
  { path: "/workers", icon: HardHat, labelKey: "nav.workers" },
  { path: "/diary", icon: BookOpen, labelKey: "nav.diary" },
  { path: "/reminders", icon: Bell, labelKey: "nav.reminders" },
  { path: "/reports", icon: BarChart3, labelKey: "nav.reports" },
  { path: "/settings", icon: Settings, labelKey: "nav.settings" },
];

const adminItem = { path: "/admin", icon: Shield, labelKey: "nav.admin" };

export function MobileNav() {
  const { t } = useTranslation();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const user = useAuthStore((s) => s.user);

  const allMenuItems = user?.role === "admin" ? [...menuItems, adminItem] : menuItems;

  return (
    <>
      {/* Overlay menu */}
      {menuOpen && (
        <div className="md:hidden fixed inset-0 z-50 bg-background/95 backdrop-blur-sm">
          <div className="flex items-center justify-between p-4 border-b">
            <span className="text-lg font-bold text-primary">{t("app.name")}</span>
            <button onClick={() => setMenuOpen(false)} className="p-2">
              <X className="h-6 w-6" />
            </button>
          </div>
          <nav className="p-4 space-y-1">
            {allMenuItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-3 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {t(item.labelKey)}
                </Link>
              );
            })}
          </nav>
        </div>
      )}

      {/* Bottom tab bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t bg-card pb-safe">
        <div className="flex items-center justify-around h-14">
          {mainTabs.map((tab) => {
            const isActive =
              tab.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(tab.path);

            return (
              <Link
                key={tab.path}
                to={tab.path}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 min-w-[44px] min-h-[44px] text-xs",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                <tab.icon className="h-5 w-5" />
                <span>{t(tab.labelKey)}</span>
              </Link>
            );
          })}

          <button
            onClick={() => setMenuOpen(true)}
            className="flex flex-col items-center justify-center gap-0.5 min-w-[44px] min-h-[44px] text-xs text-muted-foreground"
          >
            <Menu className="h-5 w-5" />
            <span>Menu</span>
          </button>
        </div>
      </nav>
    </>
  );
}
