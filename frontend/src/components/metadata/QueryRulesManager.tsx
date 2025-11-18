import { useState, useEffect } from 'react'
import { X, Plus, Edit2, Trash2, Power, PowerOff, Save } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface QueryRule {
  id?: string
  name: string
  description?: string
  rule_type: 'filter' | 'exclude_column' | 'always_include'
  condition: Record<string, any>
  is_active: boolean
  priority: number
}

interface Props {
  datasetId: string
  onClose: () => void
}

const RULE_TYPES = [
  { value: 'filter', label: 'Filter', description: 'Always apply a WHERE clause filter' },
  { value: 'exclude_column', label: 'Exclude Column', description: 'Never include a specific column' },
  { value: 'always_include', label: 'Always Include', description: 'Always apply a specific filter' }
]

const OPERATORS = ['=', '!=', '>', '<', '>=', '<=', 'IN', 'BETWEEN']

export function QueryRulesManager({ datasetId, onClose }: Props) {
  const [rules, setRules] = useState<QueryRule[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [editingRule, setEditingRule] = useState<QueryRule | null>(null)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    loadRules()
  }, [datasetId])

  const loadRules = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/metadata/datasets/${datasetId}/rules`
      )
      if (!response.ok) throw new Error('Failed to load rules')
      const data = await response.json()
      setRules(data)
    } catch (error) {
      console.error('Error loading rules:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveRule = async (rule: QueryRule) => {
    try {
      const url = rule.id
        ? `http://localhost:8000/api/v1/metadata/datasets/${datasetId}/rules/${rule.id}`
        : `http://localhost:8000/api/v1/metadata/datasets/${datasetId}/rules`

      const response = await fetch(url, {
        method: rule.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule)
      })

      if (!response.ok) throw new Error('Failed to save rule')

      await loadRules()
      setShowForm(false)
      setEditingRule(null)
    } catch (error) {
      console.error('Error saving rule:', error)
      alert('Failed to save rule')
    }
  }

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/metadata/datasets/${datasetId}/rules/${ruleId}`,
        { method: 'DELETE' }
      )

      if (!response.ok) throw new Error('Failed to delete rule')

      await loadRules()
    } catch (error) {
      console.error('Error deleting rule:', error)
      alert('Failed to delete rule')
    }
  }

  const handleToggleRule = async (ruleId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/metadata/datasets/${datasetId}/rules/${ruleId}/toggle`,
        { method: 'POST' }
      )

      if (!response.ok) throw new Error('Failed to toggle rule')

      await loadRules()
    } catch (error) {
      console.error('Error toggling rule:', error)
      alert('Failed to toggle rule')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Query Rules</h2>
            <p className="text-sm text-gray-600 mt-1">
              Manage automatic query rules that apply to all queries
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Add New Rule Button */}
          {!showForm && (
            <div className="mb-4">
              <Button
                onClick={() => {
                  setEditingRule({
                    name: '',
                    rule_type: 'filter',
                    condition: {},
                    is_active: true,
                    priority: 0
                  })
                  setShowForm(true)
                }}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add New Rule
              </Button>
            </div>
          )}

          {/* Rule Form */}
          {showForm && editingRule && (
            <RuleForm
              rule={editingRule}
              onSave={handleSaveRule}
              onCancel={() => {
                setShowForm(false)
                setEditingRule(null)
              }}
            />
          )}

          {/* Rules List */}
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Loading rules...</div>
          ) : rules.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No rules configured. Add a rule to get started.
            </div>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className={`border rounded-lg p-4 ${
                    rule.is_active ? 'bg-white' : 'bg-gray-50 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-medium text-gray-900">{rule.name}</h3>
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                          {RULE_TYPES.find((t) => t.value === rule.rule_type)?.label}
                        </span>
                        {rule.priority > 0 && (
                          <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded">
                            Priority: {rule.priority}
                          </span>
                        )}
                      </div>
                      {rule.description && (
                        <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                      )}
                      <div className="mt-2 text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded inline-block">
                        {JSON.stringify(rule.condition)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleToggleRule(rule.id!)}
                        className={`p-2 rounded hover:bg-gray-100 transition-colors ${
                          rule.is_active ? 'text-green-600' : 'text-gray-400'
                        }`}
                        title={rule.is_active ? 'Disable rule' : 'Enable rule'}
                      >
                        {rule.is_active ? (
                          <Power className="w-4 h-4" />
                        ) : (
                          <PowerOff className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setEditingRule(rule)
                          setShowForm(true)
                        }}
                        className="p-2 text-blue-600 rounded hover:bg-blue-50 transition-colors"
                        title="Edit rule"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id!)}
                        className="p-2 text-red-600 rounded hover:bg-red-50 transition-colors"
                        title="Delete rule"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function RuleForm({
  rule,
  onSave,
  onCancel
}: {
  rule: QueryRule
  onSave: (rule: QueryRule) => void
  onCancel: () => void
}) {
  const [formData, setFormData] = useState<QueryRule>(rule)

  const handleConditionChange = (key: string, value: any) => {
    setFormData({
      ...formData,
      condition: { ...formData.condition, [key]: value }
    })
  }

  return (
    <div className="border rounded-lg p-4 bg-blue-50 mb-4">
      <h3 className="font-medium text-gray-900 mb-4">
        {rule.id ? 'Edit Rule' : 'New Rule'}
      </h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Rule Name *
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Only show active records"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={formData.description || ''}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Optional description"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rule Type *
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.rule_type}
              onChange={(e) => setFormData({ ...formData, rule_type: e.target.value as any })}
            >
              {RULE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
              min="0"
            />
          </div>
        </div>

        {/* Condition Builder */}
        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Rule Condition *
          </label>

          {formData.rule_type === 'exclude_column' ? (
            <div>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.condition.column || ''}
                onChange={(e) => handleConditionChange('column', e.target.value)}
                placeholder="Column name to exclude"
              />
            </div>
          ) : (
            <div className="space-y-3">
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={formData.condition.column || ''}
                onChange={(e) => handleConditionChange('column', e.target.value)}
                placeholder="Column name"
              />

              <div className="grid grid-cols-2 gap-3">
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.condition.operator || '='}
                  onChange={(e) => handleConditionChange('operator', e.target.value)}
                >
                  {OPERATORS.map((op) => (
                    <option key={op} value={op}>
                      {op}
                    </option>
                  ))}
                </select>

                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.condition.value || ''}
                  onChange={(e) => {
                    const val = e.target.value
                    // Try to parse as JSON array for IN/BETWEEN, otherwise string
                    let parsedVal = val
                    if (val.startsWith('[')) {
                      try {
                        parsedVal = JSON.parse(val)
                      } catch {}
                    }
                    handleConditionChange('value', parsedVal)
                  }}
                  placeholder="Value (use [1,2,3] for IN)"
                />
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            checked={formData.is_active}
            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          />
          <label htmlFor="is_active" className="text-sm text-gray-700">
            Rule is active
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            onClick={() => onSave(formData)}
            disabled={!formData.name || !formData.condition.column}
            className="flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save Rule
          </Button>
        </div>
      </div>
    </div>
  )
}
