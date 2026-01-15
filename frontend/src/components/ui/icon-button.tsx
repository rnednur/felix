import * as React from 'react'
import { cn } from '@/lib/utils'

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  tooltip?: string
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className = '', variant = 'default', size = 'md', tooltip, children, ...props }, ref) => {
    const [showTooltip, setShowTooltip] = React.useState(false)

    const variantClasses = {
      default: [
        'bg-card border border-border text-foreground',
        'hover:bg-muted hover:border-border-strong',
        'shadow-sm',
      ].join(' '),
      primary: [
        'bg-primary text-primary-foreground',
        'hover:bg-primary-hover',
        'shadow-sm hover:shadow-md',
      ].join(' '),
      secondary: [
        'bg-secondary text-secondary-foreground',
        'hover:bg-secondary-hover',
      ].join(' '),
      ghost: [
        'text-muted-foreground',
        'hover:bg-muted hover:text-foreground',
      ].join(' '),
      destructive: [
        'bg-destructive-muted text-destructive border border-destructive/20',
        'hover:bg-destructive hover:text-destructive-foreground hover:border-destructive',
      ].join(' '),
    }

    const sizeClasses = {
      sm: 'h-8 w-8',
      md: 'h-10 w-10',
      lg: 'h-12 w-12',
    }

    const buttonClasses = cn(
      'inline-flex items-center justify-center rounded-lg',
      'font-medium',
      'transition-all duration-150 ease-out',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      'disabled:pointer-events-none disabled:opacity-50',
      'active:scale-[0.95]',
      variantClasses[variant],
      sizeClasses[size],
      className
    )

    return (
      <div className="relative inline-block">
        <button
          ref={ref}
          className={buttonClasses}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          {...props}
        >
          {children}
        </button>
        {tooltip && showTooltip && (
          <div
            className={cn(
              'absolute z-tooltip px-2.5 py-1.5',
              'text-xs font-medium text-popover-foreground',
              'bg-popover border border-border rounded-md shadow-elevation-2',
              'whitespace-nowrap',
              '-top-10 left-1/2 transform -translate-x-1/2',
              'pointer-events-none',
              'animate-fade-in'
            )}
          >
            {tooltip}
            <div className="absolute w-2 h-2 bg-popover border-b border-r border-border transform rotate-45 -bottom-1 left-1/2 -translate-x-1/2" />
          </div>
        )}
      </div>
    )
  }
)

IconButton.displayName = 'IconButton'

export { IconButton }
