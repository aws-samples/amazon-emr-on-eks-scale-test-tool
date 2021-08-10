# This script uses eksctl to create an EKS cluster in a new VPC and configures it so that it can be used for scale
# testing. It is highly recommended to read closely this script and its dependent resources in order to understand
# what it does.
# This script does the following:
# - creates a job execution role. The ARN of this role is printed at the end of the script because this ARN needs to be
#   pasted into job_config_parameters.py
# - creates an EKS cluster using the configuration in resources/cluster_in_new_VPC.yaml
# - installs fluent bit on the EKS cluster, which writes all pod logs to cloudwatch logs under 3 log groups with
#   prefix /aws/containerinsights/${CLUSTER_NAME}. It can be very useful to have all pod logs available in cloudwatch
#   when doing scale testing. EKS also writes logs of system pods to cloudwatch log group /aws/eks/${CLUSTER_NAME}
#   more info: https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html
# - installs cluster-autoscaler
# - installs kubernetes dashboard
# - installs dns-autoscaler
# - installs cni-metrics-helper
# There are a few additional but optional manual configuration steps explained in
# additional_cluster_configuration_steps.md.

set -eu -o pipefail

# change these variables according to your needs ====================================================================
CLUSTER_NAME=
# aws region in which to create the cluster
REGION=
INSTANCE_TYPE=m5
INSTANCE_SIZE=xlarge
# if you intend to scale the cluster quickly to more than a few dozen nodes, it is recommended to put the fluent bit
# image in ECR then set this variable to the URI of the fluent bit image in ECR. If this variable is set, the
# script uses this ECR image. If the variable is not set, the script does not modify the fluent bit yaml file, which
# means the fluent bit image is pulled from Dockerhub (which can result in being throttled if the cluster is scaling up
# quickly). To put the image in ECR, pull it from Dockerhub then push it to an ECR repo in your AWS account.
FLUENT_BIT_ECR_IMAGE_URI=
# The following are reasonable CNI settings. CNI_MINIMUM_IP_TARGET should be increased if you run scale tests with
# higher pod density. More info about these settings: https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md
# If the subnets created by eksctl still do not provide enough addresses (by default eksctl creates a "/19" subnet which
# contains ~8.1k addresses for each nodegroup), you can configure CNI to take addresses from (larger) subnets that you create
# by following https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html
CNI_MINIMUM_IP_TARGET=7
CNI_WARM_IP_TARGET=2
# ===================================================================================================================

SCRIPT_FOLDER=$(dirname "$0")
BASE_FOLDER=$(dirname "$SCRIPT_FOLDER")

EMR_ON_EKS_JOB_EXECUTION_ROLE=$CLUSTER_NAME-job-execution-role

# create job execution role per: https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/creating-job-execution-role.html
EMR_ON_EKS_JOB_EXECUTION_ROLE_ARN=$(aws iam create-role --role-name $EMR_ON_EKS_JOB_EXECUTION_ROLE \
--assume-role-policy-document "file://${BASE_FOLDER}/resources/emr-trust-policy.json" \
--query 'Role.Arn')
echo "created job execution role with ARN $EMR_ON_EKS_JOB_EXECUTION_ROLE_ARN"
aws iam put-role-policy --role-name $EMR_ON_EKS_JOB_EXECUTION_ROLE \
--policy-name EMR-Containers-Job-Execution \
--policy-document "file://${BASE_FOLDER}/resources/EMRContainers-JobExecutionRole.json"

echo "going to create EKS cluster $CLUSTER_NAME"
sed "s/REGION/$REGION/g; s/MY_CLUSTER_NAME/$CLUSTER_NAME/g; s/INSTANCE_TYPE/$INSTANCE_TYPE/g; s/INSTANCE_SIZE/$INSTANCE_SIZE/g" \
"$BASE_FOLDER"/resources/cluster_in_new_VPC.yaml \
|  eksctl create cluster -f -

