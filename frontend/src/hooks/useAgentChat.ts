import { useState, useCallback, useEffect } from 'react'
import {
  chatWithAgent,
  listAgents,
  getAgentSession,
  generateAgentSessionName,
  type Agent,
  type AgentMessage,
  type AgentResponse
} from '@/services/api'

interface UseAgentChatOptions {
  datasetId: string
  sessionId?: string
  onSessionCreated?: (sessionId: string) => void
}

interface UseAgentChatReturn {
  messages: AgentMessage[]
  agents: Agent[]
  selectedAgent: string | undefined
  setSelectedAgent: (agentName: string | undefined) => void
  sendMessage: (query: string, agentName?: string) => Promise<void>
  isLoading: boolean
  error: string | null
  sessionId: string | undefined
  sessionName: string | undefined
  clearError: () => void
}

export function useAgentChat({
  datasetId,
  sessionId: initialSessionId,
  onSessionCreated
}: UseAgentChatOptions): UseAgentChatReturn {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId)
  const [sessionName, setSessionName] = useState<string | undefined>(undefined)

  // Load available agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const result = await listAgents()
        setAgents(result.agents.filter(a => a.enabled))
      } catch (err) {
        console.error('Failed to load agents:', err)
      }
    }
    loadAgents()
  }, [])

  // Load session messages if sessionId provided
  useEffect(() => {
    const loadSession = async () => {
      if (!sessionId) return

      try {
        const session = await getAgentSession(sessionId)
        if (session.messages) {
          setMessages(session.messages)
        }
        if (session.name) {
          setSessionName(session.name)
        }
      } catch (err) {
        console.error('Failed to load session:', err)
      }
    }
    loadSession()
  }, [sessionId])

  const sendMessage = useCallback(
    async (query: string, agentName?: string) => {
      setIsLoading(true)
      setError(null)

      // Add user message to UI immediately
      const userMessage: AgentMessage = {
        id: `temp-${Date.now()}`,
        session_id: sessionId || '',
        role: 'user',
        content: query,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, userMessage])

      try {
        const response: AgentResponse = await chatWithAgent({
          query,
          dataset_id: datasetId,
          agent_name: agentName || selectedAgent,
          session_id: sessionId,
          stream: false
        })

        // Update session ID if this is a new session
        if (!sessionId && response.session_id) {
          setSessionId(response.session_id)
          onSessionCreated?.(response.session_id)

          // Generate session name after first message
          try {
            const nameResult = await generateAgentSessionName(response.session_id)
            setSessionName(nameResult.name)
          } catch (err) {
            console.error('Failed to generate session name:', err)
          }
        }

        // Add assistant message
        const assistantMessage: AgentMessage = {
          id: `${response.session_id}-${Date.now()}`,
          session_id: response.session_id,
          role: 'assistant',
          content: response.response.summary,
          agent_name: response.agent,
          code: response.response.sql,
          result_data: response.response,
          tokens_used: response.metadata.tokens_used,
          execution_time_ms: response.metadata.execution_time_ms,
          timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev.slice(0, -1), userMessage, assistantMessage])
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to send message')
        // Remove the optimistic user message on error
        setMessages(prev => prev.slice(0, -1))
      } finally {
        setIsLoading(false)
      }
    },
    [datasetId, sessionId, selectedAgent, onSessionCreated]
  )

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    messages,
    agents,
    selectedAgent,
    setSelectedAgent,
    sendMessage,
    isLoading,
    error,
    sessionId,
    sessionName,
    clearError
  }
}
