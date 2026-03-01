import { ReactNode, useState } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface DataWorkspaceLayoutProps {
  sidebar: ReactNode
  header: ReactNode
  children: ReactNode
  isSidebarCollapsed?: boolean
  onSidebarCollapsedChange?: (v: boolean) => void
}

export function DataWorkspaceLayout({
  sidebar,
  header,
  children,
  isSidebarCollapsed: externalCollapsed,
  onSidebarCollapsedChange,
}: DataWorkspaceLayoutProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false)

  // Use external control when provided, fall back to internal state
  const isSidebarCollapsed = externalCollapsed ?? internalCollapsed
  const setIsSidebarCollapsed = (v: boolean) => {
    setInternalCollapsed(v)
    onSidebarCollapsedChange?.(v)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <PanelGroup direction="horizontal">
        {/* Left Sidebar (Chat) - Collapsible & Resizable */}
        {!isSidebarCollapsed && (
          <>
            <Panel
              defaultSize={25}
              minSize={15}
              maxSize={40}
              className="border-r border-border h-full"
            >
              {sidebar}
            </Panel>
            <PanelResizeHandle className="w-1 bg-border hover:bg-blue-400 transition-colors relative group">
              <div className="absolute inset-y-0 -right-3 w-6 flex items-center justify-center">
                <button
                  onClick={() => setIsSidebarCollapsed(true)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity bg-muted hover:bg-muted/80 rounded-full p-1"
                  title="Collapse sidebar"
                >
                  <ChevronLeft className="h-3 w-3 text-muted-foreground" />
                </button>
              </div>
            </PanelResizeHandle>
          </>
        )}

        {/* Collapsed Sidebar Button */}
        {isSidebarCollapsed && (
          <div className="w-12 border-r border-border bg-muted/30 flex items-center justify-center">
            <button
              onClick={() => setIsSidebarCollapsed(false)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Expand sidebar"
            >
              <ChevronRight className="h-5 w-5 text-muted-foreground" />
            </button>
          </div>
        )}

        {/* Main Content Area */}
        <Panel className="flex flex-col min-w-0">
          {/* Top Header */}
          <div className="h-auto border-b border-border">
            {header}
          </div>

          {/* Workspace (Tabs/Canvas) */}
          <div className="flex-1 overflow-hidden bg-muted/20 relative">
            {children}
          </div>
        </Panel>
      </PanelGroup>
    </div>
  )
}
