import { app } from "../../scripts/app.js";

// ============================================================
// AIGODLIKE 兼容架构 - 核心翻译工具类 TUtils
// 复刻自 AIGODLIKE/AIGODLIKE-ComfyUI-Translation
// ============================================================

(function () {
	'use strict';

	// ============================================================
	// 工具函数
	// ============================================================

	/** 检测是否包含中文字符 */
	function containsChinese(text) {
		if (!text || typeof text !== 'string') return false;
		return /[\u4e00-\u9fff\u3400-\u4dbf]/.test(text);
	}

	/** 检测文本是否已被翻译 */
	function isAlreadyTranslated(originalName, currentLabel) {
		if (!originalName || !currentLabel) return false;
		if (originalName === currentLabel) return false;
		return containsChinese(currentLabel);
	}

	/** 检测对象属性是否有原生翻译 */
	function hasNativeTranslation(obj, property) {
		if (!obj || !obj.hasOwnProperty(property)) return false;
		const val = obj[property];
		if (!val || typeof val !== 'string') return false;
		return containsChinese(val);
	}

	/** 后缀启发式翻译 */
	function suffixHeuristic(key) {
		if (!key || typeof key !== 'string') return null;
		const map = {
			'_embeds': '嵌入', '_args': '参数', '_samples': '样本',
			'_latent': '潜空间', '_image': '图像', '_mask': '蒙版',
			'_model': '模型', '_clip': 'CLIP', '_vae': 'VAE',
			'_text': '文本', '_noise': '噪声', '_conditioning': '条件',
			'_controlnet': 'ControlNet', '_lora': 'LoRA',
		};
		for (const [suf, tr] of Object.entries(map)) {
			if (key.endsWith(suf)) return tr;
		}
		return null;
	}

	/** 是否新前端 (> 1.2) */
	function isNewUI() {
		return window.__COMFYUI_FRONTEND_VERSION__ && window.__COMFYUI_FRONTEND_VERSION__ > "1.2";
	}

	// ============================================================
	// TUtils - 复刻 AIGODLIKE 核心翻译工具类
	// ============================================================

	class TUtils {
		static LOCALE_ID = "ZN.Locale";
		static LOCALE_ID_LAST = "ZN.LocaleLast";
		static LOCALE = "zh-CN";

		/** 翻译字典：{ Menu, Nodes, NodeCategory } */
		static T = {
			Menu: {},
			Nodes: {},
			NodeCategory: {},
		};

		/** 合并后的 Menu（含 NodeCategory） */
		static Menu = {};

		/** DOM 元素引用 */
		static ELS = {};

		// --------------------------------------------------------
		// 翻译查找
		// --------------------------------------------------------

		static MT(txt) {
			if (!txt || typeof txt !== 'string') return null;
			const trimmed = txt.trim();
			if (!trimmed) return null;
			if (containsChinese(txt)) return null;
			// 精确匹配
			if (this.Menu.hasOwnProperty(txt)) return this.Menu[txt];
			if (this.Menu.hasOwnProperty(trimmed)) return this.Menu[trimmed];
			// 省略号后缀匹配
			const noEllipsis = trimmed.replace(/\.{2,3}$/, '');
			if (noEllipsis !== trimmed && this.Menu.hasOwnProperty(noEllipsis)) {
				return this.Menu[noEllipsis] + '...';
			}
			return null;
		}

		// --------------------------------------------------------
		// 语言设置
		// --------------------------------------------------------

		static setLocale(locale) {
			localStorage.setItem(this.LOCALE_ID, locale);
			localStorage.setItem(this.LOCALE_ID_LAST, locale);
			// 刷新页面使语言生效
			window.location.reload();
		}

		static getLocale() {
			let locale = localStorage.getItem(this.LOCALE_ID);
			if (locale === null) {
				// 从 ComfyUI 设置中读取
				let s = localStorage.getItem(`Comfy.Settings.${this.LOCALE_ID}`);
				if (s) locale = s.replace(/^\"(.*)\"$/, "$1");
			}
			return locale || this.LOCALE;
		}

		// --------------------------------------------------------
		// 同步翻译数据（参考 AIGODLIKE syncTranslation）
		// --------------------------------------------------------

	static syncTranslation(OnFinished) {
		const locale = this.getLocale();
		const url = "/zn_translation/get_data?locale=" + encodeURIComponent(locale);

		// 异步请求，避免阻塞 UI 线程（同步请求会导致搜索框卡死）
		const request = new XMLHttpRequest();
		request.open("GET", url, true);
		request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

		request.onload = function () {
			if (request.status !== 200) {
				console.warn("[ZN-Translation] API 返回非200状态:", request.status);
				if (OnFinished) OnFinished();
				return;
			}
			try {
				const resp = JSON.parse(request.responseText);

				// 合并后端数据到 T
				for (const key in TUtils.T) {
					if (key in resp) {
						TUtils.T[key] = resp[key];
					}
				}

				// 合并 NodeCategory 到 Menu
				TUtils.Menu = Object.assign({}, TUtils.T.Menu, TUtils.T.NodeCategory);

				// 提取节点 title 到 Menu（用于搜索框翻译）
				for (const key in TUtils.T.Nodes) {
					const node = TUtils.T.Nodes[key];
					if (node && node["title"]) {
						TUtils.Menu[key] = node["title"];
					}
				}

				// 将节点 inputs/widgets 的 snake_case 键合并到 Menu
				for (const key in TUtils.T.Nodes) {
					const node = TUtils.T.Nodes[key];
					if (!node) continue;
					for (const k of ['inputs', 'widgets']) {
						if (node[k]) {
							for (const sk in node[k]) {
								if (sk.includes('_') && !containsChinese(sk)) {
									TUtils.Menu[sk] = node[k][sk];
								}
							}
						}
					}
				}

				console.log("[ZN-Translation] 翻译数据加载完成: Menu=" +
					Object.keys(TUtils.Menu).length +
					" Nodes=" + Object.keys(TUtils.T.Nodes).length +
					" Categories=" + Object.keys(TUtils.T.NodeCategory).length);
			} catch (e) {
				console.warn("[ZN-Translation] 解析翻译数据失败:", e);
			}
			if (OnFinished) OnFinished();
		};

		request.onerror = function () {
			console.warn("[ZN-Translation] 翻译数据请求失败，使用内置字典");
			if (OnFinished) OnFinished();
		};

		request.send();
	}

		// --------------------------------------------------------
		// 增强滑块显示数值（复刻 enhandeDrawNodeWidgets）
		// --------------------------------------------------------

		static enhandeDrawNodeWidgets() {
			if (!window.LGraphCanvas) return;
			const drawNodeWidgets = LGraphCanvas.prototype.drawNodeWidgets;
			if (!drawNodeWidgets) return;

			LGraphCanvas.prototype.drawNodeWidgets = function (node, posY, ctx, active_widget) {
				if (!node.widgets || !node.widgets.length) return 0;

				const widgets = node.widgets.filter(w => w.type === "slider");
				widgets.forEach(w => {
					w._ori_label = w.label;
					const fixed = w.options && w.options.precision != null ? w.options.precision : 3;
					w.label = (w.label || w.name) + ": " + Number(w.value).toFixed(fixed).toString();
				});

				let result;
				try {
					result = drawNodeWidgets.call(this, node, posY, ctx, active_widget);
				} finally {
					widgets.forEach(w => {
						w.label = w._ori_label;
						delete w._ori_label;
					});
				}
				return result;
			};
		}

		// --------------------------------------------------------
		// 节点类型翻译（复刻 applyNodeTypeTranslationEx）
		// --------------------------------------------------------

		static applyNodeTypeTranslationEx(nodeName) {
			if (!window.LiteGraph || !LiteGraph.registered_node_types) return;
			const nodeType = LiteGraph.registered_node_types[nodeName];
			if (!nodeType) return;

			const nodesT = this.T.Nodes;
			const class_type = nodeType.comfyClass || nodeType.type;
			if (!class_type) return;

			if (nodesT.hasOwnProperty(class_type)) {
				const t = nodesT[class_type];
				if (t["title"] && !hasNativeTranslation(nodeType, 'title')) {
					nodeType.title = t["title"];
				}
			}
		}

		/** 批量翻译所有已注册节点类型 */
		static applyNodeTypeTranslation() {
			if (!window.LiteGraph || !LiteGraph.registered_node_types) return;
			const nodesT = this.T.Nodes;
			for (const nodeName in LiteGraph.registered_node_types) {
				const nodeType = LiteGraph.registered_node_types[nodeName];
				if (!nodeType) continue;
				const class_type = nodeType.comfyClass || nodeType.type;
				if (!class_type) continue;
				if (nodesT.hasOwnProperty(class_type)) {
					const t = nodesT[class_type];
					if (t["title"] && !hasNativeTranslation(nodeType, 'title')) {
						nodeType.title = t["title"];
					}
				}
			}
		}

		// --------------------------------------------------------
		// Vue 节点定义翻译（复刻 applyVueNodeDisplayNameTranslation / applyVueNodeTranslation）
		// --------------------------------------------------------

		static applyVueNodeDisplayNameTranslation(nodeDef) {
			const nodesT = this.T.Nodes;
			const class_type = nodeDef.name;
			if (nodesT.hasOwnProperty(class_type)) {
				nodeDef.display_name = nodesT[class_type]["title"] || nodeDef.display_name;
			}
		}

		static applyVueNodeTranslation(nodeDef) {
			const catsT = this.T.NodeCategory;
			if (!nodeDef.category) return;
			const catArr = nodeDef.category.split("/");
			nodeDef.category = catArr.map(cat => catsT[cat] || cat).join("/");
		}

		// --------------------------------------------------------
		// 节点实例翻译（复刻 applyNodeTranslation）
		// --------------------------------------------------------

	static applyNodeTranslation(node) {
		try {
			if (!node) return;
			// 防止重复翻译同一节点实例
			if (node._zn_translated) return;
			node._zn_translated = true;

			const keys = ["inputs", "outputs", "widgets"];
			const nodesT = this.T.Nodes;
			const class_type = node.constructor.comfyClass || node.constructor.type;
			if (!class_type) return;

				// 没有翻译数据时，还原原始标签
				if (!nodesT.hasOwnProperty(class_type)) {
					for (const key of keys) {
						if (!node.hasOwnProperty(key) || !Array.isArray(node[key])) continue;
						node[key].forEach(item => {
							if (item && item.hasOwnProperty("name")) {
								item.label = item.name;
							}
						});
					}
					return;
				}

				const t = nodesT[class_type];

				// 翻译 inputs/outputs/widgets
				for (const key of keys) {
					if (!t.hasOwnProperty(key)) continue;
					if (!node.hasOwnProperty(key)) continue;
					if (!node[key] || !Array.isArray(node[key])) continue;

					node[key].forEach(item => {
						if (!item || !item.name) return;

						// 检查原生翻译
						if (hasNativeTranslation(item, 'label') && !item._original_name) return;

						if (item.name in t[key]) {
							if (!item._original_name) item._original_name = item.name;
							item.label = t[key][item.name];
						} else if (key === 'inputs' || key === 'widgets') {
							// 后缀启发式
							const h = suffixHeuristic(item.name);
							if (h) {
								if (!item._original_name) item._original_name = item.name;
								item.label = h;
							}
						}
					});
				}

				// 翻译标题
				if (t.hasOwnProperty("title") && !hasNativeTranslation(node, 'title')) {
					const isCustomTitle = node._dd_custom_title ||
						(node.title && node.title !== class_type && node.title !== t["title"]);
					if (!isCustomTitle) {
						if (!node._original_title) node._original_title = node.title || class_type;
						node.title = t["title"];
						if (node.constructor) node.constructor.title = t["title"];
					}
				}

			// 劫持 addInput 处理动态输入翻译（只劫持一次）
			const addInput = node.addInput;
			if (addInput && !node._zn_hijacked_addInput) {
				node._zn_hijacked_addInput = true;
				node.addInput = function (name, type, extra_info) {
					const oldInputs = new Set();
					if (this.inputs && Array.isArray(this.inputs)) {
						for (const i of this.inputs) {
							if (i && i.name) oldInputs.add(i.name);
						}
					}
					const res = addInput.apply(this, arguments);
					if (this.inputs && Array.isArray(this.inputs)) {
						for (const i of this.inputs) {
							if (!i || !i.name || oldInputs.has(i.name)) continue;
							if (t["widgets"] && i.widget && i.widget.name in t["widgets"]) {
								i.label = t["widgets"][i.widget.name];
							} else if (t["inputs"] && i.name in t["inputs"]) {
								i.label = t["inputs"][i.name];
							}
						}
					}
					return res;
				};
			}

			// 劫持 onInputAdded（只劫持一次）
			const onInputAdded = node.onInputAdded;
			if (onInputAdded && !node._zn_hijacked_onInputAdded) {
				node._zn_hijacked_onInputAdded = true;
				node.onInputAdded = function (slot) {
					let res;
					res = onInputAdded.apply(this, arguments);
					if (slot && slot.name) {
						if (t["widgets"] && slot.name in t["widgets"]) {
							slot.localized_name = t["widgets"][slot.name];
						} else if (t["inputs"] && slot.name in t["inputs"]) {
							slot.localized_name = t["inputs"][slot.name];
						}
					}
					return res;
				};
			}
			} catch (e) {
				console.warn("[ZN-Translation] 节点翻译失败:", node?.title, e);
			}
		}

		// --------------------------------------------------------
		// 节点描述和 Tooltip 翻译（复刻 applyNodeDescTranslation）
		// --------------------------------------------------------

		static applyNodeDescTranslation(nodeType, nodeData) {
			try {
				const nodesT = this.T.Nodes;
				const t = nodesT[nodeType.comfyClass || nodeType.name];
				if (!t) return;

				// 描述翻译
				if (t["description"]) {
					nodeData.description = t["description"];
				}

				// 输入 tooltip 翻译
				const tooltipT = t["tooltips"] || {};
				for (const itype in nodeData.input) {
					for (const socketname in nodeData.input[itype]) {
						const inp = nodeData.input[itype][socketname];
						if (tooltipT[socketname]) {
							if (inp[1] === undefined) inp[1] = {};
							inp[1].tooltip = tooltipT[socketname];
							continue;
						}
						if (inp[1] === undefined || !inp[1].tooltip) continue;
						const nodeInputT = t["inputs"] || {};
						const nodeWidgetT = t["widgets"] || {};
						inp[1].tooltip = nodeInputT[inp[1].tooltip] || nodeWidgetT[inp[1].tooltip] || inp[1].tooltip;
					}
				}

				// 输出 tooltip 翻译
				const nodeOutputT = t["outputs"] || {};
				for (let i = 0; i < (nodeData.output_tooltips || []).length; i++) {
					const tooltip = nodeData.output_tooltips[i];
					const outputName = nodeData.output_name ? nodeData.output_name[i] : null;
					if (outputName && tooltipT[outputName]) {
						nodeData.output_tooltips[i] = tooltipT[outputName];
						continue;
					}
					nodeData.output_tooltips[i] = nodeOutputT[tooltip] || tooltip;
				}
			} catch (e) {
				console.warn("[ZN-Translation] 节点描述翻译失败:", nodeType?.comfyClass, e);
			}
		}

		// --------------------------------------------------------
		// 右键菜单翻译（复刻 applyContextMenuTranslation）
		// --------------------------------------------------------

		static applyContextMenuTranslation() {
			if (!window.LGraphCanvas) return;

			// 劫持 getCanvasMenuOptions
			const f = LGraphCanvas.prototype.getCanvasMenuOptions;
			if (!f) return;

			LGraphCanvas.prototype.getCanvasMenuOptions = function () {
				const res = f.apply(this, arguments);
				const menuT = TUtils.T.Menu;
				for (const item of res) {
					if (item == null || !item.hasOwnProperty("content")) continue;
					if (item.content in menuT) {
						item.content = menuT[item.content];
					}
				}
				return res;
			};

			// 劫持 LiteGraph.ContextMenu
			const f2 = window.LiteGraph ? LiteGraph.ContextMenu : null;
			if (!f2) return;

			LiteGraph.ContextMenu = function (values, options) {
				// 翻译节点标题
				if (options && options.hasOwnProperty("title") && options.title in TUtils.T.Nodes) {
					options.title = TUtils.T.Nodes[options.title]["title"] || options.title;
				}

				const t = TUtils.T.Menu;
				const tN = TUtils.T.Nodes;
				const reInput = /Convert (.*) to input/;
				const reWidget = /Convert (.*) to widget/;
				const cvt = t["Convert "] || "Convert ";
				const tinp = t[" to input"] || " to input";
				const twgt = t[" to widget"] || " to widget";

				for (const value of values) {
					if (value == null || !value.hasOwnProperty("content")) continue;

					// 子菜单节点标题
					if (value.value && value.value in tN) {
						value.content = tN[value.value]["title"] || value.content;
						continue;
					}

					// 直接匹配
					if (value.content in t) {
						value.content = t[value.content];
						continue;
					}

					// Convert X to input/widget 翻译
					const extra_info = options.extra || (options.parentMenu && options.parentMenu.options && options.parentMenu.options.extra);
					const matchInput = value.content && value.content.match(reInput);
					if (matchInput) {
						let match = matchInput[1];
						if (extra_info && extra_info.inputs) {
							extra_info.inputs.find(i => { if (i.name !== match) return false; match = i.label || i.name; return true; });
						}
						if (extra_info && extra_info.widgets) {
							extra_info.widgets.find(i => { if (i.name !== match) return false; match = i.label || i.name; return true; });
						}
						value.content = cvt + match + tinp;
						continue;
					}

					const matchWidget = value.content && value.content.match(reWidget);
					if (matchWidget) {
						let match = matchWidget[1];
						if (extra_info && extra_info.inputs) {
							extra_info.inputs.find(i => { if (i.name !== match) return false; match = i.label || i.name; return true; });
						}
						if (extra_info && extra_info.widgets) {
							extra_info.widgets.find(i => { if (i.name !== match) return false; match = i.label || i.name; return true; });
						}
						value.content = cvt + match + twgt;
						continue;
					}
				}

				const ctx = f2.call(this, values, options);
				return ctx;
			};
			LiteGraph.ContextMenu.prototype = f2.prototype;
		}

		// --------------------------------------------------------
		// 注册节点定义回调（复刻 addRegisterNodeDefCB）
		// --------------------------------------------------------

		static addRegisterNodeDefCB(app) {
			const f = app.registerNodeDef;
			if (!f) return;

			app.registerNodeDef = async function (nodeId, nodeData) {
				const res = await f.apply(this, arguments);
				TUtils.applyNodeTypeTranslationEx(nodeId);
				return res;
			};
		}

		// --------------------------------------------------------
		// 添加面板按钮（语言切换）
		// --------------------------------------------------------

		static addPanelButtons(app) {
			const id = this.LOCALE_ID;

			if (isNewUI() && window.comfyAPI && window.comfyAPI.buttonGroup && window.comfyAPI.button) {
				// 新版 UI：使用 ComfyButton / ComfyButtonGroup
				try {
					const ComfyButton = window.comfyAPI.button.ComfyButton;
					const ComfyButtonGroup = window.comfyAPI.buttonGroup.ComfyButtonGroup;
					const currentLocale = this.getLocale();
					const localeName = currentLocale === "zh-CN" ? "中文" : "EN";

					const btn = new ComfyButton({
						content: localeName,
						tooltip: "切换语言 / Switch Language",
						action: () => {
							const nextLocale = currentLocale === "zh-CN" ? "en-US" : "zh-CN";
							TUtils.setLocale(nextLocale);
						},
					});
					const group = new ComfyButtonGroup(btn.element);
					if (app.menu && app.menu.settingsGroup && app.menu.settingsGroup.element) {
						app.menu.settingsGroup.element.before(group.element);
					}
					this.ELS.localeBtn = btn.element;
				} catch (e) {
					console.warn("[ZN-Translation] 新版UI按钮创建失败:", e);
				}
			} else {
				// 旧版 UI：使用 DOM 操作
				try {
					const btn = document.createElement("button");
					btn.className = "zn-swlocale-btn";
					btn.textContent = this.getLocale() === "zh-CN" ? "中" : "EN";
					btn.title = "切换语言 / Switch Language";
					btn.onclick = () => {
						const nextLocale = TUtils.getLocale() === "zh-CN" ? "en-US" : "zh-CN";
						TUtils.setLocale(nextLocale);
					};
					btn.style.cssText = "margin-left:4px;padding:2px 8px;cursor:pointer;background:var(--bg-color);color:var(--fg-color);border:1px solid var(--border-color);border-radius:4px;";

					const menuContainer = app.ui && app.ui.menuContainer;
					if (menuContainer) {
						menuContainer.appendChild(btn);
					}
					this.ELS.localeBtn = btn;
				} catch (e) {
					console.warn("[ZN-Translation] 旧版UI按钮创建失败:", e);
				}
			}
		}

		// --------------------------------------------------------
		// 加载节点时保护自定义标题
		// --------------------------------------------------------

		static protectCustomTitle(node) {
			if (!node || !this.T.Nodes) return;
			const class_type = node.comfyClass || node.type;
			if (!class_type) return;
			const t = this.T.Nodes[class_type];
			if (!t) return;

			const translatedTitle = t["title"];
			if (node.title && node.title !== class_type &&
				(!translatedTitle || node.title !== translatedTitle)) {
				node._dd_custom_title = true;
			}
		}
	}

	// ============================================================
	// DOM 翻译引擎 - 复刻 AIGODLIKE TExe
	// ============================================================

	class TExe {
		constructor() {
			this.excludeClass = ["lite-search-item-type", "lite-search", "lite-searchbox", "litegraph-searchbox"];
		}

		/** 是否应跳过 */
		tSkip(node) {
			if (!node || !node.classList) return false;
			return this.excludeClass.some(cls => node.classList.contains(cls));
		}

		/** 翻译查找 */
		MT(txt) {
			return TUtils.MT(txt);
		}

	/** 递归替换文本 */
	replaceText(target) {
		if (!target) return;
		if (this.tSkip(target)) return;

		// 深度优先递归子节点（只遍历 childNodes，不重复处理 firstChild）
		for (const childNode of target.childNodes || []) {
			this.replaceText(childNode);
		}

		if (target.nodeType === Node.TEXT_NODE) {
				if (target.nodeValue) {
					const t = this.MT(target.nodeValue);
					if (t) target.nodeValue = t;
				}
			} else if (target.nodeType === Node.ELEMENT_NODE) {
				// title 属性
				if (target.title) {
					const t = this.MT(target.title);
					if (t) target.title = t;
				}
				// placeholder 属性
				if (target.placeholder) {
					const t = this.MT(target.placeholder);
					if (t) target.placeholder = t;
				}
				// button 的 value
				if (target.nodeName === "INPUT" && target.type === "button") {
					const t = this.MT(target.value);
					if (t) target.value = t;
				}
				// SELECT 的 OPTION
				if (target.nodeName === "SELECT") {
					for (const opt of target.querySelectorAll('option')) {
						const t = this.MT(opt.text);
						if (t) opt.text = t;
					}
				}
			// 叶子节点的 textContent（只设置一次）
			if (target.childNodes && target.childNodes.length === 1 &&
				target.firstChild && target.firstChild.nodeType === Node.TEXT_NODE) {
				const t = this.MT(target.textContent);
				if (t) target.textContent = t;
			}
			} else if (target.nodeType === Node.COMMENT_NODE) {
				// 跳过注释
			}
		}

		/** 翻译节点内所有文本 */
		translateAllText(node) {
			if (!node || !node.querySelectorAll) return;
			const allElements = node.querySelectorAll("*");
			for (const ele of allElements) {
				this.replaceText(ele);
			}
			this.replaceText(node);
		}

		/** 翻译 KJ 文档弹窗 */
		translateKjPopDesc(node) {
			if (!node || !node.querySelectorAll) return false;
			if (!node.classList || !node.classList.contains("kj-documentation-popup")) return false;
			const allElements = node.querySelectorAll("*");
			for (const ele of allElements) {
				this.replaceText(ele);
			}
			return true;
		}
	}

	const texe = new TExe();

	// ============================================================
	// 观察者工厂（复刻 AIGODLIKE observeFactory）
	// ============================================================

	function observeFactory(observeTarget, fn, subtree) {
		if (!observeTarget) return null;
		const observer = new MutationObserver(function (mutationsList, observer) {
			fn(mutationsList, observer);
		});
		observer.observe(observeTarget, {
			childList: true,
			attributes: true,
			subtree: subtree !== undefined ? subtree : false,
		});
		return observer;
	}

	// ============================================================
	// 菜单翻译 - 复刻 AIGODLIKE applyMenuTranslation
	// ============================================================

/** 存储所有观察者引用 */
let allObservers = [];
let menuTranslationApplied = false;

function applyMenuTranslation() {
	// 只执行一次，避免重复创建观察者导致内存泄漏
	if (menuTranslationApplied) return;
	menuTranslationApplied = true;

	// 初始翻译 litegraph 区域
	const litegraph = document.querySelector(".litegraph");
	if (litegraph) texe.translateAllText(litegraph);

	// 翻译 comfy-modal
	for (const node of document.querySelectorAll(".comfy-modal")) {
		const obs = observeFactory(node, (mutationsList) => {
			for (const mutation of mutationsList) {
				if (mutation.target && mutation.target.nodeType === Node.ELEMENT_NODE) {
					texe.replaceText(mutation.target);
				}
			}
		});
		if (obs) allObservers.push(obs);
	}

	// 监听 .comfyui-menu（新版菜单，不监听 subtree 避免高频触发）
	const comfyuiMenu = document.querySelector(".comfyui-menu");
	if (comfyuiMenu) {
		const obs = observeFactory(comfyuiMenu, (mutationsList) => {
			for (const mutation of mutationsList) {
				if (mutation.target && mutation.target.nodeType === Node.ELEMENT_NODE) {
					texe.replaceText(mutation.target);
				}
			}
		}, false);
		if (obs) allObservers.push(obs);
	}

	// 监听 .comfyui-popup（不监听 subtree）
	for (const node of document.querySelectorAll(".comfyui-popup")) {
		const obs = observeFactory(node, (mutationsList) => {
			for (const mutation of mutationsList) {
				if (mutation.target && mutation.target.nodeType === Node.ELEMENT_NODE) {
					texe.replaceText(mutation.target);
				}
			}
		}, false);
		if (obs) allObservers.push(obs);
	}

	// 翻译 Queue/History 按钮
	const viewQueueBtn = document.getElementById("comfy-view-queue-button");
	const viewHistoryBtn = document.getElementById("comfy-view-history-button");
	[viewQueueBtn, viewHistoryBtn].forEach(btn => {
		if (!btn) return;
		const obs = observeFactory(btn, (mutationsList, observer) => {
			observer.disconnect();
			for (const mutation of mutationsList) {
				if (mutation.type === "childList") {
					const translated = texe.MT(mutation.target.textContent);
					if (translated) mutation.target.textContent = translated;
				}
			}
			observer.observe(btn, { childList: true });
		});
		if (obs) allObservers.push(obs);
	});

	// 翻译设置面板
	const comfySettingDialog = document.querySelector("#comfy-settings-dialog");
	if (comfySettingDialog) {
		const tbody = comfySettingDialog.querySelector("tbody");
		if (tbody) {
			const obs = observeFactory(tbody, (mutationsList) => {
				for (const mutation of mutationsList) {
					if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
						translateSettingDialog(comfySettingDialog);
					}
				}
			});
			if (obs) allObservers.push(obs);
		}
	}

	// 监听 body 下的动态内容（仅处理弹窗/模态框等特定元素）
	const bodyObserver = observeFactory(document.body, (mutationsList) => {
		for (const mutation of mutationsList) {
			for (const node of mutation.addedNodes) {
				if (node.nodeType !== Node.ELEMENT_NODE) continue;
				if (!node.classList) continue;

				// 新版设置面板 (.p-dialog-mask)
				if (node.classList.contains("p-dialog-mask")) {
					texe.translateAllText(node);
					const dialog = node.querySelector(".p-dialog");
					if (dialog) {
						const obs = observeFactory(dialog, (mutationsList) => {
							for (const m of mutationsList) {
								if (m.target && m.target.nodeType === Node.ELEMENT_NODE) {
									texe.replaceText(m.target);
								}
							}
						}, false);
						if (obs) allObservers.push(obs);
					}
					continue;
				}

				// comfy-modal 弹窗
				if (node.classList.contains("comfy-modal")) {
					texe.translateAllText(node);
					const obs = observeFactory(node, (mutationsList) => {
						for (const m of mutationsList) {
							if (m.target && m.target.nodeType === Node.ELEMENT_NODE) {
								texe.replaceText(m.target);
							}
						}
					});
					if (obs) allObservers.push(obs);
					continue;
				}

				// .comfyui-popup 弹窗
				if (node.classList.contains("comfyui-popup")) {
					texe.translateAllText(node);
					continue;
				}
			}
		}
	}, false);
	if (bodyObserver) allObservers.push(bodyObserver);

	// 搜索框翻译（单独管理，避免内存泄漏）
	let searchDebounceTimer = null;
	let searchHelperObs = null;
	const litegraphEl = document.querySelector(".litegraph");
	if (litegraphEl) {
		const searchObs = observeFactory(litegraphEl, (mutationsList) => {
			for (const mutation of mutationsList) {
				// 搜索框关闭时彻底清理 helper 观察者
				if (mutation.removedNodes.length > 0) {
					if (searchHelperObs) {
						searchHelperObs.disconnect();
						searchHelperObs = null;
					}
					continue;
				}
				for (const sb of mutation.addedNodes) {
					if (!sb || !sb.querySelector) continue;
					const helper = sb.querySelector(".helper");
					if (!helper) continue;
					// 清理旧的 helper 观察者
					if (searchHelperObs) {
						searchHelperObs.disconnect();
					}
					searchHelperObs = observeFactory(helper, (mutationsList) => {
						if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
						searchDebounceTimer = setTimeout(() => {
							for (const m of mutationsList) {
								for (const item of m.addedNodes) {
									if (item.nodeType !== Node.ELEMENT_NODE) continue;
									const key = item.textContent || item.innerText;
									if (key && TUtils.T.Nodes[key]) {
										item.textContent = TUtils.T.Nodes[key]["title"];
									}
								}
							}
						}, 50);
					});
				}
			}
		});
		if (searchObs) allObservers.push(searchObs);
	}

		// 翻译设置面板的辅助函数
		function translateSettingDialog(dialog) {
			const allElements = dialog.querySelectorAll("*");
			for (const ele of allElements) {
				let targetLangText = texe.MT(ele.innerText);
				const titleText = texe.MT(ele.title);
				if (titleText) ele.title = titleText;
				if (!targetLangText) {
					if (ele.nodeName === "INPUT" && ele.type === "button") {
						targetLangText = texe.MT(ele.value);
						if (targetLangText) ele.value = targetLangText;
					}
					continue;
				}
				texe.replaceText(ele);
			}
		}
	}

	// ============================================================
	// 注册 ComfyUI Extension
	// ============================================================

	const ext = {
		name: "ZN.Translation",

		async init() {
			// 增强滑块显示
			TUtils.enhandeDrawNodeWidgets();

			// 同步翻译数据
			TUtils.syncTranslation(() => {
				// 数据加载完成后应用菜单翻译
				applyMenuTranslation();
			});
		},

		async setup() {
			// 应用节点类型翻译
			TUtils.applyNodeTypeTranslation();

			// 应用右键菜单翻译
			TUtils.applyContextMenuTranslation();

			// 注册节点定义回调
			TUtils.addRegisterNodeDefCB(app);

			// 添加面板按钮
			TUtils.addPanelButtons(app);

		// 初始翻译（等待 DOM 加载，applyMenuTranslation 内部有只执行一次的标记）
		setTimeout(() => applyMenuTranslation(), 300);
		},

		beforeRegisterNodeDef(nodeType, nodeData) {
			TUtils.applyNodeDescTranslation(nodeType, nodeData);
		},

		beforeRegisterVueAppNodeDefs(nodeDefs) {
			// Vue 节点系统专用
			nodeDefs.forEach(nodeDef => {
				TUtils.applyVueNodeDisplayNameTranslation(nodeDef);
				TUtils.applyVueNodeTranslation(nodeDef);
			});
		},

		nodeCreated(node) {
			TUtils.protectCustomTitle(node);
			TUtils.applyNodeTranslation(node);
		},

		loadedGraphNode(node) {
			TUtils.protectCustomTitle(node);
			TUtils.applyNodeTranslation(node);
		},
	};

	app.registerExtension(ext);
})();
