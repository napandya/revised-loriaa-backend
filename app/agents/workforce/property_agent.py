"""Property management AI agent for document Q&A and guidance."""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.prompts.property_prompt import PROPERTY_AGENT_PROMPT
from app.agents.tools import document_tools
from app.models.agent_activity import AgentType


class PropertyAgent(BaseAgent):
    """
    Property management AI agent specialized in document Q&A, policy lookup,
    procedure guidance, and training support.
    """
    
    def __init__(self):
        """Initialize the property agent with appropriate tools."""
        tools = [
            document_tools.search_knowledge_base,
            document_tools.get_document,
            document_tools.answer_question,
            document_tools.list_documents
        ]
        
        super().__init__(
            agent_name="PropertyAgent",
            system_prompt=PROPERTY_AGENT_PROMPT,
            tools=tools,
            agent_type=AgentType.property_manager
        )
    
    def answer_policy_question(
        self,
        question: str,
        property_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Answer a question about property policies or procedures.
        
        Args:
            question: The question to answer
            property_id: Optional property ID for context
            db: Database session
        
        Returns:
            Dict with answer and sources
        """
        task = f"""Answer the following property management question:
        
        {question}
        
        {f'Property ID: {property_id}' if property_id else 'General question'}
        
        Steps:
        1. Search the knowledge base for relevant policies and documents
        2. Retrieve the most relevant information
        3. Generate a comprehensive answer with specific details
        4. Cite sources and document references
        5. Provide practical guidance if applicable
        
        Provide a clear, accurate answer with source citations."""
        
        context = {
            "question": question,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def find_procedure(
        self,
        procedure_name: str,
        property_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Find a specific procedure or process.
        
        Args:
            procedure_name: Name or description of the procedure
            property_id: Optional property ID
            db: Database session
        
        Returns:
            Dict with procedure details
        """
        task = f"""Find the procedure for: {procedure_name}
        
        {f'Property ID: {property_id}' if property_id else 'General procedure'}
        
        Steps:
        1. Search knowledge base for the procedure
        2. Retrieve the full procedure document
        3. Extract step-by-step instructions
        4. Note any property-specific variations
        5. Include relevant forms or documents needed
        
        Provide the complete procedure with clear steps."""
        
        context = {
            "procedure_name": procedure_name,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def explain_compliance_requirement(
        self,
        requirement: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Explain a compliance or regulatory requirement.
        
        Args:
            requirement: The compliance requirement to explain
            db: Database session
        
        Returns:
            Dict with explanation
        """
        task = f"""Explain the compliance requirement: {requirement}
        
        Steps:
        1. Search for relevant compliance documentation
        2. Explain the requirement in clear terms
        3. Provide rationale and legal basis
        4. Describe how to ensure compliance
        5. Note any common mistakes or pitfalls
        6. Reference relevant policies or procedures
        
        Provide a comprehensive explanation that helps staff understand and comply."""
        
        context = {"requirement": requirement}
        
        return self.execute(task=task, context=context, db=db)
    
    def provide_training_guidance(
        self,
        topic: str,
        property_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Provide training guidance on a topic.
        
        Args:
            topic: Training topic
            property_id: Optional property ID
            db: Database session
        
        Returns:
            Dict with training guidance
        """
        task = f"""Provide training guidance on: {topic}
        
        {f'Property ID: {property_id}' if property_id else 'General training'}
        
        Steps:
        1. Search knowledge base for relevant training materials
        2. Identify key concepts and procedures
        3. Outline learning objectives
        4. Provide step-by-step guidance
        5. Include examples and best practices
        6. Reference additional resources
        
        Provide comprehensive training guidance that helps staff learn effectively."""
        
        context = {
            "topic": topic,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def lookup_lease_term(
        self,
        term: str,
        property_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Lookup and explain a lease term or clause.
        
        Args:
            term: Lease term or clause to lookup
            property_id: Optional property ID
            db: Database session
        
        Returns:
            Dict with explanation
        """
        task = f"""Lookup and explain the lease term: {term}
        
        {f'Property ID: {property_id}' if property_id else 'General lease term'}
        
        Steps:
        1. Search lease documents and templates
        2. Find the specific term or clause
        3. Explain what it means in plain language
        4. Describe implications for residents and property
        5. Note any variations by property if applicable
        
        Provide a clear explanation of the lease term."""
        
        context = {
            "term": term,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def troubleshoot_issue(
        self,
        issue_description: str,
        property_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Help troubleshoot a property management issue.
        
        Args:
            issue_description: Description of the issue
            property_id: Optional property ID
            db: Database session
        
        Returns:
            Dict with troubleshooting guidance
        """
        task = f"""Help troubleshoot this issue: {issue_description}
        
        {f'Property ID: {property_id}' if property_id else ''}
        
        Steps:
        1. Search for relevant procedures and policies
        2. Identify potential causes and solutions
        3. Provide step-by-step troubleshooting steps
        4. Reference relevant documentation
        5. Suggest when to escalate if needed
        
        Provide practical troubleshooting guidance."""
        
        context = {
            "issue_description": issue_description,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def get_document_summary(
        self,
        doc_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get a summary of a specific document.
        
        Args:
            doc_id: Document ID
            db: Database session
        
        Returns:
            Dict with document summary
        """
        task = f"""Provide a summary of document: {doc_id}
        
        Steps:
        1. Retrieve the document
        2. Read and analyze the content
        3. Create a concise summary of key points
        4. Note document type and purpose
        5. Highlight any critical information
        
        Provide a clear, useful summary of the document."""
        
        context = {"doc_id": doc_id}
        
        return self.execute(task=task, context=context, db=db)
    
    def _get_agent_specific_context(self) -> Dict[str, Any]:
        """Get property management-specific context."""
        return {
            "agent_type": "property_manager",
            "capabilities": [
                "policy_lookup",
                "procedure_guidance",
                "compliance_explanation",
                "training_support",
                "document_qa"
            ]
        }
