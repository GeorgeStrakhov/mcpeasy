import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toolCalls } from '../services/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { BarChart3, TrendingUp, Clock, AlertCircle, CheckCircle } from 'lucide-react'

export default function ToolCallsStats({ clientId = null, title = "Tool Call Statistics" }) {
  const [days, setDays] = useState(30)

  const { data, isLoading, error } = useQuery({
    queryKey: ['tool-calls-stats', { clientId, days }],
    queryFn: () => {
      if (clientId) {
        return toolCalls.statsForClient(clientId, { days })
      }
      return toolCalls.stats({ client_id: clientId, days })
    },
  })

  const formatDuration = (ms) => {
    if (ms === null || ms === undefined) return 'N/A'
    if (ms === 0) return '<1ms'
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span>Error loading statistics: {error.message}</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center space-x-4">
        <Label htmlFor="period">Time Period</Label>
        <Select value={days.toString()} onValueChange={(value) => setDays(parseInt(value))}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Loading State */}
      {isLoading && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistics Cards */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Calls */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.total_calls.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                Last {days} days
              </p>
            </CardContent>
          </Card>

          {/* Success Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.success_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {data.successful_calls} successful, {data.failed_calls} failed
              </p>
            </CardContent>
          </Card>

          {/* Average Duration */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatDuration(data.avg_execution_time_ms)}
              </div>
              <p className="text-xs text-muted-foreground">
                Average execution time
              </p>
            </CardContent>
          </Card>

          {/* Status Breakdown */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Badge variant="default" className="bg-green-100 text-green-800">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Success
                  </Badge>
                  <span className="text-sm">{data.successful_calls}</span>
                </div>
                <div className="flex items-center justify-between">
                  <Badge variant="destructive">
                    <AlertCircle className="mr-1 h-3 w-3" />
                    Failed
                  </Badge>
                  <span className="text-sm">{data.failed_calls}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top Tools */}
      {data && data.top_tools.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="mr-2 h-5 w-5" />
              Most Used Tools
            </CardTitle>
            <CardDescription>
              Top tools by usage in the last {days} days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.top_tools.map((tool, index) => (
                <div key={tool.tool_name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-muted-foreground">
                      #{index + 1}
                    </span>
                    <Badge variant="outline">{tool.tool_name}</Badge>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">{tool.count}</span>
                    <div className="w-20 bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{
                          width: `${(tool.count / data.top_tools[0].count) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {data && data.total_calls === 0 && (
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-muted-foreground">
              No tool calls found in the last {days} days.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}