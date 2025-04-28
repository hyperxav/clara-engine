"""Response validation for OpenAI API responses."""

from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field, field_validator
import structlog
from tiktoken import get_encoding
from better_profanity import profanity
from textblob import TextBlob
import re

logger = structlog.get_logger(__name__)

class ContentCategory(BaseModel):
    """Content category with confidence score."""
    name: str = Field(..., description="Category name")
    confidence: float = Field(..., description="Confidence score (0-1)")
    severity: str = Field(default="info", description="Category severity level")

class SafetyCheck(BaseModel):
    """Result of a safety check."""
    name: str = Field(..., description="Name of the safety check")
    passed: bool = Field(..., description="Whether the check passed")
    score: float = Field(..., description="Safety score (0-1)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")

class ValidationRule(BaseModel):
    """Configuration for a single validation rule."""
    name: str = Field(..., description="Name of the validation rule")
    enabled: bool = Field(default=True, description="Whether this rule is enabled")
    severity: str = Field(default="error", description="Severity level of rule violations")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific parameters")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        allowed = ["error", "warning", "info"]
        if v not in allowed:
            raise ValueError(f"Severity must be one of: {', '.join(allowed)}")
        return v

class ValidationConfig(BaseModel):
    """Configuration for response validation."""
    max_tokens: int = Field(default=150, description="Maximum allowed tokens")
    max_length: int = Field(default=280, description="Maximum length in characters")
    model: str = Field(default="gpt-3.5-turbo", description="Model to use for token counting")
    content_filter: bool = Field(default=True, description="Whether to enable content filtering")
    profanity_threshold: float = Field(default=0.5, description="Threshold for profanity detection")
    sentiment_threshold: float = Field(default=-0.3, description="Minimum allowed sentiment score")
    rules: List[ValidationRule] = Field(default_factory=list, description="List of validation rules")
    cache_enabled: bool = Field(default=True, description="Whether to enable validation caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    blocked_words: Set[str] = Field(default_factory=set, description="Additional blocked words")
    content_categories: List[str] = Field(
        default=["spam", "offensive", "misleading", "harmful"],
        description="Content categories to check"
    )

class ValidationResult(BaseModel):
    """Result of validation checks."""
    valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    token_count: int = Field(..., description="Number of tokens in response")
    char_count: int = Field(..., description="Number of characters in response")
    safety_score: float = Field(default=1.0, description="Overall safety score (0-1)")
    safety_checks: List[SafetyCheck] = Field(default_factory=list, description="Individual safety checks")
    categories: List[ContentCategory] = Field(default_factory=list, description="Detected content categories")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ResponseValidator:
    """Validator for OpenAI API responses."""

    def __init__(self, config: Optional[ValidationConfig] = None) -> None:
        """Initialize the validator.
        
        Args:
            config: Validation configuration. If not provided, uses defaults.
        """
        self.config = config or ValidationConfig()
        self.tokenizer = get_encoding("cl100k_base")  # GPT-4 and GPT-3.5 tokenizer
        self._cache: Dict[str, ValidationResult] = {}
        
        # Initialize profanity filter with custom words
        profanity.load_censor_words()
        if self.config.blocked_words:
            profanity.add_censor_words(self.config.blocked_words)
            
        logger.info(
            "Initialized ResponseValidator",
            max_tokens=self.config.max_tokens,
            max_length=self.config.max_length,
            content_filter=self.config.content_filter
        )

    def _check_profanity(self, text: str) -> SafetyCheck:
        """Check text for profanity.
        
        Args:
            text: Text to check
            
        Returns:
            SafetyCheck result
        """
        contains_profanity = profanity.contains_profanity(text)
        censored = profanity.censor(text)
        profanity_score = 1.0 if not contains_profanity else 0.0
        
        return SafetyCheck(
            name="profanity",
            passed=not contains_profanity,
            score=profanity_score,
            details={
                "censored_text": censored,
                "contains_profanity": contains_profanity
            }
        )

    def _analyze_sentiment(self, text: str) -> SafetyCheck:
        """Analyze text sentiment.
        
        Args:
            text: Text to analyze
            
        Returns:
            SafetyCheck result
        """
        blob = TextBlob(text)
        sentiment_score = (blob.sentiment.polarity + 1) / 2  # Convert to 0-1 scale
        passed = blob.sentiment.polarity >= self.config.sentiment_threshold
        
        return SafetyCheck(
            name="sentiment",
            passed=passed,
            score=sentiment_score,
            details={
                "polarity": blob.sentiment.polarity,
                "subjectivity": blob.sentiment.subjectivity
            }
        )

    def _categorize_content(self, text: str) -> List[ContentCategory]:
        """Categorize content based on patterns and keywords.
        
        Args:
            text: Text to categorize
            
        Returns:
            List of detected categories with confidence scores
        """
        categories = []
        text_lower = text.lower()
        
        # Simple pattern matching for categories
        patterns = {
            "spam": (
                r"\b(buy|sell|discount|offer|click|subscribe|win|lottery|prize)\b",
                "warning"
            ),
            "offensive": (
                r"\b(hate|angry|stupid|idiot|dumb)\b",
                "error"
            ),
            "misleading": (
                r"\b(guarantee|promise|best|perfect|always|never)\b",
                "warning"
            ),
            "harmful": (
                r"\b(danger|warning|caution|threat|risk)\b",
                "error"
            )
        }
        
        for category, (pattern, severity) in patterns.items():
            if category in self.config.content_categories:
                matches = len(re.findall(pattern, text_lower))
                if matches > 0:
                    confidence = min(matches * 0.2, 1.0)  # Scale with number of matches
                    categories.append(ContentCategory(
                        name=category,
                        confidence=confidence,
                        severity=severity
                    ))
        
        return categories

    async def validate(self, response: str) -> ValidationResult:
        """Validate an OpenAI API response.
        
        Args:
            response: The response text to validate
            
        Returns:
            ValidationResult containing validation details
        """
        # Check cache if enabled
        if self.config.cache_enabled:
            cache_key = f"{response}:{self.config.model}"
            if cache_key in self._cache:
                logger.debug("Cache hit for response validation")
                return self._cache[cache_key]

        # Basic validation
        token_count = len(self.tokenizer.encode(response))
        char_count = len(response)
        
        errors = []
        warnings = []
        safety_checks = []
        
        # Token limit check
        if token_count > self.config.max_tokens:
            errors.append(
                f"Response exceeds token limit: {token_count} > {self.config.max_tokens}"
            )
        
        # Length check
        if char_count > self.config.max_length:
            errors.append(
                f"Response exceeds length limit: {char_count} > {self.config.max_length}"
            )
        
        # Content safety checks
        if self.config.content_filter:
            # Profanity check
            profanity_check = self._check_profanity(response)
            safety_checks.append(profanity_check)
            if not profanity_check.passed:
                errors.append("Response contains inappropriate language")
            
            # Sentiment analysis
            sentiment_check = self._analyze_sentiment(response)
            safety_checks.append(sentiment_check)
            if not sentiment_check.passed:
                warnings.append("Response has negative sentiment")
            
            # Content categorization
            categories = self._categorize_content(response)
            for category in categories:
                if category.severity == "error":
                    errors.append(f"Response contains {category.name} content")
                elif category.severity == "warning":
                    warnings.append(f"Response may contain {category.name} content")
        
        # Calculate overall safety score
        safety_scores = [check.score for check in safety_checks]
        overall_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 1.0
        
        # Create result
        result = ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            token_count=token_count,
            char_count=char_count,
            safety_score=overall_safety,
            safety_checks=safety_checks,
            categories=categories,
            metadata={
                "model": self.config.model,
                "validation_rules": [r.name for r in self.config.rules if r.enabled]
            }
        )
        
        # Cache result if enabled
        if self.config.cache_enabled:
            self._cache[cache_key] = result
        
        return result

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a new validation rule.
        
        Args:
            rule: The validation rule to add
        """
        self.config.rules.append(rule)
        logger.info("Added validation rule", rule=rule.name)

    def add_blocked_words(self, words: Set[str]) -> None:
        """Add additional words to the block list.
        
        Args:
            words: Set of words to block
        """
        self.config.blocked_words.update(words)
        profanity.add_censor_words(words)
        logger.info("Added blocked words", count=len(words))

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._cache.clear()
        logger.debug("Cleared validation cache") 