import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toolCalls, clients } from '../services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ChevronLeft, ChevronRight, Search, Activity, Clock, AlertCircle, CheckCircle, Users } from 'lucide-react'
import ToolCallDetailDialog from './ToolCallDetailDialog'

export default function ToolCallsTable({ clientId = null, title = "Tool Call Analytics", showClientColumn = false }) {
  const [params, setParams] = useState({
    limit: 25,
    offset: 0,
    order_by: "created_at",
    order_dir: "desc",
    search: "",
    tool_name: "",
    client_id: "",
  })
  const [selectedToolCall, setSelectedToolCall] = useState(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['tool-calls', { clientId, ...params }],
    queryFn: () => {
      if (clientId) {
        return toolCalls.listForClient(clientId, params)
      }
      return toolCalls.list({ ...params, client_id: params.client_id || null })
    },
    keepPreviousData: true,
  })

  // Fetch clients list if showing client column and not already filtered by a client
  const { data: clientsData } = useQuery({
    queryKey: ['clients'],
    queryFn: clients.list,
    enabled: showClientColumn && !clientId
  })

  const handleSearch = (value) => {
    setParams(prev => ({ ...prev, search: value, offset: 0 }))
  }

  const handleToolFilter = (value) => {
    setParams(prev => ({ ...prev, tool_name: value === "all" ? "" : value, offset: 0 }))
  }

  const handleClientFilter = (value) => {
    setParams(prev => ({ ...prev, client_id: value === "all" ? "" : value, offset: 0 }))
  }

  const handleSort = (column) => {
    setParams(prev => ({
      ...prev,
      order_by: column,
      order_dir: prev.order_by === column && prev.order_dir === "desc" ? "asc" : "desc",
      offset: 0
    }))
  }

  const handlePageChange = (newOffset) => {
    setParams(prev => ({ ...prev, offset: newOffset }))
  }

  const handleRowClick = (toolCall) => {
    setSelectedToolCall(toolCall)
    setShowDetailDialog(true)
  }

  const formatDuration = (ms) => {
    if (ms === null || ms === undefined) return 'N/A'
    if (ms === 0) return '<1ms'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const truncateJson = (data, maxLength = 30) => {
    if (!data) return 'null'
    const str = JSON.stringify(data)
    if (str.length <= maxLength) return str
    return str.substring(0, maxLength) + '...'
  }

  const extractAndTruncateText = (data, maxLength = 25) => {
    if (!data) return 'null'
    
    // If it's an array (like text content), extract the text
    if (Array.isArray(data)) {
      const textItem = data.find(item => item.type === "text")
      if (textItem && textItem.text) {
        if (textItem.text.length <= maxLength) return textItem.text
        return textItem.text.substring(0, maxLength) + '...'
      }
    }
    
    // For JSON objects, stringify them
    const str = JSON.stringify(data)
    if (str.length <= maxLength) return str
    return str.substring(0, maxLength) + '...'
  }

  const totalPages = data ? Math.ceil(data.total_count / params.limit) : 0
  const currentPage = Math.floor(params.offset / params.limit) + 1

  // Extract unique tool names for filter
  const uniqueTools = data?.tool_calls 
    ? [...new Set(data.tool_calls.map(call => call.tool_name))].sort()
    : []

  // Create client name lookup map
  const clientMap = clientsData ? 
    Object.fromEntries(clientsData.map(client => [client.id, client.name])) : {}

  // Get client name by ID
  const getClientName = (clientId) => {
    return clientMap[clientId] || `Client ${clientId.substring(0, 8)}...`
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span>Error loading tool calls: {error.message}</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Activity className="mr-2 h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>
          {data ? `${data.total_count} total tool calls` : 'Loading tool call history...'}
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Filters */}
        <div className="mb-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search tool calls..."
                  value={params.search}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="tool-filter">Filter by Tool</Label>
              <Select value={params.tool_name || "all"} onValueChange={handleToolFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All tools" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All tools</SelectItem>
                  {uniqueTools.map(tool => (
                    <SelectItem key={tool} value={tool}>{tool}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {showClientColumn && !clientId && (
              <div className="space-y-2">
                <Label htmlFor="client-filter">Filter by Client</Label>
                <Select value={params.client_id || "all"} onValueChange={handleClientFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="All clients" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All clients</SelectItem>
                    {clientsData?.map(client => (
                      <SelectItem key={client.id} value={client.id}>{client.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}

        {/* Table */}
        {data && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleSort('created_at')}
                        className="font-semibold"
                      >
                        Time
                        {params.order_by === 'created_at' && (
                          <span className="ml-1">
                            {params.order_dir === 'desc' ? '↓' : '↑'}
                          </span>
                        )}
                      </Button>
                    </th>
                    {showClientColumn && (
                      <th className="text-left p-2">
                        <div className="font-semibold flex items-center">
                          <Users className="mr-1 h-3 w-3" />
                          Client
                        </div>
                      </th>
                    )}
                    <th className="text-left p-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleSort('tool_name')}
                        className="font-semibold"
                      >
                        Tool
                        {params.order_by === 'tool_name' && (
                          <span className="ml-1">
                            {params.order_dir === 'desc' ? '↓' : '↑'}
                          </span>
                        )}
                      </Button>
                    </th>
                    <th className="text-left p-2">Status</th>
                    <th className="text-left p-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleSort('execution_time_ms')}
                        className="font-semibold"
                      >
                        <Clock className="mr-1 h-3 w-3" />
                        <span className="hidden sm:inline">Duration</span>
                        <span className="sm:hidden">Time</span>
                        {params.order_by === 'execution_time_ms' && (
                          <span className="ml-1">
                            {params.order_dir === 'desc' ? '↓' : '↑'}
                          </span>
                        )}
                      </Button>
                    </th>
                    <th className="text-left p-2 hidden lg:table-cell w-32">Input</th>
                    <th className="text-left p-2 hidden lg:table-cell w-32">Output</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tool_calls.map((call) => (
                    <tr 
                      key={call.id} 
                      className="border-b hover:bg-muted/50 cursor-pointer"
                      onClick={() => handleRowClick(call)}
                    >
                      <td className="p-2 text-xs sm:text-sm text-muted-foreground">
                        <div className="hidden sm:block">{formatDate(call.created_at)}</div>
                        <div className="sm:hidden">{new Date(call.created_at).toLocaleDateString()}</div>
                      </td>
                      {showClientColumn && (
                        <td className="p-2">
                          <Badge variant="secondary" className="text-xs">
                            {getClientName(call.client_id)}
                          </Badge>
                        </td>
                      )}
                      <td className="p-2">
                        <Badge variant="outline" className="text-xs">{call.tool_name}</Badge>
                      </td>
                      <td className="p-2">
                        {call.error_message ? (
                          <Badge variant="destructive" className="flex items-center w-fit text-xs">
                            <AlertCircle className="mr-1 h-3 w-3" />
                            <span className="hidden sm:inline">Failed</span>
                            <span className="sm:hidden">✗</span>
                          </Badge>
                        ) : (
                          <Badge variant="default" className="flex items-center w-fit bg-green-100 text-green-800 text-xs">
                            <CheckCircle className="mr-1 h-3 w-3" />
                            <span className="hidden sm:inline">Success</span>
                            <span className="sm:hidden">✓</span>
                          </Badge>
                        )}
                      </td>
                      <td className="p-2 text-xs sm:text-sm">
                        {formatDuration(call.execution_time_ms)}
                      </td>
                      <td className="p-2 hidden lg:table-cell w-32">
                        <code className="text-xs bg-muted px-1 py-0.5 rounded block truncate">
                          {truncateJson(call.input_data, 25)}
                        </code>
                      </td>
                      <td className="p-2 hidden lg:table-cell w-32">
                        {call.error_message ? (
                          <span className="text-xs text-destructive block truncate">
                            {call.error_message.length > 25 
                              ? call.error_message.substring(0, 25) + '...'
                              : call.error_message
                            }
                          </span>
                        ) : call.output_json ? (
                          <code className="text-xs bg-blue-50 text-blue-800 px-1 py-0.5 rounded block truncate">
                            {truncateJson(call.output_json, 25)}
                          </code>
                        ) : call.output_text ? (
                          <code className="text-xs bg-muted px-1 py-0.5 rounded block truncate">
                            {extractAndTruncateText(call.output_text, 25)}
                          </code>
                        ) : (
                          <span className="text-xs text-muted-foreground">No output</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-6">
                <div className="text-xs sm:text-sm text-muted-foreground">
                  Showing {params.offset + 1} to {Math.min(params.offset + params.limit, data.total_count)} of {data.total_count} results
                </div>
                
                <div className="flex items-center justify-center sm:justify-end space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(Math.max(0, params.offset - params.limit))}
                    disabled={params.offset === 0}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span className="hidden sm:inline">Previous</span>
                  </Button>
                  
                  <span className="text-xs sm:text-sm px-2">
                    Page {currentPage} of {totalPages}
                  </span>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(params.offset + params.limit)}
                    disabled={params.offset + params.limit >= data.total_count}
                  >
                    <span className="hidden sm:inline">Next</span>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            {/* Empty state */}
            {data.tool_calls.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No tool calls found matching your criteria.
              </div>
            )}
          </>
        )}
      </CardContent>

      {/* Tool Call Detail Dialog */}
      <ToolCallDetailDialog
        toolCall={selectedToolCall}
        isOpen={showDetailDialog}
        onOpenChange={setShowDetailDialog}
      />
    </Card>
  )
}