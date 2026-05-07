import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { KeyRound, Eye, EyeOff, CheckCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/api/client";

export default function ResetPasswordPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [done, setDone] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      api.post("/auth/reset-password", { token, new_password: password }).then((r) => r.data),
    onSuccess: () => {
      setDone(true);
      setTimeout(() => navigate("/login"), 3000);
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || t("common.error");
      toast.error(detail);
    },
  });

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center space-y-2">
          <p className="text-red-600 font-medium">{t("auth.reset_invalid_link")}</p>
          <Link to="/login" className="text-primary hover:underline text-sm">
            {t("auth.back_to_login")}
          </Link>
        </div>
      </div>
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      toast.error(t("auth.passwords_dont_match"));
      return;
    }
    mutation.mutate();
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold">{t("auth.reset_title")}</h1>
          <p className="text-sm text-muted-foreground">{t("auth.reset_subtitle")}</p>
        </div>

        {done ? (
          <div className="rounded-lg border p-6 space-y-3 text-center">
            <CheckCircle className="h-10 w-10 text-green-600 mx-auto" />
            <p className="font-medium">{t("auth.reset_success")}</p>
            <p className="text-sm text-muted-foreground">{t("auth.reset_redirect")}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label>{t("auth.new_password")}</Label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type={showPwd ? "text" : "password"}
                  className="pl-9 pr-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  className="absolute right-3 top-2.5 text-muted-foreground"
                  onClick={() => setShowPwd((v) => !v)}
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-1">
              <Label>{t("auth.confirm_password")}</Label>
              <Input
                type={showPwd ? "text" : "password"}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <p className="text-xs text-muted-foreground">{t("auth.password_requirements")}</p>
            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? t("buttons.loading") : t("auth.reset_btn")}
            </Button>
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
