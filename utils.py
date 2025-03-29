"""
Utility functions for the Press Release Distribution Agent.

This module provides helper functions for:
- Web scraping and recipient search
- Email distribution
- Social media posting
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict
import tweepy
from linkedin_api import Linkedin
import facebook
import re
from urllib.parse import urljoin
import time

def extract_email_from_text(text: str) -> List[str]:
    """
    Extract email addresses from text using regex pattern matching.
    
    Args:
        text (str): The text to search for email addresses
        
    Returns:
        List[str]: List of unique email addresses found in the text
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_pattern, text)))

def find_contact_page(url: str) -> str:
    """
    Find the contact page URL from a website's homepage.
    
    Args:
        url (str): The website's homepage URL
        
    Returns:
        str: The URL of the contact page or the original URL if not found
        
    The function searches for common contact page patterns in the website's links.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Common contact page patterns
        contact_patterns = [
            r'contact',
            r'about',
            r'staff',
            r'team',
            r'writers',
            r'editors'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            if any(pattern in href for pattern in contact_patterns):
                return urljoin(url, href)
        
        return url
    except:
        return url

def search_recipients(topic: str) -> List[Dict[str, str]]:
    """
    Search for relevant journalists, editors, and bloggers based on the topic using News API.
    
    Args:
        topic (str): The topic to search for relevant contacts
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing recipient information
        
    The function:
    1. Uses News API to find relevant articles and sources
    2. Visits found websites
    3. Extracts contact information
    4. Validates and deduplicates results
    """
    recipients = []
    
    # International platforms and publications by region
    platforms = {
        "technology": [
            # Global Tech
            "techcrunch.com",
            "venturebeat.com",
            "wired.com",
            "theverge.com",
            "zdnet.com",
            "arstechnica.com",
            # Europe
            "euractiv.com",
            "tech.eu",
            "sifted.eu",
            # Asia
            "techinasia.com",
            "kr-asia.com",
            "36kr.com",
            # Latin America
            "techcrunch.com/latam",
            "startups.com.br"
        ],
        "business": [
            # Global Business
            "bloomberg.com",
            "reuters.com",
            "forbes.com",
            "businesswire.com",
            "prnewswire.com",
            # Europe
            "ft.com",
            "economist.com",
            "handelsblatt.com",
            # Asia
            "nikkei.com",
            "scmp.com",
            "mint.in",
            # Latin America
            "valor.com.br",
            "elmercurio.com"
        ],
        "science": [
            # Global Science
            "nature.com",
            "science.org",
            "scientificamerican.com",
            "newscientist.com",
            # Europe
            "sciencebusiness.net",
            "researchprofessional.com",
            # Asia
            "natureasia.com",
            "science.org.cn",
            # Latin America
            "scielo.org",
            "cienciahoje.org.br"
        ],
        "health": [
            # Global Health
            "medscape.com",
            "healthline.com",
            "webmd.com",
            "medicalnewstoday.com",
            # Europe
            "bmj.com",
            "thelancet.com",
            # Asia
            "healthcareasia.org",
            "healthcare.digital",
            # Latin America
            "panorama.sanidad.gob.es",
            "saude.gov.br"
        ],
        "default": [
            # Global News
            "medium.com",
            "wordpress.com",
            "blogspot.com",
            "substack.com",
            "news.google.com",
            # Europe
            "euronews.com",
            "politico.eu",
            # Asia
            "asia.nikkei.com",
            "straitstimes.com",
            # Latin America
            "mercopress.com",
            "infobae.com"
        ]
    }
    
    # Determine relevant platforms based on topic keywords
    relevant_platforms = set()
    topic_lower = topic.lower()
    for category, platform_list in platforms.items():
        if category in topic_lower:
            relevant_platforms.update(platform_list)
    if not relevant_platforms:
        relevant_platforms.update(platforms["default"])
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Use News API to find relevant articles and sources
        news_api_key = os.getenv("NEWS_API_KEY")
        if not news_api_key:
            print("Warning: NEWS_API_KEY not found in environment variables. Using fallback search method.")
            return search_recipients_fallback(topic, relevant_platforms)
            
        # Make request to News API
        news_api_url = f"https://newsapi.org/v2/everything"
        params = {
            'q': topic,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 20,
            'apiKey': news_api_key
        }
        
        response = requests.get(news_api_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Warning: News API request failed with status code {response.status_code}. Using fallback search method.")
            return search_recipients_fallback(topic, relevant_platforms)
            
        data = response.json()
        if data.get('status') != 'ok' or not data.get('articles'):
            print("Warning: No articles found from News API. Using fallback search method.")
            return search_recipients_fallback(topic, relevant_platforms)
            
        # Process articles and extract contact information
        for article in data['articles']:
            source_url = article.get('source', {}).get('url', '')
            if not source_url:
                continue
                
            # Extract domain from URL
            domain = source_url.split('//')[-1].split('/')[0]
            if domain not in relevant_platforms:
                continue
                
            try:
                # Find contact page
                contact_url = find_contact_page(source_url)
                if not contact_url:
                    continue
                    
                # Get contact page content
                contact_response = requests.get(contact_url, headers=headers, timeout=10)
                if contact_response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(contact_response.text, 'html.parser')
                
                # Extract emails and names
                emails = extract_email_from_text(contact_response.text)
                if not emails:
                    continue
                    
                # Look for names near email addresses
                for email in emails:
                    # Find the closest text node containing the email
                    email_node = soup.find(string=re.compile(email))
                    if not email_node:
                        continue
                        
                    # Look for name in surrounding text
                    name = None
                    parent = email_node.parent
                    if parent:
                        # Try to find name in parent element
                        name_text = parent.get_text().strip()
                        if name_text and name_text != email:
                            name = name_text
                        else:
                            # Try to find name in sibling elements
                            for sibling in parent.find_previous_siblings():
                                name_text = sibling.get_text().strip()
                                if name_text and name_text != email:
                                    name = name_text
                                    break
                    
                    if name:
                        # Extract role if available
                        role = ""
                        role_patterns = [
                            r'(Senior|Junior|Associate|Lead|Chief|Editor|Writer|Reporter|Journalist|Author)',
                            r'(Technology|Business|Science|Health|Politics|Sports|Arts|Culture)'
                        ]
                        
                        for pattern in role_patterns:
                            roles = re.findall(pattern, name)
                            if roles:
                                role = roles[0]
                                break
                        
                        # Determine region based on domain
                        region = "global"
                        if any(domain.endswith(tld) for tld in [".eu", ".de", ".fr", ".uk"]):
                            region = "europe"
                        elif any(domain.endswith(tld) for tld in [".cn", ".jp", ".kr", ".in", ".sg"]):
                            region = "asia"
                        elif any(domain.endswith(tld) for tld in [".br", ".ar", ".cl", ".es"]):
                            region = "latin_america"
                        
                        recipients.append({
                            'name': name,
                            'email': email,
                            'source': source_url,
                            'platform': domain,
                            'article_url': article.get('url', ''),
                            'region': region,
                            'role': role
                        })
                
            except Exception as e:
                print(f"Error processing {source_url}: {str(e)}")
                continue
                
        # If no recipients found through News API, try fallback method
        if not recipients:
            print("No recipients found through News API. Using fallback search method.")
            return search_recipients_fallback(topic, relevant_platforms)
            
        # Remove duplicates based on email and sort by relevance
        unique_recipients = []
        seen_emails = set()
        for recipient in recipients:
            if recipient['email'] not in seen_emails:
                seen_emails.add(recipient['email'])
                unique_recipients.append(recipient)
        
        # Sort recipients by relevance (region diversity, platform match, and role presence)
        unique_recipients.sort(key=lambda x: (
            x['platform'] != "unknown",  # Platform matches first
            bool(x['role']),  # Has role second
            x['name'] != "Unknown Author",  # Has name third
            x['region'] != "global"  # Regional diversity fourth
        ), reverse=True)
        
        return unique_recipients
        
    except Exception as e:
        print(f"Error in search_recipients: {str(e)}")
        return search_recipients_fallback(topic, relevant_platforms)

def search_recipients_fallback(topic: str, relevant_platforms: set) -> List[Dict[str, str]]:
    """
    Fallback function for recipient search when News API is unavailable.
    
    Args:
        topic (str): The topic to search for
        relevant_platforms (set): Set of relevant platform domains
        
    Returns:
        List[Dict[str, str]]: List of recipient dictionaries
    """
    recipients = []
    
    # Generate search queries
    search_queries = [
        f"{topic} journalist contact",
        f"{topic} editor contact",
        f"{topic} reporter contact",
        f"{topic} news writer contact",
        f"{topic} media contact",
        f"{topic} press contact",
        f"{topic} publication contact"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for query in search_queries:
        try:
            search_url = f"https://www.google.com/search?q={query}"
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all('a'):
                href = result.get('href', '')
                if any(platform in href.lower() for platform in relevant_platforms):
                    try:
                        contact_url = find_contact_page(href)
                        contact_response = requests.get(contact_url, headers=headers, timeout=10)
                        
                        emails = extract_email_from_text(contact_response.text)
                        names = []
                        for pattern in [
                            r'([A-Z][a-z]+ [A-Z][a-z]+)',
                            r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',
                            r'([A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+)'
                        ]:
                            names.extend(re.findall(pattern, contact_response.text))
                        
                        for email in emails:
                            if email and '@' in email:
                                name = "Unknown Author"
                                for n in names:
                                    if n.lower() in email.lower():
                                        name = n
                                        break
                                
                                role = ""
                                for pattern in [
                                    r'(Senior|Junior|Associate|Lead|Chief|Editor|Writer|Reporter|Journalist|Author)',
                                    r'(Technology|Business|Science|Health|Politics|Sports|Arts|Culture)'
                                ]:
                                    roles = re.findall(pattern, contact_response.text)
                                    if roles:
                                        role = roles[0]
                                        break
                                
                                region = "global"
                                if any(domain in href.lower() for domain in [".eu", ".de", ".fr", ".uk"]):
                                    region = "europe"
                                elif any(domain in href.lower() for domain in [".cn", ".jp", ".kr", ".in", ".sg"]):
                                    region = "asia"
                                elif any(domain in href.lower() for domain in [".br", ".ar", ".cl", ".es"]):
                                    region = "latin_america"
                                
                                recipients.append({
                                    "name": name,
                                    "email": email,
                                    "source": href,
                                    "role": role,
                                    "platform": next((p for p in relevant_platforms if p in href.lower()), "unknown"),
                                    "region": region
                                })
                        
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error processing {href}: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"Error searching for {query}: {str(e)}")
            continue
    
    # Remove duplicates and sort
    unique_recipients = []
    seen_emails = set()
    for recipient in recipients:
        if recipient['email'] not in seen_emails:
            seen_emails.add(recipient['email'])
            unique_recipients.append(recipient)
    
    unique_recipients.sort(key=lambda x: (
        x['platform'] != "unknown",
        bool(x['role']),
        x['name'] != "Unknown Author",
        x['region'] != "global"
    ), reverse=True)
    
    return unique_recipients

def send_email(recipients: List[Dict[str, str]], press_release: str) -> Dict[str, bool]:
    """
    Send the press release to all recipients via email.
    
    Args:
        recipients (List[Dict[str, str]]): List of recipient dictionaries with contact information
        press_release (str): The press release content to send
        
    Returns:
        Dict[str, bool]: Dictionary mapping email addresses to success status
        
    Raises:
        Exception: If there is an error sending emails
    """
    status = {}
    
    # Get email configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not all([smtp_username, smtp_password]):
        raise ValueError("SMTP credentials not configured")
    
    try:
        # Create SMTP connection
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            # Send email to each recipient
            for recipient in recipients:
                try:
                    # Create email message
                    msg = MIMEMultipart()
                    msg['From'] = smtp_username
                    msg['To'] = recipient['email']
                    msg['Subject'] = f"Press Release: {recipient.get('name', '')}"
                    
                    # Add press release content
                    msg.attach(MIMEText(press_release, 'plain'))
                    
                    # Send email
                    server.send_message(msg)
                    status[recipient['email']] = True
                    
                except Exception as e:
                    print(f"Failed to send email to {recipient['email']}: {str(e)}")
                    status[recipient['email']] = False
                    
        return status
        
    except Exception as e:
        # If SMTP connection fails, mark all emails as failed
        return {recipient['email']: False for recipient in recipients}

def post_to_social_media(press_release: str) -> Dict[str, bool]:
    """
    Post the press release to various social media platforms.
    
    Args:
        press_release (str): The press release content to post
        
    Returns:
        Dict[str, bool]: Dictionary mapping platform names to success status
        
    Raises:
        Exception: If there is an error posting to social media
    """
    status = {
        'twitter': False,
        'linkedin': False,
        'facebook': False
    }
    
    try:
        # Twitter
        try:
            twitter_api_key = os.getenv("TWITTER_API_KEY")
            twitter_api_secret = os.getenv("TWITTER_API_SECRET")
            twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
            
            if all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_token_secret]):
                auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret)
                auth.set_access_token(twitter_access_token, twitter_access_token_secret)
                api = tweepy.API(auth)
                
                # Split press release into tweets if needed
                tweets = [press_release[i:i+280] for i in range(0, len(press_release), 280)]
                for tweet in tweets:
                    api.update_status(tweet)
                status['twitter'] = True
                
        except Exception as e:
            print(f"Failed to post to Twitter: {str(e)}")
            
        # LinkedIn
        try:
            linkedin_username = os.getenv("LINKEDIN_USERNAME")
            linkedin_password = os.getenv("LINKEDIN_PASSWORD")
            
            if linkedin_username and linkedin_password:
                api = Linkedin(linkedin_username, linkedin_password)
                api.post(press_release)
                status['linkedin'] = True
                
        except Exception as e:
            print(f"Failed to post to LinkedIn: {str(e)}")
            
        # Facebook
        try:
            facebook_access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
            facebook_page_id = os.getenv("FACEBOOK_PAGE_ID")
            
            if facebook_access_token and facebook_page_id:
                graph = facebook.GraphAPI(facebook_access_token)
                graph.put_object(facebook_page_id, "feed", message=press_release)
                status['facebook'] = True
                
        except Exception as e:
            print(f"Failed to post to Facebook: {str(e)}")
            
        # If all platforms failed, raise an exception
        if not any(status.values()):
            raise Exception("Failed to post to any social media platform")
            
        return status
        
    except Exception as e:
        # If there's an error, return all platforms as failed
        return {
            'twitter': False,
            'linkedin': False,
            'facebook': False
        } 