import logging
from botocore.exceptions import ClientError
from scale_test_tool.config.job_config_parameters import *
from scale_test_tool.config.eks_cluster_config import *

logger = logging.getLogger(__name__)


# Create EMR on EKS Virtual Cluster
def create_virtual_cluster(client,
                           client_token,
                           virtual_cluster_name,
                           k8s_namespace,
                           eks_cluster_name=EKS_CLUSTER_NAME):
    response = client.create_virtual_cluster(
        name=virtual_cluster_name,
        containerProvider={
            'type': 'EKS',
            'id': eks_cluster_name,
            'info': {
                'eksInfo': {
                    'namespace': k8s_namespace
                }
            }
        },
        clientToken=client_token
    )
    return response


# Delete EMR on EKS virtual cluster
def delete_virtual_cluster(client, virtual_cluster_id):
    response = client.delete_virtual_cluster(
        id=virtual_cluster_id
    )
    return response


def list_job_run_in_running_state(client, virtual_cluster_id, states_list):
    response = client.list_job_runs(
        virtualClusterId=virtual_cluster_id,
        states=states_list
    )
    return response


# Submit EMR on EKS job with required parameters
def submit_job(client,
               job_name, client_token,
               entry_point, entry_point_arguments, spark_submit_params,
               virtual_cluster_id):
    response = client.start_job_run(
        name=job_name,
        virtualClusterId=virtual_cluster_id,
        clientToken=client_token,
        executionRoleArn=JOB_EXECUTION_ROLE_ARN,
        releaseLabel=RELEASE_LABEL,
        jobDriver={
            "sparkSubmitJobDriver": {
                "entryPoint": entry_point,
                "entryPointArguments": entry_point_arguments,
                "sparkSubmitParameters": spark_submit_params
            }
        },
        configurationOverrides={
            "monitoringConfiguration": {
                "cloudWatchMonitoringConfiguration": {
                    "logGroupName": CLOUD_WATCH_LOG_GROUP_NAME,
                    "logStreamNamePrefix": job_name
                },
                "s3MonitoringConfiguration": {
                    "logUri": S3_LOG_PATH
                }
            }
        }
    )
    return response


# Describe EMR on EKS job run
def describe_job(client, job_id, virtual_cluster_id):
    try:
        response = client.describe_job_run(
            id=job_id,
            virtualClusterId=virtual_cluster_id
        )
        return response['jobRun']
    except ClientError as error:
        logger.error(f"{error.response['Error']['Code']} occurred while describing the job")
        return None


# Describe virtual cluster
def describe_virtual_cluster(client, virtual_cluster_id):
    response = client.describe_virtual_cluster(
        id=virtual_cluster_id
    )
    return response['virtualCluster']
