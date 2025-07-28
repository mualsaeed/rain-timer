from flask import Flask, render_template, jsonify, request
import threading
import time
import os

app = Flask(__name__)

class SimpleTimer:
    def __init__(self):
        # Timer settings - 45 seconds until heavy rain
        self.rain_duration = 45
        self.safe_time = 7  # 7 seconds to find shelter
        
        # State
        self.countdown_active = False
        self.remaining_time = 0
        self.timer_thread = None
        self.clients = []  # Simple client tracking
        
    def trigger_rain_timer(self):
        """Trigger the rain countdown"""
        if self.countdown_active:
            print("Timer already running, resetting...")
            self.countdown_active = False
            if self.timer_thread:
                self.timer_thread.join(timeout=0.5)
        
        print("Timer triggered! Starting countdown...")
        self.countdown_active = True
        self.remaining_time = self.rain_duration
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.timer_thread.start()
        return True
    
    def timer_loop(self):
        """Timer countdown loop"""
        while self.countdown_active and self.remaining_time > 0:
            # Update every 0.1 seconds
            time.sleep(0.1)
            self.remaining_time -= 0.1
        
        # Timer finished
        self.countdown_active = False
        
        # Reset after 3 seconds
        time.sleep(3)
        self.remaining_time = 0
    
    def stop_timer(self):
        """Stop the current timer"""
        if self.countdown_active:
            self.countdown_active = False
            self.remaining_time = 0
            return True
        return False
    
    def get_status(self):
        """Get current timer status"""
        if not self.countdown_active:
            return {
                'active': False,
                'time': 45.0,
                'safe': True,
                'status': 'READY'
            }
        
        is_safe = self.remaining_time > self.safe_time
        return {
            'active': True,
            'time': round(self.remaining_time, 1),
            'safe': is_safe,
            'status': 'SAFE TIME' if is_safe else 'FIND SHELTER'
        }

# Global timer instance
timer = SimpleTimer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/manual_trigger', methods=['POST'])
def manual_trigger():
    """Manually trigger rain timer"""
    success = timer.trigger_rain_timer()
    return jsonify({'success': success, 'message': 'Timer triggered'})

@app.route('/api/stop_timer', methods=['POST'])
def stop_timer():
    """Stop the current timer"""
    success = timer.stop_timer()
    return jsonify({'success': success})

@app.route('/api/status')
def get_status():
    """Get current timer status"""
    return jsonify(timer.get_status())

if __name__ == '__main__':
    print("Starting Rain Alert Timer Server...")
    print("Open http://localhost:5000 in your browser")
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
