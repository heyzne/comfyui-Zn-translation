"""
生成翻译文件
"""

import json
import os
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class TranslationGenerator:
    """翻译文件生成器"""
    
    def __init__(self):
        from .config import Config
        self.config = Config()
        self.output_dir = self.config.translation_nodes_path
    
    def generate_translation_file(self, plugin_name: str, translations: Dict[str, Dict]) -> Path:
        """
        为插件生成翻译文件
        """
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = self.output_dir / f"{plugin_name}.json"
        
        # 如果文件已存在，合并而不是覆盖
        existing = {}
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                logger.info(f"Merging with existing translation: {plugin_name}")
            except Exception as e:
                logger.warning(f"Cannot read existing file: {e}")
        
        # 合并：新翻译优先，但保留旧翻译中已有的
        merged = {**existing}
        for node_name, trans in translations.items():
            if node_name in merged:
                # 更新，保留用户可能手动修改的部分
                merged[node_name].update(trans)
            else:
                merged[node_name] = trans
        
        # 写入
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Generated translation file: {output_file} ({len(merged)} nodes)")
        return output_file
    
    def generate_missing_report(self, plugins: list) -> Path:
        """生成未翻译插件报告"""
        report_file = self.output_dir.parent / "missing_translations.json"
        
        data = {
            "total_untranslated": len(plugins),
            "plugins": plugins
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return report_file
    
    def cleanup_orphaned(self, active_plugins: list) -> int:
        """清理已不存在插件的翻译文件"""
        removed = 0
        active_names = {p['name'] for p in active_plugins}
        
        if not self.output_dir.exists():
            return 0
        
        for file in self.output_dir.glob("*.json"):
            if file.stem not in active_names:
                # 备份后删除
                backup = file.with_suffix('.json.bak')
                file.rename(backup)
                removed += 1
                logger.info(f"Removed orphaned translation: {file.name}")
        
        return removed
