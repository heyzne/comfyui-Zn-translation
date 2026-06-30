#!/usr/bin/env python3
"""
安装/卸载后台监控服务
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def install_service():
    """安装为系统服务（跨平台）"""
    from auto_translate.config import Config
    config = Config()
    config.set('monitor_enabled', True)
    
    # 创建启动脚本
    script_dir = Path(__file__).parent.parent
    monitor_script = script_dir / 'auto_translate_monitor.py'
    
    with open(monitor_script, 'w') as f:
        f.write('''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto_translate.monitor import PluginMonitor
monitor = PluginMonitor()
monitor.start()
print("Monitor started. Press Ctrl+C to stop.")
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    monitor.stop()
''')
    
    print(f"Monitor script created: {monitor_script}")
    print("To start monitoring:")
    print(f"  python {monitor_script}")
    print("\\nOr add to your system startup:")
    print("  Windows: Task Scheduler")
    print("  Linux: systemd service")
    print("  macOS: launchd")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['install', 'uninstall', 'start', 'stop'])
    args = parser.parse_args()
    
    if args.action == 'install':
        install_service()
    elif args.action == 'uninstall':
        from auto_translate.config import Config
        config = Config()
        config.set('monitor_enabled', False)
        print("Monitor disabled")
    elif args.action == 'start':
        from auto_translate.monitor import PluginMonitor
        monitor = PluginMonitor()
        monitor.start()
        print("Monitor started")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
    elif args.action == 'stop':
        print("Please stop the monitor process manually (Ctrl+C or kill)")

if __name__ == '__main__':
    main()
