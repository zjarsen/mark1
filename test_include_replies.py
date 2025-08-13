#!/usr/bin/env python3
"""
Test script to see if includeReplies=false parameter works with TwitterAPI.io
"""

import requests
import json

api_key = "7e8dcf1e8ad04f41a96ff46998041225"
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

print("🔍 Testing TwitterAPI.io includeReplies parameter...")

# Test 1: Default behavior (should include replies)
print("\n=== TEST 1: Default behavior (no includeReplies param) ===")
url = "https://api.twitterapi.io/twitter/user/last_tweets"
params1 = {"userName": "Mantle_Official", "page": 1}

response1 = requests.get(url, headers=headers, params=params1, timeout=30)
if response1.status_code == 200:
    data1 = response1.json()
    tweets1 = data1.get('data', {}).get('tweets', [])
    print(f"Total tweets: {len(tweets1)}")
    
    # Check for replies (tweets that start with @)
    reply_count1 = sum(1 for tweet in tweets1 if tweet.get('text', '').strip().startswith('@'))
    retweet_count1 = sum(1 for tweet in tweets1 if tweet.get('text', '').startswith('RT @'))
    original_count1 = len(tweets1) - reply_count1 - retweet_count1
    
    print(f"- Replies (start with @): {reply_count1}")
    print(f"- Retweets (start with RT @): {retweet_count1}")
    print(f"- Original posts: {original_count1}")
    
    if tweets1:
        print(f"Sample tweet: {tweets1[0].get('text', '')[:100]}...")

# Test 2: With includeReplies=false
print("\n=== TEST 2: includeReplies=false ===")
params2 = {"userName": "Mantle_Official", "page": 1, "includeReplies": "false"}

response2 = requests.get(url, headers=headers, params=params2, timeout=30)
if response2.status_code == 200:
    data2 = response2.json()
    tweets2 = data2.get('data', {}).get('tweets', [])
    print(f"Total tweets: {len(tweets2)}")
    
    # Check for replies (tweets that start with @)
    reply_count2 = sum(1 for tweet in tweets2 if tweet.get('text', '').strip().startswith('@'))
    retweet_count2 = sum(1 for tweet in tweets2 if tweet.get('text', '').startswith('RT @'))
    original_count2 = len(tweets2) - reply_count2 - retweet_count2
    
    print(f"- Replies (start with @): {reply_count2}")
    print(f"- Retweets (start with RT @): {retweet_count2}")
    print(f"- Original posts: {original_count2}")
    
    if tweets2:
        print(f"Sample tweet: {tweets2[0].get('text', '')[:100]}...")

# Test 3: With includeReplies=true (explicit)
print("\n=== TEST 3: includeReplies=true (explicit) ===")
params3 = {"userName": "Mantle_Official", "page": 1, "includeReplies": "true"}

response3 = requests.get(url, headers=headers, params=params3, timeout=30)
if response3.status_code == 200:
    data3 = response3.json()
    tweets3 = data3.get('data', {}).get('tweets', [])
    print(f"Total tweets: {len(tweets3)}")
    
    # Check for replies (tweets that start with @)
    reply_count3 = sum(1 for tweet in tweets3 if tweet.get('text', '').strip().startswith('@'))
    retweet_count3 = sum(1 for tweet in tweets3 if tweet.get('text', '').startswith('RT @'))
    original_count3 = len(tweets3) - reply_count3 - retweet_count3
    
    print(f"- Replies (start with @): {reply_count3}")
    print(f"- Retweets (start with RT @): {retweet_count3}")
    print(f"- Original posts: {original_count3}")
    
    if tweets3:
        print(f"Sample tweet: {tweets3[0].get('text', '')[:100]}...")

print("\n🎯 Analysis:")
print(f"Default behavior: {len(tweets1) if 'tweets1' in locals() else 0} tweets ({reply_count1 if 'reply_count1' in locals() else 0} replies)")
print(f"includeReplies=false: {len(tweets2) if 'tweets2' in locals() else 0} tweets ({reply_count2 if 'reply_count2' in locals() else 0} replies)")
print(f"includeReplies=true: {len(tweets3) if 'tweets3' in locals() else 0} tweets ({reply_count3 if 'reply_count3' in locals() else 0} replies)")

if 'tweets1' in locals() and 'tweets2' in locals():
    if len(tweets2) < len(tweets1) and reply_count2 < reply_count1:
        print("✅ includeReplies=false parameter WORKS! It filters out replies.")
    elif len(tweets2) == len(tweets1):
        print("❌ includeReplies=false parameter has NO EFFECT - same results as default")
    else:
        print("🤔 includeReplies=false parameter has UNEXPECTED behavior")