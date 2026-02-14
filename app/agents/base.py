"""Base agent class for all AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
import json
import logging
from datetime import datetime
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agent_activity import AgentActivity, AgentType

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents using OpenAI GPT-4o."""
    
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
        
        # Configure OpenAI client
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model_name = settings.OPENAI_MODEL
        
        # Build function declarations for tools (OpenAI function-calling format)
        self.tool_declarations = self._build_tool_declarations()
        
        logger.info(f"Initialized {agent_name} with {len(self.tools)} tools")
    
    def _build_tool_declarations(self) -> List[Dict[str, Any]]:
        """Build function declarations from tools for OpenAI function calling."""
        declarations = []
        
        for tool in self.tools:
            # Extract function metadata
            func_name = tool.__name__
            func_doc = tool.__doc__ or ""
            
            # Build OpenAI function-calling schema
            declaration = {
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": func_doc.strip().split('\n')[0] if func_doc else func_name,
                    "parameters": self._extract_parameters(tool)
                }
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return {
                "response": response.choices[0].message.content or "",
                "metadata": {
                    "model": self.model_name,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error in simple execution: {str(e)}")
            raise
    
    def _execute_with_tools(self, prompt: str, db: Optional[Session]) -> Dict[str, Any]:
        """Execute with function calling support (OpenAI tool-use loop)."""
        try:
            # Build tools lookup
            tools_dict = {tool.__name__: tool for tool in self.tools}
            
            # Initial messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            all_tool_calls = []
            max_iterations = 10  # Safety limit to prevent infinite loops
            
            for _ in range(max_iterations):
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=self.tool_declarations,
                    tool_choice="auto",
                    temperature=0.7
                )
                
                assistant_message = response.choices[0].message
                messages.append(assistant_message)
                
                # If the model didn't call any tools, we're done
                if not assistant_message.tool_calls:
                    break
                
                # Process each tool call
                for tool_call in assistant_message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    all_tool_calls.append({
                        "name": func_name,
                        "args": func_args
                    })
                    
                    # Execute the tool
                    if func_name in tools_dict:
                        try:
                            result = tools_dict[func_name](**func_args)
                            tool_result = json.dumps(result) if not isinstance(result, str) else result
                        except Exception as tool_error:
                            logger.error(f"Tool {func_name} failed: {str(tool_error)}")
                            tool_result = json.dumps({"error": str(tool_error)})
                    else:
                        tool_result = json.dumps({"error": f"Unknown tool: {func_name}"})
                    
                    # Send tool result back to the model
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
            
            # Extract final text response
            final_content = assistant_message.content or ""
            
            return {
                "response": final_content,
                "tool_calls": all_tool_calls,
                "metadata": {
                    "model": self.model_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    }
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
