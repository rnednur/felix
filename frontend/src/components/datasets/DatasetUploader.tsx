import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useUploadDataset, useImportGoogleSheets } from '@/hooks/useDatasets'
import { useNavigate } from 'react-router-dom'
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google'

interface DatasetUploaderContentProps {
  hasGoogleOAuth: boolean
}

function DatasetUploaderContent({ hasGoogleOAuth }: DatasetUploaderContentProps) {
  const navigate = useNavigate()
  const uploadMutation = useUploadDataset()
  const importSheetsMutation = useImportGoogleSheets()
  const [showGoogleInput, setShowGoogleInput] = useState(false)
  const [googleSheetsUrl, setGoogleSheetsUrl] = useState('')

  const onDrop = useCallback((files: File[]) => {
    const file = files[0]
    const formData = new FormData()
    formData.append('file', file)

    uploadMutation.mutate(formData, {
      onSuccess: (data) => {
        navigate(`/datasets/${data.id}`)
      },
    })
  }, [uploadMutation, navigate])

  // Only use Google Login hook if OAuth is configured
  const googleLogin = hasGoogleOAuth
    ? useGoogleLogin({
        onSuccess: async (tokenResponse) => {
          if (!googleSheetsUrl) {
            alert('Please enter a Google Sheets URL')
            return
          }

          importSheetsMutation.mutate(
            {
              google_sheets_url: googleSheetsUrl,
              access_token: tokenResponse.access_token,
            },
            {
              onSuccess: (data) => {
                setShowGoogleInput(false)
                setGoogleSheetsUrl('')
                navigate(`/datasets/${data.id}`)
              },
              onError: (error: any) => {
                alert(error.response?.data?.detail || 'Failed to import Google Sheet')
              },
            }
          )
        },
        scope: 'https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/spreadsheets.readonly',
      })
    : () => {}

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
  })

  const isLoading = uploadMutation.isPending || importSheetsMutation.isPending

  return (
    <div className="space-y-6">
      {/* File Upload */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        `}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>

          <div>
            <p className="text-lg text-gray-600">
              {isDragActive
                ? 'Drop file here...'
                : 'Drag & drop CSV or XLSX, or click to browse'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Maximum file size: 100MB
            </p>
          </div>

          {uploadMutation.isError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {uploadMutation.error instanceof Error
                ? uploadMutation.error.message
                : 'Upload failed'}
            </div>
          )}
        </div>
      </div>

      {/* Google Sheets Import - Only show if OAuth is configured */}
      {hasGoogleOAuth && (
        <>
          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>

          {/* Google Sheets Import */}
          <div className="border-2 border-gray-300 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <svg className="h-8 w-8" viewBox="0 0 48 48" fill="none">
                <path fill="#0F9D58" d="M29,6H14.5C13,6,11.8,7.2,11.8,8.7v30.6c0,1.5,1.2,2.7,2.7,2.7h19.1c1.5,0,2.7-1.2,2.7-2.7V17L29,6z"/>
                <path fill="#F1F1F1" d="M31,17h5l-7-11v8.5C29,15.9,29.6,17,31,17z"/>
                <path fill="#87CEAC" d="M17,33h14v-3H17V33z M17,27h14v-3H17V27z M17,21h9v-3h-9V21z"/>
              </svg>
              <h3 className="text-lg font-medium text-gray-900">Import from Google Sheets</h3>
            </div>

            {!showGoogleInput ? (
              <button
                onClick={() => setShowGoogleInput(true)}
                className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
              >
                Import from Google Sheets
              </button>
            ) : (
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Paste Google Sheets URL here..."
                  value={googleSheetsUrl}
                  onChange={(e) => setGoogleSheetsUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => googleLogin()}
                    disabled={!googleSheetsUrl || isLoading}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    Connect & Import
                  </button>
                  <button
                    onClick={() => {
                      setShowGoogleInput(false)
                      setGoogleSheetsUrl('')
                    }}
                    disabled={isLoading}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
                {importSheetsMutation.isError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                    {importSheetsMutation.error instanceof Error
                      ? importSheetsMutation.error.message
                      : 'Import failed'}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          <p className="ml-3 text-sm text-gray-500">
            {uploadMutation.isPending ? 'Uploading and processing...' : 'Importing from Google Sheets...'}
          </p>
        </div>
      )}
    </div>
  )
}

export function DatasetUploader() {
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  const hasGoogleOAuth = !!googleClientId

  if (!hasGoogleOAuth) {
    // Fallback to file upload only if Google OAuth not configured
    return <DatasetUploaderContent hasGoogleOAuth={false} />
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <DatasetUploaderContent hasGoogleOAuth={true} />
    </GoogleOAuthProvider>
  )
}
