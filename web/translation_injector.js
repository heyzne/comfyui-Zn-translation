(function() {
    'use strict';

    const TRANSLATION_API = '/auto_translator/api/translations';
    let translationData = {};
    let isLoaded = false;

    // 面板UI翻译字典
    const uiTranslations = {
        // 主面板按钮
        "Queue Prompt": "队列提示",
        "Extra options": "额外选项",
        "Queue Front": "队列前置",
        "View Queue": "查看队列",
        "View History": "查看历史",
        "Save": "保存",
        "Save (API Format)": "保存 (API格式)",
        "Load": "加载",
        "Refresh": "刷新",
        "Clipspace": "剪贴板",
        "Clear": "清除",
        "Load Default": "加载默认",
        "Reset View": "重置视图",
        "Manager": "管理器",
        "Share": "分享",

        // 菜单
        "Workflow": "工作流",
        "Edit": "编辑",
        "View": "视图",
        "Help": "帮助",

        // 节点菜单
        "Add Node": "添加节点",
        "Delete": "删除",
        "Collapse": "折叠",
        "Pin": "固定",
        "Colors": "颜色",
        "Shapes": "形状",

        // 右键菜单
        "Show/Hide": "显示/隐藏",
        "Mute": "静音",
        "Bypass": "绕过",
        "Convert to input": "转换为输入",
        "Convert to widget": "转换为组件",
        "Convert seed to int": "转换种子为整数",
        "Reroute": "重新路由",

        // 设置
        "Settings": "设置",
        "Comfy Settings": "Comfy设置",
        "Theme": "主题",
        "Color Palette": "调色板",
        "Text Widgets": "文本组件",

        // 搜索
        "Search": "搜索",
        "Search for nodes": "搜索节点",

        // 状态
        "Ready": "就绪",
        "Executing": "执行中",
        "Error": "错误",
        "Loading": "加载中",

        // 其他
        "Node Library": "节点库",
        "Queue Size": "队列大小",
        "Auto Queue": "自动队列",
        "Interrupt": "中断",
        "Batch Count": "批次数量",
    };

    function waitForComfyUI() {
        return new Promise((resolve) => {
            if (window.app && window.app.graph) {
                resolve();
            } else {
                const check = setInterval(() => {
                    if (window.app && window.app.graph) {
                        clearInterval(check);
                        resolve();
                    }
                }, 500);
            }
        });
    }

    async function loadTranslations() {
        try {
            const response = await fetch(TRANSLATION_API);
            if (response.ok) {
                translationData = await response.json();
                isLoaded = true;
                applyAllTranslations();
            }
        } catch (e) {
            console.error('[AutoTranslator] load failed:', e);
        }
    }

    function applyAllTranslations() {
        translateUI();
        translateNodes();
        translateMenus();
    }

    // 翻译UI面板
    function translateUI() {
        // 翻译按钮文字
        document.querySelectorAll('button, .comfy-menu button, .comfy-menu span').forEach(el => {
            const text = el.textContent.trim();
            if (uiTranslations[text]) {
                el.textContent = uiTranslations[text];
            }
        });

        // 翻译标题
        document.querySelectorAll('.comfy-menu h4, .comfy-menu h3, .comfy-menu h2').forEach(el => {
            const text = el.textContent.trim();
            if (uiTranslations[text]) {
                el.textContent = uiTranslations[text];
            }
        });

        // 翻译label
        document.querySelectorAll('label').forEach(el => {
            const text = el.textContent.trim();
            if (uiTranslations[text]) {
                el.textContent = uiTranslations[text];
            }
        });

        // 翻译placeholder
        document.querySelectorAll('input[placeholder]').forEach(el => {
            const text = el.placeholder.trim();
            if (uiTranslations[text]) {
                el.placeholder = uiTranslations[text];
            }
        });
    }

    // 翻译节点
    function translateNodes() {
        if (!window.LiteGraph || !isLoaded) return;

        // 翻译已存在的节点
        if (window.app && window.app.graph) {
            window.app.graph._nodes.forEach(node => translateNode(node));
        }

        // 拦截新节点创建
        const originalAddNode = window.LiteGraph.createNode;
        window.LiteGraph.createNode = function(type, title, options) {
            const node = originalAddNode.call(this, type, title, options);
            if (node) {
                setTimeout(() => translateNode(node), 50);
            }
            return node;
        };
    }

    function translateNode(node) {
        if (!node || !node.comfyClass) return;

        const className = node.comfyClass;

        // 翻译节点标题
        const titleKey = `node.${className}.title`;
        if (translationData[titleKey] && node.title !== translationData[titleKey]) {
            node.title = translationData[titleKey];
        }

        // 翻译输入参数
        if (node.inputs) {
            node.inputs.forEach(input => {
                const inputKey = `node.${className}.input.${input.name}`;
                if (translationData[inputKey]) {
                    input.label = translationData[inputKey];
                }
            });
        }

        // 翻译输出参数
        if (node.outputs) {
            node.outputs.forEach(output => {
                const outputKey = `node.${className}.output.${output.name}`;
                if (translationData[outputKey]) {
                    output.label = translationData[outputKey];
                }
            });
        }
    }

    // 翻译菜单
    function translateMenus() {
        // 观察菜单变化
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        translateElement(node);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    function translateElement(el) {
        // 翻译菜单项
        if (el.classList && (el.classList.contains('litegraph') || el.classList.contains('lite-menu'))) {
            el.querySelectorAll('span, div, li').forEach(item => {
                const text = item.textContent.trim();
                if (uiTranslations[text]) {
                    item.textContent = uiTranslations[text];
                }
            });
        }

        // 翻译搜索建议
        if (el.classList && el.classList.contains('searchbox')) {
            el.querySelectorAll('.item').forEach(item => {
                const text = item.textContent.trim();
                // 尝试从翻译数据中查找
                for (const [key, value] of Object.entries(translationData)) {
                    if (key.endsWith('.title') && text.includes(key.split('.')[1])) {
                        item.textContent = item.textContent.replace(text, value);
                        break;
                    }
                }
            });
        }
    }

    async function init() {
        await waitForComfyUI();

        // 立即翻译UI
        translateUI();

        // 加载翻译数据并翻译节点
        await loadTranslations();

        // 定期刷新翻译
        setInterval(() => {
            translateUI();
            loadTranslations();
        }, 5000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
