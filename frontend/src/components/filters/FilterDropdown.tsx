import { useState, useRef, useEffect } from 'react'
import { Check, ChevronDown, X, Search } from 'lucide-react'

interface FilterOption {
  value: string | number | boolean
  label: string
  count?: number
}

interface FilterDropdownProps {
  column: string
  label?: string
  options: FilterOption[]
  selectedValues: (string | number | boolean)[]
  onSelectionChange: (values: (string | number | boolean)[]) => void
  onClear?: () => void
  placeholder?: string
  multiSelect?: boolean
  searchable?: boolean
}

export function FilterDropdown({
  column,
  label,
  options,
  selectedValues,
  onSelectionChange,
  onClear,
  placeholder = 'Select...',
  multiSelect = true,
  searchable = true
}: FilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Filter options based on search
  const filteredOptions = searchQuery
    ? options.filter(opt =>
        String(opt.label).toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options

  const handleToggleOption = (value: string | number | boolean) => {
    if (multiSelect) {
      const newSelection = selectedValues.includes(value)
        ? selectedValues.filter(v => v !== value)
        : [...selectedValues, value]
      onSelectionChange(newSelection)
    } else {
      onSelectionChange([value])
      setIsOpen(false)
    }
  }

  const handleSelectAll = () => {
    onSelectionChange(options.map(opt => opt.value))
  }

  const handleClearSelection = () => {
    onSelectionChange([])
    onClear?.()
  }

  const displayValue = selectedValues.length > 0
    ? selectedValues.length === 1
      ? String(options.find(opt => opt.value === selectedValues[0])?.label || selectedValues[0])
      : `${selectedValues.length} selected`
    : placeholder

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between gap-2 px-3 py-2 min-w-[140px] max-w-[200px] text-sm border rounded-lg transition-colors ${
          selectedValues.length > 0
            ? 'bg-primary/10 border-primary text-primary'
            : 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'
        }`}
      >
        <span className="truncate">
          {label && <span className="text-gray-500 mr-1">{label}:</span>}
          {displayValue}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {selectedValues.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleClearSelection()
              }}
              className="p-0.5 hover:bg-primary/20 rounded"
            >
              <X className="h-3 w-3" />
            </button>
          )}
          <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
          {/* Search */}
          {searchable && options.length > 5 && (
            <div className="p-2 border-b border-gray-100">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  autoFocus
                />
              </div>
            </div>
          )}

          {/* Actions */}
          {multiSelect && (
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100 text-xs">
              <button
                onClick={handleSelectAll}
                className="text-primary hover:text-primary/80"
              >
                Select all
              </button>
              <button
                onClick={handleClearSelection}
                className="text-gray-500 hover:text-gray-700"
              >
                Clear
              </button>
            </div>
          )}

          {/* Options */}
          <div className="max-h-60 overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">
                No options found
              </div>
            ) : (
              filteredOptions.map((option) => {
                const isSelected = selectedValues.includes(option.value)
                return (
                  <button
                    key={String(option.value)}
                    onClick={() => handleToggleOption(option.value)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-sm transition-colors ${
                      isSelected
                        ? 'bg-primary/10 text-primary'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <div className={`w-4 h-4 border rounded flex items-center justify-center flex-shrink-0 ${
                        isSelected ? 'bg-primary border-primary' : 'border-gray-300'
                      }`}>
                        {isSelected && <Check className="h-3 w-3 text-white" />}
                      </div>
                      <span className="truncate">{option.label}</span>
                    </div>
                    {option.count !== undefined && (
                      <span className="text-xs text-gray-400 ml-2">
                        {option.count.toLocaleString()}
                      </span>
                    )}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
