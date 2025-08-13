#!/usr/bin/env python3
"""
Backend API Server for Mantle Trading Dashboard
Provides REST endpoints for data pulling and analysis
"""

import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Global variables for tracking data pull progress
data_pull_status = {
    'in_progress': False,
    'progress': 0,
    'status_text': '',
    'posts_downloaded': 0,
    'api_calls': 0,
    'current_date': '',
    'error': None,
    'result': None
}

def calculate_date_based_progress(current_date: str, start_date: str, posts_downloaded: int) -> float:
    """Calculate progress based on how close we are to the target start date."""
    try:
        if not current_date or not start_date:
            # Fallback to post-based progress if no dates available
            return min(90, posts_downloaded * 1.5) if posts_downloaded <= 50 else min(90, 75 + (posts_downloaded - 50) * 0.3)
        
        # Parse dates
        today = datetime.now()
        target_date = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Parse current tweet date (format: "2025-08-12 12:00")
        try:
            current_tweet_date = datetime.strptime(current_date, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                # Try without time
                current_tweet_date = datetime.strptime(current_date.split()[0], "%Y-%m-%d")
            except ValueError:
                # Fallback to post-based progress
                return min(90, posts_downloaded * 1.5) if posts_downloaded <= 50 else min(90, 75 + (posts_downloaded - 50) * 0.3)
        
        # Calculate total time span and current progress
        total_days = (today - target_date).days
        if total_days <= 0:
            return 100  # Already reached or passed target
        
        days_remaining = (current_tweet_date - target_date).days
        if days_remaining <= 0:
            return 100  # Reached target date
        
        # Calculate progress: 0% at today, 100% at target date
        progress_percent = ((total_days - days_remaining) / total_days) * 100
        
        # Ensure we don't exceed 100% and have some minimum progress if we have posts
        if posts_downloaded > 0:
            progress_percent = max(5, min(100, progress_percent))
        else:
            progress_percent = max(0, min(100, progress_percent))
        
        return progress_percent
        
    except Exception as e:
        logger.warning(f"Error calculating date-based progress: {e}")
        # Fallback to post-based progress
        return min(90, posts_downloaded * 1.5) if posts_downloaded <= 50 else min(90, 75 + (posts_downloaded - 50) * 0.3)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API server is running'})

@app.route('/api/check-api-key', methods=['POST'])
def check_api_key():
    """Check if API key is valid"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        # Test API key by making a simple request
        import requests
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        url = "https://api.twitterapi.io/twitter/user/by_username"
        params = {"username": "Mantle_Official"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return jsonify({'valid': True, 'message': 'API key is valid'})
        elif response.status_code == 401:
            return jsonify({'valid': False, 'message': 'Invalid API key'})
        else:
            return jsonify({'valid': False, 'message': f'API error: {response.status_code}'})
            
    except Exception as e:
        logger.error(f"Error checking API key: {e}")
        return jsonify({'valid': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/start-data-pull', methods=['POST'])
def start_data_pull():
    """Start data pull process"""
    global data_pull_status
    
    if data_pull_status['in_progress']:
        return jsonify({'error': 'Data pull already in progress'}), 400
    
    try:
        data = request.get_json()
        token = data.get('token')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        api_key = data.get('api_key')
        
        # Debug: Log received parameters
        logger.info(f"Received data pull request: token={token}, start_date={start_date}, end_date={end_date}")
        
        if not all([token, start_date, api_key]):
            return jsonify({'error': 'Missing required parameters (token, start_date, api_key)'}), 400
        
        # Reset status
        data_pull_status.update({
            'in_progress': True,
            'progress': 0,
            'status_text': 'Starting data pull...',
            'posts_downloaded': 0,
            'api_calls': 0,
            'error': None,
            'result': None
        })
        
        # Start data pull in background thread
        thread = threading.Thread(
            target=execute_data_pull,
            args=(token, start_date, end_date or None, api_key)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Data pull started', 'status': data_pull_status})
        
    except Exception as e:
        logger.error(f"Error starting data pull: {e}")
        data_pull_status['in_progress'] = False
        return jsonify({'error': f'Failed to start data pull: {str(e)}'}), 500

@app.route('/api/data-pull-status', methods=['GET'])
def get_data_pull_status():
    """Get current data pull status"""
    return jsonify(data_pull_status)

@app.route('/api/cancel-data-pull', methods=['POST'])
def cancel_data_pull():
    """Cancel ongoing data pull"""
    global data_pull_status
    
    if data_pull_status['in_progress']:
        data_pull_status.update({
            'in_progress': False,
            'status_text': 'Cancelled by user',
            'error': 'Cancelled'
        })
        return jsonify({'message': 'Data pull cancelled'})
    else:
        return jsonify({'message': 'No data pull in progress'})

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    """Run analysis on existing data"""
    try:
        # Get request data
        data = request.get_json() if request.get_json() else {}
        processed_file = data.get('processed_file', '')
        token = data.get('token', 'mantle')
        
        # Run analysis script
        script_path = os.path.join(os.path.dirname(__file__), 'mantle_csv_system_simple.py')
        
        # Pass processed file as argument if provided
        args = [sys.executable, script_path]
        if processed_file:
            args.append(processed_file)
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Parse the output to extract key metrics
            output_lines = result.stdout.split('\n')
            stats = {}
            
            for line in output_lines:
                if 'Total Posts Analyzed:' in line:
                    stats['total_posts'] = int(line.split(':')[1].strip())
                elif 'Posts Qualified:' in line:
                    stats['qualified_posts'] = int(line.split(':')[1].strip())
                elif 'Qualification Rate:' in line:
                    stats['qualification_rate'] = float(line.split(':')[1].strip().replace('%', ''))
                elif 'Total P&L:' in line:
                    stats['total_pnl'] = float(line.split(':')[1].strip().replace('$', ''))
                elif 'Average Impact Score:' in line:
                    stats['average_score'] = float(line.split(':')[1].split('/')[0].strip())
            
            return jsonify({
                'success': True,
                'message': 'Analysis completed successfully',
                'stats': stats,
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Analysis failed: {result.stderr}',
                'output': result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Analysis timed out'}), 500
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def execute_data_pull(token, start_date, end_date, api_key):
    """Execute data pull in background thread"""
    global data_pull_status
    
    try:
        # Set environment variable
        env = os.environ.copy()
        env['TWITTERAPI_IO_KEY'] = api_key
        
        # Update status
        data_pull_status.update({
            'progress': 10,
            'status_text': 'Initializing data pull...'
        })
        
        # Run the data puller script
        script_path = os.path.join(os.path.dirname(__file__), 'x_data_puller.py')
        args = [sys.executable, script_path, start_date, token]
        if end_date:
            args.insert(-1, end_date)  # Insert end_date before token if provided
        
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Monitor the process output
        posts_downloaded = 0
        api_calls = 0
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
                
            if output:
                line = output.strip()
                logger.info(f"Data puller output: {line}")
                
                # Parse progress information
                if line.startswith('PROGRESS:'):
                    try:
                        parts = line.split(':')
                        posts_downloaded = int(parts[1])
                        api_calls = int(parts[2])
                        status_text = parts[3] if len(parts) > 3 else 'Processing...'
                        
                        # Calculate progress based on date proximity to target
                        progress = calculate_date_based_progress(
                            current_date=data_pull_status.get('current_date', ''),
                            start_date=start_date,
                            posts_downloaded=posts_downloaded
                        )
                        
                        data_pull_status.update({
                            'progress': progress,
                            'status_text': status_text,
                            'posts_downloaded': posts_downloaded,
                            'api_calls': api_calls
                        })
                    except (ValueError, IndexError):
                        pass
                        
                elif line.startswith('STATUS:'):
                    status_text = line[7:]  # Remove 'STATUS:' prefix
                    data_pull_status['status_text'] = status_text
                
                elif line.startswith('CURRENT_DATE:'):
                    current_date = line[13:]  # Remove 'CURRENT_DATE:' prefix
                    data_pull_status['current_date'] = current_date
                    
                elif line.startswith('SUCCESS:'):
                    try:
                        parts = line.split(':')
                        final_posts = int(parts[1])
                        filepath = parts[2] if len(parts) > 2 else 'Unknown'
                        
                        data_pull_status.update({
                            'progress': 100,
                            'status_text': 'Data pull completed successfully!',
                            'posts_downloaded': final_posts,
                            'result': {
                                'posts': final_posts,
                                'filepath': filepath,
                                'api_calls': api_calls
                            }
                        })
                    except (ValueError, IndexError):
                        pass
                        
                elif line.startswith('ERROR:'):
                    error_msg = line[6:]  # Remove 'ERROR:' prefix
                    data_pull_status.update({
                        'error': error_msg,
                        'status_text': f'Error: {error_msg}'
                    })
                    break
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0 and not data_pull_status.get('error'):
            data_pull_status.update({
                'progress': 100,
                'status_text': 'Data pull completed successfully!'
            })
        elif not data_pull_status.get('error'):
            stderr_output = process.stderr.read()
            data_pull_status.update({
                'error': f'Process failed with code {return_code}: {stderr_output}',
                'status_text': 'Data pull failed'
            })
            
    except Exception as e:
        logger.error(f"Error in data pull execution: {e}")
        data_pull_status.update({
            'error': str(e),
            'status_text': f'Error: {str(e)}'
        })
    finally:
        data_pull_status['in_progress'] = False

@app.route('/api/list-raw-files', methods=['GET'])
def list_raw_files():
    """List available raw CSV files for processing"""
    try:
        raw_data_path = '../data/raw'
        if not os.path.exists(raw_data_path):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(raw_data_path):
            if filename.endswith('.csv') and filename.startswith('raw-'):
                files.append(filename)
        
        # Sort by modification time (newest first)
        files.sort(key=lambda f: os.path.getmtime(os.path.join(raw_data_path, f)), reverse=True)
        
        return jsonify({'files': files})
        
    except Exception as e:
        logger.error(f"Error listing raw files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-threads', methods=['POST'])
def process_threads():
    """Process a raw CSV file to consolidate threads"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'Filename is required'}), 400
        
        # Run thread consolidator script
        script_path = os.path.join(os.path.dirname(__file__), 'thread_consolidator.py')
        
        # The script expects just the filename, it will look in ../data/raw/
        result = subprocess.run(
            [sys.executable, script_path, filename],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Parse output to extract information
            output_lines = result.stdout.split('\n')
            threads_detected = 0
            posts_consolidated = 0
            output_file = ''
            
            for line in output_lines:
                if 'Detected' in line and 'threads' in line:
                    # Parse: "STATUS:Detected 5 threads and 10 standalone tweets"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i < len(parts) - 1 and 'thread' in parts[i + 1]:
                            threads_detected = int(part)
                            break
                elif 'Consolidated to' in line:
                    # Parse: "STATUS:Consolidated to 15 total posts"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i < len(parts) - 1 and 'total' in parts[i + 1]:
                            posts_consolidated = int(part)
                            break
                elif 'SUCCESS:' in line:
                    # Parse: "SUCCESS:/path/to/processed-file.csv"
                    output_path = line.split('SUCCESS:')[1].strip()
                    output_file = os.path.basename(output_path)
            
            return jsonify({
                'success': True,
                'message': 'Thread consolidation completed successfully',
                'threads_detected': threads_detected,
                'posts_consolidated': posts_consolidated,
                'total_posts': posts_consolidated,  # Same as consolidated for now
                'input_file': filename,
                'output_file': output_file,
                'output': result.stdout
            })
        else:
            error_msg = result.stderr or 'Thread consolidation failed'
            return jsonify({
                'success': False,
                'error': error_msg,
                'output': result.stdout
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Thread consolidation timed out'}), 500
    except Exception as e:
        logger.error(f"Error processing threads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/list-processed-files', methods=['GET'])
def list_processed_files():
    """List available processed CSV files for analysis"""
    try:
        processed_data_path = '../data/processed'
        if not os.path.exists(processed_data_path):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(processed_data_path):
            if filename.endswith('.csv') and filename.startswith('processed-'):
                files.append(filename)
        
        # Sort by modification time (newest first)
        files.sort(key=lambda f: os.path.getmtime(os.path.join(processed_data_path, f)), reverse=True)
        
        return jsonify({'files': files})
        
    except Exception as e:
        logger.error(f"Error listing processed files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-analysis-results', methods=['GET'])
def get_analysis_results():
    """Get the latest analysis results from CSV"""
    try:
        csv_file_path = '../data/post_evaluations.csv'
        if not os.path.exists(csv_file_path):
            return jsonify({'error': 'No analysis results found. Run analysis first.'}), 404
        
        results = []
        trades = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                # Convert CSV row to result format
                result = {
                    'timestamp': row['timestamp'],
                    'post_id': row['post_id'],
                    'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
                    'engagement_likes': int(row['engagement_likes']) if row['engagement_likes'] else 0,
                    'engagement_retweets': int(row['engagement_retweets']) if row['engagement_retweets'] else 0,
                    'evaluation_reasoning': row['evaluation_reasoning'],
                    'impact_score': int(row['impact_score']) if row['impact_score'] else 0,
                    'trade_executed': row['trade_executed'] == 'True',
                    'buy_price': float(row['buy_price']) if row['buy_price'] else None,
                    'sell_price': float(row['sell_price']) if row['sell_price'] else None,
                    'pnl': float(row['pnl']) if row['pnl'] else None
                }
                results.append(result)
                
                # If this was a trade, add to trades list
                if result['trade_executed'] and result['pnl'] is not None:
                    trade = {
                        'timestamp': result['timestamp'],
                        'content': result['content'],
                        'impact_score': result['impact_score'],
                        'buy_price': result['buy_price'],
                        'sell_price': result['sell_price'],
                        'pnl': result['pnl']
                    }
                    trades.append(trade)
        
        # Calculate summary stats
        total_posts = len(results)
        qualified_posts = len([r for r in results if r['trade_executed']])
        total_pnl = sum(r['pnl'] for r in results if r['pnl'] is not None)
        avg_score = sum(r['impact_score'] for r in results) / total_posts if total_posts > 0 else 0
        
        return jsonify({
            'results': results,
            'trades': trades,
            'stats': {
                'total_posts': total_posts,
                'qualified_posts': qualified_posts,
                'qualification_rate': (qualified_posts / total_posts * 100) if total_posts > 0 else 0,
                'total_pnl': round(total_pnl, 2),
                'average_score': round(avg_score, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Mantle Trading API Server...")
    print("📡 API endpoints available at:")
    print("   - http://localhost:5000/api/health")
    print("   - http://localhost:5000/api/start-data-pull")
    print("   - http://localhost:5000/api/data-pull-status")
    print("   - http://localhost:5000/api/list-raw-files")
    print("   - http://localhost:5000/api/process-threads")
    print("   - http://localhost:5000/api/list-processed-files")
    print("   - http://localhost:5000/api/run-analysis")
    print("   - http://localhost:5000/api/get-analysis-results")
    print("\n🌐 Dashboard should connect to: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)