import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { LogOut, User, ChevronDown, Moon, Sun } from 'lucide-react'

export function UserMenu() {
  const { user, logout } = useAuth()
  const { darkMode, toggleDarkMode } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!user) return null

  return (
    <div className="flex items-center gap-2">
      {/* Dark mode toggle */}
      <button
        onClick={toggleDarkMode}
        className="p-2 rounded-lg hover:bg-accent transition-colors text-muted-foreground hover:text-foreground"
        title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>

      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
        >
          <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full">
            <User className="h-4 w-4" />
          </div>
          <div className="text-left hidden md:block">
            <div className="text-sm font-medium text-foreground">
              {user.full_name || user.username}
            </div>
            <div className="text-xs text-muted-foreground">{user.email}</div>
          </div>
          <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-56 bg-card border border-border rounded-lg shadow-lg z-50">
            <div className="p-3 border-b border-border">
              <div className="text-sm font-medium text-foreground">
                {user.full_name || user.username}
              </div>
              <div className="text-xs text-muted-foreground">{user.email}</div>
              <div className="mt-1">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {user.role}
                </span>
              </div>
            </div>

            <div className="p-2">
              <button
                onClick={() => {
                  setIsOpen(false)
                  logout()
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-destructive/10 rounded-lg transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
