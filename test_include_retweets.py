#!/usr/bin/env python3
"""
Test script to see if includeRetweets=false parameter works with TwitterAPI.io
"""

import requests
import json

api_key = "7e8dcf1e8ad04f41a96ff46998041225"
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

print("🔍 Testing TwitterAPI.io includeRetweets parameter...")

# Test 1: Default behavior
print("\n=== TEST 1: Default behavior (no includeRetweets param) ===")
url = "https://api.twitterapi.io/twitter/user/last_tweets"
params1 = {"userName": "Mantle_Official", "page": 1}

response1 = requests.get(url, headers=headers, params=params1, timeout=30)
if response1.status_code == 200:
    data1 = response1.json()
    tweets1 = data1.get('data', {}).get('tweets', [])
    print(f"Total tweets: {len(tweets1)}")
    
    retweet_count1 = sum(1 for tweet in tweets1 if tweet.get('text', '').startswith('RT @'))
    original_count1 = len(tweets1) - retweet_count1
    
    print(f"- Retweets (start with RT @): {retweet_count1}")
    print(f"- Original posts: {original_count1}")

# Test 2: With includeRetweets=false
print("\n=== TEST 2: includeRetweets=false ===")
params2 = {"userName": "Mantle_Official", "page": 1, "includeRetweets": "false"}

response2 = requests.get(url, headers=headers, params=params2, timeout=30)
if response2.status_code == 200:
    data2 = response2.json()
    tweets2 = data2.get('data', {}).get('tweets', [])
    print(f"Total tweets: {len(tweets2)}")
    
    retweet_count2 = sum(1 for tweet in tweets2 if tweet.get('text', '').startswith('RT @'))
    original_count2 = len(tweets2) - retweet_count2
    
    print(f"- Retweets (start with RT @): {retweet_count2}")
    print(f"- Original posts: {original_count2}")

# Test 3: Both parameters
print("\n=== TEST 3: includeRetweets=false AND includeReplies=false ===")
params3 = {"userName": "Mantle_Official", "page": 1, "includeRetweets": "false", "includeReplies": "false"}

response3 = requests.get(url, headers=headers, params=params3, timeout=30)
if response3.status_code == 200:
    data3 = response3.json()
    tweets3 = data3.get('data', {}).get('tweets', [])
    print(f"Total tweets: {len(tweets3)}")
    
    retweet_count3 = sum(1 for tweet in tweets3 if tweet.get('text', '').startswith('RT @'))
    original_count3 = len(tweets3) - retweet_count3
    
    print(f"- Retweets (start with RT @): {retweet_count3}")
    print(f"- Original posts: {original_count3}")

print("\n🎯 Analysis:")
print(f"Default: {len(tweets1) if 'tweets1' in locals() else 0} tweets ({retweet_count1 if 'retweet_count1' in locals() else 0} retweets)")
print(f"includeRetweets=false: {len(tweets2) if 'tweets2' in locals() else 0} tweets ({retweet_count2 if 'retweet_count2' in locals() else 0} retweets)")
print(f"Both filters: {len(tweets3) if 'tweets3' in locals() else 0} tweets ({retweet_count3 if 'retweet_count3' in locals() else 0} retweets)")

if 'tweets1' in locals() and 'tweets2' in locals():
    if retweet_count2 < retweet_count1:
        print("✅ includeRetweets=false parameter WORKS! It filters out retweets.")
    elif retweet_count2 == retweet_count1:
        print("❌ includeRetweets=false parameter has NO EFFECT")
    else:
        print("🤔 includeRetweets=false parameter has UNEXPECTED behavior")