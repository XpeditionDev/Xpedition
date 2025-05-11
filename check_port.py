import psutil
import socket
import os

def find_process_by_port(port):
    """Find the process using a specific port"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    return proc.info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

# Check port 5000
process_info = find_process_by_port(5000)
if process_info:
    print(f"Process using port 5000: {process_info}")
else:
    print("No process found using port 5000")

# Try to bind to port 5000 to see if it's free
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 5000))
    print("Port 5000 is free")
    sock.close()
except OSError:
    print("Port 5000 is in use")

# List all running Python processes
print("\nRunning Python processes:")
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower() and proc.info['cmdline']:
            cmd = ' '.join(proc.info['cmdline'])
            print(f"PID: {proc.info['pid']}, CMD: {cmd}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass 