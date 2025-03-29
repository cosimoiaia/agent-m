"""
Cloud Storage Module for Press Release Distribution Agent

This module handles all cloud storage operations using AWS S3.
It provides functionality to store and retrieve press releases and email details
in a structured JSON format with proper metadata.

The storage is organized into two main categories:
- press_releases/: Contains generated press releases
- emails/: Contains email distribution details and recipient information
"""

import boto3
import json
from datetime import datetime
import os
from typing import Dict, Any

class CloudStorage:
    """
    Handles all cloud storage operations using AWS S3.
    
    This class provides methods to store and retrieve press releases and email details
    in a structured format. It uses AWS S3 as the storage backend and maintains
    proper organization of files with timestamps and metadata.
    
    Attributes:
        s3_client: Boto3 S3 client instance
        bucket_name: Name of the S3 bucket to use
    """
    
    def __init__(self):
        """
        Initialize the CloudStorage class with AWS S3 credentials.
        
        Creates an S3 client using credentials from environment variables:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION
        - S3_BUCKET_NAME
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')

    def store_press_release(self, topic: str, press_release: str) -> str:
        """
        Store a press release in S3 with metadata.
        
        Args:
            topic (str): The topic of the press release
            press_release (str): The content of the press release
            
        Returns:
            str: The S3 URL where the press release is stored
            
        The stored JSON structure includes:
        {
            "topic": str,
            "content": str,
            "timestamp": str,
            "type": "press_release"
        }
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"press_releases/{timestamp}_{topic.replace(' ', '_')}.json"
        
        data = {
            "topic": topic,
            "content": press_release,
            "timestamp": timestamp,
            "type": "press_release"
        }
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        
        return f"s3://{self.bucket_name}/{filename}"

    def store_email(self, topic: str, press_release: str, recipients: list, email_status: Dict[str, Any]) -> str:
        """
        Store email distribution details in S3.
        
        Args:
            topic (str): The topic of the press release
            press_release (str): The content of the press release
            recipients (list): List of recipient dictionaries
            email_status (Dict[str, Any]): Status of email distribution
            
        Returns:
            str: The S3 URL where the email details are stored
            
        The stored JSON structure includes:
        {
            "topic": str,
            "press_release": str,
            "recipients": list,
            "email_status": dict,
            "timestamp": str,
            "type": "email"
        }
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"emails/{timestamp}_{topic.replace(' ', '_')}.json"
        
        data = {
            "topic": topic,
            "press_release": press_release,
            "recipients": recipients,
            "email_status": email_status,
            "timestamp": timestamp,
            "type": "email"
        }
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=filename,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        
        return f"s3://{self.bucket_name}/{filename}"

    def get_press_release(self, s3_url: str) -> Dict[str, Any]:
        """
        Retrieve a press release from S3.
        
        Args:
            s3_url (str): The S3 URL of the press release
            
        Returns:
            Dict[str, Any]: The press release data as a dictionary
            
        Raises:
            Exception: If the press release cannot be retrieved or parsed
        """
        key = s3_url.replace(f"s3://{self.bucket_name}/", "")
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))

    def get_email(self, s3_url: str) -> Dict[str, Any]:
        """
        Retrieve email distribution details from S3.
        
        Args:
            s3_url (str): The S3 URL of the email details
            
        Returns:
            Dict[str, Any]: The email details as a dictionary
            
        Raises:
            Exception: If the email details cannot be retrieved or parsed
        """
        key = s3_url.replace(f"s3://{self.bucket_name}/", "")
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return json.loads(response['Body'].read().decode('utf-8')) 