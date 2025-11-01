#!/bin/bash
# CIN Server Emulation Installer - Bash Version
UBUNTU_VERSION="22.04"
CUSTOM_IMAGE_REGISTRY=""

WORKDIR="/opt/serve-emulation"
mkdir -p "$WORKDIR"
cd "$WORKDIR" || exit 1

command -v docker >/dev/null 2>&1 || {
  echo "[!] Docker not found. Installing..."
  apt update && apt install -y docker.io
}

if [[ -n "$CUSTOM_IMAGE_REGISTRY" ]]; then
    docker pull "${CUSTOM_IMAGE_REGISTRY}/ubuntu:$UBUNTU_VERSION"
else
    docker pull "ubuntu:$UBUNTU_VERSION"
fi

docker run -dit --name cin_emulator --hostname cin-core ubuntu:$UBUNTU_VERSION
docker exec -it cin_emulator bash
