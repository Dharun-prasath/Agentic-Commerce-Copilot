import subprocess
import os
import signal
import sys
import time

def kill_process_on_port(port):
    try:
        # Find process ID listening on the port
        output = subprocess.check_output(f"lsof -t -i:{port}", shell=True).decode().strip()
        if output:
            for pid in output.splitlines():
                if pid.strip():
                    print(f"Killing process {pid.strip()} on port {port}")
                    os.kill(int(pid.strip()), signal.SIGKILL)
            time.sleep(1)
    except subprocess.CalledProcessError:
        pass # No process found

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, "backend")
    frontend_dir = os.path.join(script_dir, "frontend")
    
    print("Stopping existing Demo App servers...")
    kill_process_on_port(8001)
    kill_process_on_port(5173)
    
    print("Starting backend on port 8001...")
    backend_cmd = "source venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8001"
    backend_process = subprocess.Popen(backend_cmd, shell=True, cwd=backend_dir, executable="/bin/bash")
    
    print("Starting frontend on port 5173...")
    frontend_cmd = "npm run dev -- --port 5173 --strictPort"
    frontend_process = subprocess.Popen(frontend_cmd, shell=True, cwd=frontend_dir, executable="/bin/bash")
    
    print("\\nDemo App is running!")
    print("- Backend: http://localhost:8001")
    print("- Frontend: http://localhost:5173")
    print("Press Ctrl+C to stop both servers.\\n")

    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\\nStopping Demo App servers...")
        backend_process.kill()
        frontend_process.kill()
        kill_process_on_port(8001)
        kill_process_on_port(5173)
        sys.exit(0)

if __name__ == "__main__":                   
    main()
