"use client";

import { useRouter } from "next/navigation";
import { Lock, ArrowLeft, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";

interface ModuleNotActivatedProps {
  moduleName?: string;
  moduleId?: string;
}

export default function ModuleNotActivated({ 
  moduleName = "Ce module",
  moduleId = ""
}: ModuleNotActivatedProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const isAdmin = user?.role === "admin" || user?.is_superuser === true;

  const handleGoToSettings = () => {
    // Get current workspace ID
    const workspaceId = localStorage.getItem("current_workspace_id");
    if (workspaceId) {
      router.push(`/workspaces/${workspaceId}`);
    } else {
      router.push("/workspaces");
    }
  };

  const handleGoHome = () => {
    router.push("/today");
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center">
        {/* Icon */}
        <div className="mx-auto w-20 h-20 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center mb-6">
          <Lock className="h-10 w-10 text-gray-400 dark:text-gray-500" />
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          Module non activé
        </h1>

        {/* Message */}
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          <span className="font-medium">{moduleName}</span> n&apos;est pas activé pour ce workspace.
        </p>

        {/* Divider */}
        <div className="h-px bg-gray-200 dark:bg-slate-700 w-full mb-8" />

        {/* Actions based on role */}
        {isAdmin ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              En tant qu&apos;administrateur, vous pouvez activer ce module dans les paramètres du workspace.
            </p>
            <Button
              onClick={handleGoToSettings}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white"
            >
              <Settings className="h-4 w-4 mr-2" />
              Activer dans Paramètres Workspace
            </Button>
            <Button
              variant="outline"
              onClick={handleGoHome}
              className="w-full"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour à l&apos;accueil
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                💡 Contactez un administrateur du workspace pour activer ce module.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={handleGoHome}
              className="w-full"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour à l&apos;accueil
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
