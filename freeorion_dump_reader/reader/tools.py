from datetime import datetime


def date_from_id(item_id):
    # Use constant form AI state
    return datetime.fromtimestamp((int(item_id, 16) / 1000) + 1433809768)

