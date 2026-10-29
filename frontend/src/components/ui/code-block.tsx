import * as React from 'react';
import { Check, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

export interface CodeBlockProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CodeBlock = React.forwardRef<HTMLDivElement, CodeBlockProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'w-full rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-100 overflow-hidden font-mono text-xs shadow-sm',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CodeBlock.displayName = 'CodeBlock';

export interface CodeBlockHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CodeBlockHeader = React.forwardRef<HTMLDivElement, CodeBlockHeaderProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center justify-between px-3.5 py-2 border-b border-zinc-850 bg-zinc-900/70 text-zinc-400 text-xs',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CodeBlockHeader.displayName = 'CodeBlockHeader';

export interface CodeBlockTitleProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CodeBlockTitle = React.forwardRef<HTMLDivElement, CodeBlockTitleProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-center gap-2 font-mono text-xs text-zinc-300 font-medium', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CodeBlockTitle.displayName = 'CodeBlockTitle';

export interface CodeBlockActionsProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CodeBlockActions = React.forwardRef<HTMLDivElement, CodeBlockActionsProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div ref={ref} className={cn('flex items-center gap-1', className)} {...props}>
        {children}
      </div>
    );
  }
);
CodeBlockActions.displayName = 'CodeBlockActions';

export interface CodeBlockCopyButtonProps {
  value: string;
  className?: string;
}

export const CodeBlockCopyButton: React.FC<CodeBlockCopyButtonProps> = ({ value, className }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon-xs"
      onClick={handleCopy}
      className={cn('text-zinc-400 hover:text-zinc-100', className)}
      title={copied ? 'Copied' : 'Copy code'}
    >
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
    </Button>
  );
};
CodeBlockCopyButton.displayName = 'CodeBlockCopyButton';

export interface CodeBlockContentProps extends React.HTMLAttributes<HTMLDivElement> {
  wrap?: boolean;
  lineNumbers?: boolean;
}

export const CodeBlockContent = React.forwardRef<HTMLDivElement, CodeBlockContentProps>(
  ({ className, wrap = false, lineNumbers = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'p-3 overflow-x-auto text-xs leading-relaxed max-h-96 select-text custom-scrollbar',
          wrap ? 'whitespace-pre-wrap break-words' : 'whitespace-pre',
          lineNumbers && '[counter-reset:line]',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CodeBlockContent.displayName = 'CodeBlockContent';

export interface CodeBlockLineProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'highlighted';
  lineNumber?: number;
}

export const CodeBlockLine = React.forwardRef<HTMLDivElement, CodeBlockLineProps>(
  ({ className, variant = 'default', lineNumber, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-start gap-4 px-2 py-0.5 rounded transition-colors',
          variant === 'highlighted' && 'bg-zinc-800/60 text-zinc-100',
          className
        )}
        {...props}
      >
        {lineNumber !== undefined && (
          <span className="w-6 shrink-0 text-right text-zinc-600 select-none text-[11px]">
            {lineNumber}
          </span>
        )}
        <span className="flex-1 font-mono text-[11px]">{children}</span>
      </div>
    );
  }
);
CodeBlockLine.displayName = 'CodeBlockLine';

