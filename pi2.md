# RIPE Atlas Probe installation instructions for Raspberry Pi 2
Raspberry Pi 2 is a 32-bit machine. As such, the pre-built RIPE Atlas probe package isn't available. We'll have to build from source.

1. Burn the Raspbian OS (32-bit) onto an SD card using Raspberry Pi Imager software or similar. If you'd like to be able to SSH into the Pi later, don't forget to turn on SSH at this step.
2. Insert the card into the SD card slot in the Raspberry Pi board.
3. Connect the HDMI cable, a keyboard, and a mouse.
4. Connect the power supply and turn on the Raspberry Pi.
5. Follow the on-screen instructions to configure the Raspbian OS.
6. Open a terminal and issue the following commands in it.
7. `sudo apt update`
8. `sudo apt install -y git libssl-dev autoconf automake libtool   build-essential libcap2-bin debhelper`
9. `git clone https://github.com/RIPE-NCC/ripe-atlas-software-probe.git`
10. `cd ripe-atlas-software-probe`
11. `dpkg-buildpackage -b -us -uc`
12. `cd ..`
13. In the current directory, you'll find two `.deb` files whose name starts with `ripe-atlas-`. One of the file has the word `common` in its name, and another has `probe` in its name. First install the `.deb` file with `common` in its file name using the command: `sudo dpkg -i <filename>.deb`. 
14. Now, install the other file with the word `probe` in its name using the command: `sudo dpkg -i <filename>.deb`. This command's output has instructions on how to register the probe. Either follow the hyperlink right away on the Raspberry Pi interface, or if you'd rather do it on another computer, copy the public key that is displayed somehow (web based clipboard, email to yourself, whatsapp web to yourself etc.)
15. Finally run the command: `sudo apt-get install -f`

## Optional: Install Tailscale for remote SSH
To handle situations where you might need to run some commands remotely on the Pi while it is behind a NAT somewhere out there, you need to create a tunnel for this purpose. Tailscale is one possibility. Follow these steps:

1. Sign up for an account at Tailscale. 
2. Get an auth key from Tailscale for remote access.
3. On the Raspberry Pi terminal, run the following commands:
4. `curl -fsSL https://tailscale.com/install.sh | sh`
5. `sudo tailscale up --authkey=<your auth key>`
6. `sudo systemctl enable --now tailscaled`


Your Raspberry Pi 2 based RIPE Atlas Probe is now ready. Go ahead and deploy it.