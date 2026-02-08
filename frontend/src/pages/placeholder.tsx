import { useLocation, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Construction } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function PlaceholderPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const section = location.pathname.slice(1) || "page";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4">
      <Construction className="h-16 w-16 text-muted-foreground mb-4" />
      <h1 className="text-2xl font-bold mb-2 capitalize">{t(`nav.${section}`, section)}</h1>
      <p className="text-muted-foreground mb-6">Coming soon</p>
      <Button asChild variant="outline">
        <Link to="/">{t("buttons.back")}</Link>
      </Button>
    </div>
  );
}
