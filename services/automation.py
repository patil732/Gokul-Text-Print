from apscheduler.schedulers.background import BackgroundScheduler
from services.decision_pipeline import run_pipeline
from database.db import get_db_connection
from utils.logger import logger
import datetime

def log_decision_to_db(result):
    """
    Saves the automated decision results into the SQLite history table.
    """
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO decision_history (decision, confidence, reason)
            VALUES (?, ?, ?)
        ''', (
            result.get('decision'),
            result.get('confidence'),
            result.get('reasons')[0] if result.get('reasons') else "No driver data"
        ))
        conn.commit()
        conn.close()
        logger.info(f"Automation: Logged decision '{result.get('decision')}' to history.")
    except Exception as e:
        logger.error(f"Automation: Failed to log decision: {e}")

def automated_job():
    """
    The background task that runs the AI pipeline, logs results, and triggers alerts.
    """
    logger.info("Automation: Running scheduled AI Decision Pipeline...")
    result = run_pipeline()
    
    if "error" in result:
        logger.error(f"Automation Task Failed: {result['error']}")
        return

    # 1. Log to Database
    log_decision_to_db(result)
    
    # 2. Automated Alerts
    for alert in result.get('alerts', []):
        logger.warning(f"SYSTEM ALERT: {alert}")
        # Here you could trigger email/Slack notifications
        
    logger.info(f"Automation Task Completed successfully at {datetime.datetime.now()}")

def start_scheduler():
    """
    Initializes and starts the background scheduler.
    """
    scheduler = BackgroundScheduler()
    # Run every 5 minutes
    scheduler.add_job(func=automated_job, trigger="interval", minutes=5)
    scheduler.start()
    logger.info("Background Scheduler started: AI decisions every 5 minutes.")
    
    # Run once immediately on start
    automated_job()
