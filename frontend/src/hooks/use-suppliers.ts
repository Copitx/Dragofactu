import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listSuppliers, createSupplier, updateSupplier, deleteSupplier } from "@/api/suppliers";
import type { SupplierListParams, SupplierCreate, SupplierUpdate } from "@/types/supplier";

export function useSuppliers(params?: SupplierListParams) {
  return useQuery({
    queryKey: ["suppliers", params],
    queryFn: () => listSuppliers(params),
  });
}

export function useCreateSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SupplierCreate) => createSupplier(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

export function useUpdateSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SupplierUpdate }) => updateSupplier(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

export function useDeleteSupplier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteSupplier(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["suppliers"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
