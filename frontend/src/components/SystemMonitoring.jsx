import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { monitoring } from '../services/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Activity, Database, Zap, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react'

const SystemMonitoring = () => {
  const [autoRefresh, setAutoRefresh] = useState(true)

  const { data: healthData, isLoading, refetch } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: monitoring.systemHealth,
    refetchInterval: autoRefresh ? 3000 : false, // Refresh every 3 seconds if enabled
    retry: 3,
  })

  // Status color helpers
  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-800 border-green-200'
      case 'disconnected': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getQueueStatusColor = (utilization) => {
    if (utilization < 50) return 'bg-green-100 text-green-800 border-green-200'
    if (utilization < 80) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  const getQueueStatus = (metrics) => {
    if (!metrics.is_started) return 'Stopped'
    if (metrics.utilization_percent < 50) return 'Healthy'
    if (metrics.utilization_percent < 80) return 'Busy'
    return 'Overloaded'
  }

  return (
    <div className="container mx-auto px-4 py-4 sm:py-8">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-2 flex items-center">
              <Activity className="mr-3 h-6 sm:h-8 w-6 sm:w-8" />
              System Monitoring
            </h1>
            <p className="text-muted-foreground text-sm sm:text-base">Real-time system health and queue metrics (since system restart)</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
            >
              <Activity className="mr-2 h-4 w-4" />
              <span className="hidden xs:inline">Auto Refresh</span>
              <span className="xs:hidden">Auto</span> {autoRefresh ? 'On' : 'Off'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden xs:inline">Refresh</span>
              <span className="xs:hidden">↻</span>
            </Button>
          </div>
        </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Database Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database Status</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              {healthData?.database_status === 'connected' ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-600" />
              )}
              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-md border ${getStatusColor(healthData?.database_status)}`}>
                {healthData?.database_status || 'Unknown'}
              </span>
            </div>
            {healthData?.timestamp && (
              <p className="text-xs text-muted-foreground mt-2">
                Last checked: {new Date(healthData.timestamp).toLocaleTimeString()}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Tool Queue Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tool Execution Queue</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2 mb-2">
              {healthData?.queue_metrics?.is_started ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-600" />
              )}
              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-md border ${getQueueStatusColor(healthData?.queue_metrics?.utilization_percent || 0)}`}>
                {getQueueStatus(healthData?.queue_metrics || {})}
              </span>
            </div>
            
            {healthData?.queue_metrics && (
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Queue Depth:</span>
                  <span className="font-medium">
                    {healthData.queue_metrics.queue_depth} / {healthData.queue_metrics.max_queue_size}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Active Workers:</span>
                  <span className="font-medium">
                    {healthData.queue_metrics.active_workers} / {healthData.queue_metrics.max_workers}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tasks Processed:</span>
                  <span className="font-medium">{healthData.queue_metrics.total_tasks_processed.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Utilization:</span>
                  <span className="font-medium">{healthData.queue_metrics.utilization_percent}%</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detailed Queue Metrics */}
      {healthData?.queue_metrics && (
        <Card>
          <CardHeader>
            <CardTitle>Queue Details</CardTitle>
            <CardDescription>
              Real-time metrics for the tool execution queue system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {healthData.queue_metrics.queue_depth}
                </div>
                <div className="text-sm text-muted-foreground">
                  Queued Requests
                </div>
              </div>
              
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {healthData.queue_metrics.active_workers}
                </div>
                <div className="text-sm text-muted-foreground">
                  Active Workers
                </div>
              </div>
              
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {healthData.queue_metrics.total_tasks_processed.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground">
                  Tasks Processed
                </div>
              </div>
              
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {healthData.queue_metrics.utilization_percent}%
                </div>
                <div className="text-sm text-muted-foreground">
                  Queue Utilization
                </div>
              </div>
            </div>

            {/* Peak Activity */}
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-700">
                  {healthData.queue_metrics.peak_queue_depth}
                </div>
                <div className="text-xs text-muted-foreground">
                  Peak Queue Depth
                </div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-700">
                  {healthData.queue_metrics.peak_active_workers}
                </div>
                <div className="text-xs text-muted-foreground">
                  Peak Active Workers
                </div>
              </div>
            </div>

            {/* Progress bar for queue utilization */}
            <div className="mt-4">
              <div className="flex justify-between text-sm text-muted-foreground mb-2">
                <span>Queue Utilization</span>
                <span>{healthData.queue_metrics.utilization_percent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    healthData.queue_metrics.utilization_percent < 50 
                      ? 'bg-green-500' 
                      : healthData.queue_metrics.utilization_percent < 80 
                        ? 'bg-yellow-500' 
                        : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(healthData.queue_metrics.utilization_percent, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
        )}

        {/* Loading/Error State */}
        {isLoading && !healthData && (
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Loading system health...
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

export default SystemMonitoring