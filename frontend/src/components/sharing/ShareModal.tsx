import { useState } from 'react'
import { X, Users, Share2, Globe, Plus, Trash2, Crown, Shield, Edit, Eye, BarChart } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from '@/services/api'

interface ShareModalProps {
  datasetId: string
  datasetName: string
  onClose: () => void
}

type DatasetRole = 'OWNER' | 'ADMIN' | 'EDITOR' | 'ANALYST' | 'VIEWER'
type SharePermission = 'VIEW' | 'QUERY' | 'EDIT' | 'ADMIN'

interface Member {
  id: string
  user_id: string
  user_email: string
  user_name: string
  role: DatasetRole
  created_at: string
}

interface Share {
  id: string
  user_id: string
  user_email: string
  user_name: string
  permission: SharePermission
  expires_at?: string
  created_at: string
}

interface PublicAccess {
  id: string
  allow_download: boolean
  allow_query: boolean
  expires_at?: string
}

const roleIcons: Record<DatasetRole, any> = {
  OWNER: Crown,
  ADMIN: Shield,
  EDITOR: Edit,
  ANALYST: BarChart,
  VIEWER: Eye
}

const roleColors: Record<DatasetRole, string> = {
  OWNER: 'text-yellow-600 bg-yellow-100',
  ADMIN: 'text-purple-600 bg-purple-100',
  EDITOR: 'text-blue-600 bg-blue-100',
  ANALYST: 'text-green-600 bg-green-100',
  VIEWER: 'text-gray-600 bg-gray-100'
}

