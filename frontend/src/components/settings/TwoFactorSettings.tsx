"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import {
  Shield,
  ShieldCheck,
  ShieldOff,
  QrCode,
  Key,
  Copy,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Smartphone,
  RefreshCw,
} from "lucide-react";

interface TwoFactorStatus {
  enabled: boolean;
  has_backup_codes: boolean;
}

interface SetupResponse {
  secret: string;
  qr_code: string;
  backup_codes: string[];
}

export function TwoFactorSettings() {
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [disableDialogOpen, setDisableDialogOpen] = useState(false);
  const [backupCodesDialogOpen, setBackupCodesDialogOpen] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [setupData, setSetupData] = useState<SetupResponse | null>(null);
  const [newBackupCodes, setNewBackupCodes] = useState<string[]>([]);
  const [copiedCodes, setCopiedCodes] = useState(false);
  
  const queryClient = useQueryClient();

  // Get 2FA status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["2fa-status"],
    queryFn: async () => {
      const response = await api.get("/auth/2fa/status");
      return response.data as TwoFactorStatus;
    },
  });

  // Setup 2FA mutation
  const setupMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post("/auth/2fa/setup");
      return response.data as SetupResponse;
    },
    onSuccess: (data) => {
      setSetupData(data);
    },
  });

  // Enable 2FA mutation
  const enableMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await api.post("/auth/2fa/enable", { code });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["2fa-status"] });
      setSetupDialogOpen(false);
      setSetupData(null);
      setVerificationCode("");
    },
  });

  // Disable 2FA mutation
  const disableMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await api.post("/auth/2fa/disable", { code });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["2fa-status"] });
      setDisableDialogOpen(false);
      setVerificationCode("");
    },
  });

  // Regenerate backup codes mutation
  const regenerateMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await api.post("/auth/2fa/regenerate-backup-codes", { code });
      return response.data;
    },
    onSuccess: (data) => {
      setNewBackupCodes(data.backup_codes);
      setVerificationCode("");
    },
  });

  const handleStartSetup = async () => {
    setSetupDialogOpen(true);
    await setupMutation.mutateAsync();
  };

  const handleEnableSubmit = async () => {
    if (verificationCode.length === 6) {
      await enableMutation.mutateAsync(verificationCode);
    }
  };

  const handleDisableSubmit = async () => {
    if (verificationCode.length === 6) {
      await disableMutation.mutateAsync(verificationCode);
    }
  };

  const handleCopyBackupCodes = () => {
    const codes = setupData?.backup_codes || newBackupCodes;
    navigator.clipboard.writeText(codes.join("\n"));
    setCopiedCodes(true);
    setTimeout(() => setCopiedCodes(false), 3000);
  };

  if (statusLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Authentification à deux facteurs (2FA)
          </CardTitle>
          <CardDescription>
            Ajoutez une couche de sécurité supplémentaire à votre compte
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status */}
          <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-3">
              {status?.enabled ? (
                <ShieldCheck className="h-8 w-8 text-green-600" />
              ) : (
                <ShieldOff className="h-8 w-8 text-muted-foreground" />
              )}
              <div>
                <p className="font-medium">
                  {status?.enabled ? "2FA activée" : "2FA désactivée"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {status?.enabled
                    ? "Votre compte est protégé"
                    : "Recommandé pour plus de sécurité"}
                </p>
              </div>
            </div>
            <Badge variant={status?.enabled ? "default" : "secondary"}>
              {status?.enabled ? "Activée" : "Désactivée"}
            </Badge>
          </div>

          {/* Actions */}
          {status?.enabled ? (
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setBackupCodesDialogOpen(true)}
              >
                <Key className="h-4 w-4 mr-2" />
                Gérer les codes de secours
              </Button>
              <Button
                variant="destructive"
                className="w-full"
                onClick={() => setDisableDialogOpen(true)}
              >
                <ShieldOff className="h-4 w-4 mr-2" />
                Désactiver la 2FA
              </Button>
            </div>
          ) : (
            <Button className="w-full" onClick={handleStartSetup}>
              <ShieldCheck className="h-4 w-4 mr-2" />
              Activer la 2FA
            </Button>
          )}

          {/* Info */}
          <Alert>
            <Smartphone className="h-4 w-4" />
            <AlertDescription>
              Utilisez une application comme Google Authenticator, Authy ou 1Password
              pour scanner le code QR et générer des codes de vérification.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Setup Dialog */}
      <Dialog open={setupDialogOpen} onOpenChange={setSetupDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Configurer la 2FA</DialogTitle>
            <DialogDescription>
              Scannez le code QR avec votre application d'authentification
            </DialogDescription>
          </DialogHeader>

          {setupMutation.isPending ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : setupData ? (
            <div className="space-y-4">
              {/* QR Code */}
              <div className="flex justify-center">
                <div className="p-4 bg-white rounded-lg">
                  <img
                    src={`data:image/png;base64,${setupData.qr_code}`}
                    alt="QR Code 2FA"
                    className="w-48 h-48"
                  />
                </div>
              </div>

              {/* Manual code */}
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">
                  Ou entrez ce code manuellement:
                </p>
                <code className="px-3 py-1 bg-muted rounded text-sm font-mono">
                  {setupData.secret}
                </code>
              </div>

              {/* Backup codes */}
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-sm">Codes de secours</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCopyBackupCodes}
                  >
                    {copiedCodes ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-1 text-xs font-mono">
                  {setupData.backup_codes.map((code, i) => (
                    <span key={i} className="p-1 bg-background rounded">
                      {code}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  ⚠️ Sauvegardez ces codes en lieu sûr
                </p>
              </div>

              {/* Verification */}
              <div className="space-y-2">
                <p className="text-sm">
                  Entrez le code à 6 chiffres de votre application:
                </p>
                <Input
                  type="text"
                  placeholder="000000"
                  maxLength={6}
                  value={verificationCode}
                  onChange={(e) =>
                    setVerificationCode(e.target.value.replace(/\D/g, ""))
                  }
                  className="text-center text-2xl tracking-widest font-mono"
                />
              </div>

              {enableMutation.isError && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Code invalide. Vérifiez et réessayez.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          ) : null}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setSetupDialogOpen(false);
                setSetupData(null);
                setVerificationCode("");
              }}
            >
              Annuler
            </Button>
            <Button
              onClick={handleEnableSubmit}
              disabled={verificationCode.length !== 6 || enableMutation.isPending}
            >
              {enableMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              Activer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Disable Dialog */}
      <Dialog open={disableDialogOpen} onOpenChange={setDisableDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Désactiver la 2FA</DialogTitle>
            <DialogDescription>
              Entrez un code de vérification pour confirmer
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Attention: Désactiver la 2FA réduit la sécurité de votre compte.
              </AlertDescription>
            </Alert>

            <Input
              type="text"
              placeholder="Code à 6 chiffres"
              maxLength={6}
              value={verificationCode}
              onChange={(e) =>
                setVerificationCode(e.target.value.replace(/\D/g, ""))
              }
              className="text-center text-2xl tracking-widest font-mono"
            />

            {disableMutation.isError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>Code invalide.</AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDisableDialogOpen(false);
                setVerificationCode("");
              }}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              onClick={handleDisableSubmit}
              disabled={verificationCode.length !== 6 || disableMutation.isPending}
            >
              {disableMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : null}
              Désactiver
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Backup Codes Dialog */}
      <Dialog open={backupCodesDialogOpen} onOpenChange={setBackupCodesDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Codes de secours</DialogTitle>
            <DialogDescription>
              Régénérer de nouveaux codes de secours
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {newBackupCodes.length > 0 ? (
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-sm">Nouveaux codes</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCopyBackupCodes}
                  >
                    {copiedCodes ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-1 text-xs font-mono">
                  {newBackupCodes.map((code, i) => (
                    <span key={i} className="p-1 bg-background rounded">
                      {code}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  ⚠️ Sauvegardez ces codes en lieu sûr
                </p>
              </div>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  Entrez votre code 2FA actuel pour générer de nouveaux codes de secours.
                  Les anciens codes seront invalidés.
                </p>
                <Input
                  type="text"
                  placeholder="Code à 6 chiffres"
                  maxLength={6}
                  value={verificationCode}
                  onChange={(e) =>
                    setVerificationCode(e.target.value.replace(/\D/g, ""))
                  }
                  className="text-center text-2xl tracking-widest font-mono"
                />
              </>
            )}

            {regenerateMutation.isError && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>Code invalide.</AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setBackupCodesDialogOpen(false);
                setVerificationCode("");
                setNewBackupCodes([]);
              }}
            >
              Fermer
            </Button>
            {newBackupCodes.length === 0 && (
              <Button
                onClick={() => regenerateMutation.mutate(verificationCode)}
                disabled={verificationCode.length !== 6 || regenerateMutation.isPending}
              >
                {regenerateMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Régénérer
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
