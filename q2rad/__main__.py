from q2rad.q2rad import Q2RadApp
import logging
_logger = logging.getLogger(__name__)

try:
    app = Q2RadApp("q2RAD")
    app.run()
except Exception as e:
    logging.exception("message")
