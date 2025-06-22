import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { resources } from '@/services/api'
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

  const handleFieldChange = (fieldName, fieldValue) => {
    const newData = { ...formData, [fieldName]: fieldValue }
    setFormData(newData)
    onChange(newData)
  }

  const renderField = (fieldName, fieldSchema) => {
    const fieldType = fieldSchema.type
    const currentValue = formData[fieldName] !== undefined ? formData[fieldName] : fieldSchema.default

    switch (fieldType) {
      case 'string':
        if (fieldSchema.enum) {
          return (
            <Select value={currentValue || ''} onValueChange={(value) => handleFieldChange(fieldName, value)}>
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
        
        if (fieldSchema.format === 'email') {
          return (
            <Input
              type="email"
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(fieldName, e.target.value)}
              placeholder={fieldSchema.description}
            />
          )
        }

        if (fieldSchema.description && fieldSchema.description.length > 50) {
          return (
            <Textarea
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(fieldName, e.target.value)}
              placeholder={fieldSchema.description}
              rows={3}
            />
          )
        }

        return (
          <Input
            value={currentValue || ''}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            placeholder={fieldSchema.description}
          />
        )

      case 'number':
      case 'integer':
        return (
          <Input
            type="number"
            value={currentValue || ''}
            onChange={(e) => handleFieldChange(fieldName, Number(e.target.value))}
            placeholder={fieldSchema.description}
          />
        )

      case 'boolean':
        return (
          <Switch
            checked={!!currentValue}
            onCheckedChange={(checked) => handleFieldChange(fieldName, checked)}
          />
        )

      case 'array':
        // Simple array handling - comma-separated strings
        return (
          <div className="space-y-2">
            <Input
              value={Array.isArray(currentValue) ? currentValue.join(', ') : ''}
              onChange={(e) => {
                const arrayValue = e.target.value.split(',').map(item => item.trim()).filter(Boolean)
                handleFieldChange(fieldName, arrayValue)
              }}
              placeholder={`${fieldSchema.description} (comma-separated)`}
            />
            <p className="text-xs text-muted-foreground">
              Enter multiple values separated by commas
            </p>
          </div>
        )

      default:
        return (
          <Textarea
            value={typeof currentValue === 'object' ? JSON.stringify(currentValue, null, 2) : currentValue || ''}
            onChange={(e) => {
              try {
                const jsonValue = JSON.parse(e.target.value)
                handleFieldChange(fieldName, jsonValue)
              } catch {
                handleFieldChange(fieldName, e.target.value)
              }
            }}
            placeholder={fieldSchema.description}
            rows={4}
          />
        )
    }
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

export default function ResourceConfigurationDialog({ 
  resource, 
  clientId, 
  isOpen, 
  onOpenChange 
}) {
  const [configuration, setConfiguration] = useState(resource?.configuration || {})
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const configureResourceMutation = useMutation({
    mutationFn: ({ resourceName, config }) => resources.configure(clientId, resourceName, config),
    onSuccess: () => {
      queryClient.invalidateQueries(['client', clientId])
      toast({
        title: "Resource configured",
        description: `Successfully configured ${resource.name}.`,
      })
      onOpenChange(false)
    },
    onError: (error) => {
      toast({
        title: "Error configuring resource",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const removeResourceMutation = useMutation({
    mutationFn: (resourceName) => resources.delete(clientId, resourceName),
    onSuccess: () => {
      queryClient.invalidateQueries(['client', clientId])
      toast({
        title: "Resource removed",
        description: `Successfully removed ${resource.name}.`,
      })
      onOpenChange(false)
    },
    onError: (error) => {
      toast({
        title: "Error removing resource",
        description: error.message,
        variant: "destructive",
      })
    },
  })

  const handleSave = () => {
    configureResourceMutation.mutate({
      resourceName: resource.name,
      config: Object.keys(configuration).length > 0 ? configuration : null
    })
  }

  const handleRemove = () => {
    removeResourceMutation.mutate(resource.name)
  }

  if (!resource) return null

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure {resource.name}</DialogTitle>
          <DialogDescription>
            {resource.requires_config 
              ? `Configure the settings for the ${resource.name} resource.`
              : `Enable or disable the ${resource.name} resource.`
            }
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {resource.requires_config ? (
            <JsonSchemaForm
              schema={resource.config_schema}
              value={configuration}
              onChange={setConfiguration}
            />
          ) : (
            <p className="text-muted-foreground">
              This resource does not require any configuration. You can simply enable or disable it.
            </p>
          )}
        </div>

        <DialogFooter className="flex justify-between">
          <div className="space-x-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={configureResourceMutation.isPending}
            >
              {configureResourceMutation.isPending ? 'Saving...' : 'Save Configuration'}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}