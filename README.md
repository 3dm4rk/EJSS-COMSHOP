# EJSS-COMSHOP
best tool for computer shop owners

Overview
This guide will help you install and set up both the sender (s1.py) and receiver (r1update.py) programs for the Network Volume Control System.

Prerequisites
Python 3.6 or later

pip (Python package manager)

Git (for cloning the repository)

Windows OS (for the receiver program)

Installation Steps



```

#### 1. Clone the Repository
```bash
git clone https://github.com/3dm](https://github.com/3dm4rk/EJSS-COMSHOP
cd network-volume-control
```

3. Set Up Virtual Environment (Recommended)
bash
Copy
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
3. Install Dependencies
For the Sender (s1.py):
bash
Copy
pip install ipaddress
For the Receiver (r1update.py):
bash
Copy
pip install pycaw simpleaudio requests tkinter
4. Configuration
Sender Configuration:
Edit s1.py to update the UNITS dictionary with your device IPs:

python
Copy
UNITS = {
    "1": "192.168.1.19",
    "2": "192.168.1.4",
    "3": "192.168.1.11",
    "4": "192.168.1.3"
}
Receiver Configuration:
No configuration needed by default, but you can customize:

Idle detection settings

Volume control presets

5. Running the Programs
Start the Receiver:
bash
Copy
python r1update.py
Start the Sender:
bash
Copy
python s1.py
Usage Instructions
Sender Program:
Select a unit or custom IP

Choose from the following options:

Send message

Shutdown remote computer

Adjust speaker volume (0-100%)

Receiver Program:
Runs automatically in the background

Shows a GUI with system controls

Responds to commands from the sender

Troubleshooting
Common Issues:
Volume control not working:

Ensure pycaw is installed correctly

Check audio service is running

Connection issues:

Verify both machines are on the same network

Check firewall settings (port 12345 should be open)

GUI not appearing:

Make sure tkinter is installed

Run as administrator if needed

Additional Notes
The receiver must be running on the target machine for commands to work

For custom IPs, ensure the receiver is installed on that machine

Volume control only works on Windows systems

License
This project is licensed under the MIT License - see the LICENSE file for details.

Support
For issues or questions, please open an issue on the GitHub repository.