export function ShareModal({ datasetId, datasetName, onClose }: ShareModalProps) {
  const [activeTab, setActiveTab] = useState<'members' | 'shares' | 'public'>('members')
  const [newMemberEmail, setNewMemberEmail] = useState('')
  const [newMemberRole, setNewMemberRole] = useState<DatasetRole>('VIEWER')
  const [newShareEmail, setNewShareEmail] = useState('')
  const [newSharePermission, setNewSharePermission] = useState<SharePermission>('VIEW')
  const [shareExpireDays, setShareExpireDays] = useState<number | undefined>(undefined)
  const [publicAllowDownload, setPublicAllowDownload] = useState(false)
  const [publicAllowQuery, setPublicAllowQuery] = useState(true)

  const queryClient = useQueryClient()

  // Fetch members
  const { data: members = [] } = useQuery<Member[]>({
    queryKey: ['dataset-members', datasetId],
    queryFn: async () => {
      const { data } = await axios.get(`/sharing/datasets/${datasetId}/members`)
      return data
    }
  })

  // Fetch shares
  const { data: shares = [] } = useQuery<Share[]>({
    queryKey: ['dataset-shares', datasetId],
    queryFn: async () => {
      const { data } = await axios.get(`/sharing/datasets/${datasetId}/shares`)
      return data
    }
  })

  // Fetch public access
  const { data: publicAccess } = useQuery<PublicAccess | null>({
    queryKey: ['dataset-public', datasetId],
    queryFn: async () => {
      const { data } = await axios.get(`/sharing/datasets/${datasetId}/public`)
      return data
    }
  })

  // Add member mutation
  const addMemberMutation = useMutation({
    mutationFn: async () => {
      await axios.post(`/sharing/datasets/${datasetId}/members`, {
        email: newMemberEmail,
        role: newMemberRole
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-members', datasetId] })
      setNewMemberEmail('')
    }
  })

  // Remove member mutation
  const removeMemberMutation = useMutation({
    mutationFn: async (memberId: string) => {
      await axios.delete(`/sharing/datasets/${datasetId}/members/${memberId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-members', datasetId] })
    }
  })

  // Add share mutation
  const addShareMutation = useMutation({
    mutationFn: async () => {
      await axios.post(`/sharing/datasets/${datasetId}/shares`, {
        email: newShareEmail,
        permission: newSharePermission,
        expires_days: shareExpireDays
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-shares', datasetId] })
      setNewShareEmail('')
      setShareExpireDays(undefined)
    }
  })

  // Revoke share mutation
  const revokeShareMutation = useMutation({
    mutationFn: async (shareId: string) => {
      await axios.delete(`/sharing/datasets/${datasetId}/shares/${shareId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-shares', datasetId] })
    }
  })

  // Make public mutation
  const makePublicMutation = useMutation({
    mutationFn: async () => {
      await axios.post(`/sharing/datasets/${datasetId}/public`, {
        allow_download: publicAllowDownload,
        allow_query: publicAllowQuery
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-public', datasetId] })
    }
  })

  // Revoke public mutation
  const revokePublicMutation = useMutation({
    mutationFn: async () => {
      await axios.delete(`/sharing/datasets/${datasetId}/public`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-public', datasetId] })
    }
  })

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Share Dataset</h2>
            <p className="text-sm text-gray-600 mt-1">{datasetName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex px-6">
            <button
              onClick={() => setActiveTab('members')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'members'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <Users className="h-4 w-4" />
              Team Members ({members.length})
            </button>
            <button
              onClick={() => setActiveTab('shares')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'shares'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <Share2 className="h-4 w-4" />
              External Shares ({shares.length})
            </button>
            <button
              onClick={() => setActiveTab('public')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm ${
                activeTab === 'public'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <Globe className="h-4 w-4" />
              Public Access
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'members' && (
            <div className="space-y-6">
              {/* Add Member Form */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">Add Team Member</h3>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="Enter email address"
                    value={newMemberEmail}
                    onChange={(e) => setNewMemberEmail(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <select
                    value={newMemberRole}
                    onChange={(e) => setNewMemberRole(e.target.value as DatasetRole)}
                    className="px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="VIEWER">Viewer</option>
                    <option value="ANALYST">Analyst</option>
                    <option value="EDITOR">Editor</option>
                    <option value="ADMIN">Admin</option>
                  </select>
                  <Button
                    onClick={() => addMemberMutation.mutate()}
                    disabled={!newMemberEmail || addMemberMutation.isPending}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add
                  </Button>
                </div>
              </div>

              {/* Members List */}
              <div className="space-y-2">
                {members.map((member) => {
                  const Icon = roleIcons[member.role]
                  return (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-blue-600 font-medium">
                            {member.user_name[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{member.user_name}</div>
                          <div className="text-sm text-gray-500">{member.user_email}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${roleColors[member.role]}`}>
                          <Icon className="h-3 w-3" />
                          {member.role}
                        </span>
                        {member.role !== 'OWNER' && (
                          <button
                            onClick={() => removeMemberMutation.mutate(member.id)}
                            className="text-red-600 hover:text-red-700 p-2"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {activeTab === 'shares' && (
            <div className="space-y-6">
              {/* Add Share Form */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">Share with External User</h3>
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      type="email"
                      placeholder="Enter email address"
                      value={newShareEmail}
                      onChange={(e) => setNewShareEmail(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                    />
                    <select
                      value={newSharePermission}
                      onChange={(e) => setNewSharePermission(e.target.value as SharePermission)}
                      className="px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="VIEW">View Only</option>
                      <option value="QUERY">Query</option>
                      <option value="EDIT">Edit</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </div>
                  <div className="flex gap-2 items-center">
                    <label className="text-sm text-gray-600">Expires in (days):</label>
                    <input
                      type="number"
                      placeholder="Never"
                      value={shareExpireDays || ''}
                      onChange={(e) => setShareExpireDays(e.target.value ? parseInt(e.target.value) : undefined)}
                      className="w-24 px-3 py-2 border border-gray-300 rounded-lg"
                    />
                    <Button
                      onClick={() => addShareMutation.mutate()}
                      disabled={!newShareEmail || addShareMutation.isPending}
                      className="ml-auto"
                    >
                      <Share2 className="h-4 w-4 mr-2" />
                      Share
                    </Button>
                  </div>
                </div>
              </div>

              {/* Shares List */}
              <div className="space-y-2">
                {shares.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No external shares yet
                  </div>
                ) : (
                  shares.map((share) => (
                    <div
                      key={share.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-purple-600 font-medium">
                            {share.user_name[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{share.user_name}</div>
                          <div className="text-sm text-gray-500">{share.user_email}</div>
                          {share.expires_at && (
                            <div className="text-xs text-orange-600">
                              Expires: {new Date(share.expires_at).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium">
                          {share.permission}
                        </span>
                        <button
                          onClick={() => revokeShareMutation.mutate(share.id)}
                          className="text-red-600 hover:text-red-700 p-2"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'public' && (
            <div className="space-y-6">
              {publicAccess ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-medium text-green-900">Public Access Enabled</h3>
                      <p className="text-sm text-green-700 mt-1">
                        Anyone with the link can access this dataset
                      </p>
                    </div>
                    <Button
                      onClick={() => revokePublicMutation.mutate()}
                      variant="outline"
                      className="border-red-200 text-red-600 hover:bg-red-50"
                    >
                      Revoke Access
                    </Button>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <input type="checkbox" checked={publicAccess.allow_query} disabled className="rounded" />
                      <span>Allow queries</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <input type="checkbox" checked={publicAccess.allow_download} disabled className="rounded" />
                      <span>Allow downloads</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Make Dataset Public</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Share this dataset with anyone. They won't need to sign in.
                  </p>
                  <div className="space-y-3 mb-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={publicAllowQuery}
                        onChange={(e) => setPublicAllowQuery(e.target.checked)}
                        className="rounded"
                      />
                      <span className="text-sm">Allow queries</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={publicAllowDownload}
                        onChange={(e) => setPublicAllowDownload(e.target.checked)}
                        className="rounded"
                      />
                      <span className="text-sm">Allow downloads</span>
                    </label>
                  </div>
                  <Button
                    onClick={() => makePublicMutation.mutate()}
                    disabled={makePublicMutation.isPending}
                    className="w-full"
                  >
                    <Globe className="h-4 w-4 mr-2" />
                    Make Public
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
