import { useMemo, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowLeft,
  Download,
  RefreshCw,
  Trash2,
  Pencil,
  Mail,
} from "lucide-react";

import { Header } from "@/components/layout/header";
import { StatusBadge } from "@/components/document-editor/status-badge";
import { LineEditor, calcLineSubtotal, type LineRow } from "@/components/document-editor/line-editor";
import { TotalsPanel } from "@/components/document-editor/totals-panel";
import { ConfirmDialog } from "@/components/forms/confirm-dialog";
import { Badge } from "@/components/ui/badge";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Spinner } from "@/components/common/loading";

import {
  useDocument,
  useUpdateDocument,
  useDeleteDocument,
  useChangeStatus,
  useConvertDocument,
} from "@/hooks/use-documents";
import { useClients } from "@/hooks/use-clients";
import { useProducts } from "@/hooks/use-products";
import { downloadDocumentPdf, getEmailStatus, sendDocumentEmail } from "@/api/documents";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  DOC_TYPES,
  DOC_STATUSES,
  STATUS_TRANSITIONS,
  TYPE_I18N_MAP,
  TAX_RATE,
} from "@/lib/constants";

// Map status transitions to i18n action keys
const STATUS_ACTION_MAP: Record<string, string> = {
  [DOC_STATUSES.NOT_SENT]: "send",
  [DOC_STATUSES.SENT]: "mark_sent",
  [DOC_STATUSES.ACCEPTED]: "accept",
  [DOC_STATUSES.REJECTED]: "reject",
  [DOC_STATUSES.PAID]: "mark_paid",
  [DOC_STATUSES.PARTIALLY_PAID]: "partial_payment",
  [DOC_STATUSES.CANCELLED]: "cancel",
};

