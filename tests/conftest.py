"""
Common test fixtures and configuration for the test suite.
"""
import os
import pytest
from moto import mock_s3
import boto3
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def env_setup():
    """Set up test environment variables."""
    os.environ["GROQ_API_KEY"] = "test_key"
    os.environ["GROQ_MODEL"] = "mixtral-8x7b-32768"
    os.environ["GROQ_TEMPERATURE"] = "0.7"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["S3_BUCKET_NAME"] = "test-bucket"
    os.environ["SMTP_SERVER"] = "test.smtp.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USERNAME"] = "test_user"
    os.environ["SMTP_PASSWORD"] = "test_pass"
    os.environ["TWITTER_API_KEY"] = "test_key"
    os.environ["TWITTER_API_SECRET"] = "test_secret"
    os.environ["TWITTER_ACCESS_TOKEN"] = "test_token"
    os.environ["TWITTER_ACCESS_SECRET"] = "test_secret"
    os.environ["LINKEDIN_CLIENT_ID"] = "test_id"
    os.environ["LINKEDIN_CLIENT_SECRET"] = "test_secret"
    os.environ["FACEBOOK_ACCESS_TOKEN"] = "test_token"

@pytest.fixture
def mock_s3_bucket():
    """Create a mock S3 bucket for testing."""
    with mock_s3():
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='test-bucket')
        yield s3

@pytest.fixture
def sample_press_release():
    """Provide a sample press release for testing."""
    return {
        "topic": "Test Press Release",
        "content": "This is a test press release content.",
        "timestamp": "20240229_123456",
        "type": "press_release"
    }

@pytest.fixture
def sample_recipients():
    """Provide sample recipients for testing."""
    return [
        {
            "name": "Test Journalist",
            "email": "test@example.com",
            "source": "https://example.com"
        },
        {
            "name": "Test Editor",
            "email": "editor@example.com",
            "source": "https://example.com"
        }
    ]

@pytest.fixture
def sample_email_status():
    """Provide sample email status for testing."""
    return {
        "test@example.com": True,
        "editor@example.com": True
    }

@pytest.fixture
def sample_social_media_status():
    """Provide sample social media status for testing."""
    return {
        "twitter": True,
        "linkedin": True,
        "facebook": True
    } 