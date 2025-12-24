"use client";

import { KanbanBoard } from "@/components/opportunities/KanbanBoard";
import { AppLayout } from "@/components/layout";
import { ProtectedRoute } from "@/components/layout";

export default function KanbanPage() {
  return (
    <ProtectedRoute>
      <AppLayout>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Vue Kanban</h1>
            <p className="text-muted-foreground">
              Gérez vos opportunités par glisser-déposer
            </p>
          </div>

          <KanbanBoard />
        </div>
      </AppLayout>
    </ProtectedRoute>
  );
}
