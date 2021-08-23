# (optional) manual configuration steps once scale test cluster has been set up #

## enable logs for coredns ##
open the coredns configMap for editing:
```
kubectl edit configmap coredns -n kube-system
```
then add a line containing just the string "log" as shown in the snippet of the 
configmap below:
```
data:
   Corefile: |
     .:53 {
         log
         errors
         health
```