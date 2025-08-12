#!/usr/bin/env python3
"""
Mantle Trading Strategy - CSV-Based System (No External Dependencies)
Evaluates posts and stores results in CSV for website integration.
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CriteriaManager:
    """Manages evaluation criteria from JSON file."""
    
    def __init__(self, criteria_file="../config/evaluation_criteria.json"):
        self.criteria_file = criteria_file
        self.criteria = self.load_criteria()
    
    def load_criteria(self) -> Dict:
        """Load criteria from JSON file."""
        try:
            with open(self.criteria_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Criteria file {self.criteria_file} not found. Using defaults.")
            return self.get_default_criteria()
    
    def save_criteria(self, criteria: Dict):
        """Save criteria to JSON file."""
        with open(self.criteria_file, 'w') as f:
            json.dump(criteria, f, indent=2)
        self.criteria = criteria
        logger.info(f"Criteria saved to {self.criteria_file}")
    
    def get_default_criteria(self) -> Dict:
        """Return default evaluation criteria."""
        return {
            "high_impact_keywords": {
                "major_partnerships": ["partnership", "collaboration", "integrate", "alliance"],
                "major_launches": ["launch", "mainnet", "release", "deploy", "live"],
                "major_rewards": ["rewards", "airdrop", "incentive", "staking"],
                "milestones": ["milestone", "upgrade", "listing", "exchange"],
                "strategic_shifts": ["strategic", "roadmap", "vision", "future"]
            },
            "low_impact_keywords": ["ama", "meme", "gm", "gn", "thread", "reminder"],
            "excitement_indicators": ["🚀", "🔥", "⚡", "breaking", "major", "huge"],
            "thresholds": {
                "high_impact_threshold": 7,
                "engagement_weight": 150,
                "category_score": 3,
                "excitement_bonus": 1,
                "low_impact_penalty": 2
            },
            "trading_params": {
                "position_size_usdt": 1000,
                "hold_duration_minutes": 30
            }
        }

class CSVDataManager:
    """Manages post evaluations in CSV format."""
    
    def __init__(self, csv_file="../data/post_evaluations.csv"):
        self.csv_file = csv_file
        self.fieldnames = [
            'timestamp', 'post_id', 'content', 'engagement_likes', 
            'engagement_retweets', 'evaluation_reasoning', 'impact_score',
            'trade_executed', 'buy_price', 'sell_price', 'pnl'
        ]
        self.ensure_csv_exists()
    
    def ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
            logger.info(f"Created new CSV file: {self.csv_file}")
    
    def write_evaluations_batch(self, evaluations: List[Dict]):
        """Write multiple evaluations to CSV."""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            for evaluation in evaluations:
                writer.writerow(evaluation)
        logger.info(f"Written {len(evaluations)} evaluations to {self.csv_file}")
    
    def read_evaluations(self) -> List[Dict]:
        """Read all evaluations from CSV."""
        try:
            evaluations = []
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    evaluations.append(row)
            return evaluations
        except FileNotFoundError:
            logger.warning(f"CSV file {self.csv_file} not found.")
            return []
    
    def get_summary_stats(self) -> Dict:
        """Calculate summary statistics from CSV data."""
        evaluations = self.read_evaluations()
        if not evaluations:
            return {}
        
        total_posts = len(evaluations)
        qualified_posts = len([e for e in evaluations if e['trade_executed'] == 'True'])
        total_pnl = sum(float(e['pnl']) for e in evaluations if e['pnl'] and e['pnl'] != '')
        avg_score = sum(float(e['impact_score']) for e in evaluations) / total_posts if total_posts > 0 else 0
        
        return {
            'total_posts': total_posts,
            'qualified_posts': qualified_posts,
            'qualification_rate': (qualified_posts / total_posts * 100) if total_posts > 0 else 0,
            'total_pnl': round(total_pnl, 2),
            'average_score': round(avg_score, 2),
            'trades_executed': qualified_posts
        }

class PostEvaluator:
    """Evaluates posts based on configurable criteria."""
    
    def __init__(self, criteria_manager: CriteriaManager):
        self.criteria = criteria_manager.criteria
    
    def evaluate_post(self, post: Dict) -> Tuple[int, str]:
        """Evaluate a single post and return score + reasoning."""
        text = post['text'].lower()
        criteria = self.criteria
        
        high_impact_score = 0
        triggered_categories = []
        
        # Check for high-impact keywords
        for category, keywords in criteria['high_impact_keywords'].items():
            if any(keyword in text for keyword in keywords):
                high_impact_score += criteria['thresholds']['category_score']
                triggered_categories.append(category)
        
        # Check for low-impact keywords (penalty)
        low_impact_penalty = sum(
            criteria['thresholds']['low_impact_penalty'] 
            for keyword in criteria['low_impact_keywords'] 
            if keyword in text
        )
        
        # Calculate engagement score
        likes = post.get('public_metrics', {}).get('like_count', 0)
        retweets = post.get('public_metrics', {}).get('retweet_count', 0)
        engagement_score = min(4, (likes + retweets * 3) // criteria['thresholds']['engagement_weight'])
        
        # Check for excitement indicators
        excitement_bonus = 0
        if any(indicator in text for indicator in criteria['excitement_indicators']):
            excitement_bonus = criteria['thresholds']['excitement_bonus']
        
        # Calculate final score
        final_score = min(10, max(1, high_impact_score + engagement_score + excitement_bonus - low_impact_penalty))
        
        # Generate reasoning
        reasoning = f"Categories: {triggered_categories}, Engagement: {likes}L/{retweets}RT, Excitement: +{excitement_bonus}"
        if low_impact_penalty > 0:
            reasoning += f", Penalty: -{low_impact_penalty}"
        
        return final_score, reasoning
    
    def should_execute_trade(self, score: int) -> bool:
        """Determine if score qualifies for trade execution."""
        return score >= self.criteria['thresholds']['high_impact_threshold']

class TradingSimulator:
    """Simulates trading based on post evaluations."""
    
    def __init__(self, criteria_manager: CriteriaManager):
        self.criteria = criteria_manager.criteria
    
    def simulate_trade(self, post: Dict, score: int) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Simulate a trade and return buy_price, sell_price, pnl."""
        if score < self.criteria['thresholds']['high_impact_threshold']:
            return None, None, None
        
        # Generate realistic prices based on timestamp
        timestamp = post['created_at']
        buy_price = self.generate_price(timestamp)
        sell_time = self.add_minutes(timestamp, self.criteria['trading_params']['hold_duration_minutes'])
        sell_price = self.generate_price(sell_time)
        
        # Calculate P&L
        position_size = self.criteria['trading_params']['position_size_usdt']
        mnt_bought = position_size / buy_price
        pnl = (sell_price - buy_price) * mnt_bought
        
        return round(buy_price, 4), round(sell_price, 4), round(pnl, 2)
    
    def generate_price(self, timestamp_str: str) -> float:
        """Generate realistic sample price based on timestamp."""
        if timestamp_str.endswith('Z'):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str)
        
        # Simple price simulation around $0.60 base
        day_offset = (dt - datetime(2024, 8, 10, tzinfo=dt.tzinfo)).days
        hour_factor = dt.hour / 24.0
        
        base_price = 0.60
        daily_variation = (day_offset % 10 - 5) * 0.02
        hourly_variation = (hour_factor - 0.5) * 0.01
        
        return max(0.30, min(1.00, base_price + daily_variation + hourly_variation))
    
    def add_minutes(self, timestamp_str: str, minutes: int) -> str:
        """Add minutes to timestamp string."""
        if timestamp_str.endswith('Z'):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str)
        
        new_dt = dt + timedelta(minutes=minutes)
        return new_dt.isoformat()

