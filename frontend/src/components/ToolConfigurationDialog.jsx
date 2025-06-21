import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { tools } from '@/services/api'
import { useToast } from '@/hooks/use-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

function JsonSchemaForm({ schema, value, onChange }) {
  const [formData, setFormData] = useState(value || {})

  // Ensure formData updates when value prop changes
  useEffect(() => {
    setFormData(value || {})
  }, [value])

  const handleFieldChange = (fieldName, fieldValue) => {
    const newData = { ...formData, [fieldName]: fieldValue }
    setFormData(newData)
    onChange(newData)
  }

  const renderField = (fieldName, fieldSchema) => {
    const currentValue = formData[fieldName] !== undefined ? formData[fieldName] : (fieldSchema.default !== undefined ? fieldSchema.default : '')

    // Handle boolean types with Switch component
    if (fieldSchema.type === 'boolean') {
      const boolValue = currentValue === true || currentValue === 'true'
      return (
        <div className="flex items-center space-x-2">
          <Switch
            checked={boolValue}
            onCheckedChange={(checked) => handleFieldChange(fieldName, checked)}
          />
          <Label htmlFor={fieldName} className="text-sm font-normal">
            {boolValue ? 'Enabled' : 'Disabled'}
          </Label>
        </div>
      )
    }

    if (fieldSchema.enum) {
      return (
        <Select value={currentValue} onValueChange={(value) => handleFieldChange(fieldName, value)}>
          <SelectTrigger>
            <SelectValue placeholder={`Select ${fieldName}`} />
          </SelectTrigger>
          <SelectContent>
            {fieldSchema.enum.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )
    }

    if (fieldSchema.description && fieldSchema.description.length > 50) {
      return (
        <Textarea
          value={currentValue ?? ''}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={fieldSchema.description}
          rows={3}
        />
      )
    }

    return (
      <Input
        value={currentValue ?? ''}
        onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        placeholder={fieldSchema.description}
      />
    )
  }

  if (!schema || !schema.properties) {
    return <p className="text-muted-foreground">No configuration options available.</p>
  }

  return (
    <div className="space-y-4">
      {Object.entries(schema.properties).map(([fieldName, fieldSchema]) => (
        <div key={fieldName} className="space-y-2">
          <Label htmlFor={fieldName} className="flex items-center space-x-2">
            <span>{fieldName}</span>
            {schema.required?.includes(fieldName) && (
              <span className="text-destructive">*</span>
            )}
          </Label>
          {fieldSchema.description && (
            <p className="text-sm text-muted-foreground">{fieldSchema.description}</p>
          )}
          {renderField(fieldName, fieldSchema)}
        </div>
      ))}
    </div>
  )
}

function mergeDefaultsWithConfig(schema, config) {
  const merged = {};
  if (!schema || !schema.properties) return merged;
  for (const [field, fieldSchema] of Object.entries(schema.properties)) {
    if (config && config[field] !== undefined) {
      merged[field] = config[field];
    } else if (fieldSchema.default !== undefined) {
      merged[field] = fieldSchema.default;
    } else {
      // Set appropriate default based on field type
      if (fieldSchema.type === 'boolean') {
        merged[field] = false;
      } else if (fieldSchema.type === 'number' || fieldSchema.type === 'integer') {
        merged[field] = '';
      } else {
        merged[field] = '';
      }
    }
  }
  return merged;
}

export default function ToolConfigurationDialog({ 
  tool, 
  clientId, 
  isOpen, 
  onOpenChange 
}) {
  const [configuration, setConfiguration] = useState(() => mergeDefaultsWithConfig(tool?.config_schema, tool?.configuration));
  const { toast } = useToast()
  const queryClient = useQueryClient()

  // Reset configuration when tool changes or dialog opens
  useEffect(() => {
    setConfiguration(mergeDefaultsWithConfig(tool?.config_schema, tool?.configuration));
  }, [tool, isOpen]);

  const configureToolMutation = useMutation({
    mutationFn: ({ toolName, config }) => tools.configure(clientId, toolName, config),
    onSuccess: () => {
      queryClient.invalidateQueries(['client', clientId])
      toast({
        title: "Tool configured",
        description: `Successfully configured ${tool.name}.`,
      })
      onOpenChange(false)
    },
    onError: (error) => {
      toast({
        title: "Error configuring tool",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const handleSave = () => {
    console.log('Saving config:', configuration)
    configureToolMutation.mutate({
      toolName: tool.name,
      config: Object.keys(configuration).length > 0 ? configuration : null
    })
  }

  if (!tool) return null

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure {tool.name}</DialogTitle>
          <DialogDescription>
            {tool.requires_config 
              ? `Configure the settings for the ${tool.name} tool.`
              : `Enable or disable the ${tool.name} tool.`
            }
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {tool.requires_config ? (
            <JsonSchemaForm
              schema={tool.config_schema}
              value={configuration}
              onChange={setConfiguration}
            />
          ) : (
            <p className="text-muted-foreground">
              This tool does not require any configuration. You can simply enable or disable it.
            </p>
          )}
        </div>

        <DialogFooter className="flex justify-end space-x-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={configureToolMutation.isPending}
          >
            {configureToolMutation.isPending ? 'Saving...' : 'Save Configuration'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}