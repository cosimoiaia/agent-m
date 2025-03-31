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
import logging
import shutil

# Configure logging
logger = logging.getLogger('press_release_agent.cloud_storage')

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
        logger.info("Initializing CloudStorage with AWS S3")
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
            self.bucket_name = os.getenv('S3_BUCKET_NAME')
            logger.info(f"Successfully initialized S3 client with bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def store_press_release(self, topic: str, content: bytes) -> str:
        """
        Store a press release in S3 with proper metadata.
        
        Args:
            topic (str): The topic of the press release
            content (bytes): The press release content in JSON format
            
        Returns:
            str: The S3 URL of the stored press release
            
        Raises:
            Exception: If there is an error storing the press release
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"press_releases/{topic}_{timestamp}.json"
            
            logger.info(f"Storing press release for topic: {topic}")
            logger.debug(f"Content length: {len(content)} bytes")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType='application/json',
                Metadata={
                    'topic': topic,
                    'timestamp': timestamp,
                    'type': 'press_release'
                }
            )
            
            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Successfully stored press release at: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to store press release: {str(e)}")
            raise

    def store_email(self, topic: str, content: bytes) -> str:
        """
        Store email distribution details in S3 with proper metadata.
        
        Args:
            topic (str): The topic of the press release
            content (bytes): The email details in JSON format
            
        Returns:
            str: The S3 URL of the stored email details
            
        Raises:
            Exception: If there is an error storing the email details
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"emails/{topic}_{timestamp}.json"
            
            logger.info(f"Storing email details for topic: {topic}")
            logger.debug(f"Content length: {len(content)} bytes")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType='application/json',
                Metadata={
                    'topic': topic,
                    'timestamp': timestamp,
                    'type': 'email'
                }
            )
            
            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Successfully stored email details at: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to store email details: {str(e)}")
            raise

    def upload_logs(self, log_file: str) -> str:
        """
        Upload application logs to S3.
        
        Args:
            log_file (str): Path to the log file to upload
            
        Returns:
            str: The S3 URL of the uploaded log file
            
        Raises:
            Exception: If there is an error uploading the logs
        """
        try:
            if not os.path.exists(log_file):
                logger.error(f"Log file not found: {log_file}")
                return ""
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"logs/app_log_{timestamp}.log"
            
            logger.info(f"Uploading log file: {log_file}")
            
            # Create a copy of the log file with timestamp
            temp_log = f"{log_file}.{timestamp}"
            shutil.copy2(log_file, temp_log)
            
            try:
                with open(temp_log, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=key,
                        Body=f,
                        ContentType='text/plain',
                        Metadata={
                            'timestamp': timestamp,
                            'type': 'application_log'
                        }
                    )
                
                url = f"s3://{self.bucket_name}/{key}"
                logger.info(f"Successfully uploaded logs to: {url}")
                return url
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_log):
                    os.remove(temp_log)
                    
        except Exception as e:
            logger.error(f"Failed to upload logs: {str(e)}")
            return ""

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