import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DatasetHub } from '@/components/datasets/DatasetHub'
import { IconButton } from '@/components/ui/icon-button'
import { ArrowLeft } from 'lucide-react'

export default function Home() {
  const navigate = useNavigate()
  const [lastDatasetId, setLastDatasetId] = useState<string | null>(null)

  useEffect(() => {
    // Check if there's a last viewed dataset in localStorage
    const lastId = localStorage.getItem('lastViewedDatasetId')
    setLastDatasetId(lastId)
  }, [])

  const handleBackToDataset = () => {
    if (lastDatasetId) {
      navigate(`/datasets/${lastDatasetId}`)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
            <svg className="h-10 w-10 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2c-1.1 0-2 .9-2 2v2c0 1.1.9 2 2 2s2-.9 2-2V4c0-1.1-.9-2-2-2zm-9 9c0-1.1.9-2 2-2h2c1.1 0 2 .9 2 2s-.9 2-2 2H5c-1.1 0-2-.9-2-2zm14 0c0-1.1.9-2 2-2h2c1.1 0 2 .9 2 2s-.9 2-2 2h-2c-1.1 0-2-.9-2-2zM12 16c-2.2 0-4 1.8-4 4v2h8v-2c0-2.2-1.8-4-4-4zm-6.8-3.2l-1.4-1.4c-.8-.8-.8-2 0-2.8.8-.8 2-.8 2.8 0l1.4 1.4c.8.8.8 2 0 2.8-.8.8-2 .8-2.8 0zm13.6 0c-.8.8-2 .8-2.8 0-.8-.8-.8-2 0-2.8l1.4-1.4c.8-.8 2-.8 2.8 0 .8.8.8 2 0 2.8l-1.4 1.4zM12 13c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1z"/>
            </svg>
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Felix
            </h1>
            <p className="mt-1 text-gray-600">
              Upload your data and start asking questions in natural language
            </p>
          </div>
        </div>

        {/* Back to last dataset button */}
        {lastDatasetId && (
          <IconButton
            variant="default"
            size="md"
            tooltip="Back to Dataset"
            onClick={handleBackToDataset}
          >
            <ArrowLeft className="h-5 w-5" />
          </IconButton>
        )}
      </div>

      <DatasetHub />
    </div>
  )
}
