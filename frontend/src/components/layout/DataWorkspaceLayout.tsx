import { ReactNode, useState } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface DataWorkspaceLayoutProps {
  sidebar: ReactNode
  header: ReactNode
  children: ReactNode
}

export function DataWorkspaceLayout({ sidebar, header, children }: DataWorkspaceLayoutProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <PanelGroup direction="horizontal">
        {/* Left Sidebar (Chat) - Collapsible & Resizable */}
        {!isSidebarCollapsed && (
          <>
            <Panel
              defaultSize={25}
              minSize={15}
              maxSize={40}
              className="border-r border-gray-200 h-full"
            >
              {sidebar}
            </Panel>
            <PanelResizeHandle className="w-1 bg-gray-200 hover:bg-blue-400 transition-colors relative group">
              <div className="absolute inset-y-0 -right-3 w-6 flex items-center justify-center">
                <button
                  onClick={() => setIsSidebarCollapsed(true)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity bg-gray-200 hover:bg-gray-300 rounded-full p-1"
                  title="Collapse sidebar"
                >
                  <ChevronLeft className="h-3 w-3 text-gray-600" />
                </button>
              </div>
            </PanelResizeHandle>
          </>
        )}

        {/* Collapsed Sidebar Button */}
        {isSidebarCollapsed && (
          <div className="w-12 border-r border-gray-200 bg-gray-50 flex items-center justify-center">
            <button
              onClick={() => setIsSidebarCollapsed(false)}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              title="Expand sidebar"
            >
              <ChevronRight className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        )}

        {/* Main Content Area */}
        <Panel className="flex flex-col min-w-0">
          {/* Top Header */}
          <div className="h-auto border-b border-gray-200">
            {header}
          </div>

          {/* Workspace (Tabs/Canvas) */}
          <div className="flex-1 overflow-hidden bg-gray-50 relative">
            {children}
          </div>
        </Panel>
      </PanelGroup>
    </div>
  )
}
