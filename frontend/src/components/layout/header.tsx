import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LogOut, User, Search, Users, FileText, Building2, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageSelector } from "@/components/language-selector";
import { useAuthStore } from "@/stores/auth-store";
import { logout as logoutApi } from "@/api/auth";
import { listClients } from "@/api/clients";
import { listDocuments } from "@/api/documents";
import { projectsApi } from "@/api/projects";
interface HeaderProps {
  title: string;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function GlobalSearch({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const enabled = debouncedQuery.length >= 2;

  const { data: clientsData } = useQuery({
    queryKey: ["search-clients", debouncedQuery],
    queryFn: () => listClients({ search: debouncedQuery, limit: 5 }),
    enabled,
    staleTime: 30_000,
  });
  const { data: docsData } = useQuery({
    queryKey: ["search-docs", debouncedQuery],
    queryFn: () => listDocuments({ search: debouncedQuery, limit: 5 }),
    enabled,
    staleTime: 30_000,
  });
  const { data: projectsData } = useQuery({
    queryKey: ["search-projects", debouncedQuery],
    queryFn: () => projectsApi.list({ search: debouncedQuery, limit: 5 }),
    enabled,
    staleTime: 30_000,
  });

  const clients = clientsData?.items ?? [];
  const docs = docsData?.items ?? [];
  const projects = projectsData?.items ?? [];
  const hasResults = clients.length > 0 || docs.length > 0 || projects.length > 0;

  const go = (path: string) => {
    navigate(path);
    onClose();
  };

  const docTypeLabel: Record<string, string> = {
    quote: t("documents.types.QUOTE"),
    delivery_note: t("documents.types.DELIVERY_NOTE"),
    invoice: t("documents.types.INVOICE"),
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg p-0 gap-0 overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-2 px-4 py-3 border-b">
          <Search className="h-4 w-4 text-muted-foreground shrink-0" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("search.placeholder")}
            className="border-0 shadow-none focus-visible:ring-0 px-0 text-sm"
          />
          {query && (
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setQuery("")}>
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>

        {/* Results */}
        <div className="max-h-96 overflow-y-auto">
          {!enabled ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {t("search.type_hint")}
            </p>
          ) : !hasResults ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {t("search.no_results")}
            </p>
          ) : (
            <div className="py-2">
              {clients.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground px-4 py-1 uppercase tracking-wide">
                    {t("nav.clients")}
                  </p>
                  {clients.map((c) => (
                    <button
                      key={c.id}
                      className="w-full flex items-center gap-3 px-4 py-2 hover:bg-accent transition-colors text-left"
                      onClick={() => go(`/clients`)}
                    >
                      <Users className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{c.name}</p>
                        <p className="text-xs text-muted-foreground">{c.code}{c.tax_id ? ` · ${c.tax_id}` : ""}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              {docs.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground px-4 py-1 uppercase tracking-wide">
                    {t("nav.documents")}
                  </p>
                  {docs.map((d) => (
                    <button
                      key={d.id}
                      className="w-full flex items-center gap-3 px-4 py-2 hover:bg-accent transition-colors text-left"
                      onClick={() => go(`/documents/${d.id}`)}
                    >
                      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{d.code}</p>
                        <p className="text-xs text-muted-foreground">
                          {docTypeLabel[d.type] ?? d.type}
                          {d.client_name ? ` · ${d.client_name}` : ""}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              {projects.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground px-4 py-1 uppercase tracking-wide">
                    {t("nav.projects")}
                  </p>
                  {projects.map((p: any) => (
                    <button
                      key={p.id}
                      className="w-full flex items-center gap-3 px-4 py-2 hover:bg-accent transition-colors text-left"
                      onClick={() => go(`/projects/${p.id}`)}
                    >
                      <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{p.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {p.code}{p.client_name ? ` · ${p.client_name}` : ""}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="border-t px-4 py-2 text-xs text-muted-foreground">
          {t("search.keyboard_hint")}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function Header({ title }: HeaderProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [searchOpen, setSearchOpen] = useState(false);

  // Ctrl+K / Cmd+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen((v) => !v);
      }
      if (e.key === "Escape") setSearchOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch {
      // Clear local state even if API fails
    }
    logout();
    navigate("/login");
  };

  return (
    <>
      <header className="h-16 border-b bg-card flex items-center justify-between px-6 sticky top-0 z-40">
        <h1 className="text-lg font-semibold">{title}</h1>

        <div className="flex items-center gap-2">
          {/* Global search button */}
          <Button
            variant="outline"
            size="sm"
            className="hidden sm:flex items-center gap-2 text-muted-foreground w-48 justify-start"
            onClick={() => setSearchOpen(true)}
          >
            <Search className="h-4 w-4 shrink-0" />
            <span className="text-sm truncate">{t("search.placeholder")}</span>
            <kbd className="ml-auto text-xs bg-muted px-1.5 py-0.5 rounded font-mono">⌘K</kbd>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="sm:hidden"
            onClick={() => setSearchOpen(true)}
          >
            <Search className="h-5 w-5" />
          </Button>

          <LanguageSelector />
          <ThemeToggle />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col">
                  <span>{user?.full_name || user?.username}</span>
                  <span className="text-xs text-muted-foreground font-normal">
                    {user?.email}
                  </span>
                  {user?.company_name && (
                    <span className="text-xs text-muted-foreground font-normal">
                      {user.company_name}
                    </span>
                  )}
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                {t("auth.logout")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
