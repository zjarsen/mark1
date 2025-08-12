#!/usr/bin/env python3
"""
X Official API Data Puller
Fetches posts from X.com official API v2 and saves to raw CSV files.
"""

import os
import csv
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XOfficialAPIPuller:
    """Handles X.com official API v2 data pulling with Bearer Token authentication."""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        self.requests_made = 0
        # X API v2 pricing is complex, but Basic plan allows 10K tweets/month for $100
        self.cost_per_request = 0.01  # Rough estimate
    
    def get_user_by_username(self, username: str) -> Dict:
        """Get user information by username."""
        url = f"{self.base_url}/users/by/username/{username.replace('@', '')}"
        params = {
            "user.fields": "id,name,username,created_at,description,public_metrics,verified"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self.requests_made += 1
            response.raise_for_status()
            data = response.json()
            return data.get('data', {})
        except Exception as e:
            logger.error(f"Failed to get user info for @{username}: {e}")
            return {}
    
    def get_user_tweets(self, user_id: str, start_date: str, end_date: str, 
                       progress_callback=None) -> List[Dict]:
        """Fetch tweets for a user with proper filtering using X API v2."""
        url = f"{self.base_url}/users/{user_id}/tweets"
        
        all_tweets = []
        next_token = None
        max_results = 100  # X API v2 max per request
        page = 1
        max_pages = 10  # Reasonable limit
        
        # Convert dates to RFC3339 format for X API v2
        start_time = f"{start_date}T00:00:00.000Z"
        end_time = f"{end_date}T23:59:59.000Z"
        
        logger.info(f"Fetching tweets for user {user_id} from {start_date} to {end_date}")
        logger.info(f"Estimated cost: ~${self.cost_per_request * max_pages:.2f} for {max_pages} pages")
        
        try:
            while page <= max_pages:
                params = {
                    "max_results": max_results,
                    "start_time": start_time,
                    "end_time": end_time,
                    "exclude": "retweets,replies",  # Official API filtering!
                    "tweet.fields": "id,text,created_at,public_metrics,author_id,context_annotations,entities",
                    "expansions": "author_id"
                }
                
                if next_token:
                    params["pagination_token"] = next_token
                
                logger.info(f"Fetching page {page}...")
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                self.requests_made += 1
                
                if progress_callback:
                    progress_callback(len(all_tweets), self.requests_made, f"Page {page}/{max_pages}")
                
                response.raise_for_status()
                data = response.json()
                
                # Handle rate limiting
                if response.status_code == 429:
                    reset_time = int(response.headers.get('x-rate-limit-reset', 0))
                    sleep_time = max(reset_time - int(time.time()), 60)
                    logger.warning(f"Rate limited. Waiting {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                
                # Get tweets from response
                tweets = data.get('data', [])
                if not tweets:
                    logger.info(f"No more tweets found on page {page}")
                    break
                
                all_tweets.extend(tweets)
                logger.info(f"Found {len(tweets)} tweets on page {page}. Total: {len(all_tweets)}")
                
                # Check for next page
                meta = data.get('meta', {})
                next_token = meta.get('next_token')
                if not next_token:
                    logger.info("No more pages available")
                    break
                
                page += 1
                
                # Rate limiting: X API v2 allows 75 requests per 15 minutes
                time.sleep(1)  # Be respectful
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise e
        
        logger.info(f"Successfully fetched {len(all_tweets)} tweets with {self.requests_made} API calls")
        logger.info(f"Estimated cost: ${self.requests_made * self.cost_per_request:.2f}")
        return all_tweets
    
    def normalize_tweet_data(self, tweet: Dict) -> Dict:
        """Normalize X API v2 tweet data to consistent format."""
        try:
            # X API v2 already has clean structure
            return {
                'id': tweet.get('id'),
                'created_at': tweet.get('created_at'),
                'text': tweet.get('text'),
                'public_metrics': tweet.get('public_metrics', {}),
                'author_id': tweet.get('author_id')
            }
        except Exception as e:
            logger.warning(f"Error normalizing tweet data: {e}")
            return tweet
    
    def save_to_csv(self, tweets: List[Dict], filename: str) -> str:
        """Save tweets to CSV file in raw folder."""
        # Ensure raw directory exists
        os.makedirs('../data/raw', exist_ok=True)
        
        filepath = os.path.join('../data/raw', filename)
        
        fieldnames = [
            'tweet_id', 'created_at', 'text', 'like_count', 'retweet_count', 
            'reply_count', 'quote_count', 'author_id'
        ]
        
        # Deduplicate tweets by ID
        seen_ids = set()
        unique_tweets = []
        for tweet in tweets:
            tweet_id = tweet.get('id')
            if tweet_id and tweet_id not in seen_ids:
                seen_ids.add(tweet_id)
                unique_tweets.append(tweet)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for tweet in unique_tweets:
                normalized_tweet = self.normalize_tweet_data(tweet)
                metrics = normalized_tweet.get('public_metrics', {})
                
                row = {
                    'tweet_id': normalized_tweet.get('id', ''),
                    'created_at': normalized_tweet.get('created_at', ''),
                    'text': normalized_tweet.get('text', ''),
                    'like_count': metrics.get('like_count', 0),
                    'retweet_count': metrics.get('retweet_count', 0),
                    'reply_count': metrics.get('reply_count', 0),
                    'quote_count': metrics.get('quote_count', 0),
                    'author_id': normalized_tweet.get('author_id', '')
                }
                writer.writerow(row)
        
        logger.info(f"Saved {len(unique_tweets)} unique tweets to {filepath} (original: {len(tweets)})")
        return filepath

def main():
    """Main execution function."""
    if len(sys.argv) != 4:
        print("Usage: python x_official_data_puller.py <start_date> <end_date> <username>")
        print("Example: python x_official_data_puller.py 2024-01-01 2024-12-31 Mantle_Official")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    username = sys.argv[3]
    
    # Get Bearer Token from environment
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        logger.error("TWITTER_BEARER_TOKEN environment variable not set")
        print("ERROR: TWITTER_BEARER_TOKEN not found")
        print("Get your Bearer Token from: https://developer.twitter.com/en/portal/dashboard")
        print("Then add it to your .env file: TWITTER_BEARER_TOKEN=your_token_here")
        sys.exit(1)
    
    # Initialize puller
    puller = XOfficialAPIPuller(bearer_token)
    
    # Progress callback for real-time updates
    def progress_callback(tweets_count, api_calls, status):
        print(f"PROGRESS:{tweets_count}:{api_calls}:{status}")
        sys.stdout.flush()
    
    try:
        print("STATUS:Starting data pull with X.com Official API v2...")
        print(f"STATUS:Target: @{username} from {start_date} to {end_date}")
        
        # Get user info
        print("STATUS:Getting user information...")
        user_info = puller.get_user_by_username(username)
        if not user_info or 'id' not in user_info:
            print(f"ERROR:Could not find user @{username}")
            sys.exit(1)
        
        user_id = user_info['id']
        print(f"STATUS:Found user @{username} (ID: {user_id})")
        
        # Fetch tweets
        print("STATUS:Fetching tweets...")
        tweets = puller.get_user_tweets(user_id, start_date, end_date, progress_callback)
        
        if not tweets:
            print("ERROR:No tweets found in date range")
            print(f"INFO:Tried to fetch tweets for @{username} between {start_date} and {end_date}")
            sys.exit(1)
        
        # Generate filename
        filename = f"raw-{username}-{start_date}-{end_date}.csv"
        
        # Save to CSV
        print("STATUS:Saving to CSV...")
        filepath = puller.save_to_csv(tweets, filename)
        
        # Calculate final cost
        total_cost = puller.requests_made * puller.cost_per_request
        
        print(f"SUCCESS:{len(tweets)}:{filepath}")
        print(f"COST:${total_cost:.2f}")
        print(f"REQUESTS:{puller.requests_made}")
        
    except Exception as e:
        logger.error(f"Data pull failed: {e}")
        print(f"ERROR:{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()