class MantleTradingSystem:
    """Main system that orchestrates the trading strategy."""
    
    def __init__(self):
        self.criteria_manager = CriteriaManager()
        self.csv_manager = CSVDataManager()
        self.evaluator = PostEvaluator(self.criteria_manager)
        self.simulator = TradingSimulator(self.criteria_manager)
    
    def load_raw_csv_data(self) -> Optional[List[Dict]]:
        """Load data from the most recent raw CSV file."""
        raw_dir = '../data/raw'
        if not os.path.exists(raw_dir):
            return None
            
        # Find the most recent CSV file
        csv_files = [f for f in os.listdir(raw_dir) if f.endswith('.csv') and not f.startswith('.')]
        if not csv_files:
            return None
            
        # Sort by modification time, newest first
        csv_files.sort(key=lambda f: os.path.getmtime(os.path.join(raw_dir, f)), reverse=True)
        latest_file = os.path.join(raw_dir, csv_files[0])
        
        logger.info(f"Loading raw data from: {latest_file}")
        
        try:
            posts = []
            with open(latest_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert CSV row to post format
                    post = {
                        'timestamp': row['created_at'],
                        'text': row['text'],  # Use 'text' field to match evaluator expectations
                        'content': row['text'],
                        'engagement': {
                            'likes': int(row['like_count']) if row['like_count'] else 0,
                            'retweets': int(row['retweet_count']) if row['retweet_count'] else 0,
                            'replies': int(row['reply_count']) if row['reply_count'] else 0,
                            'quotes': int(row['quote_count']) if row['quote_count'] else 0
                        }
                    }
                    posts.append(post)
            
            logger.info(f"Loaded {len(posts)} posts from raw CSV")
            return posts
            
        except Exception as e:
            logger.error(f"Error loading raw CSV: {e}")
            return None
    
    def get_sample_posts(self) -> List[Dict]:
        """Get sample posts for testing."""
        return [
            {
                "id": "1",
                "text": "🚀 Major partnership announcement with leading DeFi protocol! Mantle Network integration brings new opportunities for yield farming and liquidity provision. #MantleNetwork #DeFi",
                "created_at": "2024-08-10T10:30:00Z",
                "public_metrics": {"like_count": 450, "retweet_count": 120}
            },
            {
                "id": "2", 
                "text": "GM Mantle fam! 🌅 Another beautiful day in the ecosystem. Remember to check out our latest blog post!",
                "created_at": "2024-08-10T14:15:00Z",
                "public_metrics": {"like_count": 85, "retweet_count": 12}
            },
            {
                "id": "3",
                "text": "🎉 MILESTONE ACHIEVED! Mantle Network surpasses $100M in TVL! Thank you to our amazing community. Major mainnet upgrade coming next week with enhanced security features.",
                "created_at": "2024-08-11T09:45:00Z", 
                "public_metrics": {"like_count": 890, "retweet_count": 234}
            },
            {
                "id": "4",
                "text": "Join us for an AMA session tomorrow at 3 PM UTC! We'll be discussing recent developments and answering your questions. 🤔",
                "created_at": "2024-08-11T16:20:00Z",
                "public_metrics": {"like_count": 156, "retweet_count": 45}
            },
            {
                "id": "5",
                "text": "🔥 BREAKING: Mantle Token ($MNT) now listed on 3 major exchanges! Trading begins in 1 hour. This marks a significant milestone in our journey toward mass adoption.",
                "created_at": "2024-08-12T12:00:00Z",
                "public_metrics": {"like_count": 1240, "retweet_count": 456}
            }
        ]
    
    def process_posts(self, posts: List[Dict]) -> List[Dict]:
        """Process all posts and return evaluation data."""
        evaluations = []
        
        for post in posts:
            # Evaluate post
            score, reasoning = self.evaluator.evaluate_post(post)
            
            # Simulate trade if qualified
            buy_price, sell_price, pnl = self.simulator.simulate_trade(post, score)
            
            evaluation_data = {
                'timestamp': post['timestamp'],
                'post_id': post.get('id', 'N/A'),
                'content': post['text'],
                'engagement_likes': post['engagement']['likes'],
                'engagement_retweets': post['engagement']['retweets'],
                'evaluation_reasoning': reasoning,
                'impact_score': score,
                'trade_executed': buy_price is not None,
                'buy_price': buy_price if buy_price is not None else '',
                'sell_price': sell_price if sell_price is not None else '',
                'pnl': pnl if pnl is not None else ''
            }
            
            evaluations.append(evaluation_data)
        
        return evaluations
    
    def run_analysis(self):
        """Run the complete analysis and save to CSV."""
        logger.info("Starting Mantle Trading Strategy Analysis")
        
        # Get posts (in future, this will be from X API)
        # Try to load real data first, fall back to sample if not found
        posts = self.load_raw_csv_data() or self.get_sample_posts()
        logger.info(f"Processing {len(posts)} posts")
        
        # Process posts
        evaluations = self.process_posts(posts)
        
        # Save to CSV
        self.csv_manager.write_evaluations_batch(evaluations)
        
        # Print summary
        stats = self.csv_manager.get_summary_stats()
        print("\n" + "="*60)
        print("MANTLE TRADING STRATEGY - ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total Posts Analyzed: {stats['total_posts']}")
        print(f"Posts Qualified: {stats['qualified_posts']}")
        print(f"Qualification Rate: {stats['qualification_rate']:.1f}%")
        print(f"Total P&L: ${stats['total_pnl']}")
        print(f"Average Impact Score: {stats['average_score']}/10")
        print(f"Data saved to: {self.csv_manager.csv_file}")
        print(f"Criteria saved to: {self.criteria_manager.criteria_file}")
        print("="*60)
        print("\n🌐 Open the dashboard: http://localhost:8000/mantle_dashboard.html")
        print("📊 CSV file created with all post evaluations")
        print("⚙️ Criteria can be edited in the dashboard")

def main():
    """Main execution function."""
    system = MantleTradingSystem()
    system.run_analysis()

if __name__ == "__main__":
    main()