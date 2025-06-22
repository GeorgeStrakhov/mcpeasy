"""
System Prompt Generation Utilities
"""
import logging
from typing import List, Optional
import os

from ..tools.registry import ToolRegistry
from ..resources.registry import ResourceRegistry
from ..services.openrouter import get_openrouter_service

logger = logging.getLogger(__name__)

PROMPT_GENERATION_MODEL = os.getenv("PROMPT_GENERATION_MODEL", "anthropic/claude-sonnet-4")


async def generate_system_prompt(
    tool_registry: ToolRegistry,
    resource_registry: ResourceRegistry,
    enabled_tools: List[str],
    enabled_resources: List[str],
    user_requirements: str,
    is_revision: bool = False,
    previous_prompt: Optional[str] = None
) -> str:
    """Generate a system prompt using LLM based on enabled tools and resources"""
    
    openrouter = get_openrouter_service()
    if not openrouter:
        raise ValueError("OpenRouter service not available - check OPENROUTER_API_KEY")
    
    # Build tool descriptions
    tool_descriptions = []
    for tool_name in enabled_tools:
        tool_class = tool_registry.get_tool(tool_name)
        if tool_class:
            schema = tool_class.get_schema()
            description = f"**{tool_name}**: {schema.description}"
            
            # Add parameters info
            properties = schema.input_schema.get('properties', {})
            if properties:
                params = []
                for param, info in properties.items():
                    param_desc = f"{param}"
                    if info.get('description'):
                        param_desc += f" - {info['description']}"
                    params.append(param_desc)
                description += f"\n  Parameters: {', '.join(params)}"
            
            tool_descriptions.append(description)
    
    # Build resource descriptions
    resource_descriptions = []
    for resource_name in enabled_resources:
        resource_class = resource_registry.get_resource(resource_name)
        if resource_class:
            description = f"**{resource_name}**: {getattr(resource_class, 'description', 'No description available')}"
            resource_descriptions.append(description)
    
    # Create the LLM prompt
    if is_revision and previous_prompt:
        prompt_content = _create_revision_prompt(
            user_requirements, previous_prompt, tool_descriptions, resource_descriptions
        )
    else:
        prompt_content = _create_generation_prompt(
            user_requirements, tool_descriptions, resource_descriptions
        )
    
    # Call OpenRouter API
    messages = [{"role": "user", "content": prompt_content}]
    response = await openrouter.completion(
        messages=messages,
        model=PROMPT_GENERATION_MODEL,
        temperature=0.7,
        max_tokens=4000
    )
    
    if not response:
        raise ValueError("Failed to generate system prompt - OpenRouter returned no response")
    
    return response.strip()


def _create_generation_prompt(
    user_requirements: str, 
    tool_descriptions: List[str], 
    resource_descriptions: List[str]
) -> str:
    """Create prompt for generating a new system prompt"""
    
    tools_section = "\n".join(tool_descriptions) if tool_descriptions else "No tools configured"
    resources_section = "\n".join(resource_descriptions) if resource_descriptions else "No resources configured"
    
    return f"""You are an expert at writing system prompts for AI assistants. Your task is to create a comprehensive system prompt that will help an AI assistant effectively use the available tools and resources to help users.

USER REQUIREMENTS:
{user_requirements}

AVAILABLE TOOLS:
{tools_section}

AVAILABLE RESOURCES:
{resources_section}

Please create a system prompt that:
1. Clearly defines the AI assistant's role and capabilities
2. Explains how to effectively use the available tools
3. Describes how to access and utilize the available resources
4. Incorporates the user's specific requirements and use case
5. Provides guidance on when and how to use different tools
6. Is written in a clear, professional tone
7. Includes specific examples where relevant

The system prompt should be comprehensive but concise, and help the AI assistant provide maximum value to users while leveraging all available capabilities.

Please write only the system prompt content, without any prefacing or explanation."""


def _create_revision_prompt(
    user_requirements: str, 
    previous_prompt: str,
    tool_descriptions: List[str], 
    resource_descriptions: List[str]
) -> str:
    """Create prompt for revising an existing system prompt"""
    
    tools_section = "\n".join(tool_descriptions) if tool_descriptions else "No tools configured"
    resources_section = "\n".join(resource_descriptions) if resource_descriptions else "No resources configured"
    
    return f"""You are an expert at writing system prompts for AI assistants. Your task is to revise and improve an existing system prompt based on user feedback and current available tools/resources.

USER FEEDBACK/REQUIREMENTS:
{user_requirements}

CURRENT SYSTEM PROMPT:
{previous_prompt}

AVAILABLE TOOLS:
{tools_section}

AVAILABLE RESOURCES:
{resources_section}

Please revise the system prompt to:
1. Address the user's feedback and requirements
2. Ensure all currently available tools are properly incorporated
3. Ensure all currently available resources are properly described
4. Improve clarity and effectiveness based on the feedback
5. Maintain the professional tone and structure
6. Add or remove sections as needed based on the feedback

Please write only the revised system prompt content, without any prefacing or explanation."""