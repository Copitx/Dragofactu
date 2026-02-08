import { z } from "zod";

export const clientSchema = z.object({
  code: z.string().min(1, "required").max(20),
  name: z.string().min(1, "required").max(200),
  tax_id: z.string().max(50).optional().or(z.literal("")),
  address: z.string().max(500).optional().or(z.literal("")),
  city: z.string().max(100).optional().or(z.literal("")),
  postal_code: z.string().max(20).optional().or(z.literal("")),
  province: z.string().max(100).optional().or(z.literal("")),
  country: z.string().max(100).optional().or(z.literal("")),
  phone: z.string().max(50).optional().or(z.literal("")),
  email: z.string().email().optional().or(z.literal("")),
  website: z.string().max(200).optional().or(z.literal("")),
  notes: z.string().max(2000).optional().or(z.literal("")),
});

export type ClientFormData = z.infer<typeof clientSchema>;

export const productSchema = z.object({
  code: z.string().min(1, "required").max(50),
  name: z.string().min(1, "required").max(200),
  description: z.string().max(2000).optional().or(z.literal("")),
  category: z.string().max(100).optional().or(z.literal("")),
  purchase_price: z.coerce.number().min(0).default(0),
  sale_price: z.coerce.number().min(0).default(0),
  current_stock: z.coerce.number().int().min(0).default(0),
  minimum_stock: z.coerce.number().int().min(0).default(0),
  stock_unit: z.string().max(20).default("unidades"),
  supplier_id: z.string().optional().or(z.literal("")),
});

export type ProductFormData = z.infer<typeof productSchema>;

export const supplierSchema = z.object({
  code: z.string().min(1, "required").max(20),
  name: z.string().min(1, "required").max(200),
  tax_id: z.string().max(50).optional().or(z.literal("")),
  address: z.string().max(500).optional().or(z.literal("")),
  city: z.string().max(100).optional().or(z.literal("")),
  postal_code: z.string().max(20).optional().or(z.literal("")),
  province: z.string().max(100).optional().or(z.literal("")),
  country: z.string().max(100).optional().or(z.literal("")),
  phone: z.string().max(50).optional().or(z.literal("")),
  email: z.string().email().optional().or(z.literal("")),
  website: z.string().max(200).optional().or(z.literal("")),
  notes: z.string().max(2000).optional().or(z.literal("")),
});

export type SupplierFormData = z.infer<typeof supplierSchema>;

export const stockAdjustmentSchema = z.object({
  quantity: z.coerce.number().int().refine((v) => v !== 0, "required"),
  reason: z.string().min(1, "required").max(500),
});

export type StockAdjustmentFormData = z.infer<typeof stockAdjustmentSchema>;

export const workerSchema = z.object({
  code: z.string().min(1, "required").max(20),
  first_name: z.string().min(1, "required").max(100),
  last_name: z.string().min(1, "required").max(100),
  phone: z.string().max(50).optional().or(z.literal("")),
  email: z.string().email().optional().or(z.literal("")),
  address: z.string().max(500).optional().or(z.literal("")),
  position: z.string().max(100).optional().or(z.literal("")),
  department: z.string().max(100).optional().or(z.literal("")),
  hire_date: z.string().optional().or(z.literal("")),
  salary: z.coerce.number().min(0).optional(),
});

export type WorkerFormData = z.infer<typeof workerSchema>;

export const courseSchema = z.object({
  name: z.string().min(1, "required").max(200),
  description: z.string().max(2000).optional().or(z.literal("")),
  provider: z.string().max(200).optional().or(z.literal("")),
  issue_date: z.string().optional().or(z.literal("")),
  expiration_date: z.string().optional().or(z.literal("")),
});

export type CourseFormData = z.infer<typeof courseSchema>;

export const diarySchema = z.object({
  title: z.string().min(1, "required").max(200),
  content: z.string().min(1, "required").max(10000),
  entry_date: z.string().min(1, "required"),
  tags: z.string().max(500).optional().or(z.literal("")),
  is_pinned: z.boolean().optional(),
});

export type DiaryFormData = z.infer<typeof diarySchema>;

export const reminderSchema = z.object({
  title: z.string().min(1, "required").max(200),
  description: z.string().max(2000).optional().or(z.literal("")),
  due_date: z.string().optional().or(z.literal("")),
  priority: z.string().default("normal"),
});

export type ReminderFormData = z.infer<typeof reminderSchema>;
