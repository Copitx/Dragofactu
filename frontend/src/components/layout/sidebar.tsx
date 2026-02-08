import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard,
  Users,
  Package,
  Truck,
  FileText,
  Warehouse,
  HardHat,
  BookOpen,
  Bell,
  BarChart3,
  Settings,
  Shield,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";

const navItems = [
  { path: "/", icon: LayoutDashboard, labelKey: "nav.dashboard" },
  { path: "/clients", icon: Users, labelKey: "nav.clients" },
  { path: "/products", icon: Package, labelKey: "nav.products" },
  { path: "/suppliers", icon: Truck, labelKey: "nav.suppliers" },
  { path: "/documents", icon: FileText, labelKey: "nav.documents" },
  { path: "/inventory", icon: Warehouse, labelKey: "nav.inventory" },
  { path: "/workers", icon: HardHat, labelKey: "nav.workers" },
  { path: "/diary", icon: BookOpen, labelKey: "nav.diary" },
  { path: "/reminders", icon: Bell, labelKey: "nav.reminders" },
  { path: "/reports", icon: BarChart3, labelKey: "nav.reports" },
  { path: "/settings", icon: Settings, labelKey: "nav.settings" },
];

const adminItem = { path: "/admin", icon: Shield, labelKey: "nav.admin" };

export function Sidebar() {
  const { t } = useTranslation();
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const user = useAuthStore((s) => s.user);

  const items = user?.role === "admin" ? [...navItems, adminItem] : navItems;

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col border-r bg-card h-screen sticky top-0 transition-all duration-200",
        sidebarCollapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b">
        {!sidebarCollapsed && (
          <Link to="/" className="text-lg font-bold text-primary">
            {t("app.name")}
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn("ml-auto", sidebarCollapsed && "mx-auto")}
          onClick={toggleSidebar}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2 px-2">
        {items.map((item) => {
          const isActive =
            item.path === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.path);

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                sidebarCollapsed && "justify-center px-2"
              )}
              title={sidebarCollapsed ? t(item.labelKey) : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!sidebarCollapsed && <span>{t(item.labelKey)}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
