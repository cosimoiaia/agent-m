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
from urllib.parse import quote
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client    
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.7"))


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

def search_recipients(topic: str, country: str = "it") -> List[Dict[str, str]]:
    """
    Search for relevant recipients based on the topic using News API and web search.
    
    Args:
        topic (str): The topic to search for
        country (str): The country code to focus the search on (default: "it" for Italy)
        
    Returns:
        List[Dict[str, str]]: List of recipients with their details
    """
    recipients = []
    
    try:
        # First try News API
        news_api_key = os.getenv("NEWS_API_KEY")
        if news_api_key:
            url = f"https://newsapi.org/v2/everything"
            params = {
                "q": topic,
                "language": "it",
                "sortBy": "relevancy",
                "apiKey": news_api_key
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    if article.get("author"):
                        recipients.append({
                            "name": article["author"],
                            "role": "Giornalista",
                            "email": "",  # News API doesn't provide email
                            "publication": article.get("source", {}).get("name", ""),
                            "focus": f"Articoli su {topic}"
                        })
        
        # If no results from News API or no API key, use web search
        if not recipients:
            # Search for Italian media contacts
            search_query = f"{topic} giornalisti italiani contatti"
            search_url = f"https://www.google.com/search?q={quote(search_query)}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Look for contact information in search results
                for result in soup.find_all("div", class_="g"):
                    title = result.find("h3")
                    if title:
                        title_text = title.get_text()
                        # Check if it's a media contact page
                        if any(keyword in title_text.lower() for keyword in ["giornalista", "redattore", "editore", "contatti", "rubrica"]):
                            snippet = result.find("div", class_="VwiC3b")
                            if snippet:
                                snippet_text = snippet.get_text()
                                # Extract potential contact information
                                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet_text)
                                if email_match:
                                    recipients.append({
                                        "name": title_text,
                                        "role": "Giornalista",
                                        "email": email_match.group(),
                                        "publication": "Da determinare",
                                        "focus": f"Articoli su {topic}"
                                    })
        
        # If still no results, try searching Italian media directories
        if not recipients:
            media_directories = [
                "https://www.odg.it/elenco-giornalisti/",
                "https://www.fnsi.it/elenco-giornalisti/"
            ]
            
            for directory in media_directories:
                try:
                    response = requests.get(directory, headers=headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        # Look for journalists in the directory
                        for journalist in soup.find_all("div", class_=["giornalista", "member", "contact"]):
                            name = journalist.find("h3") or journalist.find("strong")
                            if name:
                                recipients.append({
                                    "name": name.get_text().strip(),
                                    "role": "Giornalista",
                                    "email": "",  # Would need to visit individual pages
                                    "publication": "Da determinare",
                                    "focus": f"Articoli su {topic}"
                                })
                except Exception as e:
                    print(f"Error searching directory {directory}: {str(e)}")
        
    except Exception as e:
        print(f"Error searching for recipients: {str(e)}")
    
    return recipients

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

def extract_topics(text: str) -> str:
    """
    Extract key topics from the press release text.
    
    Args:
        text (str): The press release text
        
    Returns:
        str: Key topics extracted from the text
    """
    try:
        # Use Groq to extract key topics
        prompt = f"""Analizza il seguente comunicato stampa e estrai i topic principali:

{text}

Per favore fornisci i topic principali in italiano, separati da virgole.
Non includere testo aggiuntivo o spiegazioni."""

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        # Get the response content and clean it
        topics = response.choices[0].message.content.strip()
        return topics
        
    except Exception as e:
        print(f"Error extracting topics: {str(e)}")
        # Fallback: return the first sentence as topic
        return text.split('.')[0] if text else "" 