import sys
import uuid
import logging
from locust import User, task, TaskSet, constant, events
from locust.exception import StopUser
from datetime import datetime, timezone
from scale_test_tool.helper.scale_test_output_generator import generate_report
from scale_test_tool.locust.scale_test import scale_test_instance as scale_test
from scale_test_tool.tasks.job_run_task import job_run_task
from scale_test_tool.tasks.virtual_cluster_task import virtual_cluster_task

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(funcName)s - %(levelname)s - %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

job_run_ids_list = []


# Create a Amazon EKS namespace and create a virtual cluster associated with that namespace
def _setup_virtual_cluster():
    scale_test.virtual_cluster_id = virtual_cluster_task.create_namespace_and_virtual_cluster(
        test_id=scale_test.test_id
    )
    logger.info(f"Created virtual cluster with id: {scale_test.virtual_cluster_id}")


# This method runs at the beginning of the test.
# Documentation - https://tiny.amazon.com/19eefihkj/docslocuioenstabwrit
# We can use this method to setup virtual cluster if it has not already been setup
@events.test_start.add_listener
def on_test_start(**kwargs):
    logger.info(f"Scale Test started with Test unique id {scale_test.test_id}")
    _setup_virtual_cluster()


# This method runs at the end of the test.
# Documentation - https://tiny.amazon.com/19eefihkj/docslocuioenstabwrit
# We can use this test to cleanup the virtual cluster and namespace
@events.test_stop.add_listener
def on_test_stop(**kwargs):
    # This is executed at the end of the test. Any cleanup code will go here.
    try:
        virtual_cluster_task.delete_virtual_cluster_namespace(
            virtual_cluster_id=scale_test.virtual_cluster_id,
            test_id=scale_test.test_id
        )
    except Exception as e:
        # If there is an error while deleting virtual cluster, we will log the error
        # but finish generating the job run report.
        logger.error(f"Exception occurred while deleting the virtual cluster "
                     f"with id: {scale_test.virtual_cluster_id} {e}")
    generate_report(
        job_run_ids_list=job_run_ids_list
    )
    logger.info("Scale Test stopped")


class ScaleTestUser(User):
    abstract = True

    def __init__(self, *args, **kwargs):
        super(ScaleTestUser, self).__init__(*args, **kwargs)

    # A User’s wait_time method is an optional attribute
    # used to determine how long a simulated user should wait between executing tasks.
    # Currently as we have only 1 task, this might not be very useful.
    wait_time = constant(1)


class ScaleTestUserTaskThread(ScaleTestUser):

    def __init__(self, *args, **kwargs):
        super(ScaleTestUserTaskThread, self).__init__(*args, **kwargs)

    @task
    def start_job_run(self) -> None:
        job_user_unique_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        logger.info(f"Job unique ID: {job_user_unique_id}")
        start_job_run_response = job_run_task.start_job_run(
            job_name=job_user_unique_id,
            virtual_cluster_id=scale_test.virtual_cluster_id
        )
        job_run_ids_list.append(start_job_run_response['id'])
        self.end_task()

    # Stop the user thread once the task completes.
    # User thread will continue running tasks unless stopped.
    def end_task(self) -> None:
        raise StopUser()
