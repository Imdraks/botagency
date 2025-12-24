"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface BackgroundTask {
  id: string;
  type: "collection" | "ingestion" | "enrichment";
  title: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  result?: {
    briefId?: string;
    documentCount?: number;
    contactCount?: number;
    error?: string;
  };
  startedAt: string;
  completedAt?: string;
}

interface TasksState {
  tasks: BackgroundTask[];
  addTask: (task: BackgroundTask) => void;
  updateTask: (id: string, updates: Partial<BackgroundTask>) => void;
  removeTask: (id: string) => void;
  clearCompletedTasks: () => void;
  getActiveTasks: () => BackgroundTask[];
  getRecentTasks: () => BackgroundTask[];
}

export const useTasksStore = create<TasksState>()(
  persist(
    (set, get) => ({
      tasks: [],
      
      addTask: (task) => {
        set((state) => ({
          tasks: [task, ...state.tasks].slice(0, 50) // Keep last 50 tasks
        }));
      },
      
      updateTask: (id, updates) => {
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          )
        }));
      },
      
      removeTask: (id) => {
        set((state) => ({
          tasks: state.tasks.filter((t) => t.id !== id)
        }));
      },
      
      clearCompletedTasks: () => {
        set((state) => ({
          tasks: state.tasks.filter((t) => t.status === "pending" || t.status === "running")
        }));
      },
      
      getActiveTasks: () => {
        return get().tasks.filter((t) => t.status === "pending" || t.status === "running");
      },
      
      getRecentTasks: () => {
        return get().tasks.slice(0, 10);
      },
    }),
    {
      name: "radar-tasks",
    }
  )
);
