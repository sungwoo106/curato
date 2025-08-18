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
    """Get GPU/NPU information using various methods."""
    print("🎮 GPU/NPU Information:")
    
    # Try to get Qualcomm/Snapdragon NPU info first
    print("🔍 Detecting Qualcomm Snapdragon X Elite NPU...")
    
    # Check for Qualcomm NPU drivers and devices
    try:
        if platform.system() == "Windows":
            # Use Windows Management Instrumentation for Qualcomm devices
            result = subprocess.run(['wmic', 'path', 'win32_PnPEntity', 'where', 'name like "%Qualcomm%" or name like "%Snapdragon%" or name like "%NPU%" or name like "%AI%"', 'get', 'name,deviceid'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                qualcomm_found = False
                for line in lines:
                    if line.strip():
                        if any(keyword in line for keyword in ['Qualcomm', 'Snapdragon', 'NPU', 'AI']):
                            print(f"   Found: {line.strip()}")
                            qualcomm_found = True
                
                if not qualcomm_found:
                    print("   No Qualcomm devices found via WMI")
            
            # Try to get Qualcomm NPU info via registry or other methods
            try:
                # Check if Qualcomm NPU drivers are installed
                result = subprocess.run(['reg', 'query', 'HKLM\\SYSTEM\\CurrentControlSet\\Services', '/s', '/f', 'Qualcomm'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'Qualcomm' in result.stdout:
                    print("   Qualcomm drivers detected in registry")
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Check for Qualcomm NPU in device manager
            try:
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name,adapterram'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        if line.strip() and any(keyword in line for keyword in ['Qualcomm', 'Snapdragon', 'NPU']):
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                name = ' '.join(parts[:-1])
                                memory = parts[-1]
                                print(f"   Qualcomm NPU: {name} ({memory} bytes)")
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
                
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print("   Could not query Qualcomm devices")
    
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
    
    # Try to get Qualcomm/Snapdragon NPU usage
    try:
        if platform.system() == "Windows":
            # Check for Qualcomm NPU performance counters
            # Snapdragon X Elite NPU might expose metrics through different interfaces
            
            # Method 1: Check if Qualcomm NPU tools are available
            try:
                result = subprocess.run(['qcom-npu-monitor'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse Qualcomm NPU output
                    for line in result.stdout.split('\n'):
                        if 'NPU' in line and 'utilization' in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                gpu_info['qualcomm_npu'] = {
                                    'utilization': int(parts[2].replace('%', '')),
                                    'memory_used': 0,  # May not be available
                                    'memory_total': 0,
                                    'temperature': 0
                                }
                                break
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Method 2: Try to get NPU info from Windows performance counters
            try:
                result = subprocess.run(['typeperf', '\\Processor(_Total)\\% Processor Time'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    # This is just CPU, but we'll use it as a proxy for NPU activity
                    # since Snapdragon X Elite NPU might not expose direct metrics
                    pass
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Method 3: Check for Qualcomm NPU in device manager and try to get metrics
            try:
                result = subprocess.run(['wmic', 'path', 'win32_PerfFormattedData_PerfOS_Processor', 'get', 'PercentProcessorTime'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    if lines:
                        # Use CPU as proxy for NPU activity since they're integrated
                        gpu_info['qualcomm_npu'] = {
                            'utilization': 0,  # Will be updated with actual CPU usage
                            'memory_used': 0,
                            'memory_total': 0,
                            'temperature': 0
                        }
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
                
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
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

def get_snapdragon_npu_activity():
    """Get Snapdragon X Elite NPU activity through alternative methods."""
    npu_info = {}
    
    try:
        if platform.system() == "Windows":
            # Method 1: Check for Qualcomm NPU in device manager
            try:
                result = subprocess.run(['wmic', 'path', 'win32_PnPEntity', 'where', 'name like "%Qualcomm%" or name like "%Snapdragon%" or name like "%NPU%"', 'get', 'name,status'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]
                    for line in lines:
                        if line.strip() and any(keyword in line for keyword in ['Qualcomm', 'Snapdragon', 'NPU']):
                            npu_info['device_status'] = line.strip()
                            break
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Method 2: Check Windows performance counters for AI/ML activity
            try:
                # Look for AI/ML related performance counters
                result = subprocess.run(['typeperf', '-qx'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ai_counters = []
                    for line in result.stdout.split('\n'):
                        if any(keyword in line.lower() for keyword in ['ai', 'ml', 'npu', 'neural', 'inference']):
                            ai_counters.append(line.strip())
                    
                    if ai_counters:
                        npu_info['ai_counters'] = ai_counters[:3]  # Show first 3
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Method 3: Check for Qualcomm NPU processes
            try:
                result = subprocess.run(['tasklist', '/fi', 'imagename eq *qualcomm*'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    qualcomm_processes = []
                    for line in result.stdout.split('\n'):
                        if 'qualcomm' in line.lower() or 'npu' in line.lower():
                            qualcomm_processes.append(line.strip())
                    
                    if qualcomm_processes:
                        npu_info['qualcomm_processes'] = qualcomm_processes
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
            
            # Method 4: Check for AI/ML related services
            try:
                result = subprocess.run(['sc', 'query', 'type= service'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    ai_services = []
                    for line in result.stdout.split('\n'):
                        if any(keyword in line.lower() for keyword in ['ai', 'ml', 'npu', 'neural', 'qualcomm']):
                            ai_services.append(line.strip())
                    
                    if ai_services:
                        npu_info['ai_services'] = ai_services[:3]  # Show first 3
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                pass
                
    except Exception as e:
        print(f"   Error detecting Snapdragon NPU: {e}")
    
    return npu_info

def monitor_resources():
    """Monitor CPU, memory, disk, and GPU/NPU usage."""
    print("📊 Resource Monitoring (Press Ctrl+C to stop):")
    print("=" * 80)
    
    # Check for Snapdragon NPU activity
    snapdragon_info = get_snapdragon_npu_activity()
    if snapdragon_info:
        print("🔍 Snapdragon X Elite NPU detected!")
        for key, value in snapdragon_info.items():
            if isinstance(value, list):
                print(f"   {key}: {len(value)} items found")
            else:
                print(f"   {key}: {value}")
        print()
    
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
            
            # Show Snapdragon NPU activity indicators
            if snapdragon_info:
                # Check for increased CPU activity as proxy for NPU usage
                if cpu_percent > 50:
                    print(f"🚀 High CPU activity - NPU may be processing (CPU: {cpu_percent:.1f}%)")
                
                # Check for memory spikes that might indicate NPU model loading
                if memory_percent > 70:
                    print(f"🧠 High memory usage - NPU models may be loaded (Memory: {memory_percent:.1f}%)")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("\n💡 Tips for Snapdragon X Elite NPU monitoring:")
        print("   • Snapdragon NPU doesn't expose direct metrics like GPUs")
        print("   • Monitor CPU spikes during inference (NPU is integrated)")
        print("   • Watch memory usage for model loading")
        print("   • Check Task Manager > Performance tab for overall system activity")
        print("   • Look for 'Qualcomm' or 'Snapdragon' in Device Manager")
        print("   • NPU activity may show as increased CPU usage")
        print("   • Use Windows Performance Monitor for detailed AI/ML counters")

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