export default function DocumentDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: doc, isLoading } = useDocument(id);
  const { data: clientsData } = useClients({ limit: 500 });
  const { data: productsData } = useProducts({ limit: 500 });

  const changeStatus = useChangeStatus();
  const convertMutation = useConvertDocument();
  const updateMutation = useUpdateDocument();
  const deleteMutation = useDeleteDocument();

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editClientId, setEditClientId] = useState("");
  const [editDueDate, setEditDueDate] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editInternalNotes, setEditInternalNotes] = useState("");
  const [editLines, setEditLines] = useState<LineRow[]>([]);
  const [downloading, setDownloading] = useState(false);
  const [emailOpen, setEmailOpen] = useState(false);
  const [emailTo, setEmailTo] = useState("");
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailConfigured, setEmailConfigured] = useState<boolean | null>(null);

  const clients = clientsData?.items || [];
  const products = productsData?.items || [];

  useEffect(() => {
    getEmailStatus().then((s) => setEmailConfigured(s.configured)).catch(() => setEmailConfigured(false));
  }, []);

  const openEmailDialog = () => {
    // Pre-fill recipient with client email
    const client = clients.find((c) => c.id === doc?.client_id);
    setEmailTo(client?.email || "");
    setEmailOpen(true);
  };

  const onSendEmail = async () => {
    if (!doc || !emailTo) return;
    setSendingEmail(true);
    try {
      await sendDocumentEmail(doc.id, emailTo);
      toast.success(t("documents.actions.email_sent"));
      setEmailOpen(false);
    } catch {
      toast.error(t("common.error"));
    } finally {
      setSendingEmail(false);
    }
  };

  const isDraft = doc?.status === DOC_STATUSES.DRAFT;
  const isQuote = doc?.type === DOC_TYPES.QUOTE;
  const canConvert =
    isQuote &&
    (doc?.status === DOC_STATUSES.ACCEPTED || doc?.status === DOC_STATUSES.SENT);

  const nextStatuses = doc ? STATUS_TRANSITIONS[doc.status] || [] : [];

  const startEditing = () => {
    if (!doc) return;
    setEditClientId(doc.client_id);
    setEditDueDate(doc.due_date ? doc.due_date.split("T")[0] ?? "" : "");
    setEditNotes(doc.notes || "");
    setEditInternalNotes(doc.internal_notes || "");
    setEditLines(
      doc.lines.map((l) => ({
        line_type: l.line_type,
        product_id: l.product_id || "",
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        discount_percent: l.discount_percent,
      }))
    );
    setEditing(true);
  };

  const editSubtotal = useMemo(
    () => editLines.reduce((sum, l) => sum + calcLineSubtotal(l), 0),
    [editLines]
  );

  const saveEdit = async () => {
    if (!doc) return;
    try {
      await updateMutation.mutateAsync({
        id: doc.id,
        data: {
          client_id: editClientId,
          due_date: editDueDate ? new Date(editDueDate).toISOString() : undefined,
          notes: editNotes || undefined,
          internal_notes: editInternalNotes || undefined,
          lines: editLines
            .filter((l) => l.description)
            .map((l) => ({
              line_type: l.product_id ? "product" : "text",
              product_id: l.product_id || undefined,
              description: l.description,
              quantity: l.quantity,
              unit_price: l.unit_price,
              discount_percent: l.discount_percent,
            })),
        },
      });
      toast.success(t("documents.updated"));
      setEditing(false);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onChangeStatus = async (newStatus: string) => {
    if (!doc) return;
    try {
      await changeStatus.mutateAsync({ id: doc.id, data: { new_status: newStatus } });
      toast.success(t("documents.updated"));
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onConvert = async (targetType: string) => {
    if (!doc) return;
    try {
      const newDoc = await convertMutation.mutateAsync({
        id: doc.id,
        targetType,
      });
      toast.success(t("documents.created"));
      navigate(`/documents/${newDoc.id}`);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onDelete = async () => {
    if (!doc) return;
    try {
      await deleteMutation.mutateAsync(doc.id);
      toast.success(t("documents.deleted"));
      navigate("/documents");
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onDownloadPdf = async () => {
    if (!doc) return;
    setDownloading(true);
    try {
      await downloadDocumentPdf(doc.id, doc.code);
    } catch {
      toast.error(t("common.error"));
    } finally {
      setDownloading(false);
    }
  };

  if (isLoading) {
    return (
      <>
        <Header title={t("documents.title")} />
        <div className="flex items-center justify-center p-12">
          <Spinner className="h-8 w-8" />
        </div>
      </>
    );
  }

  if (!doc) {
    return (
      <>
        <Header title={t("documents.title")} />
        <div className="p-6 text-center text-muted-foreground">
          {t("common.no_results")}
        </div>
      </>
    );
  }

  const clientName = clients.find((c) => c.id === doc.client_id)?.name || doc.client_id;

  // --- EDIT MODE ---
  if (editing) {
    return (
      <>
        <Header title={t("documents.edit")} />
        <div className="p-4 md:p-6 space-y-6 max-w-5xl">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>{t("documents.client")} *</Label>
              <Select value={editClientId} onValueChange={setEditClientId}>
                <SelectTrigger>
                  <SelectValue />
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
              <Label>{t("documents.date")} (vto.)</Label>
              <Input
                type="date"
                value={editDueDate}
                onChange={(e) => setEditDueDate(e.target.value)}
              />
            </div>
          </div>

          <LineEditor
            lines={editLines}
            onChange={setEditLines}
            products={products}
          />

          <TotalsPanel
            subtotal={editSubtotal}
            taxAmount={editSubtotal * TAX_RATE}
            total={editSubtotal + editSubtotal * TAX_RATE}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t("documents.notes")}</Label>
              <Textarea
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>Notas internas</Label>
              <Textarea
                value={editInternalNotes}
                onChange={(e) => setEditInternalNotes(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t">
            <Button variant="outline" onClick={() => setEditing(false)}>
              {t("buttons.cancel")}
            </Button>
            <Button
              onClick={saveEdit}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? t("buttons.loading") : t("buttons.save")}
            </Button>
          </div>
        </div>
      </>
    );
  }

  // --- VIEW MODE ---
  return (
    <>
      <Header title={doc.code} />
      <div className="p-4 md:p-6 space-y-6 max-w-5xl">
        {/* Back + actions bar */}
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate("/documents")}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            {t("buttons.back")}
          </Button>
          <div className="flex-1" />

          {isDraft && (
            <Button variant="outline" size="sm" onClick={startEditing}>
              <Pencil className="h-4 w-4 mr-1" />
              {t("buttons.edit")}
            </Button>
          )}

          <Button variant="outline" size="sm" onClick={onDownloadPdf} disabled={downloading}>
            <Download className="h-4 w-4 mr-1" />
            {downloading ? t("buttons.loading") : t("documents.actions.download_pdf")}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={openEmailDialog}
            disabled={emailConfigured === false}
            title={emailConfigured === false ? t("documents.actions.email_not_configured") : ""}
          >
            <Mail className="h-4 w-4 mr-1" />
            {t("documents.actions.send_email")}
          </Button>

          {isDraft && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setDeleteOpen(true)}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              {t("buttons.delete")}
            </Button>
          )}
        </div>

        {/* Document info card */}
        <div className="rounded-lg border p-4 md:p-6 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant={doc.type === DOC_TYPES.INVOICE ? "default" : doc.type === DOC_TYPES.DELIVERY_NOTE ? "secondary" : "outline"}>
              {t(`documents.types.${TYPE_I18N_MAP[doc.type]}`)}
            </Badge>
            <StatusBadge status={doc.status} />
            <span className="text-lg font-semibold">{doc.code}</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground block">{t("documents.client")}</span>
              <span className="font-medium">{clientName}</span>
            </div>
            <div>
              <span className="text-muted-foreground block">{t("documents.date")}</span>
              <span>{formatDate(doc.issue_date)}</span>
            </div>
            {doc.due_date && (
              <div>
                <span className="text-muted-foreground block">Vencimiento</span>
                <span>{formatDate(doc.due_date)}</span>
              </div>
            )}
            <div>
              <span className="text-muted-foreground block">{t("documents.total")}</span>
              <span className="text-lg font-semibold">{formatCurrency(doc.total)}</span>
            </div>
          </div>

          {doc.notes && (
            <div className="text-sm">
              <span className="text-muted-foreground block">{t("documents.notes")}</span>
              <span>{doc.notes}</span>
            </div>
          )}
        </div>

        {/* Lines table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>{t("documents.lines.description")}</TableHead>
                <TableHead className="text-right">{t("documents.lines.quantity")}</TableHead>
                <TableHead className="text-right">{t("documents.lines.price")}</TableHead>
                <TableHead className="text-right hidden sm:table-cell">{t("documents.lines.discount")}</TableHead>
                <TableHead className="text-right">{t("documents.lines.line_total")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {doc.lines.map((line, i) => (
                <TableRow key={line.id}>
                  <TableCell className="text-muted-foreground">{i + 1}</TableCell>
                  <TableCell className="font-medium">{line.description}</TableCell>
                  <TableCell className="text-right">{line.quantity}</TableCell>
                  <TableCell className="text-right">{formatCurrency(line.unit_price)}</TableCell>
                  <TableCell className="text-right hidden sm:table-cell">{line.discount_percent}%</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(line.subtotal)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Totals */}
        <TotalsPanel
          subtotal={doc.subtotal}
          taxAmount={doc.tax_amount}
          total={doc.total}
        />

        {/* Status transitions */}
        {nextStatuses.length > 0 && (
          <div className="rounded-lg border p-4 space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">
              {t("common.actions")}
            </h3>
            <div className="flex flex-wrap gap-2">
              {nextStatuses.map((status) => (
                <Button
                  key={status}
                  size="sm"
                  variant={
                    status === DOC_STATUSES.CANCELLED || status === DOC_STATUSES.REJECTED
                      ? "destructive"
                      : status === DOC_STATUSES.PAID
                        ? "default"
                        : "outline"
                  }
                  onClick={() => onChangeStatus(status)}
                  disabled={changeStatus.isPending}
                >
                  {changeStatus.isPending && <RefreshCw className="h-3 w-3 mr-1 animate-spin" />}
                  {t(`documents.actions.${STATUS_ACTION_MAP[status] || status}`)}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Conversion */}
        {canConvert && (
          <div className="rounded-lg border p-4 space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">
              Convertir
            </h3>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => onConvert(DOC_TYPES.INVOICE)}
                disabled={convertMutation.isPending}
              >
                {t("documents.actions.convert_invoice")}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onConvert(DOC_TYPES.DELIVERY_NOTE)}
                disabled={convertMutation.isPending}
              >
                {t("documents.actions.convert_delivery")}
              </Button>
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("documents.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />

      {/* Email Dialog */}
      <Dialog open={emailOpen} onOpenChange={setEmailOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t("documents.actions.send_email")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {t("documents.actions.email_confirm")}
            </p>
            <div className="space-y-2">
              <Label>{t("documents.actions.email_recipient")}</Label>
              <Input
                type="email"
                value={emailTo}
                onChange={(e) => setEmailTo(e.target.value)}
                placeholder="email@example.com"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEmailOpen(false)}>
              {t("buttons.cancel")}
            </Button>
            <Button onClick={onSendEmail} disabled={sendingEmail || !emailTo}>
              <Mail className="h-4 w-4 mr-1" />
              {sendingEmail ? t("buttons.loading") : t("documents.actions.send_email")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
