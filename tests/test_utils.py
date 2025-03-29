"""
Tests for utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from utils import (
    extract_email_from_text,
    find_contact_page,
    search_recipients,
    send_email,
    post_to_social_media
)
import os

def test_extract_email_from_text():
    """Test email extraction from text."""
    text = """
    Contact us at test@example.com or support@example.com
    For more info, email info@example.com
    """
    emails = extract_email_from_text(text)
    assert len(emails) == 3
    assert "test@example.com" in emails
    assert "support@example.com" in emails
    assert "info@example.com" in emails

def test_extract_email_from_text_no_emails():
    """Test email extraction from text with no emails."""
    text = "This is a text without any email addresses."
    emails = extract_email_from_text(text)
    assert len(emails) == 0

@patch('requests.get')
def test_find_contact_page(mock_get):
    """Test finding contact page URL."""
    # Mock HTML response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <a href="/contact">Contact Us</a>
            <a href="/about">About</a>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    url = find_contact_page("https://example.com")
    assert url == "https://example.com/contact"

@patch('requests.get')
def test_find_contact_page_no_contact_link(mock_get):
    """Test finding contact page when no contact link exists."""
    # Mock HTML response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <a href="/home">Home</a>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    url = find_contact_page("https://example.com")
    assert url == "https://example.com"

@patch('requests.get')
def test_search_recipients_technology_topic(mock_get):
    """Test searching for recipients with a technology topic."""
    # Mock Google search response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <a href="https://techcrunch.com/author/john-doe">John Doe</a>
            <a href="https://wired.com/contact">Contact Us</a>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    recipients = search_recipients("technology startup")
    assert isinstance(recipients, list)
    assert any(r['platform'] in ['techcrunch.com', 'wired.com'] for r in recipients)

@patch('requests.get')
def test_search_recipients_business_topic(mock_get):
    """Test searching for recipients with a business topic."""
    # Mock Google search response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <a href="https://bloomberg.com/contact">Contact</a>
            <a href="https://reuters.com/editors">Editors</a>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    recipients = search_recipients("business news")
    assert isinstance(recipients, list)
    assert any(r['platform'] in ['bloomberg.com', 'reuters.com'] for r in recipients)

@patch('requests.get')
def test_search_recipients_with_roles(mock_get):
    """Test extracting recipient roles."""
    # Mock contact page response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <div>Senior Technology Editor John Smith</div>
            <div>Contact: john.smith@example.com</div>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    recipients = search_recipients("test topic")
    assert any(r['role'] == 'Senior' for r in recipients)
    assert any(r['role'] == 'Technology' for r in recipients)

@patch('requests.get')
def test_search_recipients_name_matching(mock_get):
    """Test matching names with email addresses."""
    # Mock contact page response
    mock_response = MagicMock()
    mock_response.text = """
    <html>
        <body>
            <div>Jane Doe - Senior Editor</div>
            <div>Email: jane.doe@example.com</div>
        </body>
    </html>
    """
    mock_get.return_value = mock_response
    
    recipients = search_recipients("test topic")
    assert any(r['name'] == 'Jane Doe' and r['email'] == 'jane.doe@example.com' for r in recipients)

@patch('requests.get')
def test_search_recipients_relevance_sorting(mock_get):
    """Test recipient sorting by relevance."""
    # Mock responses for different platforms
    mock_responses = [
        MagicMock(text='<a href="https://techcrunch.com">TechCrunch</a>'),
        MagicMock(text='<a href="https://unknown.com">Unknown</a>')
    ]
    mock_get.side_effect = mock_responses
    
    recipients = search_recipients("technology")
    if len(recipients) > 1:
        # Platform matches should come first
        assert recipients[0]['platform'] != 'unknown'
        # Recipients with roles should be preferred
        if any(r['role'] for r in recipients):
            assert recipients[0]['role'] != ''

@patch('requests.get')
def test_search_recipients_no_matches(mock_get):
    """Test behavior when no relevant recipients are found."""
    # Mock empty response
    mock_response = MagicMock()
    mock_response.text = "<html><body>No results</body></html>"
    mock_get.return_value = mock_response
    
    recipients = search_recipients("nonexistent topic")
    assert isinstance(recipients, list)
    assert len(recipients) == 0

@patch('smtplib.SMTP')
def test_send_email(mock_smtp, sample_recipients):
    """Test sending emails."""
    # Mock SMTP server
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    status = send_email(sample_recipients, "Test press release")
    
    assert len(status) == len(sample_recipients)
    assert all(status.values())
    mock_server.send_message.assert_called()

@patch('smtplib.SMTP')
def test_send_email_failure(mock_smtp, sample_recipients):
    """Test email sending failure."""
    # Mock SMTP server to raise an exception
    mock_smtp.side_effect = Exception("SMTP Error")
    
    status = send_email(sample_recipients, "Test press release")
    
    assert len(status) == len(sample_recipients)
    assert not any(status.values())

@patch('tweepy.API')
@patch('linkedin_api.Linkedin')
@patch('facebook.GraphAPI')
def test_post_to_social_media(mock_facebook, mock_linkedin, mock_twitter):
    """Test posting to social media platforms."""
    # Mock successful posting
    mock_twitter.return_value.update_status.return_value = True
    mock_linkedin.return_value.post.return_value = True
    mock_facebook.return_value.put_object.return_value = True
    
    status = post_to_social_media("Test press release")
    
    assert status["twitter"] is True
    assert status["linkedin"] is True
    assert status["facebook"] is True

@patch('tweepy.API')
@patch('linkedin_api.Linkedin')
@patch('facebook.GraphAPI')
def test_post_to_social_media_partial_failure(mock_facebook, mock_linkedin, mock_twitter):
    """Test partial failure in social media posting."""
    # Mock Twitter success, LinkedIn failure, Facebook success
    mock_twitter.return_value.update_status.return_value = True
    mock_linkedin.side_effect = Exception("LinkedIn Error")
    mock_facebook.return_value.put_object.return_value = True
    
    status = post_to_social_media("Test press release")
    
    assert status["twitter"] is True
    assert status["linkedin"] is False
    assert status["facebook"] is True

def test_extract_email_from_text_with_invalid_emails():
    """Test email extraction with invalid email formats."""
    text = """
    Invalid emails: test@, @example.com, test@.com
    Valid email: test@example.com
    """
    emails = extract_email_from_text(text)
    assert len(emails) == 1
    assert "test@example.com" in emails 

@patch('requests.get')
def test_search_recipients_with_news_api(mock_get):
    """Test searching for recipients using News API."""
    # Mock News API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'articles': [
            {
                'source': {'url': 'https://techcrunch.com'},
                'url': 'https://techcrunch.com/article1'
            },
            {
                'source': {'url': 'https://euractiv.com'},
                'url': 'https://euractiv.com/article2'
            }
        ]
    }
    mock_get.return_value = mock_response
    
    recipients = search_recipients("technology startup")
    assert isinstance(recipients, list)
    assert any(r['platform'] in ['techcrunch.com', 'euractiv.com'] for r in recipients)

@patch('requests.get')
def test_search_recipients_regional_diversity(mock_get):
    """Test regional diversity in recipient search."""
    # Mock News API response with articles from different regions
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'articles': [
            {
                'source': {'url': 'https://techinasia.com'},
                'url': 'https://techinasia.com/article1'
            },
            {
                'source': {'url': 'https://tech.eu'},
                'url': 'https://tech.eu/article2'
            },
            {
                'source': {'url': 'https://startups.com.br'},
                'url': 'https://startups.com.br/article3'
            }
        ]
    }
    mock_get.return_value = mock_response
    
    recipients = search_recipients("technology")
    regions = {r['region'] for r in recipients}
    assert len(regions) > 1  # Should have multiple regions
    assert any(r['region'] == 'asia' for r in recipients)
    assert any(r['region'] == 'europe' for r in recipients)
    assert any(r['region'] == 'latin_america' for r in recipients)

@patch('requests.get')
def test_search_recipients_news_api_fallback(mock_get):
    """Test fallback to basic search when News API fails."""
    # Mock News API failure
    mock_response = MagicMock()
    mock_response.json.return_value = {'status': 'error'}
    mock_get.return_value = mock_response
    
    recipients = search_recipients("test topic")
    assert isinstance(recipients, list)
    # Should still return results from fallback search

@patch('requests.get')
def test_search_recipients_article_urls(mock_get):
    """Test inclusion of article URLs in recipient data."""
    # Mock News API response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'articles': [
            {
                'source': {'url': 'https://techcrunch.com'},
                'url': 'https://techcrunch.com/article1'
            }
        ]
    }
    mock_get.return_value = mock_response
    
    recipients = search_recipients("technology")
    assert any(r.get('article_url') == 'https://techcrunch.com/article1' for r in recipients)

@patch('requests.get')
def test_search_recipients_platform_specific(mock_get):
    """Test platform-specific recipient search."""
    # Mock News API response with business-focused articles
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'status': 'ok',
        'articles': [
            {
                'source': {'url': 'https://bloomberg.com'},
                'url': 'https://bloomberg.com/article1'
            },
            {
                'source': {'url': 'https://nikkei.com'},
                'url': 'https://nikkei.com/article2'
            }
        ]
    }
    mock_get.return_value = mock_response
    
    recipients = search_recipients("business")
    assert any(r['platform'] == 'bloomberg.com' for r in recipients)
    assert any(r['platform'] == 'nikkei.com' for r in recipients)

@patch('requests.get')
def test_search_recipients_no_news_api_key(mock_get):
    """Test behavior when News API key is not set."""
    # Mock environment variable not set
    with patch.dict(os.environ, {}, clear=True):
        recipients = search_recipients("test topic")
        assert isinstance(recipients, list)
        # Should fall back to basic search 