"""
Tests for the main application functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from app import (
    press_release_writer,
    recipient_search,
    email_distributor,
    social_media_poster,
    AgentState
)

@pytest.fixture
def sample_state():
    """Provide a sample agent state for testing."""
    return {
        "topic": "Test Topic",
        "press_release": "",
        "press_release_url": "",
        "recipients": [],
        "email_status": {},
        "email_url": "",
        "social_media_status": {},
        "current_step": "initial",
        "approved": False
    }

@patch('app.client')
def test_press_release_writer(mock_client, sample_state):
    """Test press release generation."""
    # Mock Groq response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test press release content"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    state = press_release_writer(sample_state)
    
    assert state["press_release"] == "Test press release content"
    assert state["current_step"] == "press_release"

@patch('utils.search_recipients')
def test_recipient_search(mock_search, sample_state, sample_recipients):
    """Test recipient search functionality."""
    mock_search.return_value = sample_recipients
    
    state = recipient_search(sample_state)
    
    assert state["recipients"] == sample_recipients
    assert state["current_step"] == "recipients"

@patch('cloud_storage.CloudStorage')
@patch('utils.send_email')
def test_email_distributor(mock_send_email, mock_storage, sample_state, sample_recipients, sample_email_status, mock_s3_bucket):
    """Test email distribution process."""
    # Mock storage
    mock_storage_instance = MagicMock()
    mock_storage_instance.store_press_release.return_value = "s3://test-bucket/press_releases/test.json"
    mock_storage_instance.store_email.return_value = "s3://test-bucket/emails/test.json"
    mock_storage.return_value = mock_storage_instance
    
    # Mock email sending
    mock_send_email.return_value = sample_email_status
    
    # Update state with required data
    sample_state["press_release"] = "Test press release"
    sample_state["recipients"] = sample_recipients
    
    state = email_distributor(sample_state)
    
    assert state["press_release_url"] == "s3://test-bucket/press_releases/test.json"
    assert state["email_url"] == "s3://test-bucket/emails/test.json"
    assert state["email_status"] == sample_email_status
    assert state["current_step"] == "email"

@patch('utils.post_to_social_media')
def test_social_media_poster(mock_post, sample_state, sample_social_media_status):
    """Test social media posting process."""
    mock_post.return_value = sample_social_media_status
    
    state = social_media_poster(sample_state)
    
    assert state["social_media_status"] == sample_social_media_status
    assert state["current_step"] == "social_media"

def test_agent_state_validation():
    """Test AgentState type validation."""
    state = AgentState(
        topic="Test Topic",
        press_release="Test content",
        press_release_url="s3://test-bucket/test.json",
        recipients=[],
        email_status={},
        email_url="s3://test-bucket/email.json",
        social_media_status={},
        current_step="initial",
        approved=False
    )
    
    assert isinstance(state, dict)
    assert all(key in state for key in AgentState.__annotations__)

@patch('app.client')
def test_press_release_writer_error_handling(mock_client, sample_state):
    """Test error handling in press release generation."""
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        press_release_writer(sample_state)

@patch('utils.search_recipients')
def test_recipient_search_error_handling(mock_search, sample_state):
    """Test error handling in recipient search."""
    mock_search.side_effect = Exception("Search Error")
    
    with pytest.raises(Exception):
        recipient_search(sample_state)

@patch('cloud_storage.CloudStorage')
@patch('utils.send_email')
def test_email_distributor_error_handling(mock_send_email, mock_storage, sample_state):
    """Test error handling in email distribution."""
    mock_storage_instance = MagicMock()
    mock_storage_instance.store_press_release.side_effect = Exception("Storage Error")
    mock_storage.return_value = mock_storage_instance
    
    with pytest.raises(Exception):
        email_distributor(sample_state)

@patch('utils.post_to_social_media')
def test_social_media_poster_error_handling(mock_post, sample_state):
    """Test error handling in social media posting."""
    mock_post.side_effect = Exception("Social Media Error")
    
    with pytest.raises(Exception):
        social_media_poster(sample_state) 