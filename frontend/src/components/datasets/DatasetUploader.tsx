import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useUploadDataset } from '@/hooks/useDatasets'
import { useNavigate } from 'react-router-dom'

export function DatasetUploader() {
  const navigate = useNavigate()
  const uploadMutation = useUploadDataset()

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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
  })

  return (
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

        {uploadMutation.isPending && (
          <div className="mt-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
            <p className="mt-2 text-sm text-gray-500">Uploading and processing...</p>
          </div>
        )}

        {uploadMutation.isError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {uploadMutation.error instanceof Error
              ? uploadMutation.error.message
              : 'Upload failed'}
          </div>
        )}
      </div>
    </div>
  )
}
