"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, Clock, LogOut, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function NoWorkspacePage() {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    // Get user info from token or localStorage
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    
    // Decode JWT to get email (simple base64 decode of payload)
    try {
      const payload = token.split(".")[1];
      const decoded = JSON.parse(atob(payload));
      setUserEmail(decoded.email || decoded.sub);
    } catch {
      // Ignore decode errors
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <Card className="max-w-md w-full bg-white/10 backdrop-blur-lg border-white/20 text-white">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center">
            <Clock className="h-8 w-8 text-yellow-400" />
          </div>
          <CardTitle className="text-2xl">En attente d'invitation</CardTitle>
          <CardDescription className="text-gray-300">
            Votre compte a été créé avec succès
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-white/5 rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-purple-400" />
              <div>
                <p className="text-sm text-gray-400">Connecté en tant que</p>
                <p className="font-medium">{userEmail || "..."}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-purple-400" />
              <div>
                <p className="text-sm text-gray-400">Workspace</p>
                <p className="font-medium text-yellow-400">Aucun accès</p>
              </div>
            </div>
          </div>

          <div className="text-center space-y-2">
            <p className="text-gray-300">
              Vous n'êtes pas encore membre d'un espace de travail.
            </p>
            <p className="text-sm text-gray-400">
              Demandez à un administrateur de vous inviter, ou contactez le support.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <Button
              variant="outline"
              className="w-full border-white/20 hover:bg-white/10"
              onClick={() => window.location.reload()}
            >
              <Clock className="h-4 w-4 mr-2" />
              Vérifier à nouveau
            </Button>
            <Button
              variant="ghost"
              className="w-full text-gray-400 hover:text-white hover:bg-white/10"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Se déconnecter
            </Button>
          </div>

          <p className="text-xs text-center text-gray-500">
            Besoin d'aide ? Contactez{" "}
            <a href="mailto:contact@radarapp.fr" className="text-purple-400 hover:underline">
              contact@radarapp.fr
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
