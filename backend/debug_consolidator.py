#!/usr/bin/env python3
"""
Debug script to trace what happens to the 'Higher' tweet during consolidation.
"""

import os
import csv
from datetime import datetime

def parse_timestamp(created_at: str) -> datetime:
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
                print(f"Could not parse timestamp: {created_at}")
                return datetime.now()

def debug_higher_tweet():
    """Debug why the 'Higher' tweet is missing."""
    
    raw_file = '../data/raw/raw-mantle-2025-08-03.csv'
    
    print("🔍 Debugging 'Higher' tweet processing...")
    print(f"Reading from: {raw_file}")
    
    tweets = []
    higher_tweet = None
    
    # Read the raw CSV
    with open(raw_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tweet = {
                'id': row.get('tweet_id', ''),
                'created_at': row.get('created_at', ''),
                'text': row.get('text', '').strip(),
                'timestamp': parse_timestamp(row.get('created_at', ''))
            }
            
            if 'Higher' in tweet['text']:
                higher_tweet = tweet
                print(f"📍 Found 'Higher' tweet:")
                print(f"   ID: {tweet['id']}")
                print(f"   Text: '{tweet['text']}'")
                print(f"   Created: {tweet['created_at']}")
                print(f"   Timestamp: {tweet['timestamp']}")
                
            # Apply the same filtering as thread_consolidator
            if tweet['id'] and tweet['text']:
                tweets.append(tweet)
            else:
                print(f"❌ Tweet filtered out - ID: '{tweet['id']}', Text: '{tweet['text']}'")
    
    print(f"\n📊 Total tweets loaded: {len(tweets)}")
    
    # Sort by timestamp (newest first) like in thread_consolidator
    tweets.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Debug thread detection
    if higher_tweet:
        print(f"✅ 'Higher' tweet passed initial filtering")
        
        # Find the Higher tweet in the sorted list
        higher_index = None
        for i, tweet in enumerate(tweets):
            if tweet['id'] == higher_tweet['id']:
                higher_index = i
                break
        
        print(f"📍 'Higher' tweet position in sorted list: {higher_index}")
        
        # Simulate thread detection for the Higher tweet
        print(f"\n🔍 Simulating thread detection for 'Higher' tweet...")
        
        time_window_minutes = 2
        used_tweet_ids = set()
        threads = []
        standalone_tweets = []
        
        for i, tweet in enumerate(tweets):
            if tweet['id'] in used_tweet_ids:
                continue
                
            # Look for tweets within time window
            thread_tweets = [tweet]
            used_tweet_ids.add(tweet['id'])
            
            if tweet['id'] == higher_tweet['id']:
                print(f"🎯 Processing 'Higher' tweet (index {i})")
                print(f"   Looking for nearby tweets within {time_window_minutes} minutes...")
            
            # Check subsequent tweets within time window
            for j in range(i + 1, len(tweets)):
                other_tweet = tweets[j]
                if other_tweet['id'] in used_tweet_ids:
                    continue
                
                time_diff = abs((tweet['timestamp'] - other_tweet['timestamp']).total_seconds())
                
                if tweet['id'] == higher_tweet['id']:
                    print(f"   Checking tweet {j}: '{other_tweet['text'][:20]}...' - Time diff: {time_diff:.1f}s")
                
                # If within time window (default 2 minutes = 120 seconds)
                if time_diff <= (time_window_minutes * 60):
                    thread_tweets.append(other_tweet)
                    used_tweet_ids.add(other_tweet['id'])
                    if tweet['id'] == higher_tweet['id']:
                        print(f"     ✅ Added to thread")
                # Continue checking all tweets - don't break early
            
            # If we found multiple tweets in the time window, it's a thread
            if len(thread_tweets) > 1:
                # Sort thread tweets by timestamp (chronological order)
                thread_tweets.sort(key=lambda x: x['timestamp'])
                threads.append(thread_tweets)
                if tweet['id'] == higher_tweet['id']:
                    print(f"   📝 'Higher' tweet is part of a {len(thread_tweets)}-tweet thread")
            else:
                if tweet['id'] == higher_tweet['id']:
                    print(f"   📝 'Higher' tweet is standalone")
        
        # Standalone tweets are those not in any thread
        standalone_tweets = [tweet for tweet in tweets if tweet['id'] not in used_tweet_ids]
        
        print(f"\n📊 Thread detection results:")
        print(f"   Threads detected: {len(threads)}")
        print(f"   Standalone tweets: {len(standalone_tweets)}")
        
        # Check if Higher tweet is in results
        higher_in_thread = False
        higher_in_standalone = False
        
        for thread in threads:
            if any(t['id'] == higher_tweet['id'] for t in thread):
                higher_in_thread = True
                break
        
        for tweet in standalone_tweets:
            if tweet['id'] == higher_tweet['id']:
                higher_in_standalone = True
                break
        
        print(f"   'Higher' tweet in threads: {higher_in_thread}")
        print(f"   'Higher' tweet in standalone: {higher_in_standalone}")
    else:
        print("❌ 'Higher' tweet not found or filtered out during reading")

if __name__ == "__main__":
    debug_higher_tweet()