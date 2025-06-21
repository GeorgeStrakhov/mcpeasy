import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart3 } from 'lucide-react'
import ToolCallsStats from '@/components/ToolCallsStats'
import ToolCallsTable from '@/components/ToolCallsTable'

export default function AnalyticsPage() {

  return (
    <div className="container mx-auto px-4 py-4 sm:py-8">
      {/* Page Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2 flex items-center">
          <BarChart3 className="mr-3 h-6 sm:h-8 w-6 sm:w-8" />
          Analytics
        </h1>
        <p className="text-muted-foreground text-sm sm:text-base">
          Monitor tool usage and performance across all clients
        </p>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="detailed">Detailed Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <ToolCallsStats title="Global Tool Call Statistics" />
        </TabsContent>

        <TabsContent value="detailed" className="space-y-6">
          <ToolCallsTable title="All Tool Calls" showClientColumn={true} />
        </TabsContent>
      </Tabs>
    </div>
  )
}