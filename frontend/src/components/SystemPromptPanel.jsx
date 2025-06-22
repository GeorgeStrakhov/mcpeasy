import React, { useState, useEffect } from 'react'
import { systemPrompts } from '../services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
import { Plus, Copy, MessageSquare, Edit, Save, Hash } from 'lucide-react'

// Simple token estimation function (roughly 4 characters per token)
const estimateTokens = (text) => {
  if (!text) return 0
  return Math.ceil(text.length / 4)
}

const SystemPromptPanel = ({ client, copyToClipboard }) => {
  const [prompts, setPrompts] = useState([])
  const [currentPrompt, setCurrentPrompt] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [generateLoading, setGenerateLoading] = useState(false)
  const [userRequirements, setUserRequirements] = useState('')
  const [generatedPrompt, setGeneratedPrompt] = useState('')
  const [isRevision, setIsRevision] = useState(false)
  const [parentVersionId, setParentVersionId] = useState(null)
  const [isEditingMain, setIsEditingMain] = useState(false)
  const [editedMainPrompt, setEditedMainPrompt] = useState('')

  useEffect(() => {
    loadPrompts()
  }, [client.id])

  const loadPrompts = async () => {
    try {
      setLoading(true)
      const promptList = await systemPrompts.list(client.id)
      setPrompts(promptList)
      
      // Find current prompt (marked as active in backend for display purposes)
      const current = promptList.find(p => p.is_active)
      if (current) {
        const currentDetail = await systemPrompts.get(current.id)
        setCurrentPrompt(currentDetail)
        setEditedMainPrompt(currentDetail.prompt_text)
      } else {
        setCurrentPrompt(null)
        setEditedMainPrompt('')
      }
      setIsEditingMain(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!userRequirements.trim()) {
      setError('Please provide requirements for the system prompt')
      return
    }

    try {
      setGenerateLoading(true)
      setError('')
      
      const response = await systemPrompts.generate(client.id, {
        user_requirements: userRequirements,
        is_revision: isRevision,
        parent_version_id: parentVersionId
      })
      
      setGeneratedPrompt(response.prompt_text)
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerateLoading(false)
    }
  }

  const handleSave = async () => {
    if (!generatedPrompt.trim()) {
      setError('No prompt to save')
      return
    }

    try {
      setLoading(true)
      setError('')
      
      const savedPrompt = await systemPrompts.save(client.id, {
        prompt_text: generatedPrompt,
        user_requirements: userRequirements,
        generation_context: {
          generated_at: new Date().toISOString(),
          is_revision: isRevision,
          parent_version_id: parentVersionId
        },
        parent_version_id: parentVersionId
      })
      
      // Set the new prompt as current (for display purposes)
      await systemPrompts.setActive(client.id, savedPrompt.id)
      
      // Close modal and reload prompts
      setShowGenerateModal(false)
      setUserRequirements('')
      setGeneratedPrompt('')
      setIsRevision(false)
      setParentVersionId(null)
      await loadPrompts()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVersionChange = async (promptId) => {
    try {
      setLoading(true)
      await systemPrompts.setActive(client.id, parseInt(promptId))
      await loadPrompts()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRevise = () => {
    if (!currentPrompt) return
    
    setIsRevision(true)
    setParentVersionId(currentPrompt.id)
    setUserRequirements('')
    setGeneratedPrompt('')
    setShowGenerateModal(true)
  }

  const handleCopyPrompt = () => {
    if (currentPrompt) {
      copyToClipboard(currentPrompt.prompt_text, "System prompt copied to clipboard")
    }
  }

  const handleEditMain = () => {
    setIsEditingMain(true)
    setEditedMainPrompt(currentPrompt?.prompt_text || '')
  }

  const handleSaveMainEdit = async () => {
    if (!editedMainPrompt.trim() || !currentPrompt) {
      setError('No prompt content to save')
      return
    }

    try {
      setLoading(true)
      setError('')
      
      // Save as a new version with the edited content
      const savedPrompt = await systemPrompts.save(client.id, {
        prompt_text: editedMainPrompt,
        user_requirements: `Edited version of v${currentPrompt.version}`,
        generation_context: {
          edited_at: new Date().toISOString(),
          is_edit: true,
          parent_version_id: currentPrompt.id
        },
        parent_version_id: currentPrompt.id
      })
      
      // Set as current
      await systemPrompts.setActive(client.id, savedPrompt.id)
      
      // Reload and exit edit mode
      await loadPrompts()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCancelMainEdit = () => {
    setIsEditingMain(false)
    setEditedMainPrompt(currentPrompt?.prompt_text || '')
    setError('')
  }

  return (
    <Card>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <CardTitle className="flex items-center text-lg sm:text-xl">
            <MessageSquare className="mr-2 h-4 sm:h-5 w-4 sm:w-5" />
            Suggested System Prompt
          </CardTitle>
          <CardDescription className="text-sm">
            Turn enabled tools and resources into a prompt
          </CardDescription>
        </div>
        <div className="flex gap-2">
          {currentPrompt && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRevise}
              disabled={loading}
            >
              <Edit className="mr-2 h-4 w-4" />
              Revise
            </Button>
          )}
          <Button
            onClick={() => setShowGenerateModal(true)}
            disabled={loading}
            size="sm"
          >
            <Plus className="mr-2 h-4 w-4" />
            Generate
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-destructive/15 text-destructive text-sm rounded-md">
            {error}
          </div>
        )}

        {loading && <div className="text-center py-4 text-sm text-muted-foreground">Loading...</div>}

        {/* Current Prompt Display */}
        {currentPrompt && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="font-medium">Prompt</h4>
                <span className="px-2 py-1 text-xs bg-muted rounded">
                  v{currentPrompt.version}
                </span>
              </div>
              <div className="flex gap-2">
                {!isEditingMain ? (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleEditMain}
                      disabled={loading}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopyPrompt}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancelMainEdit}
                      disabled={loading}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSaveMainEdit}
                      disabled={loading || !editedMainPrompt.trim()}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </>
                )}
              </div>
            </div>
            
            {isEditingMain ? (
              <textarea
                value={editedMainPrompt}
                onChange={(e) => setEditedMainPrompt(e.target.value)}
                className="flex min-h-48 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                style={{ resize: 'vertical', minHeight: '12rem' }}
                placeholder="Edit your system prompt..."
              />
            ) : (
              <textarea
                value={currentPrompt.prompt_text}
                readOnly
                className="flex min-h-48 w-full rounded-md border border-input bg-muted px-3 py-2 text-sm shadow-sm font-mono whitespace-pre-wrap cursor-default"
                style={{ resize: 'vertical', minHeight: '12rem' }}
              />
            )}
            
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Created: {new Date(currentPrompt.created_at).toLocaleString()}</span>
              <div className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                <span>~{estimateTokens(currentPrompt.prompt_text).toLocaleString()} tokens</span>
              </div>
            </div>

            {/* Version Selector */}
            {prompts.length > 1 && !isEditingMain && (
              <div className="space-y-2">
                <Label htmlFor="version-select" className="text-sm font-medium">
                  Switch Version
                </Label>
                <Select
                  value={currentPrompt.id.toString()}
                  onValueChange={handleVersionChange}
                  disabled={loading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select version..." />
                  </SelectTrigger>
                  <SelectContent>
                    {prompts.map((prompt) => (
                      <SelectItem key={prompt.id} value={prompt.id.toString()}>
                        <div className="flex items-center gap-2">
                          <span>Version {prompt.version}</span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(prompt.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        )}

        {/* No Prompts State */}
        {!currentPrompt && !loading && (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">No system prompts yet.</p>
            <p className="text-xs mt-2">Generate your first system prompt to get started.</p>
          </div>
        )}
      </CardContent>

      {/* Generate Modal */}
      <Dialog open={showGenerateModal} onOpenChange={setShowGenerateModal}>
        <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {isRevision ? 'Revise System Prompt' : 'Generate System Prompt'}
            </DialogTitle>
            <DialogDescription>
              {isRevision 
                ? 'Describe how you want to improve the current system prompt.'
                : 'Describe what you want the AI assistant to do and how it should behave.'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="requirements">Requirements & Description</Label>
              <Textarea
                id="requirements"
                value={userRequirements}
                onChange={(e) => setUserRequirements(e.target.value)}
                placeholder="Describe what you want the AI assistant to do, how it should behave, and any specific requirements..."
                rows={4}
                className="mt-2"
                disabled={generateLoading}
              />
            </div>

            {generatedPrompt && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Generated Prompt (Editable)</Label>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Hash className="h-3 w-3" />
                    <span>~{estimateTokens(generatedPrompt).toLocaleString()} tokens</span>
                  </div>
                </div>
                <Textarea
                  value={generatedPrompt}
                  onChange={(e) => setGeneratedPrompt(e.target.value)}
                  className="mt-2 min-h-64 font-mono text-sm"
                  placeholder="Your generated prompt will appear here..."
                />
              </div>
            )}

            {error && (
              <div className="p-3 bg-destructive/15 text-destructive text-sm rounded-md">
                {error}
              </div>
            )}
          </div>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowGenerateModal(false)
                setUserRequirements('')
                setGeneratedPrompt('')
                setIsRevision(false)
                setParentVersionId(null)
                setError('')
              }}
            >
              Cancel
            </Button>
            
            {!generatedPrompt && (
              <Button
                onClick={handleGenerate}
                disabled={generateLoading || !userRequirements.trim()}
              >
                {generateLoading ? 'Generating...' : 'Generate'}
              </Button>
            )}

            {generatedPrompt && (
              <>
                <Button
                  variant="outline"
                  onClick={handleGenerate}
                  disabled={generateLoading}
                >
                  {generateLoading ? 'Regenerating...' : 'Regenerate'}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={loading}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {loading ? 'Saving...' : 'Save'}
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

export default SystemPromptPanel