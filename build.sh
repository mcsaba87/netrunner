#!/bin/bash

ROUTERBOARD_IP="192.168.74.7"
DELAY=2;
REGISTRY="docker-registry:5000"
TAG="armv7"
ARCH="linux/arm/v7" # linux/arm/v7, linux/arm64, linux/amd64

rm /tmp/netrunner.tar 2>/dev/null

echo "Building image..."
podman build   --platform ${ARCH}   --network host -t netrunner:${TAG} .
echo "Pushing image..."
podman push --tls-verify=false netrunner:${TAG} ${REGISTRY}/netrunner/netrunner:${TAG}


# Deployment

echo "Fetching image..."
podman save --format docker-archive netrunner:${TAG} > /tmp/netrunner.tar

echo "uploading image..."
scp /tmp/netrunner.tar  admin@192.168.74.7:usb1-part1/netrunner.tar

echo "Stopping containers..."
ssh admin@${ROUTERBOARD_IP} '/container/stop [ find ]'
sleep 20

echo "Removing containers..."
ssh admin@${ROUTERBOARD_IP} '/container/remove [ find ]'
sleep ${DELAY}

echo "Cleaning up filesystem..."
ssh admin@${ROUTERBOARD_IP} '/file/remove usb1-part1/netrunner'

echo "Creating container..."
ssh admin@${ROUTERBOARD_IP} '/container add cmd="/entrypoint.sh" file=usb1-part1/netrunner.tar interface=veth1 name=netrunner root-dir=usb1-part1/tmp envlist=netrunner'
ssh admin@${ROUTERBOARD_IP} '/container print'
sleep 20

echo "Starting container..."
ssh admin@${ROUTERBOARD_IP} '/container start 0'
