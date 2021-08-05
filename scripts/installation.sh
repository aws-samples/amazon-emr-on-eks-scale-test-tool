# Set these variables before running the script
CLUSTER_NAME="<EKS_CLUSTER_NAME>"

echo "- - - - - - - -  Installing Python3 - - - - - - - - - - - "
# Install python3
sudo yum -y install python3

echo "- - - - - - - -  Installing AWS CLI - - - - - - - - - - - "
# Install AWS CLI. This is pre-installed in cloud9 environment
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

echo "- - - - - - - -  Installing Boto3 - - - - - - - - - - - "
# Install boto3 client
sudo pip3 install boto3

echo "- - - - - - - -  Installing Locust - - - - - - - - - - - "
# Install locust, install kubernetes client
sudo pip3 install locust

echo "- - - - - - - -  Installing Kubectl - - - - - - - - - - - "
# Install Kubectl for Linux
echo "Installing Kubectl to the machine"
curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.20.4/2021-04-12/bin/linux/amd64/kubectl
curl -o kubectl.sha256 https://amazon-eks.s3.us-west-2.amazonaws.com/1.20.4/2021-04-12/bin/linux/amd64/kubectl.sha256
openssl sha1 -sha256 kubectl
chmod +x ./kubectl
mkdir -p $HOME/bin && cp ./kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
kubectl version --short --client
echo "Kubectl has been successfully installed to the machine"

echo "- - - - - - - -  Installing eksctl - - - - - - - - - - - "
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version

echo "- - - - - - - -  Installing python kubernetes-client - - - - - - - - - - - "
# Install Kubernetes client
sudo pip3 install kubernetes

echo "- - - - - - - -  Adding $CLUSTER_NAME EKS cluster to kubeconfig - - - - - - - - - - - "
# Update kubeconfig
aws eks update-kubeconfig --name $CLUSTER_NAME

echo "- - - - - - - -  Install helm - - - - - - - - - - - "
# Install helm, install prometheus, install grafana
curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

echo "- - - - - - - -  Installing Prometheus - - - - - - - - - - - "
# Add prometheus Helm repo and install prometheus in the EKS cluster
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
kubectl create namespace prometheus

helm install prometheus prometheus-community/prometheus \
    --namespace prometheus \
    --set alertmanager.persistentVolume.storageClass="gp2" \
    --set server.persistentVolume.storageClass="gp2" \
    --set storage.tsdb.retention.time="2d"

sleep 30s

echo "- - - - - - - -  Installing Grafana - - - - - - - - - - - "
# add grafana Helm repo
helm repo add grafana https://grafana.github.io/helm-charts
mkdir ~/environment/grafana -p
# Install grafana
cat << EoF > ${HOME}/environment/grafana/grafana.yaml
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-server.prometheus.svc.cluster.local
      access: proxy
      isDefault: true
EoF


kubectl create namespace grafana
helm install grafana grafana/grafana \
    --namespace grafana \
    --set persistence.storageClassName="gp2" \
    --set persistence.enabled=true \
    --set adminPassword='EKS!sAWSome' \
    --values ${HOME}/environment/grafana/grafana.yaml \
    --set service.type=LoadBalancer

sleep 60s

echo "- - - - - - - -  Extracting Grafana Url - - - - - - - - - - - "
# Get Grafana ELB URL using this command.
# Copy & Paste the value into browser to access Grafana web UI.
export ELB=$(kubectl get svc -n grafana grafana -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "http://$ELB"

# # When logging in, use the username admin and get the password hash by running the following:
kubectl get secret --namespace grafana grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
