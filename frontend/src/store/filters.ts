"use client";

import { create } from "zustand";

export interface OpportunityFilters {
  search?: string;
  status?: string[];
  category?: string[];
  region?: string;
  source_type?: string[];
  budget_min?: number;
  budget_max?: number;
  score_min?: number;
  deadline_before?: string;
  deadline_after?: string;
  assigned_to_id?: number;
  is_duplicate?: boolean;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

interface FiltersState {
  filters: OpportunityFilters;
  page: number;
  perPage: number;
  
  // Actions
  setFilters: (filters: Partial<OpportunityFilters>) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  setPerPage: (perPage: number) => void;
  setBudgetRange: (min?: number, max?: number) => void;
}

const defaultFilters: OpportunityFilters = {
  sort_by: "score",
  sort_order: "desc",
  is_duplicate: false,
};

export const useFiltersStore = create<FiltersState>()((set) => ({
  filters: defaultFilters,
  page: 1,
  perPage: 25,

  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
      page: 1, // Reset page when filters change
    })),

  resetFilters: () =>
    set({ filters: defaultFilters, page: 1 }),

  setPage: (page) => set({ page }),

  setPerPage: (perPage) => set({ perPage, page: 1 }),

  setBudgetRange: (min, max) =>
    set((state) => ({
      filters: {
        ...state.filters,
        budget_min: min,
        budget_max: max,
      },
      page: 1,
    })),
}));
