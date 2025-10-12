from flask import Flask, request, jsonify
import requests
import random
import time

app = Flask(__name__)

VALID_KEY = "vishalapi"
user_limits = {}

class UserLimit:
    def __init__(self, uid):
        self.uid = uid
        self.last_used = None
    
    def can_use(self):
        if not self.last_used:
            return True, None
        
        time_since_last_use = time.time() - self.last_used
        if time_since_last_use < 24 * 3600:
            remaining_time = 24 * 3600 - time_since_last_use
            return False, remaining_time
        return True, None
    
    def use(self):
        self.last_used = time.time()

def get_remaining_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@app.route('/')
def home():
    return "🚀 API Server is Running"

@app.route('/check')
def check_uid():
    try:
        uid = request.args.get('uid')
        key = request.args.get('key')
        
        if not uid:
            return jsonify({"error": "UID required"}), 400
        
        if key != VALID_KEY:
            return jsonify({"error": "Invalid authentication"}), 401
        
        if uid in user_limits:
            user_limit = user_limits[uid]
            can_use, remaining_time = user_limit.can_use()
            if not can_use:
                return jsonify({
                    "error": "You Limit Succeeded",
                    "remaining_time": get_remaining_time(remaining_time),
                    "countdown_seconds": int(remaining_time)
                }), 429
        else:
            user_limits[uid] = UserLimit(uid)
        
        # External API call
        api_url = f"https://check-api-beige-one.vercel.app/check?uid={uid}"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        # Check if account exists (name should not be null)
        if data.get('nickname') is None or data.get('region') is None:
            return jsonify({
                "error": "Account Trial Not Exist In Game Or Not Found By Nexbytes"
            }), 404
        
        if data.get('status') != 'success':
            return jsonify({"error": "Invalid UID"}), 400
        
        random_likes = random.randint(89, 100)
        user_limits[uid].use()
        
        result = {
            "message": "🚀 UID Validated - API connected",
            "data": {
                "uid": data.get('uid'),
                "name": data.get('nickname'),
                "region": data.get('region'),
                "ban_status": data.get('ban_status')
            },
            "likes_details": {
                "likes_given": random_likes,
                "sent_by": "@Unknown"
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
