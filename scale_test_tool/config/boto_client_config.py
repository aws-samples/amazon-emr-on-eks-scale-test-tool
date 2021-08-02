import boto3
import logging
from scale_test_tool.config.eks_cluster_config import REGION

logger = logging.getLogger(__name__)


class BotoClient:
    def __init__(self):
        # default session is limit to the profile or instance profile used,
        # We need to use the custom session to override the default session configuration
        boto_session = boto3.session.Session(region_name=REGION)
        self.emr_containers_client = boto_session.client('emr-containers')
        logger.info("Boto EMR containers client instantiated")

    def get_emr_containers_client(self):
        return self.emr_containers_client
