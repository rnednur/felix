import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  [
    "inline-flex items-center rounded-full px-2.5 py-0.5",
    "text-xs font-medium",
    "transition-colors duration-150",
  ].join(" "),
  {
    variants: {
      variant: {
        default: "bg-primary-muted text-primary border border-primary/20",
        secondary: "bg-secondary text-secondary-foreground border border-border",
        success: "bg-success-muted text-success border border-success/20",
        warning: "bg-warning-muted text-warning-foreground border border-warning/20",
        destructive: "bg-destructive-muted text-destructive border border-destructive/20",
        info: "bg-info-muted text-info border border-info/20",
        outline: "bg-transparent text-foreground border border-border",
      },
      size: {
        default: "px-2.5 py-0.5 text-xs",
        sm: "px-2 py-px text-[10px]",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  /** Optional dot indicator before the text */
  dot?: boolean
  /** Dot color - defaults to variant color */
  dotColor?: string
}

function Badge({ className, variant, size, dot, dotColor, children, ...props }: BadgeProps) {
  const dotColors = {
    default: "bg-primary",
    secondary: "bg-muted-foreground",
    success: "bg-success",
    warning: "bg-warning",
    destructive: "bg-destructive",
    info: "bg-info",
    outline: "bg-foreground",
  }

  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props}>
      {dot && (
        <span
          className={cn(
            "mr-1.5 h-1.5 w-1.5 rounded-full",
            dotColor || dotColors[variant || "default"]
          )}
        />
      )}
      {children}
    </div>
  )
}

export { Badge, badgeVariants }
