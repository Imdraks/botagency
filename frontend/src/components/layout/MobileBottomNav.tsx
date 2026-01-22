'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sun, 
  Inbox, 
  DollarSign, 
  FolderKanban, 
  LayoutGrid,
  Plus,
  X,
  Users,
  TrendingUp,
  Calendar,
  Settings
} from 'lucide-react';
import { cn } from '@/lib/utils';

const mobileNav = [
  { name: "Today", href: '/today', icon: Sun },
  { name: 'Inbox', href: '/inbox', icon: Inbox },
  { name: 'add', href: '#', icon: Plus, isAction: true },
  { name: 'Pipeline', href: '/pipeline', icon: DollarSign },
  { name: 'Cockpit', href: '/cockpit', icon: LayoutGrid },
];

const quickActions = [
  { name: 'Nouveau projet', href: '/projects/new', icon: FolderKanban, color: 'bg-purple-500' },
  { name: 'Nouveau client', href: '/clients/new', icon: Users, color: 'bg-blue-500' },
  { name: 'Nouveau deal', href: '/pipeline/new', icon: TrendingUp, color: 'bg-green-500' },
  { name: 'Calendrier', href: '/agency-calendar', icon: Calendar, color: 'bg-orange-500' },
  { name: 'Paramètres', href: '/settings', icon: Settings, color: 'bg-gray-500' },
];

export function MobileBottomNav() {
  const pathname = usePathname();
  const [showQuickActions, setShowQuickActions] = useState(false);

  return (
    <>
      {/* Quick Actions Overlay */}
      <AnimatePresence>
        {showQuickActions && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
              onClick={() => setShowQuickActions(false)}
            />
            
            {/* Actions Grid */}
            <motion.div
              initial={{ opacity: 0, y: 100 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 100 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="lg:hidden fixed bottom-20 left-4 right-4 z-50"
            >
              <div className="bg-white dark:bg-neutral-900 rounded-2xl p-4 shadow-2xl border border-gray-200 dark:border-neutral-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white">Actions rapides</h3>
                  <button 
                    onClick={() => setShowQuickActions(false)}
                    className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-neutral-800"
                  >
                    <X className="h-5 w-5 text-gray-500" />
                  </button>
                </div>
                
                <div className="grid grid-cols-3 gap-3">
                  {quickActions.map((action) => (
                    <Link
                      key={action.name}
                      href={action.href}
                      onClick={() => setShowQuickActions(false)}
                      className="flex flex-col items-center gap-2 p-3 rounded-xl bg-gray-50 dark:bg-neutral-800 hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors"
                    >
                      <div className={cn("p-2 rounded-full text-white", action.color)}>
                        <action.icon className="h-5 w-5" />
                      </div>
                      <span className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium">
                        {action.name}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Bottom Navigation Bar */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-50 bg-white/95 dark:bg-neutral-950/95 backdrop-blur-lg border-t border-gray-200 dark:border-neutral-800 safe-bottom">
        <div className="flex items-center justify-around h-16 px-2">
          {mobileNav.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/today' && item.href !== '#' && pathname.startsWith(item.href));
            
            // FAB Button for Add
            if (item.isAction) {
              return (
                <button
                  key={item.name}
                  onClick={() => setShowQuickActions(!showQuickActions)}
                  className={cn(
                    "relative flex items-center justify-center w-14 h-14 -mt-6 rounded-full shadow-lg transition-all duration-300",
                    showQuickActions
                      ? "bg-gray-900 dark:bg-white rotate-45"
                      : "bg-gradient-to-r from-purple-600 to-pink-500"
                  )}
                >
                  <Plus className={cn(
                    "h-6 w-6 transition-transform duration-300",
                    showQuickActions ? "text-white dark:text-black" : "text-white"
                  )} />
                </button>
              );
            }
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'relative flex flex-col items-center justify-center flex-1 h-full transition-all duration-200',
                  isActive
                    ? 'text-purple-600 dark:text-purple-400'
                    : 'text-gray-500 dark:text-gray-400'
                )}
              >
                <motion.div
                  whileTap={{ scale: 0.9 }}
                  className="flex flex-col items-center"
                >
                  <item.icon 
                    className={cn(
                      'h-5 w-5 mb-1 transition-all duration-200',
                      isActive && 'scale-110'
                    )} 
                  />
                  <span className={cn(
                    'text-[10px] font-medium',
                    isActive && 'font-semibold'
                  )}>
                    {item.name}
                  </span>
                </motion.div>
                
                {/* Active indicator */}
                {isActive && (
                  <motion.div 
                    layoutId="activeTab"
                    className="absolute -top-0.5 w-8 h-1 bg-purple-600 dark:bg-purple-400 rounded-full"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
