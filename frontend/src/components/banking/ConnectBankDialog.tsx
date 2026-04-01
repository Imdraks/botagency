"use client";

import { useState } from "react";
import { Landmark, Plus, Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useBankingStore } from "@/store/bankingStore";
import { cn } from "@/lib/utils";

// ============================================================================
// FRENCH BANK CATALOG
// ============================================================================

interface BankTemplate {
  name: string;
  code: string;
  logo?: string;
  country: string;
}

const FRENCH_BANKS: BankTemplate[] = [
  { name: "Crédit Agricole", code: "AGRIFRPP", country: "FR" },
  { name: "BNP Paribas", code: "BNPAFRPP", country: "FR" },
  { name: "Société Générale", code: "SOGEFRPP", country: "FR" },
  { name: "Crédit Mutuel", code: "CMCIFRPP", country: "FR" },
  { name: "La Banque Postale", code: "PSSTFRPP", country: "FR" },
  { name: "CIC", code: "CMCIFRPP", country: "FR" },
  { name: "Caisse d'Épargne", code: "CEPAFRPP", country: "FR" },
  { name: "Banque Populaire", code: "BPCEFRPP", country: "FR" },
  { name: "LCL", code: "CRLYFRPP", country: "FR" },
  { name: "HSBC France", code: "CCFRFRPP", country: "FR" },
  { name: "Boursorama", code: "BOUSFRPP", country: "FR" },
  { name: "ING", code: "INGBFRPP", country: "FR" },
  { name: "Fortuneo", code: "FTNOFRP1", country: "FR" },
  { name: "Hello bank!", code: "BNPAFRPP", country: "FR" },
  { name: "N26", code: "NTSBDEB1", country: "DE" },
  { name: "Revolut", code: "REVOLT21", country: "GB" },
  { name: "Qonto", code: "QNTOFRP1", country: "FR" },
  { name: "Shine", code: "SABOROBU", country: "FR" },
];

// ============================================================================
// DIALOG COMPONENT
// ============================================================================

interface ConnectBankDialogProps {
  trigger?: React.ReactNode;
}

export function ConnectBankDialog({ trigger }: ConnectBankDialogProps) {
  const { createConnection } = useBankingStore();
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<"select" | "custom">("select");
  const [search, setSearch] = useState("");
  const [selectedBank, setSelectedBank] = useState<BankTemplate | null>(null);
  const [customName, setCustomName] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const filteredBanks = FRENCH_BANKS.filter((b) =>
    b.name.toLowerCase().includes(search.toLowerCase()),
  );

  const handleSelectBank = async (bank: BankTemplate) => {
    setIsCreating(true);
    const result = await createConnection({
      bank_name: bank.name,
      bank_code: bank.code,
      bank_country: bank.country,
    });
    setIsCreating(false);
    if (result) {
      resetAndClose();
    }
  };

  const handleCustomBank = async () => {
    if (!customName.trim()) return;
    setIsCreating(true);
    const result = await createConnection({
      bank_name: customName.trim(),
      bank_code: customCode.trim() || undefined,
      bank_country: "FR",
    });
    setIsCreating(false);
    if (result) {
      resetAndClose();
    }
  };

  const resetAndClose = () => {
    setOpen(false);
    setStep("select");
    setSearch("");
    setSelectedBank(null);
    setCustomName("");
    setCustomCode("");
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) resetAndClose(); }}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Connecter une banque
          </Button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Landmark className="h-5 w-5 text-purple-600" />
            Connecter une banque
          </DialogTitle>
          <DialogDescription>
            Sélectionnez votre établissement bancaire ou ajoutez-le manuellement.
          </DialogDescription>
        </DialogHeader>

        {step === "select" && (
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Rechercher une banque…"
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoFocus
              />
            </div>

            {/* Bank list */}
            <div className="max-h-[300px] overflow-y-auto space-y-1 pr-1">
              {filteredBanks.map((bank) => (
                <button
                  key={bank.code + bank.name}
                  onClick={() => handleSelectBank(bank)}
                  disabled={isCreating}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors",
                    "hover:bg-purple-50 dark:hover:bg-purple-900/20",
                    "text-gray-700 dark:text-gray-300",
                    isCreating && "opacity-50 cursor-not-allowed",
                  )}
                >
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 dark:from-slate-700 dark:to-slate-800 flex items-center justify-center flex-shrink-0">
                    <Landmark className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{bank.name}</p>
                    <p className="text-xs text-gray-400">{bank.code}</p>
                  </div>
                </button>
              ))}

              {filteredBanks.length === 0 && (
                <div className="text-center py-6 text-sm text-gray-400">
                  Aucune banque trouvée
                </div>
              )}
            </div>

            {/* Custom bank button */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setStep("custom")}
            >
              <Plus className="h-4 w-4 mr-2" />
              Ajouter manuellement
            </Button>
          </div>
        )}

        {step === "custom" && (
          <div className="space-y-4">
            <div>
              <Label>Nom de la banque *</Label>
              <Input
                placeholder="Ex: Ma Banque Régionale"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <Label>Code BIC/SWIFT (optionnel)</Label>
              <Input
                placeholder="Ex: AGRIFRPP"
                value={customCode}
                onChange={(e) => setCustomCode(e.target.value)}
              />
            </div>

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setStep("select")}>
                Retour
              </Button>
              <Button
                onClick={handleCustomBank}
                disabled={!customName.trim() || isCreating}
              >
                {isCreating ? "Création…" : "Ajouter"}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
