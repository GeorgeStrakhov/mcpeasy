import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Copy, Clock, AlertCircle, CheckCircle, Calendar, User, Settings } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'

export default function ToolCallDetailDialog({ toolCall, isOpen, onOpenChange }) {
  const { toast } = useToast()

  if (!toolCall) return null

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString()
  }

  const formatDuration = (ms) => {
    if (ms === null || ms === undefined) return 'N/A'
    if (ms === 0) return '<1ms'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
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

  const formatJsonData = (data) => {
    if (!data) return 'null'
    return JSON.stringify(data, null, 2)
  }

  const renderJsonData = (data, title) => {
    if (!data) {
      return (
        <div className="text-muted-foreground text-center py-4">
          No {title.toLowerCase()} data
        </div>
      )
    }

    const jsonString = formatJsonData(data)

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium">{title}</h4>
          <Button
            variant="outline"
            size="sm"
            onClick={() => copyToClipboard(jsonString, `${title} copied to clipboard`)}
          >
            <Copy className="h-3 w-3 mr-1" />
            Copy
          </Button>
        </div>
        <div className="relative">
          <ScrollArea className="h-48 w-full rounded-md border">
            <pre className="text-xs p-4 font-mono whitespace-pre-wrap break-words">
              {jsonString}
            </pre>
          </ScrollArea>
        </div>
      </div>
    )
  }

  const renderOutputData = () => {
    if (toolCall.error_message) {
      return (
        <div className="text-muted-foreground text-center py-4">
          No output data due to error
        </div>
      )
    }

    // Handle JSON output (structured data)
    if (toolCall.output_json) {
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium flex items-center">
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-2">JSON</span>
              Structured Output Data
            </h4>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(formatJsonData(toolCall.output_json), "JSON output copied to clipboard")}
            >
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
          </div>
          <div className="relative">
            <ScrollArea className="h-48 w-full rounded-md border">
              <pre className="text-xs p-4 font-mono whitespace-pre-wrap break-words">
                {formatJsonData(toolCall.output_json)}
              </pre>
            </ScrollArea>
          </div>
        </div>
      )
    }

    // Handle text output (extract text from content array)
    if (toolCall.output_text) {
      // Extract text content from the content array
      let textContent = ""
      if (Array.isArray(toolCall.output_text)) {
        // Find text content in the array
        const textItem = toolCall.output_text.find(item => item.type === "text")
        textContent = textItem ? textItem.text : formatJsonData(toolCall.output_text)
      } else {
        textContent = formatJsonData(toolCall.output_text)
      }

      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium flex items-center">
              <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs mr-2">TEXT</span>
              Text Output Data
            </h4>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(textContent, "Text output copied to clipboard")}
            >
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
          </div>
          <div className="relative">
            <ScrollArea className="h-48 w-full rounded-md border">
              <pre className="text-xs p-4 font-mono whitespace-pre-wrap break-words">
                {textContent}
              </pre>
            </ScrollArea>
          </div>
        </div>
      )
    }

    return (
      <div className="text-muted-foreground text-center py-4">
        No output data
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Tool Call Details</span>
          </DialogTitle>
          <DialogDescription>
            Detailed information about tool execution #{toolCall.id}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto pr-2">
          <div className="space-y-6 pb-6">
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Status Card */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Status</CardTitle>
              </CardHeader>
              <CardContent>
                {toolCall.error_message ? (
                  <Badge variant="destructive" className="flex items-center w-fit">
                    <AlertCircle className="mr-1 h-3 w-3" />
                    Failed
                  </Badge>
                ) : (
                  <Badge variant="default" className="flex items-center w-fit bg-green-100 text-green-800">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Success
                  </Badge>
                )}
              </CardContent>
            </Card>

            {/* Execution Time Card */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <Clock className="mr-1 h-4 w-4" />
                  Duration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-semibold">
                  {formatDuration(toolCall.execution_time_ms)}
                </div>
              </CardContent>
            </Card>

            {/* Timestamp Card */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center">
                  <Calendar className="mr-1 h-4 w-4" />
                  Executed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  {formatDate(toolCall.created_at)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tool Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tool Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Tool Name</label>
                  <div className="mt-1">
                    <Badge variant="outline" className="text-sm">
                      {toolCall.tool_name}
                    </Badge>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Client ID</label>
                  <div className="mt-1 font-mono text-sm">
                    {toolCall.client_id}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Tabs */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Execution Data</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="input" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="input">Input Data</TabsTrigger>
                  <TabsTrigger value="output" disabled={!toolCall.output_json && !toolCall.output_text}>
                    Output Data
                  </TabsTrigger>
                  <TabsTrigger value="error" disabled={!toolCall.error_message}>
                    Error Details
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="input" className="mt-4">
                  {renderJsonData(toolCall.input_data, "Input Data")}
                </TabsContent>

                <TabsContent value="output" className="mt-4">
                  {renderOutputData()}
                </TabsContent>

                <TabsContent value="error" className="mt-4">
                  {toolCall.error_message ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium">Error Message</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(toolCall.error_message, "Error message copied to clipboard")}
                        >
                          <Copy className="h-3 w-3 mr-1" />
                          Copy
                        </Button>
                      </div>
                      <Card className="border-destructive/20 bg-destructive/5">
                        <CardContent className="p-4">
                          <ScrollArea className="h-24 w-full">
                            <pre className="text-sm text-destructive whitespace-pre-wrap break-words">
                              {toolCall.error_message}
                            </pre>
                          </ScrollArea>
                        </CardContent>
                      </Card>
                    </div>
                  ) : (
                    <div className="text-muted-foreground text-center py-4">
                      No error information
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}