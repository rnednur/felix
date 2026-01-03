import * as React from 'react'

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  tooltip?: string
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className = '', variant = 'default', size = 'md', tooltip, children, ...props }, ref) => {
    const [showTooltip, setShowTooltip] = React.useState(false)

    // Variant styles
    const variantClasses = {
      default: 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 shadow-sm',
      primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md',
      secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
      ghost: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
      destructive: 'bg-red-50 text-red-600 hover:bg-red-100 border border-red-200',
    }

    // Size styles
    const sizeClasses = {
      sm: 'h-8 w-8',
      md: 'h-10 w-10',
      lg: 'h-12 w-12',
    }

    const buttonClasses = `inline-flex items-center justify-center rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${variantClasses[variant]} ${sizeClasses[size]} ${className}`

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
          <div className="absolute z-[10] px-3 py-1.5 text-sm font-medium text-white bg-gray-900 rounded-lg shadow-lg whitespace-nowrap -top-5 left-1/2 transform -translate-x-1/2 pointer-events-none animate-in fade-in-0 zoom-in-95 duration-200">
            {tooltip}
            <div className="absolute w-2 h-2 bg-gray-900 transform rotate-45 -bottom-1 left-1/2 -translate-x-1/2"></div>
          </div>
        )}
      </div>
    )
  }
)

IconButton.displayName = 'IconButton'

export { IconButton }
