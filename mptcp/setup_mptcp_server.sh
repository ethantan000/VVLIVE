#!/bin/bash
# MPTCP Server Setup for Cloud VPS
# Sets up multipath TCP server to receive bonded connections

set -e

echo "====================================="
echo "VVLIVE - MPTCP Server Setup"
echo "====================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check kernel version
KERNEL_VERSION=$(uname -r | cut -d. -f1,2)
echo "Detected kernel version: $(uname -r)"

if [[ $(echo "$KERNEL_VERSION < 5.6" | bc -l) -eq 1 ]]; then
    echo "Warning: MPTCP requires kernel 5.6 or higher"
    echo "Your kernel version: $(uname -r)"
    echo "You may need to upgrade your kernel."
    exit 1
fi

# Enable MPTCP
echo "Enabling MPTCP..."
sysctl -w net.mptcp.enabled=1

# Make persistent
if ! grep -q "net.mptcp.enabled" /etc/sysctl.conf; then
    echo "net.mptcp.enabled=1" >> /etc/sysctl.conf
    echo "MPTCP enabled persistently in /etc/sysctl.conf"
fi

# Configure firewall
echo "Configuring firewall..."
if command -v ufw &> /dev/null; then
    echo "UFW detected, configuring rules..."
    ufw allow 8443/tcp comment "MPTCP Server"
    ufw allow 8000/tcp comment "VVLIVE Backend API"
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"
    echo "Firewall rules configured"
else
    echo "UFW not found, skipping firewall configuration"
    echo "Make sure ports 8443 and 8000 are open!"
fi

# Optimize network settings for streaming
echo "Optimizing network settings..."
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem='4096 87380 67108864'
sysctl -w net.ipv4.tcp_wmem='4096 65536 67108864'
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Make network optimizations persistent
cat >> /etc/sysctl.conf << EOF

# VVLIVE MPTCP Optimizations
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 87380 67108864
net.ipv4.tcp_wmem=4096 65536 67108864
net.ipv4.tcp_congestion_control=bbr
EOF

echo ""
echo "====================================="
echo "MPTCP Server Setup Complete!"
echo "====================================="
echo ""
echo "Server is ready to accept MPTCP connections on port 8443"
echo ""
echo "Next steps:"
echo "1. Configure VVLIVE backend (.env file)"
echo "2. Start VVLIVE backend service"
echo "3. Configure nginx for frontend hosting"
echo "4. Connect Pi client to this server"
echo ""
echo "Verify MPTCP is enabled:"
echo "  sysctl net.mptcp.enabled"
echo ""
echo "Monitor MPTCP connections:"
echo "  ss -M"
echo ""
