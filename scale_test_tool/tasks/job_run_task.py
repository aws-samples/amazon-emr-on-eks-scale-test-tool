from scale_test_tool.helper.emr_container_helper import *
from scale_test_tool.locust.scale_test import scale_test_instance as scale_test

JOB_TERMINAL_STATES = ['FAILED', 'CANCELLED', 'COMPLETED']
JOB_POLL_SECONDS = 60


class JobRunTask:
    #
    # JobRunTask class methods that will help with jobs creation
    #
    def __init__(self, emr_containers_client):
        self.emr_containers_client = emr_containers_client

    def start_job_run(self, job_name, virtual_cluster_id):
        job_response = submit_job(
            client=self.emr_containers_client,
            job_name=job_name,
            client_token=job_name,
            entry_point=JOB_ENTRY_POINT,
            entry_point_arguments=JOB_ENTRY_POINT_ARGS,
            spark_submit_params=JOB_SPARK_SUBMIT_PARAMS,
            virtual_cluster_id=virtual_cluster_id
        )
        logger.info(f"Started job with id: {job_response['id']}")
        return job_response


job_run_task = JobRunTask(scale_test.emr_containers_client)
