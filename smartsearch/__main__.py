from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from smartsearch.config import Config


config = Config()
interface = config.get_interface()

interface.doc_selector.refresh_data()

scheduler = BackgroundScheduler()
scheduler.add_job(func=interface.doc_selector.refresh_data(), trigger="interval", minutes=config.data_refresh_minutes)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

interface()
