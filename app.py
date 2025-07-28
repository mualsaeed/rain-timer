from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rain_alert_timer'
socketio = SocketIO(app, cors_allowed_origins="*")

class SimpleTimer:
    def __init__(self):
        # Timer settings - 45 seconds until heavy rain
        self.rain_duration = 45
        self.safe_time = 7  # 7 seconds to find shelter
        
        # State
        self.countdown_active = False
        self.remaining_time = 0
        self.timer_thread = None
        
    def trigger_rain_timer(self):
        """Trigger the rain countdown"""
        if self.countdown_active:
            print("Timer already running, resetting...")
            self.countdown_active = False
            if self.timer_thread:
                self.timer_thread.join(timeout=0.5)
        
        print("Rain detected! Starting timer...")
        self.countdown_active = True
        self.remaining_time = self.rain_duration
        
        # Notify web clients
        socketio.emit('rain_started', {'time': self.remaining_time})
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.timer_thread.start()
    
    def timer_loop(self):
        """Timer countdown loop"""
        while self.countdown_active and self.remaining_time > 0:
            # Update every 0.1 seconds
            time.sleep(0.1)
            self.remaining_time -= 0.1
            
            # Send updates to web clients
            is_safe = self.remaining_time > self.safe_time
            
            socketio.emit('timer_update', {
                'time': round(self.remaining_time, 1),
                'safe': is_safe,
                'status': 'SAFE TIME' if is_safe else 'FIND SHELTER'
            })
        
        # Timer finished
        if self.remaining_time <= 0:
            socketio.emit('timer_finished', {'status': 'HEAVY RAIN'})
        
        self.countdown_active = False
        
        # Reset after 3 seconds
        time.sleep(3)
        socketio.emit('timer_reset')
    
    def stop_timer(self):
        """Stop the current timer"""
        if self.countdown_active:
            self.countdown_active = False
            socketio.emit('timer_reset')
            return True
        return False

# Global timer instance
timer = SimpleTimer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/manual_trigger', methods=['POST'])
def manual_trigger():
    """Manually trigger rain timer"""
    timer.trigger_rain_timer()
    return jsonify({'success': True, 'message': 'Timer triggered'})

@app.route('/api/stop_timer', methods=['POST'])
def stop_timer():
    """Stop the current timer"""
    success = timer.stop_timer()
    return jsonify({'success': success})

@app.route('/api/status')
def get_status():
    """Get current timer status"""
    return jsonify({
        'active': timer.countdown_active,
        'remaining_time': timer.remaining_time if timer.countdown_active else 0
    })

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'status': 'Connected to Rain Alert System'})
    
    # Send current status if timer is running
    if timer.countdown_active:
        is_safe = timer.remaining_time > timer.safe_time
        emit('timer_update', {
            'time': round(timer.remaining_time, 1),
            'safe': is_safe,
            'status': 'SAFE TIME' if is_safe else 'FIND SHELTER'
        })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('keyboard_trigger')
def handle_keyboard_trigger():
    """Handle keyboard shortcut trigger from client"""
    timer.trigger_rain_timer()

if __name__ == '__main__':
    print("Starting Rain Alert Timer Server...")
    print("Open http://localhost:5000 in your browser")
    print("Use hotkey_client.py for global shortcuts")
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
