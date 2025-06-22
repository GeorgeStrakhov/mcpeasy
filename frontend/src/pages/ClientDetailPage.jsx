import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clients, apiKeys, tools } from '../services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { ArrowLeft, Plus, Copy, Settings, Key, Shield, Pickaxe, BookOpenText, BarChart3, Trash2, MessageSquare } from 'lucide-react'
import ToolConfigurationDialog from '@/components/ToolConfigurationDialog'
import ResourceConfigurationDialog from '@/components/ResourceConfigurationDialog'
import ToolCallsStats from '@/components/ToolCallsStats'
import ToolCallsTable from '@/components/ToolCallsTable'
import SystemPromptPanel from '@/components/SystemPromptPanel'
import config from '@/config'

export default function ClientDetailPage() {
  const { clientId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  
  const [showKeyDialog, setShowKeyDialog] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [selectedKey, setSelectedKey] = useState(null)
  const [showKeyRemoveDialog, setShowKeyRemoveDialog] = useState(false)
  const [selectedTool, setSelectedTool] = useState(null)
  const [showToolDialog, setShowToolDialog] = useState(false)
  const [showToolRemoveDialog, setShowToolRemoveDialog] = useState(false)
  const [selectedResource, setSelectedResource] = useState(null)
  const [showResourceDialog, setShowResourceDialog] = useState(false)
  const [selectedToolToAdd, setSelectedToolToAdd] = useState(null)

  const { data: client, isLoading } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => clients.get(clientId),
  })

  const createKeyMutation = useMutation({
    mutationFn: (data) => apiKeys.create(clientId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries(['client', clientId])
      setShowKeyDialog(false)
      setNewKeyName('')
      toast({
        title: "API key created",
        description: `Successfully created "${data.name}".`,
      })
    },
    onError: (error) => {
      toast({
        title: "Error creating API key",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const deleteKeyMutation = useMutation({
    mutationFn: (keyValue) => apiKeys.delete(keyValue),
    onSuccess: () => {
      queryClient.invalidateQueries(['client', clientId])
      setShowKeyRemoveDialog(false)
      setSelectedKey(null)
      toast({
        title: "API key deleted",
        description: `Successfully deleted "${selectedKey?.name}".`,
      })
    },
    onError: (error) => {
      toast({
        title: "Error deleting API key",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const removeToolMutation = useMutation({
    mutationFn: (toolName) => tools.delete(clientId, toolName),
    onSuccess: () => {
      queryClient.invalidateQueries(['client', clientId])
      setShowToolRemoveDialog(false)
      setSelectedTool(null)
      toast({
        title: "Tool removed",
        description: `Successfully removed ${selectedTool?.name}.`,
      })
    },
    onError: (error) => {
      toast({
        title: "Error removing tool",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const handleCreateKey = (e) => {
    e.preventDefault()
    createKeyMutation.mutate({ name: newKeyName })
  }

  const handleKeyRemove = (key) => {
    setSelectedKey(key)
    setShowKeyRemoveDialog(true)
  }

  const addToolMutation = useMutation({
    mutationFn: ({ toolName, config }) => tools.configure(clientId, toolName, config),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries(['client', clientId])
      setSelectedToolToAdd(null)
      toast({
        title: "Tool added",
        description: `Successfully added ${variables.toolName}.`,
      })
    },
    onError: (error) => {
      toast({
        title: "Error adding tool",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const handleToolAdd = (tool) => {
    // For tools that don't require config, add them directly
    addToolMutation.mutate({
      toolName: tool.name,
      config: null
    })
  }

  const handleToolConfigure = (tool) => {
    setSelectedTool(tool)
    setShowToolDialog(true)
  }

  const handleToolRemove = (tool) => {
    setSelectedTool(tool)
    setShowToolRemoveDialog(true)
  }

  const handleResourceConfigure = (resource) => {
    setSelectedResource(resource)
    setShowResourceDialog(true)
  }

  const copyToClipboard = async (text, description) => {
    try {
      await navigator.clipboard.writeText(text)
      toast({
        title: "Copied to clipboard",
        description: description,
      })
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy to clipboard.",
        variant: "destructive",
      })
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4">
          <div className="flex items-center py-4 sm:py-6">
            <Button
              variant="ghost"
              onClick={() => navigate('/')}
              className="mr-3 sm:mr-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              <span className="hidden sm:inline">Back</span>
            </Button>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold">{client?.client?.name}</h1>
              {client?.client?.description && (
                <p className="text-muted-foreground text-sm sm:text-base">{client.client.description}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-4 sm:py-8">
        <Tabs defaultValue="configuration" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="configuration">Configuration</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="logs">Tool Logs</TabsTrigger>
          </TabsList>

          <TabsContent value="configuration" className="space-y-6">
            {/* API Keys and System Prompt - Side by side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
              {/* API Keys */}
              <Card>
                <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <CardTitle className="flex items-center text-lg sm:text-xl">
                      <Key className="mr-2 h-4 sm:h-5 w-4 sm:w-5" />
                      API Keys
                    </CardTitle>
                    <CardDescription className="text-sm">Manage API keys for this client</CardDescription>
                  </div>
                  <Button onClick={() => setShowKeyDialog(true)} className="w-full sm:w-auto">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Key
                  </Button>
                </CardHeader>

                <CardContent>
                  <div className="space-y-4">
                    {client?.api_keys?.map((key) => (
                      <div key={key.id} className="p-3 sm:p-4 border rounded-lg">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 sm:gap-2 mb-2">
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-sm sm:text-base">{key.name}</h3>
                            <p className="text-xs text-muted-foreground font-mono break-all mt-1">
                              {key.key_value}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              Created: {new Date(key.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(
                                config.getMcpUrl(key.key_value),
                                "MCP URL copied to clipboard"
                              )}
                              className="flex-shrink-0"
                            >
                              <Copy className="h-4 w-4 mr-2 sm:mr-0" />
                              <span className="sm:hidden">Copy MCP URL</span>
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleKeyRemove(key)}
                              className="flex-shrink-0 text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-1 sm:mr-0" />
                              <span className="sm:hidden">Delete</span>
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* System Prompt */}
              {client?.client && <SystemPromptPanel client={client.client} copyToClipboard={copyToClipboard} />}
            </div>

            {/* Tools and Resources - Side by side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
              {/* Tools */}
              <Card>
            <CardHeader className="space-y-4">
              <div>
                <CardTitle className="flex items-center text-lg sm:text-xl">
                  <Pickaxe className="mr-2 h-4 sm:h-5 w-4 sm:w-5" />
                  Tools
                </CardTitle>
                <CardDescription className="text-sm">Configure available tools for this client</CardDescription>
              </div>
              {/* Add tool dropdown - only show if there are available tools to add */}
              {client?.tools?.filter(t => !t.is_configured).length > 0 && (
                <div className="flex gap-2">
                  <Select
                    value={selectedToolToAdd?.name || ''}
                    onValueChange={(toolName) => {
                      const tool = client.tools.find(t => t.name === toolName)
                      setSelectedToolToAdd(tool)
                    }}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue placeholder="Select a tool to add..." />
                    </SelectTrigger>
                    <SelectContent>
                      {client?.tools
                        ?.filter(tool => !tool.is_configured)
                        .map(tool => (
                          <SelectItem key={tool.name} value={tool.name}>
                            <div className="flex items-center gap-2">
                              <span>{tool.name}</span>
                              <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                                tool.name.includes('core/') 
                                  ? 'bg-purple-100 text-blue-700' 
                                  : 'bg-blue-100 text-purple-700'
                              }`}>
                                {tool.name.includes('core/') ? 'CORE' : 'CUSTOM'}
                              </span>
                              {tool.requires_config && (
                                <span className="text-xs text-blue-600">Config required</span>
                              )}
                            </div>
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={() => {
                      if (selectedToolToAdd) {
                        if (selectedToolToAdd.requires_config) {
                          handleToolConfigure(selectedToolToAdd)
                        } else {
                          handleToolAdd(selectedToolToAdd)
                        }
                        setSelectedToolToAdd(null)
                      }
                    }}
                    disabled={!selectedToolToAdd || addToolMutation.isPending}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Only show enabled tools */}
                {client?.tools?.filter(tool => tool.is_configured).length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No tools enabled yet. Use the dropdown above to add tools.
                  </p>
                ) : (
                  client?.tools?.filter(tool => tool.is_configured).map((tool) => (
                  <div key={tool.name} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 border rounded-lg">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-sm sm:text-base">{tool.name}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                          tool.name.includes('core/') 
                            ? 'bg-blue-100 text-purple-700' 
                            : 'bg-purple-100 text-blue-700'
                        }`}>
                          {tool.name.includes('core/') ? 'CORE' : 'CUSTOM'}
                        </span>
                      </div>
                      {tool.description && (
                        <p className="text-xs text-muted-foreground mt-1">{tool.description}</p>
                      )}
                      {tool.requires_config && (
                        <p className="text-xs text-blue-600 mt-1">Requires configuration</p>
                      )}
                    </div>
                    <div className="flex items-center justify-between sm:justify-end gap-2 sm:space-x-2">
                      <div className="flex gap-2">
                        {tool.requires_config && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToolConfigure(tool)}
                            className="flex-shrink-0"
                          >
                            Configure
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleToolRemove(tool)}
                          className="flex-shrink-0 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4 mr-1 sm:mr-0" />
                          <span className="sm:hidden">Remove</span>
                        </Button>
                      </div>
                    </div>
                  </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Resources */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-lg sm:text-xl">
                <BookOpenText className="mr-2 h-4 sm:h-5 w-4 sm:w-5" />
                Resources
              </CardTitle>
              <CardDescription className="text-sm">Configure available resources for this client</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {client?.resources?.map((resource) => (
                  <div key={resource.name} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 border rounded-lg">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium text-sm sm:text-base">{resource.name}</h3>
                      {resource.requires_config && (
                        <p className="text-xs text-muted-foreground">Requires configuration</p>
                      )}
                    </div>
                    <div className="flex items-center justify-between sm:justify-end gap-2 sm:space-x-2">
                      <div className={`px-2 py-1 text-xs rounded-full ${
                        resource.is_configured 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {resource.is_configured ? 'Enabled' : 'Disabled'}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResourceConfigure(resource)}
                        className="flex-shrink-0"
                      >
                        Configure
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <ToolCallsStats 
              clientId={clientId} 
              title={`Tool Statistics for ${client?.client?.name}`}
            />
          </TabsContent>

          <TabsContent value="logs" className="space-y-6">
            <ToolCallsTable 
              clientId={clientId} 
              title={`Tool Call History for ${client?.client?.name}`}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Tool Configuration Dialog */}
      <ToolConfigurationDialog
        tool={selectedTool}
        clientId={clientId}
        isOpen={showToolDialog}
        onOpenChange={(open) => {
          setShowToolDialog(open)
          // Clear the selected tool to add when dialog closes
          if (!open) {
            setSelectedToolToAdd(null)
          }
        }}
      />

      {/* Resource Configuration Dialog */}
      <ResourceConfigurationDialog
        resource={selectedResource}
        clientId={clientId}
        isOpen={showResourceDialog}
        onOpenChange={setShowResourceDialog}
      />

      {/* Create API Key Dialog */}
      <Dialog open={showKeyDialog} onOpenChange={setShowKeyDialog}>
        <DialogContent className="w-[95vw] max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
            <DialogDescription>
              Add a new API key for this client.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateKey} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="create-key-name">Key name</Label>
              <Input
                id="create-key-name"
                placeholder="Enter key name"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                required
              />
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowKeyDialog(false)}
                className="w-full sm:w-auto"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createKeyMutation.isPending}
                className="w-full sm:w-auto"
              >
                {createKeyMutation.isPending ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* API Key Remove Confirmation Dialog */}
      <AlertDialog open={showKeyRemoveDialog} onOpenChange={setShowKeyRemoveDialog}>
        <AlertDialogContent className="w-[95vw] max-w-[425px]">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API Key</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the API key "{selectedKey?.name}"? 
              This action cannot be undone and any applications using this key will lose access.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col sm:flex-row gap-2">
            <AlertDialogCancel 
              onClick={() => setShowKeyRemoveDialog(false)}
              className="w-full sm:w-auto"
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (selectedKey) {
                  deleteKeyMutation.mutate(selectedKey.key_value)
                }
              }}
              disabled={deleteKeyMutation.isPending}
              className="w-full sm:w-auto bg-destructive hover:bg-destructive/90"
            >
              {deleteKeyMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Tool Remove Confirmation Dialog */}
      <AlertDialog open={showToolRemoveDialog} onOpenChange={setShowToolRemoveDialog}>
        <AlertDialogContent className="w-[95vw] max-w-[425px]">
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Tool</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove "{selectedTool?.name}" from this client? 
              This will disable the tool and remove any configuration.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col sm:flex-row gap-2">
            <AlertDialogCancel 
              onClick={() => setShowToolRemoveDialog(false)}
              className="w-full sm:w-auto"
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (selectedTool) {
                  removeToolMutation.mutate(selectedTool.name)
                }
              }}
              disabled={removeToolMutation.isPending}
              className="w-full sm:w-auto bg-destructive hover:bg-destructive/90"
            >
              {removeToolMutation.isPending ? 'Removing...' : 'Remove'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}