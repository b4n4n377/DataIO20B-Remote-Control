# Data I/O 20B Remote Control
This project provides a graphical user interface (GUI) to remotely control the Data I/O 20B programmer. The application is built using Python and Tkinter, and it allows users to connect to the programmer via a serial port, select devices, and perform various operations such as loading devices, calculating checksums, and retrieving programmer status.

## Features

- Connect to the Data I/O 20B programmer via a serial port.
- Select supported devices from a CSV file.
- Load device data and save it to a file.
- Calculate checksums of all saved files.
- Retrieve and display the programmer status.

## Requirements

- Python 3.x
- Tkinter
- pySerial

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/data-io-20b-remote-control.git
    cd data-io-20b-remote-control
    ```

2. Install the required Python packages:
    ```sh
    pip install pyserial
    ```

3. Ensure the `data_io_20b_supported_devices.csv` file is in the same directory as the script.

## Usage

1. Run the script:
    ```sh
    python data_io_20b_remote.py
    ```

    If the regular users do not have permissions for the serial port, you may need to run the script with `sudo`:
    ```sh
    sudo python data_io_20b_remote.py
    ```

2. Use the GUI to set the serial port and select a device.

3. Connect to the programmer and use the available functions to interact with the device.

## Acknowledgements

Special thanks to the [DataioEPROM](https://groups.io/g/DataioEPROM) community. Without their support, much of this script would not have been possible. They always provide great assistance. This is also where I gather all information about Data I/O programmers.
