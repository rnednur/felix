import { useState } from 'react'
import { Plus, Trash2, Link2, ArrowRight, Sparkles, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ColumnPair {
  from_column: string
  to_column: string
}

interface Relationship {
  id: string
  from_dataset: string
  to_dataset: string
  column_pairs: ColumnPair[]
  relationship_type: 'one_to_many' | 'many_to_one' | 'one_to_one' | 'many_to_many'
  join_type: 'inner' | 'left' | 'right' | 'full'
  custom_condition?: string
}

interface RelationshipsManagerProps {
  groupId: string
  datasets: Array<{ id: string; name: string; alias?: string }>
  schemas: Array<{
    dataset_id: string
    schema: {
      columns: Array<{ name: string; dtype: string }>
    }
  }>
}

export function RelationshipsManager({ groupId, datasets, schemas }: RelationshipsManagerProps) {
  const [relationships, setRelationships] = useState<Relationship[]>([])
  const [isAdding, setIsAdding] = useState(false)
  const [newRelationship, setNewRelationship] = useState<Partial<Relationship>>({
    relationship_type: 'one_to_many',
    join_type: 'inner',
    column_pairs: [{ from_column: '', to_column: '' }]
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  const getDatasetName = (datasetId: string) => {
    const dataset = datasets.find(d => d.id === datasetId)
    return dataset?.alias || dataset?.name || datasetId
  }

  const getColumnsForDataset = (datasetId: string) => {
    const schemaData = schemas.find(s => s.dataset_id === datasetId)
    return schemaData?.schema?.columns || []
  }

  const handleAddRelationship = () => {
    if (!newRelationship.from_dataset || !newRelationship.to_dataset) {
      alert('Please select both tables')
      return
    }

    const columnPairs = newRelationship.column_pairs?.filter(
      pair => pair.from_column && pair.to_column
    ) || []

    if (columnPairs.length === 0) {
      alert('Please add at least one column pair')
      return
    }

    const relationship: Relationship = {
      id: Date.now().toString(),
      from_dataset: newRelationship.from_dataset!,
      to_dataset: newRelationship.to_dataset!,
      column_pairs: columnPairs,
      relationship_type: newRelationship.relationship_type || 'one_to_many',
      join_type: newRelationship.join_type || 'inner',
      custom_condition: newRelationship.custom_condition
    }

    setRelationships([...relationships, relationship])
    setNewRelationship({
      relationship_type: 'one_to_many',
      join_type: 'inner',
      column_pairs: [{ from_column: '', to_column: '' }]
    })
    setShowAdvanced(false)
    setIsAdding(false)
  }

  const handleAddColumnPair = () => {
    setNewRelationship({
      ...newRelationship,
      column_pairs: [...(newRelationship.column_pairs || []), { from_column: '', to_column: '' }]
    })
  }

  const handleRemoveColumnPair = (index: number) => {
    const pairs = [...(newRelationship.column_pairs || [])]
    pairs.splice(index, 1)
    setNewRelationship({
      ...newRelationship,
      column_pairs: pairs.length > 0 ? pairs : [{ from_column: '', to_column: '' }]
    })
  }

  const handleUpdateColumnPair = (index: number, field: 'from_column' | 'to_column', value: string) => {
    const pairs = [...(newRelationship.column_pairs || [])]
    pairs[index] = { ...pairs[index], [field]: value }
    setNewRelationship({
      ...newRelationship,
      column_pairs: pairs
    })
  }

  const handleDeleteRelationship = (id: string) => {
    if (!confirm('Delete this relationship?')) return
    setRelationships(relationships.filter(r => r.id !== id))
  }

  const handleAutoDetect = () => {
    const detected: Relationship[] = []
    const datasetMap = new Map(datasets.map(d => [d.id, d]))

    // For each dataset pair
    for (let i = 0; i < datasets.length; i++) {
      for (let j = 0; j < datasets.length; j++) {
        if (i === j) continue

        const fromDataset = datasets[i]
        const toDataset = datasets[j]
        const fromSchema = schemas.find(s => s.dataset_id === fromDataset.id)
        const toSchema = schemas.find(s => s.dataset_id === toDataset.id)

        if (!fromSchema || !toSchema) continue

        // Strategy 1: Look for foreign key patterns (e.g., customer_id → customers.id)
        fromSchema.schema.columns.forEach(fromCol => {
          const colName = fromCol.name.toLowerCase()

          // Check if column name suggests a foreign key
          // Patterns: table_id, tableId, table_name_id, fk_table
          const patterns = [
            new RegExp(`^${toDataset.name.toLowerCase()}_id$`),
            new RegExp(`^${toDataset.name.toLowerCase()}id$`),
            new RegExp(`^fk_${toDataset.name.toLowerCase()}`),
            new RegExp(`^${(toDataset.alias || toDataset.name).toLowerCase()}_id$`),
          ]

          const isForeignKey = patterns.some(pattern => pattern.test(colName))

          if (isForeignKey) {
            // Look for matching 'id' column in target table
            const idColumn = toSchema.schema.columns.find(c =>
              c.name.toLowerCase() === 'id' ||
              c.name.toLowerCase() === `${toDataset.name.toLowerCase()}_id`
            )

            if (idColumn) {
              // Check if relationship already exists
              const alreadyExists = relationships.some(r =>
                r.from_dataset === fromDataset.id &&
                r.to_dataset === toDataset.id &&
                r.column_pairs.some(cp => cp.from_column === fromCol.name && cp.to_column === idColumn.name)
              )

              const alreadyDetected = detected.some(r =>
                r.from_dataset === fromDataset.id &&
                r.to_dataset === toDataset.id &&
                r.column_pairs.some(cp => cp.from_column === fromCol.name && cp.to_column === idColumn.name)
              )

              if (!alreadyExists && !alreadyDetected) {
                detected.push({
                  id: `auto_${Date.now()}_${detected.length}`,
                  from_dataset: fromDataset.id,
                  to_dataset: toDataset.id,
                  column_pairs: [{ from_column: fromCol.name, to_column: idColumn.name }],
                  relationship_type: 'many_to_one',
                  join_type: 'inner'
                })
              }
            }
          }
        })

        // Strategy 2: Look for exact column name matches
        fromSchema.schema.columns.forEach(fromCol => {
          toSchema.schema.columns.forEach(toCol => {
            if (fromCol.name === toCol.name &&
                fromCol.dtype === toCol.dtype &&
                fromCol.name.toLowerCase() !== 'id') { // Skip generic 'id' columns

              // Check if relationship already exists
              const alreadyExists = relationships.some(r =>
                r.from_dataset === fromDataset.id &&
                r.to_dataset === toDataset.id &&
                r.column_pairs.some(cp => cp.from_column === fromCol.name && cp.to_column === toCol.name)
              )

              const alreadyDetected = detected.some(r =>
                r.from_dataset === fromDataset.id &&
                r.to_dataset === toDataset.id &&
                r.column_pairs.some(cp => cp.from_column === fromCol.name && cp.to_column === toCol.name)
              )

              if (!alreadyExists && !alreadyDetected) {
                detected.push({
                  id: `auto_${Date.now()}_${detected.length}`,
                  from_dataset: fromDataset.id,
                  to_dataset: toDataset.id,
                  column_pairs: [{ from_column: fromCol.name, to_column: toCol.name }],
                  relationship_type: 'one_to_many',
                  join_type: 'inner'
                })
              }
            }
          })
        })
      }
    }

    if (detected.length === 0) {
      alert('No relationships detected. Try adding relationships manually.')
      return
    }

    const message = `Found ${detected.length} potential relationship${detected.length > 1 ? 's' : ''}:\n\n` +
      detected.map(r => {
        const pairs = r.column_pairs.map(cp => `${cp.from_column} → ${cp.to_column}`).join(', ')
        return `• ${getDatasetName(r.from_dataset)} ↔ ${getDatasetName(r.to_dataset)}: ${pairs}`
      }).join('\n') +
      '\n\nAdd these relationships?'

    if (confirm(message)) {
      setRelationships([...relationships, ...detected])
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Table Relationships</h3>
          <p className="text-sm text-gray-600 mt-1">
            Define how tables are related for multi-table queries
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleAutoDetect}
            variant="outline"
            className="gap-2"
          >
            <Sparkles className="h-4 w-4" />
            Auto-detect
          </Button>
          <Button
            onClick={() => setIsAdding(true)}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Relationship
          </Button>
        </div>
      </div>

      {/* Existing Relationships */}
      {relationships.length > 0 ? (
        <div className="space-y-3">
          {relationships.map((rel) => (
            <div
              key={rel.id}
              className="border border-gray-200 rounded-lg p-4 bg-white hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-3">
                    {/* From Table */}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {getDatasetName(rel.from_dataset)}
                      </div>
                    </div>

                    {/* Relationship Type */}
                    <div className="flex flex-col items-center">
                      <ArrowRight className="h-5 w-5 text-blue-600" />
                      <div className="text-xs text-gray-500 mt-1">
                        {rel.relationship_type.replace('_', '-')}
                      </div>
                      <div className="text-xs text-gray-400">
                        ({rel.join_type})
                      </div>
                    </div>

                    {/* To Table */}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {getDatasetName(rel.to_dataset)}
                      </div>
                    </div>
                  </div>

                  {/* Column Pairs */}
                  <div className="space-y-1">
                    {rel.column_pairs.map((pair, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        <span className="font-mono text-gray-700 bg-gray-100 px-2 py-1 rounded">
                          {pair.from_column}
                        </span>
                        <span className="text-gray-400">→</span>
                        <span className="font-mono text-gray-700 bg-gray-100 px-2 py-1 rounded">
                          {pair.to_column}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Custom Condition */}
                  {rel.custom_condition && (
                    <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                      <div className="text-xs font-medium text-yellow-900 mb-1">Custom Condition:</div>
                      <div className="text-xs font-mono text-yellow-800">{rel.custom_condition}</div>
                    </div>
                  )}
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => handleDeleteRelationship(rel.id)}
                  className="p-2 hover:bg-red-50 rounded text-red-600 transition-colors"
                  title="Delete relationship"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <Link2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">No relationships defined</h4>
          <p className="text-sm text-gray-600 mb-4">
            Add relationships to enable queries across multiple tables
          </p>
          <Button onClick={() => setIsAdding(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            Add First Relationship
          </Button>
        </div>
      )}

      {/* Add Relationship Modal */}
      {isAdding && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Add Table Relationship</h3>

            <div className="space-y-4">
              {/* From and To Tables */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    From Table
                  </label>
                  <select
                    value={newRelationship.from_dataset || ''}
                    onChange={(e) => setNewRelationship({ ...newRelationship, from_dataset: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select table...</option>
                    {datasets.map(d => (
                      <option key={d.id} value={d.id}>
                        {d.alias || d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    To Table
                  </label>
                  <select
                    value={newRelationship.to_dataset || ''}
                    onChange={(e) => setNewRelationship({ ...newRelationship, to_dataset: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select table...</option>
                    {datasets.filter(d => d.id !== newRelationship.from_dataset).map(d => (
                      <option key={d.id} value={d.id}>
                        {d.alias || d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Column Pairs */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Column Mappings
                  </label>
                  <button
                    onClick={handleAddColumnPair}
                    disabled={!newRelationship.from_dataset || !newRelationship.to_dataset}
                    className="text-xs text-blue-600 hover:text-blue-700 disabled:text-gray-400 flex items-center gap-1"
                  >
                    <Plus className="h-3 w-3" />
                    Add Column Pair
                  </button>
                </div>

                <div className="space-y-2">
                  {(newRelationship.column_pairs || []).map((pair, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <select
                        value={pair.from_column}
                        onChange={(e) => handleUpdateColumnPair(index, 'from_column', e.target.value)}
                        disabled={!newRelationship.from_dataset}
                        className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                      >
                        <option value="">Select from column...</option>
                        {newRelationship.from_dataset && getColumnsForDataset(newRelationship.from_dataset).map(col => (
                          <option key={col.name} value={col.name}>
                            {col.name} ({col.dtype})
                          </option>
                        ))}
                      </select>

                      <ArrowRight className="h-4 w-4 text-gray-400" />

                      <select
                        value={pair.to_column}
                        onChange={(e) => handleUpdateColumnPair(index, 'to_column', e.target.value)}
                        disabled={!newRelationship.to_dataset}
                        className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                      >
                        <option value="">Select to column...</option>
                        {newRelationship.to_dataset && getColumnsForDataset(newRelationship.to_dataset).map(col => (
                          <option key={col.name} value={col.name}>
                            {col.name} ({col.dtype})
                          </option>
                        ))}
                      </select>

                      {(newRelationship.column_pairs?.length || 0) > 1 && (
                        <button
                          onClick={() => handleRemoveColumnPair(index)}
                          className="p-2 hover:bg-red-50 rounded text-red-600"
                          title="Remove column pair"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Relationship Type */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Relationship Type
                  </label>
                  <select
                    value={newRelationship.relationship_type}
                    onChange={(e) => setNewRelationship({ ...newRelationship, relationship_type: e.target.value as any })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="one_to_many">One to Many</option>
                    <option value="many_to_one">Many to One</option>
                    <option value="one_to_one">One to One</option>
                    <option value="many_to_many">Many to Many</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Join Type
                  </label>
                  <select
                    value={newRelationship.join_type}
                    onChange={(e) => setNewRelationship({ ...newRelationship, join_type: e.target.value as any })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="inner">Inner Join</option>
                    <option value="left">Left Join</option>
                    <option value="right">Right Join</option>
                    <option value="full">Full Outer Join</option>
                  </select>
                </div>
              </div>

              {/* Advanced Options */}
              <div>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
                >
                  {showAdvanced ? '▼' : '▶'} Advanced: Custom Condition
                </button>

                {showAdvanced && (
                  <div className="mt-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Custom WHERE Condition (optional)
                    </label>
                    <textarea
                      value={newRelationship.custom_condition || ''}
                      onChange={(e) => setNewRelationship({ ...newRelationship, custom_condition: e.target.value })}
                      placeholder="e.g., table1.status = 'active' AND table2.deleted_at IS NULL"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Add additional SQL conditions beyond the column joins
                    </p>
                  </div>
                )}
              </div>

              {/* Info Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  💡 <strong>Tip:</strong> Add multiple column pairs for composite keys. Relationships help the AI understand how to join tables when you ask questions across multiple datasets.
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-6">
              <Button
                variant="outline"
                onClick={() => {
                  setIsAdding(false)
                  setNewRelationship({ relationship_type: 'one_to_many', join_type: 'inner' })
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleAddRelationship}>
                Add Relationship
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">💡 Understanding Relationships</h4>
        <div className="text-sm text-gray-700 space-y-2">
          <p><strong>One-to-Many:</strong> One record in Table A relates to many in Table B (e.g., Customer → Orders)</p>
          <p><strong>Many-to-One:</strong> Many records in Table A relate to one in Table B (e.g., Orders → Customer)</p>
          <p><strong>One-to-One:</strong> One record in Table A relates to exactly one in Table B (e.g., User → Profile)</p>
          <p><strong>Many-to-Many:</strong> Records in both tables can relate to multiple records (e.g., Students ↔ Courses)</p>
        </div>
      </div>
    </div>
  )
}
