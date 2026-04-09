#!/bin/bash
echo "blacklist usblp" | sudo tee /etc/modprobe.d/blacklist.conf
sudo update-initramfs -u
echo "usblp blacklisted. Please reboot."
