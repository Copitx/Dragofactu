import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Mail, CheckCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/api/client";

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");

  const mutation = useMutation({
    mutationFn: (email: string) =>
      api.post("/auth/forgot-password", { email }).then((r) => r.data),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (email) mutation.mutate(email);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold">{t("auth.forgot_title")}</h1>
          <p className="text-sm text-muted-foreground">{t("auth.forgot_subtitle")}</p>
        </div>

        {mutation.isSuccess ? (
          <div className="rounded-lg border p-6 space-y-3 text-center">
            <CheckCircle className="h-10 w-10 text-green-600 mx-auto" />
            <p className="font-medium">{t("auth.forgot_sent_title")}</p>
            <p className="text-sm text-muted-foreground">{t("auth.forgot_sent_desc")}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label>{t("auth.email")}</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="email"
                  className="pl-9"
                  placeholder="tu@empresa.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? t("buttons.loading") : t("auth.forgot_send_btn")}
            </Button>
            {mutation.isError && (
              <p className="text-xs text-red-600 text-center">{t("common.error")}</p>
            )}
          </form>
        )}

        <p className="text-center text-sm text-muted-foreground">
          <Link to="/login" className="text-primary hover:underline">
            {t("auth.back_to_login")}
          </Link>
        </p>
      </div>
    </div>
  );
}
