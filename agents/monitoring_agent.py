import pandas as pd
from utils.logger import logger

class MonitoringAgent:
    def detect_alerts(self, latest_data: pd.Series):
        """
        Scans latest data for critical business alerts.
        """
        alerts = []
        
        try:
            # Alert 1: Low Sales
            if latest_data['sales'] < 5000:
                alerts.append("low_sales") # Using a simple tag as per pipeline requirement
                alerts.append(f"Low Sales Alert: {latest_data['sales']:.2f}")
            
            # Alert 2: High Growth
            if latest_data['growth_rate'] > 0.1:
                alerts.append(f"High Growth Opportunity: {latest_data['growth_rate']*100:.1f}%")
            
            # Alert 3: Declining Trend
            if latest_data['trend'] == -1:
                alerts.append("Declining Trend Warning: Negative sales movement detected.")
                
            logger.info(f"Monitoring Agent: {len(alerts)} alerts detected.")
            return alerts
            
        except Exception as e:
            logger.error(f"Monitoring Agent failed: {e}")
            return ["Monitoring Error"]

def get_alerts(latest_data):
    """
    Main entry point for external services to fetch monitoring alerts.
    """
    agent = MonitoringAgent()
    return agent.detect_alerts(latest_data)
