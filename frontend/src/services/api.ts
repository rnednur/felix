import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
})

export interface Dataset {
  id: string
  name: string
  description?: string
  source_type: string
  status: string
  row_count: number
  size_bytes: number
  dataset_version: number
  created_at: string
  updated_at: string
}

export interface DatasetGroupMembership {
  id: string
  dataset_id: string
  alias?: string
  display_order: number
  dataset: Dataset
  created_at: string
}

export interface DatasetGroup {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  memberships: DatasetGroupMembership[]
}

export interface DatasetGroupListItem {
  id: string
  name: string
  description?: string
  created_at: string
  dataset_count: number
}

export interface QueryResult {
  query_id: string
  sql: string
  rows: any[]
  total_rows: number
  execution_time_ms?: number
  retrieved_columns?: string[]
  status: string
}

export interface ChartSuggestion {
  type: string
  spec: any
}

export interface PythonAnalysisResult {
  execution_id: string
  mode: string
  generated_code: string
  steps?: Array<{
    step: number
    description: string
    code?: string
  }>
  estimated_runtime: string
  requires_review: boolean
  safety_warnings?: string[]
}

export interface ExecutionResult {
  execution_id: string
  status: string
  output?: any
  visualizations?: Array<{
    type: string
    format: string
    data: string
  }>
  error?: string
  execution_time_ms?: number
}

export interface DeepResearchResult {
  success: boolean
  main_question: string
  direct_answer: string
  key_findings: string[]
  supporting_details: Record<string, any>
  data_coverage: Record<string, any>
  follow_up_questions: string[]
  stages_completed: string[]
  execution_time_seconds: number
  error?: string
}

export interface ColumnMetadataSuggestion {
  column: string
  description: string
  business_definition?: string
  semantic_type?: string
  examples?: string[]
}

export interface AIDescribeColumnsResult {
  success: boolean
  suggestions: ColumnMetadataSuggestion[]
  message: string
}

// Datasets
export const uploadDataset = async (formData: FormData): Promise<Dataset> => {
  const { data } = await api.post('/datasets/upload', formData)
  return data
}

export const getDataset = async (id: string): Promise<Dataset> => {
  const { data } = await api.get(`/datasets/${id}`)
  return data
}

export const listDatasets = async (): Promise<Dataset[]> => {
  const { data } = await api.get('/datasets/')
  return data
}

export const getDatasetPreview = async (id: string) => {
  const { data } = await api.get(`/datasets/${id}/preview`)
  return data
}

export const getDatasetSchema = async (id: string) => {
  const { data } = await api.get(`/datasets/${id}/schema`)
  return data
}

export const deleteDataset = async (id: string): Promise<void> => {
  await api.delete(`/datasets/${id}`)
}

// Dataset Groups
export const createDatasetGroup = async (group: {
  name: string
  description?: string
}): Promise<DatasetGroup> => {
  const { data } = await api.post('/dataset-groups/', group)
  return data
}

export const listDatasetGroups = async (): Promise<DatasetGroupListItem[]> => {
  const { data } = await api.get('/dataset-groups/')
  return data
}

export const getDatasetGroup = async (id: string): Promise<DatasetGroup> => {
  const { data } = await api.get(`/dataset-groups/${id}`)
  return data
}

export const updateDatasetGroup = async (
  id: string,
  updates: { name?: string; description?: string }
): Promise<DatasetGroup> => {
  const { data } = await api.patch(`/dataset-groups/${id}`, updates)
  return data
}

export const deleteDatasetGroup = async (id: string): Promise<void> => {
  await api.delete(`/dataset-groups/${id}`)
}

export const addDatasetToGroup = async (
  groupId: string,
  membership: { dataset_id: string; alias?: string; display_order?: number }
): Promise<DatasetGroupMembership> => {
  const { data } = await api.post(`/dataset-groups/${groupId}/datasets`, membership)
  return data
}

