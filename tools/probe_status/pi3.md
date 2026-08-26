# RIPE Atlas Probe installation instructions for Raspberry Pi 3 and later

These are 64-bit boards and there are official Debian packages for installation. Follow these instructions:

1. Burn the Raspbian OS (32-bit) onto an SD card using Raspberry Pi Imager software or similar. If you'd like to be able to SSH into the Pi later, don't forget to turn on SSH at this step.
2. Insert the card into the SD card slot in the Raspberry Pi board.
3. Connect the HDMI cable, a keyboard, and a mouse.
4. Connect the power supply and turn on the Raspberry Pi.
5. Follow the on-screen instructions to configure the Raspbian OS.
6. Open a terminal and issue the following commands in it.
7. `ARCH=$(dpkg --print-architecture)`
8. `CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")`
9. `REPO_PKG=ripe-atlas-repo_1.5-5_all.deb`
10. `wget https://ftp.ripe.net/ripe/atlas/software-probe/debian/dists/"$CODENAME"/main/binary-"$ARCH"/"$REPO_PKG" \
     https://github.com/RIPE-NCC/ripe-atlas-software-probe/releases/latest/download/CHECKSUMS`
11. `grep -q "$(sha256sum "$REPO_PKG")" CHECKSUMS && echo "Checksum OK" || echo "CHECKSUM FAILED"`. Verify that the checksum is OK.
12. `sudo dpkg -i "$REPO_PKG" && rm "$REPO_PKG"`
13. `sudo apt update`
14. `sudo apt-get install ripe-atlas-probe`

## Optional: Install Tailscale for remote SSH
To handle situations where you might need to run some commands remotely on the Pi while it is behind a NAT somewhere out there, you need to create a tunnel for this purpose. Tailscale is one possibility. Follow these steps:

1. Sign up for an account at Tailscale. 
2. Get an auth key from Tailscale for remote access.
3. On the Raspberry Pi terminal, run the following commands:
4. `curl -fsSL https://tailscale.com/install.sh | sh`
5. `sudo tailscale up --authkey=<your auth key>`
6. `sudo systemctl enable --now tailscaled`


Your Raspberry Pi-based RIPE Atlas Probe is now ready. Go ahead and deploy it.