"""Tests for prompt management functionality."""

import pytest
from clara_engine.openai.prompts import PromptTemplate, PromptManager

def test_prompt_template_validation():
    """Test prompt template validation."""
    # Valid template
    template = PromptTemplate(
        name="test",
        template="Hello {{ name }}!",
        description="Test template"
    )
    assert template.required_vars == ["name"]
    
    # Invalid template
    with pytest.raises(ValueError):
        PromptTemplate(
            name="invalid",
            template="Hello {{ name!",
            description="Invalid template"
        )

def test_prompt_manager_defaults():
    """Test prompt manager default templates."""
    manager = PromptManager()
    assert "tweet_reply" in manager.templates
    
    template = manager.get_template("tweet_reply")
    assert template.name == "tweet_reply"
    assert template.max_length == 280

def test_add_template():
    """Test adding new templates."""
    manager = PromptManager()
    
    new_template = PromptTemplate(
        name="greeting",
        template="Hello {{ name }}! How are you {{ time_of_day }}?",
        description="Greeting template"
    )
    manager.add_template(new_template)
    
    assert "greeting" in manager.templates
    retrieved = manager.get_template("greeting")
    assert retrieved.required_vars == ["name", "time_of_day"]

def test_template_not_found():
    """Test error handling for missing templates."""
    manager = PromptManager()
    
    with pytest.raises(KeyError):
        manager.get_template("nonexistent")

def test_render_prompt():
    """Test prompt rendering."""
    manager = PromptManager()
    
    # Add test template
    template = PromptTemplate(
        name="test",
        template="Hello {{ name }}! Count: {{ count }}",
        max_length=20
    )
    manager.add_template(template)
    
    # Test successful rendering
    rendered = manager.render_prompt(
        "test",
        {"name": "Alice", "count": 42}
    )
    assert rendered == "Hello Alice! Count: 42"
    
    # Test missing variables
    with pytest.raises(ValueError) as exc:
        manager.render_prompt("test", {"name": "Bob"})
    assert "Missing required variables" in str(exc.value)
    
    # Test length truncation
    long_rendered = manager.render_prompt(
        "test",
        {"name": "Bob" * 10, "count": 9999}
    )
    assert len(long_rendered) == 20

def test_tweet_reply_template():
    """Test the default tweet reply template."""
    manager = PromptManager()
    
    variables = {
        "tweet_text": "When will AI take over the world?",
        "context": "User is curious about AI safety",
        "max_chars": 240
    }
    
    rendered = manager.render_prompt("tweet_reply", variables)
    assert len(rendered) <= 280
    assert "tweet_text" in rendered
    assert "context" in rendered 