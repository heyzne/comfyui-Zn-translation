#!/usr/bin/env python3
"""
一键扫描并翻译所有未翻译的插件
用法: python scan_now.py [--api-key YOUR_KEY] [--model gpt-3.5-turbo]
"""

import sys
import os
import argparse
import logging

# 添加到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_translate.scanner import PluginScanner
from auto_translate.extractor import NodeExtractor
from auto_translate.translator import AITranslator
from auto_translate.generator import TranslationGenerator
from auto_translate.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Scan and translate ComfyUI plugins')
    parser.add_argument('--api-key', help='OpenAI API Key')
    parser.add_argument('--api-base', help='API Base URL', default='https://api.openai.com/v1')
    parser.add_argument('--model', help='Model name', default='gpt-3.5-turbo')
    parser.add_argument('--dry-run', action='store_true', help='Preview without generating files')
    parser.add_argument('--force', action='store_true', help='Force re-translate all plugins')
    args = parser.parse_args()
    
    # 配置
    config = Config()
    if args.api_key:
        config.set('api_key', args.api_key)
        config.set('api_base', args.api_base)
        config.set('model', args.model)
    
    # 扫描
    scanner = PluginScanner()
    
    if args.force:
        plugins = scanner.scan_plugins()
        target_plugins = [p for p in plugins if p['has_node_mappings']]
        logger.info(f"Force mode: scanning all {len(target_plugins)} plugins with node mappings")
    else:
        target_plugins = scanner.get_untranslated_plugins()
        outdated = scanner.get_outdated_plugins()
        
        if outdated:
            logger.info(f"Found {len(outdated)} outdated plugins")
            target_plugins.extend(outdated)
        
        logger.info(f"Found {len(target_plugins)} plugins to translate")
    
    if not target_plugins:
        logger.info("All plugins are up to date!")
        return
    
    # 检查API
    if not config.has_api_key and not args.dry_run:
        logger.error("No API key configured. Set it via --api-key or config file")
        print("\nPlease set your API key:")
        print(f"  python scan_now.py --api-key sk-...")
        print("\nOr edit: {config.config_file}")
        return
    
    # 翻译
    extractor = NodeExtractor()
    translator = AITranslator()
    generator = TranslationGenerator()
    
    success = 0
    failed = 0
    
    for plugin in target_plugins:
        logger.info(f"\\nProcessing: {plugin['name']}")
        try:
            plugin_dir = Path(plugin['path'])
            nodes = extractor.extract_from_plugin(plugin_dir)
            
            if not nodes:
                logger.warning(f"  No nodes found in {plugin['name']}")
                continue
            
            logger.info(f"  Found {len(nodes)} nodes")
            
            if args.dry_run:
                logger.info(f"  [DRY RUN] Would translate: {list(nodes.keys())[:3]}...")
                continue
            
            translated = translator.translate_nodes(nodes)
            generator.generate_translation_file(plugin['name'], translated)
            success += 1
            
        except Exception as e:
            logger.error(f"  Failed: {e}")
            failed += 1
    
    logger.info(f"\\n{'='*50}")
    logger.info(f"Done! Success: {success}, Failed: {failed}")
    logger.info(f"Translation files saved to: {config.translation_nodes_path}")

if __name__ == '__main__':
    main()
