import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Sun, Moon, Monitor, Globe, Info, LogOut, Building, Mail } from "lucide-react";

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
import {
  useCompanySettings,
  useUpdateCompanySettings,
  useCompanyEmailSettings,
  useUpdateCompanyEmailSettings,
} from "@/hooks/use-company";

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
  const { data: emailSettings } = useCompanyEmailSettings();
  const updateEmailSettings = useUpdateCompanyEmailSettings();

  const companyForm = useForm({
    defaultValues: {
      name: "",
      legal_name: "",
      trade_name: "",
      tax_id: "",
      address: "",
      city: "",
      postal_code: "",
      phone: "",
      email: "",
      pdf_footer_text: "",
    },
  });

  const emailForm = useForm({
    defaultValues: {
      email_subject_template: "",
      email_body_template: "",
    },
  });

  useEffect(() => {
    if (company) {
      companyForm.reset({
        name: company.name || "",
        legal_name: company.legal_name || "",
        trade_name: (company as any).trade_name || "",
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

  useEffect(() => {
    if (emailSettings) {
      emailForm.reset({
        email_subject_template: emailSettings.email_subject_template || "",
        email_body_template: emailSettings.email_body_template || "",
      });
    }
  }, [emailSettings, emailForm]);

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

  const onSaveEmail = emailForm.handleSubmit(async (values) => {
    try {
      await updateEmailSettings.mutateAsync({
        email_subject_template: values.email_subject_template,
        email_body_template: values.email_body_template,
      });
      toast.success(t("settings.email_saved"));
    } catch {
      toast.error(t("settings.email_error"));
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
                <Label>{t("settings.trade_name")}</Label>
                <Input {...companyForm.register("trade_name")} placeholder={t("settings.trade_name_hint")} />
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

        {/* Email Settings */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Mail className="h-4 w-4" />
            {t("settings.email_title")}
          </h3>
          <p className="text-sm text-muted-foreground">
            {t("settings.email_template_intro")}
          </p>
          <form onSubmit={onSaveEmail} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("settings.email_subject_template")}</Label>
              <Input
                {...emailForm.register("email_subject_template")}
                placeholder={t("settings.email_subject_template_placeholder")}
              />
              <p className="text-xs text-muted-foreground">{t("settings.email_template_simple_help")}</p>
            </div>
            <div className="space-y-2">
              <Label>{t("settings.email_body_template")}</Label>
              <Textarea
                {...emailForm.register("email_body_template")}
                rows={6}
                placeholder={t("settings.email_body_template_placeholder")}
              />
              <p className="text-xs text-muted-foreground">{t("settings.email_template_simple_help")}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={updateEmailSettings.isPending}>
                {updateEmailSettings.isPending ? t("buttons.loading") : t("settings.email_save")}
              </Button>
            </div>
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
