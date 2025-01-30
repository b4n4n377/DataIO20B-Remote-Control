import os
import tkinter as tk
from tkinter import ttk
import csv
import serial


class DataIO20BRemoteControl:
    def __init__(self, window):
        self.main_window = window
        self.main_window.title("Data I/O 20B Remote Control")
        self.main_window.geometry("600x400")
        self.main_window.protocol("WM_DELETE_WINDOW", self.terminate_program)

        self.filename = "data_io_20b_supported_devices.csv"
        self.devices_info = self._load_devices_and_get_info()
        self.devices = [
            device["DisplayName"]
            for device in self.devices_info
            if "DisplayName" in device
        ]
        self.serial_connection = None
        self.setup_ui()

    def log(self, message, to_terminal=False):
        if to_terminal:
            self.terminal_output.insert(tk.END, message + "\n")
            self.terminal_output.see(tk.END)
        else:
            print(f"- {message}")

    def _load_devices_and_get_info(self, device_name=None):
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                devices = list(csv.DictReader(file))
                if not devices:
                    raise ValueError("CSV file is empty or not correctly formatted.")
                if device_name:
                    return next(
                        (
                            device
                            for device in devices
                            if device["DisplayName"] == device_name
                        ),
                        None,
                    )
                return devices
        except (FileNotFoundError, csv.Error, ValueError, KeyError) as e:
            self.log(f"Error loading devices from {self.filename}: {e}")
            return None if device_name else []

    def setup_ui(self):
        frame = tk.Frame(self.main_window)
        frame.pack(pady=5, padx=10, fill="x")
        frame.columnconfigure(1, weight=1)

        tk.Label(
            frame, text="Set Serial Port:", font=("TkDefaultFont", 12), anchor="w"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.serial_port_var = tk.StringVar(value="/dev/ttyUSB0")
        tk.Entry(
            frame, textvariable=self.serial_port_var, font=("TkDefaultFont", 12)
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        tk.Label(
            frame, text="Set Device:", font=("TkDefaultFont", 12), anchor="w"
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.device_var = tk.StringVar(value="- please select -")

        style = ttk.Style()
        style.map("TCombobox", fieldbackground=[("readonly", "white")])
        style.map("TCombobox", selectbackground=[("readonly", "white")])
        style.map("TCombobox", selectforeground=[("readonly", "black")])

        self.device_menu = ttk.Combobox(
            frame,
            textvariable=self.device_var,
            values=["- please select -"],
            state="readonly",
            font=("TkDefaultFont", 12),
        )
        self.device_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.device_menu.bind("<Button-1>", self.populate_devices)
        self.device_menu.bind("<<ComboboxSelected>>", self.handle_device_selection)

        tk.Label(
            frame,
            text="Select the same device on the programmer and enable remote mode ('rC')",
            font=("TkDefaultFont", 12),
            anchor="w",
        ).grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        self.connect_button = tk.Button(
            frame,
            text="Connect to Programmer",
            font=("TkDefaultFont", 12),
            command=self.handle_connect_button,
            state=tk.DISABLED,
        )
        self.connect_button.grid(row=3, column=1, padx=5, pady=10, sticky="ew")

        self.button_frame = tk.LabelFrame(
            self.main_window, text="Functions", font=("TkDefaultFont", 12)
        )
        self.button_frame.pack(pady=10, padx=10, fill="x")

        self.respond_button = tk.Button(
            self.button_frame,
            text="Get Programmer Status",
            font=("TkDefaultFont", 12),
            command=self.handle_status_button,
            state=tk.DISABLED,
        )
        self.respond_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.load_device_button = tk.Button(
            self.button_frame,
            text="Load Device and Save to File",
            font=("TkDefaultFont", 12),
            command=self.handle_load_device_button,
            state=tk.DISABLED,
        )
        self.load_device_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.checksum_button = tk.Button(
            self.button_frame,
            text="Calculate Checksum of All Files",
            font=("TkDefaultFont", 12),
            command=self.handle_calculate_checksums_button,
            state=tk.DISABLED,
        )
        self.checksum_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        terminal_frame = tk.Frame(self.main_window)
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.terminal_output = tk.Text(
            terminal_frame,
            font=("TkDefaultFont", 10),
            bg="black",
            fg="green",
            wrap="word",
        )
        self.terminal_output.pack(fill="both", expand=True)

        self.context_menu = tk.Menu(self.terminal_output, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_to_clipboard)
        self.terminal_output.bind("<Button-3>", self.show_context_menu)

    def populate_devices(self, event=None):
        if len(self.device_menu["values"]) == 1:
            self.device_menu["values"] = self.devices

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_to_clipboard(self):
        try:
            selected = self.terminal_output.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.main_window.clipboard_clear()
            self.main_window.clipboard_append(selected)
            self.main_window.update()
            self.log("Copied to clipboard.")
        except tk.TclError:
            self.log("No text selected to copy.", to_terminal=True)

    def handle_device_selection(self, event=None):
        if self.device_var.get() != "- please select -":
            self.connect_button.config(state=tk.NORMAL)
            self.log(f"Device selected: {self.device_var.get()}")

    def handle_connect_button(self):
        try:
            self.serial_connection = serial.Serial(
                port=self.serial_port_var.get(), baudrate=9600, timeout=5
            )
            response = self.send_command("\x1B[A", timeout=0.5)
            if response != ">":
                raise ValueError(f"Unexpected response: {response}")
            self.log("Connected to Data I/O 20B Programmer.")
            self.log(
                "Connected to Data I/O 20B Programmer - waiting for commands:\n",
                to_terminal=True,
            )
            self.respond_button.config(state=tk.NORMAL)
            self.load_device_button.config(state=tk.NORMAL)
            self.checksum_button.config(state=tk.NORMAL)
        except (serial.SerialException, ValueError, TypeError) as e:
            self.log(f"Connection error: {e}")

    def handle_status_button(self):
        try:
            response = self.send_command("R", timeout=0.5)
            self.log(response, to_terminal=True)
        except (serial.SerialException, ValueError) as e:
            self.log(f"Respond command error: {e}")

    def handle_load_device_button(self):
        try:
            device_info = next(
                (
                    d
                    for d in self.devices_info
                    if d["DisplayName"] == self.device_var.get()
                ),
                None,
            )
            if not device_info:
                self.log(
                    f"Device {self.device_var.get()} not found in CSV.",
                    to_terminal=True,
                )
                return

            block_size = 0x0800
            start_address = int(device_info["StartHex"], 16)
            end_address = int(device_info["EndHex"], 16)
            total_blocks = (
                (end_address - start_address + 1) + block_size - 1
            ) // block_size

            self.log(
                f"Device {self.device_var.get()} needs to be read in {total_blocks} blocks",
                to_terminal=True,
            )
            eprom_code = ""

            for block_num in range(total_blocks):
                block_start = start_address + block_num * block_size
                if block_start > end_address:
                    break
                block_end = min(block_start + block_size - 1, end_address)

                self.log(
                    f"\n### Block {block_num + 1}: {block_start:04X} - {block_end:04X} ###",
                    to_terminal=True,
                )

                commands = [
                    (f"{block_start:04X}<", 0.5),
                    (f"{block_size:04X};", 0.5),
                    (f"{block_start:04X}:", 0.5),
                    ("L", 3),
                    ("O", 0.5),
                ]

                for cmd, timeout in commands:
                    self.log(f"Command: {cmd}", to_terminal=True)
                    response = self.send_command(cmd, timeout=timeout)
                    cleaned_response = (
                        response.replace("\x00", "").replace("\r", "").strip()
                    )
                    self.log(cleaned_response, to_terminal=True)
                    self.main_window.update_idletasks()
                    if cmd == "O":
                        eprom_code += cleaned_response

            cleaned_eprom_code = self.validate_eprom_code(
                eprom_code, start_address, end_address
            )
            try:
                self.save_eprom_code_to_file(cleaned_eprom_code)
            except (IOError, OSError) as e:
                self.log(f"Error saving EPROM code: {e}", to_terminal=True)

        except (serial.SerialException, ValueError, IOError, KeyError) as e:
            self.log(f"Load Device error: {e}")

    def validate_eprom_code(self, eprom_code, start_address, end_address):
        eprom_code = eprom_code.replace(">", "").replace(" ", "").replace("\r", "")
        lines = eprom_code.split("\n")
        valid_lines = [line for line in lines if len(line) == len(lines[0])]

        current_address = start_address
        updated_lines = []
        while current_address <= end_address:
            for line in valid_lines:
                byte_count = int(line[1:3], 16)
                record_type = line[7:9]
                if record_type == "00":
                    updated_line = f":{byte_count:02X}{current_address:04X}{line[7:]}"
                    updated_lines.append(updated_line)
                    current_address += byte_count
                else:
                    updated_lines.append(line)

            if current_address <= end_address:
                empty_line = f":10{current_address:04X}00{'00' * 16}00"
                updated_lines.append(empty_line)
                current_address += 16

        if not updated_lines or updated_lines[-1] != ":00000001FF":
            updated_lines.append(":00000001FF")

        return "\n".join(updated_lines)

    def save_eprom_code_to_file(self, eprom_code):
        filename = f"eprom_code_{self.device_var.get().replace(' ', '_').lower()}.hex"
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(eprom_code)
            self.log(f"EPROM code saved to {filename}.", to_terminal=True)
            return filename
        except (IOError, OSError) as e:
            self.log(f"Error saving EPROM code: {e}", to_terminal=True)
            return None

    def handle_calculate_checksums_button(self):
        try:
            hex_files = [f for f in os.listdir(".") if f.endswith(".hex")]
            for hex_file in hex_files:
                checksum = self.calculate_eprom_checksum(hex_file)
                if checksum is not None:
                    self.log(f"{hex_file}: Checksum = {checksum:04X}", to_terminal=True)
        except (IOError, OSError) as e:
            self.log(f"Error calculating checksums: {e}", to_terminal=True)

    def calculate_eprom_checksum(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                total = sum(
                    int(line[i : i + 2], 16)
                    for line in file
                    if line.startswith(":")
                    for i in range(9, len(line) - 3, 2)
                )
            return total & 0xFFFF
        except (IOError, OSError, ValueError, KeyError) as e:
            self.log(f"Checksum error: {e}", to_terminal=True)
            return None

    def send_command(self, command, timeout=None):
        if not (self.serial_connection and self.serial_connection.is_open):
            self.log("Not connected to programmer.")
            return None

        try:
            if timeout is not None:
                self.serial_connection.timeout = timeout

            self.serial_connection.write((command + "\r").encode("ASCII"))
            self.log(f"Command sent: {repr(command)}")

            response = b""
            while True:
                byte = self.serial_connection.read(1)
                if byte:
                    response += byte
                else:
                    break

            return response.decode("ASCII").strip()
        except (serial.SerialException, ValueError) as e:
            self.log(f"Command error: {e}")
            return None
        finally:
            if timeout is not None:
                self.serial_connection.timeout = 5

    def terminate_program(self):
        if self.serial_connection:
            self.serial_connection.close()
        self.log("Program terminated by user.")
        self.main_window.destroy()


if __name__ == "__main__":
    main_window = tk.Tk()
    app = DataIO20BRemoteControl(main_window)
    main_window.mainloop()
