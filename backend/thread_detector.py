#!/usr/bin/env python3
"""
Tweet Thread Detection System
Identifies and combines related tweets into cohesive threads
"""

import csv
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import re
import logging

class TwitterThreadDetector:
    """Detects and combines tweet threads based on multiple criteria."""
    
    def __init__(self, time_window_minutes: int = 2):
        """
        Initialize thread detector.
        
        Args:
            time_window_minutes: Maximum time gap between tweets in same thread (1-2 minutes)
        """
        self.time_window = timedelta(minutes=time_window_minutes)
        self.logger = logging.getLogger(__name__)
        
    def detect_threads(self, csv_file_path: str) -> List[Dict]:
        """
        Detect threads in CSV file and return combined thread data.
        
        Returns:
            List of thread objects with combined content
        """
        # Load tweets
        tweets = self._load_tweets(csv_file_path)
        
        # Group tweets into potential threads
        thread_groups = self._group_by_time_proximity(tweets)
        
        # Analyze each group for thread characteristics
        detected_threads = []
        standalone_tweets = []
        
        for group in thread_groups:
            if self._is_thread(group):
                thread = self._combine_thread(group)
                detected_threads.append(thread)
            else:
                standalone_tweets.extend(group)
        
        return {
            'threads': detected_threads,
            'standalone': standalone_tweets,
            'stats': {
                'total_tweets': len(tweets),
                'threads_found': len(detected_threads),
                'standalone_tweets': len(standalone_tweets),
                'threads_combined_tweets': sum(len(t['original_tweets']) for t in detected_threads)
            }
        }
    
    def _load_tweets(self, csv_file_path: str) -> List[Dict]:
        """Load tweets from CSV and parse timestamps."""
        tweets = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse Twitter's timestamp format
                    timestamp = datetime.strptime(row['created_at'], "%a %b %d %H:%M:%S %z %Y")
                    
                    tweets.append({
                        'id': row['tweet_id'],
                        'timestamp': timestamp,
                        'text': row['text'],
                        'like_count': int(row['like_count'] or 0),
                        'retweet_count': int(row['retweet_count'] or 0),
                        'reply_count': int(row['reply_count'] or 0),
                        'author_id': row['author_id']
                    })
                except Exception as e:
                    self.logger.warning(f"Could not parse tweet {row.get('tweet_id', 'unknown')}: {e}")
        
        # Sort by timestamp (oldest first for proper thread order)
        tweets.sort(key=lambda x: x['timestamp'])
        return tweets
    
    def _group_by_time_proximity(self, tweets: List[Dict]) -> List[List[Dict]]:
        """Group tweets that are close in time."""
        if not tweets:
            return []
        
        groups = []
        current_group = [tweets[0]]
        
        for i in range(1, len(tweets)):
            time_diff = tweets[i]['timestamp'] - current_group[-1]['timestamp']
            
            if time_diff <= self.time_window:
                current_group.append(tweets[i])
            else:
                groups.append(current_group)
                current_group = [tweets[i]]
        
        groups.append(current_group)
        return groups
    
    def _is_thread(self, tweet_group: List[Dict]) -> bool:
        """
        Determine if a group of tweets constitutes a thread.
        
        Simple criteria for rapid-fire threads:
        1. Multiple tweets (2+) 
        2. Posted within 1-2 minutes
        3. Basic topic coherence OR rapid posting pattern
        """
        if len(tweet_group) < 2:
            return False
        
        # For very rapid tweets (within 2 minutes), be more lenient
        time_span = tweet_group[-1]['timestamp'] - tweet_group[0]['timestamp']
        
        # If posted very rapidly (within 1 minute), likely a thread
        if time_span.total_seconds() <= 60:
            return True
        
        # If posted within 2 minutes AND has topic coherence, it's a thread
        if time_span.total_seconds() <= 120 and self._has_topic_coherence(tweet_group):
            return True
        
        return False
    
    def _has_sequential_content(self, tweets: List[Dict]) -> bool:
        """Check for sequential content indicators."""
        texts = [t['text'].lower() for t in tweets]
        
        # Look for numbered sequences (1/, 2/, etc.)
        numbered_pattern = r'(\d+/\d+|\d+\.|^\d+\))'
        numbered_tweets = sum(1 for text in texts if re.search(numbered_pattern, text))
        
        if numbered_tweets >= 2:
            return True
        
        # Look for continuation indicators
        continuation_words = ['however', 'furthermore', 'additionally', 'meanwhile', 'next', 'then', 'finally']
        continuation_count = sum(1 for text in texts for word in continuation_words if word in text)
        
        return continuation_count >= 1
    
    def _has_topic_coherence(self, tweets: List[Dict]) -> bool:
        """Check if tweets share common topics/themes."""
        texts = [t['text'].lower() for t in tweets]
        
        # Extract key terms (hashtags, mentions, common words)
        all_words = ' '.join(texts).split()
        hashtags = [word for word in all_words if word.startswith('#')]
        mentions = [word for word in all_words if word.startswith('@')]
        
        # Check for repeated key terms
        key_terms = hashtags + mentions
        if len(set(key_terms)) < len(key_terms) * 0.8:  # Some repetition
            return True
        
        # Check for thematic keywords appearing multiple times
        business_terms = ['partnership', 'collaboration', 'launch', 'update', 'announcement', 'ecosystem', 'advisor', 'advisors']
        tech_terms = ['blockchain', 'defi', 'crypto', 'token', 'network', 'protocol']
        event_terms = ['live', 'stream', 'broadcast', 'calendar', 'date', 'featuring', '@bybit_official', 'helen liu', 'emily bao']
        
        for term_group in [business_terms, tech_terms, event_terms]:
            matches = sum(1 for text in texts for term in term_group if term in text)
            if matches >= 2:
                return True
        
        # Special case: Bybit partnership references
        bybit_refs = sum(1 for text in texts if 'bybit' in text)
        if bybit_refs >= 2:
            return True
        
        return False
    
    def _has_narrative_flow(self, tweets: List[Dict]) -> bool:
        """Check for narrative progression (intro -> details -> conclusion)."""
        if len(tweets) < 3:
            return False
        
        texts = [t['text'].lower() for t in tweets]
        
        # First tweet often introduces topic
        intro_indicators = ['introducing', 'announcing', 'excited to', 'proud to', 'what is']
        has_intro = any(indicator in texts[0] for indicator in intro_indicators)
        
        # Last tweet often concludes or calls to action
        conclusion_indicators = ['learn more', 'check out', 'join us', 'stay tuned', 'coming soon']
        has_conclusion = any(indicator in texts[-1] for indicator in conclusion_indicators)
        
        return has_intro or has_conclusion
    
    def _combine_thread(self, tweets: List[Dict]) -> Dict:
        """Combine tweets into a single thread object."""
        # Sort tweets chronologically
        sorted_tweets = sorted(tweets, key=lambda x: x['timestamp'])
        
        # Combine text with thread indicators
        combined_text_parts = []
        for i, tweet in enumerate(sorted_tweets, 1):
            text = tweet['text']
            # Add thread numbering if not already present
            if not re.match(r'^\d+[/.)]', text):
                text = f"{i}/{len(sorted_tweets)} {text}"
            combined_text_parts.append(text)
        
        combined_text = '\n\n'.join(combined_text_parts)
        
        # Aggregate engagement metrics
        total_likes = sum(t['like_count'] for t in tweets)
        total_retweets = sum(t['retweet_count'] for t in tweets)
        total_replies = sum(t['reply_count'] for t in tweets)
        
        return {
            'thread_id': f"thread_{sorted_tweets[0]['id']}",
            'start_time': sorted_tweets[0]['timestamp'],
            'end_time': sorted_tweets[-1]['timestamp'],
            'duration_minutes': (sorted_tweets[-1]['timestamp'] - sorted_tweets[0]['timestamp']).total_seconds() / 60,
            'tweet_count': len(tweets),
            'combined_text': combined_text,
            'total_engagement': {
                'likes': total_likes,
                'retweets': total_retweets,
                'replies': total_replies,
                'total': total_likes + total_retweets + total_replies
            },
            'original_tweets': [{'id': t['id'], 'text': t['text'], 'timestamp': t['timestamp']} for t in sorted_tweets],
            'author_id': tweets[0]['author_id']
        }

