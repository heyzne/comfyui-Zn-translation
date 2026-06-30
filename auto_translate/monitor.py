"""
文件监控服务 - 实时监控 custom_nodes 目录变化
"""

import os
import time
import threading
from pathlib import Path
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class PluginMonitor:
    """插件目录监控器"""
    
    def __init__(self, callback: Callable = None):
        from .config import Config
        self.config = Config()
        self.custom_nodes_path = self.config.custom_nodes_path
        self.callback = callback or self._default_callback
        self.interval = self.config.get('check_interval', 60)
        self._running = False
        self._thread = None
        self._last_state = {}
    
    def _default_callback(self, new_plugins: list):
        """默认回调：自动翻译新插件"""
        from .scanner import PluginScanner
        from .extractor import NodeExtractor
        from .translator import AITranslator
        from .generator import TranslationGenerator
        
        logger.info(f"Auto-translating {len(new_plugins)} new plugins...")
        
        translator = AITranslator()
        generator = TranslationGenerator()
        extractor = NodeExtractor()
        
        for plugin in new_plugins:
            try:
                plugin_dir = Path(plugin['path'])
                nodes = extractor.extract_from_plugin(plugin_dir)
                
                if nodes:
                    translated = translator.translate_nodes(nodes)
                    generator.generate_translation_file(plugin['name'], translated)
                    logger.info(f"Auto-translated: {plugin['name']}")
            except Exception as e:
                logger.error(f"Failed to translate {plugin['name']}: {e}")
    
    def _scan_state(self) -> dict:
        """扫描当前状态"""
        state = {}
        if not self.custom_nodes_path.exists():
            return state
        
        for item in self.custom_nodes_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 记录目录修改时间
                mtime = os.path.getmtime(item)
                state[item.name] = mtime
        
        return state
    
    def start(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._last_state = self._scan_state()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Plugin monitor started (interval: {self.interval}s)")
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Plugin monitor stopped")
    
    def _run(self):
        """监控循环"""
        while self._running:
            try:
                current_state = self._scan_state()
                
                # 检测新增
                new_plugins = []
                for name, mtime in current_state.items():
                    if name not in self._last_state:
                        new_plugins.append({
                            'name': name,
                            'path': str(self.custom_nodes_path / name),
                            'mtime': mtime
                        })
                
                if new_plugins:
                    self.callback(new_plugins)
                
                self._last_state = current_state
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            # 间隔检查
            for _ in range(self.interval):
                if not self._running:
                    break
                time.sleep(1)
