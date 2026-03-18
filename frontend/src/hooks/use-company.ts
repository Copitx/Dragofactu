import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCompanySettings,
  updateCompanySettings,
  getCompanyEmailSettings,
  updateCompanyEmailSettings,
  testCompanyEmailSettings,
  type CompanySettingsUpdate,
  type CompanyEmailSettingsUpdate,
} from "@/api/company";

export function useCompanySettings() {
  return useQuery({
    queryKey: ["company", "settings"],
    queryFn: getCompanySettings,
  });
}

export function useUpdateCompanySettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CompanySettingsUpdate) => updateCompanySettings(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["company", "settings"] }),
  });
}

export function useCompanyEmailSettings() {
  return useQuery({
    queryKey: ["company", "email", "settings"],
    queryFn: getCompanyEmailSettings,
  });
}

export function useUpdateCompanyEmailSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CompanyEmailSettingsUpdate) => updateCompanyEmailSettings(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["company", "email", "settings"] });
      qc.invalidateQueries({ queryKey: ["documents", "email", "status"] });
    },
  });
}

export function useTestCompanyEmailSettings() {
  return useMutation({
    mutationFn: () => testCompanyEmailSettings(),
  });
}
