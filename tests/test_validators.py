"""Tests for response validation."""

import pytest
from clara_engine.openai.validators import (
    ResponseValidator,
    ValidationConfig,
    ValidationRule,
    ValidationResult,
    SafetyCheck,
    ContentCategory
)

@pytest.fixture
def validator():
    """Create a validator instance with test configuration."""
    config = ValidationConfig(
        max_tokens=10,
        max_length=50,
        model="gpt-3.5-turbo",
        content_filter=True,
        profanity_threshold=0.5,
        sentiment_threshold=-0.3,
        blocked_words={"badword", "blockedterm"}
    )
    return ResponseValidator(config)

@pytest.fixture
def custom_rule():
    """Create a custom validation rule for testing."""
    return ValidationRule(
        name="test_rule",
        enabled=True,
        severity="warning",
        parameters={"key": "value"}
    )

@pytest.mark.asyncio
async def test_validator_initialization():
    """Test validator initialization with different configurations."""
    # Default config
    validator = ResponseValidator()
    assert validator.config.max_tokens == 150
    assert validator.config.max_length == 280
    assert validator.config.model == "gpt-3.5-turbo"
    assert validator.config.content_filter is True

    # Custom config
    config = ValidationConfig(
        max_tokens=50,
        max_length=100,
        model="gpt-4",
        content_filter=False
    )
    validator = ResponseValidator(config)
    assert validator.config.max_tokens == 50
    assert validator.config.max_length == 100
    assert validator.config.model == "gpt-4"
    assert validator.config.content_filter is False

@pytest.mark.asyncio
async def test_basic_validation(validator):
    """Test basic validation checks."""
    # Valid response
    result = await validator.validate("Hello world!")
    assert result.valid is True
    assert len(result.errors) == 0
    assert result.token_count <= validator.config.max_tokens
    assert result.char_count <= validator.config.max_length

    # Response exceeding limits
    long_response = "This is a very long response that exceeds the configured limits for testing purposes."
    result = await validator.validate(long_response)
    assert result.valid is False
    assert any("exceeds" in error for error in result.errors)
    assert result.token_count > validator.config.max_tokens
    assert result.char_count > validator.config.max_length

@pytest.mark.asyncio
async def test_profanity_filtering(validator):
    """Test profanity filtering functionality."""
    # Clean text
    result = await validator.validate("Hello, this is a friendly message!")
    assert result.valid is True
    profanity_check = next(c for c in result.safety_checks if c.name == "profanity")
    assert profanity_check.passed is True
    assert profanity_check.score == 1.0

    # Text with blocked word
    result = await validator.validate("This contains a badword!")
    assert result.valid is False
    profanity_check = next(c for c in result.safety_checks if c.name == "profanity")
    assert profanity_check.passed is False
    assert profanity_check.score == 0.0
    assert "inappropriate language" in result.errors

@pytest.mark.asyncio
async def test_sentiment_analysis(validator):
    """Test sentiment analysis functionality."""
    # Positive sentiment
    result = await validator.validate("This is wonderful and amazing!")
    assert result.valid is True
    sentiment_check = next(c for c in result.safety_checks if c.name == "sentiment")
    assert sentiment_check.passed is True
    assert sentiment_check.details["polarity"] > 0

    # Negative sentiment
    result = await validator.validate("This is terrible and horrible!")
    sentiment_check = next(c for c in result.safety_checks if c.name == "sentiment")
    assert sentiment_check.passed is False
    assert sentiment_check.details["polarity"] < 0
    assert "negative sentiment" in result.warnings

@pytest.mark.asyncio
async def test_content_categorization(validator):
    """Test content categorization functionality."""
    # Spam content
    result = await validator.validate("Buy now! Special discount offer!")
    assert any(c.name == "spam" for c in result.categories)
    assert "may contain spam content" in result.warnings

    # Offensive content
    result = await validator.validate("You are stupid and dumb!")
    assert any(c.name == "offensive" for c in result.categories)
    assert "contains offensive content" in result.errors

    # Multiple categories
    result = await validator.validate("Buy now! This is the best guarantee ever!")
    categories = {c.name for c in result.categories}
    assert "spam" in categories
    assert "misleading" in categories

@pytest.mark.asyncio
async def test_validation_caching(validator):
    """Test validation result caching."""
    response = "Hello world!"
    
    # First validation
    result1 = await validator.validate(response)
    
    # Second validation (should use cache)
    result2 = await validator.validate(response)
    
    # Results should be identical
    assert result1.valid == result2.valid
    assert result1.token_count == result2.token_count
    assert result1.safety_score == result2.safety_score
    
    # Clear cache and validate again
    validator.clear_cache()
    result3 = await validator.validate(response)
    
    # Should be same values but different object
    assert result3.valid == result1.valid
    assert result3.token_count == result1.token_count
    assert result3.safety_score == result1.safety_score
    assert result3 is not result1

@pytest.mark.asyncio
async def test_blocked_words_management(validator):
    """Test blocked words management."""
    # Initial validation with default blocked words
    result = await validator.validate("This is a clean message.")
    assert result.valid is True

    # Add new blocked words
    new_words = {"test", "example"}
    validator.add_blocked_words(new_words)
    
    # Validate with newly blocked word
    result = await validator.validate("This is a test message.")
    assert result.valid is False
    assert "inappropriate language" in result.errors

@pytest.mark.asyncio
async def test_safety_score_calculation(validator):
    """Test safety score calculation."""
    # Completely safe content
    result = await validator.validate("Hello! This is a friendly and positive message.")
    assert result.safety_score == 1.0
    assert all(check.score == 1.0 for check in result.safety_checks)

    # Mixed content
    result = await validator.validate("This product is the best guarantee ever!")
    assert 0 < result.safety_score < 1.0
    assert len(result.safety_checks) > 0
    assert len(result.categories) > 0

@pytest.mark.asyncio
async def test_validation_rule_management(validator, custom_rule):
    """Test validation rule management."""
    # Add custom rule
    validator.add_rule(custom_rule)
    assert custom_rule in validator.config.rules
    
    # Validate with custom rule
    result = await validator.validate("Test message")
    assert custom_rule.name in result.metadata["validation_rules"]

@pytest.mark.asyncio
async def test_validation_models():
    """Test validation model classes."""
    # Test SafetyCheck
    check = SafetyCheck(
        name="test_check",
        passed=True,
        score=0.8,
        details={"key": "value"}
    )
    assert check.name == "test_check"
    assert check.passed is True
    assert check.score == 0.8
    assert check.details["key"] == "value"

    # Test ContentCategory
    category = ContentCategory(
        name="test_category",
        confidence=0.9,
        severity="warning"
    )
    assert category.name == "test_category"
    assert category.confidence == 0.9
    assert category.severity == "warning"

def test_validation_rule_severity():
    """Test validation rule severity validation."""
    # Valid severity
    rule = ValidationRule(name="test", severity="warning")
    assert rule.severity == "warning"
    
    # Invalid severity
    with pytest.raises(ValueError):
        ValidationRule(name="test", severity="invalid")

def test_validation_result_model():
    """Test ValidationResult model."""
    result = ValidationResult(
        valid=True,
        token_count=5,
        char_count=20,
        safety_score=0.95,
        metadata={"test": "value"}
    )
    assert result.valid is True
    assert result.token_count == 5
    assert result.char_count == 20
    assert result.safety_score == 0.95
    assert result.metadata["test"] == "value"
    assert isinstance(result.errors, list)
    assert isinstance(result.warnings, list) 