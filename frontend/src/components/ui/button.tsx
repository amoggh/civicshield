import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'xs' | 'icon' | 'icon-xs';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    const variantStyles = {
      default: 'bg-zinc-100 text-zinc-950 hover:bg-zinc-200 shadow-sm',
      destructive: 'bg-red-950 text-red-300 hover:bg-red-900 border border-red-800',
      outline: 'border border-zinc-800 bg-transparent hover:bg-zinc-900 text-zinc-200',
      secondary: 'bg-zinc-850 text-zinc-200 hover:bg-zinc-800 border border-zinc-800',
      ghost: 'hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-100',
      link: 'text-zinc-100 underline-offset-4 hover:underline',
    };

    const sizeStyles = {
      default: 'h-9 px-4 py-2 text-sm',
      sm: 'h-8 px-3 text-xs',
      lg: 'h-10 px-8 text-sm',
      xs: 'h-7 px-2.5 text-xs',
      icon: 'h-9 w-9 p-0',
      'icon-xs': 'h-6 w-6 p-0 text-xs',
    };

    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