# update trust policy of the IAM role that was just created so that it can be used with all namespaces of this cluster.
# It would be cleaner to do this on a per-namespace basis (instead of "*") but that would require creating a new
# IAM role for every namespace because only 4 namespaces can be associated with an IAM role because IAM roles have a
# character limit on the size of trust policies.
aws emr-containers update-role-trust-policy \
    --cluster-name $CLUSTER_NAME \
    --role-name $EMR_ON_EKS_JOB_EXECUTION_ROLE \
    --namespace "*" \
    --region $REGION

echo "going to install cluster autoscaler"
# READ THE COMMENTS AT THE TOP OF resources/cluster-autoscaler-autodiscover.yaml
sed "s/MY_CLUSTER_NAME/$CLUSTER_NAME/g" "$BASE_FOLDER"/resources/cluster-autoscaler-autodiscover.yaml \
| kubectl apply -f -

echo "going to install fluent bit"
# install fluent bit per https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-logs-FluentBit.html
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml
ClusterName=$CLUSTER_NAME
RegionName=$REGION
FluentBitHttpPort='2020'
FluentBitReadFromHead='Off'
[[ ${FluentBitReadFromHead} = 'On' ]] && FluentBitReadFromTail='Off'|| FluentBitReadFromTail='On'
[[ -z ${FluentBitHttpPort} ]] && FluentBitHttpServer='Off' || FluentBitHttpServer='On'
kubectl create configmap fluent-bit-cluster-info \
--from-literal=cluster.name=${ClusterName} \
--from-literal=http.server=${FluentBitHttpServer} \
--from-literal=http.port=${FluentBitHttpPort} \
--from-literal=read.head=${FluentBitReadFromHead} \
--from-literal=read.tail=${FluentBitReadFromTail} \
--from-literal=logs.region=${RegionName} -n amazon-cloudwatch

if [ -n "${FLUENT_BIT_ECR_IMAGE_URI}" ]; then
   yq e "select(.kind == \"DaemonSet\" and .metadata.name == \"fluent-bit\").spec.template.spec.containers.[].image |= \"${FLUENT_BIT_ECR_IMAGE_URI}\"" "$BASE_FOLDER"/resources/fluent-bit.yaml \
   | kubectl apply -f -
else
   kubectl apply -f "$BASE_FOLDER"/resources/fluent-bit.yaml
fi

echo "going to install dns autoscaler"
# READ THE COMMENTS AT THE TOP OF resources/dns-horizontal-autoscaler.yaml
kubectl apply -f "$BASE_FOLDER"/resources/dns-horizontal-autoscaler.yaml

echo "going to install kubernetes dashboard"
# instructions for viewing the dashboard in your browser: https://docs.aws.amazon.com/eks/latest/userguide/dashboard-tutorial.html
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.5/aio/deploy/recommended.yaml

echo "going to install cni metrics helper"
# CNI metrics helper sends to cloudwatch metrics about IP address usage, ENI usage, and CNI errors
# https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html
# Note: the metrics published to cloudwatch will have a dimension called CLUSTER_ID whose value includes--in addition
# to the cluster name--the name of the nodegroup of the node that the cni-metrics-helper deployment is running on.
# But the metrics published are for the entire cluster, not just whichever nodegroup the deployment ends up on.
# This means that during the life of a cluster, the metric may be published using different dimension values if the
# cni-metrics-helper pod terminates and is started up again in a different nodegroup
# The node roles must have the cloudwatch:PutMetricData permission for this to work
kubectl apply -f https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/master/config/v1.7/cni-metrics-helper.yaml

kubectl set env daemonset aws-node -n kube-system MINIMUM_IP_TARGET=$CNI_MINIMUM_IP_TARGET
kubectl set env daemonset aws-node -n kube-system WARM_IP_TARGET=$CNI_WARM_IP_TARGET

echo "ARN of job execution role created by this script: $EMR_ON_EKS_JOB_EXECUTION_ROLE_ARN"
