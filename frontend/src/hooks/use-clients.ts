import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listClients, createClient, updateClient, deleteClient } from "@/api/clients";
import type { ClientListParams, ClientCreate, ClientUpdate } from "@/types/client";

export function useClients(params?: ClientListParams) {
  return useQuery({
    queryKey: ["clients", params],
    queryFn: () => listClients(params),
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ClientCreate) => createClient(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

export function useUpdateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ClientUpdate }) => updateClient(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteClient(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
