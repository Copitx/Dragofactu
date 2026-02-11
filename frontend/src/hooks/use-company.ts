import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCompanySettings, updateCompanySettings, type CompanySettingsUpdate } from "@/api/company";

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
