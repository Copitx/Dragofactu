import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/stores/auth-store";
import { register as registerApi, login } from "@/api/auth";
import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageSelector } from "@/components/language-selector";

const registerSchema = z.object({
  company_code: z.string().min(3).max(20),
  company_name: z.string().min(2).max(200),
  company_tax_id: z.string().max(20).optional(),
  username: z.string().min(3).max(50),
  email: z.string().email(),
  password: z.string().min(6).max(128),
  first_name: z.string().max(50).optional(),
  last_name: z.string().max(50).optional(),
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    setError("");
    setIsLoading(true);
    try {
      await registerApi(data);
      // Auto-login after registration
      const loginResponse = await login({
        username: data.username,
        password: data.password,
      });
      setTokens(loginResponse.access_token, loginResponse.refresh_token);
      setUser(loginResponse.user);
      navigate("/");
    } catch (err) {
      if (err instanceof Error && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail ?? t("auth.register_error"));
      } else {
        setError(t("auth.register_error"));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <LanguageSelector />
        <ThemeToggle />
      </div>

      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">{t("auth.register_title")}</CardTitle>
          <CardDescription>{t("auth.register_subtitle")}</CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-1">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Empresa
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="company_code">{t("auth.company_code")}</Label>
                <Input
                  id="company_code"
                  {...register("company_code")}
                  aria-invalid={!!errors.company_code}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_tax_id">{t("auth.company_tax_id")}</Label>
                <Input
                  id="company_tax_id"
                  {...register("company_tax_id")}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="company_name">{t("auth.company_name")}</Label>
              <Input
                id="company_name"
                {...register("company_name")}
                aria-invalid={!!errors.company_name}
              />
            </div>

            <div className="space-y-1 pt-2">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                Admin
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">{t("auth.first_name")}</Label>
                <Input id="first_name" {...register("first_name")} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">{t("auth.last_name")}</Label>
                <Input id="last_name" {...register("last_name")} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="username">{t("auth.username")}</Label>
              <Input
                id="username"
                autoComplete="username"
                {...register("username")}
                aria-invalid={!!errors.username}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">{t("auth.email")}</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                aria-invalid={!!errors.email}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">{t("auth.password")}</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                {...register("password")}
                aria-invalid={!!errors.password}
              />
              <p className="text-xs text-muted-foreground">
                {t("auth.password_requirements")}
              </p>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t("auth.register")}
            </Button>
            <p className="text-sm text-muted-foreground">
              {t("auth.has_account")}{" "}
              <Link to="/login" className="text-primary hover:underline">
                {t("auth.login")}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
