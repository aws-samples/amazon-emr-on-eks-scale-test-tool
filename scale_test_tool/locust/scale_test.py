from datetime import datetime, timezone
import uuid
from scale_test_tool.config.boto_client_config import BotoClient


def _setup_unique_test_id():
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d')}" \
           f"-{str(uuid.uuid4())[:8]}"


class ScaleTest:
    #
    # This class initializes clients and variables that will be shared across the Users
    # We will create a singleton of this class and will be used while running test jobs.
    #
    def __init__(self):
        boto = BotoClient()
        self.emr_containers_client = boto.get_emr_containers_client()
        self.virtual_cluster_id = None
        self.test_id = _setup_unique_test_id()


scale_test_instance = ScaleTest()
