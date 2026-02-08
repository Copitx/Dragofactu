import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { FileQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4">
      <FileQuestion className="h-16 w-16 text-muted-foreground mb-4" />
      <h1 className="text-2xl font-bold mb-2">{t("common.not_found")}</h1>
      <p className="text-muted-foreground mb-6">{t("common.not_found_description")}</p>
      <Button asChild>
        <Link to="/">{t("common.go_home")}</Link>
      </Button>
    </div>
  );
}
