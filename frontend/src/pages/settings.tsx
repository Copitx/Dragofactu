import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Sun, Moon, Monitor, Globe, Info, LogOut, Building } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useUIStore } from "@/stores/ui-store";
import { useAuthStore } from "@/stores/auth-store";
import { useCompanySettings, useUpdateCompanySettings } from "@/hooks/use-company";

const THEMES = [
  { value: "light", icon: Sun },
  { value: "dark", icon: Moon },
  { value: "system", icon: Monitor },
] as const;

const LANGUAGES = [
  { value: "es", label: "Español" },
  { value: "en", label: "English" },
  { value: "de", label: "Deutsch" },
] as const;

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const theme = useUIStore((s) => s.theme);
  const setTheme = useUIStore((s) => s.setTheme);
  const locale = useUIStore((s) => s.locale);
  const setLocale = useUIStore((s) => s.setLocale);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const { data: company } = useCompanySettings();
  const updateCompany = useUpdateCompanySettings();

  const companyForm = useForm({
    defaultValues: {
      name: "",
      legal_name: "",
      tax_id: "",
      address: "",
      city: "",
      postal_code: "",
      phone: "",
      email: "",
      pdf_footer_text: "",
    },
  });

  useEffect(() => {
    if (company) {
      companyForm.reset({
        name: company.name || "",
        legal_name: company.legal_name || "",
        tax_id: company.tax_id || "",
        address: company.address || "",
        city: company.city || "",
        postal_code: company.postal_code || "",
        phone: company.phone || "",
        email: company.email || "",
        pdf_footer_text: company.pdf_footer_text || "",
      });
    }
  }, [company, companyForm]);

  const handleLocaleChange = (value: string) => {
    const loc = value as "es" | "en" | "de";
    setLocale(loc);
    i18n.changeLanguage(loc);
  };

  const onSaveCompany = companyForm.handleSubmit(async (values) => {
    try {
      await updateCompany.mutateAsync(values);
      toast.success(t("settings.company_saved"));
    } catch {
      toast.error(t("settings.company_error"));
    }
  });

  return (
    <>
      <Header title={t("settings.title")} />
      <div className="p-4 md:p-6 max-w-2xl space-y-6">
        {/* Appearance */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h3 className="font-semibold">{t("settings.appearance")}</h3>

          {/* Theme */}
          <div className="space-y-2">
            <Label>{t("settings.theme")}</Label>
            <div className="flex gap-2">
              {THEMES.map(({ value, icon: Icon }) => (
                <Button
                  key={value}
                  variant={theme === value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTheme(value)}
                  className="flex items-center gap-2"
                >
                  <Icon className="h-4 w-4" />
                  {t(`settings.theme_${value}`)}
                </Button>
              ))}
            </div>
          </div>

          {/* Language */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Globe className="h-4 w-4" />
              {t("settings.language")}
            </Label>
            <Select value={locale} onValueChange={handleLocaleChange}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Company / PDF Settings */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Building className="h-4 w-4" />
            {t("settings.company_pdf")}
          </h3>
          <form onSubmit={onSaveCompany} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("settings.company_name")}</Label>
                <Input {...companyForm.register("name")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.legal_name")}</Label>
                <Input {...companyForm.register("legal_name")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.tax_id")}</Label>
                <Input {...companyForm.register("tax_id")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.company_phone")}</Label>
                <Input {...companyForm.register("phone")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.company_email")}</Label>
                <Input type="email" {...companyForm.register("email")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.company_postal_code")}</Label>
                <Input {...companyForm.register("postal_code")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.company_address")}</Label>
                <Input {...companyForm.register("address")} />
              </div>
              <div className="space-y-2">
                <Label>{t("settings.company_city")}</Label>
                <Input {...companyForm.register("city")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("settings.pdf_footer")}</Label>
              <Textarea {...companyForm.register("pdf_footer_text")} rows={4} />
            </div>
            <Button type="submit" disabled={updateCompany.isPending}>
              {updateCompany.isPending ? t("buttons.loading") : t("buttons.save")}
            </Button>
          </form>
        </div>

        {/* About */}
        <div className="rounded-lg border bg-card p-6 space-y-3">
          <h3 className="font-semibold flex items-center gap-2">
            <Info className="h-4 w-4" />
            {t("settings.about")}
          </h3>
          <div className="text-sm space-y-1">
            <p><span className="text-muted-foreground">{t("settings.version")}:</span> v3.0.0-dev</p>
            {user && (
              <>
                <p><span className="text-muted-foreground">Usuario:</span> {user.full_name} ({user.username})</p>
                <p><span className="text-muted-foreground">Email:</span> {user.email}</p>
                <p><span className="text-muted-foreground">Rol:</span> {user.role}</p>
                {user.company_name && (
                  <p><span className="text-muted-foreground">Empresa:</span> {user.company_name}</p>
                )}
              </>
            )}
          </div>
        </div>

        {/* Logout */}
        <Button
          variant="destructive"
          onClick={logout}
          className="w-full sm:w-auto"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Cerrar Sesión
        </Button>
      </div>
    </>
  );
}
