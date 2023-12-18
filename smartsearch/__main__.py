from apscheduler.schedulers.background import BackgroundScheduler
import argparse
import atexit
from smartsearch.config import Config
from smartsearch.retrievers import Retriever
from smartsearch.docselector import DocSelector


def parse_cli_args():
    parser = argparse.ArgumentParser()
    _config = Config(validate=False)
    for arg, val in vars(_config).items():
        arg_type = type(val) if val is not None else str
        parser.add_argument(f"--{arg}", type=arg_type, help=_config.help_message(arg))
    return parser.parse_args()


args = parse_cli_args()
config = Config(args)


def refresh_data():
    retriever = Retriever(config)
    retriever.fetch_docs()
    retriever.scrape_docs()
    DocSelector(config).fetch_doc_embeddings()


refresh_data()
scheduler = BackgroundScheduler()
scheduler.add_job(func=refresh_data, trigger="interval", minutes=config.data_refresh_minutes)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

interface = config.get_interface()
interface()
