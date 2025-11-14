#!/usr/bin/env python3
"""
OCR PDF Application Launcher
One-click start/stop for the entire application.
"""
import os
import sys
import time
import subprocess
import signal
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pathlib import Path
import threading
import webbrowser

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

class OCRLauncher:
    def __init__(self):
        self.processes = {}
        self.running = False
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("OCR PDF Launcher")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set icon (if available)
        try:
            # You can add an icon file later
            pass
        except:
            pass
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title = tk.Label(
            self.root,
            text="🔍 OCR PDF Application",
            font=("Arial", 20, "bold"),
            pady=10
        )
        title.pack()
        
        # Status
        self.status_label = tk.Label(
            self.root,
            text="⚫ Not Running",
            font=("Arial", 14),
            fg="gray"
        )
        self.status_label.pack()
        
        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # Start button
        self.start_button = tk.Button(
            button_frame,
            text="▶ Start All Services",
            command=self.start_all,
            bg="#28a745",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
            height=2
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        # Stop button
        self.stop_button = tk.Button(
            button_frame,
            text="⏹ Stop All Services",
            command=self.stop_all,
            bg="#dc3545",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
            height=2,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Open browser button
        self.browser_button = tk.Button(
            button_frame,
            text="🌐 Open in Browser",
            command=lambda: webbrowser.open("http://localhost:3000"),
            bg="#007bff",
            fg="white",
            font=("Arial", 12, "bold"),
            width=20,
            height=2,
            state=tk.DISABLED
        )
        self.browser_button.grid(row=0, column=2, padx=5)
        
        # Service status frame
        status_frame = tk.LabelFrame(self.root, text="Service Status", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, padx=20, pady=10)
        
        self.service_labels = {}
        services = ["Redis", "Backend API", "RQ Worker", "Frontend"]
        for i, service in enumerate(services):
            label = tk.Label(
                status_frame,
                text=f"{service}: ⚫ Stopped",
                font=("Arial", 10),
                anchor="w"
            )
            label.grid(row=i, column=0, sticky="w", pady=2)
            self.service_labels[service] = label
        
        # Log output
        log_frame = tk.LabelFrame(self.root, text="Logs", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=15,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Info
        info = tk.Label(
            self.root,
            text="Frontend: http://localhost:3000 | API: http://localhost:8000",
            font=("Arial", 9),
            fg="gray"
        )
        info.pack(pady=5)
        
    def log(self, message, level="INFO"):
        """Add message to log window."""
        timestamp = time.strftime("%H:%M:%S")
        color_map = {
            "INFO": "black",
            "SUCCESS": "green",
            "ERROR": "red",
            "WARNING": "orange"
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def update_service_status(self, service, status):
        """Update service status indicator."""
        status_map = {
            "running": "🟢 Running",
            "stopped": "⚫ Stopped",
            "starting": "🟡 Starting...",
            "error": "🔴 Error"
        }
        
        if service in self.service_labels:
            self.service_labels[service].config(
                text=f"{service}: {status_map.get(status, status)}"
            )
            
    def check_redis(self):
        """Check if Redis is running."""
        try:
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0 and "PONG" in result.stdout
        except:
            return False
            
    def start_redis(self):
        """Start Redis if not running."""
        if self.check_redis():
            self.log("Redis is already running", "SUCCESS")
            self.update_service_status("Redis", "running")
            return True
            
        self.log("Starting Redis...", "INFO")
        self.update_service_status("Redis", "starting")
        
        # Try to start Redis
        try:
            # Try homebrew service
            subprocess.run(["brew", "services", "start", "redis"], 
                         capture_output=True, timeout=5)
            time.sleep(2)
            
            if self.check_redis():
                self.log("Redis started successfully", "SUCCESS")
                self.update_service_status("Redis", "running")
                return True
        except:
            pass
            
        # Try direct redis-server
        try:
            process = subprocess.Popen(
                ["redis-server"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.processes["redis"] = process
            time.sleep(2)
            
            if self.check_redis():
                self.log("Redis started successfully", "SUCCESS")
                self.update_service_status("Redis", "running")
                return True
        except:
            pass
            
        self.log("Failed to start Redis. Please install Redis first.", "ERROR")
        self.log("Run: brew install redis", "INFO")
        self.update_service_status("Redis", "error")
        return False
        
    def install_dependencies(self):
        """Install backend and frontend dependencies if needed."""
        # Check backend venv
        venv_path = BACKEND_DIR / "venv"
        if not venv_path.exists():
            self.log("Creating Python virtual environment...", "INFO")
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                cwd=str(BACKEND_DIR)
            )
            
        # Install backend dependencies
        pip_path = venv_path / "bin" / "pip"
        self.log("Installing backend dependencies...", "INFO")
        subprocess.run(
            [str(pip_path), "install", "-q", "-r", "requirements.txt"],
            cwd=str(BACKEND_DIR)
        )
        
        # Check frontend node_modules
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            self.log("Installing frontend dependencies...", "INFO")
            subprocess.run(
                ["npm", "install"],
                cwd=str(FRONTEND_DIR),
                stdout=subprocess.DEVNULL
            )
            
    def start_backend(self):
        """Start backend API server."""
        self.log("Starting Backend API...", "INFO")
        self.update_service_status("Backend API", "starting")
        
        venv_python = BACKEND_DIR / "venv" / "bin" / "python"
        
        process = subprocess.Popen(
            [str(venv_python), "-m", "uvicorn", "app.main:app", 
             "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes["backend"] = process
        
        # Wait for backend to start
        time.sleep(3)
        
        if process.poll() is None:
            self.log("Backend API started on http://localhost:8000", "SUCCESS")
            self.update_service_status("Backend API", "running")
            return True
        else:
            self.log("Failed to start Backend API", "ERROR")
            self.update_service_status("Backend API", "error")
            return False
            
    def start_worker(self):
        """Start RQ worker."""
        self.log("Starting RQ Worker...", "INFO")
        self.update_service_status("RQ Worker", "starting")
        
        venv_python = BACKEND_DIR / "venv" / "bin" / "python"
        
        process = subprocess.Popen(
            [str(venv_python), "-m", "rq", "worker", "app.workers"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes["worker"] = process
        time.sleep(2)
        
        if process.poll() is None:
            self.log("RQ Worker started", "SUCCESS")
            self.update_service_status("RQ Worker", "running")
            return True
        else:
            self.log("Failed to start RQ Worker", "ERROR")
            self.update_service_status("RQ Worker", "error")
            return False
            
    def start_frontend(self):
        """Start frontend dev server."""
        self.log("Starting Frontend...", "INFO")
        self.update_service_status("Frontend", "starting")
        
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        self.processes["frontend"] = process
        time.sleep(4)
        
        if process.poll() is None:
            self.log("Frontend started on http://localhost:3000", "SUCCESS")
            self.update_service_status("Frontend", "running")
            return True
        else:
            self.log("Failed to start Frontend", "ERROR")
            self.update_service_status("Frontend", "error")
            return False
            
    def start_all(self):
        """Start all services."""
        self.start_button.config(state=tk.DISABLED)
        self.log("=== Starting OCR PDF Application ===", "INFO")
        
        def start_thread():
            try:
                # Install dependencies
                self.install_dependencies()
                
                # Start Redis
                if not self.start_redis():
                    self.log("Cannot continue without Redis", "ERROR")
                    self.start_button.config(state=tk.NORMAL)
                    return
                
                # Start Backend
                if not self.start_backend():
                    self.stop_all()
                    self.start_button.config(state=tk.NORMAL)
                    return
                
                # Start Worker
                if not self.start_worker():
                    self.stop_all()
                    self.start_button.config(state=tk.NORMAL)
                    return
                
                # Start Frontend
                if not self.start_frontend():
                    self.stop_all()
                    self.start_button.config(state=tk.NORMAL)
                    return
                
                # Success!
                self.running = True
                self.status_label.config(text="🟢 Running", fg="green")
                self.stop_button.config(state=tk.NORMAL)
                self.browser_button.config(state=tk.NORMAL)
                
                self.log("=== All services started successfully! ===", "SUCCESS")
                self.log("Opening browser in 2 seconds...", "INFO")
                
                time.sleep(2)
                webbrowser.open("http://localhost:3000")
                
            except Exception as e:
                self.log(f"Error during startup: {e}", "ERROR")
                self.stop_all()
                self.start_button.config(state=tk.NORMAL)
        
        threading.Thread(target=start_thread, daemon=True).start()
        
    def stop_all(self):
        """Stop all services."""
        self.log("=== Stopping all services ===", "INFO")
        self.stop_button.config(state=tk.DISABLED)
        self.browser_button.config(state=tk.DISABLED)
        
        # Stop processes
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    self.log(f"Stopping {name}...", "INFO")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except:
                pass
                
        self.processes.clear()
        
        # Update UI
        for service in self.service_labels:
            self.update_service_status(service, "stopped")
            
        self.running = False
        self.status_label.config(text="⚫ Not Running", fg="gray")
        self.start_button.config(state=tk.NORMAL)
        self.log("All services stopped", "INFO")
        
    def on_closing(self):
        """Handle window close."""
        if self.running:
            if messagebox.askokcancel("Quit", "Stop all services and quit?"):
                self.stop_all()
                self.root.destroy()
        else:
            self.root.destroy()
            
    def run(self):
        """Run the launcher."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log("OCR PDF Launcher ready", "INFO")
        self.log("Click 'Start All Services' to begin", "INFO")
        self.root.mainloop()

if __name__ == "__main__":
    launcher = OCRLauncher()
    launcher.run()

