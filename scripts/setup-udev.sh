#!/bin/bash
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="balanza"' | sudo tee /etc/udev/rules.d/99-balanza.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
echo "Udev rules applied (Generic values used)."
