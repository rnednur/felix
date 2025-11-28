import { useMutation } from '@tanstack/react-query'
import api from '@/services/api'

export interface PresentationRequest {
  research_id?: string
  research_result?: any
  theme?: 'professional' | 'modern' | 'corporate' | 'vibrant'
  include_verbose?: boolean
}

export interface PresentationResponse {
  success: boolean
  message: string
  file_path: string
  file_name: string
  file_size: number
  data: string  // base64 encoded PPTX
  theme: string
}

export function useGeneratePresentation() {
  return useMutation({
    mutationFn: async (request: PresentationRequest) => {
      const response = await api.post<PresentationResponse>(
        '/deep-research/generate-presentation',
        request
      )
      return response.data
    }
  })
}

export function downloadPresentation(filename: string) {
  const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'
  window.open(`${apiUrl}/deep-research/download-presentation/${filename}`, '_blank')
}

export function downloadPresentationFromBase64(base64Data: string, filename: string) {
  // Convert base64 to blob
  const byteCharacters = atob(base64Data)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const blob = new Blob([byteArray], {
    type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  })

  // Create download link
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
