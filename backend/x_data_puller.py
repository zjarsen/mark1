#!/usr/bin/env python3
"""
X Data Puller v2 - TwitterAPI.io Integration with includeReplies=false
Fetches posts from TwitterAPI.io and saves to raw CSV files.
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

class TwitterAPIOPullerV2:
    """Handles TwitterAPI.io data pulling with includeReplies=false parameter."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io"
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        self.requests_made = 0
        self.cost_per_request = 0.00015  # $0.00015 per request according to docs
    
    def get_user_info(self, username: str) -> Dict:
        """Get user information by username."""
        url = f"{self.base_url}/twitter/user/by_username"
        params = {"username": username.replace("@", "")}  # Remove @ if present
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            self.requests_made += 1
            response.raise_for_status()
            data = response.json()
            return data.get('data', {}) if data else {}
        except Exception as e:
            logger.error(f"Failed to get user info for @{username}: {e}")
            return {}
        
    def get_user_tweets_by_username(self, username: str, start_date: str, end_date: str = None, 
                                   progress_callback=None, token: str = "Mantle") -> List[Dict]:
        """Fetch tweets directly by username using TwitterAPI.io with includeReplies=false."""
        # First get user info to get the correct user ID
        user_info = self.get_user_info(username)
        if not user_info or 'id' not in user_info:
            raise Exception(f"Could not find user info for @{username}")
        
        user_id = user_info['id']
        url = f"{self.base_url}/twitter/user/last_tweets"
        
        all_tweets = []
        page = 1
        cursor = None  # For proper pagination
        # No page limit - keep going until we reach start_date
        
        # Convert dates for filtering
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = None
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include end date
        
        date_range_str = f"from {start_date}" + (f" to {end_date}" if end_date else " onwards")
        logger.info(f"Fetching tweets for @{username} (ID: {user_id}) {date_range_str}")
        logger.info(f"Using includeReplies=false AND includeRetweets=false for API-level filtering")
        logger.info(f"Will pull all tweets until reaching start date (no page limit)")
        
        try:
            while True:  # No page limit
                params = {
                    "userName": username.replace("@", ""),
                    "includeReplies": "false",  # Filter out replies
                    "includeRetweets": "false"  # Filter out retweets
                }
                
                # Add cursor for proper pagination (skip page parameter)
                if cursor:
                    params["cursor"] = cursor
                elif page > 1:
                    # Fallback to page if cursor not available
                    params["page"] = page
                
                logger.info(f"Fetching page {page} with includeReplies=false AND includeRetweets=false...")
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                self.requests_made += 1
                
                if progress_callback:
                    progress_callback(len(all_tweets), self.requests_made, f"Page {page} (pulling to start date)")
                
                # Send progress update every few pages
                if page % 3 == 0:  # Every 3 pages
                    print(f"PROGRESS:{len(all_tweets)}:{self.requests_made}:Page {page} (pulling to start date)")
                
                response.raise_for_status()
                data = response.json()
                
                # Debug: log the response structure and pagination info
                logger.info(f"API Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                print(f"STATUS:API returned {list(data.keys()) if isinstance(data, dict) else type(data)}")
                
                # Check for pagination tokens
                if isinstance(data, dict):
                    has_next = data.get('has_next_page', False)
                    next_cursor = data.get('next_cursor', '')
                    print(f"STATUS:Pagination - has_next_page: {has_next}, next_cursor: {next_cursor[:20] if next_cursor else 'None'}...")
                    
                    # Update cursor for next iteration
                    if has_next and next_cursor:
                        cursor = next_cursor
                    elif not has_next:
                        print(f"STATUS:No more pages available (has_next_page: {has_next})")
                        break
                
                # Check if we got tweets - handle different response formats
                if not data:
                    logger.info(f"No data returned on page {page}")
                    print(f"STATUS:No data returned on page {page}")
                    break
                
                # Handle TwitterAPI.io response format
                if isinstance(data, dict) and 'data' in data:
                    data_obj = data['data']
                    if isinstance(data_obj, dict) and 'tweets' in data_obj:
                        tweets = data_obj['tweets']
                    else:
                        tweets = data_obj if isinstance(data_obj, list) else []
                elif isinstance(data, list):
                    tweets = data
                else:
                    logger.info(f"Unexpected response format: {data}")
                    break
                
                if not tweets:
                    logger.info(f"No tweets found on page {page}")
                    print(f"STATUS:No tweets found on page {page}")
                    break
                
                print(f"STATUS:Found {len(tweets)} tweets on page {page}, checking date range...")
                
                tweets_in_range = []
                
                # Filter tweets by date range and author
                for tweet in tweets:
                    try:
                        # Debug: check tweet structure
                        if not isinstance(tweet, dict):
                            logger.warning(f"Tweet is not a dict: {type(tweet)} - {tweet}")
                            continue
                        
                        # Filter to only include tweets from target account (double-check)
                        author = tweet.get('author', {})
                        author_username = author.get('userName', '')
                        if author_username not in ['Mantle_Official', '0xMantle']:
                            logger.debug(f"Skipping tweet from different user: {author_username}")
                            continue  # Skip tweets from other users
                        
                        # Skip retweets - even with includeReplies=false, we might get RTs
                        tweet_text = tweet.get('text', '')
                        if tweet_text.startswith('RT @'):
                            logger.debug("Skipping retweet")
                            continue  # Skip retweets
                            
                        # Parse tweet creation time - handle different date formats
                        created_at = tweet.get('createdAt') or tweet.get('created_at')
                        if not created_at:
                            logger.warning(f"No created_at field in tweet: {list(tweet.keys())}")
                            continue
                            
                        # Try different date formats
                        try:
                            # TwitterAPI.io format: "Mon Feb 03 15:06:15 +0000 2025"
                            tweet_date = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                        except ValueError:
                            try:
                                # ISO format: "2025-02-03T15:06:15.000Z"
                                tweet_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                            except ValueError:
                                try:
                                    # ISO format without microseconds: "2025-02-03T15:06:15Z"
                                    tweet_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                                except ValueError:
                                    logger.warning(f"Could not parse date: {created_at}")
                                    continue
                        
                        # Convert to naive datetime for comparison (remove timezone info)
                        tweet_date = tweet_date.replace(tzinfo=None)
                        
                        # Debug: Show tweet dates for first few tweets
                        if len(all_tweets) < 5:  # Only log first 5 tweets
                            print(f"STATUS:Tweet date: {tweet_date} - {tweet_text[:50]}...")
                        
                        # Update current date being processed (for frontend)
                        if len(tweets_in_range) == 0:  # First tweet in this batch
                            current_date_str = tweet_date.strftime("%Y-%m-%d %H:%M")
                            print(f"CURRENT_DATE:{current_date_str}")
                        
                        # Check if tweet is in our date range
                        if end_datetime:
                            # Have both start and end date
                            if start_datetime <= tweet_date <= end_datetime:
                                tweets_in_range.append(tweet)
                                logger.debug(f"Added tweet from {tweet_date}: {tweet_text[:50]}...")
                                print(f"STATUS:✅ MATCH! Tweet from {tweet_date}")
                            elif tweet_date < start_datetime:
                                # If we've gone past our start date, we can stop
                                logger.info(f"Reached tweets before start date. Stopping at page {page}")
                                print(f"STATUS:Reached tweets before start date ({tweet_date}). Stopping.")
                                all_tweets.extend(tweets_in_range)
                                return all_tweets
                            else:
                                # Tweet is after our end date
                                if len(all_tweets) < 3:  # Only log for first few
                                    print(f"STATUS:Tweet too recent: {tweet_date} (after {end_datetime})")
                        else:
                            # Only have start date - include all tweets from start_date onwards
                            if tweet_date >= start_datetime:
                                tweets_in_range.append(tweet)
                                logger.debug(f"Added tweet from {tweet_date}: {tweet_text[:50]}...")
                                print(f"STATUS:✅ MATCH! Tweet from {tweet_date}")
                            else:
                                # If we've gone past our start date, we can stop
                                logger.info(f"Reached tweets before start date. Stopping at page {page}")
                                print(f"STATUS:Reached tweets before start date ({tweet_date}). Stopping.")
                                all_tweets.extend(tweets_in_range)
                                return all_tweets
                            
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing tweet date: {e}")
                        continue
                
                all_tweets.extend(tweets_in_range)
                logger.info(f"Found {len(tweets_in_range)} tweets in date range from page {page}. Total: {len(all_tweets)}")
                
                # Save to CSV immediately after each page (real-time saving)
                if tweets_in_range:
                    self.save_page_to_csv(tweets_in_range, page, start_date, token)
                
                # Don't break on fewer tweets - rely on API's has_next_page flag instead
                # Some pages may have fewer than 20 tweets due to filtering
                if len(tweets) < 20:
                    logger.info(f"Page {page} has {len(tweets)} tweets (may be filtered or partial page)")
                    # Continue anyway - let the API tell us when to stop
                
                page += 1
                
                # Small delay to be respectful
                time.sleep(0.1)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response.status_code == 429:
                logger.error("Rate limited by TwitterAPI.io")
            raise e
        
        logger.info(f"Successfully fetched {len(all_tweets)} tweets with {self.requests_made} API calls")
        logger.info(f"Estimated cost: ${self.requests_made * self.cost_per_request:.4f}")
        return all_tweets
    
    def normalize_tweet_data(self, tweet: Dict) -> Dict:
        """Normalize TwitterAPI.io tweet data to consistent format."""
        try:
            # TwitterAPI.io might have different field names, normalize them
            normalized = {
                'id': tweet.get('id') or tweet.get('tweet_id'),
                'created_at': tweet.get('createdAt') or tweet.get('created_at'),
                'text': tweet.get('text') or tweet.get('full_text'),
                'public_metrics': {
                    'like_count': tweet.get('likeCount', 0) or tweet.get('favorite_count', 0) or tweet.get('like_count', 0),
                    'retweet_count': tweet.get('retweetCount', 0) or tweet.get('retweet_count', 0),
                    'reply_count': tweet.get('replyCount', 0) or tweet.get('reply_count', 0),
                    'quote_count': tweet.get('quoteCount', 0) or tweet.get('quote_count', 0)
                },
                'author_id': tweet.get('user_id') or tweet.get('author_id')
            }
            return normalized
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
        
        # Deduplicate tweets by ID to prevent duplicates
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
                # Normalize tweet data first
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
    
    def save_page_to_csv(self, tweets: List[Dict], page_num: int, start_date: str = None, token: str = "Mantle") -> None:
        """Save tweets from a single page to CSV immediately (real-time saving with deduplication)."""
        if not tweets:
            return
            
        # Ensure raw directory exists
        os.makedirs('../data/raw', exist_ok=True)
        
        # Generate filename using target date format: raw-[token]-yyyy-mm-dd
        target_date = start_date if start_date else datetime.now().strftime("%Y-%m-%d")
        filename = f"raw-{token}-{target_date}.csv"
        filepath = os.path.join('../data/raw', filename)
        
        # Read existing tweet IDs to prevent duplicates
        existing_ids = set()
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        existing_ids.add(row['tweet_id'])
            except Exception as e:
                logger.warning(f"Could not read existing CSV for deduplication: {e}")
        
        # Filter out duplicate tweets
        new_tweets = []
        for tweet in tweets:
            tweet_id = tweet.get('id', '')
            if tweet_id and tweet_id not in existing_ids:
                new_tweets.append(tweet)
                existing_ids.add(tweet_id)
        
        if not new_tweets:
            print(f"STATUS:⚠️  Page {page_num}: All {len(tweets)} tweets already exist (skipping duplicates)")
            return
        
        # Check if file exists to determine if we need header
        file_exists = os.path.exists(filepath)
        
        fieldnames = [
            'tweet_id', 'created_at', 'text', 'like_count', 'retweet_count', 
            'reply_count', 'quote_count', 'author_id'
        ]
        
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
                print(f"STATUS:📄 Created real-time CSV: {filename}")
            
            for tweet in new_tweets:
                writer.writerow({
                    'tweet_id': tweet.get('id', ''),
                    'created_at': tweet.get('createdAt', ''),
                    'text': tweet.get('text', '').replace('\n', ' ').replace('\r', ' '),
                    'like_count': tweet.get('like_count', 0),
                    'retweet_count': tweet.get('retweet_count', 0),
                    'reply_count': tweet.get('reply_count', 0),
                    'quote_count': tweet.get('quote_count', 0),
                    'author_id': tweet.get('author', {}).get('id', '')
                })
        
        print(f"STATUS:💾 Saved page {page_num} ({len(new_tweets)}/{len(tweets)} new tweets) to {filename}")
        logger.info(f"Real-time saved page {page_num} with {len(new_tweets)} new tweets to {filepath} (filtered {len(tweets)-len(new_tweets)} duplicates)")
    
    def detect_and_save_threads(self, csv_filepath: str) -> None:
        """Detect threads and save enhanced CSV with thread information."""
        try:
            from thread_detector import TwitterThreadDetector
            
            detector = TwitterThreadDetector(time_window_minutes=2)
            results = detector.detect_threads(csv_filepath)
            
            # Create thread-enhanced CSV
            thread_filename = csv_filepath.replace('.csv', '-with-threads.csv')
            
            with open(thread_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'tweet_id', 'created_at', 'text', 'like_count', 'retweet_count', 
                    'reply_count', 'quote_count', 'author_id', 'thread_id', 'thread_position', 'is_thread'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Create lookup for thread membership
                tweet_to_thread = {}
                for thread in results['threads']:
                    for i, tweet in enumerate(thread['original_tweets'], 1):
                        tweet_to_thread[tweet['id']] = {
                            'thread_id': thread['thread_id'],
                            'position': f"{i}/{len(thread['original_tweets'])}",
                            'is_thread': True
                        }
                
                # Read original CSV and enhance with thread info
                with open(csv_filepath, 'r', encoding='utf-8') as original_file:
                    reader = csv.DictReader(original_file)
                    for row in reader:
                        tweet_id = row['tweet_id']
                        thread_info = tweet_to_thread.get(tweet_id, {
                            'thread_id': '',
                            'position': '',
                            'is_thread': False
                        })
                        
                        enhanced_row = {**row, **{
                            'thread_id': thread_info['thread_id'],
                            'thread_position': thread_info['position'],
                            'is_thread': thread_info['is_thread']
                        }}
                        writer.writerow(enhanced_row)
            
            print(f"STATUS:🧵 Thread analysis complete: {len(results['threads'])} threads detected")
            print(f"STATUS:📄 Enhanced CSV saved: {thread_filename}")
            
        except Exception as e:
            logger.warning(f"Thread detection failed: {e}")
            print(f"STATUS:⚠️ Thread detection failed: {e}")

def main():
    """Main execution function."""
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python x_data_puller.py <start_date> [<end_date>] <token>")
        print("Example: python x_data_puller.py 2025-08-03 mantle")
        print("Example: python x_data_puller.py 2025-01-01 2025-01-31 mantle")
        sys.exit(1)
    
    if len(sys.argv) == 3:
        # Only start_date and token provided
        start_date = sys.argv[1]
        end_date = None
        token = sys.argv[2]
    else:
        # All three provided
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        token = sys.argv[3]
    
    # Get TwitterAPI.io API key from environment
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    if not api_key:
        logger.error("TWITTERAPI_IO_KEY environment variable not set")
        print("ERROR: TWITTERAPI_IO_KEY not found")
        print("Get your API key from: https://twitterapi.io/dashboard")
        sys.exit(1)
    
    # Token to username mapping
    token_usernames = {
        'mantle': 'Mantle_Official'
    }
    
    if token not in token_usernames:
        logger.error(f"Unknown token: {token}")
        print(f"ERROR: Unknown token {token}")
        sys.exit(1)
    
    username = token_usernames[token]
    
    # Initialize puller
    puller = TwitterAPIOPullerV2(api_key)
    
    # Progress callback for real-time updates
    def progress_callback(posts_count, api_calls, status):
        print(f"PROGRESS:{posts_count}:{api_calls}:{status}")
        sys.stdout.flush()
    
    try:
        print("STATUS:Starting data pull with TwitterAPI.io (includeReplies=false)...")
        date_range_str = f"from {start_date}" + (f" to {end_date}" if end_date else " onwards")
        print(f"STATUS:Target: @{username} {date_range_str}")
        
        # Debug: Show parsed dates
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            print(f"STATUS:Parsed date range: {start_datetime} to {end_datetime}")
        else:
            print(f"STATUS:Parsed start date: {start_datetime} (no end date - pull all recent tweets)")
        print(f"STATUS:Today is: {datetime.now()}")
        
        # Fetch tweets directly by username
        print("STATUS:Fetching tweets with API-level filtering...")
        tweets = puller.get_user_tweets_by_username(username, start_date, end_date, progress_callback, token)
        
        if not tweets:
            print("ERROR:No tweets found in date range")
            print(f"INFO:Tried to fetch tweets for @{username} between {start_date} and {end_date}")
            print("INFO:This might be normal if the account didn't post during this period")
            sys.exit(1)
        
        # Get the realtime filename that was created during the process
        realtime_filename = f"raw-{token}-{start_date}.csv"
        realtime_filepath = os.path.join('../data/raw', realtime_filename)
        
        # Calculate final cost
        total_cost = puller.requests_made * puller.cost_per_request
        
        print(f"SUCCESS:{len(tweets)}:{realtime_filepath}")
        print(f"COST:${total_cost:.4f}")
        print(f"REQUESTS:{puller.requests_made}")
        
    except Exception as e:
        logger.error(f"Data pull failed: {e}")
        print(f"ERROR:{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()