def main():
    """Test the thread detector on the current CSV."""
    detector = TwitterThreadDetector(time_window_minutes=2)
    
    # Analyze the current CSV
    csv_path = '../data/raw/raw-Mantle-realtime-2025-08-12.csv'
    
    try:
        results = detector.detect_threads(csv_path)
        
        print("🧵 THREAD DETECTION RESULTS")
        print("=" * 50)
        print(f"📊 Total tweets analyzed: {results['stats']['total_tweets']}")
        print(f"🔗 Threads detected: {results['stats']['threads_found']}")
        print(f"📝 Standalone tweets: {results['stats']['standalone_tweets']}")
        print(f"🔄 Tweets combined into threads: {results['stats']['threads_combined_tweets']}")
        print()
        
        # Show detected threads
        for i, thread in enumerate(results['threads'], 1):
            print(f"🧵 THREAD {i}")
            print(f"   📅 Time: {thread['start_time'].strftime('%Y-%m-%d %H:%M')} - {thread['end_time'].strftime('%H:%M')}")
            print(f"   ⏱️  Duration: {thread['duration_minutes']:.1f} minutes")
            print(f"   📝 Tweets: {thread['tweet_count']}")
            print(f"   💡 Combined text preview: {thread['combined_text'][:200]}...")
            print()
        
    except FileNotFoundError:
        print("❌ CSV file not found. Make sure the data pull has completed.")
    except Exception as e:
        print(f"❌ Error analyzing threads: {e}")

if __name__ == "__main__":
    main()