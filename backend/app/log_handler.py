import logging
from collections import deque
from datetime import datetime


class LogBufferHandler(logging.Handler):
    def __init__(self, capacity=500):
        super().__init__()
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))

    def emit(self, record):
        try:
            entry = {
                "time": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
            }
            self.buffer.append(entry)
        except Exception:
            self.handleError(record)

    def get_logs(self, lines=100):
        return list(self.buffer)[-lines:]


log_buffer = LogBufferHandler(capacity=500)
