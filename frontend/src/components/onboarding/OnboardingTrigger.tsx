"use client";

import { HelpCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useOnboarding } from "./OnboardingContext";

interface OnboardingTriggerProps {
  variant?: "icon" | "button" | "menu";
  className?: string;
}

export function OnboardingTrigger({ variant = "icon", className }: OnboardingTriggerProps) {
  const { startOnboarding, hasCompletedOnboarding, resetOnboarding } = useOnboarding();

  const handleClick = () => {
    if (hasCompletedOnboarding) {
      resetOnboarding();
    }
    startOnboarding();
  };

  if (variant === "menu") {
    return (
      <button
        onClick={handleClick}
        className="flex w-full items-center px-2 py-1.5 text-sm hover:bg-accent rounded-sm cursor-pointer"
      >
        {hasCompletedOnboarding ? (
          <>
            <RotateCcw className="mr-2 h-4 w-4" />
            Revoir le tutoriel
          </>
        ) : (
          <>
            <HelpCircle className="mr-2 h-4 w-4" />
            Démarrer le tutoriel
          </>
        )}
      </button>
    );
  }

  if (variant === "button") {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={handleClick}
        className={className}
      >
        {hasCompletedOnboarding ? (
          <>
            <RotateCcw className="mr-2 h-4 w-4" />
            Revoir le tutoriel
          </>
        ) : (
          <>
            <HelpCircle className="mr-2 h-4 w-4" />
            Aide
          </>
        )}
      </Button>
    );
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClick}
            className={className}
          >
            <HelpCircle className="h-5 w-5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {hasCompletedOnboarding ? "Revoir le tutoriel" : "Aide & tutoriel"}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
