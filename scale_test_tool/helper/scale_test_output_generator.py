import csv
import logging
import os
from scale_test_tool.config.job_config_parameters import JOB_RUN_OUTPUT_FILE_PATH_PREFIX
from scale_test_tool.helper.emr_container_helper import describe_job
from scale_test_tool.locust.scale_test import scale_test_instance as scale_test

logger = logging.getLogger(__name__)


def generate_report(job_run_ids_list):
    # Append unique test_id to the job run output file path.
    # Example report name: "scale-test-run-report-20210524-54da474e.csv"
    report_file_path = f"{JOB_RUN_OUTPUT_FILE_PATH_PREFIX}-{scale_test.test_id}.csv"
    write_job_run_report_header(report_file_path=report_file_path)
    for job_run_id in job_run_ids_list:
        logger.info(f"writing output for job-id {job_run_id}")
        job_run = describe_job(
            client=scale_test.emr_containers_client,
            virtual_cluster_id=scale_test.virtual_cluster_id,
            job_id=job_run_id
        )
        write_job_run_entry_to_csv(
            job_run=job_run,
            report_file_path=report_file_path
        )

    logger.info(f"Successfully generated jobRuns report at filepath "
                f"{report_file_path}")


def write_job_run_entry_to_csv(job_run, report_file_path):
    with open(report_file_path, mode='a') as csv_file:
        fieldnames = ['job_id', 'virtual_cluster_id', 'state', 'state_details', 'job_created_at',
                      'job_finished_at', 'job_latency']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(extract_job_run_report_data(job_run=job_run))


def extract_job_run_report_data(job_run):
    created_at = job_run['createdAt']
    finished_at = job_run['finishedAt']
    timedelta = (finished_at - created_at).total_seconds()
    return {'job_id': job_run['id'], 'virtual_cluster_id': job_run['virtualClusterId'], 'state': job_run['state'],
            'state_details': job_run['stateDetails'], 'job_created_at': job_run['createdAt'],
            'job_finished_at': job_run['finishedAt'], 'job_latency': timedelta}


def write_job_run_report_header(report_file_path):
    os.makedirs(os.path.dirname(report_file_path), exist_ok=True)
    with open(report_file_path, mode='w') as csv_file:
        fieldnames = ['job_id', 'virtual_cluster_id', 'state', 'state_details', 'job_created_at',
                      'job_finished_at', 'job_latency']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