export const removeDatasetFromGroup = async (
  groupId: string,
  datasetId: string
): Promise<void> => {
  await api.delete(`/dataset-groups/${groupId}/datasets/${datasetId}`)
}

export const getDatasetGroupSchemas = async (groupId: string) => {
  const { data } = await api.get(`/dataset-groups/${groupId}/schemas`)
  return data
}

export const getDatasetGroupPreview = async (groupId: string) => {
  const { data } = await api.get(`/dataset-groups/${groupId}/preview`)
  return data
}

export const describeDataset = async (id: string) => {
  const { data } = await api.get(`/analysis/datasets/${id}/describe`)
  return data
}

export const getDatasetSummary = async (id: string) => {
  const { data } = await api.get(`/analysis/datasets/${id}/summary`)
  return data
}

export const aiDescribeColumns = async (datasetId: string): Promise<AIDescribeColumnsResult> => {
  const { data } = await api.post(`/metadata/datasets/${datasetId}/ai-describe-columns`)
  return data
}

export const getColumnMetadata = async (datasetId: string) => {
  const { data } = await api.get(`/metadata/datasets/${datasetId}/columns`)
  return data
}

// Queries
export const executeNLQuery = async (
  query: string,
  options: { datasetId?: string; groupId?: string }
): Promise<QueryResult> => {
  const { data } = await api.post('/queries/nl', {
    dataset_id: options.datasetId,
    group_id: options.groupId,
    query,
  })
  return data
}

export const executeSQLQuery = async (
  sql: string,
  options: { datasetId?: string; groupId?: string }
): Promise<QueryResult> => {
  const { data } = await api.post('/queries/sql', {
    dataset_id: options.datasetId,
    group_id: options.groupId,
    sql,
  })
  return data
}

export const getQuery = async (queryId: string): Promise<QueryResult> => {
  const { data } = await api.get(`/queries/${queryId}`)
  return data
}

// Visualizations
export const getVisualizationSuggestions = async (
  queryId: string
): Promise<{ suggestions: ChartSuggestion[] }> => {
  const { data } = await api.post('/visualizations/suggest', { query_id: queryId })
  return data
}

export const createVisualization = async (vizData: {
  query_id: string
  name: string
  chart_type: string
  vega_spec: any
}) => {
  const { data } = await api.post('/visualizations/', vizData)
  return data
}

// Python Analysis
export const generatePythonCode = async (
  datasetId: string,
  query: string,
  mode: string = 'auto',
  executeImmediately: boolean = false
): Promise<PythonAnalysisResult> => {
  const { data } = await api.post('/python-analysis/generate', {
    dataset_id: datasetId,
    query,
    mode,
    execute_immediately: executeImmediately
  })
  return data
}

export const executePythonCode = async (
  executionId: string
): Promise<ExecutionResult> => {
  const { data } = await api.post('/python-analysis/execute', {
    execution_id: executionId
  })
  return data
}

export const getExecutionResult = async (
  executionId: string
): Promise<ExecutionResult> => {
  const { data } = await api.get(`/python-analysis/execution/${executionId}`)
  return data
}

export const executeWorkflow = async (
  datasetId: string,
  query: string
): Promise<any> => {
  const { data } = await api.post('/python-analysis/workflow', {
    dataset_id: datasetId,
    query
  })
  return data
}

// Deep Research
export const executeDeepResearch = async (
  datasetId: string,
  question: string,
  options?: {
    maxSubQuestions?: number
    enablePython?: boolean
    enableWorldKnowledge?: boolean
  }
): Promise<DeepResearchResult> => {
  const { data } = await api.post('/deep-research/analyze', {
    dataset_id: datasetId,
    question,
    max_sub_questions: options?.maxSubQuestions ?? 10,
    enable_python: options?.enablePython ?? true,
    enable_world_knowledge: options?.enableWorldKnowledge ?? true
  })
  return data
}

export default api
