"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface Confetti {
  id: number;
  x: number;
  color: string;
  delay: number;
  duration: number;
}

const COLORS = [
  "#3B82F6", // blue
  "#8B5CF6", // purple
  "#EC4899", // pink
  "#10B981", // green
  "#F59E0B", // amber
  "#EF4444", // red
];

interface ConfettiCelebrationProps {
  isActive: boolean;
  duration?: number;
  onComplete?: () => void;
}

export function ConfettiCelebration({
  isActive,
  duration = 3000,
  onComplete,
}: ConfettiCelebrationProps) {
  const [confetti, setConfetti] = useState<Confetti[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isActive) {
      setConfetti([]);
      return;
    }

    // Generate confetti pieces
    const pieces: Confetti[] = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      delay: Math.random() * 0.5,
      duration: 2 + Math.random() * 2,
    }));

    setConfetti(pieces);

    // Clean up after animation
    const timer = setTimeout(() => {
      setConfetti([]);
      onComplete?.();
    }, duration);

    return () => clearTimeout(timer);
  }, [isActive, duration, onComplete]);

  if (!mounted || confetti.length === 0) return null;

  return createPortal(
    <div className="fixed inset-0 pointer-events-none z-[10000] overflow-hidden">
      {confetti.map((piece) => (
        <div
          key={piece.id}
          className="absolute w-3 h-3 animate-confetti-fall"
          style={{
            left: `${piece.x}%`,
            top: "-20px",
            backgroundColor: piece.color,
            animationDelay: `${piece.delay}s`,
            animationDuration: `${piece.duration}s`,
            borderRadius: Math.random() > 0.5 ? "50%" : "0",
            transform: `rotate(${Math.random() * 360}deg)`,
          }}
        />
      ))}
    </div>,
    document.body
  );
}
