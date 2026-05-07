import { useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Upload, FileText, CheckCircle, AlertTriangle, Download } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

import api from "@/api/client";

type EntityType = "clients" | "products" | "suppliers" | "workers" | "diary";

interface PreviewResponse {
  total_rows: number;
  valid_rows: number;
  skipped_rows: number;
  error_rows: number;
  errors: string[];
  sample: Record<string, string>[];
  headers: string[];
}

const ENTITY_LABELS: Record<EntityType, string> = {
  clients: "Clientes",
  products: "Productos",
  suppliers: "Proveedores",
  workers: "Trabajadores",
  diary: "Diario",
};


async function fetchPreview(entityType: EntityType, file: File): Promise<PreviewResponse> {
  const form = new FormData();
  form.append("entity_type", entityType);
  form.append("file", file);
  const res = await api.post<PreviewResponse>("/export/import/preview", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

async function runImport(entityType: EntityType, file: File): Promise<{ message: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<{ message: string }>(`/export/import/${entityType}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export default function ExportPage() {
  const { t } = useTranslation();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [entityType, setEntityType] = useState<EntityType>("clients");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const previewMutation = useMutation({
    mutationFn: () => fetchPreview(entityType, file!),
    onSuccess: (data) => {
      setPreview(data);
      setStep(2);
    },
    onError: () => toast.error(t("common.error")),
  });

  const importMutation = useMutation({
    mutationFn: () => runImport(entityType, file!),
    onSuccess: (data) => {
      toast.success(data.message || t("export.import_success"));
      setStep(3);
    },
    onError: () => toast.error(t("common.error")),
  });

  function reset() {
    setStep(1);
    setFile(null);
    setPreview(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <>
      <Header title={t("export.title")} />
      <div className="p-4 md:p-6 space-y-6 max-w-4xl">

        {/* Export section */}
        <div className="rounded-md border p-4 space-y-3">
          <h2 className="font-semibold text-sm">{t("export.export_title")}</h2>
          <div className="flex flex-wrap gap-2">
            {(["clients", "products", "suppliers"] as EntityType[]).map((e) => (
              <a key={e} href={`/api/v1/export/${e}`} download>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-1" />
                  {ENTITY_LABELS[e]}
                </Button>
              </a>
            ))}
          </div>
        </div>

        {/* Import wizard */}
        <div className="rounded-md border p-4 space-y-4">
          <h2 className="font-semibold text-sm">{t("export.import_title")}</h2>

          {/* Step indicator */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={step >= 1 ? "text-primary font-medium" : ""}>1. {t("export.step_select")}</span>
            <span>→</span>
            <span className={step >= 2 ? "text-primary font-medium" : ""}>2. {t("export.step_preview")}</span>
            <span>→</span>
            <span className={step >= 3 ? "text-primary font-medium" : ""}>3. {t("export.step_confirm")}</span>
          </div>

          {/* Step 1: Select entity + upload file */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs">{t("export.entity_type")}</Label>
                  <Select value={entityType} onValueChange={(v) => setEntityType(v as EntityType)}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(Object.keys(ENTITY_LABELS) as EntityType[]).map((e) => (
                        <SelectItem key={e} value={e}>{ENTITY_LABELS[e]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t("export.select_file")} (CSV, XLSX)</Label>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    className="block w-full text-xs border rounded px-2 py-1.5 bg-background"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">{t("export.file_hint")}</p>
              <Button
                size="sm"
                disabled={!file || previewMutation.isPending}
                onClick={() => previewMutation.mutate()}
              >
                <FileText className="h-4 w-4 mr-1" />
                {previewMutation.isPending ? t("buttons.loading") : t("export.preview_btn")}
              </Button>
            </div>
          )}

          {/* Step 2: Preview */}
          {step === 2 && preview && (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3 text-sm">
                <Badge variant="outline" className="bg-blue-50 text-blue-700">
                  {t("export.total_rows")}: {preview.total_rows}
                </Badge>
                <Badge variant="outline" className="bg-green-50 text-green-700">
                  {t("export.valid_rows")}: {preview.valid_rows}
                </Badge>
                {preview.error_rows > 0 && (
                  <Badge variant="outline" className="bg-red-50 text-red-700">
                    {t("export.error_rows")}: {preview.error_rows}
                  </Badge>
                )}
              </div>

              {preview.errors.length > 0 && (
                <div className="rounded-md bg-red-50 border border-red-200 p-3 space-y-1">
                  <div className="flex items-center gap-1 text-xs font-medium text-red-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {t("export.errors_found")}
                  </div>
                  {preview.errors.slice(0, 10).map((err, i) => (
                    <p key={i} className="text-xs text-red-600">{err}</p>
                  ))}
                </div>
              )}

              {preview.sample.length > 0 && (
                <div className="overflow-x-auto">
                  <p className="text-xs text-muted-foreground mb-1">{t("export.sample_rows")}:</p>
                  <table className="text-xs w-full border-collapse">
                    <thead>
                      <tr>
                        {preview.headers.map((h) => (
                          <th key={h} className="border px-2 py-1 bg-muted text-left font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.sample.map((row, i) => (
                        <tr key={i}>
                          {preview.headers.map((h) => (
                            <td key={h} className="border px-2 py-1 max-w-[150px] truncate">{row[h] || ""}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={reset}>
                  {t("buttons.back")}
                </Button>
                <Button
                  size="sm"
                  disabled={preview.valid_rows === 0 || importMutation.isPending}
                  onClick={() => importMutation.mutate()}
                >
                  <Upload className="h-4 w-4 mr-1" />
                  {importMutation.isPending
                    ? t("buttons.loading")
                    : `${t("export.import_btn")} ${preview.valid_rows} ${t("export.records")}`}
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Done */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">{t("export.import_success")}</span>
              </div>
              <Button size="sm" variant="outline" onClick={reset}>
                {t("export.import_another")}
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
