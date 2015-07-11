from datetime import datetime


def date_from_uid(uid):
    # Use constant form AI state
    return datetime.fromtimestamp((int(uid, 16) / 1000) + 1433809768)

