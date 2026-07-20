import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/endpoints";

export function useDimensions() {
  const businessEntities = useQuery({ queryKey: ["dim-entities"], queryFn: endpoints.dimensions.businessEntities, staleTime: 5 * 60_000 });
  const departments = useQuery({ queryKey: ["dim-departments"], queryFn: endpoints.dimensions.departments, staleTime: 5 * 60_000 });
  const costCenters = useQuery({ queryKey: ["dim-cost-centers"], queryFn: endpoints.dimensions.costCenters, staleTime: 5 * 60_000 });
  const regions = useQuery({ queryKey: ["dim-regions"], queryFn: endpoints.dimensions.regions, staleTime: 5 * 60_000 });
  const categories = useQuery({ queryKey: ["dim-categories"], queryFn: endpoints.dimensions.categories, staleTime: 5 * 60_000 });
  const vendors = useQuery({ queryKey: ["dim-vendors"], queryFn: endpoints.vendors.list, staleTime: 5 * 60_000 });

  return { businessEntities, departments, costCenters, regions, categories, vendors };
}
