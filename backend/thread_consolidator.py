#!/usr/bin/env python3
"""
Thread Consolidator
Processes raw CSV files to consolidate tweet threads into single posts.
Outputs simplified CSV with 3 columns: tweet_id, timestamp, text
"""

import os
import csv
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThreadConsolidator:
    """Consolidates tweet threads into single posts with simplified output."""
    
    def __init__(self, time_window_minutes: int = 2):
        self.time_window_minutes = time_window_minutes
        
    def process_csv(self, input_filepath: str, output_filename: str = None) -> str:
        """Process a raw CSV file and consolidate threads."""
        
        # Read tweets from CSV
        tweets = self._read_tweets_from_csv(input_filepath)
        if not tweets:
            raise Exception("No tweets found in CSV file")
        
        logger.info(f"Loaded {len(tweets)} tweets from {input_filepath}")
        print(f"STATUS:Loaded {len(tweets)} tweets")
        
        # Detect threads
        threads, standalone_tweets = self._detect_threads(tweets)
        
        logger.info(f"Detected {len(threads)} threads and {len(standalone_tweets)} standalone tweets")
        print(f"STATUS:Detected {len(threads)} threads and {len(standalone_tweets)} standalone tweets")
        
        # Create consolidated posts
        consolidated_posts = self._create_consolidated_posts(threads, standalone_tweets)
        
        logger.info(f"Consolidated to {len(consolidated_posts)} total posts")
        print(f"STATUS:Consolidated to {len(consolidated_posts)} total posts")
        
        # Generate output filename if not provided
        if not output_filename:
            base_name = os.path.basename(input_filepath)
            # Replace "raw" with "processed" in the filename
            if base_name.startswith('raw-'):
                output_filename = base_name.replace('raw-', 'processed-', 1)
            else:
                # Fallback for files that don't start with "raw-"
                output_filename = f"processed-{base_name}"
        
        # Save to processed folder
        output_filepath = self._save_consolidated_csv(consolidated_posts, output_filename)
        
        return output_filepath
    
    def _read_tweets_from_csv(self, filepath: str) -> List[Dict]:
        """Read tweets from CSV file."""
        tweets = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Parse the tweet data
                    tweet = {
                        'id': row.get('tweet_id', ''),
                        'created_at': row.get('created_at', ''),
                        'text': row.get('text', '').strip(),
                        'timestamp': self._parse_timestamp(row.get('created_at', ''))
                    }
                    
                    if tweet['id'] and tweet['text']:
                        tweets.append(tweet)
                        
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
        
        # Sort by timestamp (newest first)
        tweets.sort(key=lambda x: x['timestamp'], reverse=True)
        return tweets
    
    def _parse_timestamp(self, created_at: str) -> datetime:
        """Parse timestamp from various Twitter date formats."""
        if not created_at:
            return datetime.now()
            
        try:
            # TwitterAPI.io format: "Tue Aug 12 13:11:03 +0000 2025"
            return datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y").replace(tzinfo=None)
        except ValueError:
            try:
                # ISO format: "2025-08-12T13:11:03.000Z"
                return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    # ISO format without microseconds: "2025-08-12T13:11:03Z"
                    return datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    logger.warning(f"Could not parse timestamp: {created_at}")
                    return datetime.now()
    
    def _detect_threads(self, tweets: List[Dict]) -> tuple:
        """Detect which tweets belong to threads."""
        threads = []
        thread_tweet_ids = set()  # Only tweets that are part of multi-tweet threads
        
        for i, tweet in enumerate(tweets):
            if tweet['id'] in thread_tweet_ids:
                continue
                
            # Look for tweets within time window
            thread_tweets = [tweet]
            candidate_ids = {tweet['id']}  # Temporary set for this potential thread
            
            # Check subsequent tweets within time window
            for j in range(i + 1, len(tweets)):
                other_tweet = tweets[j]
                if other_tweet['id'] in thread_tweet_ids:
                    continue
                
                time_diff = abs((tweet['timestamp'] - other_tweet['timestamp']).total_seconds())
                
                # If within time window (default 2 minutes = 120 seconds)
                if time_diff <= (self.time_window_minutes * 60):
                    thread_tweets.append(other_tweet)
                    candidate_ids.add(other_tweet['id'])
                # Continue checking all tweets - don't break early
            
            # If we found multiple tweets in the time window, it's a thread
            if len(thread_tweets) > 1:
                # Sort thread tweets by timestamp (chronological order)
                thread_tweets.sort(key=lambda x: x['timestamp'])
                threads.append(thread_tweets)
                # Mark all tweets in this thread as used
                thread_tweet_ids.update(candidate_ids)
        
        # Standalone tweets are those not in any thread
        standalone_tweets = [tweet for tweet in tweets if tweet['id'] not in thread_tweet_ids]
        
        return threads, standalone_tweets
    
    def _create_consolidated_posts(self, threads: List[List[Dict]], standalone_tweets: List[Dict]) -> List[Dict]:
        """Create consolidated posts from threads and standalone tweets."""
        consolidated_posts = []
        
        # Process threads - combine text into single post
        for thread in threads:
            if not thread:
                continue
                
            # Use the first tweet's ID and timestamp
            first_tweet = thread[0]
            
            # Combine all text with line breaks
            combined_text = ""
            for i, tweet in enumerate(thread):
                if i == 0:
                    combined_text = tweet['text']
                else:
                    # Add subsequent tweets as continuation
                    combined_text += f"\n\n{tweet['text']}"
            
            consolidated_post = {
                'tweet_id': first_tweet['id'],
                'timestamp': first_tweet['created_at'],
                'text': combined_text,
                'is_thread': True,
                'thread_count': len(thread)
            }
            
            consolidated_posts.append(consolidated_post)
        
        # Process standalone tweets
        for tweet in standalone_tweets:
            consolidated_post = {
                'tweet_id': tweet['id'],
                'timestamp': tweet['created_at'],
                'text': tweet['text'],
                'is_thread': False,
                'thread_count': 1
            }
            
            consolidated_posts.append(consolidated_post)
        
        # Sort by timestamp (newest first)
        consolidated_posts.sort(key=lambda x: self._parse_timestamp(x['timestamp']), reverse=True)
        
        return consolidated_posts
    
    def _save_consolidated_csv(self, posts: List[Dict], filename: str) -> str:
        """Save consolidated posts to CSV with only 3 columns."""
        
        # Ensure processed directory exists
        processed_dir = '../data/processed'
        os.makedirs(processed_dir, exist_ok=True)
        
        filepath = os.path.join(processed_dir, filename)
        
        # Write CSV with only 3 columns as requested
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['tweet_id', 'timestamp', 'text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for post in posts:
                # Clean text for CSV (remove newlines that would break CSV format)
                clean_text = post['text'].replace('\n', ' ').replace('\r', ' ')
                
                row = {
                    'tweet_id': post['tweet_id'],
                    'timestamp': post['timestamp'],
                    'text': clean_text
                }
                writer.writerow(row)
        
        logger.info(f"Saved {len(posts)} consolidated posts to {filepath}")
        print(f"STATUS:Saved {len(posts)} consolidated posts to {filepath}")
        
        return filepath


def main():
    """Main execution function."""
    if len(sys.argv) != 2:
        print("Usage: python thread_consolidator.py <input_csv_file>")
        print("Example: python thread_consolidator.py raw-Mantle-realtime-2025-08-12.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(input_file):
        # Try looking in the raw data folder
        raw_file_path = os.path.join('../data/raw', input_file)
        if os.path.exists(raw_file_path):
            input_file = raw_file_path
        else:
            print(f"ERROR:File not found: {input_file}")
            sys.exit(1)
    
    try:
        print("STATUS:Starting thread consolidation...")
        print(f"STATUS:Processing file: {input_file}")
        
        consolidator = ThreadConsolidator(time_window_minutes=2)
        output_filepath = consolidator.process_csv(input_file)
        
        print(f"SUCCESS:{output_filepath}")
        
    except Exception as e:
        logger.error(f"Thread consolidation failed: {e}")
        print(f"ERROR:{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()