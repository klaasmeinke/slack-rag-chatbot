from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from smartsearch.config import Config
from smartsearch.retrievers.slack import SlackRetriever

config = Config()

retriever = SlackRetriever(config)
retriever.fetch_docs()
retriever.scrape_docs()

for doc in retriever.docs.values():
    print(doc)

# interface = config.get_interface()
#
# interface.refresh_data()


# scheduler = BackgroundScheduler()
# scheduler.add_job(func=interface.refresh_data(), trigger="interval", minutes=config.data_refresh_minutes)
# scheduler.start()
# atexit.register(lambda: scheduler.shutdown())
#
# interface()
