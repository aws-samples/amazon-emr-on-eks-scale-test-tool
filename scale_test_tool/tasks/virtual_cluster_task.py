import subprocess
import time
from scale_test_tool.helper.emr_container_helper import *
from scale_test_tool.locust.scale_test import scale_test_instance as scale_test

JOB_RUNNING_STATES = ['PENDING', 'SUBMITTED', 'RUNNING']


class VirtualClusterTask:
    #
    # VirtualClusterTask class has methods that will help with virtual cluster creation
    # and deletion
    #
    def __init__(self, emr_containers_client):
        self.emr_containers_client = emr_containers_client

    def create_namespace_and_virtual_cluster(self, test_id):
        # Creating namespace in EKS cluster
        kubernetes_ns = self._generate_namespace_name(test_id)
        subprocess.run(["sh", "scripts/create_new_namespace_setup_emr_on_eks.sh",
                        REGION, EKS_CLUSTER_NAME, kubernetes_ns])
        # Creating virtual cluster
        virtual_cluster_name = self._generate_virtual_cluster_name(test_id)
        create_virtual_cluster_response = create_virtual_cluster(
            client=self.emr_containers_client,
            client_token=test_id,
            virtual_cluster_name=virtual_cluster_name,
            eks_cluster_name=EKS_CLUSTER_NAME,
            k8s_namespace=kubernetes_ns)
        return create_virtual_cluster_response['id']

    def delete_virtual_cluster_namespace(self, virtual_cluster_id, test_id):
        ready_for_cleanup = self._is_virtual_cluster_ready_for_cleanup(virtual_cluster_id)
        while ready_for_cleanup is False:
            logger.info(f"Waiting for all jobs to terminate in Virtual Cluster {virtual_cluster_id}")
            time.sleep(10)
            ready_for_cleanup = self._is_virtual_cluster_ready_for_cleanup(virtual_cluster_id)

        logger.info(f"No running jobs, {virtual_cluster_id} can be now terminated")
        delete_virtual_cluster(
            client=self.emr_containers_client,
            virtual_cluster_id=virtual_cluster_id
        )
        logger.info(f"Virtual cluster {virtual_cluster_id} has been terminated")
        kubernetes_ns = self._generate_namespace_name(test_id)
        subprocess.run(["sh", "scripts/delete_namespace.sh", kubernetes_ns])
        logger.info(f"Namespace {kubernetes_ns} has been Deleted")

    def _is_virtual_cluster_ready_for_cleanup(self, virtual_cluster_id):
        list_job_run_response = list_job_run_in_running_state(
            client=self.emr_containers_client,
            virtual_cluster_id=virtual_cluster_id,
            states_list=JOB_RUNNING_STATES
        )
        if list_job_run_response['jobRuns']:
            return False
        return True

    def _generate_namespace_name(self, test_id):
        return f"{test_id}-ns"

    def _generate_virtual_cluster_name(self, test_id):
        return f"{test_id}-vc"


virtual_cluster_task = VirtualClusterTask(scale_test.emr_containers_client)
