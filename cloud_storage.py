"""
Cloud Storage Module for Press Release Distribution Agent

This module handles all storage operations using AWS S3 with local fallback.
It provides functionality to store and retrieve press releases and email details
in a structured JSON format with proper metadata.

The storage is organized into two main categories:
- press_releases/: Contains generated press releases
- emails/: Contains email distribution details and recipient information

If cloud storage operations fail, the module automatically falls back to local storage
in a 'local_storage' directory within the project.
"""

import boto3
import json
from datetime import datetime
import os
from typing import Dict, Any, Optional
import logging
import shutil
from pathlib import Path

# Configure logging
logger = logging.getLogger('press_release_agent.cloud_storage')

class CloudStorage:
    """
    Handles all storage operations using AWS S3 with local fallback.
    
    This class provides methods to store and retrieve press releases and email details
    in a structured format. It uses AWS S3 as the primary storage backend and falls back
    to local storage if cloud operations fail.
    
    Attributes:
        s3_client: Boto3 S3 client instance
        bucket_name: Name of the S3 bucket to use
        use_cloud: Boolean indicating if cloud storage is available
        local_storage_path: Path to the local storage directory
    """
    
    def __init__(self):
        """
        Initialize the CloudStorage class with AWS S3 credentials and local fallback.
        
        Creates an S3 client using credentials from environment variables:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION
        - S3_BUCKET_NAME
        
        Also sets up local storage directory for fallback.
        """
        logger.info("Initializing CloudStorage with AWS S3 and local fallback")
        
        # Set up local storage path
        self.local_storage_path = Path("local_storage")
        self.local_storage_path.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of content
        (self.local_storage_path / "press_releases").mkdir(exist_ok=True)
        (self.local_storage_path / "emails").mkdir(exist_ok=True)
        (self.local_storage_path / "logs").mkdir(exist_ok=True)
        
        # Try to initialize S3 client
        self.use_cloud = False
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
            self.bucket_name = os.getenv('S3_BUCKET_NAME')
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.use_cloud = True
            logger.info(f"Successfully initialized S3 client with bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client, falling back to local storage: {str(e)}")
            self.use_cloud = False

    def _store_local(self, content_type: str, topic: str, content: bytes) -> str:
        """
        Store content locally as a fallback.
        
        Args:
            content_type (str): Type of content ('press_releases' or 'emails')
            topic (str): The topic of the content
            content (bytes): The content to store
            
        Returns:
            str: The local file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{topic}_{timestamp}.json"
        filepath = self.local_storage_path / content_type / filename
        
        try:
            with open(filepath, 'wb') as f:
                f.write(content)
            logger.info(f"Successfully stored {content_type} locally at: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to store {content_type} locally: {str(e)}")
            return ""

    def store_press_release(self, topic: str, content: bytes) -> str:
        """
        Store a press release in S3 with local fallback.
        
        Args:
            topic (str): The topic of the press release
            content (bytes): The press release content in JSON format
            
        Returns:
            str: The storage URL/path of the stored press release
        """
        try:
            if self.use_cloud:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                key = f"press_releases/{topic}_{timestamp}.json"
                
                logger.info(f"Storing press release in cloud for topic: {topic}")
                
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
            else:
                return self._store_local("press_releases", topic, content)
                
        except Exception as e:
            logger.warning(f"Failed to store press release in cloud, falling back to local: {str(e)}")
            return self._store_local("press_releases", topic, content)

    def store_email(self, topic: str, content: bytes) -> str:
        """
        Store email distribution details in S3 with local fallback.
        
        Args:
            topic (str): The topic of the press release
            content (bytes): The email details in JSON format
            
        Returns:
            str: The storage URL/path of the stored email details
        """
        try:
            if self.use_cloud:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                key = f"emails/{topic}_{timestamp}.json"
                
                logger.info(f"Storing email details in cloud for topic: {topic}")
                
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
            else:
                return self._store_local("emails", topic, content)
                
        except Exception as e:
            logger.warning(f"Failed to store email details in cloud, falling back to local: {str(e)}")
            return self._store_local("emails", topic, content)

    def upload_logs(self, log_file: str) -> str:
        """
        Upload application logs to S3 with local fallback.
        
        Args:
            log_file (str): Path to the log file to upload
            
        Returns:
            str: The storage URL/path of the uploaded log file
        """
        try:
            if not os.path.exists(log_file):
                logger.error(f"Log file not found: {log_file}")
                return ""
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.use_cloud:
                key = f"logs/app_log_{timestamp}.log"
                
                logger.info(f"Uploading log file to cloud: {log_file}")
                
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
            else:
                # Store locally
                dest_path = self.local_storage_path / "logs" / f"app_log_{timestamp}.log"
                shutil.copy2(log_file, dest_path)
                logger.info(f"Successfully stored logs locally at: {dest_path}")
                return str(dest_path)
                    
        except Exception as e:
            logger.error(f"Failed to upload logs: {str(e)}")
            return ""

    def get_press_release(self, storage_path: str) -> Dict[str, Any]:
        """
        Retrieve a press release from storage.
        
        Args:
            storage_path (str): The storage URL/path of the press release
            
        Returns:
            Dict[str, Any]: The press release data as a dictionary
        """
        try:
            if storage_path.startswith("s3://"):
                key = storage_path.replace(f"s3://{self.bucket_name}/", "")
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                return json.loads(response['Body'].read().decode('utf-8'))
            else:
                # Local file
                with open(storage_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to retrieve press release: {str(e)}")
            return {}

    def get_email(self, storage_path: str) -> Dict[str, Any]:
        """
        Retrieve email distribution details from storage.
        
        Args:
            storage_path (str): The storage URL/path of the email details
            
        Returns:
            Dict[str, Any]: The email details as a dictionary
        """
        try:
            if storage_path.startswith("s3://"):
                key = storage_path.replace(f"s3://{self.bucket_name}/", "")
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                return json.loads(response['Body'].read().decode('utf-8'))
            else:
                # Local file
                with open(storage_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to retrieve email details: {str(e)}")
            return {} 