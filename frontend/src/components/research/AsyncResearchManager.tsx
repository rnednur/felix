import { useEffect, useState } from 'react'
import { useSubmitResearchJob, useJobStatus } from '@/hooks/useResearchJobs'
import { useToast } from '@/components/ui/toast'
import { Loader2 } from 'lucide-react'

interface AsyncResearchManagerProps {
  datasetId: string
  question: string
  verbose: number
  onComplete: (result: any) => void
  onError?: (error: string) => void
  triggerSubmit: boolean
  onSubmitted?: () => void
}

export function AsyncResearchManager({
  datasetId,
  question,
  verbose,
  onComplete,
  onError,
  triggerSubmit,
  onSubmitted
}: AsyncResearchManagerProps) {
  const [jobId, setJobId] = useState<string | null>(null)
  const [toastId, setToastId] = useState<string | null>(null)
  const submitJob = useSubmitResearchJob()
  const { addToast, updateToast, removeToast } = useToast()

  // Poll for job status when we have a job ID
  const { data: jobStatus } = useJobStatus(jobId, {
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Stop polling if job is completed, failed, or cancelled
      if (data?.status === 'completed' || data?.status === 'failed' || data?.status === 'cancelled') {
        return false
      }
      // Poll every 2 seconds while running
      return 2000
    }
  })

  // Submit job when triggered
  useEffect(() => {
    if (triggerSubmit && !jobId) {
      submitJob.mutate(
        { datasetId, question, verbose },
        {
          onSuccess: (data) => {
            setJobId(data.job_id)

            // Show loading toast
            const id = addToast({
              title: 'Research job started',
              description: 'Your deep research analysis is running in the background...',
              type: 'loading'
            })
            setToastId(id)

            onSubmitted?.()
          },
          onError: (error: any) => {
            addToast({
              title: 'Failed to start research',
              description: error.message || 'An error occurred',
              type: 'error'
            })
            onError?.(error.message)
          }
        }
      )
    }
  }, [triggerSubmit, jobId])

  // Handle job status updates
  useEffect(() => {
    if (!jobStatus || !toastId) return

    // Update toast with progress
    if (jobStatus.status === 'running') {
      updateToast(toastId, {
        title: 'Research in progress',
        description: `${jobStatus.current_stage || 'Processing...'} (${jobStatus.progress_percentage}%)`,
        type: 'loading'
      })
    }

    // Handle completion
    if (jobStatus.status === 'completed' && jobStatus.result) {
      removeToast(toastId)

      // Show success notification
      const successToastId = addToast({
        title: 'Research completed!',
        description: `Analysis finished in ${jobStatus.execution_time_seconds}s`,
        type: 'success',
        duration: 7000,
        action: {
          label: 'View Results',
          onClick: () => {
            onComplete(jobStatus.result)
            removeToast(successToastId)
          }
        }
      })

      // Show browser notification if permission granted
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Research Completed', {
          body: 'Your deep research analysis has finished',
          icon: '/favicon.ico'
        })
      }

      // Auto-load results after 3 seconds
      setTimeout(() => {
        onComplete(jobStatus.result)
        removeToast(successToastId)
      }, 3000)
    }

    // Handle failure
    if (jobStatus.status === 'failed') {
      removeToast(toastId)

      addToast({
        title: 'Research failed',
        description: jobStatus.error_message || 'An error occurred during analysis',
        type: 'error',
        duration: 10000
      })

      onError?.(jobStatus.error_message || 'Research failed')
    }
  }, [jobStatus, toastId])

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  return null // This is a headless component
}
