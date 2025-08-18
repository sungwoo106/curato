#!/usr/bin/env python3
"""
NPU/GPU Monitoring Script for Windows

This script helps monitor NPU/GPU usage during model inference.
Run this in a separate terminal while running your Phi model test.
"""

import time
import psutil
import platform
import subprocess
import os

def get_system_info():
    """Get basic system information."""
    print("🖥️  System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   CPU: {psutil.cpu_count()} cores")
    print(f"   Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print()

def get_gpu_info():
    """Get GPU/NPU information using nvidia-smi or other methods."""
    print("🎮 GPU/NPU Information:")
    
    # Try to get NVIDIA GPU info
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_lines = result.stdout.strip().split('\n')
            for i, line in enumerate(gpu_lines):
                if line.strip():
                    name, memory, driver = line.split(', ')
                    print(f"   GPU {i}: {name} ({memory} MB) - Driver: {driver}")
        else:
            print("   No NVIDIA GPUs detected")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print("   nvidia-smi not available")
    
    # Try to get Intel GPU info (for Intel NPUs)
    try:
        if platform.system() == "Windows":
            # Use Windows Management Instrumentation for Intel GPU info
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name,adapterram'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and 'Intel' in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            name = ' '.join(parts[:-1])
                            memory = parts[-1]
                            print(f"   Intel GPU: {name} ({memory} bytes)")
        else:
            # Try lspci on Linux/macOS
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or '3D' in line:
                        print(f"   GPU: {line.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    print()

def get_gpu_usage():
    """Get current GPU/NPU usage."""
    gpu_info = {}
    
    # Try NVIDIA GPU usage
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu', 
                               '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    util, mem_used, mem_total, temp = line.split(', ')
                    gpu_info[f'nvidia_{i}'] = {
                        'utilization': int(util),
                        'memory_used': int(mem_used),
                        'memory_total': int(mem_total),
                        'temperature': int(temp)
                    }
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Try Intel GPU usage (for NPUs)
    try:
        if platform.system() == "Windows":
            # Use Intel GPU monitoring tools if available
            result = subprocess.run(['intel_gpu_top', '--once'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse Intel GPU output
                for line in result.stdout.split('\n'):
                    if 'GPU' in line and 'utilization' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            gpu_info['intel'] = {
                                'utilization': int(parts[2].replace('%', '')),
                                'memory_used': 0,  # Intel tools may not show memory
                                'memory_total': 0,
                                'temperature': 0
                            }
                            break
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    return gpu_info

def monitor_resources():
    """Monitor CPU, memory, disk, and GPU/NPU usage."""
    print("📊 Resource Monitoring (Press Ctrl+C to stop):")
    print("=" * 80)
    
    # Header for GPU info
    gpu_headers = []
    gpu_info = get_gpu_usage()
    if gpu_info:
        for gpu_name in gpu_info.keys():
            gpu_headers.append(f"{gpu_name.upper()}")
    
    header = f"{'Time':<8} {'CPU%':<6} {'Memory%':<8} {'Disk%':<6}"
    if gpu_headers:
        for header_name in gpu_headers:
            header += f" {header_name}%:Mem:Temp"
    
    print(header)
    print("-" * len(header))
    
    try:
        while True:
            # Get current time
            current_time = time.strftime("%H:%M:%S")
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
            except OSError:
                disk_percent = 0
            
            # Get GPU/NPU usage
            gpu_info = get_gpu_usage()
            
            # Build output line
            output_line = f"{current_time:<8} {cpu_percent:<6.1f} {memory_percent:<8.1f} {disk_percent:<6.1f}"
            
            if gpu_info:
                for gpu_name, gpu_data in gpu_info.items():
                    util = gpu_data.get('utilization', 0)
                    mem_used = gpu_data.get('memory_used', 0)
                    mem_total = gpu_data.get('memory_total', 1)
                    temp = gpu_data.get('temperature', 0)
                    mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
                    output_line += f" {util:>3}%:{mem_percent:>3.0f}%:{temp:>3}°C"
            
            print(output_line)
            
            # Check for high resource usage
            if cpu_percent > 80:
                print(f"⚠️  High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 80:
                print(f"⚠️  High memory usage: {memory_percent:.1f}%")
            
            # Check GPU usage
            for gpu_name, gpu_data in gpu_info.items():
                util = gpu_data.get('utilization', 0)
                temp = gpu_data.get('temperature', 0)
                if util > 80:
                    print(f"🔥 High {gpu_name} utilization: {util}%")
                if temp > 80:
                    print(f"🌡️  High {gpu_name} temperature: {temp}°C")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("\n💡 Tips for NPU/GPU monitoring:")
        print("   • Check Task Manager > Performance tab for GPU/NPU usage")
        print("   • Use GPU-Z for detailed GPU statistics")
        print("   • Monitor temperature and power consumption")
        print("   • Look for 'NPU' or 'AI Engine' in device manager")
        print("   • Intel NPUs may show up as 'Intel Graphics' or 'Intel UHD Graphics'")

def main():
    """Main function."""
    print("🚀 NPU/GPU Monitoring Script for Windows")
    print("=" * 50)
    
    get_system_info()
    get_gpu_info()
    
    print("💡 To monitor NPU/GPU usage:")
    print("   1. Run this script in one terminal")
    print("   2. Run your Phi model test in another terminal")
    print("   3. Watch for GPU/NPU utilization spikes during inference")
    print("   4. Check Task Manager for GPU/NPU activity")
    print("   5. Monitor temperature and memory usage")
    print()
    
    input("Press Enter to start monitoring...")
    
    monitor_resources()

if __name__ == "__main__":
    main()
