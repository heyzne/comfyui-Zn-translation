"""
配置管理
"""

import os
import json
from pathlib import Path

class Config:
    """配置类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        "comfyui_path": "",  # 自动检测
        "custom_nodes_path": "",  # 自动检测
        "translation_path": "",  # 自动检测
        "api_key": "",  # AI翻译API密钥
        "api_base": "https://api.openai.com/v1",  # API基础地址
        "model": "gpt-3.5-turbo",  # 默认模型
        "batch_size": 10,  # 批量翻译数量
        "auto_translate": True,  # 是否自动翻译
        "monitor_enabled": False,  # 是否启用监控
        "check_interval": 60,  # 监控检查间隔（秒）
        "translate_descriptions": True,  # 是否翻译描述
        "translate_widgets": True,  # 是否翻译参数
        "cache_translations": True,  # 是否缓存翻译结果
    }
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent
        self.config_file = self.config_dir / "auto_translate_config.json"
        self.config = self.load_config()
        self._detect_paths()
    
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return {**self.DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def _detect_paths(self):
        """自动检测路径"""
        # 检测ComfyUI路径
        if not self.config["comfyui_path"]:
            current = self.config_dir
            # 向上查找ComfyUI目录
            while current.name != "custom_nodes" and current.parent != current:
                current = current.parent
            
            if current.name == "custom_nodes":
                self.config["custom_nodes_path"] = str(current)
                comfyui = current.parent
                self.config["comfyui_path"] = str(comfyui)
                # 翻译文件路径
                trans_path = self.config_dir / "translations" / "zh-CN"
                self.config["translation_path"] = str(trans_path)
                self.save_config()
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    @property
    def custom_nodes_path(self):
        return Path(self.config.get("custom_nodes_path", ""))
    
    @property
    def translation_nodes_path(self):
        return Path(self.config.get("translation_path", "")) / "Nodes"
    
    @property
    def has_api_key(self):
        return bool(self.config.get("api_key"))
