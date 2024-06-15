import logging
import __main__
import datetime
import sys
import os

try:
    PREFIX = os.path.basename(__main__.__file__)
except:
    PREFIX = "ipythonNB"
    # main file not set by ipynb, no time to think of ergonomic solution

LOG_PATH = "../logs/"
LOG_NAME = f"{PREFIX}_{datetime.datetime.now().date()}"


logFormatter = logging.Formatter(
    "%(asctime)s [%(levelname)-5.5s]  %(message)s"  # [%(threadName)-12.12s]
)
logger = logging.getLogger(PREFIX)

fileHandler = logging.FileHandler(
    "{0}/{1}.log".format(LOG_PATH, LOG_NAME),
    mode="a+",
)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)
logger.info("\n\n>>>>> start execution")
