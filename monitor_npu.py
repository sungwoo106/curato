#!/usr/bin/env python3
"""
NPU Monitoring Script for Windows

This script helps monitor NPU/GPU usage during model inference.
Run this in a separate terminal while running your Phi model test.
"""

import time
import psutil
import platform

def get_system_info():
    """Get basic system information."""
    print("🖥️  System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   CPU: {psutil.cpu_count()} cores")
    print(f"   Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print()

def monitor_resources():
    """Monitor CPU, memory, and disk usage."""
    print("📊 Resource Monitoring (Press Ctrl+C to stop):")
    print("=" * 60)
    print(f"{'Time':<8} {'CPU%':<6} {'Memory%':<8} {'Disk%':<6} {'Network':<15}")
    print("-" * 60)
    
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
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Get network usage
            network = psutil.net_io_counters()
            network_bytes = network.bytes_sent + network.bytes_recv
            
            # Format network bytes
            if network_bytes > 1024**3:
                network_str = f"{network_bytes / (1024**3):.1f}GB"
            elif network_bytes > 1024**2:
                network_str = f"{network_bytes / (1024**2):.1f}MB"
            else:
                network_str = f"{network_bytes / 1024:.1f}KB"
            
            # Print current stats
            print(f"{current_time:<8} {cpu_percent:<6.1f} {memory_percent:<8.1f} {disk_percent:<6.1f} {network_str:<15}")
            
            # Check for high resource usage
            if cpu_percent > 80:
                print(f"⚠️  High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 80:
                print(f"⚠️  High memory usage: {memory_percent:.1f}%")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("\n💡 Tips for NPU monitoring:")
        print("   • Check Task Manager > Performance tab for GPU/NPU usage")
        print("   • Use GPU-Z for detailed GPU statistics")
        print("   • Monitor temperature and power consumption")
        print("   • Look for 'NPU' or 'AI Engine' in device manager")

def main():
    """Main function."""
    print("🚀 NPU Monitoring Script for Windows")
    print("=" * 40)
    
    get_system_info()
    
    print("💡 To monitor NPU usage:")
    print("   1. Run this script in one terminal")
    print("   2. Run your Phi model test in another terminal")
    print("   3. Watch for resource spikes during inference")
    print("   4. Check Task Manager for GPU/NPU activity")
    print()
    
    input("Press Enter to start monitoring...")
    
    monitor_resources()

if __name__ == "__main__":
    main()
