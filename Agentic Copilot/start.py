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
    print("Starting Agentic Commerce Copilot...")
    
    # Kill old processes
    kill_port(8000) # Backend
    kill_port(5174) # Frontend
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Start Backend
    backend_dir = os.path.join(base_dir, 'backend')
    print("Starting Backend on port 8000...")
    # Assume venv is at backend/venv
    venv_python = os.path.join(backend_dir, 'venv', 'bin', 'python')
    if not os.path.exists(venv_python):
        print(f"Warning: Virtual environment not found at {venv_python}")
        venv_python = sys.executable

    backend_process = subprocess.Popen(
        [venv_python, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
        cwd=backend_dir
    )
    
    # Start Frontend
    frontend_dir = os.path.join(base_dir, 'frontend')
    print("Starting Frontend on port 5174...")
    frontend_process = subprocess.Popen(
        ['npm', 'run', 'dev', '--', '--port', '5174'],
        cwd=frontend_dir
    )
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        sys.exit(0)

if __name__ == '__main__':
    main()
