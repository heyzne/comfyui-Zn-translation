/**
 * Zn Translation - ComfyUI 前端翻译插件
 * 支持中英互译，API 配置在 ComfyUI 设置界面
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { LOCALES, getCurrentLocale, setCurrentLocale, getAvailableLocales } from "./LocaleMap.js";

const ZN_TRANSLATION_ID = "comfyui-zn-translation";
let translationData = null;
let currentLocale = getCurrentLocale();
let menuObserver = null;

// ============ 翻译核心 ============

async function loadTranslation(locale) {
    try {
        const resp = await fetch("/zn/get_translation", {
            method: "POST",
            body: new URLSearchParams({ locale })
        });
        const data = await resp.json();
        if (data) {
            translationData = data;
            currentLocale = locale;
            return true;
        }
    } catch (e) {
        console.error("[Zn-Translation] 加载翻译失败:", e);
    }
    return false;
}

function t(key, fallback = null) {
    if (!translationData) return fallback || key;

    if (translationData.Nodes && translationData.Nodes[key]) {
        return translationData.Nodes[key];
    }
    if (translationData.NodeCategory && translationData.NodeCategory[key]) {
        return translationData.NodeCategory[key];
    }
    if (translationData.Menu && translationData.Menu[key]) {
        return translationData.Menu[key];
    }
    return fallback || key;
}

// ============ 节点标题翻译 ============

function translateNodeTitle(node) {
    if (!node || !node.comfyClass) return;
    const translated = t(node.comfyClass);
    if (translated && translated !== node.comfyClass) {
        node.title = translated;
    }
}

function translateNodeInputs(node) {
    if (!node.inputs) return;
    for (const input of node.inputs) {
        const key = `${node.comfyClass}|${input.name}`;
        const translated = t(key) || t(input.name);
        if (translated && translated !== input.name) {
            input.label = translated;
        }
    }
}

function translateNodeWidgets(node) {
    if (!node.widgets) return;
    for (const widget of node.widgets) {
        const key = `${node.comfyClass}|${widget.name}`;
        const translated = t(key) || t(widget.name);
        if (translated && translated !== widget.name) {
            widget.label = translated;
        }
    }
}

// ============ 全面菜单翻译（修复右侧菜单） ============

function translateAllMenus() {
    if (!translationData || !translationData.Menu) return;

    // 1. 右侧主菜单按钮 - 多种选择器覆盖不同版本
    const rightMenuSelectors = [
        '.comfy-menu button',
        '.comfy-menu .comfy-menu-btn',
        '#comfy-menu button',
        '.comfyui-menu button',
        '.comfyui-menu .p-button',
        '.p-menubar button',
        '.comfyui-menu .p-button-label',
        '.comfyui-menu .p-menuitem-text',
        '.comfyui-menu .p-menubar-button',
        '.comfyui-menu .action-button',
        '.comfyui-menu .comfyui-button',
        '[class*="comfy-menu"] button',
        '[class*="ComfyMenu"] button',
        '.comfyui-menu > div > button',
        '.comfyui-menu > div > div > button',
        '.comfyui-menu .v-list-item__title',
        '.comfyui-menu .v-btn__content',
        '.comfyui-menu .q-btn__content',
    ];

    rightMenuSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(item => {
            translateElementText(item);
        });
    });

    // 2. 下拉菜单 / 上下文菜单
    const dropdownSelectors = [
        '.litecontextmenu .litemenu-entry',
        '.p-dropdown-item',
        '.p-menuitem',
        '.p-menuitem-text',
        '.p-menu-list .p-menuitem-link',
        '.comfy-context-menu-item',
        '.p-tieredmenu .p-menuitem',
        '.p-contextmenu .p-menuitem',
        '.p-menubar .p-submenu-list .p-menuitem',
        '.v-menu__content .v-list-item__title',
        '.q-menu .q-item__label',
    ];

    dropdownSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(item => {
            translateElementText(item);
        });
    });

    // 3. 对话框按钮
    const dialogSelectors = [
        '.litegraph .dialog .dialog-content button',
        '.p-dialog button',
        '.p-confirm-dialog button',
        '.comfy-modal button',
        '.comfy-dialog button',
        '.v-dialog button',
        '.q-dialog button',
    ];

    dialogSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(item => {
            translateElementText(item);
        });
    });

    // 4. 设置面板标签
    const settingSelectors = [
        '.comfy-settings .setting-label',
        '.comfy-setting-name',
        '.p-field label',
        '.p-inputtext + label',
        '.setting-name',
        '.comfy-setting-row label',
        '.settings-row label',
    ];

    settingSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(item => {
            translateElementText(item);
        });
    });

    // 5. 管理器菜单特殊处理
    const managerSelectors = [
        '.comfy-manager-menu-item',
        '.manager-menu-item',
        '[class*="manager"] button',
        '[class*="Manager"] button',
        '[class*="manager"] .p-button-label',
        '[class*="Manager"] .p-button-label',
    ];

    managerSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(item => {
            translateElementText(item);
        });
    });

    // 6. 工具提示
    document.querySelectorAll('[title], [data-tooltip], .p-tooltip-text').forEach(item => {
        const title = item.getAttribute('title');
        if (title) {
            const translated = t(title);
            if (translated && translated !== title) {
                item.setAttribute('title', translated);
            }
        }
    });

    // 7. 面板标题
    const panelSelectors = [
        '.comfy-panel-header',
        '.panel-header',
        '.sidebar-header',
        '.comfy-sidebar-header',
        '.comfyui-panel-header',
    ];

    panelSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(item => {
            translateElementText(item);
        });
    });

    // 8. 按钮文字内容（通用兜底）
    document.querySelectorAll('button').forEach(btn => {
        // 只翻译有明确文本内容的按钮
        if (btn.childNodes.length === 1 && btn.childNodes[0].nodeType === Node.TEXT_NODE) {
            translateElementText(btn);
        }
    });
}

function translateElementText(element) {
    if (!element || element.hasAttribute('data-zn-translated')) return;

    const text = element.textContent.trim();
    if (!text || text.length === 0) return;

    const translated = t(text);
    if (translated && translated !== text) {
        // 保留原有子元素，只替换文本节点
        const childNodes = Array.from(element.childNodes);
        for (const node of childNodes) {
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                node.textContent = translated;
            }
        }
        element.setAttribute('data-zn-translated', 'true');
    }
}

// ============ 动态监听菜单变化 ============

function setupMenuObserver() {
    if (menuObserver) menuObserver.disconnect();

    menuObserver = new MutationObserver((mutations) => {
        let shouldTranslate = false;
        for (const mutation of mutations) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // 检测新添加的菜单元素
                        if (node.matches && (
                            node.matches('.litecontextmenu, .p-menu, .p-dropdown-panel, .comfy-menu, .comfyui-menu') ||
                            node.querySelector('.litecontextmenu, .p-menu, .p-dropdown-panel')
                        )) {
                            shouldTranslate = true;
                            break;
                        }
                    }
                }
            }
        }
        if (shouldTranslate) {
            setTimeout(translateAllMenus, 50);
        }
    });

    menuObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// ============ 设置面板（API标注更清晰） ============

function createSettings() {
    // 界面语言
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.locale`,
        name: "界面语言 (Zn Translation)",
        type: "combo",
        options: getAvailableLocales().map(l => ({ value: l.code, text: l.name })),
        defaultValue: "zh-CN",
        onChange: async (value) => {
            setCurrentLocale(value);
            await loadTranslation(value);
            // 清除已翻译标记，重新翻译
            document.querySelectorAll('[data-zn-translated]').forEach(el => {
                el.removeAttribute('data-zn-translated');
            });
            app.graph.setDirtyCanvas(true, true);
            translateAllMenus();
        }
    });

    // 翻译 API 选择
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.translation_api`,
        name: "在线翻译 API 服务商",
        type: "combo",
        options: [
            { value: "libre", text: "LibreTranslate (免费公共API，国内可能慢)" },
            { value: "baidu", text: "百度翻译 (国内推荐，需申请密钥)" },
            { value: "youdao", text: "有道翻译 (国内推荐，需申请密钥)" },
            { value: "custom", text: "自定义 API (填写下方地址和密钥)" }
        ],
        defaultValue: "libre"
    });

    // API 密钥 - 根据选择的API动态显示提示
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.api_key`,
        name: "API 密钥 / AppKey",
        type: "text",
        defaultValue: "",
        tooltip: "百度: appid:secret | 有道: appKey:appSecret | 自定义: 按接口要求填写"
    });

    // 自定义 API 地址
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.api_url`,
        name: "自定义 API 接口地址 (选自定义API时必填)",
        type: "text",
        defaultValue: "",
        tooltip: "例如: http://localhost:5000/translate 或你的自建翻译服务地址"
    });

    // 自动翻译开关
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.auto_translate`,
        name: "启用实时自动翻译 (消耗API额度)",
        type: "boolean",
        defaultValue: false,
        tooltip: "开启后会实时调用在线API翻译未覆盖的文本，可能产生费用"
    });

    // 保存配置按钮
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.save_config`,
        name: "💾 保存以上翻译配置到文件",
        type: "button",
        tooltip: "将当前设置保存到 config.json，重启后生效",
        onChange: async () => {
            const config = {
                translation_api: app.ui.settings.getSettingValue(`${ZN_TRANSLATION_ID}.translation_api`, "libre"),
                api_key: app.ui.settings.getSettingValue(`${ZN_TRANSLATION_ID}.api_key`, ""),
                api_url: app.ui.settings.getSettingValue(`${ZN_TRANSLATION_ID}.api_url`, ""),
                enable_auto_translate: app.ui.settings.getSettingValue(`${ZN_TRANSLATION_ID}.auto_translate`, false)
            };

            try {
                const resp = await fetch("/zn/save_config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(config)
                });
                const result = await resp.json();
                if (result.status === "success") {
                    console.log("[Zn-Translation] 配置已保存到 config.json");
                } else {
                    console.error("[Zn-Translation] 保存失败:", result.message);
                }
            } catch (e) {
                console.error("[Zn-Translation] 保存配置失败:", e);
                console.error("[Zn-Translation] 网络错误，保存失败");
            }
        }
    });

    // API 申请帮助链接
    app.ui.settings.addSetting({
        id: `${ZN_TRANSLATION_ID}.api_help`,
        name: "📖 API 申请帮助",
        type: "button",
        tooltip: "查看如何申请百度/有道翻译API密钥",
        onChange: () => {
            window.open("https://fanyi-api.baidu.com/doc/21", "_blank");
        }
    });
}

// ============ 节点注册 ============

app.registerExtension({
    name: ZN_TRANSLATION_ID,
    async setup() {
        console.log("[Zn-Translation] 初始化中...");

        await loadTranslation(currentLocale);
        createSettings();

        // 监听节点添加
        const originalOnNodeAdded = app.graph.onNodeAdded;
        app.graph.onNodeAdded = function(node) {
            if (originalOnNodeAdded) originalOnNodeAdded.call(this, node);
            translateNodeTitle(node);
            translateNodeInputs(node);
            translateNodeWidgets(node);
        };

        // 监听画布渲染，翻译菜单
        const originalDraw = app.graph.draw;
        app.graph.draw = function() {
            translateAllMenus();
            return originalDraw.call(this);
        };

        // 翻译现有节点
        for (const node of app.graph._nodes) {
            translateNodeTitle(node);
            translateNodeInputs(node);
            translateNodeWidgets(node);
        }

        // 启动菜单变化监听
        setupMenuObserver();

        // 初始翻译一次
        setTimeout(translateAllMenus, 500);
        setTimeout(translateAllMenus, 1500);

        console.log("[Zn-Translation] 初始化完成，当前语言:", currentLocale);
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name && translationData && translationData.Nodes) {
            const translated = translationData.Nodes[nodeData.name];
            if (translated) {
                nodeData.display_name = translated;
            }
        }
    }
});
