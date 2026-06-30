// 在合适位置添加自动翻译按钮
class ZnAutoTranslate {
    constructor() {
        this.apiBase = "/zn_translation";
        this.initUI();
    }
    
    initUI() {
        // 在设置面板添加按钮
        const menu = document.querySelector('.comfy-menu');
        if (!menu) return;
        
        const btn = document.createElement('button');
        btn.textContent = "🔄 检测新插件";
        btn.title = "扫描并翻译新安装的插件";
        btn.style.cssText = "background: #2d2d2d; color: #fff; border: 1px solid #555; padding: 4px 8px; margin: 4px 0; cursor: pointer; border-radius: 4px;";
        btn.onclick = () => this.scanPlugins();
        
        // 插入到菜单中
        const queueBtn = menu.querySelector('button');
        if (queueBtn && queueBtn.parentNode) {
            queueBtn.parentNode.insertBefore(btn, queueBtn.nextSibling);
        }
    }
    
    async scanPlugins() {
        const btn = document.querySelector('button[title*="扫描"]');
        const originalText = btn.textContent;
        btn.textContent = "⏳ 扫描中...";
        btn.disabled = true;
        
        try {
            // 调用后端 API 或直接显示提示
            const response = await fetch('/zn_translation/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.plugins && result.plugins.length > 0) {
                const names = result.plugins.map(p => p.name).join(', ');
                if (confirm(`发现 ${result.plugins.length} 个未翻译插件:\\n${names}\\n\\n是否现在翻译？`)) {
                    await this.translatePlugins(result.plugins);
                }
            } else {
                alert("✅ 所有插件已翻译，没有新插件！");
            }
        } catch (e) {
            // 如果后端 API 不可用，提示用户运行命令行
            alert("请使用命令行运行扫描:\\npython custom_nodes/comfyui-Zn-translation/tools/scan_now.py");
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }
    
    async translatePlugins(plugins) {
        const btn = document.querySelector('button[title*="扫描"]');
        btn.textContent = "🤖 AI翻译中...";
        
        try {
            const response = await fetch('/zn_translation/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plugins: plugins.map(p => p.name) })
            });
            
            const result = await response.json();
            alert(`翻译完成!\\n成功: ${result.success}\\n失败: ${result.failed}\\n请刷新页面查看效果。`);
        } catch (e) {
            alert("翻译请求失败，请检查 API 配置。");
        } finally {
            btn.textContent = "🔄 检测新插件";
            btn.disabled = false;
        }
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => new ZnAutoTranslate(), 2000);
});
