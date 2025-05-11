from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import signal
import sys

app = Flask(__name__)

class ScoreboardServer:
    def __init__(self):
        self.scores = []
        self.data_file = 'scores.json'
        self.load_scores()
        print("Scoreboard server initialized")

    def load_scores(self):
        """保存されたスコアデータを読み込む"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.scores = json.load(f)
                print(f"Loaded {len(self.scores)} scores from {self.data_file}")
            else:
                self.scores = []
                self.save_scores()
                print("Created new scores file")
        except Exception as e:
            print(f"Error loading scores: {e}")
            self.scores = []

    def save_scores(self):
        """スコアデータをファイルに保存"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(self.scores)} scores to {self.data_file}")
        except Exception as e:
            print(f"Error saving scores: {e}")

    def submit_score(self, player_name, score, accuracy):
        """スコアを追加"""
        score_data = {
            'player_name': player_name,
            'score': score,
            'accuracy': accuracy,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.scores.append(score_data)
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        self.scores = self.scores[:10]  # Keep only top 10 scores
        self.save_scores()
        return {'status': 'success', 'message': 'Score submitted'}

    def get_scores(self):
        """スコアを取得"""
        return {'status': 'success', 'scores': self.scores}

server = ScoreboardServer()

@app.route('/submit_score', methods=['POST'])
def submit_score():
    data = request.get_json()
    if not data or not all(k in data for k in ['player_name', 'score', 'accuracy']):
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400
    
    result = server.submit_score(
        data['player_name'],
        data['score'],
        data['accuracy']
    )
    return jsonify(result)

@app.route('/get_scores', methods=['GET'])
def get_scores():
    result = server.get_scores()
    return jsonify(result)

def signal_handler(signum, frame):
    """シグナルハンドラ"""
    print("\nShutting down server...")
    server.save_scores()
    sys.exit(0)

if __name__ == '__main__':
    # シグナルハンドラを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Server started. Press Ctrl+C to stop.")
    print(f"Current scores: {server.scores}")

    # Flaskサーバーを起動
    app.run(host='0.0.0.0', port=5050)
