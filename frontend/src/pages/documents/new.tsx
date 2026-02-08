import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Header } from "@/components/layout/header";
import { LineEditor, calcLineSubtotal, type LineRow } from "@/components/document-editor/line-editor";
import { TotalsPanel } from "@/components/document-editor/totals-panel";
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

import { useCreateDocument } from "@/hooks/use-documents";
import { useClients } from "@/hooks/use-clients";
import { useProducts } from "@/hooks/use-products";
import { DOC_TYPES, TAX_RATE } from "@/lib/constants";
import type { DocumentCreate } from "@/types/document";

const defaultLine: LineRow = {
  line_type: "product",
  product_id: "",
  description: "",
  quantity: 1,
  unit_price: 0,
  discount_percent: 0,
};

export default function DocumentNewPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [docType, setDocType] = useState<string>(DOC_TYPES.INVOICE);
  const [clientId, setClientId] = useState("");
  const [issueDate, setIssueDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [internalNotes, setInternalNotes] = useState("");
  const [lines, setLines] = useState<LineRow[]>([{ ...defaultLine }]);

  const { data: clientsData } = useClients({ limit: 500 });
  const { data: productsData } = useProducts({ limit: 500 });
  const createMutation = useCreateDocument();

  const clients = clientsData?.items || [];
  const products = productsData?.items || [];

  const subtotal = useMemo(
    () => lines.reduce((sum, line) => sum + calcLineSubtotal(line), 0),
    [lines]
  );
  const taxAmount = subtotal * TAX_RATE;
  const total = subtotal + taxAmount;

  const canSubmit = clientId && lines.length > 0 && lines.some((l) => l.description);

  const onSubmit = async () => {
    const payload: DocumentCreate = {
      type: docType,
      client_id: clientId,
      issue_date: new Date(issueDate).toISOString(),
      due_date: dueDate.length > 0 ? new Date(dueDate).toISOString() : undefined,
      notes: notes || undefined,
      internal_notes: internalNotes || undefined,
      lines: lines
        .filter((l) => l.description)
        .map((l) => ({
          line_type: l.product_id ? "product" : "text",
          product_id: l.product_id || undefined,
          description: l.description,
          quantity: l.quantity,
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
        })),
    };

    try {
      const doc = await createMutation.mutateAsync(payload);
      toast.success(t("documents.created"));
      navigate(`/documents/${doc.id}`);
    } catch {
      toast.error(t("common.error"));
    }
  };

  return (
    <>
      <Header title={t("documents.new")} />
      <div className="p-4 md:p-6 space-y-6 max-w-5xl">
        {/* Document header */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-2">
            <Label>{t("documents.type")} *</Label>
            <Select value={docType} onValueChange={setDocType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={DOC_TYPES.QUOTE}>
                  {t("documents.types.QUOTE")}
                </SelectItem>
                <SelectItem value={DOC_TYPES.DELIVERY_NOTE}>
                  {t("documents.types.DELIVERY_NOTE")}
                </SelectItem>
                <SelectItem value={DOC_TYPES.INVOICE}>
                  {t("documents.types.INVOICE")}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t("documents.client")} *</Label>
            <Select value={clientId} onValueChange={setClientId}>
              <SelectTrigger>
                <SelectValue placeholder={t("documents.client")} />
              </SelectTrigger>
              <SelectContent>
                {clients.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.code} - {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t("documents.date")} *</Label>
            <Input
              type="date"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>{t("documents.date")} (vto.)</Label>
            <Input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>
        </div>

        {/* Line editor */}
        <div className="space-y-2">
          <Label className="text-base font-semibold">
            {t("documents.lines.product")}s
          </Label>
          <LineEditor
            lines={lines}
            onChange={setLines}
            products={products}
          />
        </div>

        {/* Totals */}
        <TotalsPanel subtotal={subtotal} taxAmount={taxAmount} total={total} />

        {/* Notes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>{t("documents.notes")}</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Notas internas</Label>
            <Textarea
              value={internalNotes}
              onChange={(e) => setInternalNotes(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t">
          <Button variant="outline" onClick={() => navigate("/documents")}>
            {t("buttons.cancel")}
          </Button>
          <Button
            onClick={onSubmit}
            disabled={!canSubmit || createMutation.isPending}
          >
            {createMutation.isPending ? t("buttons.loading") : t("buttons.save")}
          </Button>
        </div>
      </div>
    </>
  );
}
