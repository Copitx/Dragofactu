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
  ClipboardList,
  Settings,
  Shield,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Building2,
  ArrowUpDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useDashboardStats } from "@/hooks/use-dashboard";

const navItems = [
  { path: "/", icon: LayoutDashboard, labelKey: "nav.dashboard" },
  { path: "/clients", icon: Users, labelKey: "nav.clients" },
  { path: "/products", icon: Package, labelKey: "nav.products" },
  { path: "/suppliers", icon: Truck, labelKey: "nav.suppliers" },
  { path: "/documents", icon: FileText, labelKey: "nav.documents", badgeKey: "documents" },
  { path: "/inventory", icon: Warehouse, labelKey: "nav.inventory" },
  { path: "/workers", icon: HardHat, labelKey: "nav.workers" },
  { path: "/diary", icon: BookOpen, labelKey: "nav.diary" },
  { path: "/reminders", icon: Bell, labelKey: "nav.reminders" },
  { path: "/projects", icon: Building2, labelKey: "nav.projects" },
  { path: "/reports", icon: BarChart3, labelKey: "nav.reports" },
  { path: "/export", icon: ArrowUpDown, labelKey: "nav.export" },
  { path: "/audit", icon: ClipboardList, labelKey: "nav.audit" },
  { path: "/settings", icon: Settings, labelKey: "nav.settings" },
];

const adminItem = { path: "/admin", icon: Shield, labelKey: "nav.admin" };
const superadminItem = { path: "/superadmin", icon: ShieldAlert, labelKey: "nav.superadmin" };

export function Sidebar() {
  const { t } = useTranslation();
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const user = useAuthStore((s) => s.user);
  const { data: stats } = useDashboardStats();

  // Badge counts
  const overdueCount = (stats?.overdue_invoices ?? 0) + (stats?.due_soon_invoices ?? 0);

  let items = [...navItems];
  if (user?.role === "admin") items = [...items, adminItem];
  if (user?.is_superadmin) items = [...items, superadminItem];

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

          // Determine badge count for this item
          const badgeCount = item.badgeKey === "documents" && overdueCount > 0
            ? overdueCount
            : 0;

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
              <div className="relative">
                <item.icon className="h-5 w-5 shrink-0" />
                {badgeCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 h-4 w-4 rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground flex items-center justify-center">
                    {badgeCount > 9 ? "9+" : badgeCount}
                  </span>
                )}
              </div>
              {!sidebarCollapsed && (
                <span className="flex-1">{t(item.labelKey)}</span>
              )}
              {!sidebarCollapsed && badgeCount > 0 && (
                <span className="ml-auto bg-destructive text-destructive-foreground text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
                  {badgeCount > 99 ? "99+" : badgeCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
