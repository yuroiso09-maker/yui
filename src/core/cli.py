#!/usr/bin/env python3
"""
OTIS Command Line Interface
Simple CLI for controlling the OTIS optimization system
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from loguru import logger
from .main import OTISCore


def print_banner():
    """Print OTIS banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗ ████████╗██╗███████╗                               ║
    ║  ██╔═══██╗╚══██╔══╝██║██╔════╝                               ║
    ║  ██║   ██║   ██║   ██║███████╗                               ║
    ║  ██║   ██║   ██║   ██║╚════██║                               ║
    ║  ╚██████╔╝   ██║   ██║███████║                               ║
    ║   ╚═════╝    ╚═╝   ╚═╝╚══════╝                               ║
    ║                                                               ║
    ║  Optimization and Transformation Intelligence System          ║
    ║  Transform your Linux system into a supercomputer!           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_status(status_data):
    """Print formatted status information"""
    print("\n🚀 OTIS System Status")
    print("=" * 50)
    
    if status_data['running']:
        print(f"Status: ✅ RUNNING")
        print(f"Uptime: {status_data['uptime']:.1f} seconds")
        print(f"Performance Multiplier: {status_data['performance']['performance_multiplier']:.1f}x")
        
        print("\n📊 Engine Status:")
        for engine_name, engine_status in status_data['engines'].items():
            status_icon = "✅" if engine_status.get('enabled', False) else "❌"
            print(f"  {status_icon} {engine_name.capitalize()}: {engine_status.get('enabled', 'Unknown')}")
        
        print("\n💾 System Resources:")
        perf = status_data['performance']
        print(f"  Memory Usage: {perf['memory_usage']:.1f}%")
        print(f"  CPU Usage: {perf['cpu_usage']:.1f}%")
        print(f"  GPU Usage: {perf['gpu_usage']:.1f}%")
        print(f"  Storage Usage: {perf['storage_usage']:.1f}%")
        
    else:
        print(f"Status: ❌ STOPPED")
    
    print()


async def cmd_start(args):
    """Start OTIS optimization"""
    print_banner()
    print(f"🚀 Starting OTIS in {args.mode} mode...")
    
    otis = OTISCore(config_path=args.config)
    success = await otis.start_optimization(mode=args.mode)
    
    if success:
        print("✅ OTIS started successfully!")
        print("Press Ctrl+C to stop...")
        
        try:
            # Keep running until interrupted
            while otis.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping OTIS...")
            await otis.stop_optimization()
            print("✅ OTIS stopped successfully")
    else:
        print("❌ Failed to start OTIS")
        sys.exit(1)


async def cmd_stop(args):
    """Stop OTIS optimization"""
    print("🛑 Stopping OTIS...")
    otis = OTISCore(config_path=args.config)
    success = await otis.stop_optimization()
    
    if success:
        print("✅ OTIS stopped successfully")
    else:
        print("❌ Failed to stop OTIS")
        sys.exit(1)


async def cmd_status(args):
    """Show OTIS status"""
    otis = OTISCore(config_path=args.config)
    status = await otis.get_status()
    
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print_status(status)


async def cmd_optimize(args):
    """Optimize for specific application"""
    if not args.app:
        print("❌ Application name required")
        sys.exit(1)
    
    print(f"🎯 Optimizing system for {args.app}...")
    otis = OTISCore(config_path=args.config)
    success = await otis.optimize_for_application(args.app, args.app_type)
    
    if success:
        print(f"✅ System optimized for {args.app}")
    else:
        print(f"❌ Failed to optimize for {args.app}")
        sys.exit(1)


async def cmd_info(args):
    """Show system information"""
    from .system_info import SystemInfo
    
    print_banner()
    print("🔍 System Information")
    print("=" * 50)
    
    system_info = SystemInfo()
    info = system_info.get_detailed_info()
    
    # System info
    sys_info = info['system']
    print(f"OS: {sys_info['platform']} {sys_info['release']}")
    print(f"Architecture: {sys_info['machine']}")
    
    # CPU info
    cpu_info = info['cpu']
    print(f"CPU: {cpu_info.brand}")
    print(f"Cores: {cpu_info.cores_physical} physical, {cpu_info.cores_logical} logical")
    print(f"Frequency: {cpu_info.frequency_current:.0f} MHz (max: {cpu_info.frequency_max:.0f} MHz)")
    
    # Memory info
    mem_info = info['memory']
    print(f"Memory: {mem_info.total_gb:.1f}GB total, {mem_info.available_gb:.1f}GB available ({mem_info.usage_percent:.1f}% used)")
    
    # GPU info
    gpu_info = info['gpu']
    for i, gpu in enumerate(gpu_info):
        print(f"GPU {i+1}: {gpu.name} ({gpu.type})")
    
    # Storage info
    storage_info = info['storage']
    for i, storage in enumerate(storage_info):
        print(f"Storage {i+1}: {storage.total_gb:.1f}GB total, {storage.free_gb:.1f}GB free ({storage.usage_percent:.1f}% used)")
    
    # Capabilities
    print("\n🔧 System Capabilities:")
    capabilities = info['capabilities']
    for capability, available in capabilities.items():
        status = "✅" if available else "❌"
        print(f"  {status} {capability.replace('_', ' ').title()}")
    
    # Recommendations
    print("\n💡 Optimization Recommendations:")
    recommendations = system_info.get_optimization_recommendations()
    
    if recommendations['memory']['enable_zram']:
        print(f"  💾 Enable zRAM with {recommendations['memory']['zram_size_percent']}% of memory")
    
    if recommendations['gpu']['enable_llvmpipe']:
        print(f"  🎮 Enable LLVMPIPE software rendering with {recommendations['gpu']['software_rendering_threads']} threads")
    
    print(f"  📁 Use compression level {recommendations['storage']['compression_level']}")
    print(f"  🚀 Recommended performance mode: {recommendations['performance_mode']}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="OTIS - Optimization and Transformation Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  otis start                    # Start with auto mode
  otis start --mode gaming      # Start in gaming mode
  otis status                   # Show current status
  otis optimize --app firefox   # Optimize for Firefox
  otis info                     # Show system information
        """
    )
    
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start OTIS optimization')
    start_parser.add_argument('--mode', choices=['auto', 'gaming', 'productivity', 'extreme'], 
                             default='auto', help='Optimization mode')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop OTIS optimization')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show OTIS status')
    status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize for specific application')
    optimize_parser.add_argument('--app', required=True, help='Application name')
    optimize_parser.add_argument('--app-type', choices=['game', 'office', 'media', 'development'], 
                                default='auto', help='Application type')
    
    # Info command
    subparsers.add_parser('info', help='Show system information and recommendations')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    
    # Run command
    try:
        if args.command == 'start':
            asyncio.run(cmd_start(args))
        elif args.command == 'stop':
            asyncio.run(cmd_stop(args))
        elif args.command == 'status':
            asyncio.run(cmd_status(args))
        elif args.command == 'optimize':
            asyncio.run(cmd_optimize(args))
        elif args.command == 'info':
            asyncio.run(cmd_info(args))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()