#!/bin/bash
# Cloud Server Setup Script for DigitalOcean Droplet

echo "[1/5] Updating system packages..."
apt update && apt upgrade -y

echo "[2/5] Installing Python and dependencies..."
apt install -y python3-pip python3-venv

echo "[3/5] Creating virtual environment..."
python3 -m venv /root/venv
source /root/venv/bin/activate

echo "[4/5] Installing Python packages..."
pip install flask torch transformers

echo "[5/5] Setting up swap memory (2GB)..."
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

echo "✓ Cloud server setup complete!"
echo "Now upload cloud_server.py and run: python3 cloud_server.py"