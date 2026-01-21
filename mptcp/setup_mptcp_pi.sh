#!/bin/bash
# MPTCP Client Setup for Raspberry Pi
# Sets up multipath TCP for bonding multiple cellular connections

set -e

echo "====================================="
echo "VVLIVE - MPTCP Client Setup"
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
    echo "Consider upgrading: sudo rpi-update"
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

# Configure routing for dual uplink
echo "Configuring routing tables..."

# Create routing tables if not exists
if ! grep -q "200 verizon" /etc/iproute2/rt_tables; then
    echo "200 verizon" >> /etc/iproute2/rt_tables
fi
if ! grep -q "201 att" /etc/iproute2/rt_tables; then
    echo "201 att" >> /etc/iproute2/rt_tables
fi

echo ""
echo "====================================="
echo "MPTCP Client Setup Complete!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Configure network interfaces for both cellular connections"
echo "2. Set up routing rules for each uplink"
echo "3. Test MPTCP connection to server"
echo ""
echo "Example network configuration:"
echo "  Verizon:  eth0 or wlan0 - 192.168.1.0/24"
echo "  AT&T:     eth1 or wlan1 - 192.168.2.0/24"
echo ""
echo "Verify MPTCP is enabled:"
echo "  sysctl net.mptcp.enabled"
echo ""
