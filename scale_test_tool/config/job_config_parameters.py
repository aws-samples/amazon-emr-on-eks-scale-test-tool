# Amazon EMR on EKS Job related configuration parameters

# IAM role Arn to run workloads on Amazon EMR on EKS
# Steps to create Job execution role:
# https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/creating-job-execution-role.html
# Format: arn:<AWS_PARTITION>:iam::<AWS_ACCOUNT_ID>:role/<JOB_EXECUTION_ROLE_NAME>
JOB_EXECUTION_ROLE_ARN = "<JOB_EXECUTION_ROLE_ARN>"

# We are using Sample Pi calculation job for a default scale test run.
# Please modify below parameters based on the Job that you may want to run as a part of scale test.
# Documentation - https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks-jobs-CLI.html#emr-eks-jobs-parameters

# This is the HCFS (Hadoop compatible file system) reference to the main jar/py file you want to run.
JOB_ENTRY_POINT = "local:///usr/lib/spark/examples/jars/spark-examples.jar"
# This is the argument you want to pass to your JAR. You should handle reading this parameter using your entry-point code.
JOB_ENTRY_POINT_ARGS = ["2"]
# These are the additional spark parameters you want to send to the job.
# Use this parameter to override default Spark properties such as driver memory or number of executors like —conf or —class
JOB_SPARK_SUBMIT_PARAMS = "--class org.apache.spark.examples.SparkPi " \
                                 "--conf spark.executor.instances=3 " \
                                 "--conf spark.executor.memory=3G " + \
                                 "--conf spark.executor.cores=1 " \
                                 "--conf spark.driver.cores=1 " + \
                                 "--conf spark.driver.memory=3G " \
                                 "--conf spark.kubernetes.allocation.batch.size=1000"

# Amazon EMR on EKS release version
# https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks-releases.html
RELEASE_LABEL = "emr-6.3.0-latest"

# Name of the Amazon Cloudwatch log group for publishing job logs.
# https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks-jobs-CLI.html#emr-eks-jobs-cloudwatch
CLOUD_WATCH_LOG_GROUP_NAME = "<CLOUD_WATCH_LOG_GROUP_NAME>"

# Amazon S3 bucket URI for publishing logs
# https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks-jobs-CLI.html#emr-eks-jobs-s3
# Format: "s3://path-to-log-bucket"
S3_LOG_PATH = "<S3_BUCKET_PATH>"

# Scale Test tool report local file path.
# After a successful execution of scale test, a folder "scale-test-output" will be created (only if it doesn't exist)
# at the path "<path-to-repo>/amazon-emr-on-eks-scale-test-tool/" and a file with prefix "scale-test-run-report" will be
# generated.
JOB_RUN_OUTPUT_FILE_PATH_PREFIX = "scale-test-output/scale-test-run-report"
