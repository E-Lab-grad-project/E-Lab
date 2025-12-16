import serial
import time
import sys

class ESP32Communicator:
    def __init__(self, port=None, baudrate=115200):
        """
        Initialize serial connection
        If port is None, it will try to auto-detect
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        
        if not port:
            self.port = self.find_esp32_port()
        
    def find_esp32_port(self):
        """Try to auto-detect ESP32 port"""
        import serial.tools.list_ports
        
        # Common ESP32 board identifiers
        esp32_identifiers = ['Silicon Labs', 'CP210', 'CH340', 'FTDI', 'USB2.0-Serial']
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"Found: {port.device} - {port.description}")
            for identifier in esp32_identifiers:
                if identifier in port.description:
                    print(f"Likely ESP32 found on: {port.device}")
                    return port.device
        
        raise Exception("ESP32 not found. Please specify port manually.")
    
    def connect(self):
        """Establish serial connection"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1  # Read timeout in seconds
            )
            time.sleep(2)  # Wait for connection to establish
            print(f"Connected to ESP32 on {self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_command(self, command):
        """Send a command to ESP32"""
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Not connected to ESP32")
            return None
        
        try:
            # Add newline character as terminator
            self.serial_connection.write((command + '\n').encode())
            print(f"Sent: {command}")
            
            # Wait for and read response
            response = self.read_response()
            return response
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
    
    def read_response(self, timeout=1):
        """Read response from ESP32"""
        response = ""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if self.serial_connection.in_waiting > 0:
                line = self.serial_connection.readline().decode('utf-8').strip()
                if line:
                    print(f"Received: {line}")
                    response += line + "\n"
        
        return response if response else "No response"
    
    def close(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Connection closed")

def main():
    # Option 1: Auto-detect port (recommended for first try)
    esp = ESP32Communicator()
    
    # Option 2: Specify port manually (uncomment and modify)
    # esp = ESP32Communicator(port='COM3')  # Windows
    # esp = ESP32Communicator(port='/dev/ttyUSB0')  # Linux
    # esp = ESP32Communicator(port='/dev/tty.usbserial-*')  # macOS
    
    try:
        if esp.connect():
            # Example commands
            print("\nSending commands to ESP32...")
            
            # Turn LED ON
            response = esp.send_command("LED_ON")
            time.sleep(1)
            
            # Turn LED OFF
            response = esp.send_command("LED_OFF")
            time.sleep(1)
            
            # Get temperature
            response = esp.send_command("GET_TEMP")
            
            # You can also send custom commands
            custom_cmd = input("\nEnter custom command (or 'exit' to quit): ")
            while custom_cmd.lower() != 'exit':
                esp.send_command(custom_cmd)
                custom_cmd = input("\nEnter custom command (or 'exit' to quit): ")
    
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        esp.close()

if __name__ == "__main__":
    main()