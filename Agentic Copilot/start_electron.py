import os
import subprocess
import time
import sys

def kill_port(port):
    try:
        # Find process listening on port
        result = subprocess.run(['lsof', '-t', f'-i:{port}'], capture_output=True, text=True)
        pids = result.stdout.strip().splitlines()
        for pid in pids:
            if pid:
                print(f"Killing process {pid} on port {port}")
                os.kill(int(pid), 9)
    except Exception as e:
        print(f"Error killing port {port}: {e}")

def main():
    print("Starting Electron Phone UI...")
    
    # Kill old processes
    kill_port(5180) # Electron Vite
    kill_port(3456) # Electron IPC Server
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Start Electron
    electron_dir = os.path.join(base_dir, 'electron')
    print("Launching Electron...")
    electron_process = subprocess.Popen(
        ['npm', 'run', 'start'],
        cwd=electron_dir
    )
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Electron...")
        electron_process.terminate()
        sys.exit(0)

if __name__ == '__main__':
    main()
