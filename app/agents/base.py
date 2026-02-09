"""Base agent class for all AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
import json
import logging
from datetime import datetime
import google.generativeai as genai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agent_activity import AgentActivity, AgentType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents using Google Gemini."""
    
    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        tools: Optional[List[Callable]] = None,
        agent_type: Optional[AgentType] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name identifier for the agent
            system_prompt: System prompt defining agent behavior
            tools: List of callable functions available to the agent
            agent_type: Type of agent for activity logging
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.agent_type = agent_type
        
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Initialize model with function calling support
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_prompt
        )
        
        # Build function declarations for tools
        self.tool_declarations = self._build_tool_declarations()
        
        logger.info(f"Initialized {agent_name} with {len(self.tools)} tools")
    
    def _build_tool_declarations(self) -> List[Dict[str, Any]]:
        """Build function declarations from tools for Gemini."""
        declarations = []
        
        for tool in self.tools:
            # Extract function metadata
            func_name = tool.__name__
            func_doc = tool.__doc__ or ""
            
            # Parse docstring for parameters (basic implementation)
            declaration = {
                "name": func_name,
                "description": func_doc.strip().split('\n')[0] if func_doc else func_name,
                "parameters": self._extract_parameters(tool)
            }
            declarations.append(declaration)
        
        return declarations
    
    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """Extract function parameters and types."""
        import inspect
        
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'db']:
                continue
            
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == dict:
                    param_type = "object"
                elif param.annotation == list:
                    param_type = "array"
            
            parameters["properties"][param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            
            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        return parameters
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        lead_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using the agent.
        
        Args:
            task: The task or query to execute
            context: Additional context information
            db: Database session for logging
            lead_id: Optional lead ID for activity tracking
        
        Returns:
            Dict containing response and metadata
        """
        try:
            # Build the prompt with context
            full_prompt = self._build_prompt(task, context)
            
            # Log the activity start
            if db and self.agent_type:
                self.log_activity(
                    db=db,
                    action=f"execute_task",
                    result="started",
                    metadata={"task": task, "context": context},
                    lead_id=lead_id
                )
            
            # Generate response with function calling
            if self.tool_declarations:
                response = self._execute_with_tools(full_prompt, db)
            else:
                response = self._execute_simple(full_prompt)
            
            # Log successful completion
            if db and self.agent_type:
                self.log_activity(
                    db=db,
                    action=f"execute_task",
                    result="completed",
                    metadata={
                        "task": task,
                        "response_length": len(response.get("response", ""))
                    },
                    lead_id=lead_id
                )
            
            return {
                "success": True,
                "response": response.get("response", ""),
                "tool_calls": response.get("tool_calls", []),
                "metadata": response.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error executing task in {self.agent_name}: {str(e)}")
            
            # Log the error
            if db and self.agent_type:
                self.log_activity(
                    db=db,
                    action=f"execute_task",
                    result="error",
                    metadata={"task": task, "error": str(e)},
                    lead_id=lead_id
                )
            
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error: {str(e)}"
            }
    
    def _build_prompt(self, task: str, context: Optional[Dict[str, Any]]) -> str:
        """Build the full prompt with context."""
        if not context:
            return task
        
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"Context:\n{context_str}\n\nTask: {task}"
    
    def _execute_simple(self, prompt: str) -> Dict[str, Any]:
        """Execute without function calling."""
        try:
            response = self.model.generate_content(prompt)
            return {
                "response": response.text,
                "metadata": {}
            }
        except Exception as e:
            logger.error(f"Error in simple execution: {str(e)}")
            raise
    
    def _execute_with_tools(self, prompt: str, db: Optional[Session]) -> Dict[str, Any]:
        """Execute with function calling support."""
        try:
            # Create chat session
            chat = self.model.start_chat(enable_automatic_function_calling=True)
            
            # Build tools for the model
            tools_dict = {tool.__name__: tool for tool in self.tools}
            
            # Send message
            response = chat.send_message(
                prompt,
                tools=self.tools
            )
            
            # Extract tool calls if any
            tool_calls = []
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        fc = part.function_call
                        tool_calls.append({
                            "name": fc.name,
                            "args": dict(fc.args)
                        })
            
            return {
                "response": response.text if hasattr(response, 'text') else str(response),
                "tool_calls": tool_calls,
                "metadata": {
                    "model": settings.GEMINI_MODEL,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in tool execution: {str(e)}")
            raise
    
    def log_activity(
        self,
        db: Session,
        action: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None,
        lead_id: Optional[str] = None
    ) -> None:
        """
        Log agent activity to database.
        
        Args:
            db: Database session
            action: Action performed by agent
            result: Result of the action
            metadata: Additional metadata
            lead_id: Optional lead ID
        """
        try:
            if not self.agent_type:
                return
            
            activity = AgentActivity(
                agent_type=self.agent_type,
                action=action,
                result=result,
                metadata=metadata or {},
                lead_id=lead_id
            )
            
            db.add(activity)
            db.commit()
            
            logger.debug(f"Logged activity for {self.agent_name}: {action}")
            
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            db.rollback()
    
    @abstractmethod
    def _get_agent_specific_context(self) -> Dict[str, Any]:
        """Get agent-specific context. Implemented by subclasses."""
        pass
