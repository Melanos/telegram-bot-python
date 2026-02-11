"""Stock price alert management and monitoring."""
import json
import os
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime
from config import DATA_DIR
from api_handlers import get_stock_price
import yfinance as yf


# Alert storage
ALERTS_FILE = f"{DATA_DIR}/alerts.json"


class AlertManager:
    """Manages stock price alerts with persistent storage."""
    
    def __init__(self):
        """Initialize alert manager and load existing alerts."""
        self.alerts: List[Dict] = []
        self.load_alerts()
    
    def add_alert(self, user_id: int, symbol: str, target_price: float, 
                  condition: str = "above") -> Dict:
        """
        Add a new price alert.
        
        Args:
            user_id: Telegram user ID
            symbol: Stock ticker symbol
            target_price: Price to trigger alert
            condition: 'above' or 'below'
            
        Returns:
            Dictionary with success status and message
        """
        symbol = symbol.upper().strip()
        
        # Validate symbol exists
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.info.get("regularMarketPrice") or ticker.info.get("currentPrice")
            if current_price is None:
                return {"success": False, "message": f"Invalid symbol: {symbol}"}
        except Exception as e:
            return {"success": False, "message": f"Could not validate {symbol}: {str(e)}"}
        
        # Check for duplicate
        for alert in self.alerts:
            if (alert["user_id"] == user_id and 
                alert["symbol"] == symbol and 
                alert["target_price"] == target_price):
                return {"success": False, "message": f"Alert already exists for {symbol} at ${target_price}"}
        
        # Create alert
        alert = {
            "user_id": user_id,
            "symbol": symbol,
            "target_price": target_price,
            "condition": condition,
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        
        self.alerts.append(alert)
        self.save_alerts()
        
        return {
            "success": True,
            "message": f"✅ Alert set: {symbol} {condition} ${target_price:.2f}\n"
                      f"Current price: ${current_price:.2f}",
            "current_price": current_price
        }
    
    def remove_alert(self, user_id: int, symbol: str) -> Dict:
        """
        Remove alert for a specific symbol.
        
        Args:
            user_id: Telegram user ID
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary with success status and message
        """
        symbol = symbol.upper().strip()
        initial_count = len(self.alerts)
        
        self.alerts = [
            a for a in self.alerts 
            if not (a["user_id"] == user_id and a["symbol"] == symbol)
        ]
        
        removed = initial_count - len(self.alerts)
        
        if removed > 0:
            self.save_alerts()
            return {"success": True, "message": f"✅ Removed {removed} alert(s) for {symbol}"}
        else:
            return {"success": False, "message": f"No alerts found for {symbol}"}
    
    def get_user_alerts(self, user_id: int) -> List[Dict]:
        """
        Get all alerts for a specific user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of alert dictionaries
        """
        return [a for a in self.alerts if a["user_id"] == user_id and not a["triggered"]]
    
    def save_alerts(self):
        """Save alerts to JSON file."""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(ALERTS_FILE, "w") as f:
            json.dump(self.alerts, f, indent=2)
        print(f"✅ Saved {len(self.alerts)} alerts to {ALERTS_FILE}")
    
    def load_alerts(self):
        """Load alerts from JSON file."""
        if os.path.exists(ALERTS_FILE):
            try:
                with open(ALERTS_FILE, "r") as f:
                    self.alerts = json.load(f)
                print(f"✅ Loaded {len(self.alerts)} alerts from {ALERTS_FILE}")
            except Exception as e:
                print(f"⚠️ Error loading alerts: {e}")
                self.alerts = []
        else:
            print(f"ℹ️ No alerts file found, starting fresh")
            self.alerts = []


def check_alerts(alert_manager: AlertManager, bot, check_interval: int = 300):
    """
    Background thread to check stock prices against alerts.
    
    Args:
        alert_manager: AlertManager instance
        bot: Telegram bot instance
        check_interval: Seconds between checks (default 300 = 5 minutes)
    """
    print(f"🔔 Alert monitoring started (checking every {check_interval}s)")
    
    while True:
        try:
            active_alerts = [a for a in alert_manager.alerts if not a["triggered"]]
            
            if not active_alerts:
                time.sleep(check_interval)
                continue
            
            # Group alerts by symbol to minimize API calls
            symbols = list(set(a["symbol"] for a in active_alerts))
            
            for symbol in symbols:
                try:
                    # Fetch current price
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    current_price = info.get("regularMarketPrice") or info.get("currentPrice")
                    
                    if current_price is None:
                        print(f"⚠️ Could not fetch price for {symbol}")
                        continue
                    
                    # Check each alert for this symbol
                    for alert in active_alerts:
                        if alert["symbol"] != symbol:
                            continue
                        
                        triggered = False
                        
                        if alert["condition"] == "above" and current_price >= alert["target_price"]:
                            triggered = True
                        elif alert["condition"] == "below" and current_price <= alert["target_price"]:
                            triggered = True
                        
                        if triggered:
                            # Send notification
                            message = (
                                f"🚨 PRICE ALERT!\n\n"
                                f"{symbol} is now ${current_price:.2f}\n"
                                f"Target: {alert['condition']} ${alert['target_price']:.2f}\n\n"
                                f"Alert triggered! ✅"
                            )
                            
                            try:
                                bot.send_message(alert["user_id"], message)
                                print(f"✅ Alert sent to user {alert['user_id']}: {symbol} @ ${current_price:.2f}")
                                
                                # Mark as triggered
                                alert["triggered"] = True
                                alert["triggered_at"] = datetime.now().isoformat()
                                alert["triggered_price"] = current_price
                                
                            except Exception as e:
                                print(f"❌ Failed to send alert to user {alert['user_id']}: {e}")
                    
                    # Small delay between symbols
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Error checking {symbol}: {e}")
            
            # Save after checking all alerts
            alert_manager.save_alerts()
            
            # Wait before next check cycle
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"❌ Alert monitoring error: {e}")
            time.sleep(check_interval)


def start_alert_monitoring(alert_manager: AlertManager, bot, check_interval: int = 300):
    """
    Start background alert monitoring thread.
    
    Args:
        alert_manager: AlertManager instance
        bot: Telegram bot instance
        check_interval: Seconds between checks
    """
    monitor_thread = threading.Thread(
        target=check_alerts,
        args=(alert_manager, bot, check_interval),
        daemon=True
    )
    monitor_thread.start()
    print("🚀 Stock alert monitoring thread started")
