import { useState, useEffect } from 'react'
import { Sparkles, TrendingUp, Users, DollarSign, Calendar, Search } from 'lucide-react'
import axios from '@/services/api'
import { DataScoutPanel } from './DataScoutPanel'

interface SuggestedAnalysis {
  id: string
  title: string
  description: string
  icon: 'trending' | 'users' | 'dollar' | 'calendar'
  query: string
  category: 'overview' | 'trends' | 'insights'
}

interface DatasetHubProps {
  datasetId: string
  datasetName: string
  onQuerySelect: (query: string) => void
}

const iconMap = {
  trending: TrendingUp,
  users: Users,
  dollar: DollarSign,
  calendar: Calendar,
}

export function DatasetHub({ datasetId, datasetName, onQuerySelect }: DatasetHubProps) {
  const [suggestions, setSuggestions] = useState<SuggestedAnalysis[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [quickStartTemplates] = useState([
    {
      id: 'overview',
      title: 'Dataset Overview',
      description: 'Get a comprehensive summary of your data',
      icon: 'trending' as const,
    },
    {
      id: 'trends',
      title: 'Analyze Trends',
      description: 'Discover patterns and trends over time',
      icon: 'calendar' as const,
    },
    {
      id: 'top-performers',
      title: 'Identify Top Performers',
      description: 'Find the highest performing segments',
      icon: 'users' as const,
    },
    {
      id: 'revenue-analysis',
      title: 'Revenue Analysis',
      description: 'Analyze revenue by different dimensions',
      icon: 'dollar' as const,
    },
  ])

  useEffect(() => {
    loadSuggestions()
  }, [datasetId])

  const loadSuggestions = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsLoading(false)
        return
      }

      // Call AI suggestions endpoint
      const response = await axios.post(
        `/datasets/${datasetId}/ai-suggestions`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setSuggestions(response.data.suggestions || [])
    } catch (error) {
      console.error('Failed to load AI suggestions:', error)
      // Fallback to empty suggestions
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleTemplateClick = (templateId: string) => {
    const queries: Record<string, string> = {
      overview: 'Give me an overview of this dataset with key statistics',
      trends: 'Show me trends over time in this data',
      'top-performers': 'What are the top 10 items by value?',
      'revenue-analysis': 'Analyze revenue by category and region',
    }
    onQuerySelect(queries[templateId] || queries.overview)
  }

  return (
    <div className="h-full overflow-auto bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-8 py-12">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{datasetName}</h1>
              <p className="text-gray-600 mt-1">What would you like to discover today?</p>
            </div>
          </div>
        </div>

        {/* Data Scout Panel - First Look */}
        <div className="mb-12">
          <DataScoutPanel
            datasetId={datasetId}
            datasetName={datasetName}
            onQuestionClick={(question) => onQuerySelect(question)}
          />
        </div>

        {/* AI-Generated Suggestions */}
        {isLoading ? (
          <div className="mb-12">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles className="h-5 w-5 text-purple-600 animate-pulse" />
              <h2 className="text-xl font-semibold text-gray-800">Generating insights...</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-48 bg-white rounded-xl border border-gray-200 animate-pulse" />
              ))}
            </div>
          </div>
        ) : suggestions.length > 0 ? (
          <div className="mb-12">
            <div className="flex items-center gap-2 mb-6">
              <Sparkles className="h-5 w-5 text-purple-600" />
              <h2 className="text-xl font-semibold text-gray-800">AI-Suggested Analyses</h2>
              <span className="text-sm text-gray-500">Based on your data structure</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {suggestions.map((suggestion) => {
                const Icon = iconMap[suggestion.icon] || TrendingUp
                return (
                  <button
                    key={suggestion.id}
                    onClick={() => onQuerySelect(suggestion.query)}
                    className="group relative bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition-all p-6 text-left"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg group-hover:scale-110 transition-transform">
                        <Icon className="h-6 w-6 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                          {suggestion.title}
                        </h3>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          {suggestion.description}
                        </p>
                        <div className="mt-3 flex items-center gap-2 text-xs text-blue-600 font-medium">
                          <Search className="h-3 w-3" />
                          Click to analyze
                        </div>
                      </div>
                    </div>
                    <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-lg">→</span>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        ) : null}

        {/* Quick Start Templates */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">Quick Start</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickStartTemplates.map((template) => {
              const Icon = iconMap[template.icon]
              return (
                <button
                  key={template.id}
                  onClick={() => handleTemplateClick(template.id)}
                  className="group bg-white rounded-xl border-2 border-gray-200 hover:border-green-400 hover:shadow-lg transition-all p-6 text-left"
                >
                  <div className="mb-4">
                    <div className="inline-flex p-3 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg group-hover:scale-110 transition-transform">
                      <Icon className="h-6 w-6 text-green-600" />
                    </div>
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-green-600 transition-colors">
                    {template.title}
                  </h3>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {template.description}
                  </p>
                </button>
              )
            })}
          </div>
        </div>

        {/* Call to Action */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold mb-2">Have a specific question?</h3>
              <p className="text-blue-100">
                Use the chat sidebar to ask anything about your data in natural language
              </p>
            </div>
            <div className="hidden lg:block">
              <div className="h-24 w-24 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                <Search className="h-12 w-12 text-white" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
