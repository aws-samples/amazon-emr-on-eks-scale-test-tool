# amazon-emr-on-eks-scale-test-tool #
Amazon EMR on EKS Scale Test tool allows users to submit sample/custom Spark jobs at scale to an EMR on EKS Virtual Cluster. 
Users can customize the job and the job submission rate. The tool summarizes the results of the scale test in a CSV file containing information about every job submitted during test execution.

## Pre-requisites ##

### Create a cluster for scale testing ###
you can create a cluster that is configured for scaling by modifying the variables in `scripts/create_cluster_for_scale_test.sh` (eg cluster name and aws region) then running this script.
You can skip this step if you already have a cluster setup for scale testing. After creating the cluster, take a look 
at the (optional) additional manual configuration steps described in
`resources/additional_cluster_configuration_steps.md`. `create_cluster_for_scale_test.sh` uses kubectl
and eksctl, which can be installed using `installation.sh` (described below)

### Create Job Execution Role ###
Steps to create Job execution role: https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/creating-job-execution-role.html
This is not necessary if you created a cluster using the `create_cluster_for_scale_test.sh` script because this script creates a job execution role and prints the ARN to stdout.
If you need to add permissions to the job execution role created by `create_cluster_for_scale_test.sh`, add the permissions to `resources/EMRContainers-JobExecutionRole.json`

### Setup Cloud9 Environment (This step is optional) ###

This step can be ignored if we are running scale test tool on another machine or locally on mac.
https://docs.aws.amazon.com/cloud9/latest/user-guide/create-environment.html

### Run the installation script. ### 
1. Change variable CLUSTER_NAME to the Scale test EKS cluster in the `installation.sh` file. 
1. Run the installation script
- ```cd scripts/```
- ```chmod +x installation.sh``` (Make the script executable)
- ```./installation.sh``` (Run the installation script)

**Note: This script needs to be run only once before running the scale test to install all the pre-requisite tools required to run the
 tests.**


**This script will download and install the following things:**

1. Install python3. This is pre-installed in cloud9 environment
1. Install boto3 client. This is pre-installed in cloud9 environment
1. Install AWS CLI. This is pre-installed in cloud9 environment
1. Install locust, install python kubernetes client.
1. Install Kubectl for Linux
1. Install eksctl
1. Install Kubernetes client 
1. Update kubeconfig
1. Install helm for prometheus and grafana
1. Add prometheus Helm repo and install prometheus in the EKS cluster
1. Add grafana Helm repo and install Grafana
1. After the installation is complete, command to get the Grafana ELB URL will be executed.
This should print the web url of the ELB and we access Grafana web UI from a web browser.
Use the username "admin" to login. After the web url, password for Grafana UI 
will also be printed on the console 
 
## Run the scale test ##
### Configure cluster config file and locust
1. Set the variables in `scale_test_tool/config/eks_cluster_config.py` 
   - EKS_CLUSTER_NAME
   - AWS REGION 
1. Set the variables in `scale_test_tool/config/job_config_parameters.py` 
   - JOB_EXECUTION_ROLE_ARN, CLOUD_WATCH_LOG_GROUP_NAME, S3_LOG_PATH
   - Optionally, override the various job config parameters in order to have the scale test run your own job. The default configuration will run the example SparkPi Job that is bundled with Spark.

Configure the locust file at path `scale_test_tool/locust/locust.conf`:
1. Configure ```users``` parameter based on the number of Jobs that should run as a part of scale test.
1. Configure ```spawn-rate ``` parameter which determines at what rate per second the job threads should be spawned
1. Configure ```run-time``` which determines the total runtime of the Scale test

Details about how to configure these parameters has been mentioned in the ```locust.conf``` file.
There are other parameters as well which can be configured as per the requirement. More details in the ```locust.conf``` file.

### Run the scale test
```
cd ~/<Path to github repository>/

locust  --config=scale_test_tool/locust/locust.conf 
```
