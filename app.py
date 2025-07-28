import keyboard
import requests
import time
import threading
import sys
import os

# Try to import notification, fallback if not available
try:
    from plyer import notification
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False
    print("Note: Install 'plyer' for system notifications: pip install plyer")

class GlobalHotkeyClient:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.is_running = True
        self.last_trigger = 0  # Prevent spam clicking
        
    def send_trigger(self):
        """Send trigger to web server"""
        # Prevent spam (max once per second)
        current_time = time.time()
        if current_time - self.last_trigger < 1.0:
            print("⚠ Too fast! Wait 1 second between triggers")
            return
        
        self.last_trigger = current_time
        
        try:
            print("🚀 Sending trigger...")
            response = requests.post(f"{self.server_url}/api/manual_trigger", timeout=3)
            if response.status_code == 200:
                print("✅ Timer started!")
                
                # Show system notification if available
                if HAS_NOTIFICATIONS:
                    notification.notify(
                        title="Rain Alert ⚡",
                        message="Timer started! Check your browser.",
                        timeout=2
                    )
            else:
                print(f"❌ Server error: {response.status_code}")
                
        except requests.exceptions.ConnectError:
            print("❌ Cannot connect to server. Is it running?")
            if HAS_NOTIFICATIONS:
                notification.notify(
                    title="Rain Alert Error",
                    message="Cannot connect to server",
                    timeout=2
                )
        except requests.exceptions.Timeout:
            print("❌ Server timeout")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        print("\n" + "="*50)
        print("🌧️  RAIN ALERT - GLOBAL HOTKEY CLIENT")
        print("="*50)
        print(f"📡 Server: {self.server_url}")
        print("\n⌨️  HOTKEYS:")
        print("   Ctrl+P     → Trigger timer")  
        print("   Ctrl+Alt+Q → Quit this app")
        print("\n✅ Ready! Hotkeys work from anywhere.")
        print("   Minimize this window and play your game!")
        print("\n" + "-"*50)
        
        # Main trigger hotkey - Ctrl+P
        keyboard.add_hotkey('ctrl+p', self.send_trigger, suppress=True)
        
        # Quit hotkey - Ctrl+Alt+Q  
        keyboard.add_hotkey('ctrl+alt+q', self.quit_app, suppress=True)
        
    def test_connection(self):
        """Test connection to server"""
        try:
            response = requests.get(f"{self.server_url}/api/status", timeout=3)
            if response.status_code == 200:
                print("✅ Connected to server!")
                return True
            else:
                print(f"⚠ Server responded with status: {response.status_code}")
                return False
        except requests.exceptions.ConnectError:
            print("❌ Cannot connect to server!")
            print(f"   Make sure server is running at: {self.server_url}")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def quit_app(self):
        """Quit the application"""
        print("\n👋 Shutting down global hotkey client...")
        self.is_running = False
        keyboard.unhook_all()
        sys.exit(0)
    
    def run(self):
        """Run the hotkey client"""
        try:
            # Test connection first
            if not self.test_connection():
                print("\n💡 Tips:")
                print("   1. Make sure your web server is running")
                print("   2. Check the server URL is correct")
                print("   3. Try opening the URL in your browser first")
                input("\nPress Enter to continue anyway or Ctrl+C to quit...")
            
            self.setup_hotkeys()
            
            # Keep the script running
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.quit_app()

if __name__ == "__main__":
    print("Starting Global Hotkey Client...")
    
    # Get server URL
    default_url = "http://localhost:5000"
    print(f"\nServer URL (press Enter for {default_url}):")
    server_url = input("> ").strip()
    
    if not server_url:
        server_url = default_url
    
    # Ensure URL has http://
    if not server_url.startswith(('http://', 'https://')):
        server_url = 'http://' + server_url
    
    client = GlobalHotkeyClient(server_url)
    client.run()
