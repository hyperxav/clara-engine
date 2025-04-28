"""Prompt management and validation for Clara Engine."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import structlog
from jinja2 import Template, Environment, meta

logger = structlog.get_logger(__name__)

class PromptTemplate(BaseModel):
    """Template for generating prompts."""
    name: str = Field(..., description="Unique name for the template")
    template: str = Field(..., description="Jinja2 template string")
    required_vars: List[str] = Field(default_factory=list, description="Required variables")
    max_length: Optional[int] = Field(default=None, description="Maximum length in characters")
    description: Optional[str] = Field(default=None, description="Template description")

    @validator("template")
    def validate_template(cls, v: str) -> str:
        """Validate the template string and extract required variables."""
        try:
            env = Environment()
            ast = env.parse(v)
            required = meta.find_undeclared_variables(ast)
            setattr(cls, "required_vars", list(required))
            return v
        except Exception as e:
            logger.error("Invalid template string", error=str(e))
            raise ValueError(f"Invalid template string: {e}")

class PromptManager:
    """Manager for handling prompt templates and generation."""

    def __init__(self) -> None:
        """Initialize the prompt manager."""
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        defaults = {
            "tweet_reply": PromptTemplate(
                name="tweet_reply",
                template="""You are Clara, a helpful AI assistant.
                Please provide a concise and helpful response to the following tweet:
                {{ tweet_text }}
                
                Context:
                {{ context }}
                
                Response should be:
                - Professional and friendly
                - Under {{ max_chars }} characters
                - Relevant to the tweet content
                - Include any necessary disclaimers
                """,
                description="Template for generating tweet replies",
                max_length=280
            ),
            # Add more default templates as needed
        }
        self.templates.update(defaults)
        logger.info("Loaded default templates", count=len(defaults))

    def add_template(self, template: PromptTemplate) -> None:
        """Add a new prompt template.
        
        Args:
            template: The template to add
        """
        if template.name in self.templates:
            logger.warning("Overwriting existing template", name=template.name)
        self.templates[template.name] = template
        logger.info("Added new template", name=template.name)

    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template by name.
        
        Args:
            name: Template name
            
        Returns:
            The prompt template
            
        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            logger.error("Template not found", name=name)
            raise KeyError(f"Template '{name}' not found")
        return self.templates[name]

    def render_prompt(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render a prompt using a template.
        
        Args:
            template_name: Name of the template to use
            variables: Variables to use in template rendering
            
        Returns:
            The rendered prompt string
        """
        template = self.get_template(template_name)
        
        # Validate required variables
        missing = [var for var in template.required_vars if var not in variables]
        if missing:
            logger.error("Missing required variables", missing=missing)
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
            
        # Render template
        try:
            env = Environment(autoescape=True)
            rendered = env.from_string(template.template).render(**variables)
            
            # Check length if max_length specified
            if template.max_length and len(rendered) > template.max_length:
                logger.warning(
                    "Rendered prompt exceeds max length",
                    length=len(rendered),
                    max_length=template.max_length
                )
                rendered = rendered[:template.max_length]
                
            return rendered
        except Exception as e:
            logger.error("Failed to render template", error=str(e))
            raise 