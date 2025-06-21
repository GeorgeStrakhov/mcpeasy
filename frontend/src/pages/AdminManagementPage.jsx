import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Trash2, UserPlus, Key, Shield } from 'lucide-react'
import { admins } from '../services/api'

export default function AdminManagementPage() {
  const queryClient = useQueryClient()
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isPasswordDialogOpen, setIsPasswordDialogOpen] = useState(false)
  const [selectedAdmin, setSelectedAdmin] = useState(null)
  
  // Form states
  const [newAdmin, setNewAdmin] = useState({
    username: '',
    email: '',
    password: ''
  })
  const [newPassword, setNewPassword] = useState('')

  // Fetch admins
  const { data: adminData, isLoading } = useQuery({
    queryKey: ['admins'],
    queryFn: admins.list,
  })

  // Create admin mutation
  const createAdminMutation = useMutation({
    mutationFn: admins.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['admins'])
      setIsCreateDialogOpen(false)
      setNewAdmin({ username: '', email: '', password: '' })
    },
  })

  // Delete admin mutation
  const deleteAdminMutation = useMutation({
    mutationFn: admins.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['admins'])
    },
  })

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: ({ username, newPassword }) => admins.changePassword(username, newPassword),
    onSuccess: () => {
      queryClient.invalidateQueries(['admins'])
      setIsPasswordDialogOpen(false)
      setNewPassword('')
      setSelectedAdmin(null)
    },
  })

  const handleCreateAdmin = (e) => {
    e.preventDefault()
    createAdminMutation.mutate(newAdmin)
  }

  const handleDeleteAdmin = (username) => {
    deleteAdminMutation.mutate(username)
  }

  const handleChangePassword = (e) => {
    e.preventDefault()
    if (selectedAdmin) {
      changePasswordMutation.mutate({
        username: selectedAdmin.username,
        newPassword
      })
    }
  }

  const openPasswordDialog = (admin) => {
    setSelectedAdmin(admin)
    setIsPasswordDialogOpen(true)
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading...</div>
      </div>
    )
  }

  const adminsData = adminData?.admins || []
  const currentAdmin = adminData?.current_admin

  return (
    <div className="container mx-auto px-4 py-4 sm:py-8">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">Admin Management</h1>
          <p className="text-muted-foreground text-sm sm:text-base">Manage admin users and permissions</p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full sm:w-auto">
              <UserPlus className="w-4 h-4 mr-2" />
              Add Admin
            </Button>
          </DialogTrigger>
          <DialogContent className="w-[95vw] max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create New Admin</DialogTitle>
              <DialogDescription>
                Add a new administrator to the system
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateAdmin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={newAdmin.username}
                  onChange={(e) => setNewAdmin(prev => ({ ...prev, username: e.target.value }))}
                  placeholder="Enter username"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={newAdmin.email}
                  onChange={(e) => setNewAdmin(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="Enter email address"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={newAdmin.password}
                  onChange={(e) => setNewAdmin(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="Enter password"
                  required
                />
              </div>

              {createAdminMutation.error && (
                <div className="text-destructive text-sm">
                  {createAdminMutation.error.message}
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-2 sm:justify-end">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setIsCreateDialogOpen(false)}
                  className="w-full sm:w-auto"
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={createAdminMutation.isPending}
                  className="w-full sm:w-auto"
                >
                  {createAdminMutation.isPending ? 'Creating...' : 'Create Admin'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Change Password Dialog */}
      <Dialog open={isPasswordDialogOpen} onOpenChange={setIsPasswordDialogOpen}>
        <DialogContent className="w-[95vw] max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Change password for {selectedAdmin?.username}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                required
              />
            </div>

            {changePasswordMutation.error && (
              <div className="text-destructive text-sm">
                {changePasswordMutation.error.message}
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-2 sm:justify-end">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => setIsPasswordDialogOpen(false)}
                className="w-full sm:w-auto"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={changePasswordMutation.isPending}
                className="w-full sm:w-auto"
              >
                {changePasswordMutation.isPending ? 'Changing...' : 'Change Password'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Admins List */}
      <div className="grid gap-4">
        {adminsData.map((admin) => (
          <Card key={admin.id}>
            <CardContent className="p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-start sm:items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {admin.is_superadmin && (
                      <Shield className="w-5 h-5 text-blue-600" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3 className="font-semibold text-sm sm:text-base truncate">
                        {admin.username}
                      </h3>
                      {admin.username === currentAdmin && (
                        <Badge variant="secondary" className="text-xs">You</Badge>
                      )}
                      {admin.is_superadmin && (
                        <Badge variant="default" className="text-xs">Superadmin</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{admin.email}</p>
                    <p className="text-xs text-muted-foreground">
                      Created {new Date(admin.created_at).toLocaleDateString()}
                      {admin.created_by_username && (
                        <span className="hidden sm:inline"> by {admin.created_by_username}</span>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:space-x-2">
                  {/* Change Password - only for current user */}
                  {admin.username === currentAdmin && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openPasswordDialog(admin)}
                      className="w-full sm:w-auto"
                    >
                      <Key className="w-4 h-4 mr-2" />
                      <span className="hidden sm:inline">Change Password</span>
                      <span className="sm:hidden">Password</span>
                    </Button>
                  )}

                  {/* Delete Admin - not for superadmin or current user */}
                  {!admin.is_superadmin && admin.username !== currentAdmin && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="outline" size="sm" className="w-full sm:w-auto">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete Admin</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to delete admin "{admin.username}"? This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => handleDeleteAdmin(admin.username)}
                            className="bg-destructive hover:bg-destructive/90"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {adminsData.length === 0 && (
          <Card>
            <CardContent className="p-6 text-center">
              <p className="text-muted-foreground">No administrators found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
} 