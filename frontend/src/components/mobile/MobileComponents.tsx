'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MobileStatCardProps {
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
  label: string;
  value: string | number;
  subValue?: string;
  subColor?: string;
  onClick?: () => void;
}

export function MobileStatCard({
  icon: Icon,
  iconColor,
  iconBg,
  label,
  value,
  subValue,
  subColor = 'text-gray-400',
  onClick
}: MobileStatCardProps) {
  return (
    <motion.div
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "bg-white dark:bg-neutral-900 rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-neutral-800",
        onClick && "cursor-pointer active:bg-gray-50 dark:active:bg-neutral-800"
      )}
    >
      <div className="flex items-center gap-3">
        <div className={cn("p-2.5 rounded-xl", iconBg)}>
          <Icon className={cn("h-5 w-5", iconColor)} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">{label}</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white truncate">{value}</p>
          {subValue && (
            <p className={cn("text-xs font-medium truncate", subColor)}>{subValue}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

interface MobileKanbanCardProps {
  title: string;
  subtitle?: string;
  tag?: string;
  tagColor?: string;
  rightText?: string;
  rightColor?: string;
  borderColor?: string;
  onClick?: () => void;
}

export function MobileKanbanCard({
  title,
  subtitle,
  tag,
  tagColor = 'bg-gray-100 text-gray-600',
  rightText,
  rightColor = 'text-gray-500',
  borderColor = 'border-gray-300',
  onClick
}: MobileKanbanCardProps) {
  return (
    <motion.div
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "bg-white dark:bg-neutral-900 rounded-xl p-3 border-l-4 shadow-sm",
        borderColor,
        onClick && "cursor-pointer"
      )}
    >
      <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{title}</p>
      {subtitle && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{subtitle}</p>
      )}
      <div className="flex items-center justify-between mt-2">
        {tag && (
          <span className={cn("text-[10px] font-medium px-2 py-0.5 rounded-full", tagColor)}>
            {tag}
          </span>
        )}
        {rightText && (
          <span className={cn("text-xs font-medium", rightColor)}>{rightText}</span>
        )}
      </div>
    </motion.div>
  );
}

interface MobileSectionHeaderProps {
  title: string;
  count?: number;
  countColor?: string;
  dotColor?: string;
  action?: ReactNode;
}

export function MobileSectionHeader({
  title,
  count,
  countColor = 'bg-gray-100 text-gray-600',
  dotColor = 'bg-gray-400',
  action
}: MobileSectionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <div className={cn("h-2 w-2 rounded-full", dotColor)} />
        <h3 className="font-semibold text-gray-900 dark:text-white text-sm">{title}</h3>
        {count !== undefined && (
          <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded-full", countColor)}>
            {count}
          </span>
        )}
      </div>
      {action}
    </div>
  );
}

interface MobilePageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function MobilePageHeader({ title, subtitle, actions }: MobilePageHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">{title}</h1>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

interface MobileEmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}

export function MobileEmptyState({ icon: Icon, title, description, action }: MobileEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className="p-4 bg-gray-100 dark:bg-neutral-800 rounded-full mb-4">
        <Icon className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs mb-4">{description}</p>
      {action}
    </div>
  );
}

interface MobileListItemProps {
  icon?: LucideIcon;
  iconBg?: string;
  iconColor?: string;
  title: string;
  subtitle?: string;
  rightContent?: ReactNode;
  onClick?: () => void;
}

export function MobileListItem({
  icon: Icon,
  iconBg = 'bg-purple-100 dark:bg-purple-900',
  iconColor = 'text-purple-600 dark:text-purple-400',
  title,
  subtitle,
  rightContent,
  onClick
}: MobileListItemProps) {
  return (
    <motion.div
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 p-3 bg-white dark:bg-neutral-900 rounded-xl border border-gray-100 dark:border-neutral-800",
        onClick && "cursor-pointer active:bg-gray-50 dark:active:bg-neutral-800"
      )}
    >
      {Icon && (
        <div className={cn("p-2 rounded-full flex-shrink-0", iconBg)}>
          <Icon className={cn("h-4 w-4", iconColor)} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{title}</p>
        {subtitle && (
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{subtitle}</p>
        )}
      </div>
      {rightContent}
    </motion.div>
  );
}

interface MobileSwipeableCardProps {
  children: ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  leftAction?: ReactNode;
  rightAction?: ReactNode;
}

export function MobileSwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftAction,
  rightAction
}: MobileSwipeableCardProps) {
  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.2}
      onDragEnd={(_, info) => {
        if (info.offset.x < -100 && onSwipeLeft) {
          onSwipeLeft();
        } else if (info.offset.x > 100 && onSwipeRight) {
          onSwipeRight();
        }
      }}
      className="relative"
    >
      {/* Background Actions */}
      <div className="absolute inset-y-0 left-0 flex items-center pl-4">
        {leftAction}
      </div>
      <div className="absolute inset-y-0 right-0 flex items-center pr-4">
        {rightAction}
      </div>
      
      {/* Main Content */}
      <div className="relative bg-white dark:bg-neutral-900 rounded-xl">
        {children}
      </div>
    </motion.div>
  );
}
