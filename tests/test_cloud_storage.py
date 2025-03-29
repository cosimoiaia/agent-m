"""
Tests for the cloud storage functionality.
"""
import pytest
import json
from cloud_storage import CloudStorage

def test_store_press_release(mock_s3_bucket, sample_press_release):
    """Test storing a press release in S3."""
    storage = CloudStorage()
    
    # Store the press release
    url = storage.store_press_release(
        sample_press_release["topic"],
        sample_press_release["content"]
    )
    
    # Verify the URL format
    assert url.startswith("s3://test-bucket/press_releases/")
    
    # Retrieve and verify the content
    stored_data = storage.get_press_release(url)
    assert stored_data["topic"] == sample_press_release["topic"]
    assert stored_data["content"] == sample_press_release["content"]
    assert stored_data["type"] == "press_release"
    assert "timestamp" in stored_data

def test_store_email(mock_s3_bucket, sample_press_release, sample_recipients, sample_email_status):
    """Test storing email details in S3."""
    storage = CloudStorage()
    
    # Store the email details
    url = storage.store_email(
        sample_press_release["topic"],
        sample_press_release["content"],
        sample_recipients,
        sample_email_status
    )
    
    # Verify the URL format
    assert url.startswith("s3://test-bucket/emails/")
    
    # Retrieve and verify the content
    stored_data = storage.get_email(url)
    assert stored_data["topic"] == sample_press_release["topic"]
    assert stored_data["press_release"] == sample_press_release["content"]
    assert stored_data["recipients"] == sample_recipients
    assert stored_data["email_status"] == sample_email_status
    assert stored_data["type"] == "email"
    assert "timestamp" in stored_data

def test_get_press_release_invalid_url(mock_s3_bucket):
    """Test retrieving a press release with an invalid URL."""
    storage = CloudStorage()
    
    with pytest.raises(Exception):
        storage.get_press_release("s3://test-bucket/invalid/path.json")

def test_get_email_invalid_url(mock_s3_bucket):
    """Test retrieving email details with an invalid URL."""
    storage = CloudStorage()
    
    with pytest.raises(Exception):
        storage.get_email("s3://test-bucket/invalid/path.json")

def test_store_press_release_with_special_characters(mock_s3_bucket):
    """Test storing a press release with special characters in the topic."""
    storage = CloudStorage()
    topic = "Test!@#$%^&*() Press Release"
    content = "Test content with special chars: !@#$%^&*()"
    
    url = storage.store_press_release(topic, content)
    stored_data = storage.get_press_release(url)
    
    assert stored_data["topic"] == topic
    assert stored_data["content"] == content

def test_store_email_with_empty_recipients(mock_s3_bucket, sample_press_release):
    """Test storing email details with an empty recipients list."""
    storage = CloudStorage()
    
    url = storage.store_email(
        sample_press_release["topic"],
        sample_press_release["content"],
        [],
        {}
    )
    
    stored_data = storage.get_email(url)
    assert stored_data["recipients"] == []
    assert stored_data["email_status"] == {} 