import logging

filename = "/home/adminas/Documents/teltonika.log"
encoding = "utf-8"
logFormatter = "%(asctime)s:%(message)s"
logging.basicConfig(format=logFormatter, level=logging.INFO)
logger = logging.getLogger(__name__)
