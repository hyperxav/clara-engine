"""Tweet generation using OpenAI."""

import structlog
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from clara_engine.openai.client import OpenAIClient
from clara_engine.openai.prompts import PromptManager
from clara_engine.openai.validators import ResponseValidator, ValidationResult
from clara_engine.knowledge.base import KnowledgeBase

logger = structlog.get_logger()

class TweetGenerationConfig(BaseModel):
    """Configuration for tweet generation."""
    max_attempts: int = Field(default=3, description="Maximum number of attempts to generate a valid tweet")
    temperature: float = Field(default=0.7, description="OpenAI temperature parameter")
    max_tokens: int = Field(default=100, description="Maximum tokens in generated tweet")
    model: str = Field(default="gpt-4", description="OpenAI model to use")
    use_knowledge_base: bool = Field(default=True, description="Whether to use knowledge base for context")
    max_context_entries: int = Field(default=3, description="Maximum number of knowledge base entries to include")
    context_similarity_threshold: float = Field(default=0.7, description="Minimum similarity for context entries")

class TweetGenerator:
    """Generates tweets using OpenAI."""
    
    def __init__(
        self,
        openai_client: OpenAIClient,
        prompt_manager: PromptManager,
        validator: ResponseValidator,
        knowledge_base: Optional[KnowledgeBase] = None,
        config: Optional[TweetGenerationConfig] = None
    ):
        """Initialize tweet generator.
        
        Args:
            openai_client: OpenAI client for API calls
            prompt_manager: Manager for prompt templates
            validator: Validator for generated tweets
            knowledge_base: Optional knowledge base for context
            config: Optional generation config
        """
        self.openai = openai_client
        self.prompts = prompt_manager
        self.validator = validator
        self.knowledge_base = knowledge_base
        self.config = config or TweetGenerationConfig()
        
        self.logger = logger.bind(component="tweet_generator")
    
    def _get_context_entries(
        self,
        topic: str,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Get relevant context entries from knowledge base.
        
        Args:
            topic: Topic to find context for
            metadata_filter: Optional metadata filter
            
        Returns:
            List of relevant context entries
        """
        if not self.knowledge_base or not self.config.use_knowledge_base:
            return []
            
        entries = self.knowledge_base.search(
            query=topic,
            metadata_filter=metadata_filter
        )
        
        return [entry.content for entry in entries[:self.config.max_context_entries]]
    
    async def generate_tweet(
        self,
        topic: str,
        previous_tweets: Optional[List[str]] = None,
        tone: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a tweet on the given topic.
        
        Args:
            topic: Main topic/subject for the tweet
            previous_tweets: Optional list of previous tweets for context
            tone: Optional tone specification (e.g. "professional", "casual")
            metadata_filter: Optional metadata filter for knowledge base
            
        Returns:
            Generated tweet text
            
        Raises:
            ValueError: If unable to generate valid tweet after max attempts
        """
        # Get context from knowledge base
        context_entries = self._get_context_entries(topic, metadata_filter)
        
        template = self.prompts.get_template("tweet_generation")
        variables = {
            "topic": topic,
            "previous_tweets": previous_tweets or [],
            "context_entries": context_entries,
            "tone": tone or "professional",
            "max_length": 280  # Twitter's character limit
        }
        
        prompt = template.render(**variables)
        
        for attempt in range(self.config.max_attempts):
            self.logger.debug(
                "generating_tweet",
                attempt=attempt + 1,
                topic=topic,
                tone=tone,
                context_count=len(context_entries)
            )
            
            completion = await self.openai.generate_completion(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                model=self.config.model
            )
            
            tweet_text = completion.choices[0].text.strip()
            validation: ValidationResult = await self.validator.validate(tweet_text)
            
            if validation.valid:
                self.logger.info(
                    "tweet_generated",
                    topic=topic,
                    attempt=attempt + 1,
                    length=len(tweet_text),
                    used_context=bool(context_entries)
                )
                return tweet_text
                
            self.logger.warning(
                "invalid_tweet",
                attempt=attempt + 1,
                errors=validation.errors,
                warnings=validation.warnings
            )
            
        raise ValueError(
            f"Failed to generate valid tweet after {self.config.max_attempts} attempts"
        ) 