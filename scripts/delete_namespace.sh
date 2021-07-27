#!/bin/bash

readonly NAMESPACE=$1

# delete namespace
kubectl delete namespace $NAMESPACE

