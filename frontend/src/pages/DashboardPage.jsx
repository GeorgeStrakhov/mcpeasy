import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dashboard, clients } from '../services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/hooks/use-toast'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Users, Key, Settings, Plus, Edit, Trash2, Search } from 'lucide-react'

export default function DashboardPage() {
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedClient, setSelectedClient] = useState(null)
  const [clientName, setClientName] = useState('')
  const [clientDescription, setClientDescription] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboard.get,
  })

  const createClientMutation = useMutation({
    mutationFn: clients.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries(['dashboard'])
      handleCloseCreateDialog()
      toast({
        title: "Client created",
        description: `Successfully created client "${data.name}".`,
      })
    },
    onError: (error) => {
      toast({
        title: "Error creating client",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const updateClientMutation = useMutation({
    mutationFn: ({ clientId, data }) => clients.update(clientId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries(['dashboard'])
      handleCloseEditDialog()
      toast({
        title: "Client updated",
        description: `Successfully updated client "${data.name}".`,
      })
    },
    onError: (error) => {
      toast({
        title: "Error updating client",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const deleteClientMutation = useMutation({
    mutationFn: clients.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['dashboard'])
      handleCloseDeleteDialog()
      toast({
        title: "Client deleted",
        description: "Client has been successfully deleted.",
      })
    },
    onError: (error) => {
      toast({
        title: "Error deleting client",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const handleOpenCreateDialog = () => {
    setClientName('')
    setClientDescription('')
    setShowCreateDialog(true)
  }

  const handleCloseCreateDialog = () => {
    setShowCreateDialog(false)
    setClientName('')
    setClientDescription('')
  }

  const handleOpenEditDialog = (client) => {
    setSelectedClient(client)
    setClientName(client.name)
    setClientDescription(client.description || '')
    setShowEditDialog(true)
  }

  const handleCloseEditDialog = () => {
    setShowEditDialog(false)
    setSelectedClient(null)
    setClientName('')
    setClientDescription('')
  }

  const handleOpenDeleteDialog = (client) => {
    setSelectedClient(client)
    setShowDeleteDialog(true)
  }

  const handleCloseDeleteDialog = () => {
    setShowDeleteDialog(false)
    setSelectedClient(null)
  }

  const handleCreateClient = (e) => {
    e.preventDefault()
    createClientMutation.mutate({
      name: clientName,
      description: clientDescription || undefined,
    })
  }

  const handleUpdateClient = (e) => {
    e.preventDefault()
    updateClientMutation.mutate({
      clientId: selectedClient.id,
      data: {
        name: clientName,
        description: clientDescription || undefined,
      },
    })
  }

  const handleDeleteClient = () => {
    deleteClientMutation.mutate(selectedClient.id)
  }

  const handleClientClick = (clientId) => {
    window.location.href = `/clients/${clientId}`
  }

  // Filter clients based on search term
  const filteredClients = dashboardData?.clients?.filter(client => {
    if (!searchTerm) return true
    const searchLower = searchTerm.toLowerCase()
    return (
      client.name.toLowerCase().includes(searchLower) ||
      (client.description && client.description.toLowerCase().includes(searchLower))
    )
  }) || []

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-4 sm:py-8">
      {/* Page Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground text-sm sm:text-base">Overview of your MCP server management</p>
      </div>

      {/* Stats */}
      <div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Clients</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData?.clients?.length || 0}</div>
              <p className="text-xs text-muted-foreground">Active clients</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total API Keys</CardTitle>
              <Key className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData?.total_api_keys || 0}</div>
              <p className="text-xs text-muted-foreground">Across all clients</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Available Tools</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData?.available_tools || 0}</div>
              <p className="text-xs text-muted-foreground">Tools ready for use</p>
            </CardContent>
          </Card>
        </div>

        {/* Clients */}
        <Card>
          <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-lg sm:text-xl">Clients</CardTitle>
              <CardDescription className="text-sm">Manage your MCP clients and their configurations</CardDescription>
            </div>
            <Button onClick={handleOpenCreateDialog} className="w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" />
              Add Client
            </Button>
          </CardHeader>

          <CardContent>
            {/* Search bar */}
            <div className="mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search clients by name or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Client list */}
            <div className="space-y-4">
              {filteredClients.map((client) => (
                <div key={client.id} className="group relative">
                  <div 
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                    onClick={() => handleClientClick(client.id)}
                  >
                    <div className="flex items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
                      <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-primary font-medium text-sm">
                          {client.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-medium text-sm sm:text-base truncate group-hover:text-primary transition-colors">{client.name}</h3>
                        {client.description && (
                          <p className="text-xs sm:text-sm text-muted-foreground truncate">{client.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center justify-between sm:justify-end sm:space-x-6">
                      <div className="flex items-center space-x-4 sm:space-x-6 text-xs sm:text-sm text-muted-foreground">
                        <span>{client.api_key_count} keys</span>
                        <span>{client.tool_count} tools</span>
                      </div>
                      <div className="flex-shrink-0">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="h-8 w-8 p-0"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Settings className="h-4 w-4" />
                              <span className="sr-only">Client settings</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem 
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                handleOpenEditDialog(client)
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                handleOpenDeleteDialog(client)
                              }}
                              className="text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {filteredClients.length === 0 && dashboardData?.clients?.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">No clients found</p>
                  <p className="text-xs">Click "Add Client" to get started</p>
                </div>
              )}

              {filteredClients.length === 0 && dashboardData?.clients?.length > 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">No clients match your search</p>
                  <p className="text-xs">Try adjusting your search terms</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Create Client Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="w-[95vw] max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create Client</DialogTitle>
            <DialogDescription>
              Add a new client to manage their API keys and tool configurations.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateClient} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="create-client-name">Client name</Label>
              <Input
                id="create-client-name"
                placeholder="Enter client name"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-client-description">Description (optional)</Label>
              <Input
                id="create-client-description"
                placeholder="Enter description"
                value={clientDescription}
                onChange={(e) => setClientDescription(e.target.value)}
              />
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCloseCreateDialog}
                className="w-full sm:w-auto"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createClientMutation.isPending}
                className="w-full sm:w-auto"
              >
                {createClientMutation.isPending ? 'Creating...' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Client Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="w-[95vw] max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Edit Client</DialogTitle>
            <DialogDescription>
              Update the client information.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateClient} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-client-name">Client name</Label>
              <Input
                id="edit-client-name"
                placeholder="Enter client name"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-client-description">Description (optional)</Label>
              <Input
                id="edit-client-description"
                placeholder="Enter description"
                value={clientDescription}
                onChange={(e) => setClientDescription(e.target.value)}
              />
            </div>
            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCloseEditDialog}
                className="w-full sm:w-auto"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateClientMutation.isPending}
                className="w-full sm:w-auto"
              >
                {updateClientMutation.isPending ? 'Updating...' : 'Update'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Client Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="w-[95vw] max-w-[425px]">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Client</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{selectedClient?.name}"? This action cannot be undone.
              All API keys, tool configurations, and related data will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-col sm:flex-row gap-2">
            <AlertDialogCancel 
              onClick={handleCloseDeleteDialog}
              className="w-full sm:w-auto"
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteClient}
              disabled={deleteClientMutation.isPending}
              className="w-full sm:w-auto bg-destructive hover:bg-destructive/90"
            >
              {deleteClientMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}