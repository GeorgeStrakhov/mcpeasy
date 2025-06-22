import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { useAuth } from '../hooks/useAuth'
import { LogOut, BarChart3, Users, Settings, Menu, Activity } from 'lucide-react'

export default function Header() {
  const location = useLocation()
  const { logout } = useAuth()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const isActive = (path) => {
    return location.pathname === path
  }

  const handleLogout = () => {
    logout()
  }

  const handleLinkClick = () => {
    setIsMenuOpen(false)
  }

  const navItems = [
    { path: '/', icon: Users, label: 'Dashboard' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/monitoring', icon: Activity, label: 'Monitoring' },
    { path: '/admins', icon: Settings, label: 'Admin Management' },
  ]

  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo/Title */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <div className="font-bold text-xl">MCPeasy</div>
              <Badge variant="secondary" className="hidden sm:inline-flex">Admin</Badge>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link key={path} to={path}>
                <Button 
                  variant={isActive(path) ? 'default' : 'ghost'} 
                  size="sm"
                  className="flex items-center space-x-2"
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </Button>
              </Link>
            ))}

            {/* Desktop Logout */}
            <div className="ml-4 pl-4 border-l">
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleLogout}
                className="flex items-center space-x-2"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </Button>
            </div>
          </nav>

          {/* Mobile Navigation */}
          <div className="md:hidden">
            {/* Mobile Menu */}
            <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="sm">
                  <Menu className="w-4 h-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[300px] sm:w-[400px]">
                <SheetHeader>
                  <SheetTitle>MCPeasy Admin</SheetTitle>
                  <SheetDescription>
                    Navigate through the admin dashboard and manage your settings.
                  </SheetDescription>
                </SheetHeader>
                <nav className="flex flex-col space-y-2 mt-6">
                  {navItems.map(({ path, icon: Icon, label }) => (
                    <Link key={path} to={path} onClick={handleLinkClick}>
                      <Button 
                        variant={isActive(path) ? 'default' : 'ghost'} 
                        className="w-full justify-start space-x-2"
                      >
                        <Icon className="w-4 h-4" />
                        <span>{label}</span>
                      </Button>
                    </Link>
                  ))}
                  
                  <div className="pt-4 border-t">
                    <Button 
                      variant="outline" 
                      onClick={handleLogout}
                      className="w-full justify-start space-x-2"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </Button>
                  </div>
                </nav>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  )
} 