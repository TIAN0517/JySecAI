// START code to replace ? (if present) with a #
const query = window.location.search.slice(1); // removes '?'
const hash = window.location.hash; // gets '#foo=bar' if exists
const searchPagePath = window.location.pathname;
// replacing + in the url with %20
const output = query.replace(/\+/g, "%20");

// Only redirect if query string exists AND hash is empty
if (query && !hash && (searchPagePath == '/search.html' || searchPagePath == '/content/corporate/search.html')) {
    const target = `${searchPagePath}#${output}`;
    window.location.replace(target);
}
// END code to replace ? (if present) with a #

// START add default hash to the search results page
const locationHash = window.location.hash;
if (locationHash == '' && (searchPagePath == '/search.html' || searchPagePath == '/content/corporate/search.html')) {
	window.location.hash = 'f-commoncontenttype=Everything';
}
// END add default hash to the search results page
var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => {
  __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
  return value;
};

// dist/components/p-CesU89ss.js
var NAMESPACE = "unisyd-atomic-app";
var BUILD = (
  /* unisyd-atomic-app */
  { hydratedSelectorName: "hydrated", lazyLoad: false, updatable: true, watchCallback: false }
);
var __defProp2 = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp2(target, name, { get: all[name], enumerable: true });
};
var SVG_NS = "http://www.w3.org/2000/svg";
var HTML_NS = "http://www.w3.org/1999/xhtml";
var getHostRef = (ref) => {
  if (ref.__stencil__getHostRef) {
    return ref.__stencil__getHostRef();
  }
  return void 0;
};
var registerHost = (hostElement, cmpMeta) => {
  const hostRef = {
    $flags$: 0,
    $hostElement$: hostElement,
    $cmpMeta$: cmpMeta,
    $instanceValues$: /* @__PURE__ */ new Map()
  };
  {
    hostRef.$onReadyPromise$ = new Promise((r) => hostRef.$onReadyResolve$ = r);
    hostElement["s-p"] = [];
    hostElement["s-rc"] = [];
  }
  const ref = hostRef;
  hostElement.__stencil__getHostRef = () => ref;
  return ref;
};
var isMemberInElement = (elm, memberName) => memberName in elm;
var consoleError = (e7, el3) => (0, console.error)(e7, el3);
var styles = /* @__PURE__ */ new Map();
var SLOT_FB_CSS = "slot-fb{display:contents}slot-fb[hidden]{display:none}";
var win = typeof window !== "undefined" ? window : {};
var H = win.HTMLElement || class {
};
var plt = {
  $flags$: 0,
  $resourcesUrl$: "",
  jmp: (h22) => h22(),
  raf: (h22) => requestAnimationFrame(h22),
  ael: (el3, eventName, listener, opts) => el3.addEventListener(eventName, listener, opts),
  rel: (el3, eventName, listener, opts) => el3.removeEventListener(eventName, listener, opts),
  ce: (eventName, opts) => new CustomEvent(eventName, opts)
};
var promiseResolve = (v) => Promise.resolve(v);
var supportsConstructableStylesheets = /* @__PURE__ */ (() => {
  try {
    new CSSStyleSheet();
    return typeof new CSSStyleSheet().replaceSync === "function";
  } catch (e7) {
  }
  return false;
})();
var supportsMutableAdoptedStyleSheets = supportsConstructableStylesheets ? /* @__PURE__ */ (() => !!win.document && Object.getOwnPropertyDescriptor(win.document.adoptedStyleSheets, "length").writable)() : false;
var queuePending = false;
var queueDomReads = [];
var queueDomWrites = [];
var queueTask = (queue, write) => (cb) => {
  queue.push(cb);
  if (!queuePending) {
    queuePending = true;
    if (write && plt.$flags$ & 4) {
      nextTick(flush);
    } else {
      plt.raf(flush);
    }
  }
};
var consume = (queue) => {
  for (let i2 = 0; i2 < queue.length; i2++) {
    try {
      queue[i2](performance.now());
    } catch (e7) {
      consoleError(e7);
    }
  }
  queue.length = 0;
};
var flush = () => {
  consume(queueDomReads);
  {
    consume(queueDomWrites);
    if (queuePending = queueDomReads.length > 0) {
      plt.raf(flush);
    }
  }
};
var nextTick = (cb) => promiseResolve().then(cb);
var writeTask = /* @__PURE__ */ queueTask(queueDomWrites, true);
var getAssetPath = (path) => {
  const assetUrl = new URL(path, plt.$resourcesUrl$);
  return assetUrl.origin !== win.location.origin ? assetUrl.href : assetUrl.pathname;
};
var setAssetPath = (path) => plt.$resourcesUrl$ = path;
var isComplexType = (o) => {
  o = typeof o;
  return o === "object" || o === "function";
};
function queryNonceMetaTagContent(doc) {
  var _a3, _b, _c3;
  return (_c3 = (_b = (_a3 = doc.head) == null ? void 0 : _a3.querySelector('meta[name="csp-nonce"]')) == null ? void 0 : _b.getAttribute("content")) != null ? _c3 : void 0;
}
var escapeRegExpSpecialCharacters = (text) => {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
};
var result_exports = {};
__export(result_exports, {
  err: () => err,
  map: () => map,
  ok: () => ok,
  unwrap: () => unwrap,
  unwrapErr: () => unwrapErr
});
var ok = (value) => ({
  isOk: true,
  isErr: false,
  value
});
var err = (value) => ({
  isOk: false,
  isErr: true,
  value
});
function map(result, fn) {
  if (result.isOk) {
    const val = fn(result.value);
    if (val instanceof Promise) {
      return val.then((newVal) => ok(newVal));
    } else {
      return ok(val);
    }
  }
  if (result.isErr) {
    const value = result.value;
    return err(value);
  }
  throw "should never get here";
}
var unwrap = (result) => {
  if (result.isOk) {
    return result.value;
  } else {
    throw result.value;
  }
};
var unwrapErr = (result) => {
  if (result.isErr) {
    return result.value;
  } else {
    throw result.value;
  }
};
function createStyleSheetIfNeededAndSupported(styles2) {
  return void 0;
}
var globalStyleSheet;
function createShadowRoot(cmpMeta) {
  var _a3;
  const shadowRoot = this.attachShadow({ mode: "open" });
  if (globalStyleSheet === void 0)
    globalStyleSheet = (_a3 = createStyleSheetIfNeededAndSupported()) != null ? _a3 : null;
  if (globalStyleSheet) {
    if (supportsMutableAdoptedStyleSheets) {
      shadowRoot.adoptedStyleSheets.push(globalStyleSheet);
    } else {
      shadowRoot.adoptedStyleSheets = [...shadowRoot.adoptedStyleSheets, globalStyleSheet];
    }
  }
}
var createTime = (fnName, tagName = "") => {
  {
    return () => {
      return;
    };
  }
};
var rootAppliedStyles = /* @__PURE__ */ new WeakMap();
var registerStyle = (scopeId2, cssText, allowCS) => {
  let style = styles.get(scopeId2);
  if (supportsConstructableStylesheets && allowCS) {
    style = style || new CSSStyleSheet();
    if (typeof style === "string") {
      style = cssText;
    } else {
      style.replaceSync(cssText);
    }
  } else {
    style = cssText;
  }
  styles.set(scopeId2, style);
};
var addStyle = (styleContainerNode, cmpMeta, mode) => {
  var _a3;
  const scopeId2 = getScopeId(cmpMeta);
  const style = styles.get(scopeId2);
  if (!win.document) {
    return scopeId2;
  }
  styleContainerNode = styleContainerNode.nodeType === 11 ? styleContainerNode : win.document;
  if (style) {
    if (typeof style === "string") {
      styleContainerNode = styleContainerNode.head || styleContainerNode;
      let appliedStyles = rootAppliedStyles.get(styleContainerNode);
      let styleElm;
      if (!appliedStyles) {
        rootAppliedStyles.set(styleContainerNode, appliedStyles = /* @__PURE__ */ new Set());
      }
      if (!appliedStyles.has(scopeId2)) {
        {
          styleElm = win.document.createElement("style");
          styleElm.innerHTML = style;
          const nonce = (_a3 = plt.$nonce$) != null ? _a3 : queryNonceMetaTagContent(win.document);
          if (nonce != null) {
            styleElm.setAttribute("nonce", nonce);
          }
          if (!(cmpMeta.$flags$ & 1)) {
            if (styleContainerNode.nodeName === "HEAD") {
              const preconnectLinks = styleContainerNode.querySelectorAll("link[rel=preconnect]");
              const referenceNode2 = preconnectLinks.length > 0 ? preconnectLinks[preconnectLinks.length - 1].nextSibling : styleContainerNode.querySelector("style");
              styleContainerNode.insertBefore(
                styleElm,
                (referenceNode2 == null ? void 0 : referenceNode2.parentNode) === styleContainerNode ? referenceNode2 : null
              );
            } else if ("host" in styleContainerNode) {
              if (supportsConstructableStylesheets) {
                const stylesheet = new CSSStyleSheet();
                stylesheet.replaceSync(style);
                if (supportsMutableAdoptedStyleSheets) {
                  styleContainerNode.adoptedStyleSheets.unshift(stylesheet);
                } else {
                  styleContainerNode.adoptedStyleSheets = [stylesheet, ...styleContainerNode.adoptedStyleSheets];
                }
              } else {
                const existingStyleContainer = styleContainerNode.querySelector("style");
                if (existingStyleContainer) {
                  existingStyleContainer.innerHTML = style + existingStyleContainer.innerHTML;
                } else {
                  styleContainerNode.prepend(styleElm);
                }
              }
            } else {
              styleContainerNode.append(styleElm);
            }
          }
          if (cmpMeta.$flags$ & 1) {
            styleContainerNode.insertBefore(styleElm, null);
          }
        }
        if (cmpMeta.$flags$ & 4) {
          styleElm.innerHTML += SLOT_FB_CSS;
        }
        if (appliedStyles) {
          appliedStyles.add(scopeId2);
        }
      }
    } else if (!styleContainerNode.adoptedStyleSheets.includes(style)) {
      if (supportsMutableAdoptedStyleSheets) {
        styleContainerNode.adoptedStyleSheets.push(style);
      } else {
        styleContainerNode.adoptedStyleSheets = [...styleContainerNode.adoptedStyleSheets, style];
      }
    }
  }
  return scopeId2;
};
var attachStyles = (hostRef) => {
  const cmpMeta = hostRef.$cmpMeta$;
  const elm = hostRef.$hostElement$;
  const flags = cmpMeta.$flags$;
  const endAttachStyles = createTime("attachStyles", cmpMeta.$tagName$);
  const scopeId2 = addStyle(
    elm.shadowRoot ? elm.shadowRoot : elm.getRootNode(),
    cmpMeta
  );
  if (flags & 10) {
    elm["s-sc"] = scopeId2;
    elm.classList.add(scopeId2 + "-h");
  }
  endAttachStyles();
};
var getScopeId = (cmp, mode) => "sc-" + cmp.$tagName$;
var h = (nodeName, vnodeData, ...children) => {
  let child = null;
  let key = null;
  let simple = false;
  let lastSimple = false;
  const vNodeChildren = [];
  const walk = (c) => {
    for (let i2 = 0; i2 < c.length; i2++) {
      child = c[i2];
      if (Array.isArray(child)) {
        walk(child);
      } else if (child != null && typeof child !== "boolean") {
        if (simple = typeof nodeName !== "function" && !isComplexType(child)) {
          child = String(child);
        }
        if (simple && lastSimple) {
          vNodeChildren[vNodeChildren.length - 1].$text$ += child;
        } else {
          vNodeChildren.push(simple ? newVNode(null, child) : child);
        }
        lastSimple = simple;
      }
    }
  };
  walk(children);
  if (vnodeData) {
    if (vnodeData.key) {
      key = vnodeData.key;
    }
    {
      const classData = vnodeData.className || vnodeData.class;
      if (classData) {
        vnodeData.class = typeof classData !== "object" ? classData : Object.keys(classData).filter((k) => classData[k]).join(" ");
      }
    }
  }
  const vnode = newVNode(nodeName, null);
  vnode.$attrs$ = vnodeData;
  if (vNodeChildren.length > 0) {
    vnode.$children$ = vNodeChildren;
  }
  {
    vnode.$key$ = key;
  }
  return vnode;
};
var newVNode = (tag, text) => {
  const vnode = {
    $flags$: 0,
    $tag$: tag,
    $text$: text,
    $elm$: null,
    $children$: null
  };
  {
    vnode.$attrs$ = null;
  }
  {
    vnode.$key$ = null;
  }
  return vnode;
};
var Host = {};
var isHost = (node) => node && node.$tag$ === Host;
var createSupportsRuleRe = (selector) => {
  const safeSelector2 = escapeRegExpSpecialCharacters(selector);
  return new RegExp(
    // First capture group: match any context before the selector that's not inside @supports selector()
    // Using negative lookahead to avoid matching inside @supports selector(...) condition
    `(^|[^@]|@(?!supports\\s+selector\\s*\\([^{]*?${safeSelector2}))(${safeSelector2}\\b)`,
    "g"
  );
};
createSupportsRuleRe("::slotted");
createSupportsRuleRe(":host");
createSupportsRuleRe(":host-context");
var parsePropertyValue = (propValue, propType, isFormAssociated) => {
  if (typeof propValue === "string" && (propType & 16 || propType & 8) && (propValue.startsWith("{") && propValue.endsWith("}") || propValue.startsWith("[") && propValue.endsWith("]"))) {
    try {
      return JSON.parse(propValue);
    } catch (e7) {
    }
  }
  if (propValue != null && !isComplexType(propValue)) {
    if (propType & 2) {
      return typeof propValue === "string" ? parseFloat(propValue) : typeof propValue === "number" ? propValue : NaN;
    }
    if (propType & 1) {
      return String(propValue);
    }
    return propValue;
  }
  return propValue;
};
var getElement = (ref) => {
  return ref;
};
var createEvent = (ref, name, flags) => {
  const elm = getElement(ref);
  return {
    emit: (detail) => {
      return emitEvent(elm, name, {
        bubbles: true,
        composed: true,
        cancelable: true,
        detail
      });
    }
  };
};
var emitEvent = (elm, name, opts) => {
  const ev2 = plt.ce(name, opts);
  elm.dispatchEvent(ev2);
  return ev2;
};
var setAccessor = (elm, memberName, oldValue, newValue, isSvg, flags, initialRender) => {
  if (oldValue === newValue) {
    return;
  }
  let isProp = isMemberInElement(elm, memberName);
  let ln3 = memberName.toLowerCase();
  if (memberName === "class") {
    const classList = elm.classList;
    const oldClasses = parseClassList(oldValue);
    let newClasses = parseClassList(newValue);
    {
      classList.remove(...oldClasses.filter((c) => c && !newClasses.includes(c)));
      classList.add(...newClasses.filter((c) => c && !oldClasses.includes(c)));
    }
  } else if (memberName === "key")
    ;
  else if (!elm.__lookupSetter__(memberName) && memberName[0] === "o" && memberName[1] === "n") {
    if (memberName[2] === "-") {
      memberName = memberName.slice(3);
    } else if (isMemberInElement(win, ln3)) {
      memberName = ln3.slice(2);
    } else {
      memberName = ln3[2] + memberName.slice(3);
    }
    if (oldValue || newValue) {
      const capture = memberName.endsWith(CAPTURE_EVENT_SUFFIX);
      memberName = memberName.replace(CAPTURE_EVENT_REGEX, "");
      if (oldValue) {
        plt.rel(elm, memberName, oldValue, capture);
      }
      if (newValue) {
        plt.ael(elm, memberName, newValue, capture);
      }
    }
  } else {
    const isComplex = isComplexType(newValue);
    if ((isProp || isComplex && newValue !== null) && !isSvg) {
      try {
        if (!elm.tagName.includes("-")) {
          const n = newValue == null ? "" : newValue;
          if (memberName === "list") {
            isProp = false;
          } else if (oldValue == null || elm[memberName] != n) {
            if (typeof elm.__lookupSetter__(memberName) === "function") {
              elm[memberName] = n;
            } else {
              elm.setAttribute(memberName, n);
            }
          }
        } else if (elm[memberName] !== newValue) {
          elm[memberName] = newValue;
        }
      } catch (e7) {
      }
    }
    if (newValue == null || newValue === false) {
      if (newValue !== false || elm.getAttribute(memberName) === "") {
        {
          elm.removeAttribute(memberName);
        }
      }
    } else if ((!isProp || flags & 4 || isSvg) && !isComplex && elm.nodeType === 1) {
      newValue = newValue === true ? "" : newValue;
      {
        elm.setAttribute(memberName, newValue);
      }
    }
  }
};
var parseClassListRegex = /\s/;
var parseClassList = (value) => {
  if (typeof value === "object" && value && "baseVal" in value) {
    value = value.baseVal;
  }
  if (!value || typeof value !== "string") {
    return [];
  }
  return value.split(parseClassListRegex);
};
var CAPTURE_EVENT_SUFFIX = "Capture";
var CAPTURE_EVENT_REGEX = new RegExp(CAPTURE_EVENT_SUFFIX + "$");
var updateElement = (oldVnode, newVnode, isSvgMode2, isInitialRender) => {
  const elm = newVnode.$elm$.nodeType === 11 && newVnode.$elm$.host ? newVnode.$elm$.host : newVnode.$elm$;
  const oldVnodeAttrs = oldVnode && oldVnode.$attrs$ || {};
  const newVnodeAttrs = newVnode.$attrs$ || {};
  {
    for (const memberName of sortedAttrNames(Object.keys(oldVnodeAttrs))) {
      if (!(memberName in newVnodeAttrs)) {
        setAccessor(
          elm,
          memberName,
          oldVnodeAttrs[memberName],
          void 0,
          isSvgMode2,
          newVnode.$flags$
        );
      }
    }
  }
  for (const memberName of sortedAttrNames(Object.keys(newVnodeAttrs))) {
    setAccessor(
      elm,
      memberName,
      oldVnodeAttrs[memberName],
      newVnodeAttrs[memberName],
      isSvgMode2,
      newVnode.$flags$
    );
  }
};
function sortedAttrNames(attrNames) {
  return attrNames.includes("ref") ? (
    // we need to sort these to ensure that `'ref'` is the last attr
    [...attrNames.filter((attr) => attr !== "ref"), "ref"]
  ) : (
    // no need to sort, return the original array
    attrNames
  );
}
var hostTagName;
var isSvgMode = false;
var createElm = (oldParentVNode, newParentVNode, childIndex) => {
  const newVNode2 = newParentVNode.$children$[childIndex];
  let i2 = 0;
  let elm;
  let childNode;
  if (newVNode2.$text$ !== null) {
    elm = newVNode2.$elm$ = win.document.createTextNode(newVNode2.$text$);
  } else {
    if (!isSvgMode) {
      isSvgMode = newVNode2.$tag$ === "svg";
    }
    if (!win.document) {
      throw new Error(
        "You are trying to render a Stencil component in an environment that doesn't support the DOM. Make sure to populate the [`window`](https://developer.mozilla.org/en-US/docs/Web/API/Window/window) object before rendering a component."
      );
    }
    elm = newVNode2.$elm$ = win.document.createElementNS(
      isSvgMode ? SVG_NS : HTML_NS,
      newVNode2.$tag$
    );
    if (isSvgMode && newVNode2.$tag$ === "foreignObject") {
      isSvgMode = false;
    }
    {
      updateElement(null, newVNode2, isSvgMode);
    }
    if (newVNode2.$children$) {
      for (i2 = 0; i2 < newVNode2.$children$.length; ++i2) {
        childNode = createElm(oldParentVNode, newVNode2, i2);
        if (childNode) {
          elm.appendChild(childNode);
        }
      }
    }
    {
      if (newVNode2.$tag$ === "svg") {
        isSvgMode = false;
      } else if (elm.tagName === "foreignObject") {
        isSvgMode = true;
      }
    }
  }
  elm["s-hn"] = hostTagName;
  return elm;
};
var addVnodes = (parentElm, before, parentVNode, vnodes, startIdx, endIdx) => {
  let containerElm = parentElm;
  let childNode;
  if (containerElm.shadowRoot && containerElm.tagName === hostTagName) {
    containerElm = containerElm.shadowRoot;
  }
  for (; startIdx <= endIdx; ++startIdx) {
    if (vnodes[startIdx]) {
      childNode = createElm(null, parentVNode, startIdx);
      if (childNode) {
        vnodes[startIdx].$elm$ = childNode;
        insertBefore(containerElm, childNode, before);
      }
    }
  }
};
var removeVnodes = (vnodes, startIdx, endIdx) => {
  for (let index = startIdx; index <= endIdx; ++index) {
    const vnode = vnodes[index];
    if (vnode) {
      const elm = vnode.$elm$;
      if (elm) {
        elm.remove();
      }
    }
  }
};
var updateChildren = (parentElm, oldCh, newVNode2, newCh, isInitialRender = false) => {
  let oldStartIdx = 0;
  let newStartIdx = 0;
  let idxInOld = 0;
  let i2 = 0;
  let oldEndIdx = oldCh.length - 1;
  let oldStartVnode = oldCh[0];
  let oldEndVnode = oldCh[oldEndIdx];
  let newEndIdx = newCh.length - 1;
  let newStartVnode = newCh[0];
  let newEndVnode = newCh[newEndIdx];
  let node;
  let elmToMove;
  while (oldStartIdx <= oldEndIdx && newStartIdx <= newEndIdx) {
    if (oldStartVnode == null) {
      oldStartVnode = oldCh[++oldStartIdx];
    } else if (oldEndVnode == null) {
      oldEndVnode = oldCh[--oldEndIdx];
    } else if (newStartVnode == null) {
      newStartVnode = newCh[++newStartIdx];
    } else if (newEndVnode == null) {
      newEndVnode = newCh[--newEndIdx];
    } else if (isSameVnode(oldStartVnode, newStartVnode, isInitialRender)) {
      patch(oldStartVnode, newStartVnode, isInitialRender);
      oldStartVnode = oldCh[++oldStartIdx];
      newStartVnode = newCh[++newStartIdx];
    } else if (isSameVnode(oldEndVnode, newEndVnode, isInitialRender)) {
      patch(oldEndVnode, newEndVnode, isInitialRender);
      oldEndVnode = oldCh[--oldEndIdx];
      newEndVnode = newCh[--newEndIdx];
    } else if (isSameVnode(oldStartVnode, newEndVnode, isInitialRender)) {
      patch(oldStartVnode, newEndVnode, isInitialRender);
      insertBefore(parentElm, oldStartVnode.$elm$, oldEndVnode.$elm$.nextSibling);
      oldStartVnode = oldCh[++oldStartIdx];
      newEndVnode = newCh[--newEndIdx];
    } else if (isSameVnode(oldEndVnode, newStartVnode, isInitialRender)) {
      patch(oldEndVnode, newStartVnode, isInitialRender);
      insertBefore(parentElm, oldEndVnode.$elm$, oldStartVnode.$elm$);
      oldEndVnode = oldCh[--oldEndIdx];
      newStartVnode = newCh[++newStartIdx];
    } else {
      idxInOld = -1;
      {
        for (i2 = oldStartIdx; i2 <= oldEndIdx; ++i2) {
          if (oldCh[i2] && oldCh[i2].$key$ !== null && oldCh[i2].$key$ === newStartVnode.$key$) {
            idxInOld = i2;
            break;
          }
        }
      }
      if (idxInOld >= 0) {
        elmToMove = oldCh[idxInOld];
        if (elmToMove.$tag$ !== newStartVnode.$tag$) {
          node = createElm(oldCh && oldCh[newStartIdx], newVNode2, idxInOld);
        } else {
          patch(elmToMove, newStartVnode, isInitialRender);
          oldCh[idxInOld] = void 0;
          node = elmToMove.$elm$;
        }
        newStartVnode = newCh[++newStartIdx];
      } else {
        node = createElm(oldCh && oldCh[newStartIdx], newVNode2, newStartIdx);
        newStartVnode = newCh[++newStartIdx];
      }
      if (node) {
        {
          insertBefore(oldStartVnode.$elm$.parentNode, node, oldStartVnode.$elm$);
        }
      }
    }
  }
  if (oldStartIdx > oldEndIdx) {
    addVnodes(
      parentElm,
      newCh[newEndIdx + 1] == null ? null : newCh[newEndIdx + 1].$elm$,
      newVNode2,
      newCh,
      newStartIdx,
      newEndIdx
    );
  } else if (newStartIdx > newEndIdx) {
    removeVnodes(oldCh, oldStartIdx, oldEndIdx);
  }
};
var isSameVnode = (leftVNode, rightVNode, isInitialRender = false) => {
  if (leftVNode.$tag$ === rightVNode.$tag$) {
    if (!isInitialRender) {
      return leftVNode.$key$ === rightVNode.$key$;
    }
    if (isInitialRender && !leftVNode.$key$ && rightVNode.$key$) {
      leftVNode.$key$ = rightVNode.$key$;
    }
    return true;
  }
  return false;
};
var patch = (oldVNode, newVNode2, isInitialRender = false) => {
  const elm = newVNode2.$elm$ = oldVNode.$elm$;
  const oldChildren = oldVNode.$children$;
  const newChildren = newVNode2.$children$;
  const tag = newVNode2.$tag$;
  const text = newVNode2.$text$;
  if (text === null) {
    {
      isSvgMode = tag === "svg" ? true : tag === "foreignObject" ? false : isSvgMode;
    }
    {
      updateElement(oldVNode, newVNode2, isSvgMode);
    }
    if (oldChildren !== null && newChildren !== null) {
      updateChildren(elm, oldChildren, newVNode2, newChildren, isInitialRender);
    } else if (newChildren !== null) {
      if (oldVNode.$text$ !== null) {
        elm.textContent = "";
      }
      addVnodes(elm, null, newVNode2, newChildren, 0, newChildren.length - 1);
    } else if (
      // don't do this on initial render as it can cause non-hydrated content to be removed
      !isInitialRender && BUILD.updatable && oldChildren !== null
    ) {
      removeVnodes(oldChildren, 0, oldChildren.length - 1);
    } else
      ;
    if (isSvgMode && tag === "svg") {
      isSvgMode = false;
    }
  } else if (oldVNode.$text$ !== text) {
    elm.data = text;
  }
};
var insertBefore = (parent, newNode, reference) => {
  {
    return parent == null ? void 0 : parent.insertBefore(newNode, reference);
  }
};
var renderVdom = (hostRef, renderFnResults, isInitialLoad = false) => {
  const hostElm = hostRef.$hostElement$;
  const oldVNode = hostRef.$vnode$ || newVNode(null, null);
  const isHostElement = isHost(renderFnResults);
  const rootVnode = isHostElement ? renderFnResults : h(null, null, renderFnResults);
  hostTagName = hostElm.tagName;
  if (isInitialLoad && rootVnode.$attrs$) {
    for (const key of Object.keys(rootVnode.$attrs$)) {
      if (hostElm.hasAttribute(key) && !["key", "ref", "style", "class"].includes(key)) {
        rootVnode.$attrs$[key] = hostElm[key];
      }
    }
  }
  rootVnode.$tag$ = null;
  rootVnode.$flags$ |= 4;
  hostRef.$vnode$ = rootVnode;
  rootVnode.$elm$ = oldVNode.$elm$ = hostElm.shadowRoot || hostElm;
  patch(oldVNode, rootVnode, isInitialLoad);
};
var attachToAncestor = (hostRef, ancestorComponent) => {
  if (ancestorComponent && !hostRef.$onRenderResolve$ && ancestorComponent["s-p"]) {
    const index = ancestorComponent["s-p"].push(
      new Promise(
        (r) => hostRef.$onRenderResolve$ = () => {
          ancestorComponent["s-p"].splice(index - 1, 1);
          r();
        }
      )
    );
  }
};
var scheduleUpdate = (hostRef, isInitialLoad) => {
  {
    hostRef.$flags$ |= 16;
  }
  if (hostRef.$flags$ & 4) {
    hostRef.$flags$ |= 512;
    return;
  }
  attachToAncestor(hostRef, hostRef.$ancestorComponent$);
  const dispatch = () => dispatchHooks(hostRef, isInitialLoad);
  if (isInitialLoad) {
    queueMicrotask(() => {
      dispatch();
    });
    return;
  }
  return writeTask(dispatch);
};
var dispatchHooks = (hostRef, isInitialLoad) => {
  const elm = hostRef.$hostElement$;
  const endSchedule = createTime("scheduleUpdate", hostRef.$cmpMeta$.$tagName$);
  const instance = elm;
  if (!instance) {
    throw new Error(
      `Can't render component <${elm.tagName.toLowerCase()} /> with invalid Stencil runtime! Make sure this imported component is compiled with a \`externalRuntime: true\` flag. For more information, please refer to https://stenciljs.com/docs/custom-elements#externalruntime`
    );
  }
  let maybePromise;
  if (isInitialLoad) {
    maybePromise = safeCall(instance, "componentWillLoad", void 0, elm);
  } else {
    maybePromise = safeCall(instance, "componentWillUpdate", void 0, elm);
  }
  maybePromise = enqueue(maybePromise, () => safeCall(instance, "componentWillRender", void 0, elm));
  endSchedule();
  return enqueue(maybePromise, () => updateComponent(hostRef, instance, isInitialLoad));
};
var enqueue = (maybePromise, fn) => isPromisey(maybePromise) ? maybePromise.then(fn).catch((err22) => {
  console.error(err22);
  fn();
}) : fn();
var isPromisey = (maybePromise) => maybePromise instanceof Promise || maybePromise && maybePromise.then && typeof maybePromise.then === "function";
var updateComponent = async (hostRef, instance, isInitialLoad) => {
  var _a3;
  const elm = hostRef.$hostElement$;
  const endUpdate = createTime("update", hostRef.$cmpMeta$.$tagName$);
  const rc = elm["s-rc"];
  if (isInitialLoad) {
    attachStyles(hostRef);
  }
  const endRender = createTime("render", hostRef.$cmpMeta$.$tagName$);
  {
    callRender(hostRef, instance, elm, isInitialLoad);
  }
  if (rc) {
    rc.map((cb) => cb());
    elm["s-rc"] = void 0;
  }
  endRender();
  endUpdate();
  {
    const childrenPromises = (_a3 = elm["s-p"]) != null ? _a3 : [];
    const postUpdate = () => postUpdateComponent(hostRef);
    if (childrenPromises.length === 0) {
      postUpdate();
    } else {
      Promise.all(childrenPromises).then(postUpdate);
      hostRef.$flags$ |= 4;
      childrenPromises.length = 0;
    }
  }
};
var callRender = (hostRef, instance, elm, isInitialLoad) => {
  try {
    instance = instance.render();
    {
      hostRef.$flags$ &= -17;
    }
    {
      hostRef.$flags$ |= 2;
    }
    {
      {
        {
          renderVdom(hostRef, instance, isInitialLoad);
        }
      }
    }
  } catch (e7) {
    consoleError(e7, hostRef.$hostElement$);
  }
  return null;
};
var postUpdateComponent = (hostRef) => {
  const tagName = hostRef.$cmpMeta$.$tagName$;
  const elm = hostRef.$hostElement$;
  const endPostUpdate = createTime("postUpdate", tagName);
  const instance = elm;
  const ancestorComponent = hostRef.$ancestorComponent$;
  safeCall(instance, "componentDidRender", void 0, elm);
  if (!(hostRef.$flags$ & 64)) {
    hostRef.$flags$ |= 64;
    {
      addHydratedFlag(elm);
    }
    safeCall(instance, "componentDidLoad", void 0, elm);
    endPostUpdate();
    {
      hostRef.$onReadyResolve$(elm);
      if (!ancestorComponent) {
        appDidLoad();
      }
    }
  } else {
    safeCall(instance, "componentDidUpdate", void 0, elm);
    endPostUpdate();
  }
  {
    if (hostRef.$onRenderResolve$) {
      hostRef.$onRenderResolve$();
      hostRef.$onRenderResolve$ = void 0;
    }
    if (hostRef.$flags$ & 512) {
      nextTick(() => scheduleUpdate(hostRef, false));
    }
    hostRef.$flags$ &= -517;
  }
};
var appDidLoad = (who) => {
  nextTick(() => emitEvent(win, "appload", { detail: { namespace: NAMESPACE } }));
};
var safeCall = (instance, method, arg, elm) => {
  if (instance && instance[method]) {
    try {
      return instance[method](arg);
    } catch (e7) {
      consoleError(e7, elm);
    }
  }
  return void 0;
};
var addHydratedFlag = (elm) => {
  var _a3;
  return elm.classList.add((_a3 = BUILD.hydratedSelectorName) != null ? _a3 : "hydrated");
};
var getValue = (ref, propName) => getHostRef(ref).$instanceValues$.get(propName);
var setValue = (ref, propName, newVal, cmpMeta) => {
  const hostRef = getHostRef(ref);
  if (!hostRef) {
    return;
  }
  const elm = ref;
  const oldVal = hostRef.$instanceValues$.get(propName);
  const flags = hostRef.$flags$;
  const instance = elm;
  newVal = parsePropertyValue(
    newVal,
    cmpMeta.$members$[propName][0]
  );
  const areBothNaN = Number.isNaN(oldVal) && Number.isNaN(newVal);
  const didValueChange = newVal !== oldVal && !areBothNaN;
  if (didValueChange) {
    hostRef.$instanceValues$.set(propName, newVal);
    {
      if ((flags & (2 | 16)) === 2) {
        if (instance.componentShouldUpdate) {
          if (instance.componentShouldUpdate(newVal, oldVal, propName) === false) {
            return;
          }
        }
        scheduleUpdate(hostRef, false);
      }
    }
  }
};
var proxyComponent = (Cstr, cmpMeta, flags) => {
  var _a3, _b;
  const prototype = Cstr.prototype;
  if (cmpMeta.$members$ || BUILD.watchCallback) {
    const members = Object.entries((_a3 = cmpMeta.$members$) != null ? _a3 : {});
    members.map(([memberName, [memberFlags]]) => {
      if (memberFlags & 31 || memberFlags & 32) {
        const { get: origGetter, set: origSetter } = Object.getOwnPropertyDescriptor(prototype, memberName) || {};
        if (origGetter)
          cmpMeta.$members$[memberName][0] |= 2048;
        if (origSetter)
          cmpMeta.$members$[memberName][0] |= 4096;
        {
          Object.defineProperty(prototype, memberName, {
            get() {
              {
                return origGetter ? origGetter.apply(this) : getValue(this, memberName);
              }
            },
            configurable: true,
            enumerable: true
          });
        }
        Object.defineProperty(prototype, memberName, {
          set(newValue) {
            const ref = getHostRef(this);
            if (!ref) {
              return;
            }
            if (origSetter) {
              const currentValue = memberFlags & 32 ? this[memberName] : ref.$hostElement$[memberName];
              if (typeof currentValue === "undefined" && ref.$instanceValues$.get(memberName)) {
                newValue = ref.$instanceValues$.get(memberName);
              } else if (!ref.$instanceValues$.get(memberName) && currentValue) {
                ref.$instanceValues$.set(memberName, currentValue);
              }
              origSetter.apply(this, [
                parsePropertyValue(
                  newValue,
                  memberFlags
                )
              ]);
              newValue = memberFlags & 32 ? this[memberName] : ref.$hostElement$[memberName];
              setValue(this, memberName, newValue, cmpMeta);
              return;
            }
            {
              setValue(this, memberName, newValue, cmpMeta);
              return;
            }
          }
        });
      }
    });
    {
      const attrNameToPropName = /* @__PURE__ */ new Map();
      prototype.attributeChangedCallback = function(attrName, oldValue, newValue) {
        plt.jmp(() => {
          var _a22;
          const propName = attrNameToPropName.get(attrName);
          if (this.hasOwnProperty(propName) && BUILD.lazyLoad)
            ;
          else if (prototype.hasOwnProperty(propName) && typeof this[propName] === "number" && // cast type to number to avoid TS compiler issues
          this[propName] == newValue) {
            return;
          } else if (propName == null) {
            const hostRef = getHostRef(this);
            const flags2 = hostRef == null ? void 0 : hostRef.$flags$;
            if (hostRef && flags2 && !(flags2 & 8) && flags2 & 128 && newValue !== oldValue) {
              const elm = this;
              const instance = elm;
              const entry = (_a22 = cmpMeta.$watchers$) == null ? void 0 : _a22[attrName];
              entry == null ? void 0 : entry.forEach((callbackName) => {
                if (instance[callbackName] != null) {
                  instance[callbackName].call(instance, newValue, oldValue, attrName);
                }
              });
            }
            return;
          }
          const propDesc = Object.getOwnPropertyDescriptor(prototype, propName);
          newValue = newValue === null && typeof this[propName] === "boolean" ? false : newValue;
          if (newValue !== this[propName] && (!propDesc.get || !!propDesc.set)) {
            this[propName] = newValue;
          }
        });
      };
      Cstr.observedAttributes = Array.from(
        /* @__PURE__ */ new Set([
          ...Object.keys((_b = cmpMeta.$watchers$) != null ? _b : {}),
          ...members.filter(
            ([_, m]) => m[0] & 15
            /* HasAttribute */
          ).map(([propName, m]) => {
            const attrName = m[1] || propName;
            attrNameToPropName.set(attrName, propName);
            return attrName;
          })
        ])
      );
    }
  }
  return Cstr;
};
var initializeComponent = async (elm, hostRef, cmpMeta, hmrVersionId) => {
  let Cstr;
  if ((hostRef.$flags$ & 32) === 0) {
    hostRef.$flags$ |= 32;
    {
      Cstr = elm.constructor;
      const cmpTag = elm.localName;
      customElements.whenDefined(cmpTag).then(
        () => hostRef.$flags$ |= 128
        /* isWatchReady */
      );
    }
    if (Cstr && Cstr.style) {
      let style;
      if (typeof Cstr.style === "string") {
        style = Cstr.style;
      }
      const scopeId2 = getScopeId(cmpMeta);
      if (!styles.has(scopeId2)) {
        const endRegisterStyles = createTime("registerStyles", cmpMeta.$tagName$);
        registerStyle(scopeId2, style, !!(cmpMeta.$flags$ & 1));
        endRegisterStyles();
      }
    }
  }
  const ancestorComponent = hostRef.$ancestorComponent$;
  const schedule = () => scheduleUpdate(hostRef, true);
  if (ancestorComponent && ancestorComponent["s-rc"]) {
    ancestorComponent["s-rc"].push(schedule);
  } else {
    schedule();
  }
};
var fireConnectedCallback = (instance, elm) => {
};
var connectedCallback = (elm) => {
  if ((plt.$flags$ & 1) === 0) {
    const hostRef = getHostRef(elm);
    if (!hostRef) {
      return;
    }
    const cmpMeta = hostRef.$cmpMeta$;
    const endConnected = createTime("connectedCallback", cmpMeta.$tagName$);
    if (!(hostRef.$flags$ & 1)) {
      hostRef.$flags$ |= 1;
      {
        let ancestorComponent = elm;
        while (ancestorComponent = ancestorComponent.parentNode || ancestorComponent.host) {
          if (ancestorComponent["s-p"]) {
            attachToAncestor(hostRef, hostRef.$ancestorComponent$ = ancestorComponent);
            break;
          }
        }
      }
      if (cmpMeta.$members$) {
        Object.entries(cmpMeta.$members$).map(([memberName, [memberFlags]]) => {
          if (memberFlags & 31 && elm.hasOwnProperty(memberName)) {
            const value = elm[memberName];
            delete elm[memberName];
            elm[memberName] = value;
          }
        });
      }
      if (BUILD.initializeNextTick) {
        nextTick(() => initializeComponent(elm, hostRef, cmpMeta));
      } else {
        initializeComponent(elm, hostRef, cmpMeta);
      }
    } else {
      if (hostRef == null ? void 0 : hostRef.$lazyInstance$)
        ;
      else if (hostRef == null ? void 0 : hostRef.$onReadyPromise$) {
        hostRef.$onReadyPromise$.then(() => fireConnectedCallback());
      }
    }
    endConnected();
  }
};
var disconnectedCallback = async (elm) => {
  if ((plt.$flags$ & 1) === 0) {
    getHostRef(elm);
  }
  if (rootAppliedStyles.has(elm)) {
    rootAppliedStyles.delete(elm);
  }
  if (elm.shadowRoot && rootAppliedStyles.has(elm.shadowRoot)) {
    rootAppliedStyles.delete(elm.shadowRoot);
  }
};
var proxyCustomElement = (Cstr, compactMeta) => {
  const cmpMeta = {
    $flags$: compactMeta[0],
    $tagName$: compactMeta[1]
  };
  {
    cmpMeta.$members$ = compactMeta[2];
  }
  const originalConnectedCallback = Cstr.prototype.connectedCallback;
  const originalDisconnectedCallback = Cstr.prototype.disconnectedCallback;
  Object.assign(Cstr.prototype, {
    __hasHostListenerAttached: false,
    __registerHost() {
      registerHost(this, cmpMeta);
    },
    connectedCallback() {
      if (!this.__hasHostListenerAttached) {
        const hostRef = getHostRef(this);
        if (!hostRef) {
          return;
        }
        this.__hasHostListenerAttached = true;
      }
      connectedCallback(this);
      if (originalConnectedCallback) {
        originalConnectedCallback.call(this);
      }
    },
    disconnectedCallback() {
      disconnectedCallback(this);
      if (originalDisconnectedCallback) {
        originalDisconnectedCallback.call(this);
      }
    },
    __attachShadow() {
      {
        if (!this.shadowRoot) {
          createShadowRoot.call(this, cmpMeta);
        } else {
          if (this.shadowRoot.mode !== "open") {
            throw new Error(
              `Unable to re-use existing shadow root for ${cmpMeta.$tagName$}! Mode is set to ${this.shadowRoot.mode} but Stencil only supports open shadow roots.`
            );
          }
        }
      }
    }
  });
  Cstr.is = cmpMeta.$tagName$;
  return proxyComponent(Cstr, cmpMeta);
};
var setNonce = (nonce) => plt.$nonce$ = nonce;
var setPlatformOptions = (opts) => Object.assign(plt, opts);
function render(vnode, container) {
  const ref = {
    $hostElement$: container
  };
  renderVdom(ref, vnode);
}

// dist/components/p-Dytd6a2c.js
var searchComponents = {
  // Add entries as such when new components are added/moved to Lit.
  // 'atomic-text': async () => await import('./atomic-text/atomic-text.js'),
};
if (typeof window !== "undefined") {
  const discover = async (root) => {
    const rootTagName = root instanceof Element ? root.tagName.toLowerCase() : "";
    const rootIsAtomicElement = rootTagName?.startsWith("atomic-");
    const tags = [...root.querySelectorAll(":not(:defined)")].map((el3) => el3.tagName.toLowerCase()).filter((tag) => tag.startsWith("atomic-"));
    if (rootIsAtomicElement && !customElements.get(rootTagName)) {
      tags.push(rootTagName);
    }
    if (rootIsAtomicElement) {
      const childTemplates = root.querySelectorAll("template");
      for (const template of childTemplates) {
        discover(template.content);
        observer.observe(template.content, { subtree: true, childList: true });
      }
      if ("shadowRoot" in root && root.shadowRoot) {
        discover(root.shadowRoot);
        observer.observe(root.shadowRoot, { subtree: true, childList: true });
      }
    }
    const tagsToRegister = [...new Set(tags)];
    await Promise.allSettled(
      tagsToRegister.map((tagName) => register(tagName))
    );
    customElements.upgrade(root);
  };
  const register = (tagName) => {
    if (customElements.get(tagName)) {
      return Promise.resolve();
    }
    return searchComponents[tagName]?.();
  };
  const observer = new MutationObserver((mutations) => {
    for (const { addedNodes } of mutations) {
      for (const node of addedNodes) {
        if (node.nodeType === Node.ELEMENT_NODE) {
          discover(node);
        }
      }
    }
  });
  discover(document.body);
  observer.observe(document.documentElement, { subtree: true, childList: true });
}
var __defProp3 = Object.defineProperty;
var __export2 = (target, all) => {
  for (var name in all)
    __defProp3(target, name, { get: all[name], enumerable: true });
};
var result_exports2 = {};
__export2(result_exports2, {
  err: () => err2,
  map: () => map2,
  ok: () => ok$1,
  unwrap: () => unwrap2,
  unwrapErr: () => unwrapErr2
});
var ok$1 = (value) => ({
  isOk: true,
  isErr: false,
  value
});
var err2 = (value) => ({
  isOk: false,
  isErr: true,
  value
});
function map2(result, fn) {
  if (result.isOk) {
    const val = fn(result.value);
    if (val instanceof Promise) {
      return val.then((newVal) => ok$1(newVal));
    } else {
      return ok$1(val);
    }
  }
  if (result.isErr) {
    const value = result.value;
    return err2(value);
  }
  throw "should never get here";
}
var unwrap2 = (result) => {
  if (result.isOk) {
    return result.value;
  } else {
    throw result.value;
  }
};
var unwrapErr2 = (result) => {
  if (result.isErr) {
    return result.value;
  } else {
    throw result.value;
  }
};
function buildCustomEvent(name, detail) {
  return new CustomEvent(name, {
    detail,
    // Event will bubble up the DOM until it is caught
    bubbles: true,
    // Allows to verify if event is caught (cancelled). If it's not caught, it won't be initialized.
    cancelable: true,
    // Allows to compose Atomic components inside one another, event will go across DOM/Shadow DOM
    composed: true
  });
}
var commonjsGlobal = typeof globalThis !== "undefined" ? globalThis : typeof window !== "undefined" ? window : typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : {};
var purify = { exports: {} };
(function(module, exports) {
  (function(global2, factory) {
    module.exports = factory();
  })(commonjsGlobal, function() {
    const {
      entries,
      setPrototypeOf,
      isFrozen,
      getPrototypeOf,
      getOwnPropertyDescriptor
    } = Object;
    let {
      freeze,
      seal,
      create
    } = Object;
    let {
      apply,
      construct
    } = typeof Reflect !== "undefined" && Reflect;
    if (!freeze) {
      freeze = function freeze2(x2) {
        return x2;
      };
    }
    if (!seal) {
      seal = function seal2(x2) {
        return x2;
      };
    }
    if (!apply) {
      apply = function apply2(fun, thisValue, args) {
        return fun.apply(thisValue, args);
      };
    }
    if (!construct) {
      construct = function construct2(Func, args) {
        return new Func(...args);
      };
    }
    const arrayForEach = unapply(Array.prototype.forEach);
    const arrayLastIndexOf = unapply(Array.prototype.lastIndexOf);
    const arrayPop = unapply(Array.prototype.pop);
    const arrayPush = unapply(Array.prototype.push);
    const arraySplice = unapply(Array.prototype.splice);
    const stringToLowerCase = unapply(String.prototype.toLowerCase);
    const stringToString = unapply(String.prototype.toString);
    const stringMatch = unapply(String.prototype.match);
    const stringReplace = unapply(String.prototype.replace);
    const stringIndexOf = unapply(String.prototype.indexOf);
    const stringTrim = unapply(String.prototype.trim);
    const objectHasOwnProperty = unapply(Object.prototype.hasOwnProperty);
    const regExpTest = unapply(RegExp.prototype.test);
    const typeErrorCreate = unconstruct(TypeError);
    function unapply(func) {
      return function(thisArg) {
        for (var _len = arguments.length, args = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
          args[_key - 1] = arguments[_key];
        }
        return apply(func, thisArg, args);
      };
    }
    function unconstruct(func) {
      return function() {
        for (var _len2 = arguments.length, args = new Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
          args[_key2] = arguments[_key2];
        }
        return construct(func, args);
      };
    }
    function addToSet(set, array) {
      let transformCaseFunc = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : stringToLowerCase;
      if (setPrototypeOf) {
        setPrototypeOf(set, null);
      }
      let l = array.length;
      while (l--) {
        let element = array[l];
        if (typeof element === "string") {
          const lcElement = transformCaseFunc(element);
          if (lcElement !== element) {
            if (!isFrozen(array)) {
              array[l] = lcElement;
            }
            element = lcElement;
          }
        }
        set[element] = true;
      }
      return set;
    }
    function cleanArray(array) {
      for (let index = 0; index < array.length; index++) {
        const isPropertyExist = objectHasOwnProperty(array, index);
        if (!isPropertyExist) {
          array[index] = null;
        }
      }
      return array;
    }
    function clone(object) {
      const newObject = create(null);
      for (const [property, value] of entries(object)) {
        const isPropertyExist = objectHasOwnProperty(object, property);
        if (isPropertyExist) {
          if (Array.isArray(value)) {
            newObject[property] = cleanArray(value);
          } else if (value && typeof value === "object" && value.constructor === Object) {
            newObject[property] = clone(value);
          } else {
            newObject[property] = value;
          }
        }
      }
      return newObject;
    }
    function lookupGetter(object, prop) {
      while (object !== null) {
        const desc = getOwnPropertyDescriptor(object, prop);
        if (desc) {
          if (desc.get) {
            return unapply(desc.get);
          }
          if (typeof desc.value === "function") {
            return unapply(desc.value);
          }
        }
        object = getPrototypeOf(object);
      }
      function fallbackValue() {
        return null;
      }
      return fallbackValue;
    }
    const html$1 = freeze(["a", "abbr", "acronym", "address", "area", "article", "aside", "audio", "b", "bdi", "bdo", "big", "blink", "blockquote", "body", "br", "button", "canvas", "caption", "center", "cite", "code", "col", "colgroup", "content", "data", "datalist", "dd", "decorator", "del", "details", "dfn", "dialog", "dir", "div", "dl", "dt", "element", "em", "fieldset", "figcaption", "figure", "font", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html", "i", "img", "input", "ins", "kbd", "label", "legend", "li", "main", "map", "mark", "marquee", "menu", "menuitem", "meter", "nav", "nobr", "ol", "optgroup", "option", "output", "p", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "section", "select", "shadow", "small", "source", "spacer", "span", "strike", "strong", "style", "sub", "summary", "sup", "table", "tbody", "td", "template", "textarea", "tfoot", "th", "thead", "time", "tr", "track", "tt", "u", "ul", "var", "video", "wbr"]);
    const svg$1 = freeze(["svg", "a", "altglyph", "altglyphdef", "altglyphitem", "animatecolor", "animatemotion", "animatetransform", "circle", "clippath", "defs", "desc", "ellipse", "filter", "font", "g", "glyph", "glyphref", "hkern", "image", "line", "lineargradient", "marker", "mask", "metadata", "mpath", "path", "pattern", "polygon", "polyline", "radialgradient", "rect", "stop", "style", "switch", "symbol", "text", "textpath", "title", "tref", "tspan", "view", "vkern"]);
    const svgFilters = freeze(["feBlend", "feColorMatrix", "feComponentTransfer", "feComposite", "feConvolveMatrix", "feDiffuseLighting", "feDisplacementMap", "feDistantLight", "feDropShadow", "feFlood", "feFuncA", "feFuncB", "feFuncG", "feFuncR", "feGaussianBlur", "feImage", "feMerge", "feMergeNode", "feMorphology", "feOffset", "fePointLight", "feSpecularLighting", "feSpotLight", "feTile", "feTurbulence"]);
    const svgDisallowed = freeze(["animate", "color-profile", "cursor", "discard", "font-face", "font-face-format", "font-face-name", "font-face-src", "font-face-uri", "foreignobject", "hatch", "hatchpath", "mesh", "meshgradient", "meshpatch", "meshrow", "missing-glyph", "script", "set", "solidcolor", "unknown", "use"]);
    const mathMl$1 = freeze(["math", "menclose", "merror", "mfenced", "mfrac", "mglyph", "mi", "mlabeledtr", "mmultiscripts", "mn", "mo", "mover", "mpadded", "mphantom", "mroot", "mrow", "ms", "mspace", "msqrt", "mstyle", "msub", "msup", "msubsup", "mtable", "mtd", "mtext", "mtr", "munder", "munderover", "mprescripts"]);
    const mathMlDisallowed = freeze(["maction", "maligngroup", "malignmark", "mlongdiv", "mscarries", "mscarry", "msgroup", "mstack", "msline", "msrow", "semantics", "annotation", "annotation-xml", "mprescripts", "none"]);
    const text = freeze(["#text"]);
    const html = freeze(["accept", "action", "align", "alt", "autocapitalize", "autocomplete", "autopictureinpicture", "autoplay", "background", "bgcolor", "border", "capture", "cellpadding", "cellspacing", "checked", "cite", "class", "clear", "color", "cols", "colspan", "controls", "controlslist", "coords", "crossorigin", "datetime", "decoding", "default", "dir", "disabled", "disablepictureinpicture", "disableremoteplayback", "download", "draggable", "enctype", "enterkeyhint", "face", "for", "headers", "height", "hidden", "high", "href", "hreflang", "id", "inputmode", "integrity", "ismap", "kind", "label", "lang", "list", "loading", "loop", "low", "max", "maxlength", "media", "method", "min", "minlength", "multiple", "muted", "name", "nonce", "noshade", "novalidate", "nowrap", "open", "optimum", "pattern", "placeholder", "playsinline", "popover", "popovertarget", "popovertargetaction", "poster", "preload", "pubdate", "radiogroup", "readonly", "rel", "required", "rev", "reversed", "role", "rows", "rowspan", "spellcheck", "scope", "selected", "shape", "size", "sizes", "span", "srclang", "start", "src", "srcset", "step", "style", "summary", "tabindex", "title", "translate", "type", "usemap", "valign", "value", "width", "wrap", "xmlns", "slot"]);
    const svg = freeze(["accent-height", "accumulate", "additive", "alignment-baseline", "amplitude", "ascent", "attributename", "attributetype", "azimuth", "basefrequency", "baseline-shift", "begin", "bias", "by", "class", "clip", "clippathunits", "clip-path", "clip-rule", "color", "color-interpolation", "color-interpolation-filters", "color-profile", "color-rendering", "cx", "cy", "d", "dx", "dy", "diffuseconstant", "direction", "display", "divisor", "dur", "edgemode", "elevation", "end", "exponent", "fill", "fill-opacity", "fill-rule", "filter", "filterunits", "flood-color", "flood-opacity", "font-family", "font-size", "font-size-adjust", "font-stretch", "font-style", "font-variant", "font-weight", "fx", "fy", "g1", "g2", "glyph-name", "glyphref", "gradientunits", "gradienttransform", "height", "href", "id", "image-rendering", "in", "in2", "intercept", "k", "k1", "k2", "k3", "k4", "kerning", "keypoints", "keysplines", "keytimes", "lang", "lengthadjust", "letter-spacing", "kernelmatrix", "kernelunitlength", "lighting-color", "local", "marker-end", "marker-mid", "marker-start", "markerheight", "markerunits", "markerwidth", "maskcontentunits", "maskunits", "max", "mask", "media", "method", "mode", "min", "name", "numoctaves", "offset", "operator", "opacity", "order", "orient", "orientation", "origin", "overflow", "paint-order", "path", "pathlength", "patterncontentunits", "patterntransform", "patternunits", "points", "preservealpha", "preserveaspectratio", "primitiveunits", "r", "rx", "ry", "radius", "refx", "refy", "repeatcount", "repeatdur", "restart", "result", "rotate", "scale", "seed", "shape-rendering", "slope", "specularconstant", "specularexponent", "spreadmethod", "startoffset", "stddeviation", "stitchtiles", "stop-color", "stop-opacity", "stroke-dasharray", "stroke-dashoffset", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity", "stroke", "stroke-width", "style", "surfacescale", "systemlanguage", "tabindex", "tablevalues", "targetx", "targety", "transform", "transform-origin", "text-anchor", "text-decoration", "text-rendering", "textlength", "type", "u1", "u2", "unicode", "values", "viewbox", "visibility", "version", "vert-adv-y", "vert-origin-x", "vert-origin-y", "width", "word-spacing", "wrap", "writing-mode", "xchannelselector", "ychannelselector", "x", "x1", "x2", "xmlns", "y", "y1", "y2", "z", "zoomandpan"]);
    const mathMl = freeze(["accent", "accentunder", "align", "bevelled", "close", "columnsalign", "columnlines", "columnspan", "denomalign", "depth", "dir", "display", "displaystyle", "encoding", "fence", "frame", "height", "href", "id", "largeop", "length", "linethickness", "lspace", "lquote", "mathbackground", "mathcolor", "mathsize", "mathvariant", "maxsize", "minsize", "movablelimits", "notation", "numalign", "open", "rowalign", "rowlines", "rowspacing", "rowspan", "rspace", "rquote", "scriptlevel", "scriptminsize", "scriptsizemultiplier", "selection", "separator", "separators", "stretchy", "subscriptshift", "supscriptshift", "symmetric", "voffset", "width", "xmlns"]);
    const xml = freeze(["xlink:href", "xml:id", "xlink:title", "xml:space", "xmlns:xlink"]);
    const MUSTACHE_EXPR = seal(/\{\{[\w\W]*|[\w\W]*\}\}/gm);
    const ERB_EXPR = seal(/<%[\w\W]*|[\w\W]*%>/gm);
    const TMPLIT_EXPR = seal(/\$\{[\w\W]*/gm);
    const DATA_ATTR = seal(/^data-[\-\w.\u00B7-\uFFFF]+$/);
    const ARIA_ATTR = seal(/^aria-[\-\w]+$/);
    const IS_ALLOWED_URI = seal(
      /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
      // eslint-disable-line no-useless-escape
    );
    const IS_SCRIPT_OR_DATA = seal(/^(?:\w+script|data):/i);
    const ATTR_WHITESPACE = seal(
      /[\u0000-\u0020\u00A0\u1680\u180E\u2000-\u2029\u205F\u3000]/g
      // eslint-disable-line no-control-regex
    );
    const DOCTYPE_NAME = seal(/^html$/i);
    const CUSTOM_ELEMENT = seal(/^[a-z][.\w]*(-[.\w]+)+$/i);
    var EXPRESSIONS = /* @__PURE__ */ Object.freeze({
      __proto__: null,
      ARIA_ATTR,
      ATTR_WHITESPACE,
      CUSTOM_ELEMENT,
      DATA_ATTR,
      DOCTYPE_NAME,
      ERB_EXPR,
      IS_ALLOWED_URI,
      IS_SCRIPT_OR_DATA,
      MUSTACHE_EXPR,
      TMPLIT_EXPR
    });
    const NODE_TYPE = {
      element: 1,
      text: 3,
      // Deprecated
      progressingInstruction: 7,
      comment: 8,
      document: 9
    };
    const getGlobal = function getGlobal2() {
      return typeof window === "undefined" ? null : window;
    };
    const _createTrustedTypesPolicy = function _createTrustedTypesPolicy2(trustedTypes, purifyHostElement) {
      if (typeof trustedTypes !== "object" || typeof trustedTypes.createPolicy !== "function") {
        return null;
      }
      let suffix = null;
      const ATTR_NAME = "data-tt-policy-suffix";
      if (purifyHostElement && purifyHostElement.hasAttribute(ATTR_NAME)) {
        suffix = purifyHostElement.getAttribute(ATTR_NAME);
      }
      const policyName = "dompurify" + (suffix ? "#" + suffix : "");
      try {
        return trustedTypes.createPolicy(policyName, {
          createHTML(html2) {
            return html2;
          },
          createScriptURL(scriptUrl) {
            return scriptUrl;
          }
        });
      } catch (_) {
        console.warn("TrustedTypes policy " + policyName + " could not be created.");
        return null;
      }
    };
    const _createHooksMap = function _createHooksMap2() {
      return {
        afterSanitizeAttributes: [],
        afterSanitizeElements: [],
        afterSanitizeShadowDOM: [],
        beforeSanitizeAttributes: [],
        beforeSanitizeElements: [],
        beforeSanitizeShadowDOM: [],
        uponSanitizeAttribute: [],
        uponSanitizeElement: [],
        uponSanitizeShadowNode: []
      };
    };
    function createDOMPurify() {
      let window2 = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : getGlobal();
      const DOMPurify = (root) => createDOMPurify(root);
      DOMPurify.version = "3.2.4";
      DOMPurify.removed = [];
      if (!window2 || !window2.document || window2.document.nodeType !== NODE_TYPE.document || !window2.Element) {
        DOMPurify.isSupported = false;
        return DOMPurify;
      }
      let {
        document: document2
      } = window2;
      const originalDocument = document2;
      const currentScript = originalDocument.currentScript;
      const {
        DocumentFragment,
        HTMLTemplateElement,
        Node: Node2,
        Element: Element2,
        NodeFilter,
        NamedNodeMap = window2.NamedNodeMap || window2.MozNamedAttrMap,
        HTMLFormElement,
        DOMParser,
        trustedTypes
      } = window2;
      const ElementPrototype = Element2.prototype;
      const cloneNode = lookupGetter(ElementPrototype, "cloneNode");
      const remove = lookupGetter(ElementPrototype, "remove");
      const getNextSibling = lookupGetter(ElementPrototype, "nextSibling");
      const getChildNodes = lookupGetter(ElementPrototype, "childNodes");
      const getParentNode = lookupGetter(ElementPrototype, "parentNode");
      if (typeof HTMLTemplateElement === "function") {
        const template = document2.createElement("template");
        if (template.content && template.content.ownerDocument) {
          document2 = template.content.ownerDocument;
        }
      }
      let trustedTypesPolicy;
      let emptyHTML = "";
      const {
        implementation,
        createNodeIterator,
        createDocumentFragment,
        getElementsByTagName
      } = document2;
      const {
        importNode
      } = originalDocument;
      let hooks = _createHooksMap();
      DOMPurify.isSupported = typeof entries === "function" && typeof getParentNode === "function" && implementation && implementation.createHTMLDocument !== void 0;
      const {
        MUSTACHE_EXPR: MUSTACHE_EXPR2,
        ERB_EXPR: ERB_EXPR2,
        TMPLIT_EXPR: TMPLIT_EXPR2,
        DATA_ATTR: DATA_ATTR2,
        ARIA_ATTR: ARIA_ATTR2,
        IS_SCRIPT_OR_DATA: IS_SCRIPT_OR_DATA2,
        ATTR_WHITESPACE: ATTR_WHITESPACE2,
        CUSTOM_ELEMENT: CUSTOM_ELEMENT2
      } = EXPRESSIONS;
      let {
        IS_ALLOWED_URI: IS_ALLOWED_URI$1
      } = EXPRESSIONS;
      let ALLOWED_TAGS = null;
      const DEFAULT_ALLOWED_TAGS = addToSet({}, [...html$1, ...svg$1, ...svgFilters, ...mathMl$1, ...text]);
      let ALLOWED_ATTR = null;
      const DEFAULT_ALLOWED_ATTR = addToSet({}, [...html, ...svg, ...mathMl, ...xml]);
      let CUSTOM_ELEMENT_HANDLING = Object.seal(create(null, {
        tagNameCheck: {
          writable: true,
          configurable: false,
          enumerable: true,
          value: null
        },
        attributeNameCheck: {
          writable: true,
          configurable: false,
          enumerable: true,
          value: null
        },
        allowCustomizedBuiltInElements: {
          writable: true,
          configurable: false,
          enumerable: true,
          value: false
        }
      }));
      let FORBID_TAGS = null;
      let FORBID_ATTR = null;
      let ALLOW_ARIA_ATTR = true;
      let ALLOW_DATA_ATTR = true;
      let ALLOW_UNKNOWN_PROTOCOLS = false;
      let ALLOW_SELF_CLOSE_IN_ATTR = true;
      let SAFE_FOR_TEMPLATES = false;
      let SAFE_FOR_XML = true;
      let WHOLE_DOCUMENT = false;
      let SET_CONFIG = false;
      let FORCE_BODY = false;
      let RETURN_DOM = false;
      let RETURN_DOM_FRAGMENT = false;
      let RETURN_TRUSTED_TYPE = false;
      let SANITIZE_DOM = true;
      let SANITIZE_NAMED_PROPS = false;
      const SANITIZE_NAMED_PROPS_PREFIX = "user-content-";
      let KEEP_CONTENT = true;
      let IN_PLACE = false;
      let USE_PROFILES = {};
      let FORBID_CONTENTS = null;
      const DEFAULT_FORBID_CONTENTS = addToSet({}, ["annotation-xml", "audio", "colgroup", "desc", "foreignobject", "head", "iframe", "math", "mi", "mn", "mo", "ms", "mtext", "noembed", "noframes", "noscript", "plaintext", "script", "style", "svg", "template", "thead", "title", "video", "xmp"]);
      let DATA_URI_TAGS = null;
      const DEFAULT_DATA_URI_TAGS = addToSet({}, ["audio", "video", "img", "source", "image", "track"]);
      let URI_SAFE_ATTRIBUTES = null;
      const DEFAULT_URI_SAFE_ATTRIBUTES = addToSet({}, ["alt", "class", "for", "id", "label", "name", "pattern", "placeholder", "role", "summary", "title", "value", "style", "xmlns"]);
      const MATHML_NAMESPACE = "http://www.w3.org/1998/Math/MathML";
      const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
      const HTML_NAMESPACE = "http://www.w3.org/1999/xhtml";
      let NAMESPACE2 = HTML_NAMESPACE;
      let IS_EMPTY_INPUT = false;
      let ALLOWED_NAMESPACES = null;
      const DEFAULT_ALLOWED_NAMESPACES = addToSet({}, [MATHML_NAMESPACE, SVG_NAMESPACE, HTML_NAMESPACE], stringToString);
      let MATHML_TEXT_INTEGRATION_POINTS = addToSet({}, ["mi", "mo", "mn", "ms", "mtext"]);
      let HTML_INTEGRATION_POINTS = addToSet({}, ["annotation-xml"]);
      const COMMON_SVG_AND_HTML_ELEMENTS = addToSet({}, ["title", "style", "font", "a", "script"]);
      let PARSER_MEDIA_TYPE = null;
      const SUPPORTED_PARSER_MEDIA_TYPES = ["application/xhtml+xml", "text/html"];
      const DEFAULT_PARSER_MEDIA_TYPE = "text/html";
      let transformCaseFunc = null;
      let CONFIG = null;
      const formElement = document2.createElement("form");
      const isRegexOrFunction = function isRegexOrFunction2(testValue) {
        return testValue instanceof RegExp || testValue instanceof Function;
      };
      const _parseConfig = function _parseConfig2() {
        let cfg = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
        if (CONFIG && CONFIG === cfg) {
          return;
        }
        if (!cfg || typeof cfg !== "object") {
          cfg = {};
        }
        cfg = clone(cfg);
        PARSER_MEDIA_TYPE = // eslint-disable-next-line unicorn/prefer-includes
        SUPPORTED_PARSER_MEDIA_TYPES.indexOf(cfg.PARSER_MEDIA_TYPE) === -1 ? DEFAULT_PARSER_MEDIA_TYPE : cfg.PARSER_MEDIA_TYPE;
        transformCaseFunc = PARSER_MEDIA_TYPE === "application/xhtml+xml" ? stringToString : stringToLowerCase;
        ALLOWED_TAGS = objectHasOwnProperty(cfg, "ALLOWED_TAGS") ? addToSet({}, cfg.ALLOWED_TAGS, transformCaseFunc) : DEFAULT_ALLOWED_TAGS;
        ALLOWED_ATTR = objectHasOwnProperty(cfg, "ALLOWED_ATTR") ? addToSet({}, cfg.ALLOWED_ATTR, transformCaseFunc) : DEFAULT_ALLOWED_ATTR;
        ALLOWED_NAMESPACES = objectHasOwnProperty(cfg, "ALLOWED_NAMESPACES") ? addToSet({}, cfg.ALLOWED_NAMESPACES, stringToString) : DEFAULT_ALLOWED_NAMESPACES;
        URI_SAFE_ATTRIBUTES = objectHasOwnProperty(cfg, "ADD_URI_SAFE_ATTR") ? addToSet(clone(DEFAULT_URI_SAFE_ATTRIBUTES), cfg.ADD_URI_SAFE_ATTR, transformCaseFunc) : DEFAULT_URI_SAFE_ATTRIBUTES;
        DATA_URI_TAGS = objectHasOwnProperty(cfg, "ADD_DATA_URI_TAGS") ? addToSet(clone(DEFAULT_DATA_URI_TAGS), cfg.ADD_DATA_URI_TAGS, transformCaseFunc) : DEFAULT_DATA_URI_TAGS;
        FORBID_CONTENTS = objectHasOwnProperty(cfg, "FORBID_CONTENTS") ? addToSet({}, cfg.FORBID_CONTENTS, transformCaseFunc) : DEFAULT_FORBID_CONTENTS;
        FORBID_TAGS = objectHasOwnProperty(cfg, "FORBID_TAGS") ? addToSet({}, cfg.FORBID_TAGS, transformCaseFunc) : {};
        FORBID_ATTR = objectHasOwnProperty(cfg, "FORBID_ATTR") ? addToSet({}, cfg.FORBID_ATTR, transformCaseFunc) : {};
        USE_PROFILES = objectHasOwnProperty(cfg, "USE_PROFILES") ? cfg.USE_PROFILES : false;
        ALLOW_ARIA_ATTR = cfg.ALLOW_ARIA_ATTR !== false;
        ALLOW_DATA_ATTR = cfg.ALLOW_DATA_ATTR !== false;
        ALLOW_UNKNOWN_PROTOCOLS = cfg.ALLOW_UNKNOWN_PROTOCOLS || false;
        ALLOW_SELF_CLOSE_IN_ATTR = cfg.ALLOW_SELF_CLOSE_IN_ATTR !== false;
        SAFE_FOR_TEMPLATES = cfg.SAFE_FOR_TEMPLATES || false;
        SAFE_FOR_XML = cfg.SAFE_FOR_XML !== false;
        WHOLE_DOCUMENT = cfg.WHOLE_DOCUMENT || false;
        RETURN_DOM = cfg.RETURN_DOM || false;
        RETURN_DOM_FRAGMENT = cfg.RETURN_DOM_FRAGMENT || false;
        RETURN_TRUSTED_TYPE = cfg.RETURN_TRUSTED_TYPE || false;
        FORCE_BODY = cfg.FORCE_BODY || false;
        SANITIZE_DOM = cfg.SANITIZE_DOM !== false;
        SANITIZE_NAMED_PROPS = cfg.SANITIZE_NAMED_PROPS || false;
        KEEP_CONTENT = cfg.KEEP_CONTENT !== false;
        IN_PLACE = cfg.IN_PLACE || false;
        IS_ALLOWED_URI$1 = cfg.ALLOWED_URI_REGEXP || IS_ALLOWED_URI;
        NAMESPACE2 = cfg.NAMESPACE || HTML_NAMESPACE;
        MATHML_TEXT_INTEGRATION_POINTS = cfg.MATHML_TEXT_INTEGRATION_POINTS || MATHML_TEXT_INTEGRATION_POINTS;
        HTML_INTEGRATION_POINTS = cfg.HTML_INTEGRATION_POINTS || HTML_INTEGRATION_POINTS;
        CUSTOM_ELEMENT_HANDLING = cfg.CUSTOM_ELEMENT_HANDLING || {};
        if (cfg.CUSTOM_ELEMENT_HANDLING && isRegexOrFunction(cfg.CUSTOM_ELEMENT_HANDLING.tagNameCheck)) {
          CUSTOM_ELEMENT_HANDLING.tagNameCheck = cfg.CUSTOM_ELEMENT_HANDLING.tagNameCheck;
        }
        if (cfg.CUSTOM_ELEMENT_HANDLING && isRegexOrFunction(cfg.CUSTOM_ELEMENT_HANDLING.attributeNameCheck)) {
          CUSTOM_ELEMENT_HANDLING.attributeNameCheck = cfg.CUSTOM_ELEMENT_HANDLING.attributeNameCheck;
        }
        if (cfg.CUSTOM_ELEMENT_HANDLING && typeof cfg.CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements === "boolean") {
          CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements = cfg.CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements;
        }
        if (SAFE_FOR_TEMPLATES) {
          ALLOW_DATA_ATTR = false;
        }
        if (RETURN_DOM_FRAGMENT) {
          RETURN_DOM = true;
        }
        if (USE_PROFILES) {
          ALLOWED_TAGS = addToSet({}, text);
          ALLOWED_ATTR = [];
          if (USE_PROFILES.html === true) {
            addToSet(ALLOWED_TAGS, html$1);
            addToSet(ALLOWED_ATTR, html);
          }
          if (USE_PROFILES.svg === true) {
            addToSet(ALLOWED_TAGS, svg$1);
            addToSet(ALLOWED_ATTR, svg);
            addToSet(ALLOWED_ATTR, xml);
          }
          if (USE_PROFILES.svgFilters === true) {
            addToSet(ALLOWED_TAGS, svgFilters);
            addToSet(ALLOWED_ATTR, svg);
            addToSet(ALLOWED_ATTR, xml);
          }
          if (USE_PROFILES.mathMl === true) {
            addToSet(ALLOWED_TAGS, mathMl$1);
            addToSet(ALLOWED_ATTR, mathMl);
            addToSet(ALLOWED_ATTR, xml);
          }
        }
        if (cfg.ADD_TAGS) {
          if (ALLOWED_TAGS === DEFAULT_ALLOWED_TAGS) {
            ALLOWED_TAGS = clone(ALLOWED_TAGS);
          }
          addToSet(ALLOWED_TAGS, cfg.ADD_TAGS, transformCaseFunc);
        }
        if (cfg.ADD_ATTR) {
          if (ALLOWED_ATTR === DEFAULT_ALLOWED_ATTR) {
            ALLOWED_ATTR = clone(ALLOWED_ATTR);
          }
          addToSet(ALLOWED_ATTR, cfg.ADD_ATTR, transformCaseFunc);
        }
        if (cfg.ADD_URI_SAFE_ATTR) {
          addToSet(URI_SAFE_ATTRIBUTES, cfg.ADD_URI_SAFE_ATTR, transformCaseFunc);
        }
        if (cfg.FORBID_CONTENTS) {
          if (FORBID_CONTENTS === DEFAULT_FORBID_CONTENTS) {
            FORBID_CONTENTS = clone(FORBID_CONTENTS);
          }
          addToSet(FORBID_CONTENTS, cfg.FORBID_CONTENTS, transformCaseFunc);
        }
        if (KEEP_CONTENT) {
          ALLOWED_TAGS["#text"] = true;
        }
        if (WHOLE_DOCUMENT) {
          addToSet(ALLOWED_TAGS, ["html", "head", "body"]);
        }
        if (ALLOWED_TAGS.table) {
          addToSet(ALLOWED_TAGS, ["tbody"]);
          delete FORBID_TAGS.tbody;
        }
        if (cfg.TRUSTED_TYPES_POLICY) {
          if (typeof cfg.TRUSTED_TYPES_POLICY.createHTML !== "function") {
            throw typeErrorCreate('TRUSTED_TYPES_POLICY configuration option must provide a "createHTML" hook.');
          }
          if (typeof cfg.TRUSTED_TYPES_POLICY.createScriptURL !== "function") {
            throw typeErrorCreate('TRUSTED_TYPES_POLICY configuration option must provide a "createScriptURL" hook.');
          }
          trustedTypesPolicy = cfg.TRUSTED_TYPES_POLICY;
          emptyHTML = trustedTypesPolicy.createHTML("");
        } else {
          if (trustedTypesPolicy === void 0) {
            trustedTypesPolicy = _createTrustedTypesPolicy(trustedTypes, currentScript);
          }
          if (trustedTypesPolicy !== null && typeof emptyHTML === "string") {
            emptyHTML = trustedTypesPolicy.createHTML("");
          }
        }
        if (freeze) {
          freeze(cfg);
        }
        CONFIG = cfg;
      };
      const ALL_SVG_TAGS = addToSet({}, [...svg$1, ...svgFilters, ...svgDisallowed]);
      const ALL_MATHML_TAGS = addToSet({}, [...mathMl$1, ...mathMlDisallowed]);
      const _checkValidNamespace = function _checkValidNamespace2(element) {
        let parent = getParentNode(element);
        if (!parent || !parent.tagName) {
          parent = {
            namespaceURI: NAMESPACE2,
            tagName: "template"
          };
        }
        const tagName = stringToLowerCase(element.tagName);
        const parentTagName = stringToLowerCase(parent.tagName);
        if (!ALLOWED_NAMESPACES[element.namespaceURI]) {
          return false;
        }
        if (element.namespaceURI === SVG_NAMESPACE) {
          if (parent.namespaceURI === HTML_NAMESPACE) {
            return tagName === "svg";
          }
          if (parent.namespaceURI === MATHML_NAMESPACE) {
            return tagName === "svg" && (parentTagName === "annotation-xml" || MATHML_TEXT_INTEGRATION_POINTS[parentTagName]);
          }
          return Boolean(ALL_SVG_TAGS[tagName]);
        }
        if (element.namespaceURI === MATHML_NAMESPACE) {
          if (parent.namespaceURI === HTML_NAMESPACE) {
            return tagName === "math";
          }
          if (parent.namespaceURI === SVG_NAMESPACE) {
            return tagName === "math" && HTML_INTEGRATION_POINTS[parentTagName];
          }
          return Boolean(ALL_MATHML_TAGS[tagName]);
        }
        if (element.namespaceURI === HTML_NAMESPACE) {
          if (parent.namespaceURI === SVG_NAMESPACE && !HTML_INTEGRATION_POINTS[parentTagName]) {
            return false;
          }
          if (parent.namespaceURI === MATHML_NAMESPACE && !MATHML_TEXT_INTEGRATION_POINTS[parentTagName]) {
            return false;
          }
          return !ALL_MATHML_TAGS[tagName] && (COMMON_SVG_AND_HTML_ELEMENTS[tagName] || !ALL_SVG_TAGS[tagName]);
        }
        if (PARSER_MEDIA_TYPE === "application/xhtml+xml" && ALLOWED_NAMESPACES[element.namespaceURI]) {
          return true;
        }
        return false;
      };
      const _forceRemove = function _forceRemove2(node) {
        arrayPush(DOMPurify.removed, {
          element: node
        });
        try {
          getParentNode(node).removeChild(node);
        } catch (_) {
          remove(node);
        }
      };
      const _removeAttribute = function _removeAttribute2(name, element) {
        try {
          arrayPush(DOMPurify.removed, {
            attribute: element.getAttributeNode(name),
            from: element
          });
        } catch (_) {
          arrayPush(DOMPurify.removed, {
            attribute: null,
            from: element
          });
        }
        element.removeAttribute(name);
        if (name === "is") {
          if (RETURN_DOM || RETURN_DOM_FRAGMENT) {
            try {
              _forceRemove(element);
            } catch (_) {
            }
          } else {
            try {
              element.setAttribute(name, "");
            } catch (_) {
            }
          }
        }
      };
      const _initDocument = function _initDocument2(dirty) {
        let doc = null;
        let leadingWhitespace = null;
        if (FORCE_BODY) {
          dirty = "<remove></remove>" + dirty;
        } else {
          const matches = stringMatch(dirty, /^[\r\n\t ]+/);
          leadingWhitespace = matches && matches[0];
        }
        if (PARSER_MEDIA_TYPE === "application/xhtml+xml" && NAMESPACE2 === HTML_NAMESPACE) {
          dirty = '<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body>' + dirty + "</body></html>";
        }
        const dirtyPayload = trustedTypesPolicy ? trustedTypesPolicy.createHTML(dirty) : dirty;
        if (NAMESPACE2 === HTML_NAMESPACE) {
          try {
            doc = new DOMParser().parseFromString(dirtyPayload, PARSER_MEDIA_TYPE);
          } catch (_) {
          }
        }
        if (!doc || !doc.documentElement) {
          doc = implementation.createDocument(NAMESPACE2, "template", null);
          try {
            doc.documentElement.innerHTML = IS_EMPTY_INPUT ? emptyHTML : dirtyPayload;
          } catch (_) {
          }
        }
        const body = doc.body || doc.documentElement;
        if (dirty && leadingWhitespace) {
          body.insertBefore(document2.createTextNode(leadingWhitespace), body.childNodes[0] || null);
        }
        if (NAMESPACE2 === HTML_NAMESPACE) {
          return getElementsByTagName.call(doc, WHOLE_DOCUMENT ? "html" : "body")[0];
        }
        return WHOLE_DOCUMENT ? doc.documentElement : body;
      };
      const _createNodeIterator = function _createNodeIterator2(root) {
        return createNodeIterator.call(
          root.ownerDocument || root,
          root,
          // eslint-disable-next-line no-bitwise
          NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_COMMENT | NodeFilter.SHOW_TEXT | NodeFilter.SHOW_PROCESSING_INSTRUCTION | NodeFilter.SHOW_CDATA_SECTION,
          null
        );
      };
      const _isClobbered = function _isClobbered2(element) {
        return element instanceof HTMLFormElement && (typeof element.nodeName !== "string" || typeof element.textContent !== "string" || typeof element.removeChild !== "function" || !(element.attributes instanceof NamedNodeMap) || typeof element.removeAttribute !== "function" || typeof element.setAttribute !== "function" || typeof element.namespaceURI !== "string" || typeof element.insertBefore !== "function" || typeof element.hasChildNodes !== "function");
      };
      const _isNode = function _isNode2(value) {
        return typeof Node2 === "function" && value instanceof Node2;
      };
      function _executeHooks(hooks2, currentNode, data) {
        arrayForEach(hooks2, (hook) => {
          hook.call(DOMPurify, currentNode, data, CONFIG);
        });
      }
      const _sanitizeElements = function _sanitizeElements2(currentNode) {
        let content = null;
        _executeHooks(hooks.beforeSanitizeElements, currentNode, null);
        if (_isClobbered(currentNode)) {
          _forceRemove(currentNode);
          return true;
        }
        const tagName = transformCaseFunc(currentNode.nodeName);
        _executeHooks(hooks.uponSanitizeElement, currentNode, {
          tagName,
          allowedTags: ALLOWED_TAGS
        });
        if (currentNode.hasChildNodes() && !_isNode(currentNode.firstElementChild) && regExpTest(/<[/\w]/g, currentNode.innerHTML) && regExpTest(/<[/\w]/g, currentNode.textContent)) {
          _forceRemove(currentNode);
          return true;
        }
        if (currentNode.nodeType === NODE_TYPE.progressingInstruction) {
          _forceRemove(currentNode);
          return true;
        }
        if (SAFE_FOR_XML && currentNode.nodeType === NODE_TYPE.comment && regExpTest(/<[/\w]/g, currentNode.data)) {
          _forceRemove(currentNode);
          return true;
        }
        if (!ALLOWED_TAGS[tagName] || FORBID_TAGS[tagName]) {
          if (!FORBID_TAGS[tagName] && _isBasicCustomElement(tagName)) {
            if (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.tagNameCheck, tagName)) {
              return false;
            }
            if (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.tagNameCheck(tagName)) {
              return false;
            }
          }
          if (KEEP_CONTENT && !FORBID_CONTENTS[tagName]) {
            const parentNode = getParentNode(currentNode) || currentNode.parentNode;
            const childNodes = getChildNodes(currentNode) || currentNode.childNodes;
            if (childNodes && parentNode) {
              const childCount = childNodes.length;
              for (let i = childCount - 1; i >= 0; --i) {
                const childClone = cloneNode(childNodes[i], true);
                childClone.__removalCount = (currentNode.__removalCount || 0) + 1;
                parentNode.insertBefore(childClone, getNextSibling(currentNode));
              }
            }
          }
          _forceRemove(currentNode);
          return true;
        }
        if (currentNode instanceof Element2 && !_checkValidNamespace(currentNode)) {
          _forceRemove(currentNode);
          return true;
        }
        if ((tagName === "noscript" || tagName === "noembed" || tagName === "noframes") && regExpTest(/<\/no(script|embed|frames)/i, currentNode.innerHTML)) {
          _forceRemove(currentNode);
          return true;
        }
        if (SAFE_FOR_TEMPLATES && currentNode.nodeType === NODE_TYPE.text) {
          content = currentNode.textContent;
          arrayForEach([MUSTACHE_EXPR2, ERB_EXPR2, TMPLIT_EXPR2], (expr) => {
            content = stringReplace(content, expr, " ");
          });
          if (currentNode.textContent !== content) {
            arrayPush(DOMPurify.removed, {
              element: currentNode.cloneNode()
            });
            currentNode.textContent = content;
          }
        }
        _executeHooks(hooks.afterSanitizeElements, currentNode, null);
        return false;
      };
      const _isValidAttribute = function _isValidAttribute2(lcTag, lcName, value) {
        if (SANITIZE_DOM && (lcName === "id" || lcName === "name") && (value in document2 || value in formElement)) {
          return false;
        }
        if (ALLOW_DATA_ATTR && !FORBID_ATTR[lcName] && regExpTest(DATA_ATTR2, lcName))
          ;
        else if (ALLOW_ARIA_ATTR && regExpTest(ARIA_ATTR2, lcName))
          ;
        else if (!ALLOWED_ATTR[lcName] || FORBID_ATTR[lcName]) {
          if (
            // First condition does a very basic check if a) it's basically a valid custom element tagname AND
            // b) if the tagName passes whatever the user has configured for CUSTOM_ELEMENT_HANDLING.tagNameCheck
            // and c) if the attribute name passes whatever the user has configured for CUSTOM_ELEMENT_HANDLING.attributeNameCheck
            _isBasicCustomElement(lcTag) && (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.tagNameCheck, lcTag) || CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.tagNameCheck(lcTag)) && (CUSTOM_ELEMENT_HANDLING.attributeNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.attributeNameCheck, lcName) || CUSTOM_ELEMENT_HANDLING.attributeNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.attributeNameCheck(lcName)) || // Alternative, second condition checks if it's an `is`-attribute, AND
            // the value passes whatever the user has configured for CUSTOM_ELEMENT_HANDLING.tagNameCheck
            lcName === "is" && CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements && (CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof RegExp && regExpTest(CUSTOM_ELEMENT_HANDLING.tagNameCheck, value) || CUSTOM_ELEMENT_HANDLING.tagNameCheck instanceof Function && CUSTOM_ELEMENT_HANDLING.tagNameCheck(value))
          )
            ;
          else {
            return false;
          }
        } else if (URI_SAFE_ATTRIBUTES[lcName])
          ;
        else if (regExpTest(IS_ALLOWED_URI$1, stringReplace(value, ATTR_WHITESPACE2, "")))
          ;
        else if ((lcName === "src" || lcName === "xlink:href" || lcName === "href") && lcTag !== "script" && stringIndexOf(value, "data:") === 0 && DATA_URI_TAGS[lcTag])
          ;
        else if (ALLOW_UNKNOWN_PROTOCOLS && !regExpTest(IS_SCRIPT_OR_DATA2, stringReplace(value, ATTR_WHITESPACE2, "")))
          ;
        else if (value) {
          return false;
        } else
          ;
        return true;
      };
      const _isBasicCustomElement = function _isBasicCustomElement2(tagName) {
        return tagName !== "annotation-xml" && stringMatch(tagName, CUSTOM_ELEMENT2);
      };
      const _sanitizeAttributes = function _sanitizeAttributes2(currentNode) {
        _executeHooks(hooks.beforeSanitizeAttributes, currentNode, null);
        const {
          attributes
        } = currentNode;
        if (!attributes || _isClobbered(currentNode)) {
          return;
        }
        const hookEvent = {
          attrName: "",
          attrValue: "",
          keepAttr: true,
          allowedAttributes: ALLOWED_ATTR,
          forceKeepAttr: void 0
        };
        let l = attributes.length;
        while (l--) {
          const attr = attributes[l];
          const {
            name,
            namespaceURI,
            value: attrValue
          } = attr;
          const lcName = transformCaseFunc(name);
          let value = name === "value" ? attrValue : stringTrim(attrValue);
          hookEvent.attrName = lcName;
          hookEvent.attrValue = value;
          hookEvent.keepAttr = true;
          hookEvent.forceKeepAttr = void 0;
          _executeHooks(hooks.uponSanitizeAttribute, currentNode, hookEvent);
          value = hookEvent.attrValue;
          if (SANITIZE_NAMED_PROPS && (lcName === "id" || lcName === "name")) {
            _removeAttribute(name, currentNode);
            value = SANITIZE_NAMED_PROPS_PREFIX + value;
          }
          if (SAFE_FOR_XML && regExpTest(/((--!?|])>)|<\/(style|title)/i, value)) {
            _removeAttribute(name, currentNode);
            continue;
          }
          if (hookEvent.forceKeepAttr) {
            continue;
          }
          _removeAttribute(name, currentNode);
          if (!hookEvent.keepAttr) {
            continue;
          }
          if (!ALLOW_SELF_CLOSE_IN_ATTR && regExpTest(/\/>/i, value)) {
            _removeAttribute(name, currentNode);
            continue;
          }
          if (SAFE_FOR_TEMPLATES) {
            arrayForEach([MUSTACHE_EXPR2, ERB_EXPR2, TMPLIT_EXPR2], (expr) => {
              value = stringReplace(value, expr, " ");
            });
          }
          const lcTag = transformCaseFunc(currentNode.nodeName);
          if (!_isValidAttribute(lcTag, lcName, value)) {
            continue;
          }
          if (trustedTypesPolicy && typeof trustedTypes === "object" && typeof trustedTypes.getAttributeType === "function") {
            if (namespaceURI)
              ;
            else {
              switch (trustedTypes.getAttributeType(lcTag, lcName)) {
                case "TrustedHTML": {
                  value = trustedTypesPolicy.createHTML(value);
                  break;
                }
                case "TrustedScriptURL": {
                  value = trustedTypesPolicy.createScriptURL(value);
                  break;
                }
              }
            }
          }
          try {
            if (namespaceURI) {
              currentNode.setAttributeNS(namespaceURI, name, value);
            } else {
              currentNode.setAttribute(name, value);
            }
            if (_isClobbered(currentNode)) {
              _forceRemove(currentNode);
            } else {
              arrayPop(DOMPurify.removed);
            }
          } catch (_) {
          }
        }
        _executeHooks(hooks.afterSanitizeAttributes, currentNode, null);
      };
      const _sanitizeShadowDOM = function _sanitizeShadowDOM2(fragment) {
        let shadowNode = null;
        const shadowIterator = _createNodeIterator(fragment);
        _executeHooks(hooks.beforeSanitizeShadowDOM, fragment, null);
        while (shadowNode = shadowIterator.nextNode()) {
          _executeHooks(hooks.uponSanitizeShadowNode, shadowNode, null);
          _sanitizeElements(shadowNode);
          _sanitizeAttributes(shadowNode);
          if (shadowNode.content instanceof DocumentFragment) {
            _sanitizeShadowDOM2(shadowNode.content);
          }
        }
        _executeHooks(hooks.afterSanitizeShadowDOM, fragment, null);
      };
      DOMPurify.sanitize = function(dirty) {
        let cfg = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
        let body = null;
        let importedNode = null;
        let currentNode = null;
        let returnNode = null;
        IS_EMPTY_INPUT = !dirty;
        if (IS_EMPTY_INPUT) {
          dirty = "<!-->";
        }
        if (typeof dirty !== "string" && !_isNode(dirty)) {
          if (typeof dirty.toString === "function") {
            dirty = dirty.toString();
            if (typeof dirty !== "string") {
              throw typeErrorCreate("dirty is not a string, aborting");
            }
          } else {
            throw typeErrorCreate("toString is not a function");
          }
        }
        if (!DOMPurify.isSupported) {
          return dirty;
        }
        if (!SET_CONFIG) {
          _parseConfig(cfg);
        }
        DOMPurify.removed = [];
        if (typeof dirty === "string") {
          IN_PLACE = false;
        }
        if (IN_PLACE) {
          if (dirty.nodeName) {
            const tagName = transformCaseFunc(dirty.nodeName);
            if (!ALLOWED_TAGS[tagName] || FORBID_TAGS[tagName]) {
              throw typeErrorCreate("root node is forbidden and cannot be sanitized in-place");
            }
          }
        } else if (dirty instanceof Node2) {
          body = _initDocument("<!---->");
          importedNode = body.ownerDocument.importNode(dirty, true);
          if (importedNode.nodeType === NODE_TYPE.element && importedNode.nodeName === "BODY") {
            body = importedNode;
          } else if (importedNode.nodeName === "HTML") {
            body = importedNode;
          } else {
            body.appendChild(importedNode);
          }
        } else {
          if (!RETURN_DOM && !SAFE_FOR_TEMPLATES && !WHOLE_DOCUMENT && // eslint-disable-next-line unicorn/prefer-includes
          dirty.indexOf("<") === -1) {
            return trustedTypesPolicy && RETURN_TRUSTED_TYPE ? trustedTypesPolicy.createHTML(dirty) : dirty;
          }
          body = _initDocument(dirty);
          if (!body) {
            return RETURN_DOM ? null : RETURN_TRUSTED_TYPE ? emptyHTML : "";
          }
        }
        if (body && FORCE_BODY) {
          _forceRemove(body.firstChild);
        }
        const nodeIterator = _createNodeIterator(IN_PLACE ? dirty : body);
        while (currentNode = nodeIterator.nextNode()) {
          _sanitizeElements(currentNode);
          _sanitizeAttributes(currentNode);
          if (currentNode.content instanceof DocumentFragment) {
            _sanitizeShadowDOM(currentNode.content);
          }
        }
        if (IN_PLACE) {
          return dirty;
        }
        if (RETURN_DOM) {
          if (RETURN_DOM_FRAGMENT) {
            returnNode = createDocumentFragment.call(body.ownerDocument);
            while (body.firstChild) {
              returnNode.appendChild(body.firstChild);
            }
          } else {
            returnNode = body;
          }
          if (ALLOWED_ATTR.shadowroot || ALLOWED_ATTR.shadowrootmode) {
            returnNode = importNode.call(originalDocument, returnNode, true);
          }
          return returnNode;
        }
        let serializedHTML = WHOLE_DOCUMENT ? body.outerHTML : body.innerHTML;
        if (WHOLE_DOCUMENT && ALLOWED_TAGS["!doctype"] && body.ownerDocument && body.ownerDocument.doctype && body.ownerDocument.doctype.name && regExpTest(DOCTYPE_NAME, body.ownerDocument.doctype.name)) {
          serializedHTML = "<!DOCTYPE " + body.ownerDocument.doctype.name + ">\n" + serializedHTML;
        }
        if (SAFE_FOR_TEMPLATES) {
          arrayForEach([MUSTACHE_EXPR2, ERB_EXPR2, TMPLIT_EXPR2], (expr) => {
            serializedHTML = stringReplace(serializedHTML, expr, " ");
          });
        }
        return trustedTypesPolicy && RETURN_TRUSTED_TYPE ? trustedTypesPolicy.createHTML(serializedHTML) : serializedHTML;
      };
      DOMPurify.setConfig = function() {
        let cfg = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
        _parseConfig(cfg);
        SET_CONFIG = true;
      };
      DOMPurify.clearConfig = function() {
        CONFIG = null;
        SET_CONFIG = false;
      };
      DOMPurify.isValidAttribute = function(tag, attr, value) {
        if (!CONFIG) {
          _parseConfig({});
        }
        const lcTag = transformCaseFunc(tag);
        const lcName = transformCaseFunc(attr);
        return _isValidAttribute(lcTag, lcName, value);
      };
      DOMPurify.addHook = function(entryPoint, hookFunction) {
        if (typeof hookFunction !== "function") {
          return;
        }
        arrayPush(hooks[entryPoint], hookFunction);
      };
      DOMPurify.removeHook = function(entryPoint, hookFunction) {
        if (hookFunction !== void 0) {
          const index = arrayLastIndexOf(hooks[entryPoint], hookFunction);
          return index === -1 ? void 0 : arraySplice(hooks[entryPoint], index, 1)[0];
        }
        return arrayPop(hooks[entryPoint]);
      };
      DOMPurify.removeHooks = function(entryPoint) {
        hooks[entryPoint] = [];
      };
      DOMPurify.removeAllHooks = function() {
        hooks = _createHooksMap();
      };
      return DOMPurify;
    }
    var purify2 = createDOMPurify();
    return purify2;
  });
})(purify);
function closest(element, selector) {
  if (!element) {
    return null;
  }
  if (element.matches(selector)) {
    return element;
  }
  if (element.parentNode instanceof ShadowRoot) {
    return closest(element.parentNode.host, selector);
  }
  return closest(element.parentElement, selector);
}
function buildSchemaValidationError(errors, context) {
  const message = `
  The following properties are invalid:

    ${errors.join("\n	")}

  ${context}
  `;
  return new SchemaValidationError(message);
}
var SchemaValidationError = class extends Error {
  constructor(message) {
    super(message);
    this.name = "SchemaValidationError";
  }
};
var Schema = class {
  constructor(definition) {
    this.definition = definition;
  }
  validate(values = {}, message = "") {
    const mergedValues = {
      ...this.default,
      ...values
    };
    const errors = [];
    for (const property in this.definition) {
      const error = this.definition[property].validate(mergedValues[property]);
      error && errors.push(`${property}: ${error}`);
    }
    if (errors.length) {
      throw buildSchemaValidationError(errors, message);
    }
    return mergedValues;
  }
  get default() {
    const defaultValues = {};
    for (const property in this.definition) {
      const defaultValue = this.definition[property].default;
      if (defaultValue !== void 0) {
        defaultValues[property] = defaultValue;
      }
    }
    return defaultValues;
  }
};
var Value = class {
  constructor(baseConfig = {}) {
    this.baseConfig = baseConfig;
  }
  validate(value) {
    if (this.baseConfig.required && isNullOrUndefined(value)) {
      return "value is required.";
    }
    return null;
  }
  get default() {
    return this.baseConfig.default instanceof Function ? this.baseConfig.default() : this.baseConfig.default;
  }
  get required() {
    return this.baseConfig.required === true;
  }
};
function isUndefined(value) {
  return value === void 0;
}
function isNull(value) {
  return value === null;
}
function isNullOrUndefined(value) {
  return isUndefined(value) || isNull(value);
}
var NumberValue = class {
  constructor(config = {}) {
    __publicField(this, "value");
    this.config = config;
    this.value = new Value(config);
  }
  validate(value) {
    const valueValidation = this.value.validate(value);
    if (valueValidation) {
      return valueValidation;
    }
    if (!isNumberOrUndefined(value)) {
      return "value is not a number.";
    }
    if (value < this.config.min) {
      return `minimum value of ${this.config.min} not respected.`;
    }
    if (value > this.config.max) {
      return `maximum value of ${this.config.max} not respected.`;
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
function isNumberOrUndefined(value) {
  return isUndefined(value) || isNumber(value);
}
function isNumber(value) {
  return typeof value === "number" && !isNaN(value);
}
var BooleanValue = class {
  constructor(config = {}) {
    __publicField(this, "value");
    this.value = new Value(config);
  }
  validate(value) {
    const valueValidation = this.value.validate(value);
    if (valueValidation) {
      return valueValidation;
    }
    if (!isBooleanOrUndefined(value)) {
      return "value is not a boolean.";
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
function isBooleanOrUndefined(value) {
  return isUndefined(value) || isBoolean(value);
}
function isBoolean(value) {
  return typeof value === "boolean";
}
var ISODateStringRegex = /^\d{4}(-\d\d(-\d\d(T\d\d:\d\d(:\d\d)?(\.\d+)?(([+-]\d\d:\d\d)|Z)?)?)?)?$/i;
var StringValue = class {
  constructor(config = {}) {
    __publicField(this, "value");
    __publicField(this, "config");
    this.config = {
      emptyAllowed: true,
      url: false,
      ...config
    };
    this.value = new Value(this.config);
  }
  validate(value) {
    const { emptyAllowed, url, regex, constrainTo, ISODate } = this.config;
    const valueValidation = this.value.validate(value);
    if (valueValidation) {
      return valueValidation;
    }
    if (isUndefined(value)) {
      return null;
    }
    if (!isString(value)) {
      return "value is not a string.";
    }
    if (!emptyAllowed && !value.length) {
      return "value is an empty string.";
    }
    if (url) {
      try {
        new URL(value);
      } catch (e7) {
        return "value is not a valid URL.";
      }
    }
    if (regex && !regex.test(value)) {
      return `value did not match provided regex ${regex}`;
    }
    if (constrainTo && !constrainTo.includes(value)) {
      const values = constrainTo.join(", ");
      return `value should be one of: ${values}.`;
    }
    if (ISODate && !(ISODateStringRegex.test(value) && new Date(value).toString() !== "Invalid Date")) {
      return "value is not a valid ISO8601 date string";
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
function isString(value) {
  return Object.prototype.toString.call(value) === "[object String]";
}
var RecordValue = class {
  constructor(config = {}) {
    __publicField(this, "config");
    this.config = {
      options: { required: false },
      values: {},
      ...config
    };
  }
  validate(input) {
    if (isUndefined(input)) {
      return this.config.options.required ? "value is required and is currently undefined" : null;
    }
    if (!isRecord(input)) {
      return "value is not an object";
    }
    for (const [k, v] of Object.entries(this.config.values)) {
      if (v.required && isNullOrUndefined(input[k])) {
        return `value does not contain ${k}`;
      }
    }
    let out = "";
    for (const [key, validator] of Object.entries(this.config.values)) {
      const value = input[key];
      const invalidValue = validator.validate(value);
      if (invalidValue !== null) {
        out += " " + invalidValue;
      }
    }
    return out === "" ? null : out;
  }
  get default() {
    return void 0;
  }
  get required() {
    return !!this.config.options.required;
  }
};
function isRecord(value) {
  return value !== void 0 && typeof value === "object";
}
var ArrayValue = class {
  constructor(config = {}) {
    __publicField(this, "value");
    this.config = config;
    this.value = new Value(this.config);
  }
  validate(input) {
    if (!isNullOrUndefined(input) && !Array.isArray(input)) {
      return "value is not an array";
    }
    const invalid = this.value.validate(input);
    if (invalid !== null) {
      return invalid;
    }
    if (isNullOrUndefined(input)) {
      return null;
    }
    if (this.config.max !== void 0 && input.length > this.config.max) {
      return `value contains more than ${this.config.max}`;
    }
    if (this.config.min !== void 0 && input.length < this.config.min) {
      return `value contains less than ${this.config.min}`;
    }
    if (this.config.each !== void 0) {
      let out = "";
      input.forEach((el3) => {
        if (this.config.each.required && isNullOrUndefined(el3)) {
          out = `value is null or undefined: ${input.join(",")}`;
        }
        const isInvalid = this.validatePrimitiveValue(el3, this.config.each);
        if (isInvalid !== null) {
          out += " " + isInvalid;
        }
      });
      return out === "" ? null : out;
    }
    return null;
  }
  validatePrimitiveValue(v, validator) {
    if (isBoolean(v)) {
      return validator.validate(v);
    } else if (isString(v)) {
      return validator.validate(v);
    } else if (isNumber(v)) {
      return validator.validate(v);
    } else if (isRecord(v)) {
      return validator.validate(v);
    }
    return "value is not a primitive value";
  }
  get default() {
    return void 0;
  }
  get required() {
    return this.value.required;
  }
};
function isArray(value) {
  return Array.isArray(value);
}
var EnumValue = class {
  constructor(config) {
    __publicField(this, "value");
    this.config = config;
    this.value = new Value(config);
  }
  validate(value) {
    const invalid = this.value.validate(value);
    if (invalid !== null) {
      return invalid;
    }
    if (isUndefined(value)) {
      return null;
    }
    const valueInEnum = Object.values(this.config.enum).find(
      (enumValue) => enumValue === value
    );
    if (!valueInEnum) {
      return "value is not in enum.";
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
var $b = Object.create;
var xc = Object.defineProperty;
var Gb = Object.getOwnPropertyDescriptor;
var Wb = Object.getOwnPropertyNames;
var Hb = Object.getPrototypeOf;
var zb = Object.prototype.hasOwnProperty;
var Kb = (e7, t, r) => t in e7 ? xc(e7, t, { enumerable: true, configurable: true, writable: true, value: r }) : e7[t] = r;
var Oe = (e7, t) => () => (t || e7((t = { exports: {} }).exports, t), t.exports);
var Yb = (e7, t) => {
  for (var r in t)
    xc(e7, r, { get: t[r], enumerable: true });
};
var Jb = (e7, t, r, n) => {
  if (t && typeof t == "object" || typeof t == "function")
    for (let o of Wb(t))
      !zb.call(e7, o) && o !== r && xc(e7, o, { get: () => t[o], enumerable: !(n = Gb(t, o)) || n.enumerable });
  return e7;
};
var Vt = (e7, t, r) => (r = e7 != null ? $b(Hb(e7)) : {}, Jb(xc(r, "default", { value: e7, enumerable: true }), e7));
var Ce = (e7, t, r) => Kb(e7, typeof t != "symbol" ? t + "" : t, r);
var iS = Oe((Ki) => {
  var Pc = Ki && Ki.__assign || function() {
    return Pc = Object.assign || function(e7) {
      for (var t, r = 1, n = arguments.length; r < n; r++) {
        t = arguments[r];
        for (var o in t)
          Object.prototype.hasOwnProperty.call(t, o) && (e7[o] = t[o]);
      }
      return e7;
    }, Pc.apply(this, arguments);
  };
  Object.defineProperty(Ki, "__esModule", { value: true });
  var uv = { delayFirstAttempt: false, jitter: "none", maxDelay: 1 / 0, numOfAttempts: 10, retry: function() {
    return true;
  }, startingDelay: 100, timeMultiple: 2 };
  function lv(e7) {
    var t = Pc(Pc({}, uv), e7);
    return t.numOfAttempts < 1 && (t.numOfAttempts = 1), t;
  }
  Ki.getSanitizedOptions = lv;
});
var sS = Oe((kp2) => {
  Object.defineProperty(kp2, "__esModule", { value: true });
  function dv(e7) {
    var t = Math.random() * e7;
    return Math.round(t);
  }
  kp2.fullJitter = dv;
});
var cS = Oe((Op) => {
  Object.defineProperty(Op, "__esModule", { value: true });
  function pv(e7) {
    return e7;
  }
  Op.noJitter = pv;
});
var uS = Oe((qp) => {
  Object.defineProperty(qp, "__esModule", { value: true });
  var mv = sS(), fv = cS();
  function gv(e7) {
    switch (e7.jitter) {
      case "full":
        return mv.fullJitter;
      case "none":
      default:
        return fv.noJitter;
    }
  }
  qp.JitterFactory = gv;
});
var Vp = Oe((Dp) => {
  Object.defineProperty(Dp, "__esModule", { value: true });
  var Sv = uS(), hv = function() {
    function e7(t) {
      this.options = t, this.attempt = 0;
    }
    return e7.prototype.apply = function() {
      var t = this;
      return new Promise(function(r) {
        return setTimeout(r, t.jitteredDelay);
      });
    }, e7.prototype.setAttemptNumber = function(t) {
      this.attempt = t;
    }, Object.defineProperty(e7.prototype, "jitteredDelay", { get: function() {
      var t = Sv.JitterFactory(this.options);
      return t(this.delay);
    }, enumerable: true, configurable: true }), Object.defineProperty(e7.prototype, "delay", { get: function() {
      var t = this.options.startingDelay, r = this.options.timeMultiple, n = this.numOfDelayedAttempts, o = t * Math.pow(r, n);
      return Math.min(o, this.options.maxDelay);
    }, enumerable: true, configurable: true }), Object.defineProperty(e7.prototype, "numOfDelayedAttempts", { get: function() {
      return this.attempt;
    }, enumerable: true, configurable: true }), e7;
  }();
  Dp.Delay = hv;
});
var lS = Oe((Fr) => {
  var yv = Fr && Fr.__extends || function() {
    var e7 = function(t, r) {
      return e7 = Object.setPrototypeOf || { __proto__: [] } instanceof Array && function(n, o) {
        n.__proto__ = o;
      } || function(n, o) {
        for (var a in o)
          o.hasOwnProperty(a) && (n[a] = o[a]);
      }, e7(t, r);
    };
    return function(t, r) {
      e7(t, r);
      function n() {
        this.constructor = t;
      }
      t.prototype = r === null ? Object.create(r) : (n.prototype = r.prototype, new n());
    };
  }(), Cv = Fr && Fr.__awaiter || function(e7, t, r, n) {
    function o(a) {
      return a instanceof r ? a : new r(function(i) {
        i(a);
      });
    }
    return new (r || (r = Promise))(function(a, i) {
      function s(l) {
        try {
          u(n.next(l));
        } catch (m) {
          i(m);
        }
      }
      function c(l) {
        try {
          u(n.throw(l));
        } catch (m) {
          i(m);
        }
      }
      function u(l) {
        l.done ? a(l.value) : o(l.value).then(s, c);
      }
      u((n = n.apply(e7, t || [])).next());
    });
  }, xv = Fr && Fr.__generator || function(e7, t) {
    var r = { label: 0, sent: function() {
      if (a[0] & 1)
        throw a[1];
      return a[1];
    }, trys: [], ops: [] }, n, o, a, i;
    return i = { next: s(0), throw: s(1), return: s(2) }, typeof Symbol == "function" && (i[Symbol.iterator] = function() {
      return this;
    }), i;
    function s(u) {
      return function(l) {
        return c([u, l]);
      };
    }
    function c(u) {
      if (n)
        throw new TypeError("Generator is already executing.");
      for (; r; )
        try {
          if (n = 1, o && (a = u[0] & 2 ? o.return : u[0] ? o.throw || ((a = o.return) && a.call(o), 0) : o.next) && !(a = a.call(o, u[1])).done)
            return a;
          switch (o = 0, a && (u = [u[0] & 2, a.value]), u[0]) {
            case 0:
            case 1:
              a = u;
              break;
            case 4:
              return r.label++, { value: u[1], done: false };
            case 5:
              r.label++, o = u[1], u = [0];
              continue;
            case 7:
              u = r.ops.pop(), r.trys.pop();
              continue;
            default:
              if (a = r.trys, !(a = a.length > 0 && a[a.length - 1]) && (u[0] === 6 || u[0] === 2)) {
                r = 0;
                continue;
              }
              if (u[0] === 3 && (!a || u[1] > a[0] && u[1] < a[3])) {
                r.label = u[1];
                break;
              }
              if (u[0] === 6 && r.label < a[1]) {
                r.label = a[1], a = u;
                break;
              }
              if (a && r.label < a[2]) {
                r.label = a[2], r.ops.push(u);
                break;
              }
              a[2] && r.ops.pop(), r.trys.pop();
              continue;
          }
          u = t.call(e7, r);
        } catch (l) {
          u = [6, l], o = 0;
        } finally {
          n = a = 0;
        }
      if (u[0] & 5)
        throw u[1];
      return { value: u[0] ? u[1] : void 0, done: true };
    }
  };
  Object.defineProperty(Fr, "__esModule", { value: true });
  var Av = Vp(), Fv = function(e7) {
    yv(t, e7);
    function t() {
      return e7 !== null && e7.apply(this, arguments) || this;
    }
    return t.prototype.apply = function() {
      return Cv(this, void 0, void 0, function() {
        return xv(this, function(r) {
          return [2, this.isFirstAttempt ? true : e7.prototype.apply.call(this)];
        });
      });
    }, Object.defineProperty(t.prototype, "isFirstAttempt", { get: function() {
      return this.attempt === 0;
    }, enumerable: true, configurable: true }), Object.defineProperty(t.prototype, "numOfDelayedAttempts", { get: function() {
      return this.attempt - 1;
    }, enumerable: true, configurable: true }), t;
  }(Av.Delay);
  Fr.SkipFirstDelay = Fv;
});
var dS = Oe((Yi) => {
  var Rv = Yi && Yi.__extends || function() {
    var e7 = function(t, r) {
      return e7 = Object.setPrototypeOf || { __proto__: [] } instanceof Array && function(n, o) {
        n.__proto__ = o;
      } || function(n, o) {
        for (var a in o)
          o.hasOwnProperty(a) && (n[a] = o[a]);
      }, e7(t, r);
    };
    return function(t, r) {
      e7(t, r);
      function n() {
        this.constructor = t;
      }
      t.prototype = r === null ? Object.create(r) : (n.prototype = r.prototype, new n());
    };
  }();
  Object.defineProperty(Yi, "__esModule", { value: true });
  var bv = Vp(), vv = function(e7) {
    Rv(t, e7);
    function t() {
      return e7 !== null && e7.apply(this, arguments) || this;
    }
    return t;
  }(bv.Delay);
  Yi.AlwaysDelay = vv;
});
var pS = Oe((Np2) => {
  Object.defineProperty(Np2, "__esModule", { value: true });
  var Pv = lS(), wv = dS();
  function Iv(e7, t) {
    var r = Ev(e7);
    return r.setAttemptNumber(t), r;
  }
  Np2.DelayFactory = Iv;
  function Ev(e7) {
    return e7.delayFirstAttempt ? new wv.AlwaysDelay(e7) : new Pv.SkipFirstDelay(e7);
  }
});
var mS = Oe((jn) => {
  var Mp = jn && jn.__awaiter || function(e7, t, r, n) {
    function o(a) {
      return a instanceof r ? a : new r(function(i) {
        i(a);
      });
    }
    return new (r || (r = Promise))(function(a, i) {
      function s(l) {
        try {
          u(n.next(l));
        } catch (m) {
          i(m);
        }
      }
      function c(l) {
        try {
          u(n.throw(l));
        } catch (m) {
          i(m);
        }
      }
      function u(l) {
        l.done ? a(l.value) : o(l.value).then(s, c);
      }
      u((n = n.apply(e7, t || [])).next());
    });
  }, Qp = jn && jn.__generator || function(e7, t) {
    var r = { label: 0, sent: function() {
      if (a[0] & 1)
        throw a[1];
      return a[1];
    }, trys: [], ops: [] }, n, o, a, i;
    return i = { next: s(0), throw: s(1), return: s(2) }, typeof Symbol == "function" && (i[Symbol.iterator] = function() {
      return this;
    }), i;
    function s(u) {
      return function(l) {
        return c([u, l]);
      };
    }
    function c(u) {
      if (n)
        throw new TypeError("Generator is already executing.");
      for (; r; )
        try {
          if (n = 1, o && (a = u[0] & 2 ? o.return : u[0] ? o.throw || ((a = o.return) && a.call(o), 0) : o.next) && !(a = a.call(o, u[1])).done)
            return a;
          switch (o = 0, a && (u = [u[0] & 2, a.value]), u[0]) {
            case 0:
            case 1:
              a = u;
              break;
            case 4:
              return r.label++, { value: u[1], done: false };
            case 5:
              r.label++, o = u[1], u = [0];
              continue;
            case 7:
              u = r.ops.pop(), r.trys.pop();
              continue;
            default:
              if (a = r.trys, !(a = a.length > 0 && a[a.length - 1]) && (u[0] === 6 || u[0] === 2)) {
                r = 0;
                continue;
              }
              if (u[0] === 3 && (!a || u[1] > a[0] && u[1] < a[3])) {
                r.label = u[1];
                break;
              }
              if (u[0] === 6 && r.label < a[1]) {
                r.label = a[1], a = u;
                break;
              }
              if (a && r.label < a[2]) {
                r.label = a[2], r.ops.push(u);
                break;
              }
              a[2] && r.ops.pop(), r.trys.pop();
              continue;
          }
          u = t.call(e7, r);
        } catch (l) {
          u = [6, l], o = 0;
        } finally {
          n = a = 0;
        }
      if (u[0] & 5)
        throw u[1];
      return { value: u[0] ? u[1] : void 0, done: true };
    }
  };
  Object.defineProperty(jn, "__esModule", { value: true });
  var Tv = iS(), kv = pS();
  function Ov(e7, t) {
    return t === void 0 && (t = {}), Mp(this, void 0, void 0, function() {
      var r, n;
      return Qp(this, function(o) {
        switch (o.label) {
          case 0:
            return r = Tv.getSanitizedOptions(t), n = new qv(e7, r), [4, n.execute()];
          case 1:
            return [2, o.sent()];
        }
      });
    });
  }
  jn.backOff = Ov;
  var qv = function() {
    function e7(t, r) {
      this.request = t, this.options = r, this.attemptNumber = 0;
    }
    return e7.prototype.execute = function() {
      return Mp(this, void 0, void 0, function() {
        var t, r;
        return Qp(this, function(n) {
          switch (n.label) {
            case 0:
              if (this.attemptLimitReached)
                return [3, 7];
              n.label = 1;
            case 1:
              return n.trys.push([1, 4, , 6]), [4, this.applyDelay()];
            case 2:
              return n.sent(), [4, this.request()];
            case 3:
              return [2, n.sent()];
            case 4:
              return t = n.sent(), this.attemptNumber++, [4, this.options.retry(t, this.attemptNumber)];
            case 5:
              if (r = n.sent(), !r || this.attemptLimitReached)
                throw t;
              return [3, 6];
            case 6:
              return [3, 0];
            case 7:
              throw new Error("Something went wrong.");
          }
        });
      });
    }, Object.defineProperty(e7.prototype, "attemptLimitReached", { get: function() {
      return this.attemptNumber >= this.options.numOfAttempts;
    }, enumerable: true, configurable: true }), e7.prototype.applyDelay = function() {
      return Mp(this, void 0, void 0, function() {
        var t;
        return Qp(this, function(r) {
          switch (r.label) {
            case 0:
              return t = kv.DelayFactory(this.options, this.attemptNumber), [4, t.apply()];
            case 1:
              return r.sent(), [2];
          }
        });
      });
    }, e7;
  }();
});
var gu = Oe((Um2, _m) => {
  (function(e7, t) {
    typeof Um2 == "object" && typeof _m < "u" ? _m.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs = t();
  })(Um2, function() {
    var e7 = 1e3, t = 6e4, r = 36e5, n = "millisecond", o = "second", a = "minute", i = "hour", s = "day", c = "week", u = "month", l = "quarter", m = "year", p = "date", d = "Invalid Date", f = /^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/, x2 = /\[([^\]]+)]|Y{1,4}|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g, S = { name: "en", weekdays: "Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_"), months: "January_February_March_April_May_June_July_August_September_October_November_December".split("_"), ordinal: function(D) {
      var O = ["th", "st", "nd", "rd"], k = D % 100;
      return "[" + D + (O[(k - 20) % 10] || O[k] || O[0]) + "]";
    } }, g = function(D, O, k) {
      var Q = String(D);
      return !Q || Q.length >= O ? D : "" + Array(O + 1 - Q.length).join(k) + D;
    }, C = { s: g, z: function(D) {
      var O = -D.utcOffset(), k = Math.abs(O), Q = Math.floor(k / 60), q = k % 60;
      return (O <= 0 ? "+" : "-") + g(Q, 2, "0") + ":" + g(q, 2, "0");
    }, m: function D(O, k) {
      if (O.date() < k.date())
        return -D(k, O);
      var Q = 12 * (k.year() - O.year()) + (k.month() - O.month()), q = O.clone().add(Q, u), U = k - q < 0, _ = O.clone().add(Q + (U ? -1 : 1), u);
      return +(-(Q + (k - q) / (U ? q - _ : _ - q)) || 0);
    }, a: function(D) {
      return D < 0 ? Math.ceil(D) || 0 : Math.floor(D);
    }, p: function(D) {
      return { M: u, y: m, w: c, d: s, D: p, h: i, m: a, s: o, ms: n, Q: l }[D] || String(D || "").toLowerCase().replace(/s$/, "");
    }, u: function(D) {
      return D === void 0;
    } }, y = "en", A = {};
    A[y] = S;
    var I = "$isDayjsObject", v = function(D) {
      return D instanceof T || !(!D || !D[I]);
    }, R = function D(O, k, Q) {
      var q;
      if (!O)
        return y;
      if (typeof O == "string") {
        var U = O.toLowerCase();
        A[U] && (q = U), k && (A[U] = k, q = U);
        var _ = O.split("-");
        if (!q && _.length > 1)
          return D(_[0]);
      } else {
        var H2 = O.name;
        A[H2] = O, q = H2;
      }
      return !Q && q && (y = q), q || !Q && y;
    }, b = function(D, O) {
      if (v(D))
        return D.clone();
      var k = typeof O == "object" ? O : {};
      return k.date = D, k.args = arguments, new T(k);
    }, P = C;
    P.l = R, P.i = v, P.w = function(D, O) {
      return b(D, { locale: O.$L, utc: O.$u, x: O.$x, $offset: O.$offset });
    };
    var T = function() {
      function D(k) {
        this.$L = R(k.locale, null, true), this.parse(k), this.$x = this.$x || k.x || {}, this[I] = true;
      }
      var O = D.prototype;
      return O.parse = function(k) {
        this.$d = function(Q) {
          var q = Q.date, U = Q.utc;
          if (q === null)
            return /* @__PURE__ */ new Date(NaN);
          if (P.u(q))
            return /* @__PURE__ */ new Date();
          if (q instanceof Date)
            return new Date(q);
          if (typeof q == "string" && !/Z$/i.test(q)) {
            var _ = q.match(f);
            if (_) {
              var H2 = _[2] - 1 || 0, ee = (_[7] || "0").substring(0, 3);
              return U ? new Date(Date.UTC(_[1], H2, _[3] || 1, _[4] || 0, _[5] || 0, _[6] || 0, ee)) : new Date(_[1], H2, _[3] || 1, _[4] || 0, _[5] || 0, _[6] || 0, ee);
            }
          }
          return new Date(q);
        }(k), this.init();
      }, O.init = function() {
        var k = this.$d;
        this.$y = k.getFullYear(), this.$M = k.getMonth(), this.$D = k.getDate(), this.$W = k.getDay(), this.$H = k.getHours(), this.$m = k.getMinutes(), this.$s = k.getSeconds(), this.$ms = k.getMilliseconds();
      }, O.$utils = function() {
        return P;
      }, O.isValid = function() {
        return this.$d.toString() !== d;
      }, O.isSame = function(k, Q) {
        var q = b(k);
        return this.startOf(Q) <= q && q <= this.endOf(Q);
      }, O.isAfter = function(k, Q) {
        return b(k) < this.startOf(Q);
      }, O.isBefore = function(k, Q) {
        return this.endOf(Q) < b(k);
      }, O.$g = function(k, Q, q) {
        return P.u(k) ? this[Q] : this.set(q, k);
      }, O.unix = function() {
        return Math.floor(this.valueOf() / 1e3);
      }, O.valueOf = function() {
        return this.$d.getTime();
      }, O.startOf = function(k, Q) {
        var q = this, U = !!P.u(Q) || Q, _ = P.p(k), H2 = function(se2, fe) {
          var ye = P.w(q.$u ? Date.UTC(q.$y, fe, se2) : new Date(q.$y, fe, se2), q);
          return U ? ye : ye.endOf(s);
        }, ee = function(se2, fe) {
          return P.w(q.toDate()[se2].apply(q.toDate("s"), (U ? [0, 0, 0, 0] : [23, 59, 59, 999]).slice(fe)), q);
        }, oe = this.$W, X = this.$M, te = this.$D, J = "set" + (this.$u ? "UTC" : "");
        switch (_) {
          case m:
            return U ? H2(1, 0) : H2(31, 11);
          case u:
            return U ? H2(1, X) : H2(0, X + 1);
          case c:
            var re = this.$locale().weekStart || 0, ge = (oe < re ? oe + 7 : oe) - re;
            return H2(U ? te - ge : te + (6 - ge), X);
          case s:
          case p:
            return ee(J + "Hours", 0);
          case i:
            return ee(J + "Minutes", 1);
          case a:
            return ee(J + "Seconds", 2);
          case o:
            return ee(J + "Milliseconds", 3);
          default:
            return this.clone();
        }
      }, O.endOf = function(k) {
        return this.startOf(k, false);
      }, O.$set = function(k, Q) {
        var q, U = P.p(k), _ = "set" + (this.$u ? "UTC" : ""), H2 = (q = {}, q[s] = _ + "Date", q[p] = _ + "Date", q[u] = _ + "Month", q[m] = _ + "FullYear", q[i] = _ + "Hours", q[a] = _ + "Minutes", q[o] = _ + "Seconds", q[n] = _ + "Milliseconds", q)[U], ee = U === s ? this.$D + (Q - this.$W) : Q;
        if (U === u || U === m) {
          var oe = this.clone().set(p, 1);
          oe.$d[H2](ee), oe.init(), this.$d = oe.set(p, Math.min(this.$D, oe.daysInMonth())).$d;
        } else
          H2 && this.$d[H2](ee);
        return this.init(), this;
      }, O.set = function(k, Q) {
        return this.clone().$set(k, Q);
      }, O.get = function(k) {
        return this[P.p(k)]();
      }, O.add = function(k, Q) {
        var q, U = this;
        k = Number(k);
        var _ = P.p(Q), H2 = function(X) {
          var te = b(U);
          return P.w(te.date(te.date() + Math.round(X * k)), U);
        };
        if (_ === u)
          return this.set(u, this.$M + k);
        if (_ === m)
          return this.set(m, this.$y + k);
        if (_ === s)
          return H2(1);
        if (_ === c)
          return H2(7);
        var ee = (q = {}, q[a] = t, q[i] = r, q[o] = e7, q)[_] || 1, oe = this.$d.getTime() + k * ee;
        return P.w(oe, this);
      }, O.subtract = function(k, Q) {
        return this.add(-1 * k, Q);
      }, O.format = function(k) {
        var Q = this, q = this.$locale();
        if (!this.isValid())
          return q.invalidDate || d;
        var U = k || "YYYY-MM-DDTHH:mm:ssZ", _ = P.z(this), H2 = this.$H, ee = this.$m, oe = this.$M, X = q.weekdays, te = q.months, J = q.meridiem, re = function(fe, ye, Ge, it) {
          return fe && (fe[ye] || fe(Q, U)) || Ge[ye].slice(0, it);
        }, ge = function(fe) {
          return P.s(H2 % 12 || 12, fe, "0");
        }, se2 = J || function(fe, ye, Ge) {
          var it = fe < 12 ? "AM" : "PM";
          return Ge ? it.toLowerCase() : it;
        };
        return U.replace(x2, function(fe, ye) {
          return ye || function(Ge) {
            switch (Ge) {
              case "YY":
                return String(Q.$y).slice(-2);
              case "YYYY":
                return P.s(Q.$y, 4, "0");
              case "M":
                return oe + 1;
              case "MM":
                return P.s(oe + 1, 2, "0");
              case "MMM":
                return re(q.monthsShort, oe, te, 3);
              case "MMMM":
                return re(te, oe);
              case "D":
                return Q.$D;
              case "DD":
                return P.s(Q.$D, 2, "0");
              case "d":
                return String(Q.$W);
              case "dd":
                return re(q.weekdaysMin, Q.$W, X, 2);
              case "ddd":
                return re(q.weekdaysShort, Q.$W, X, 3);
              case "dddd":
                return X[Q.$W];
              case "H":
                return String(H2);
              case "HH":
                return P.s(H2, 2, "0");
              case "h":
                return ge(1);
              case "hh":
                return ge(2);
              case "a":
                return se2(H2, ee, true);
              case "A":
                return se2(H2, ee, false);
              case "m":
                return String(ee);
              case "mm":
                return P.s(ee, 2, "0");
              case "s":
                return String(Q.$s);
              case "ss":
                return P.s(Q.$s, 2, "0");
              case "SSS":
                return P.s(Q.$ms, 3, "0");
              case "Z":
                return _;
            }
            return null;
          }(fe) || _.replace(":", "");
        });
      }, O.utcOffset = function() {
        return 15 * -Math.round(this.$d.getTimezoneOffset() / 15);
      }, O.diff = function(k, Q, q) {
        var U, _ = this, H2 = P.p(Q), ee = b(k), oe = (ee.utcOffset() - this.utcOffset()) * t, X = this - ee, te = function() {
          return P.m(_, ee);
        };
        switch (H2) {
          case m:
            U = te() / 12;
            break;
          case u:
            U = te();
            break;
          case l:
            U = te() / 3;
            break;
          case c:
            U = (X - oe) / 6048e5;
            break;
          case s:
            U = (X - oe) / 864e5;
            break;
          case i:
            U = X / r;
            break;
          case a:
            U = X / t;
            break;
          case o:
            U = X / e7;
            break;
          default:
            U = X;
        }
        return q ? U : P.a(U);
      }, O.daysInMonth = function() {
        return this.endOf(u).$D;
      }, O.$locale = function() {
        return A[this.$L];
      }, O.locale = function(k, Q) {
        if (!k)
          return this.$L;
        var q = this.clone(), U = R(k, Q, true);
        return U && (q.$L = U), q;
      }, O.clone = function() {
        return P.w(this.$d, this);
      }, O.toDate = function() {
        return new Date(this.valueOf());
      }, O.toJSON = function() {
        return this.isValid() ? this.toISOString() : null;
      }, O.toISOString = function() {
        return this.$d.toISOString();
      }, O.toString = function() {
        return this.$d.toUTCString();
      }, D;
    }(), B = T.prototype;
    return b.prototype = B, [["$ms", n], ["$s", o], ["$m", a], ["$H", i], ["$W", s], ["$M", u], ["$y", m], ["$D", p]].forEach(function(D) {
      B[D[1]] = function(O) {
        return this.$g(O, D[0], D[1]);
      };
    }), b.extend = function(D, O) {
      return D.$i || (D(O, T, b), D.$i = true), b;
    }, b.locale = R, b.isDayjs = v, b.unix = function(D) {
      return b(1e3 * D);
    }, b.en = A[y], b.Ls = A, b.p = {}, b;
  });
});
var Ay = Oe((jm, $m) => {
  (function(e7, t) {
    typeof jm == "object" && typeof $m < "u" ? $m.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_quarterOfYear = t();
  })(jm, function() {
    var e7 = "month", t = "quarter";
    return function(r, n) {
      var o = n.prototype;
      o.quarter = function(s) {
        return this.$utils().u(s) ? Math.ceil((this.month() + 1) / 3) : this.month(this.month() % 3 + 3 * (s - 1));
      };
      var a = o.add;
      o.add = function(s, c) {
        return s = Number(s), this.$utils().p(c) === t ? this.add(3 * s, e7) : a.bind(this)(s, c);
      };
      var i = o.startOf;
      o.startOf = function(s, c) {
        var u = this.$utils(), l = !!u.u(c) || c;
        if (u.p(s) === t) {
          var m = this.quarter() - 1;
          return l ? this.month(3 * m).startOf(e7).startOf("day") : this.month(3 * m + 2).endOf(e7).endOf("day");
        }
        return i.bind(this)(s, c);
      };
    };
  });
});
var Fy = Oe((Gm, Wm) => {
  (function(e7, t) {
    typeof Gm == "object" && typeof Wm < "u" ? Wm.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_customParseFormat = t();
  })(Gm, function() {
    var e7 = { LTS: "h:mm:ss A", LT: "h:mm A", L: "MM/DD/YYYY", LL: "MMMM D, YYYY", LLL: "MMMM D, YYYY h:mm A", LLLL: "dddd, MMMM D, YYYY h:mm A" }, t = /(\[[^[]*\])|([-_:/.,()\s]+)|(A|a|Q|YYYY|YY?|ww?|MM?M?M?|Do|DD?|hh?|HH?|mm?|ss?|S{1,3}|z|ZZ?)/g, r = /\d/, n = /\d\d/, o = /\d\d?/, a = /\d*[^-_:/,()\s\d]+/, i = {}, s = function(f) {
      return (f = +f) + (f > 68 ? 1900 : 2e3);
    }, c = function(f) {
      return function(x2) {
        this[f] = +x2;
      };
    }, u = [/[+-]\d\d:?(\d\d)?|Z/, function(f) {
      (this.zone || (this.zone = {})).offset = function(x2) {
        if (!x2 || x2 === "Z")
          return 0;
        var S = x2.match(/([+-]|\d\d)/g), g = 60 * S[1] + (+S[2] || 0);
        return g === 0 ? 0 : S[0] === "+" ? -g : g;
      }(f);
    }], l = function(f) {
      var x2 = i[f];
      return x2 && (x2.indexOf ? x2 : x2.s.concat(x2.f));
    }, m = function(f, x2) {
      var S, g = i.meridiem;
      if (g) {
        for (var C = 1; C <= 24; C += 1)
          if (f.indexOf(g(C, 0, x2)) > -1) {
            S = C > 12;
            break;
          }
      } else
        S = f === (x2 ? "pm" : "PM");
      return S;
    }, p = { A: [a, function(f) {
      this.afternoon = m(f, false);
    }], a: [a, function(f) {
      this.afternoon = m(f, true);
    }], Q: [r, function(f) {
      this.month = 3 * (f - 1) + 1;
    }], S: [r, function(f) {
      this.milliseconds = 100 * +f;
    }], SS: [n, function(f) {
      this.milliseconds = 10 * +f;
    }], SSS: [/\d{3}/, function(f) {
      this.milliseconds = +f;
    }], s: [o, c("seconds")], ss: [o, c("seconds")], m: [o, c("minutes")], mm: [o, c("minutes")], H: [o, c("hours")], h: [o, c("hours")], HH: [o, c("hours")], hh: [o, c("hours")], D: [o, c("day")], DD: [n, c("day")], Do: [a, function(f) {
      var x2 = i.ordinal, S = f.match(/\d+/);
      if (this.day = S[0], x2)
        for (var g = 1; g <= 31; g += 1)
          x2(g).replace(/\[|\]/g, "") === f && (this.day = g);
    }], w: [o, c("week")], ww: [n, c("week")], M: [o, c("month")], MM: [n, c("month")], MMM: [a, function(f) {
      var x2 = l("months"), S = (l("monthsShort") || x2.map(function(g) {
        return g.slice(0, 3);
      })).indexOf(f) + 1;
      if (S < 1)
        throw new Error();
      this.month = S % 12 || S;
    }], MMMM: [a, function(f) {
      var x2 = l("months").indexOf(f) + 1;
      if (x2 < 1)
        throw new Error();
      this.month = x2 % 12 || x2;
    }], Y: [/[+-]?\d+/, c("year")], YY: [n, function(f) {
      this.year = s(f);
    }], YYYY: [/\d{4}/, c("year")], Z: u, ZZ: u };
    function d(f) {
      var x2, S;
      x2 = f, S = i && i.formats;
      for (var g = (f = x2.replace(/(\[[^\]]+])|(LTS?|l{1,4}|L{1,4})/g, function(b, P, T) {
        var B = T && T.toUpperCase();
        return P || S[T] || e7[T] || S[B].replace(/(\[[^\]]+])|(MMMM|MM|DD|dddd)/g, function(D, O, k) {
          return O || k.slice(1);
        });
      })).match(t), C = g.length, y = 0; y < C; y += 1) {
        var A = g[y], I = p[A], v = I && I[0], R = I && I[1];
        g[y] = R ? { regex: v, parser: R } : A.replace(/^\[|\]$/g, "");
      }
      return function(b) {
        for (var P = {}, T = 0, B = 0; T < C; T += 1) {
          var D = g[T];
          if (typeof D == "string")
            B += D.length;
          else {
            var O = D.regex, k = D.parser, Q = b.slice(B), q = O.exec(Q)[0];
            k.call(P, q), b = b.replace(q, "");
          }
        }
        return function(U) {
          var _ = U.afternoon;
          if (_ !== void 0) {
            var H2 = U.hours;
            _ ? H2 < 12 && (U.hours += 12) : H2 === 12 && (U.hours = 0), delete U.afternoon;
          }
        }(P), P;
      };
    }
    return function(f, x2, S) {
      S.p.customParseFormat = true, f && f.parseTwoDigitYear && (s = f.parseTwoDigitYear);
      var g = x2.prototype, C = g.parse;
      g.parse = function(y) {
        var A = y.date, I = y.utc, v = y.args;
        this.$u = I;
        var R = v[1];
        if (typeof R == "string") {
          var b = v[2] === true, P = v[3] === true, T = b || P, B = v[2];
          P && (B = v[2]), i = this.$locale(), !b && B && (i = S.Ls[B]), this.$d = function(Q, q, U, _) {
            try {
              if (["x", "X"].indexOf(q) > -1)
                return new Date((q === "X" ? 1e3 : 1) * Q);
              var H2 = d(q)(Q), ee = H2.year, oe = H2.month, X = H2.day, te = H2.hours, J = H2.minutes, re = H2.seconds, ge = H2.milliseconds, se2 = H2.zone, fe = H2.week, ye = /* @__PURE__ */ new Date(), Ge = X || (ee || oe ? 1 : ye.getDate()), it = ee || ye.getFullYear(), Ur = 0;
              ee && !oe || (Ur = oe > 0 ? oe - 1 : ye.getMonth());
              var Io2, Eo = te || 0, Wi = J || 0, Rp2 = re || 0, bp = ge || 0;
              return se2 ? new Date(Date.UTC(it, Ur, Ge, Eo, Wi, Rp2, bp + 60 * se2.offset * 1e3)) : U ? new Date(Date.UTC(it, Ur, Ge, Eo, Wi, Rp2, bp)) : (Io2 = new Date(it, Ur, Ge, Eo, Wi, Rp2, bp), fe && (Io2 = _(Io2).week(fe).toDate()), Io2);
            } catch {
              return /* @__PURE__ */ new Date("");
            }
          }(A, R, I, S), this.init(), B && B !== true && (this.$L = this.locale(B).$L), T && A != this.format(R) && (this.$d = /* @__PURE__ */ new Date("")), i = {};
        } else if (R instanceof Array)
          for (var D = R.length, O = 1; O <= D; O += 1) {
            v[1] = R[O - 1];
            var k = S.apply(this, v);
            if (k.isValid()) {
              this.$d = k.$d, this.$L = k.$L, this.init();
              break;
            }
            O === D && (this.$d = /* @__PURE__ */ new Date(""));
          }
        else
          C.call(this, y);
      };
    };
  });
});
var NC = Oe((oz, VC) => {
  var vk = /(^|; )Coveo-Pendragon=([^;]*)/;
  VC.exports = () => vk.exec(document.cookie)?.pop() || null;
});
var MC = Oe((xf, Af) => {
  (function(e7, t) {
    typeof xf == "object" && typeof Af < "u" ? Af.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_timezone = t();
  })(xf, function() {
    var e7 = { year: 0, month: 1, day: 2, hour: 3, minute: 4, second: 5 }, t = {};
    return function(r, n, o) {
      var a, i = function(l, m, p) {
        p === void 0 && (p = {});
        var d = new Date(l), f = function(x2, S) {
          S === void 0 && (S = {});
          var g = S.timeZoneName || "short", C = x2 + "|" + g, y = t[C];
          return y || (y = new Intl.DateTimeFormat("en-US", { hour12: false, timeZone: x2, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZoneName: g }), t[C] = y), y;
        }(m, p);
        return f.formatToParts(d);
      }, s = function(l, m) {
        for (var p = i(l, m), d = [], f = 0; f < p.length; f += 1) {
          var x2 = p[f], S = x2.type, g = x2.value, C = e7[S];
          C >= 0 && (d[C] = parseInt(g, 10));
        }
        var y = d[3], A = y === 24 ? 0 : y, I = d[0] + "-" + d[1] + "-" + d[2] + " " + A + ":" + d[4] + ":" + d[5] + ":000", v = +l;
        return (o.utc(I).valueOf() - (v -= v % 1e3)) / 6e4;
      }, c = n.prototype;
      c.tz = function(l, m) {
        l === void 0 && (l = a);
        var p, d = this.utcOffset(), f = this.toDate(), x2 = f.toLocaleString("en-US", { timeZone: l }), S = Math.round((f - new Date(x2)) / 1e3 / 60), g = 15 * -Math.round(f.getTimezoneOffset() / 15) - S;
        if (!Number(g))
          p = this.utcOffset(0, m);
        else if (p = o(x2, { locale: this.$L }).$set("millisecond", this.$ms).utcOffset(g, true), m) {
          var C = p.utcOffset();
          p = p.add(d - C, "minute");
        }
        return p.$x.$timezone = l, p;
      }, c.offsetName = function(l) {
        var m = this.$x.$timezone || o.tz.guess(), p = i(this.valueOf(), m, { timeZoneName: l }).find(function(d) {
          return d.type.toLowerCase() === "timezonename";
        });
        return p && p.value;
      };
      var u = c.startOf;
      c.startOf = function(l, m) {
        if (!this.$x || !this.$x.$timezone)
          return u.call(this, l, m);
        var p = o(this.format("YYYY-MM-DD HH:mm:ss:SSS"), { locale: this.$L });
        return u.call(p, l, m).tz(this.$x.$timezone, true);
      }, o.tz = function(l, m, p) {
        var d = p && m, f = p || m || a, x2 = s(+o(), f);
        if (typeof l != "string")
          return o(l).tz(f);
        var S = function(A, I, v) {
          var R = A - 60 * I * 1e3, b = s(R, v);
          if (I === b)
            return [R, I];
          var P = s(R -= 60 * (b - I) * 1e3, v);
          return b === P ? [R, b] : [A - 60 * Math.min(b, P) * 1e3, Math.max(b, P)];
        }(o.utc(l, d).valueOf(), x2, f), g = S[0], C = S[1], y = o(g).utcOffset(C);
        return y.$x.$timezone = f, y;
      }, o.tz.guess = function() {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
      }, o.tz.setDefault = function(l) {
        a = l;
      };
    };
  });
});
var QC = Oe((Ff, Rf) => {
  (function(e7, t) {
    typeof Ff == "object" && typeof Rf < "u" ? Rf.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_utc = t();
  })(Ff, function() {
    var e7 = "minute", t = /[+-]\d\d(?::?\d\d)?/g, r = /([+-]|\d\d)/g;
    return function(n, o, a) {
      var i = o.prototype;
      a.utc = function(d) {
        var f = { date: d, utc: true, args: arguments };
        return new o(f);
      }, i.utc = function(d) {
        var f = a(this.toDate(), { locale: this.$L, utc: true });
        return d ? f.add(this.utcOffset(), e7) : f;
      }, i.local = function() {
        return a(this.toDate(), { locale: this.$L, utc: false });
      };
      var s = i.parse;
      i.parse = function(d) {
        d.utc && (this.$u = true), this.$utils().u(d.$offset) || (this.$offset = d.$offset), s.call(this, d);
      };
      var c = i.init;
      i.init = function() {
        if (this.$u) {
          var d = this.$d;
          this.$y = d.getUTCFullYear(), this.$M = d.getUTCMonth(), this.$D = d.getUTCDate(), this.$W = d.getUTCDay(), this.$H = d.getUTCHours(), this.$m = d.getUTCMinutes(), this.$s = d.getUTCSeconds(), this.$ms = d.getUTCMilliseconds();
        } else
          c.call(this);
      };
      var u = i.utcOffset;
      i.utcOffset = function(d, f) {
        var x2 = this.$utils().u;
        if (x2(d))
          return this.$u ? 0 : x2(this.$offset) ? u.call(this) : this.$offset;
        if (typeof d == "string" && (d = function(y) {
          y === void 0 && (y = "");
          var A = y.match(t);
          if (!A)
            return null;
          var I = ("" + A[0]).match(r) || ["-", 0, 0], v = I[0], R = 60 * +I[1] + +I[2];
          return R === 0 ? 0 : v === "+" ? R : -R;
        }(d), d === null))
          return this;
        var S = Math.abs(d) <= 16 ? 60 * d : d, g = this;
        if (f)
          return g.$offset = S, g.$u = d === 0, g;
        if (d !== 0) {
          var C = this.$u ? this.toDate().getTimezoneOffset() : -1 * this.utcOffset();
          (g = this.local().add(S + C, e7)).$offset = S, g.$x.$localOffset = C;
        } else
          g = this.utc();
        return g;
      };
      var l = i.format;
      i.format = function(d) {
        var f = d || (this.$u ? "YYYY-MM-DDTHH:mm:ss[Z]" : "");
        return l.call(this, f);
      }, i.valueOf = function() {
        var d = this.$utils().u(this.$offset) ? 0 : this.$offset + (this.$x.$localOffset || this.$d.getTimezoneOffset());
        return this.$d.valueOf() - 6e4 * d;
      }, i.isUTC = function() {
        return !!this.$u;
      }, i.toISOString = function() {
        return this.toDate().toISOString();
      }, i.toString = function() {
        return this.toDate().toUTCString();
      };
      var m = i.toDate;
      i.toDate = function(d) {
        return d === "s" && this.$offset ? a(this.format("YYYY-MM-DD HH:mm:ss:SSS")).toDate() : m.call(this);
      };
      var p = i.diff;
      i.diff = function(d, f, x2) {
        if (d && this.$u === d.$u)
          return p.call(this, d, f, x2);
        var S = this.local(), g = a(d).local();
        return p.call(S, g, f, x2);
      };
    };
  });
});
var YC = Oe((pK, KC) => {
  function Qk(e7) {
    try {
      return JSON.stringify(e7);
    } catch {
      return '"[Circular]"';
    }
  }
  KC.exports = Lk;
  function Lk(e7, t, r) {
    var n = r && r.stringify || Qk, o = 1;
    if (typeof e7 == "object" && e7 !== null) {
      var a = t.length + o;
      if (a === 1)
        return e7;
      var i = new Array(a);
      i[0] = n(e7);
      for (var s = 1; s < a; s++)
        i[s] = n(t[s]);
      return i.join(" ");
    }
    if (typeof e7 != "string")
      return e7;
    var c = t.length;
    if (c === 0)
      return e7;
    for (var u = "", l = 1 - o, m = -1, p = e7 && e7.length || 0, d = 0; d < p; ) {
      if (e7.charCodeAt(d) === 37 && d + 1 < p) {
        switch (m = m > -1 ? m : 0, e7.charCodeAt(d + 1)) {
          case 100:
          case 102:
            if (l >= c || t[l] == null)
              break;
            m < d && (u += e7.slice(m, d)), u += Number(t[l]), m = d + 2, d++;
            break;
          case 105:
            if (l >= c || t[l] == null)
              break;
            m < d && (u += e7.slice(m, d)), u += Math.floor(Number(t[l])), m = d + 2, d++;
            break;
          case 79:
          case 111:
          case 106:
            if (l >= c || t[l] === void 0)
              break;
            m < d && (u += e7.slice(m, d));
            var f = typeof t[l];
            if (f === "string") {
              u += "'" + t[l] + "'", m = d + 2, d++;
              break;
            }
            if (f === "function") {
              u += t[l].name || "<anonymous>", m = d + 2, d++;
              break;
            }
            u += n(t[l]), m = d + 2, d++;
            break;
          case 115:
            if (l >= c)
              break;
            m < d && (u += e7.slice(m, d)), u += String(t[l]), m = d + 2, d++;
            break;
          case 37:
            m < d && (u += e7.slice(m, d)), u += "%", m = d + 2, d++, l--;
            break;
        }
        ++l;
      }
      ++d;
    }
    return m === -1 ? e7 : (m < p && (u += e7.slice(m)), u);
  }
});
var rx = Oe((mK, ol) => {
  var JC2 = YC();
  ol.exports = Or;
  var $s2 = eO().console || {}, Bk = { mapHttpRequest: nl, mapHttpResponse: nl, wrapRequestSerializer: wf, wrapResponseSerializer: wf, wrapErrorSerializer: wf, req: nl, res: nl, err: ZC, errWithCause: ZC };
  function fn(e7, t) {
    return e7 === "silent" ? 1 / 0 : t.levels.values[e7];
  }
  var Tf = Symbol("pino.logFuncs"), If = Symbol("pino.hierarchy"), Uk = { error: "log", fatal: "error", warn: "error", info: "log", debug: "log", trace: "log" };
  function XC(e7, t) {
    let r = { logger: t, parent: e7[If] };
    t[If] = r;
  }
  function _k(e7, t, r) {
    let n = {};
    t.forEach((o) => {
      n[o] = r[o] ? r[o] : $s2[o] || $s2[Uk[o] || "log"] || Va2;
    }), e7[Tf] = n;
  }
  function jk(e7, t) {
    return Array.isArray(e7) ? e7.filter(function(n) {
      return n !== "!stdSerializers.err";
    }) : e7 === true ? Object.keys(t) : false;
  }
  function Or(e7) {
    e7 = e7 || {}, e7.browser = e7.browser || {};
    let t = e7.browser.transmit;
    if (t && typeof t.send != "function")
      throw Error("pino: transmit option must have a send function");
    let r = e7.browser.write || $s2;
    e7.browser.write && (e7.browser.asObject = true);
    let n = e7.serializers || {}, o = jk(e7.browser.serialize, n), a = e7.browser.serialize;
    Array.isArray(e7.browser.serialize) && e7.browser.serialize.indexOf("!stdSerializers.err") > -1 && (a = false);
    let i = Object.keys(e7.customLevels || {}), s = ["error", "fatal", "warn", "info", "debug", "trace"].concat(i);
    typeof r == "function" && s.forEach(function(x2) {
      r[x2] = r;
    }), (e7.enabled === false || e7.browser.disabled) && (e7.level = "silent");
    let c = e7.level || "info", u = Object.create(r);
    u.log || (u.log = Va2), _k(u, s, r), XC({}, u), Object.defineProperty(u, "levelVal", { get: m }), Object.defineProperty(u, "level", { get: p, set: d });
    let l = { transmit: t, serialize: o, asObject: e7.browser.asObject, formatters: e7.browser.formatters, levels: s, timestamp: Jk(e7), messageKey: e7.messageKey || "msg", onChild: e7.onChild || Va2 };
    u.levels = $k(e7), u.level = c, u.setMaxListeners = u.getMaxListeners = u.emit = u.addListener = u.on = u.prependListener = u.once = u.prependOnceListener = u.removeListener = u.removeAllListeners = u.listeners = u.listenerCount = u.eventNames = u.write = u.flush = Va2, u.serializers = n, u._serialize = o, u._stdErrSerialize = a, u.child = function(...x2) {
      return f.call(this, l, ...x2);
    }, t && (u._logEvent = Ef());
    function m() {
      return fn(this.level, this);
    }
    function p() {
      return this._level;
    }
    function d(x2) {
      if (x2 !== "silent" && !this.levels.values[x2])
        throw Error("unknown level " + x2);
      this._level = x2, ao(this, l, u, "error"), ao(this, l, u, "fatal"), ao(this, l, u, "warn"), ao(this, l, u, "info"), ao(this, l, u, "debug"), ao(this, l, u, "trace"), i.forEach((S) => {
        ao(this, l, u, S);
      });
    }
    function f(x2, S, g) {
      if (!S)
        throw new Error("missing bindings for child Pino");
      g = g || {}, o && S.serializers && (g.serializers = S.serializers);
      let C = g.serializers;
      if (o && C) {
        var y = Object.assign({}, n, C), A = e7.browser.serialize === true ? Object.keys(y) : o;
        delete S.serializers, kf([S], A, y, this._stdErrSerialize);
      }
      function I(R) {
        this._childLevel = (R._childLevel | 0) + 1, this.bindings = S, y && (this.serializers = y, this._serialize = A), t && (this._logEvent = Ef([].concat(R._logEvent.bindings, S)));
      }
      I.prototype = this;
      let v = new I(this);
      return XC(this, v), v.child = function(...R) {
        return f.call(this, x2, ...R);
      }, v.level = g.level || this.level, x2.onChild(v), v;
    }
    return u;
  }
  function $k(e7) {
    let t = e7.customLevels || {}, r = Object.assign({}, Or.levels.values, t), n = Object.assign({}, Or.levels.labels, Gk(t));
    return { values: r, labels: n };
  }
  function Gk(e7) {
    let t = {};
    return Object.keys(e7).forEach(function(r) {
      t[e7[r]] = r;
    }), t;
  }
  Or.levels = { values: { fatal: 60, error: 50, warn: 40, info: 30, debug: 20, trace: 10 }, labels: { 10: "trace", 20: "debug", 30: "info", 40: "warn", 50: "error", 60: "fatal" } };
  Or.stdSerializers = Bk;
  Or.stdTimeFunctions = Object.assign({}, { nullTime: ex, epochTime: tx, unixTime: Xk, isoTime: Zk });
  function Wk(e7) {
    let t = [];
    e7.bindings && t.push(e7.bindings);
    let r = e7[If];
    for (; r.parent; )
      r = r.parent, r.logger.bindings && t.push(r.logger.bindings);
    return t.reverse();
  }
  function ao(e7, t, r, n) {
    if (Object.defineProperty(e7, n, { value: fn(e7.level, r) > fn(n, r) ? Va2 : r[Tf][n], writable: true, enumerable: true, configurable: true }), e7[n] === Va2) {
      if (!t.transmit)
        return;
      let a = t.transmit.level || e7.level, i = fn(a, r);
      if (fn(n, r) < i)
        return;
    }
    e7[n] = zk(e7, t, r, n);
    let o = Wk(e7);
    o.length !== 0 && (e7[n] = Hk(o, e7[n]));
  }
  function Hk(e7, t) {
    return function() {
      return t.apply(this, [...e7, ...arguments]);
    };
  }
  function zk(e7, t, r, n) {
    return function(o) {
      return function() {
        let i = t.timestamp(), s = new Array(arguments.length), c = Object.getPrototypeOf && Object.getPrototypeOf(this) === $s2 ? $s2 : this;
        for (var u = 0; u < s.length; u++)
          s[u] = arguments[u];
        var l = false;
        if (t.serialize && (kf(s, this._serialize, this.serializers, this._stdErrSerialize), l = true), t.asObject || t.formatters ? o.call(c, Kk(this, n, s, i, t)) : o.apply(c, s), t.transmit) {
          let m = t.transmit.level || e7._level, p = fn(m, r), d = fn(n, r);
          if (d < p)
            return;
          Yk(this, { ts: i, methodLevel: n, methodValue: d, send: t.transmit.send, val: fn(e7._level, r) }, s, l);
        }
      };
    }(e7[Tf][n]);
  }
  function Kk(e7, t, r, n, o) {
    let { level: a, log: i = (p) => p } = o.formatters || {}, s = r.slice(), c = s[0], u = {};
    if (n && (u.time = n), a) {
      let p = a(t, e7.levels.values[t]);
      Object.assign(u, p);
    } else
      u.level = e7.levels.values[t];
    let l = (e7._childLevel | 0) + 1;
    if (l < 1 && (l = 1), c !== null && typeof c == "object") {
      for (; l-- && typeof s[0] == "object"; )
        Object.assign(u, s.shift());
      c = s.length ? JC2(s.shift(), s) : void 0;
    } else
      typeof c == "string" && (c = JC2(s.shift(), s));
    return c !== void 0 && (u[o.messageKey] = c), i(u);
  }
  function kf(e7, t, r, n) {
    for (let o in e7)
      if (n && e7[o] instanceof Error)
        e7[o] = Or.stdSerializers.err(e7[o]);
      else if (typeof e7[o] == "object" && !Array.isArray(e7[o]) && t)
        for (let a in e7[o])
          t.indexOf(a) > -1 && a in r && (e7[o][a] = r[a](e7[o][a]));
  }
  function Yk(e7, t, r, n = false) {
    let o = t.send, a = t.ts, i = t.methodLevel, s = t.methodValue, c = t.val, u = e7._logEvent.bindings;
    n || kf(r, e7._serialize || Object.keys(e7.serializers), e7.serializers, e7._stdErrSerialize === void 0 ? true : e7._stdErrSerialize), e7._logEvent.ts = a, e7._logEvent.messages = r.filter(function(l) {
      return u.indexOf(l) === -1;
    }), e7._logEvent.level.label = i, e7._logEvent.level.value = s, o(i, e7._logEvent, c), e7._logEvent = Ef(u);
  }
  function Ef(e7) {
    return { ts: 0, messages: [], bindings: e7 || [], level: { label: "", value: 0 } };
  }
  function ZC(e7) {
    let t = { type: e7.constructor.name, msg: e7.message, stack: e7.stack };
    for (let r in e7)
      t[r] === void 0 && (t[r] = e7[r]);
    return t;
  }
  function Jk(e7) {
    return typeof e7.timestamp == "function" ? e7.timestamp : e7.timestamp === false ? ex : tx;
  }
  function nl() {
    return {};
  }
  function wf(e7) {
    return e7;
  }
  function Va2() {
  }
  function ex() {
    return false;
  }
  function tx() {
    return Date.now();
  }
  function Xk() {
    return Math.round(Date.now() / 1e3);
  }
  function Zk() {
    return new Date(Date.now()).toISOString();
  }
  function eO() {
    function e7(t) {
      return typeof t < "u" && t;
    }
    try {
      return typeof globalThis < "u" || Object.defineProperty(Object.prototype, "globalThis", { get: function() {
        return delete Object.prototype.globalThis, this.globalThis = this;
      }, configurable: true }), globalThis;
    } catch {
      return e7(self) || e7(window) || e7(this) || {};
    }
  }
  ol.exports.default = Or;
  ol.exports.pino = Or;
});
var Xg = {};
Yb(Xg, { escape: () => ko, getHighlightedSuggestion: () => Pp, highlightString: () => tv });
function Ac(e7) {
  return Array.isArray(e7);
}
function Fc(e7) {
  return e7.trim() === "";
}
function zg(e7, t) {
  return [...e7.reduce((r, n) => {
    let o = t(n);
    return r.has(o) || r.set(o, n), r;
  }, /* @__PURE__ */ new Map()).values()];
}
function Xb(e7) {
  return btoa(encodeURI(e7));
}
function To(e7) {
  return Xb(JSON.stringify(e7));
}
function Hi(e7) {
  if (typeof e7 != "object" || !e7)
    return e7;
  try {
    return JSON.parse(JSON.stringify(e7));
  } catch {
    return e7;
  }
}
function tv(e7) {
  if (Fc(e7.openingDelimiter) || Fc(e7.closingDelimiter))
    throw Error("delimiters should be a non-empty string");
  if (isNullOrUndefined(e7.content) || Fc(e7.content))
    return e7.content;
  if (e7.highlights.length === 0)
    return ko(e7.content);
  let t = e7.content.length, r = "", n = 0;
  for (let o = 0; o < e7.highlights.length; o++) {
    let a = e7.highlights[o], i = a.offset, s = i + a.length;
    if (s > t)
      break;
    r += ko(e7.content.slice(n, i)), r += e7.openingDelimiter, r += ko(e7.content.slice(i, s)), r += e7.closingDelimiter, n = s;
  }
  return n !== t && (r += ko(e7.content.slice(n))), r;
}
function Pp(e7, t) {
  return e7 = ko(e7), e7.replace(/\[(.*?)\]|\{(.*?)\}|\((.*?)\)/g, (r, n, o, a) => n ? vp(n, t.notMatchDelimiters) : o ? vp(o, t.exactMatchDelimiters) : a ? vp(a, t.correctionDelimiters) : r);
}
function vp(e7, t) {
  return t ? t.open + e7 + t.close : e7;
}
function ko(e7) {
  let t = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;", "`": "&#x60;" }, r = "(?:" + Object.keys(t).join("|") + ")", n = RegExp(r), o = RegExp(r, "g");
  return n.test(e7) ? e7.replace(o, (a) => t[a]) : e7;
}
async function eS(e7, t) {
  let r = e7.getReader(), n;
  for (; !(n = await r.read()).done; )
    t(n.value);
}
function tS(e7) {
  let t, r, n, o = false;
  return function(i) {
    t === void 0 ? (t = i, r = 0, n = -1) : t = nv(t, i);
    let s = t.length, c = 0;
    for (; r < s; ) {
      o && (t[r] === 10 && (c = ++r), o = false);
      let u = -1;
      for (; r < s && u === -1; ++r)
        switch (t[r]) {
          case 58:
            n === -1 && (n = r - c);
            break;
          case 13:
            o = true, u = r;
            break;
          case 10:
            u = r;
            break;
        }
      if (u === -1)
        break;
      e7(t.subarray(c, u), n), c = r, n = -1;
    }
    c === s ? t = void 0 : c !== 0 && (t = t.subarray(c), r -= c);
  };
}
function rS(e7, t, r) {
  let n = Zg(), o = new TextDecoder();
  return function(i, s) {
    if (i.length === 0)
      r?.(n), n = Zg();
    else if (s > 0) {
      let c = o.decode(i.subarray(0, s)), u = s + (i[s + 1] === 32 ? 2 : 1), l = o.decode(i.subarray(u));
      switch (c) {
        case "data":
          n.data = n.data ? n.data + `
` + l : l;
          break;
        case "event":
          n.event = l;
          break;
        case "id":
          e7(n.id = l);
          break;
        case "retry":
          rv(l, n, t);
          break;
      }
    }
  };
}
function rv(e7, t, r) {
  let n = parseInt(e7, 10);
  isNaN(n) || r(t.retry = n);
}
function nv(e7, t) {
  let r = new Uint8Array(e7.length + t.length);
  return r.set(e7), r.set(t, e7.length), r;
}
function Zg() {
  return { data: "", event: "", id: "", retry: void 0 };
}
var wp = "text/event-stream";
var ov = 1e3;
var nS = "last-event-id";
function oS() {
  return typeof window < "u";
}
function bc(e7, { signal: t, headers: r, onopen: n, onmessage: o, onclose: a, onerror: i, openWhenHidden: s, fetch: c, ...u }) {
  return new Promise((l, m) => {
    let p = { ...r };
    p.accept || (p.accept = wp);
    let d;
    function f() {
      d?.abort(), document.hidden || A();
    }
    !s && oS() && document.addEventListener("visibilitychange", f);
    let x2 = ov, S;
    function g() {
      oS() && document.removeEventListener("visibilitychange", f), clearTimeout(S), d?.abort();
    }
    t?.addEventListener("abort", () => {
      g(), l();
    });
    let C = c ?? fetch, y = n ?? av;
    async function A() {
      d = AbortController ? new AbortController() : null;
      try {
        let I = await C(e7, { ...u, headers: p, signal: d?.signal });
        await y(I), await eS(I.body, tS(rS((v) => {
          v ? p[nS] = v : delete p[nS];
        }, (v) => {
          x2 = v;
        }, o))), a?.(), g(), l();
      } catch (I) {
        if (!d?.signal?.aborted)
          try {
            let v = i?.(I) ?? x2;
            clearTimeout(S), S = setTimeout(A, v);
          } catch (v) {
            g(), m(v);
          }
      }
    }
    A();
  });
}
function av(e7) {
  let t = e7.headers.get("content-type");
  if (!t?.startsWith(wp))
    throw new Error(`Expected content-type to be ${wp}, Actual: ${t}`);
}
var jr = class {
  constructor(t) {
    Ce(this, "_basePath");
    Ce(this, "_params", {});
    this._basePath = t;
  }
  addParam(t, r) {
    this._params = { ...this.params, [t]: r };
  }
  get basePath() {
    return this._basePath;
  }
  get params() {
    return this._params;
  }
  get hasParams() {
    return Object.entries(this._params).length;
  }
  get href() {
    return this.hasParams ? `${this.basePath}?${Object.entries(this.params).map(([t, r]) => `${t}=${encodeURIComponent(r)}`).join("&")}` : this.basePath;
  }
};
var Tp = 1;
Vt(mS());
function Me(e7, t = "prod", r = "platform") {
  let n = t === "prod" ? "" : t, o = r === "platform" ? "" : `.${r}`;
  return `https://${e7}${o}.org${n}.coveo.com`;
}
function ve(e7, t = "prod") {
  return `${Me(e7, t)}/rest/search/v2`;
}
function Lp(e7, t = "prod") {
  return `${Me(e7, t, "analytics")}/rest/organizations/${e7}/events/v1`;
}
function qo() {
  return { answerSnippet: "", documentId: { contentIdKey: "", contentIdValue: "" }, question: "", relatedQuestions: [], score: 0 };
}
function et() {
  return { response: { results: [], searchUid: "", totalCountFiltered: 0, facets: [], generateAutomaticFacets: { facets: [] }, queryCorrections: [], triggers: [], questionAnswer: qo(), pipeline: "", splitTestRun: "", termsToHighlight: {}, phrasesToHighlight: {}, extendedResults: {} }, duration: 0, queryExecuted: "", error: null, automaticallyCorrected: false, isLoading: false, results: [], searchResponseId: "", requestId: "", questionAnswer: qo(), extendedResults: {} };
}
var FS = (e7, t) => {
  let r = new jr(`${e7.url}${t}`);
  return r.addParam("access_token", e7.accessToken), r.addParam("organizationId", e7.organizationId), r.addParam("uniqueId", e7.uniqueId), e7.authentication && r.addParam("authentication", e7.authentication), e7.q !== void 0 && r.addParam("q", e7.q), e7.enableNavigation !== void 0 && r.addParam("enableNavigation", `${e7.enableNavigation}`), e7.requestedOutputSize !== void 0 && r.addParam("requestedOutputSize", `${e7.requestedOutputSize}`), r.href;
};
var Ec = (e7) => e7.success !== void 0;
var we = (e7) => e7.error !== void 0;
var V = new StringValue({ required: true, emptyAllowed: false });
var de = new StringValue({ required: false, emptyAllowed: false });
var ce = new StringValue({ required: true, emptyAllowed: true });
var PS = new StringValue({ required: false, emptyAllowed: true });
var Tc = new ArrayValue({ each: V, required: true });
var wS = new StringValue({ required: false, emptyAllowed: false, regex: /^\d+\.\d+\.\d+$/ });
var br = ({ message: e7, name: t, stack: r }) => ({ message: e7, name: t, stack: r });
var ct = (e7, t) => {
  if ("required" in t)
    return { payload: new Schema({ value: t }).validate({ value: e7 }).value };
  let o = new RecordValue({ options: { required: true }, values: t }).validate(e7);
  if (o)
    throw new SchemaValidationError(o);
  return { payload: e7 };
};
var F = (e7, t) => {
  try {
    return ct(e7, t);
  } catch (r) {
    return { payload: e7, error: br(r) };
  }
};
function qe(e7) {
  return `Minified Redux error #${e7}; visit https://redux.js.org/Errors?code=${e7} for the full message or use the non-minified dev environment for full errors. `;
}
var Bp = () => Math.random().toString(36).substring(7).split("").join(".");
var tP = { INIT: `@@redux/INIT${Bp()}`, REPLACE: `@@redux/REPLACE${Bp()}`, PROBE_UNKNOWN_ACTION: () => `@@redux/PROBE_UNKNOWN_ACTION${Bp()}` };
var kc = tP;
function Nt(e7) {
  if (typeof e7 != "object" || e7 === null)
    return false;
  let t = e7;
  for (; Object.getPrototypeOf(t) !== null; )
    t = Object.getPrototypeOf(t);
  return Object.getPrototypeOf(e7) === t || Object.getPrototypeOf(e7) === null;
}
function rP(e7) {
  Object.keys(e7).forEach((t) => {
    let r = e7[t];
    if (typeof r(void 0, { type: kc.INIT }) > "u")
      throw new Error(qe(12));
    if (typeof r(void 0, { type: kc.PROBE_UNKNOWN_ACTION() }) > "u")
      throw new Error(qe(13));
  });
}
function Do(e7) {
  let t = Object.keys(e7), r = {};
  for (let i = 0; i < t.length; i++) {
    let s = t[i];
    typeof e7[s] == "function" && (r[s] = e7[s]);
  }
  let n = Object.keys(r), a;
  try {
    rP(r);
  } catch (i) {
    a = i;
  }
  return function(s = {}, c) {
    if (a)
      throw a;
    let u = false, l = {};
    for (let m = 0; m < n.length; m++) {
      let p = n[m], d = r[p], f = s[p], x2 = d(f, c);
      if (typeof x2 > "u") {
        throw new Error(qe(14));
      }
      l[p] = x2, u = u || x2 !== f;
    }
    return u = u || n.length !== Object.keys(s).length, u ? l : s;
  };
}
function Oc(e7) {
  return Nt(e7) && "type" in e7 && typeof e7.type == "string";
}
var Jp = Symbol.for("immer-nothing");
var Zi = Symbol.for("immer-draftable");
var We = Symbol.for("immer-state");
function De(e7, ...t) {
  throw new Error(`[Immer] minified error nr: ${e7}. Full error at: https://bit.ly/3cXEKWf`);
}
var Wn = Object.getPrototypeOf;
function tt(e7) {
  return !!e7 && !!e7[We];
}
function He(e7) {
  return e7 ? VS(e7) || Array.isArray(e7) || !!e7[Zi] || !!e7.constructor?.[Zi] || os(e7) || as(e7) : false;
}
var nP = Object.prototype.constructor.toString();
function VS(e7) {
  if (!e7 || typeof e7 != "object")
    return false;
  let t = Wn(e7);
  if (t === null)
    return true;
  let r = Object.hasOwnProperty.call(t, "constructor") && t.constructor;
  return r === Object ? true : typeof r == "function" && Function.toString.call(r) === nP;
}
function Xp(e7) {
  return tt(e7) || De(15, e7), e7[We].base_;
}
function es(e7, t) {
  Hn(e7) === 0 ? Reflect.ownKeys(e7).forEach((r) => {
    t(r, e7[r], e7);
  }) : e7.forEach((r, n) => t(n, r, e7));
}
function Hn(e7) {
  let t = e7[We];
  return t ? t.type_ : Array.isArray(e7) ? 1 : os(e7) ? 2 : as(e7) ? 3 : 0;
}
function ts(e7, t) {
  return Hn(e7) === 2 ? e7.has(t) : Object.prototype.hasOwnProperty.call(e7, t);
}
function _p(e7, t) {
  return Hn(e7) === 2 ? e7.get(t) : e7[t];
}
function NS(e7, t, r) {
  let n = Hn(e7);
  n === 2 ? e7.set(t, r) : n === 3 ? e7.add(r) : e7[t] = r;
}
function oP(e7, t) {
  return e7 === t ? e7 !== 0 || 1 / e7 === 1 / t : e7 !== e7 && t !== t;
}
function os(e7) {
  return e7 instanceof Map;
}
function as(e7) {
  return e7 instanceof Set;
}
function Gn(e7) {
  return e7.copy_ || e7.base_;
}
function Gp(e7, t) {
  if (os(e7))
    return new Map(e7);
  if (as(e7))
    return new Set(e7);
  if (Array.isArray(e7))
    return Array.prototype.slice.call(e7);
  let r = VS(e7);
  if (t === true || t === "class_only" && !r) {
    let n = Object.getOwnPropertyDescriptors(e7);
    delete n[We];
    let o = Reflect.ownKeys(n);
    for (let a = 0; a < o.length; a++) {
      let i = o[a], s = n[i];
      s.writable === false && (s.writable = true, s.configurable = true), (s.get || s.set) && (n[i] = { configurable: true, writable: true, enumerable: s.enumerable, value: e7[i] });
    }
    return Object.create(Wn(e7), n);
  } else {
    let n = Wn(e7);
    if (n !== null && r)
      return { ...e7 };
    let o = Object.create(n);
    return Object.assign(o, e7);
  }
}
function Vc(e7, t = false) {
  return Nc(e7) || tt(e7) || !He(e7) || (Hn(e7) > 1 && (e7.set = e7.add = e7.clear = e7.delete = aP), Object.freeze(e7), t && Object.entries(e7).forEach(([r, n]) => Vc(n, true))), e7;
}
function aP() {
  De(2);
}
function Nc(e7) {
  return Object.isFrozen(e7);
}
var Wp = {};
function zn(e7) {
  let t = Wp[e7];
  return t || De(0, e7), t;
}
function iP(e7, t) {
  Wp[e7] || (Wp[e7] = t);
}
var rs;
function MS() {
  return rs;
}
function sP(e7, t) {
  return { drafts_: [], parent_: e7, immer_: t, canAutoFreeze_: true, unfinalizedDrafts_: 0 };
}
function kS(e7, t) {
  t && (zn("Patches"), e7.patches_ = [], e7.inversePatches_ = [], e7.patchListener_ = t);
}
function Hp(e7) {
  zp(e7), e7.drafts_.forEach(cP), e7.drafts_ = null;
}
function zp(e7) {
  e7 === rs && (rs = e7.parent_);
}
function OS(e7) {
  return rs = sP(rs, e7);
}
function cP(e7) {
  let t = e7[We];
  t.type_ === 0 || t.type_ === 1 ? t.revoke_() : t.revoked_ = true;
}
function qS(e7, t) {
  t.unfinalizedDrafts_ = t.drafts_.length;
  let r = t.drafts_[0];
  return e7 !== void 0 && e7 !== r ? (r[We].modified_ && (Hp(t), De(4)), He(e7) && (e7 = qc(t, e7), t.parent_ || Dc(t, e7)), t.patches_ && zn("Patches").generateReplacementPatches_(r[We].base_, e7, t.patches_, t.inversePatches_)) : e7 = qc(t, r, []), Hp(t), t.patches_ && t.patchListener_(t.patches_, t.inversePatches_), e7 !== Jp ? e7 : void 0;
}
function qc(e7, t, r) {
  if (Nc(t))
    return t;
  let n = t[We];
  if (!n)
    return es(t, (o, a) => DS(e7, n, t, o, a, r)), t;
  if (n.scope_ !== e7)
    return t;
  if (!n.modified_)
    return Dc(e7, n.base_, true), n.base_;
  if (!n.finalized_) {
    n.finalized_ = true, n.scope_.unfinalizedDrafts_--;
    let o = n.copy_, a = o, i = false;
    n.type_ === 3 && (a = new Set(o), o.clear(), i = true), es(a, (s, c) => DS(e7, n, o, s, c, r, i)), Dc(e7, o, false), r && e7.patches_ && zn("Patches").generatePatches_(n, r, e7.patches_, e7.inversePatches_);
  }
  return n.copy_;
}
function DS(e7, t, r, n, o, a, i) {
  if (tt(o)) {
    let s = a && t && t.type_ !== 3 && !ts(t.assigned_, n) ? a.concat(n) : void 0, c = qc(e7, o, s);
    if (NS(r, n, c), tt(c))
      e7.canAutoFreeze_ = false;
    else
      return;
  } else
    i && r.add(o);
  if (He(o) && !Nc(o)) {
    if (!e7.immer_.autoFreeze_ && e7.unfinalizedDrafts_ < 1)
      return;
    qc(e7, o), (!t || !t.scope_.parent_) && typeof n != "symbol" && Object.prototype.propertyIsEnumerable.call(r, n) && Dc(e7, o);
  }
}
function Dc(e7, t, r = false) {
  !e7.parent_ && e7.immer_.autoFreeze_ && e7.canAutoFreeze_ && Vc(t, r);
}
function uP(e7, t) {
  let r = Array.isArray(e7), n = { type_: r ? 1 : 0, scope_: t ? t.scope_ : MS(), modified_: false, finalized_: false, assigned_: {}, parent_: t, base_: e7, draft_: null, copy_: null, revoke_: null, isManual_: false }, o = n, a = Zp;
  r && (o = [n], a = ns);
  let { revoke: i, proxy: s } = Proxy.revocable(o, a);
  return n.draft_ = s, n.revoke_ = i, s;
}
var Zp = { get(e7, t) {
  if (t === We)
    return e7;
  let r = Gn(e7);
  if (!ts(r, t))
    return lP(e7, r, t);
  let n = r[t];
  return e7.finalized_ || !He(n) ? n : n === jp(e7.base_, t) ? ($p(e7), e7.copy_[t] = Yp(n, e7)) : n;
}, has(e7, t) {
  return t in Gn(e7);
}, ownKeys(e7) {
  return Reflect.ownKeys(Gn(e7));
}, set(e7, t, r) {
  let n = QS(Gn(e7), t);
  if (n?.set)
    return n.set.call(e7.draft_, r), true;
  if (!e7.modified_) {
    let o = jp(Gn(e7), t), a = o?.[We];
    if (a && a.base_ === r)
      return e7.copy_[t] = r, e7.assigned_[t] = false, true;
    if (oP(r, o) && (r !== void 0 || ts(e7.base_, t)))
      return true;
    $p(e7), Kp(e7);
  }
  return e7.copy_[t] === r && (r !== void 0 || t in e7.copy_) || Number.isNaN(r) && Number.isNaN(e7.copy_[t]) || (e7.copy_[t] = r, e7.assigned_[t] = true), true;
}, deleteProperty(e7, t) {
  return jp(e7.base_, t) !== void 0 || t in e7.base_ ? (e7.assigned_[t] = false, $p(e7), Kp(e7)) : delete e7.assigned_[t], e7.copy_ && delete e7.copy_[t], true;
}, getOwnPropertyDescriptor(e7, t) {
  let r = Gn(e7), n = Reflect.getOwnPropertyDescriptor(r, t);
  return n && { writable: true, configurable: e7.type_ !== 1 || t !== "length", enumerable: n.enumerable, value: r[t] };
}, defineProperty() {
  De(11);
}, getPrototypeOf(e7) {
  return Wn(e7.base_);
}, setPrototypeOf() {
  De(12);
} };
var ns = {};
es(Zp, (e7, t) => {
  ns[e7] = function() {
    return arguments[0] = arguments[0][0], t.apply(this, arguments);
  };
});
ns.deleteProperty = function(e7, t) {
  return ns.set.call(this, e7, t, void 0);
};
ns.set = function(e7, t, r) {
  return Zp.set.call(this, e7[0], t, r, e7[0]);
};
function jp(e7, t) {
  let r = e7[We];
  return (r ? Gn(r) : e7)[t];
}
function lP(e7, t, r) {
  let n = QS(t, r);
  return n ? "value" in n ? n.value : n.get?.call(e7.draft_) : void 0;
}
function QS(e7, t) {
  if (!(t in e7))
    return;
  let r = Wn(e7);
  for (; r; ) {
    let n = Object.getOwnPropertyDescriptor(r, t);
    if (n)
      return n;
    r = Wn(r);
  }
}
function Kp(e7) {
  e7.modified_ || (e7.modified_ = true, e7.parent_ && Kp(e7.parent_));
}
function $p(e7) {
  e7.copy_ || (e7.copy_ = Gp(e7.base_, e7.scope_.immer_.useStrictShallowCopy_));
}
var dP = class {
  constructor(e7) {
    this.autoFreeze_ = true, this.useStrictShallowCopy_ = false, this.produce = (t, r, n) => {
      if (typeof t == "function" && typeof r != "function") {
        let a = r;
        r = t;
        let i = this;
        return function(c = a, ...u) {
          return i.produce(c, (l) => r.call(this, l, ...u));
        };
      }
      typeof r != "function" && De(6), n !== void 0 && typeof n != "function" && De(7);
      let o;
      if (He(t)) {
        let a = OS(this), i = Yp(t, void 0), s = true;
        try {
          o = r(i), s = false;
        } finally {
          s ? Hp(a) : zp(a);
        }
        return kS(a, n), qS(o, a);
      } else if (!t || typeof t != "object") {
        if (o = r(t), o === void 0 && (o = t), o === Jp && (o = void 0), this.autoFreeze_ && Vc(o, true), n) {
          let a = [], i = [];
          zn("Patches").generateReplacementPatches_(t, o, a, i), n(a, i);
        }
        return o;
      } else
        De(1, t);
    }, this.produceWithPatches = (t, r) => {
      if (typeof t == "function")
        return (i, ...s) => this.produceWithPatches(i, (c) => t(c, ...s));
      let n, o;
      return [this.produce(t, r, (i, s) => {
        n = i, o = s;
      }), n, o];
    }, typeof e7?.autoFreeze == "boolean" && this.setAutoFreeze(e7.autoFreeze), typeof e7?.useStrictShallowCopy == "boolean" && this.setUseStrictShallowCopy(e7.useStrictShallowCopy);
  }
  createDraft(e7) {
    He(e7) || De(8), tt(e7) && (e7 = LS(e7));
    let t = OS(this), r = Yp(e7, void 0);
    return r[We].isManual_ = true, zp(t), r;
  }
  finishDraft(e7, t) {
    let r = e7 && e7[We];
    (!r || !r.isManual_) && De(9);
    let { scope_: n } = r;
    return kS(n, t), qS(void 0, n);
  }
  setAutoFreeze(e7) {
    this.autoFreeze_ = e7;
  }
  setUseStrictShallowCopy(e7) {
    this.useStrictShallowCopy_ = e7;
  }
  applyPatches(e7, t) {
    let r;
    for (r = t.length - 1; r >= 0; r--) {
      let o = t[r];
      if (o.path.length === 0 && o.op === "replace") {
        e7 = o.value;
        break;
      }
    }
    r > -1 && (t = t.slice(r + 1));
    let n = zn("Patches").applyPatches_;
    return tt(e7) ? n(e7, t) : this.produce(e7, (o) => n(o, t));
  }
};
function Yp(e7, t) {
  let r = os(e7) ? zn("MapSet").proxyMap_(e7, t) : as(e7) ? zn("MapSet").proxySet_(e7, t) : uP(e7, t);
  return (t ? t.scope_ : MS()).drafts_.push(r), r;
}
function LS(e7) {
  return tt(e7) || De(10, e7), BS(e7);
}
function BS(e7) {
  if (!He(e7) || Nc(e7))
    return e7;
  let t = e7[We], r;
  if (t) {
    if (!t.modified_)
      return t.base_;
    t.finalized_ = true, r = Gp(e7, t.scope_.immer_.useStrictShallowCopy_);
  } else
    r = Gp(e7, true);
  return es(r, (n, o) => {
    NS(r, n, BS(o));
  }), t && (t.finalized_ = false), r;
}
function US() {
  let t = "replace", r = "add", n = "remove";
  function o(p, d, f, x2) {
    switch (p.type_) {
      case 0:
      case 2:
        return i(p, d, f, x2);
      case 1:
        return a(p, d, f, x2);
      case 3:
        return s(p, d, f, x2);
    }
  }
  function a(p, d, f, x2) {
    let { base_: S, assigned_: g } = p, C = p.copy_;
    C.length < S.length && ([S, C] = [C, S], [f, x2] = [x2, f]);
    for (let y = 0; y < S.length; y++)
      if (g[y] && C[y] !== S[y]) {
        let A = d.concat([y]);
        f.push({ op: t, path: A, value: m(C[y]) }), x2.push({ op: t, path: A, value: m(S[y]) });
      }
    for (let y = S.length; y < C.length; y++) {
      let A = d.concat([y]);
      f.push({ op: r, path: A, value: m(C[y]) });
    }
    for (let y = C.length - 1; S.length <= y; --y) {
      let A = d.concat([y]);
      x2.push({ op: n, path: A });
    }
  }
  function i(p, d, f, x2) {
    let { base_: S, copy_: g } = p;
    es(p.assigned_, (C, y) => {
      let A = _p(S, C), I = _p(g, C), v = y ? ts(S, C) ? t : r : n;
      if (A === I && v === t)
        return;
      let R = d.concat(C);
      f.push(v === n ? { op: v, path: R } : { op: v, path: R, value: I }), x2.push(v === r ? { op: n, path: R } : v === n ? { op: r, path: R, value: m(A) } : { op: t, path: R, value: m(A) });
    });
  }
  function s(p, d, f, x2) {
    let { base_: S, copy_: g } = p, C = 0;
    S.forEach((y) => {
      if (!g.has(y)) {
        let A = d.concat([C]);
        f.push({ op: n, path: A, value: y }), x2.unshift({ op: r, path: A, value: y });
      }
      C++;
    }), C = 0, g.forEach((y) => {
      if (!S.has(y)) {
        let A = d.concat([C]);
        f.push({ op: r, path: A, value: y }), x2.unshift({ op: n, path: A, value: y });
      }
      C++;
    });
  }
  function c(p, d, f, x2) {
    f.push({ op: t, path: [], value: d === Jp ? void 0 : d }), x2.push({ op: t, path: [], value: p });
  }
  function u(p, d) {
    return d.forEach((f) => {
      let { path: x2, op: S } = f, g = p;
      for (let I = 0; I < x2.length - 1; I++) {
        let v = Hn(g), R = x2[I];
        typeof R != "string" && typeof R != "number" && (R = "" + R), (v === 0 || v === 1) && (R === "__proto__" || R === "constructor") && De(19), typeof g == "function" && R === "prototype" && De(19), g = _p(g, R), typeof g != "object" && De(18, x2.join("/"));
      }
      let C = Hn(g), y = l(f.value), A = x2[x2.length - 1];
      switch (S) {
        case t:
          switch (C) {
            case 2:
              return g.set(A, y);
            case 3:
              De(16);
            default:
              return g[A] = y;
          }
        case r:
          switch (C) {
            case 1:
              return A === "-" ? g.push(y) : g.splice(A, 0, y);
            case 2:
              return g.set(A, y);
            case 3:
              return g.add(y);
            default:
              return g[A] = y;
          }
        case n:
          switch (C) {
            case 1:
              return g.splice(A, 1);
            case 2:
              return g.delete(A);
            case 3:
              return g.delete(f.value);
            default:
              return delete g[A];
          }
        default:
          De(17, S);
      }
    }), p;
  }
  function l(p) {
    if (!He(p))
      return p;
    if (Array.isArray(p))
      return p.map(l);
    if (os(p))
      return new Map(Array.from(p.entries()).map(([f, x2]) => [f, l(x2)]));
    if (as(p))
      return new Set(Array.from(p).map(l));
    let d = Object.create(Wn(p));
    for (let f in p)
      d[f] = l(p[f]);
    return ts(p, Zi) && (d[Zi] = p[Zi]), d;
  }
  function m(p) {
    return tt(p) ? l(p) : p;
  }
  iP("Patches", { applyPatches_: u, generatePatches_: o, generateReplacementPatches_: c });
}
var rt = new dP();
var vr = rt.produce;
var Mc = rt.produceWithPatches.bind(rt);
rt.setAutoFreeze.bind(rt);
rt.setUseStrictShallowCopy.bind(rt);
var em = rt.applyPatches.bind(rt);
rt.createDraft.bind(rt);
rt.finishDraft.bind(rt);
function pP(e7, t = `expected a function, instead received ${typeof e7}`) {
  if (typeof e7 != "function")
    throw new TypeError(t);
}
function mP(e7, t = `expected an object, instead received ${typeof e7}`) {
  if (typeof e7 != "object")
    throw new TypeError(t);
}
function fP(e7, t = "expected all items to be functions, instead received the following types: ") {
  if (!e7.every((r) => typeof r == "function")) {
    let r = e7.map((n) => typeof n == "function" ? `function ${n.name || "unnamed"}()` : typeof n).join(", ");
    throw new TypeError(`${t}[${r}]`);
  }
}
var _S = (e7) => Array.isArray(e7) ? e7 : [e7];
function gP(e7) {
  let t = Array.isArray(e7[0]) ? e7[0] : e7;
  return fP(t, "createSelector expects all input-selectors to be functions, but received the following types: "), t;
}
function SP(e7, t) {
  let r = [], { length: n } = e7;
  for (let o = 0; o < n; o++)
    r.push(e7[o].apply(null, t));
  return r;
}
var hP = class {
  constructor(e7) {
    this.value = e7;
  }
  deref() {
    return this.value;
  }
};
var yP = typeof WeakRef < "u" ? WeakRef : hP;
var CP = 0;
var jS = 1;
function Qc() {
  return { s: CP, v: void 0, o: null, p: null };
}
function No(e7, t = {}) {
  let r = Qc(), { resultEqualityCheck: n } = t, o, a = 0;
  function i() {
    let s = r, { length: c } = arguments;
    for (let m = 0, p = c; m < p; m++) {
      let d = arguments[m];
      if (typeof d == "function" || typeof d == "object" && d !== null) {
        let f = s.o;
        f === null && (s.o = f = /* @__PURE__ */ new WeakMap());
        let x2 = f.get(d);
        x2 === void 0 ? (s = Qc(), f.set(d, s)) : s = x2;
      } else {
        let f = s.p;
        f === null && (s.p = f = /* @__PURE__ */ new Map());
        let x2 = f.get(d);
        x2 === void 0 ? (s = Qc(), f.set(d, s)) : s = x2;
      }
    }
    let u = s, l;
    if (s.s === jS)
      l = s.v;
    else if (l = e7.apply(null, arguments), a++, n) {
      let m = o?.deref?.() ?? o;
      m != null && n(m, l) && (l = m, a !== 0 && a--), o = typeof l == "object" && l !== null || typeof l == "function" ? new yP(l) : l;
    }
    return u.s = jS, u.v = l, l;
  }
  return i.clearCache = () => {
    r = Qc(), i.resetResultsCount();
  }, i.resultsCount = () => a, i.resetResultsCount = () => {
    a = 0;
  }, i;
}
function $S(e7, ...t) {
  let r = typeof e7 == "function" ? { memoize: e7, memoizeOptions: t } : e7, n = (...o) => {
    let a = 0, i = 0, s, c = {}, u = o.pop();
    typeof u == "object" && (c = u, u = o.pop()), pP(u, `createSelector expects an output function after the inputs, but received: [${typeof u}]`);
    let l = { ...r, ...c }, { memoize: m, memoizeOptions: p = [], argsMemoize: d = No, argsMemoizeOptions: f = [] } = l, S = _S(p), g = _S(f), C = gP(o), y = m(function() {
      return a++, u.apply(null, arguments);
    }, ...S), I = d(function() {
      i++;
      let R = SP(C, arguments);
      return s = y.apply(null, R), s;
    }, ...g);
    return Object.assign(I, { resultFunc: u, memoizedResultFunc: y, dependencies: C, dependencyRecomputations: () => i, resetDependencyRecomputations: () => {
      i = 0;
    }, lastResult: () => s, recomputations: () => a, resetRecomputations: () => {
      a = 0;
    }, memoize: m, argsMemoize: d });
  };
  return Object.assign(n, { withTypes: () => n }), n;
}
var Y = $S(No);
var xP = Object.assign((e7, t = Y) => {
  mP(e7, `createStructuredSelector expects first argument to be an object where each property is a selector, instead received a ${typeof e7}`);
  let r = Object.keys(e7), n = r.map((a) => e7[a]);
  return t(n, (...a) => a.reduce((i, s, c) => (i[r[c]] = s, i), {}));
}, { withTypes: () => xP });
var FP = (e7) => e7 && typeof e7.match == "function";
function h2(e7, t) {
  function r(...n) {
    if (t) {
      let o = t(...n);
      if (!o)
        throw new Error(Pt(0));
      return { type: e7, payload: o.payload, ..."meta" in o && { meta: o.meta }, ..."error" in o && { error: o.error } };
    }
    return { type: e7, payload: n[0] };
  }
  return r.toString = () => `${e7}`, r.type = e7, r.match = (n) => Oc(n) && n.type === e7, r;
}
function zS(e7) {
  return He(e7) ? vr(e7, () => {
  }) : e7;
}
function KS(e7, t, r) {
  return e7.has(t) ? e7.get(t) : e7.set(t, r(t)).get(t);
}
var ss = "RTK_autoBatch";
var Qo = () => (e7) => ({ payload: e7, meta: { [ss]: true } });
function eh(e7) {
  let t = {}, r = [], n, o = { addCase(a, i) {
    let s = typeof a == "string" ? a : a.type;
    if (!s)
      throw new Error(Pt(28));
    if (s in t)
      throw new Error(Pt(29));
    return t[s] = i, o;
  }, addMatcher(a, i) {
    return r.push({ matcher: a, reducer: i }), o;
  }, addDefaultCase(a) {
    return n = a, o;
  } };
  return e7(o), [t, r, n];
}
function wP(e7) {
  return typeof e7 == "function";
}
function $(e7, t) {
  let [r, n, o] = eh(t), a;
  if (wP(e7))
    a = () => zS(e7());
  else {
    let s = zS(e7);
    a = () => s;
  }
  function i(s = a(), c) {
    let u = [r[c.type], ...n.filter(({ matcher: l }) => l(c)).map(({ reducer: l }) => l)];
    return u.filter((l) => !!l).length === 0 && (u = [o]), u.reduce((l, m) => {
      if (m)
        if (tt(l)) {
          let d = m(l, c);
          return d === void 0 ? l : d;
        } else {
          if (He(l))
            return vr(l, (p) => m(p, c));
          {
            let p = m(l, c);
            if (p === void 0) {
              if (l === null)
                return l;
              throw Error("A case reducer on a non-draftable value must not return undefined");
            }
            return p;
          }
        }
      return l;
    }, s);
  }
  return i.getInitialState = a, i;
}
var th = (e7, t) => FP(e7) ? e7.match(t) : e7(t);
function Mt(...e7) {
  return (t) => e7.some((r) => th(r, t));
}
function Mo(...e7) {
  return (t) => e7.every((r) => th(r, t));
}
function Bc(e7, t) {
  if (!e7 || !e7.meta)
    return false;
  let r = typeof e7.meta.requestId == "string", n = t.indexOf(e7.meta.requestStatus) > -1;
  return r && n;
}
function cs(e7) {
  return typeof e7[0] == "function" && "pending" in e7[0] && "fulfilled" in e7[0] && "rejected" in e7[0];
}
function Uc(...e7) {
  return e7.length === 0 ? (t) => Bc(t, ["pending"]) : cs(e7) ? Mt(...e7.map((t) => t.pending)) : Uc()(e7[0]);
}
function Kn(...e7) {
  return e7.length === 0 ? (t) => Bc(t, ["rejected"]) : cs(e7) ? Mt(...e7.map((t) => t.rejected)) : Kn()(e7[0]);
}
function us(...e7) {
  let t = (r) => r && r.meta && r.meta.rejectedWithValue;
  return e7.length === 0 ? Mo(Kn(...e7), t) : cs(e7) ? Mo(Kn(...e7), t) : us()(e7[0]);
}
function Pr(...e7) {
  return e7.length === 0 ? (t) => Bc(t, ["fulfilled"]) : cs(e7) ? Mt(...e7.map((t) => t.fulfilled)) : Pr()(e7[0]);
}
function _c(...e7) {
  return e7.length === 0 ? (t) => Bc(t, ["pending", "fulfilled", "rejected"]) : cs(e7) ? Mt(...e7.flatMap((t) => [t.pending, t.rejected, t.fulfilled])) : _c()(e7[0]);
}
var IP = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW";
var jc = (e7 = 21) => {
  let t = "", r = e7;
  for (; r--; )
    t += IP[Math.random() * 64 | 0];
  return t;
};
var EP = ["name", "message", "stack", "code"];
var tm = class {
  constructor(e7, t) {
    Ce(this, "_type");
    this.payload = e7, this.meta = t;
  }
};
var JS = class {
  constructor(e7, t) {
    Ce(this, "_type");
    this.payload = e7, this.meta = t;
  }
};
var TP = (e7) => {
  if (typeof e7 == "object" && e7 !== null) {
    let t = {};
    for (let r of EP)
      typeof e7[r] == "string" && (t[r] = e7[r]);
    return t;
  }
  return { message: String(e7) };
};
var W = (() => {
  function e7(t, r, n) {
    let o = h2(t + "/fulfilled", (c, u, l, m) => ({ payload: c, meta: { ...m || {}, arg: l, requestId: u, requestStatus: "fulfilled" } })), a = h2(t + "/pending", (c, u, l) => ({ payload: void 0, meta: { ...l || {}, arg: u, requestId: c, requestStatus: "pending" } })), i = h2(t + "/rejected", (c, u, l, m, p) => ({ payload: m, error: (n && n.serializeError || TP)(c || "Rejected"), meta: { ...p || {}, arg: l, requestId: u, rejectedWithValue: !!m, requestStatus: "rejected", aborted: c?.name === "AbortError", condition: c?.name === "ConditionError" } }));
    function s(c) {
      return (u, l, m) => {
        let p = n?.idGenerator ? n.idGenerator(c) : jc(), d = new AbortController(), f, x2;
        function S(C) {
          x2 = C, d.abort();
        }
        let g = async function() {
          let C;
          try {
            let A = n?.condition?.(c, { getState: l, extra: m });
            if (OP(A) && (A = await A), A === false || d.signal.aborted)
              throw { name: "ConditionError", message: "Aborted due to condition callback returning false." };
            let I = new Promise((v, R) => {
              f = () => {
                R({ name: "AbortError", message: x2 || "Aborted" });
              }, d.signal.addEventListener("abort", f);
            });
            u(a(p, c, n?.getPendingMeta?.({ requestId: p, arg: c }, { getState: l, extra: m }))), C = await Promise.race([I, Promise.resolve(r(c, { dispatch: u, getState: l, extra: m, requestId: p, signal: d.signal, abort: S, rejectWithValue: (v, R) => new tm(v, R), fulfillWithValue: (v, R) => new JS(v, R) })).then((v) => {
              if (v instanceof tm)
                throw v;
              return v instanceof JS ? o(v.payload, p, c, v.meta) : o(v, p, c);
            })]);
          } catch (A) {
            C = A instanceof tm ? i(null, p, c, A.payload, A.meta) : i(A, p, c);
          } finally {
            f && d.signal.removeEventListener("abort", f);
          }
          return n && !n.dispatchConditionRejection && i.match(C) && C.meta.condition || u(C), C;
        }();
        return Object.assign(g, { abort: S, requestId: p, arg: c, unwrap() {
          return g.then(kP);
        } });
      };
    }
    return Object.assign(s, { pending: a, rejected: i, fulfilled: o, settled: Mt(i, o), typePrefix: t });
  }
  return e7.withTypes = () => e7, e7;
})();
function kP(e7) {
  if (e7.meta && e7.meta.rejectedWithValue)
    throw e7.payload;
  if (e7.error)
    throw e7.error;
  return e7.payload;
}
function OP(e7) {
  return e7 !== null && typeof e7 == "object" && typeof e7.then == "function";
}
var rh = Symbol.for("rtk-slice-createasyncthunk");
function qP(e7, t) {
  return `${e7}/${t}`;
}
function DP({ creators: e7 } = {}) {
  let t = e7?.asyncThunk?.[rh];
  return function(n) {
    let { name: o, reducerPath: a = o } = n;
    if (!o)
      throw new Error(Pt(11));
    let i = (typeof n.reducers == "function" ? n.reducers(NP()) : n.reducers) || {}, s = Object.keys(i), c = { sliceCaseReducersByName: {}, sliceCaseReducersByType: {}, actionCreators: {}, sliceMatchers: [] }, u = { addCase(C, y) {
      let A = typeof C == "string" ? C : C.type;
      if (!A)
        throw new Error(Pt(12));
      if (A in c.sliceCaseReducersByType)
        throw new Error(Pt(13));
      return c.sliceCaseReducersByType[A] = y, u;
    }, addMatcher(C, y) {
      return c.sliceMatchers.push({ matcher: C, reducer: y }), u;
    }, exposeAction(C, y) {
      return c.actionCreators[C] = y, u;
    }, exposeCaseReducer(C, y) {
      return c.sliceCaseReducersByName[C] = y, u;
    } };
    s.forEach((C) => {
      let y = i[C], A = { reducerName: C, type: qP(o, C), createNotation: typeof n.reducers == "function" };
      QP(y) ? BP(A, y, u, t) : MP(A, y, u);
    });
    function l() {
      let [C = {}, y = [], A = void 0] = typeof n.extraReducers == "function" ? eh(n.extraReducers) : [n.extraReducers], I = { ...C, ...c.sliceCaseReducersByType };
      return $(n.initialState, (v) => {
        for (let R in I)
          v.addCase(R, I[R]);
        for (let R of c.sliceMatchers)
          v.addMatcher(R.matcher, R.reducer);
        for (let R of y)
          v.addMatcher(R.matcher, R.reducer);
        A && v.addDefaultCase(A);
      });
    }
    let m = (C) => C, p = /* @__PURE__ */ new Map(), d;
    function f(C, y) {
      return d || (d = l()), d(C, y);
    }
    function x2() {
      return d || (d = l()), d.getInitialState();
    }
    function S(C, y = false) {
      function A(v) {
        let R = v[C];
        return typeof R > "u" && y && (R = x2()), R;
      }
      function I(v = m) {
        let R = KS(p, y, () => /* @__PURE__ */ new WeakMap());
        return KS(R, v, () => {
          let b = {};
          for (let [P, T] of Object.entries(n.selectors ?? {}))
            b[P] = VP(T, v, x2, y);
          return b;
        });
      }
      return { reducerPath: C, getSelectors: I, get selectors() {
        return I(A);
      }, selectSlice: A };
    }
    let g = { name: o, reducer: f, actions: c.actionCreators, caseReducers: c.sliceCaseReducersByName, getInitialState: x2, ...S(a), injectInto(C, { reducerPath: y, ...A } = {}) {
      let I = y ?? a;
      return C.inject({ reducerPath: I, reducer: f }, A), { ...g, ...S(I, true) };
    } };
    return g;
  };
}
function VP(e7, t, r, n) {
  function o(a, ...i) {
    let s = t(a);
    return typeof s > "u" && n && (s = r()), e7(s, ...i);
  }
  return o.unwrapped = e7, o;
}
var Yn = DP();
function NP() {
  function e7(t, r) {
    return { _reducerDefinitionType: "asyncThunk", payloadCreator: t, ...r };
  }
  return e7.withTypes = () => e7, { reducer(t) {
    return Object.assign({ [t.name](...r) {
      return t(...r);
    } }[t.name], { _reducerDefinitionType: "reducer" });
  }, preparedReducer(t, r) {
    return { _reducerDefinitionType: "reducerWithPrepare", prepare: t, reducer: r };
  }, asyncThunk: e7 };
}
function MP({ type: e7, reducerName: t, createNotation: r }, n, o) {
  let a, i;
  if ("reducer" in n) {
    if (r && !LP(n))
      throw new Error(Pt(17));
    a = n.reducer, i = n.prepare;
  } else
    a = n;
  o.addCase(e7, a).exposeCaseReducer(t, a).exposeAction(t, i ? h2(e7, i) : h2(e7));
}
function QP(e7) {
  return e7._reducerDefinitionType === "asyncThunk";
}
function LP(e7) {
  return e7._reducerDefinitionType === "reducerWithPrepare";
}
function BP({ type: e7, reducerName: t }, r, n, o) {
  if (!o)
    throw new Error(Pt(18));
  let { payloadCreator: a, fulfilled: i, pending: s, rejected: c, settled: u, options: l } = r, m = o(e7, a, l);
  n.exposeAction(t, m), i && n.addCase(m.fulfilled, i), s && n.addCase(m.pending, s), c && n.addCase(m.rejected, c), u && n.addMatcher(m.settled, u), n.exposeCaseReducer(t, { fulfilled: i || Lc, pending: s || Lc, rejected: c || Lc, settled: u || Lc });
}
function Lc() {
}
var { assign: ih } = Object;
var rm = "listenerMiddleware";
var UP = ih(h2(`${rm}/add`), { withTypes: () => UP });
h2(`${rm}/removeAll`);
var _P = ih(h2(`${rm}/remove`), { withTypes: () => _P });
function Pt(e7) {
  return `Minified Redux Toolkit error #${e7}; visit https://redux-toolkit.js.org/Errors?code=${e7} for the full message or use the non-minified dev environment for full errors. `;
}
function jP({ config: e7, environment: t, event: r, listenerManager: n }) {
  let { url: o, token: a, mode: i } = e7;
  i !== "disabled" && (n.call(r), t.send(o, a, r));
}
var $P = /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|00000000-0000-0000-0000-000000000000|ffffffff-ffff-ffff-ffff-ffffffffffff)$/i;
function GP(e7) {
  return typeof e7 == "string" && $P.test(e7);
}
var Ve = [];
for (let e7 = 0; e7 < 256; ++e7)
  Ve.push((e7 + 256).toString(16).slice(1));
function WP(e7, t = 0) {
  return (Ve[e7[t + 0]] + Ve[e7[t + 1]] + Ve[e7[t + 2]] + Ve[e7[t + 3]] + "-" + Ve[e7[t + 4]] + Ve[e7[t + 5]] + "-" + Ve[e7[t + 6]] + Ve[e7[t + 7]] + "-" + Ve[e7[t + 8]] + Ve[e7[t + 9]] + "-" + Ve[e7[t + 10]] + Ve[e7[t + 11]] + Ve[e7[t + 12]] + Ve[e7[t + 13]] + Ve[e7[t + 14]] + Ve[e7[t + 15]]).toLowerCase();
}
var nm;
var HP = new Uint8Array(16);
function zP() {
  if (!nm) {
    if (typeof crypto > "u" || !crypto.getRandomValues)
      throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");
    nm = crypto.getRandomValues.bind(crypto);
  }
  return nm(HP);
}
var KP = typeof crypto < "u" && crypto.randomUUID && crypto.randomUUID.bind(crypto);
var sh = { randomUUID: KP };
function YP(e7, t, r) {
  if (sh.randomUUID && !e7)
    return sh.randomUUID();
  e7 = e7 || {};
  let n = e7.random ?? e7.rng?.() ?? zP();
  if (n.length < 16)
    throw new Error("Random bytes length must be >= 16");
  return n[6] = n[6] & 15 | 64, n[8] = n[8] & 63 | 128, WP(n);
}
function JP(e7) {
  return { getClientId: () => {
    let t = "visitorId", r = e7.get(), n = r.storage, o = n.getItem(t), a = o && GP(o) ? o : r.generateUUID();
    return n.setItem(t, a), a;
  } };
}
var uh = "1.0.0";
function XP(e7) {
  let { trackingId: t } = e7;
  return { trackingId: t };
}
function ZP(e7) {
  return (e7.source || []).concat([`relay@${uh}`]);
}
function lh(e7, t, r, n) {
  let { getReferrer: o, getLocation: a, getUserAgent: i } = r, s = XP(t), c = n.getClientId();
  return Object.freeze({ type: e7, config: s, ts: Date.now(), source: ZP(t), clientId: c, userAgent: i(), referrer: o(), location: a() });
}
function ew(e7, t, r, n, o) {
  return { ...t, meta: lh(e7, r, n, o) };
}
var tw = "*";
function rw() {
  let e7 = [];
  function t({ type: c, callback: u }) {
    return e7.findIndex((l) => l.type === c && l.callback === u);
  }
  function r(c, u) {
    return c.type === "*" || u === c.type;
  }
  function n(c) {
    return t(c) < 0 && e7.push(c), () => s(c.type, c.callback);
  }
  function o(c) {
    e7.forEach((u) => {
      if (r(u, c.meta.type))
        try {
          u.callback(c);
        } catch (l) {
          console.error(l);
        }
    });
  }
  function a(c) {
    if (c === tw)
      e7.length = 0;
    else
      for (let u = e7.length - 1; u >= 0; u--)
        e7[u].type === c && e7.splice(u, 1);
  }
  function i(c) {
    let u = t(c);
    u >= 0 && e7.splice(u, 1);
  }
  function s(c, u) {
    u ? i({ type: c, callback: u }) : a(c);
  }
  return { add: n, call: o, remove: s };
}
function ch({ url: e7, token: t, trackingId: r, ...n }) {
  return Object.freeze({ url: e7, token: t, trackingId: r, ...!!n.mode && { mode: n.mode }, ...!!n.source && { source: n.source } });
}
function nw(e7) {
  let t = ch(e7);
  return { get: () => t, update: (r) => {
    t = ch({ ...t, ...r });
  } };
}
function ow() {
  let e7 = typeof window < "u";
  return { sendMessage(t) {
    e7 && window.postMessage(t, "*");
  } };
}
var om = aw();
function aw() {
  let e7 = "coveo_", t = (r) => {
    let n = r.split(".").slice(-2);
    return n.length == 2 ? n.join(".") : "";
  };
  return { getItem(r) {
    let n = `${e7}${r}=`, o = document.cookie.split(";");
    for (let a of o) {
      let i = a.replace(/^\s+/, "");
      if (i.lastIndexOf(n, 0) === 0)
        return i.substring(n.length, i.length);
    }
    return null;
  }, setItem(r, n, o) {
    let a = t(window.location.hostname), i = `;expires=${new Date((/* @__PURE__ */ new Date()).getTime() + o).toUTCString()}`, s = a ? `;domain=${a}` : "";
    document.cookie = `${e7}${r}=${n}${i}${s};path=/;SameSite=Lax`;
  }, removeItem(r) {
    this.setItem(r, "", -1);
  } };
}
function iw() {
  return { getItem(e7) {
    return om.getItem(e7) || localStorage.getItem(e7);
  }, removeItem(e7) {
    om.removeItem(e7), localStorage.removeItem(e7);
  }, setItem(e7, t) {
    localStorage.setItem(e7, t), om.setItem(e7, t, 31556952e3);
  } };
}
function sw() {
  let e7 = document.referrer;
  return e7 === "" ? null : e7;
}
function cw() {
  return { runtime: "browser", send: (e7, t, r) => {
    let n = navigator.sendBeacon(`${e7}?access_token=${t}`, new Blob([JSON.stringify([r])], { type: "application/json" }));
    if (ow().sendMessage({ kind: "EVENT_PROTOCOL", event: r, url: e7, token: t }), !n)
      throw new Error("Failed to send the event(s) because the payload size exceeded the maximum allowed size (32 KB). Please contact support if the problem persists.");
  }, getReferrer: () => sw(), getLocation: () => window.location.href, getUserAgent: () => navigator.userAgent, generateUUID: () => YP(), storage: iw() };
}
function uw() {
  try {
    let e7 = "__storage_test__";
    return localStorage.setItem(e7, e7), localStorage.removeItem(e7), true;
  } catch (e7) {
    return e7 instanceof DOMException && e7.name === "QuotaExceededError" && localStorage && localStorage.length !== 0;
  }
}
function lw() {
  return { getItem() {
    return null;
  }, removeItem() {
  }, setItem() {
  } };
}
function dw() {
  return { runtime: "null", send: () => {
  }, getReferrer: () => null, getLocation: () => null, getUserAgent: () => null, generateUUID: () => "", storage: lw() };
}
function pw(e7) {
  return e7.get().mode !== "disabled" && mw() && uw() ? cw() : dw();
}
function mw() {
  try {
    return typeof window == "object";
  } catch {
    return false;
  }
}
function fw(e7) {
  return { get: () => Object.freeze(pw(e7)) };
}
function dh(e7) {
  let t = nw(e7), r = rw(), n = fw(t), o = JP(n);
  return { emit: (a, i) => {
    let s = t.get(), c = n.get(), u = ew(a, i, s, c, o);
    return jP({ config: s, environment: c, event: u, listenerManager: r });
  }, getMeta: (a) => lh(a, t.get(), n.get(), o), on: (a, i) => r.add({ type: a, callback: i }), off: (a, i) => r.remove(a, i), updateConfig: (a) => t.update(a), version: uh };
}
var Jn = "3.20.0";
var ph = ["@coveo/atomic", "@coveo/quantic"];
var Hr = Y((e7) => e7.source, (e7) => Object.entries(e7).map(([t, r]) => `${t}@${r}`).concat(`@coveo/headless@${Jn}`));
var Lo = Y((e7) => e7.configuration.organizationId, (e7) => e7.configuration.environment, (e7) => e7.configuration.accessToken, (e7) => e7.configuration.analytics, (e7) => Hr(e7.configuration.analytics), (e7, t, r, { trackingId: n, apiBaseUrl: o, enabled: a }, i) => dh({ mode: a ? "emit" : "disabled", url: o ?? Lp(e7, t), token: r, trackingId: n, source: i }));
function wr(e7, t) {
  var r = {};
  for (var n in e7)
    Object.prototype.hasOwnProperty.call(e7, n) && t.indexOf(n) < 0 && (r[n] = e7[n]);
  if (e7 != null && typeof Object.getOwnPropertySymbols == "function")
    for (var o = 0, n = Object.getOwnPropertySymbols(e7); o < n.length; o++)
      t.indexOf(n[o]) < 0 && Object.prototype.propertyIsEnumerable.call(e7, n[o]) && (r[n[o]] = e7[n[o]]);
  return r;
}
function w(e7, t, r, n) {
  function o(a) {
    return a instanceof r ? a : new r(function(i) {
      i(a);
    });
  }
  return new (r || (r = Promise))(function(a, i) {
    function s(l) {
      try {
        u(n.next(l));
      } catch (m) {
        i(m);
      }
    }
    function c(l) {
      try {
        u(n.throw(l));
      } catch (m) {
        i(m);
      }
    }
    function u(l) {
      l.done ? a(l.value) : o(l.value).then(s, c);
    }
    u((n = n.apply(e7, [])).next());
  });
}
var ne;
(function(e7) {
  e7.search = "search", e7.click = "click", e7.custom = "custom", e7.view = "view", e7.collect = "collect";
})(ne || (ne = {}));
function sm() {
  return typeof window < "u";
}
function xm() {
  return typeof navigator < "u";
}
function Bo() {
  return typeof document < "u";
}
function cm() {
  try {
    return typeof localStorage < "u";
  } catch {
    return false;
  }
}
function gw() {
  try {
    return typeof sessionStorage < "u";
  } catch {
    return false;
  }
}
function Ph() {
  return xm() && navigator.cookieEnabled;
}
var Sw = [ne.click, ne.custom, ne.search, ne.view];
var hw = (e7, t) => Sw.indexOf(e7) !== -1 ? Object.assign({ language: Bo() ? document.documentElement.lang : "unknown", userAgent: xm() ? navigator.userAgent : "unknown" }, t) : t;
var ps = class e {
  static set(t, r, n) {
    var o, a, i, s;
    n && (a = /* @__PURE__ */ new Date(), a.setTime(a.getTime() + n)), s = window.location.hostname, s.indexOf(".") === -1 ? mh(t, r, a) : (i = s.split("."), o = i[i.length - 2] + "." + i[i.length - 1], mh(t, r, a, o));
  }
  static get(t) {
    for (var r = t + "=", n = document.cookie.split(";"), o = 0; o < n.length; o++) {
      var a = n[o];
      if (a = a.replace(/^\s+/, ""), a.lastIndexOf(r, 0) === 0)
        return a.substring(r.length, a.length);
    }
    return null;
  }
  static erase(t) {
    e.set(t, "", -1);
  }
};
function mh(e7, t, r, n) {
  document.cookie = `${e7}=${t}` + (r ? `;expires=${r.toUTCString()}` : "") + (n ? `;domain=${n}` : "") + ";path=/;SameSite=Lax";
}
function yw() {
  return cm() ? localStorage : Ph() ? new ms() : gw() ? sessionStorage : new _o();
}
var ms = class e2 {
  getItem(t) {
    return ps.get(`${e2.prefix}${t}`);
  }
  removeItem(t) {
    ps.erase(`${e2.prefix}${t}`);
  }
  setItem(t, r, n) {
    ps.set(`${e2.prefix}${t}`, r, n);
  }
};
ms.prefix = "coveo_";
var um = class {
  constructor() {
    this.cookieStorage = new ms();
  }
  getItem(t) {
    return localStorage.getItem(t) || this.cookieStorage.getItem(t);
  }
  removeItem(t) {
    this.cookieStorage.removeItem(t), localStorage.removeItem(t);
  }
  setItem(t, r) {
    localStorage.setItem(t, r), this.cookieStorage.setItem(t, r, 31556926e3);
  }
};
var _o = class {
  getItem(t) {
    return null;
  }
  removeItem(t) {
  }
  setItem(t, r) {
  }
};
var ls = "__coveo.analytics.history";
var wh = 20;
var Ih = 1e3 * 60;
var Eh = 75;
var jo = class {
  constructor(t) {
    this.store = t || yw();
  }
  addElement(t) {
    t.internalTime = (/* @__PURE__ */ new Date()).getTime(), t = this.cropQueryElement(this.stripEmptyQuery(t));
    let r = this.getHistoryWithInternalTime();
    r != null ? this.isValidEntry(t) && this.setHistory([t].concat(r)) : this.setHistory([t]);
  }
  addElementAsync(t) {
    return w(this, void 0, void 0, function* () {
      t.internalTime = (/* @__PURE__ */ new Date()).getTime(), t = this.cropQueryElement(this.stripEmptyQuery(t));
      let r = yield this.getHistoryWithInternalTimeAsync();
      r != null ? this.isValidEntry(t) && this.setHistory([t].concat(r)) : this.setHistory([t]);
    });
  }
  getHistory() {
    let t = this.getHistoryWithInternalTime();
    return this.stripEmptyQueries(this.stripInternalTime(t));
  }
  getHistoryAsync() {
    return w(this, void 0, void 0, function* () {
      let t = yield this.getHistoryWithInternalTimeAsync();
      return this.stripEmptyQueries(this.stripInternalTime(t));
    });
  }
  getHistoryWithInternalTime() {
    try {
      let t = this.store.getItem(ls);
      return t && typeof t == "string" ? JSON.parse(t) : [];
    } catch {
      return [];
    }
  }
  getHistoryWithInternalTimeAsync() {
    return w(this, void 0, void 0, function* () {
      try {
        let t = yield this.store.getItem(ls);
        return t ? JSON.parse(t) : [];
      } catch {
        return [];
      }
    });
  }
  setHistory(t) {
    try {
      this.store.setItem(ls, JSON.stringify(t.slice(0, wh)));
    } catch {
    }
  }
  clear() {
    try {
      this.store.removeItem(ls);
    } catch {
    }
  }
  getMostRecentElement() {
    let t = this.getHistoryWithInternalTime();
    return Array.isArray(t) ? t.sort((n, o) => (o.internalTime || 0) - (n.internalTime || 0))[0] : null;
  }
  cropQueryElement(t) {
    return t.name && t.value && t.name.toLowerCase() === "query" && (t.value = t.value.slice(0, Eh)), t;
  }
  isValidEntry(t) {
    let r = this.getMostRecentElement();
    return r && r.value == t.value ? (t.internalTime || 0) - (r.internalTime || 0) > Ih : true;
  }
  stripInternalTime(t) {
    return Array.isArray(t) ? t.map((r) => {
      let { name: n, time: o, value: a } = r;
      return { name: n, time: o, value: a };
    }) : [];
  }
  stripEmptyQuery(t) {
    let { name: r, time: n, value: o } = t;
    return r && typeof o == "string" && r.toLowerCase() === "query" && o.trim() === "" ? { name: r, time: n } : t;
  }
  stripEmptyQueries(t) {
    return t.map((r) => this.stripEmptyQuery(r));
  }
};
var Th = Object.freeze({ __proto__: null, HistoryStore: jo, MAX_NUMBER_OF_HISTORY_ELEMENTS: wh, MAX_VALUE_SIZE: Eh, MIN_THRESHOLD_FOR_DUPLICATE_VALUE: Ih, STORE_KEY: ls, default: jo });
var Cw = (e7, t) => w(void 0, void 0, void 0, function* () {
  return e7 === ne.view ? (yield xw(t.contentIdValue), Object.assign({ location: window.location.toString(), referrer: document.referrer, title: document.title }, t)) : t;
});
var xw = (e7) => w(void 0, void 0, void 0, function* () {
  let t = new jo(), r = { name: "PageView", value: e7, time: (/* @__PURE__ */ new Date()).toISOString() };
  yield t.addElementAsync(r);
});
var $c;
var Aw = new Uint8Array(16);
function Fw() {
  if (!$c && ($c = typeof crypto < "u" && crypto.getRandomValues && crypto.getRandomValues.bind(crypto), !$c))
    throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");
  return $c(Aw);
}
var Rw = /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|00000000-0000-0000-0000-000000000000)$/i;
function Wc(e7) {
  return typeof e7 == "string" && Rw.test(e7);
}
var Ne = [];
for (let e7 = 0; e7 < 256; ++e7)
  Ne.push((e7 + 256).toString(16).slice(1));
function kh(e7, t = 0) {
  return (Ne[e7[t + 0]] + Ne[e7[t + 1]] + Ne[e7[t + 2]] + Ne[e7[t + 3]] + "-" + Ne[e7[t + 4]] + Ne[e7[t + 5]] + "-" + Ne[e7[t + 6]] + Ne[e7[t + 7]] + "-" + Ne[e7[t + 8]] + Ne[e7[t + 9]] + "-" + Ne[e7[t + 10]] + Ne[e7[t + 11]] + Ne[e7[t + 12]] + Ne[e7[t + 13]] + Ne[e7[t + 14]] + Ne[e7[t + 15]]).toLowerCase();
}
function bw(e7) {
  if (!Wc(e7))
    throw TypeError("Invalid UUID");
  let t, r = new Uint8Array(16);
  return r[0] = (t = parseInt(e7.slice(0, 8), 16)) >>> 24, r[1] = t >>> 16 & 255, r[2] = t >>> 8 & 255, r[3] = t & 255, r[4] = (t = parseInt(e7.slice(9, 13), 16)) >>> 8, r[5] = t & 255, r[6] = (t = parseInt(e7.slice(14, 18), 16)) >>> 8, r[7] = t & 255, r[8] = (t = parseInt(e7.slice(19, 23), 16)) >>> 8, r[9] = t & 255, r[10] = (t = parseInt(e7.slice(24, 36), 16)) / 1099511627776 & 255, r[11] = t / 4294967296 & 255, r[12] = t >>> 24 & 255, r[13] = t >>> 16 & 255, r[14] = t >>> 8 & 255, r[15] = t & 255, r;
}
function vw(e7) {
  e7 = unescape(encodeURIComponent(e7));
  let t = [];
  for (let r = 0; r < e7.length; ++r)
    t.push(e7.charCodeAt(r));
  return t;
}
var Pw = "6ba7b810-9dad-11d1-80b4-00c04fd430c8";
var ww = "6ba7b811-9dad-11d1-80b4-00c04fd430c8";
function Iw(e7, t, r) {
  function n(o, a, i, s) {
    var c;
    if (typeof o == "string" && (o = vw(o)), typeof a == "string" && (a = bw(a)), ((c = a) === null || c === void 0 ? void 0 : c.length) !== 16)
      throw TypeError("Namespace must be array-like (16 iterable integer values, 0-255)");
    let u = new Uint8Array(16 + o.length);
    if (u.set(a), u.set(o, a.length), u = r(u), u[6] = u[6] & 15 | t, u[8] = u[8] & 63 | 128, i) {
      s = s || 0;
      for (let l = 0; l < 16; ++l)
        i[s + l] = u[l];
      return i;
    }
    return kh(u);
  }
  try {
    n.name = e7;
  } catch {
  }
  return n.DNS = Pw, n.URL = ww, n;
}
var Ew = typeof crypto < "u" && crypto.randomUUID && crypto.randomUUID.bind(crypto);
var fh = { randomUUID: Ew };
function Xn(e7, t, r) {
  if (fh.randomUUID && true && !e7)
    return fh.randomUUID();
  e7 = e7 || {};
  let n = e7.random || (e7.rng || Fw)();
  if (n[6] = n[6] & 15 | 64, n[8] = n[8] & 63 | 128, t)
    ;
  return kh(n);
}
function Tw(e7, t, r, n) {
  switch (e7) {
    case 0:
      return t & r ^ ~t & n;
    case 1:
      return t ^ r ^ n;
    case 2:
      return t & r ^ t & n ^ r & n;
    case 3:
      return t ^ r ^ n;
  }
}
function am(e7, t) {
  return e7 << t | e7 >>> 32 - t;
}
function kw(e7) {
  let t = [1518500249, 1859775393, 2400959708, 3395469782], r = [1732584193, 4023233417, 2562383102, 271733878, 3285377520];
  if (typeof e7 == "string") {
    let i = unescape(encodeURIComponent(e7));
    e7 = [];
    for (let s = 0; s < i.length; ++s)
      e7.push(i.charCodeAt(s));
  } else
    Array.isArray(e7) || (e7 = Array.prototype.slice.call(e7));
  e7.push(128);
  let n = e7.length / 4 + 2, o = Math.ceil(n / 16), a = new Array(o);
  for (let i = 0; i < o; ++i) {
    let s = new Uint32Array(16);
    for (let c = 0; c < 16; ++c)
      s[c] = e7[i * 64 + c * 4] << 24 | e7[i * 64 + c * 4 + 1] << 16 | e7[i * 64 + c * 4 + 2] << 8 | e7[i * 64 + c * 4 + 3];
    a[i] = s;
  }
  a[o - 1][14] = (e7.length - 1) * 8 / Math.pow(2, 32), a[o - 1][14] = Math.floor(a[o - 1][14]), a[o - 1][15] = (e7.length - 1) * 8 & 4294967295;
  for (let i = 0; i < o; ++i) {
    let s = new Uint32Array(80);
    for (let d = 0; d < 16; ++d)
      s[d] = a[i][d];
    for (let d = 16; d < 80; ++d)
      s[d] = am(s[d - 3] ^ s[d - 8] ^ s[d - 14] ^ s[d - 16], 1);
    let c = r[0], u = r[1], l = r[2], m = r[3], p = r[4];
    for (let d = 0; d < 80; ++d) {
      let f = Math.floor(d / 20), x2 = am(c, 5) + Tw(f, u, l, m) + p + t[f] + s[d] >>> 0;
      p = m, m = l, l = am(u, 30) >>> 0, u = c, c = x2;
    }
    r[0] = r[0] + c >>> 0, r[1] = r[1] + u >>> 0, r[2] = r[2] + l >>> 0, r[3] = r[3] + m >>> 0, r[4] = r[4] + p >>> 0;
  }
  return [r[0] >> 24 & 255, r[0] >> 16 & 255, r[0] >> 8 & 255, r[0] & 255, r[1] >> 24 & 255, r[1] >> 16 & 255, r[1] >> 8 & 255, r[1] & 255, r[2] >> 24 & 255, r[2] >> 16 & 255, r[2] >> 8 & 255, r[2] & 255, r[3] >> 24 & 255, r[3] >> 16 & 255, r[3] >> 8 & 255, r[3] & 255, r[4] >> 24 & 255, r[4] >> 16 & 255, r[4] >> 8 & 255, r[4] & 255];
}
var Ow = Iw("v5", 80, kw);
var gh = Ow;
var Oh = "2.30.45";
var ds = { pageview: "pageview", event: "event" };
var zr = class e3 {
  constructor(t, r) {
    if (!Wc(t))
      throw Error("Not a valid uuid");
    this.clientId = t, this.creationDate = Math.floor(r / 1e3);
  }
  toString() {
    return this.clientId.replace(/-/g, "") + "." + this.creationDate.toString();
  }
  get expired() {
    let t = Math.floor(Date.now() / 1e3) - this.creationDate;
    return t < 0 || t > e3.expirationTime;
  }
  validate(t, r) {
    return !this.expired && this.matchReferrer(t, r);
  }
  matchReferrer(t, r) {
    try {
      let n = new URL(t);
      return r.some((o) => new RegExp(o.replace(/\\/g, "\\\\").replace(/\./g, "\\.").replace(/\*/g, ".*") + "$").test(n.host));
    } catch {
      return false;
    }
  }
  static fromString(t) {
    let r = t.split(".");
    if (r.length !== 2)
      return null;
    let [n, o] = r;
    if (n.length !== 32 || isNaN(parseInt(o)))
      return null;
    let a = n.substring(0, 8) + "-" + n.substring(8, 12) + "-" + n.substring(12, 16) + "-" + n.substring(16, 20) + "-" + n.substring(20, 32);
    return Wc(a) ? new e3(a, Number.parseInt(o) * 1e3) : null;
  }
};
zr.cvo_cid = "cvo_cid";
zr.expirationTime = 120;
var lt = Object.keys;
function Gc(e7) {
  return e7 !== null && typeof e7 == "object" && !Array.isArray(e7);
}
var im = 128;
var qh = 192;
var hh = 224;
var yh = 240;
function qw(e7) {
  return (e7 & 248) === yh ? 4 : (e7 & yh) === hh ? 3 : (e7 & hh) === qh ? 2 : 1;
}
function Dw(e7, t) {
  if (t < 0 || e7.length <= t)
    return e7;
  let r = e7.indexOf("%", t - 2);
  for (r < 0 || r > t ? r = t : t = r; r > 2 && e7.charAt(r - 3) == "%"; ) {
    let n = Number.parseInt(e7.substring(r - 2, r), 16);
    if ((n & im) != im)
      break;
    if (r -= 3, (n & qh) != im) {
      t - r >= qw(n) * 3 && (r = t);
      break;
    }
  }
  return e7.substring(0, r);
}
var pm = { id: "svc_ticket_id", subject: "svc_ticket_subject", description: "svc_ticket_description", category: "svc_ticket_category", productId: "svc_ticket_product_id", custom: "svc_ticket_custom" };
var Vw = lt(pm).map((e7) => pm[e7]);
var Nw = [...Vw].join("|");
var Mw = new RegExp(`^(${Nw}$)`);
var Qw = { svcAction: "svc_action", svcActionData: "svc_action_data" };
var Bw = (e7) => Mw.test(e7);
var Uw = [Bw];
var Ch = { id: "id", name: "nm", brand: "br", category: "ca", variant: "va", price: "pr", quantity: "qt", coupon: "cc", position: "ps", group: "group" };
var xh = { id: "id", name: "nm", brand: "br", category: "ca", variant: "va", position: "ps", price: "pr", group: "group" };
var Qe = { action: "pa", list: "pal", listSource: "pls" };
var zc = { id: "ti", revenue: "tr", tax: "tt", shipping: "ts", coupon: "tcc", affiliation: "ta", step: "cos", option: "col" };
var _w = ["loyaltyCardId", "loyaltyTier", "thirdPartyPersona", "companyName", "favoriteStore", "storeName", "userIndustry", "userRole", "userDepartment", "businessUnit"];
var mm = { id: "quoteId", affiliation: "quoteAffiliation" };
var fm = { id: "reviewId", rating: "reviewRating", comment: "reviewComment" };
var jw = { add: Qe, bookmark_add: Qe, bookmark_remove: Qe, click: Qe, checkout: Qe, checkout_option: Qe, detail: Qe, impression: Qe, remove: Qe, refund: Object.assign(Object.assign({}, Qe), zc), purchase: Object.assign(Object.assign({}, Qe), zc), quickview: Qe, quote: Object.assign(Object.assign({}, Qe), mm), review: Object.assign(Object.assign({}, Qe), fm) };
var $w = lt(Ch).map((e7) => Ch[e7]);
var Gw = lt(xh).map((e7) => xh[e7]);
var Ww = lt(Qe).map((e7) => Qe[e7]);
var Hw = lt(zc).map((e7) => zc[e7]);
var zw = lt(fm).map((e7) => fm[e7]);
var Kw = lt(mm).map((e7) => mm[e7]);
var Yw = [...$w, "custom"].join("|");
var Jw = [...Gw, "custom"].join("|");
var Dh = "(pr[0-9]+)";
var Vh = "(il[0-9]+pi[0-9]+)";
var Xw = new RegExp(`^${Dh}(${Yw})$`);
var Zw = new RegExp(`^(${Vh}(${Jw}))|(il[0-9]+nm)$`);
var eI = new RegExp(`^(${Ww.join("|")})$`);
var tI = new RegExp(`^(${Hw.join("|")})$`);
var rI = new RegExp(`^${Dh}custom$`);
var nI = new RegExp(`^${Vh}custom$`);
var oI = new RegExp(`^(${[..._w, ...zw, ...Kw].join("|")})$`);
var aI = (e7) => Xw.test(e7);
var iI = (e7) => Zw.test(e7);
var sI = (e7) => eI.test(e7);
var cI = (e7) => tI.test(e7);
var uI = (e7) => oI.test(e7);
var lI = [iI, aI, sI, cI, uI];
var dI = [rI, nI];
var pI = { anonymizeIp: "aip" };
var mI = { eventCategory: "ec", eventAction: "ea", eventLabel: "el", eventValue: "ev", page: "dp", visitorId: "cid", clientId: "cid", userId: "uid", currencyCode: "cu" };
var fI = { hitType: "t", pageViewId: "pid", encoding: "de", location: "dl", referrer: "dr", screenColor: "sd", screenResolution: "sr", title: "dt", userAgent: "ua", language: "ul", eventId: "z", time: "tm" };
var gI = ["contentId", "contentIdKey", "contentType", "searchHub", "tab", "searchUid", "permanentId", "contentLocale", "trackingId"];
var SI = Object.assign(Object.assign(Object.assign(Object.assign({}, pI), mI), fI), gI.reduce((e7, t) => Object.assign(Object.assign({}, e7), { [t]: t }), {}));
var gm = Object.assign(Object.assign({}, SI), Qw);
var hI = (e7) => {
  let t = !!e7.action && jw[e7.action] || {};
  return lt(e7).reduce((r, n) => {
    let o = t[n] || gm[n] || n;
    return Object.assign(Object.assign({}, r), { [o]: e7[n] });
  }, {});
};
var yI = lt(gm).map((e7) => gm[e7]);
var CI = (e7) => yI.indexOf(e7) !== -1;
var xI = (e7) => e7 === "custom";
var AI = (e7) => [...lI, ...Uw, CI, xI].some((t) => t(e7));
var FI = (e7) => lt(e7).reduce((t, r) => {
  let n = RI(r);
  return n ? Object.assign(Object.assign({}, t), bI(n, e7[r])) : Object.assign(Object.assign({}, t), { [r]: e7[r] });
}, {});
var RI = (e7) => {
  let t;
  return [...dI].every((r) => {
    var n;
    return t = (n = r.exec(e7)) === null || n === void 0 ? void 0 : n[1], !t;
  }), t;
};
var bI = (e7, t) => lt(t).reduce((r, n) => Object.assign(Object.assign({}, r), { [`${e7}${n}`]: t[n] }), {});
var Sm = class {
  constructor(t) {
    this.opts = t;
  }
  sendEvent(t, r) {
    return w(this, void 0, void 0, function* () {
      if (!this.isAvailable())
        throw new Error('navigator.sendBeacon is not supported in this browser. Consider adding a polyfill like "sendbeacon-polyfill".');
      let { baseUrl: n, preprocessRequest: o } = this.opts, a = yield this.getQueryParamsForEventType(t), { url: i, payload: s } = yield this.preProcessRequestAsPotentialJSONString(`${n}/analytics/${t}?${a}`, r, o), c = this.encodeForEventType(t, s), u = new Blob([c], { type: "application/x-www-form-urlencoded" });
      navigator.sendBeacon(i, u);
    });
  }
  isAvailable() {
    return "sendBeacon" in navigator;
  }
  deleteHttpCookieVisitorId() {
    return Promise.resolve();
  }
  preProcessRequestAsPotentialJSONString(t, r, n) {
    return w(this, void 0, void 0, function* () {
      let o = t, a = r;
      if (n) {
        let i = yield n({ url: t, body: JSON.stringify(r) }, "analyticsBeacon"), { url: s, body: c } = i;
        o = s || t;
        try {
          a = JSON.parse(c);
        } catch (u) {
          console.error("Unable to process the request body as a JSON string", u);
        }
      }
      return { payload: a, url: o };
    });
  }
  encodeForEventType(t, r) {
    return this.isEventTypeLegacy(t) ? this.encodeEventToJson(t, r) : this.encodeEventToJson(t, r, this.opts.token);
  }
  getQueryParamsForEventType(t) {
    return w(this, void 0, void 0, function* () {
      let { token: r, visitorIdProvider: n } = this.opts, o = yield n.getCurrentVisitorId();
      return [r && this.isEventTypeLegacy(t) ? `access_token=${r}` : "", o ? `visitorId=${o}` : "", "discardVisitInfo=true"].filter((a) => !!a).join("&");
    });
  }
  isEventTypeLegacy(t) {
    return [ne.click, ne.custom, ne.search, ne.view].indexOf(t) !== -1;
  }
  encodeEventToJson(t, r, n) {
    let o = `${t}Event=${encodeURIComponent(JSON.stringify(r))}`;
    return n && (o = `access_token=${encodeURIComponent(n)}&${o}`), o;
  }
};
var hm = class {
  sendEvent(t, r) {
    return w(this, void 0, void 0, function* () {
      return Promise.resolve();
    });
  }
  deleteHttpCookieVisitorId() {
    return w(this, void 0, void 0, function* () {
      return Promise.resolve();
    });
  }
};
var Ah = globalThis.fetch;
var Kc = class {
  constructor(t) {
    this.opts = t;
  }
  sendEvent(t, r) {
    return w(this, void 0, void 0, function* () {
      let { baseUrl: n, visitorIdProvider: o, preprocessRequest: a } = this.opts, i = this.shouldAppendVisitorId(t) ? yield this.getVisitorIdParam() : "", s = { url: `${n}/analytics/${t}${i}`, credentials: "include", mode: "cors", headers: this.getHeaders(), method: "POST", body: JSON.stringify(r) }, c = Object.assign(Object.assign({}, s), a ? yield a(s, "analyticsFetch") : {}), { url: u } = c, l = wr(c, ["url"]), m;
      try {
        m = yield Ah(u, l);
      } catch (p) {
        console.error("An error has occured when sending the event.", p);
        return;
      }
      if (m.ok) {
        let p = yield m.json();
        return p.visitorId && o.setCurrentVisitorId(p.visitorId), p;
      } else {
        try {
          m.json();
        } catch {
        }
        throw console.error(`An error has occured when sending the "${t}" event.`, m, r), new Error(`An error has occurred when sending the "${t}" event. Check the console logs for more details.`);
      }
    });
  }
  deleteHttpCookieVisitorId() {
    return w(this, void 0, void 0, function* () {
      let { baseUrl: t } = this.opts, r = `${t}/analytics/visit`;
      yield Ah(r, { headers: this.getHeaders(), method: "DELETE" });
    });
  }
  shouldAppendVisitorId(t) {
    return [ne.click, ne.custom, ne.search, ne.view].indexOf(t) !== -1;
  }
  getVisitorIdParam() {
    return w(this, void 0, void 0, function* () {
      let { visitorIdProvider: t } = this.opts, r = yield t.getCurrentVisitorId();
      return r ? `?visitor=${r}` : "";
    });
  }
  getHeaders() {
    let { token: t } = this.opts;
    return Object.assign(Object.assign({}, t ? { Authorization: `Bearer ${t}` } : {}), { "Content-Type": "application/json" });
  }
};
var ym = class {
  constructor(t, r) {
    cm() && Ph() ? this.storage = new um() : cm() ? this.storage = localStorage : (console.warn("BrowserRuntime detected no valid storage available.", this), this.storage = new _o()), this.client = new Kc(t), this.beaconClient = new Sm(t), window.addEventListener("beforeunload", () => {
      let n = r();
      for (let { eventType: o, payload: a } of n)
        this.beaconClient.sendEvent(o, a);
    });
  }
  getClientDependingOnEventType(t) {
    return t === "click" && this.beaconClient.isAvailable() ? this.beaconClient : this.client;
  }
};
var Cm = class {
  constructor(t, r) {
    this.storage = r || new _o(), this.client = new Kc(t);
  }
  getClientDependingOnEventType(t) {
    return this.client;
  }
};
var Yc = class {
  constructor() {
    this.storage = new _o(), this.client = new hm();
  }
  getClientDependingOnEventType(t) {
    return this.client;
  }
};
var vI = "xx";
var PI = (e7) => e7?.startsWith(vI) || false;
var wI = `
        We've detected you're using React Native but have not provided the corresponding runtime,
        for an optimal experience please use the "coveo.analytics/react-native" subpackage.
        Follow the Readme on how to set it up: https://github.com/coveo/coveo.analytics.js#using-react-native
    `;
function II() {
  return typeof navigator < "u" && navigator.product == "ReactNative";
}
var EI = ["1", 1, "yes", true];
function Jc() {
  let e7 = [];
  return sm() && e7.push(window.doNotTrack), xm() && e7.push(navigator.doNotTrack, navigator.msDoNotTrack, navigator.globalPrivacyControl), e7.some((t) => EI.indexOf(t) !== -1);
}
var Nh = "v15";
var Mh = { default: "https://analytics.cloud.coveo.com/rest/ua" };
function TI(e7 = Mh.default, t = Nh, r = false) {
  if (e7 = e7.replace(/\/$/, ""), r)
    return `${e7}/${t}`;
  let n = e7.endsWith("/rest") || e7.endsWith("/rest/ua");
  return `${e7}${n ? "" : "/rest"}/${t}`;
}
var kI = "38824e1f-37f5-42d3-8372-a4b8fa9df946";
var Qt = class {
  get defaultOptions() {
    return { endpoint: Mh.default, isCustomEndpoint: false, token: "", version: Nh, beforeSendHooks: [], afterSendHooks: [] };
  }
  get version() {
    return Oh;
  }
  constructor(t) {
    if (this.acceptedLinkReferrers = [], !t)
      throw new Error("You have to pass options to this constructor");
    this.options = Object.assign(Object.assign({}, this.defaultOptions), t), this.visitorId = "", this.bufferedRequests = [], this.beforeSendHooks = [Cw, hw].concat(this.options.beforeSendHooks), this.afterSendHooks = this.options.afterSendHooks, this.eventTypeMapping = {};
    let r = { baseUrl: this.baseUrl, token: this.options.token, visitorIdProvider: this, preprocessRequest: this.options.preprocessRequest };
    Jc() ? this.runtime = new Yc() : this.runtime = this.options.runtimeEnvironment || this.initRuntime(r), this.addEventTypeMapping(ne.view, { newEventType: ne.view, addClientIdParameter: true }), this.addEventTypeMapping(ne.click, { newEventType: ne.click, addClientIdParameter: true }), this.addEventTypeMapping(ne.custom, { newEventType: ne.custom, addClientIdParameter: true }), this.addEventTypeMapping(ne.search, { newEventType: ne.search, addClientIdParameter: true });
  }
  initRuntime(t) {
    return sm() && Bo() ? new ym(t, () => {
      let r = [...this.bufferedRequests];
      return this.bufferedRequests = [], r;
    }) : (II() && console.warn(wI), new Cm(t));
  }
  get storage() {
    return this.runtime.storage;
  }
  determineVisitorId() {
    return w(this, void 0, void 0, function* () {
      try {
        return sm() && this.extractClientIdFromLink(window.location.href) || (yield this.storage.getItem("visitorId")) || Xn();
      } catch (t) {
        return console.log("Could not get visitor ID from the current runtime environment storage. Using a random ID instead.", t), Xn();
      }
    });
  }
  getCurrentVisitorId() {
    return w(this, void 0, void 0, function* () {
      if (!this.visitorId) {
        let t = yield this.determineVisitorId();
        yield this.setCurrentVisitorId(t);
      }
      return this.visitorId;
    });
  }
  setCurrentVisitorId(t) {
    return w(this, void 0, void 0, function* () {
      this.visitorId = t, yield this.storage.setItem("visitorId", t);
    });
  }
  setClientId(t, r) {
    return w(this, void 0, void 0, function* () {
      if (Wc(t))
        this.setCurrentVisitorId(t.toLowerCase());
      else {
        if (!r)
          throw Error("Cannot generate uuid client id without a specific namespace string.");
        this.setCurrentVisitorId(gh(t, gh(r, kI)));
      }
    });
  }
  getParameters(t, ...r) {
    return w(this, void 0, void 0, function* () {
      return yield this.resolveParameters(t, ...r);
    });
  }
  getPayload(t, ...r) {
    return w(this, void 0, void 0, function* () {
      let n = yield this.resolveParameters(t, ...r);
      return yield this.resolvePayloadForParameters(t, n);
    });
  }
  get currentVisitorId() {
    return typeof (this.visitorId || this.storage.getItem("visitorId")) != "string" && this.setCurrentVisitorId(Xn()), this.visitorId;
  }
  set currentVisitorId(t) {
    this.visitorId = t, this.storage.setItem("visitorId", t);
  }
  extractClientIdFromLink(t) {
    if (Jc())
      return null;
    try {
      let r = new URL(t).searchParams.get(zr.cvo_cid);
      if (r == null)
        return null;
      let n = zr.fromString(r);
      return !n || !Bo() || !n.validate(document.referrer, this.acceptedLinkReferrers) ? null : n.clientId;
    } catch {
    }
    return null;
  }
  resolveParameters(t, ...r) {
    return w(this, void 0, void 0, function* () {
      let { variableLengthArgumentsNames: n = [], addVisitorIdParameter: o = false, usesMeasurementProtocol: a = false, addClientIdParameter: i = false } = this.eventTypeMapping[t] || {};
      return yield [(d) => n.length > 0 ? this.parseVariableArgumentsPayload(n, d) : d[0], (d) => w(this, void 0, void 0, function* () {
        return Object.assign(Object.assign({}, d), { visitorId: o ? yield this.getCurrentVisitorId() : "" });
      }), (d) => w(this, void 0, void 0, function* () {
        return i ? Object.assign(Object.assign({}, d), { clientId: yield this.getCurrentVisitorId() }) : d;
      }), (d) => a ? this.ensureAnonymousUserWhenUsingApiKey(d) : d, (d) => this.beforeSendHooks.reduce((f, x2) => w(this, void 0, void 0, function* () {
        let S = yield f;
        return yield x2(t, S);
      }), d)].reduce((d, f) => w(this, void 0, void 0, function* () {
        let x2 = yield d;
        return yield f(x2);
      }), Promise.resolve(r));
    });
  }
  resolvePayloadForParameters(t, r) {
    return w(this, void 0, void 0, function* () {
      let { usesMeasurementProtocol: n = false } = this.eventTypeMapping[t] || {};
      return yield [(m) => this.setTrackingIdIfTrackingIdNotPresent(m), (m) => this.removeEmptyPayloadValues(m, t), (m) => this.validateParams(m, t), (m) => n ? hI(m) : m, (m) => n ? this.removeUnknownParameters(m) : m, (m) => n ? this.processCustomParameters(m) : this.mapCustomParametersToCustomData(m)].reduce((m, p) => w(this, void 0, void 0, function* () {
        let d = yield m;
        return yield p(d);
      }), Promise.resolve(r));
    });
  }
  makeEvent(t, ...r) {
    return w(this, void 0, void 0, function* () {
      let { newEventType: n = t } = this.eventTypeMapping[t] || {}, o = yield this.resolveParameters(t, ...r), a = yield this.resolvePayloadForParameters(t, o);
      return { eventType: n, payload: a, log: (i) => w(this, void 0, void 0, function* () {
        return this.bufferedRequests.push({ eventType: n, payload: Object.assign(Object.assign({}, a), i) }), yield Promise.all(this.afterSendHooks.map((s) => s(t, Object.assign(Object.assign({}, o), i)))), yield this.deferExecution(), yield this.sendFromBuffer();
      }) };
    });
  }
  sendEvent(t, ...r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeEvent(t, ...r)).log({});
    });
  }
  deferExecution() {
    return new Promise((t) => setTimeout(t, 0));
  }
  sendFromBuffer() {
    return w(this, void 0, void 0, function* () {
      let t = this.bufferedRequests.shift();
      if (t) {
        let { eventType: r, payload: n } = t;
        return this.runtime.getClientDependingOnEventType(r).sendEvent(r, n);
      }
    });
  }
  clear() {
    this.storage.removeItem("visitorId"), new jo().clear();
  }
  deleteHttpOnlyVisitorId() {
    this.runtime.client.deleteHttpCookieVisitorId();
  }
  makeSearchEvent(t) {
    return w(this, void 0, void 0, function* () {
      return this.makeEvent(ne.search, t);
    });
  }
  sendSearchEvent(t) {
    var { searchQueryUid: r } = t, n = wr(t, ["searchQueryUid"]);
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSearchEvent(n)).log({ searchQueryUid: r });
    });
  }
  makeClickEvent(t) {
    return w(this, void 0, void 0, function* () {
      return this.makeEvent(ne.click, t);
    });
  }
  sendClickEvent(t) {
    var { searchQueryUid: r } = t, n = wr(t, ["searchQueryUid"]);
    return w(this, void 0, void 0, function* () {
      return (yield this.makeClickEvent(n)).log({ searchQueryUid: r });
    });
  }
  makeCustomEvent(t) {
    return w(this, void 0, void 0, function* () {
      return this.makeEvent(ne.custom, t);
    });
  }
  sendCustomEvent(t) {
    var { lastSearchQueryUid: r } = t, n = wr(t, ["lastSearchQueryUid"]);
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCustomEvent(n)).log({ lastSearchQueryUid: r });
    });
  }
  makeViewEvent(t) {
    return w(this, void 0, void 0, function* () {
      return this.makeEvent(ne.view, t);
    });
  }
  sendViewEvent(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeViewEvent(t)).log({});
    });
  }
  getVisit() {
    return w(this, void 0, void 0, function* () {
      let r = yield (yield fetch(`${this.baseUrl}/analytics/visit`)).json();
      return this.visitorId = r.visitorId, r;
    });
  }
  getHealth() {
    return w(this, void 0, void 0, function* () {
      return yield (yield fetch(`${this.baseUrl}/analytics/monitoring/health`)).json();
    });
  }
  registerBeforeSendEventHook(t) {
    this.beforeSendHooks.push(t);
  }
  registerAfterSendEventHook(t) {
    this.afterSendHooks.push(t);
  }
  addEventTypeMapping(t, r) {
    this.eventTypeMapping[t] = r;
  }
  setAcceptedLinkReferrers(t) {
    if (Array.isArray(t) && t.every((r) => typeof r == "string"))
      this.acceptedLinkReferrers = t;
    else
      throw Error("Parameter should be an array of domain strings");
  }
  parseVariableArgumentsPayload(t, r) {
    let n = {};
    for (let o = 0, a = r.length; o < a; o++) {
      let i = r[o];
      if (typeof i == "string")
        n[t[o]] = i;
      else if (typeof i == "object")
        return Object.assign(Object.assign({}, n), i);
    }
    return n;
  }
  isKeyAllowedEmpty(t, r) {
    return ({ [ne.search]: ["queryText"] }[t] || []).indexOf(r) !== -1;
  }
  removeEmptyPayloadValues(t, r) {
    let n = (o) => typeof o < "u" && o !== null && o !== "";
    return Object.keys(t).filter((o) => this.isKeyAllowedEmpty(r, o) || n(t[o])).reduce((o, a) => Object.assign(Object.assign({}, o), { [a]: t[a] }), {});
  }
  removeUnknownParameters(t) {
    return Object.keys(t).filter((n) => {
      if (AI(n))
        return true;
      console.log(n, "is not processed by coveoua");
    }).reduce((n, o) => Object.assign(Object.assign({}, n), { [o]: t[o] }), {});
  }
  processCustomParameters(t) {
    let { custom: r } = t, n = wr(t, ["custom"]), o = {};
    r && Gc(r) && (o = this.lowercaseKeys(r));
    let a = FI(n);
    return Object.assign(Object.assign({}, o), a);
  }
  mapCustomParametersToCustomData(t) {
    let { custom: r } = t, n = wr(t, ["custom"]);
    if (r && Gc(r)) {
      let o = this.lowercaseKeys(r);
      return Object.assign(Object.assign({}, n), { customData: Object.assign(Object.assign({}, o), t.customData) });
    } else
      return t;
  }
  lowercaseKeys(t) {
    let r = Object.keys(t), n = {};
    return r.forEach((o) => {
      n[o.toLowerCase()] = t[o];
    }), n;
  }
  validateParams(t, r) {
    let { anonymizeIp: n } = t, o = wr(t, ["anonymizeIp"]);
    return n !== void 0 && ["0", "false", "undefined", "null", "{}", "[]", ""].indexOf(`${n}`.toLowerCase()) == -1 && (o.anonymizeIp = 1), (r == ne.view || r == ne.click || r == ne.search || r == ne.custom) && (o.originLevel3 = this.limit(o.originLevel3, 1024)), r == ne.view && (o.location = this.limit(o.location, 1024)), (r == "pageview" || r == "event") && (o.referrer = this.limit(o.referrer, 2048), o.location = this.limit(o.location, 2048), o.page = this.limit(o.page, 2048)), o;
  }
  ensureAnonymousUserWhenUsingApiKey(t) {
    let { userId: r } = t, n = wr(t, ["userId"]);
    return PI(this.options.token) && !r ? (n.userId = "anonymous", n) : t;
  }
  setTrackingIdIfTrackingIdNotPresent(t) {
    let { trackingId: r } = t, n = wr(t, ["trackingId"]);
    return r ? t : (n.hasOwnProperty("custom") && Gc(n.custom) && (n.custom.hasOwnProperty("context_website") || n.custom.hasOwnProperty("siteName")) && (n.trackingId = n.custom.context_website || n.custom.siteName), n.hasOwnProperty("customData") && Gc(n.customData) && (n.customData.hasOwnProperty("context_website") || n.customData.hasOwnProperty("siteName")) && (n.trackingId = n.customData.context_website || n.customData.siteName), n);
  }
  limit(t, r) {
    return typeof t == "string" ? Dw(t, r) : t;
  }
  get baseUrl() {
    return TI(this.options.endpoint, this.options.version, this.options.isCustomEndpoint);
  }
};
var Ir;
(function(e7) {
  e7.contextChanged = "contextChanged", e7.expandToFullUI = "expandToFullUI", e7.openUserActions = "openUserActions", e7.showPrecedingSessions = "showPrecedingSessions", e7.showFollowingSessions = "showFollowingSessions", e7.clickViewedDocument = "clickViewedDocument", e7.clickPageView = "clickPageView", e7.createArticle = "createArticle";
})(Ir || (Ir = {}));
var E;
(function(e7) {
  e7.interfaceLoad = "interfaceLoad", e7.interfaceChange = "interfaceChange", e7.didyoumeanAutomatic = "didyoumeanAutomatic", e7.didyoumeanClick = "didyoumeanClick", e7.resultsSort = "resultsSort", e7.searchboxSubmit = "searchboxSubmit", e7.searchboxClear = "searchboxClear", e7.searchboxAsYouType = "searchboxAsYouType", e7.breadcrumbFacet = "breadcrumbFacet", e7.breadcrumbResetAll = "breadcrumbResetAll", e7.documentQuickview = "documentQuickview", e7.documentOpen = "documentOpen", e7.omniboxAnalytics = "omniboxAnalytics", e7.omniboxFromLink = "omniboxFromLink", e7.searchFromLink = "searchFromLink", e7.triggerNotify = "notify", e7.triggerExecute = "execute", e7.triggerQuery = "query", e7.undoTriggerQuery = "undoQuery", e7.triggerRedirect = "redirect", e7.pagerResize = "pagerResize", e7.pagerNumber = "pagerNumber", e7.pagerNext = "pagerNext", e7.pagerPrevious = "pagerPrevious", e7.pagerScrolling = "pagerScrolling", e7.staticFilterClearAll = "staticFilterClearAll", e7.staticFilterSelect = "staticFilterSelect", e7.staticFilterDeselect = "staticFilterDeselect", e7.facetClearAll = "facetClearAll", e7.facetSearch = "facetSearch", e7.facetSelect = "facetSelect", e7.facetSelectAll = "facetSelectAll", e7.facetDeselect = "facetDeselect", e7.facetExclude = "facetExclude", e7.facetUnexclude = "facetUnexclude", e7.facetUpdateSort = "facetUpdateSort", e7.facetShowMore = "showMoreFacetResults", e7.facetShowLess = "showLessFacetResults", e7.queryError = "query", e7.queryErrorBack = "errorBack", e7.queryErrorClear = "errorClearQuery", e7.queryErrorRetry = "errorRetry", e7.recommendation = "recommendation", e7.recommendationInterfaceLoad = "recommendationInterfaceLoad", e7.recommendationOpen = "recommendationOpen", e7.likeSmartSnippet = "likeSmartSnippet", e7.dislikeSmartSnippet = "dislikeSmartSnippet", e7.expandSmartSnippet = "expandSmartSnippet", e7.collapseSmartSnippet = "collapseSmartSnippet", e7.openSmartSnippetFeedbackModal = "openSmartSnippetFeedbackModal", e7.closeSmartSnippetFeedbackModal = "closeSmartSnippetFeedbackModal", e7.sendSmartSnippetReason = "sendSmartSnippetReason", e7.expandSmartSnippetSuggestion = "expandSmartSnippetSuggestion", e7.collapseSmartSnippetSuggestion = "collapseSmartSnippetSuggestion", e7.showMoreSmartSnippetSuggestion = "showMoreSmartSnippetSuggestion", e7.showLessSmartSnippetSuggestion = "showLessSmartSnippetSuggestion", e7.openSmartSnippetSource = "openSmartSnippetSource", e7.openSmartSnippetSuggestionSource = "openSmartSnippetSuggestionSource", e7.openSmartSnippetInlineLink = "openSmartSnippetInlineLink", e7.openSmartSnippetSuggestionInlineLink = "openSmartSnippetSuggestionInlineLink", e7.recentQueryClick = "recentQueriesClick", e7.clearRecentQueries = "clearRecentQueries", e7.recentResultClick = "recentResultClick", e7.clearRecentResults = "clearRecentResults", e7.noResultsBack = "noResultsBack", e7.showMoreFoldedResults = "showMoreFoldedResults", e7.showLessFoldedResults = "showLessFoldedResults", e7.copyToClipboard = "copyToClipboard", e7.caseSendEmail = "Case.SendEmail", e7.feedItemTextPost = "FeedItem.TextPost", e7.caseAttach = "caseAttach", e7.caseDetach = "caseDetach", e7.retryGeneratedAnswer = "retryGeneratedAnswer", e7.likeGeneratedAnswer = "likeGeneratedAnswer", e7.dislikeGeneratedAnswer = "dislikeGeneratedAnswer", e7.openGeneratedAnswerSource = "openGeneratedAnswerSource", e7.generatedAnswerStreamEnd = "generatedAnswerStreamEnd", e7.generatedAnswerSourceHover = "generatedAnswerSourceHover", e7.generatedAnswerCopyToClipboard = "generatedAnswerCopyToClipboard", e7.generatedAnswerHideAnswers = "generatedAnswerHideAnswers", e7.generatedAnswerShowAnswers = "generatedAnswerShowAnswers", e7.generatedAnswerExpand = "generatedAnswerExpand", e7.generatedAnswerCollapse = "generatedAnswerCollapse", e7.generatedAnswerFeedbackSubmit = "generatedAnswerFeedbackSubmit", e7.rephraseGeneratedAnswer = "rephraseGeneratedAnswer", e7.generatedAnswerFeedbackSubmitV2 = "generatedAnswerFeedbackSubmitV2", e7.generatedAnswerCitationClick = "generatedAnswerCitationClick";
})(E || (E = {}));
var Fh = { [E.triggerNotify]: "queryPipelineTriggers", [E.triggerExecute]: "queryPipelineTriggers", [E.triggerQuery]: "queryPipelineTriggers", [E.triggerRedirect]: "queryPipelineTriggers", [E.queryError]: "errors", [E.queryErrorBack]: "errors", [E.queryErrorClear]: "errors", [E.queryErrorRetry]: "errors", [E.pagerNext]: "getMoreResults", [E.pagerPrevious]: "getMoreResults", [E.pagerNumber]: "getMoreResults", [E.pagerResize]: "getMoreResults", [E.pagerScrolling]: "getMoreResults", [E.facetSearch]: "facet", [E.facetShowLess]: "facet", [E.facetShowMore]: "facet", [E.recommendation]: "recommendation", [E.likeSmartSnippet]: "smartSnippet", [E.dislikeSmartSnippet]: "smartSnippet", [E.expandSmartSnippet]: "smartSnippet", [E.collapseSmartSnippet]: "smartSnippet", [E.openSmartSnippetFeedbackModal]: "smartSnippet", [E.closeSmartSnippetFeedbackModal]: "smartSnippet", [E.sendSmartSnippetReason]: "smartSnippet", [E.expandSmartSnippetSuggestion]: "smartSnippetSuggestions", [E.collapseSmartSnippetSuggestion]: "smartSnippetSuggestions", [E.showMoreSmartSnippetSuggestion]: "smartSnippetSuggestions", [E.showLessSmartSnippetSuggestion]: "smartSnippetSuggestions", [E.clearRecentQueries]: "recentQueries", [E.recentResultClick]: "recentlyClickedDocuments", [E.clearRecentResults]: "recentlyClickedDocuments", [E.showLessFoldedResults]: "folding", [E.caseDetach]: "case", [E.likeGeneratedAnswer]: "generatedAnswer", [E.dislikeGeneratedAnswer]: "generatedAnswer", [E.openGeneratedAnswerSource]: "generatedAnswer", [E.generatedAnswerStreamEnd]: "generatedAnswer", [E.generatedAnswerSourceHover]: "generatedAnswer", [E.generatedAnswerCopyToClipboard]: "generatedAnswer", [E.generatedAnswerHideAnswers]: "generatedAnswer", [E.generatedAnswerShowAnswers]: "generatedAnswer", [E.generatedAnswerExpand]: "generatedAnswer", [E.generatedAnswerCollapse]: "generatedAnswer", [E.generatedAnswerFeedbackSubmit]: "generatedAnswer", [E.generatedAnswerFeedbackSubmitV2]: "generatedAnswer", [Ir.expandToFullUI]: "interface", [Ir.openUserActions]: "User Actions", [Ir.showPrecedingSessions]: "User Actions", [Ir.showFollowingSessions]: "User Actions", [Ir.clickViewedDocument]: "User Actions", [Ir.clickPageView]: "User Actions", [Ir.createArticle]: "createArticle" };
var $o = class {
  constructor() {
    this.runtime = new Yc(), this.currentVisitorId = "";
  }
  getPayload() {
    return Promise.resolve();
  }
  getParameters() {
    return Promise.resolve();
  }
  makeEvent(t) {
    return Promise.resolve({ eventType: t, payload: null, log: () => Promise.resolve() });
  }
  sendEvent() {
    return Promise.resolve();
  }
  makeSearchEvent() {
    return this.makeEvent(ne.search);
  }
  sendSearchEvent() {
    return Promise.resolve();
  }
  makeClickEvent() {
    return this.makeEvent(ne.click);
  }
  sendClickEvent() {
    return Promise.resolve();
  }
  makeCustomEvent() {
    return this.makeEvent(ne.custom);
  }
  sendCustomEvent() {
    return Promise.resolve();
  }
  makeViewEvent() {
    return this.makeEvent(ne.view);
  }
  sendViewEvent() {
    return Promise.resolve();
  }
  getVisit() {
    return Promise.resolve({ id: "", visitorId: "" });
  }
  getHealth() {
    return Promise.resolve({ status: "" });
  }
  registerBeforeSendEventHook() {
  }
  registerAfterSendEventHook() {
  }
  addEventTypeMapping() {
  }
  get version() {
    return Oh;
  }
};
function OI(e7) {
  let t = "";
  return e7.filter((r) => {
    let n = r !== t;
    return t = r, n;
  });
}
function qI(e7) {
  return e7.map((t) => t.replace(/;/g, ""));
}
function Qh(e7) {
  let r = e7.join(";");
  return r.length <= 256 ? r : Qh(e7.slice(1));
}
var Rh = (e7) => {
  let t = qI(e7), r = OI(t);
  return Qh(r);
};
function bh(e7) {
  let t = typeof e7.partialQueries == "string" ? e7.partialQueries : Rh(e7.partialQueries), r = typeof e7.suggestions == "string" ? e7.suggestions : Rh(e7.suggestions);
  return Object.assign(Object.assign({}, e7), { partialQueries: t, suggestions: r });
}
var Xc = class {
  constructor(t, r) {
    this.opts = t, this.provider = r;
    let n = t.enableAnalytics === false || Jc();
    this.coveoAnalyticsClient = n ? new $o() : new Qt(t);
  }
  disable() {
    this.coveoAnalyticsClient = new $o();
  }
  enable() {
    this.coveoAnalyticsClient = new Qt(this.opts);
  }
  makeInterfaceLoad() {
    return this.makeSearchEvent(E.interfaceLoad);
  }
  logInterfaceLoad() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeInterfaceLoad()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecommendationInterfaceLoad() {
    return this.makeSearchEvent(E.recommendationInterfaceLoad);
  }
  logRecommendationInterfaceLoad() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRecommendationInterfaceLoad()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecommendation() {
    return this.makeCustomEvent(E.recommendation);
  }
  logRecommendation() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRecommendation()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecommendationOpen(t, r) {
    return this.makeClickEvent(E.recommendationOpen, t, r);
  }
  logRecommendationOpen(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRecommendationOpen(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeStaticFilterClearAll(t) {
    return this.makeSearchEvent(E.staticFilterClearAll, t);
  }
  logStaticFilterClearAll(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeStaticFilterClearAll(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeStaticFilterSelect(t) {
    return this.makeSearchEvent(E.staticFilterSelect, t);
  }
  logStaticFilterSelect(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeStaticFilterSelect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeStaticFilterDeselect(t) {
    return this.makeSearchEvent(E.staticFilterDeselect, t);
  }
  logStaticFilterDeselect(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeStaticFilterDeselect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFetchMoreResults() {
    return this.makeCustomEvent(E.pagerScrolling, { type: "getMoreResults" });
  }
  logFetchMoreResults() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFetchMoreResults()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeInterfaceChange(t) {
    return this.makeSearchEvent(E.interfaceChange, t);
  }
  logInterfaceChange(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeInterfaceChange(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDidYouMeanAutomatic() {
    return this.makeSearchEvent(E.didyoumeanAutomatic);
  }
  logDidYouMeanAutomatic() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeDidYouMeanAutomatic()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDidYouMeanClick() {
    return this.makeSearchEvent(E.didyoumeanClick);
  }
  logDidYouMeanClick() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeDidYouMeanClick()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeResultsSort(t) {
    return this.makeSearchEvent(E.resultsSort, t);
  }
  logResultsSort(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeResultsSort(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchboxSubmit() {
    return this.makeSearchEvent(E.searchboxSubmit);
  }
  logSearchboxSubmit() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSearchboxSubmit()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchboxClear() {
    return this.makeSearchEvent(E.searchboxClear);
  }
  logSearchboxClear() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSearchboxClear()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchboxAsYouType() {
    return this.makeSearchEvent(E.searchboxAsYouType);
  }
  logSearchboxAsYouType() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSearchboxAsYouType()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeBreadcrumbFacet(t) {
    return this.makeSearchEvent(E.breadcrumbFacet, t);
  }
  logBreadcrumbFacet(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeBreadcrumbFacet(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeBreadcrumbResetAll() {
    return this.makeSearchEvent(E.breadcrumbResetAll);
  }
  logBreadcrumbResetAll() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeBreadcrumbResetAll()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDocumentQuickview(t, r) {
    return this.makeClickEvent(E.documentQuickview, t, r);
  }
  logDocumentQuickview(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeDocumentQuickview(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDocumentOpen(t, r) {
    return this.makeClickEvent(E.documentOpen, t, r);
  }
  logDocumentOpen(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeDocumentOpen(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOmniboxAnalytics(t) {
    return this.makeSearchEvent(E.omniboxAnalytics, bh(t));
  }
  logOmniboxAnalytics(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOmniboxAnalytics(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOmniboxFromLink(t) {
    return this.makeSearchEvent(E.omniboxFromLink, bh(t));
  }
  logOmniboxFromLink(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOmniboxFromLink(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchFromLink() {
    return this.makeSearchEvent(E.searchFromLink);
  }
  logSearchFromLink() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSearchFromLink()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerNotify(t) {
    return this.makeCustomEvent(E.triggerNotify, t);
  }
  logTriggerNotify(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeTriggerNotify(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerExecute(t) {
    return this.makeCustomEvent(E.triggerExecute, t);
  }
  logTriggerExecute(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeTriggerExecute(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerQuery() {
    return this.makeCustomEvent(E.triggerQuery, { query: this.provider.getSearchEventRequestPayload().queryText }, "queryPipelineTriggers");
  }
  logTriggerQuery() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeTriggerQuery()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeUndoTriggerQuery(t) {
    return this.makeSearchEvent(E.undoTriggerQuery, t);
  }
  logUndoTriggerQuery(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeUndoTriggerQuery(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerRedirect(t) {
    return this.makeCustomEvent(E.triggerRedirect, Object.assign(Object.assign({}, t), { query: this.provider.getSearchEventRequestPayload().queryText }));
  }
  logTriggerRedirect(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeTriggerRedirect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerResize(t) {
    return this.makeCustomEvent(E.pagerResize, t);
  }
  logPagerResize(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makePagerResize(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerNumber(t) {
    return this.makeCustomEvent(E.pagerNumber, t);
  }
  logPagerNumber(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makePagerNumber(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerNext(t) {
    return this.makeCustomEvent(E.pagerNext, t);
  }
  logPagerNext(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makePagerNext(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerPrevious(t) {
    return this.makeCustomEvent(E.pagerPrevious, t);
  }
  logPagerPrevious(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makePagerPrevious(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerScrolling() {
    return this.makeCustomEvent(E.pagerScrolling);
  }
  logPagerScrolling() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makePagerScrolling()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetClearAll(t) {
    return this.makeSearchEvent(E.facetClearAll, t);
  }
  logFacetClearAll(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetClearAll(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetSearch(t) {
    return this.makeSearchEvent(E.facetSearch, t);
  }
  logFacetSearch(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetSearch(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetSelect(t) {
    return this.makeSearchEvent(E.facetSelect, t);
  }
  logFacetSelect(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetSelect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetDeselect(t) {
    return this.makeSearchEvent(E.facetDeselect, t);
  }
  logFacetDeselect(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetDeselect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetExclude(t) {
    return this.makeSearchEvent(E.facetExclude, t);
  }
  logFacetExclude(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetExclude(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetUnexclude(t) {
    return this.makeSearchEvent(E.facetUnexclude, t);
  }
  logFacetUnexclude(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetUnexclude(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetSelectAll(t) {
    return this.makeSearchEvent(E.facetSelectAll, t);
  }
  logFacetSelectAll(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetSelectAll(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetUpdateSort(t) {
    return this.makeSearchEvent(E.facetUpdateSort, t);
  }
  logFacetUpdateSort(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetUpdateSort(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetShowMore(t) {
    return this.makeCustomEvent(E.facetShowMore, t);
  }
  logFacetShowMore(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetShowMore(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetShowLess(t) {
    return this.makeCustomEvent(E.facetShowLess, t);
  }
  logFacetShowLess(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeFacetShowLess(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryError(t) {
    return this.makeCustomEvent(E.queryError, t);
  }
  logQueryError(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeQueryError(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryErrorBack() {
    return w(this, void 0, void 0, function* () {
      let t = yield this.makeCustomEvent(E.queryErrorBack);
      return { description: t.description, log: () => w(this, void 0, void 0, function* () {
        return yield t.log({ searchUID: this.provider.getSearchUID() }), this.logSearchEvent(E.queryErrorBack);
      }) };
    });
  }
  logQueryErrorBack() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeQueryErrorBack()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryErrorRetry() {
    return w(this, void 0, void 0, function* () {
      let t = yield this.makeCustomEvent(E.queryErrorRetry);
      return { description: t.description, log: () => w(this, void 0, void 0, function* () {
        return yield t.log({ searchUID: this.provider.getSearchUID() }), this.logSearchEvent(E.queryErrorRetry);
      }) };
    });
  }
  logQueryErrorRetry() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeQueryErrorRetry()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryErrorClear() {
    return w(this, void 0, void 0, function* () {
      let t = yield this.makeCustomEvent(E.queryErrorClear);
      return { description: t.description, log: () => w(this, void 0, void 0, function* () {
        return yield t.log({ searchUID: this.provider.getSearchUID() }), this.logSearchEvent(E.queryErrorClear);
      }) };
    });
  }
  logQueryErrorClear() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeQueryErrorClear()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeLikeSmartSnippet() {
    return this.makeCustomEvent(E.likeSmartSnippet);
  }
  logLikeSmartSnippet() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeLikeSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDislikeSmartSnippet() {
    return this.makeCustomEvent(E.dislikeSmartSnippet);
  }
  logDislikeSmartSnippet() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeDislikeSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeExpandSmartSnippet() {
    return this.makeCustomEvent(E.expandSmartSnippet);
  }
  logExpandSmartSnippet() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeExpandSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCollapseSmartSnippet() {
    return this.makeCustomEvent(E.collapseSmartSnippet);
  }
  logCollapseSmartSnippet() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCollapseSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetFeedbackModal() {
    return this.makeCustomEvent(E.openSmartSnippetFeedbackModal);
  }
  logOpenSmartSnippetFeedbackModal() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetFeedbackModal()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCloseSmartSnippetFeedbackModal() {
    return this.makeCustomEvent(E.closeSmartSnippetFeedbackModal);
  }
  logCloseSmartSnippetFeedbackModal() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCloseSmartSnippetFeedbackModal()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSmartSnippetFeedbackReason(t, r) {
    return this.makeCustomEvent(E.sendSmartSnippetReason, { reason: t, details: r });
  }
  logSmartSnippetFeedbackReason(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSmartSnippetFeedbackReason(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeExpandSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E.expandSmartSnippetSuggestion, "documentId" in t ? t : { documentId: t });
  }
  logExpandSmartSnippetSuggestion(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeExpandSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCollapseSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E.collapseSmartSnippetSuggestion, "documentId" in t ? t : { documentId: t });
  }
  logCollapseSmartSnippetSuggestion(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCollapseSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowMoreSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E.showMoreSmartSnippetSuggestion, t);
  }
  logShowMoreSmartSnippetSuggestion(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeShowMoreSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowLessSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E.showLessSmartSnippetSuggestion, t);
  }
  logShowLessSmartSnippetSuggestion(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeShowLessSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetSource(t, r) {
    return this.makeClickEvent(E.openSmartSnippetSource, t, r);
  }
  logOpenSmartSnippetSource(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetSource(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetSuggestionSource(t, r) {
    return this.makeClickEvent(E.openSmartSnippetSuggestionSource, t, { contentIDKey: r.documentId.contentIdKey, contentIDValue: r.documentId.contentIdValue }, r);
  }
  makeCopyToClipboard(t, r) {
    return this.makeClickEvent(E.copyToClipboard, t, r);
  }
  logCopyToClipboard(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCopyToClipboard(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  logOpenSmartSnippetSuggestionSource(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetSuggestionSource(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetInlineLink(t, r) {
    return this.makeClickEvent(E.openSmartSnippetInlineLink, t, { contentIDKey: r.contentIDKey, contentIDValue: r.contentIDValue }, r);
  }
  logOpenSmartSnippetInlineLink(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetInlineLink(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetSuggestionInlineLink(t, r) {
    return this.makeClickEvent(E.openSmartSnippetSuggestionInlineLink, t, { contentIDKey: r.documentId.contentIdKey, contentIDValue: r.documentId.contentIdValue }, r);
  }
  logOpenSmartSnippetSuggestionInlineLink(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetSuggestionInlineLink(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecentQueryClick() {
    return this.makeSearchEvent(E.recentQueryClick);
  }
  logRecentQueryClick() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRecentQueryClick()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeClearRecentQueries() {
    return this.makeCustomEvent(E.clearRecentQueries);
  }
  logClearRecentQueries() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeClearRecentQueries()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecentResultClick(t, r) {
    return this.makeCustomEvent(E.recentResultClick, { info: t, identifier: r });
  }
  logRecentResultClick(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRecentResultClick(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeClearRecentResults() {
    return this.makeCustomEvent(E.clearRecentResults);
  }
  logClearRecentResults() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeClearRecentResults()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeNoResultsBack() {
    return this.makeSearchEvent(E.noResultsBack);
  }
  logNoResultsBack() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeNoResultsBack()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowMoreFoldedResults(t, r) {
    return this.makeClickEvent(E.showMoreFoldedResults, t, r);
  }
  logShowMoreFoldedResults(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeShowMoreFoldedResults(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowLessFoldedResults() {
    return this.makeCustomEvent(E.showLessFoldedResults);
  }
  logShowLessFoldedResults() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeShowLessFoldedResults()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeEventDescription(t, r) {
    var n;
    return { actionCause: r, customData: (n = t.payload) === null || n === void 0 ? void 0 : n.customData };
  }
  makeCustomEvent(t, r, n = Fh[t]) {
    return w(this, void 0, void 0, function* () {
      let o = Object.assign(Object.assign({}, this.provider.getBaseMetadata()), r), a = Object.assign(Object.assign({}, yield this.getBaseEventRequest(o)), { eventType: n, eventValue: t }), i = yield this.coveoAnalyticsClient.makeCustomEvent(a);
      return { description: this.makeEventDescription(i, t), log: ({ searchUID: s }) => i.log({ lastSearchQueryUid: s }) };
    });
  }
  logCustomEvent(t, r, n = Fh[t]) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCustomEvent(t, r, n)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCustomEventWithType(t, r, n) {
    return w(this, void 0, void 0, function* () {
      let o = Object.assign(Object.assign({}, this.provider.getBaseMetadata()), n), a = Object.assign(Object.assign({}, yield this.getBaseEventRequest(o)), { eventType: r, eventValue: t }), i = yield this.coveoAnalyticsClient.makeCustomEvent(a);
      return { description: this.makeEventDescription(i, t), log: ({ searchUID: s }) => i.log({ lastSearchQueryUid: s }) };
    });
  }
  logCustomEventWithType(t, r, n) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeCustomEventWithType(t, r, n)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  logSearchEvent(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeSearchEvent(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchEvent(t, r) {
    return w(this, void 0, void 0, function* () {
      let n = yield this.getBaseSearchEventRequest(t, r), o = yield this.coveoAnalyticsClient.makeSearchEvent(n);
      return { description: this.makeEventDescription(o, t), log: ({ searchUID: a }) => o.log({ searchQueryUid: a }) };
    });
  }
  makeClickEvent(t, r, n, o) {
    return w(this, void 0, void 0, function* () {
      let a = Object.assign(Object.assign(Object.assign({}, r), yield this.getBaseEventRequest(Object.assign(Object.assign({}, n), o))), { queryPipeline: this.provider.getPipeline(), actionCause: t }), i = yield this.coveoAnalyticsClient.makeClickEvent(a);
      return { description: this.makeEventDescription(i, t), log: ({ searchUID: s }) => i.log({ searchQueryUid: s }) };
    });
  }
  logClickEvent(t, r, n, o) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeClickEvent(t, r, n, o)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  getBaseSearchEventRequest(t, r) {
    var n, o;
    return w(this, void 0, void 0, function* () {
      return Object.assign(Object.assign(Object.assign({}, yield this.getBaseEventRequest(Object.assign(Object.assign({}, r), (o = (n = this.provider).getGeneratedAnswerMetadata) === null || o === void 0 ? void 0 : o.call(n)))), this.provider.getSearchEventRequestPayload()), { queryPipeline: this.provider.getPipeline(), actionCause: t });
    });
  }
  getBaseEventRequest(t) {
    return w(this, void 0, void 0, function* () {
      let r = Object.assign(Object.assign({}, this.provider.getBaseMetadata()), t);
      return Object.assign(Object.assign(Object.assign({}, this.getOrigins()), this.getSplitTestRun()), { customData: r, language: this.provider.getLanguage(), facetState: this.provider.getFacetState ? this.provider.getFacetState() : [], anonymous: this.provider.getIsAnonymous(), clientId: yield this.getClientId() });
    });
  }
  getOrigins() {
    var t, r;
    return { originContext: (r = (t = this.provider).getOriginContext) === null || r === void 0 ? void 0 : r.call(t), originLevel1: this.provider.getOriginLevel1(), originLevel2: this.provider.getOriginLevel2(), originLevel3: this.provider.getOriginLevel3() };
  }
  getClientId() {
    return this.coveoAnalyticsClient instanceof Qt ? this.coveoAnalyticsClient.getCurrentVisitorId() : void 0;
  }
  getSplitTestRun() {
    let t = this.provider.getSplitTestRunName ? this.provider.getSplitTestRunName() : "", r = this.provider.getSplitTestRunVersion ? this.provider.getSplitTestRunVersion() : "";
    return Object.assign(Object.assign({}, t && { splitTestRunName: t }), r && { splitTestRunVersion: r });
  }
  makeLikeGeneratedAnswer(t) {
    return this.makeCustomEvent(E.likeGeneratedAnswer, t);
  }
  logLikeGeneratedAnswer(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeLikeGeneratedAnswer(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDislikeGeneratedAnswer(t) {
    return this.makeCustomEvent(E.dislikeGeneratedAnswer, t);
  }
  logDislikeGeneratedAnswer(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeDislikeGeneratedAnswer(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenGeneratedAnswerSource(t) {
    return this.makeCustomEvent(E.openGeneratedAnswerSource, t);
  }
  logOpenGeneratedAnswerSource(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeOpenGeneratedAnswerSource(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerCitationClick(t, r) {
    return this.makeClickEvent(E.generatedAnswerCitationClick, Object.assign(Object.assign({}, t), { documentPosition: 1 }), { contentIDKey: r.documentId.contentIdKey, contentIDValue: r.documentId.contentIdValue }, r);
  }
  logGeneratedAnswerCitationClick(t, r) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerCitationClick(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerSourceHover(t) {
    return this.makeCustomEvent(E.generatedAnswerSourceHover, t);
  }
  logGeneratedAnswerSourceHover(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerSourceHover(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerCopyToClipboard(t) {
    return this.makeCustomEvent(E.generatedAnswerCopyToClipboard, t);
  }
  logGeneratedAnswerCopyToClipboard(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerCopyToClipboard(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerHideAnswers(t) {
    return this.makeCustomEvent(E.generatedAnswerHideAnswers, t);
  }
  logGeneratedAnswerHideAnswers(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerHideAnswers(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerShowAnswers(t) {
    return this.makeCustomEvent(E.generatedAnswerShowAnswers, t);
  }
  logGeneratedAnswerShowAnswers(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerShowAnswers(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerExpand(t) {
    return this.makeCustomEvent(E.generatedAnswerExpand, t);
  }
  logGeneratedAnswerExpand(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerExpand(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerCollapse(t) {
    return this.makeCustomEvent(E.generatedAnswerCollapse, t);
  }
  logGeneratedAnswerCollapse(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerCollapse(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerFeedbackSubmit(t) {
    return this.makeCustomEvent(E.generatedAnswerFeedbackSubmit, t);
  }
  logGeneratedAnswerFeedbackSubmit(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerFeedbackSubmit(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerFeedbackSubmitV2(t) {
    return this.makeCustomEvent(E.generatedAnswerFeedbackSubmitV2, t);
  }
  logGeneratedAnswerFeedbackSubmitV2(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerFeedbackSubmitV2(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRephraseGeneratedAnswer(t) {
    return this.makeSearchEvent(E.rephraseGeneratedAnswer, t);
  }
  logRephraseGeneratedAnswer(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRephraseGeneratedAnswer(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRetryGeneratedAnswer() {
    return this.makeSearchEvent(E.retryGeneratedAnswer);
  }
  logRetryGeneratedAnswer() {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeRetryGeneratedAnswer()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerStreamEnd(t) {
    return this.makeCustomEvent(E.generatedAnswerStreamEnd, t);
  }
  logGeneratedAnswerStreamEnd(t) {
    return w(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerStreamEnd(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
};
var Zc = Object.assign({}, ds);
Object.keys(Zc).map((e7) => Zc[e7]);
var eu;
(function(e7) {
  e7.click = "click", e7.flowStart = "flowStart";
})(eu || (eu = {}));
var ut;
(function(e7) {
  e7.enterInterface = "ticket_create_start", e7.fieldUpdate = "ticket_field_update", e7.fieldSuggestionClick = "ticket_classification_click", e7.documentSuggestionClick = "documentSuggestionClick", e7.documentSuggestionQuickview = "documentSuggestionQuickview", e7.suggestionRate = "suggestion_rate", e7.nextCaseStep = "ticket_next_stage", e7.caseCancelled = "ticket_cancel", e7.caseSolved = "ticket_cancel", e7.caseCreated = "ticket_create";
})(ut || (ut = {}));
var tu;
(function(e7) {
  e7.quit = "Quit", e7.solved = "Solved";
})(tu || (tu = {}));
var Kr = () => "default";
var DI = (e7) => {
  let t = e7.configuration.search.locale.split("-")[0];
  return !t || t.length !== 2 ? "en" : t;
};
var Zn = class {
  constructor(t) {
    this.getState = t;
    Ce(this, "state");
    this.state = t();
  }
  getLanguage() {
    return DI(this.state);
  }
  getBaseMetadata() {
    let { context: t, configuration: r } = this.state, n = t?.contextValues || {}, o = {};
    for (let [a, i] of Object.entries(n)) {
      let s = `context_${a}`;
      o[s] = i;
    }
    return r.analytics.analyticsMode === "legacy" && (o.coveoHeadlessVersion = Jn), o;
  }
  getOriginContext() {
    return this.state.configuration.analytics.originContext;
  }
  getOriginLevel1() {
    return this.state.searchHub || Kr();
  }
  getOriginLevel2() {
    return this.state.configuration.analytics.originLevel2;
  }
  getOriginLevel3() {
    return this.state.configuration.analytics.originLevel3;
  }
  getIsAnonymous() {
    return this.state.configuration.analytics.anonymous;
  }
};
var Lh = (e7) => new Qt(e7).getCurrentVisitorId();
var dt = new Th.HistoryStore();
var fs = (e7, t) => typeof t == "function" ? (...r) => {
  let n = Hi(r[0]);
  try {
    return t.apply(t, r);
  } catch (o) {
    return e7.error(o, "Error in analytics preprocessRequest. Returning original request."), n;
  }
} : void 0;
var gs = (e7, t) => (...r) => {
  let n = Hi(r[1]);
  try {
    return t.apply(t, r);
  } catch (o) {
    return e7.error(o, "Error in analytics hook. Returning original request."), n;
  }
};
function Go() {
  return { desiredCount: 5, numberOfValues: 8, set: {} };
}
function ze(e7) {
  let { activeValue: t, ancestryMap: r } = MI(e7);
  return t ? QI(t, r) : [];
}
function MI(e7) {
  let t = [...e7], r = /* @__PURE__ */ new Map();
  for (; t.length > 0; ) {
    let n = t.shift();
    if (n.state === "selected")
      return { activeValue: n, ancestryMap: r };
    if (r)
      for (let o of n.children)
        r.set(o, n);
    t.unshift(...n.children);
  }
  return {};
}
function QI(e7, t) {
  let r = [];
  if (!e7)
    return [];
  let n = e7;
  do
    r.unshift(n), n = t.get(n);
  while (n);
  return r;
}
var vm = (e7, t) => e7.categoryFacetSet[t]?.request;
var Pm = (e7, t) => {
  let r = vm(e7, t);
  return ze(r?.currentValues ?? []);
};
function Wo() {
  return {};
}
function $h(e7) {
  return { request: e7 };
}
function Ho() {
  return {};
}
function Gh(e7) {
  return { request: e7 };
}
function zo() {
  return {};
}
function Wh(e7) {
  return { request: e7, hasBreadcrumbs: true };
}
function Ko() {
  return {};
}
function nt(e7) {
  return { facetSet: e7.facetSet ?? Ko(), categoryFacetSet: e7.categoryFacetSet ?? Wo(), dateFacetSet: e7.dateFacetSet ?? Ho(), numericFacetSet: e7.numericFacetSet ?? zo(), automaticFacetSet: e7.automaticFacetSet ?? Go() };
}
var wm = (e7) => {
  let t = [];
  return _I(e7).forEach((r, n) => {
    let o = Jh(e7, r.facetId), a = HI(r, n + 1);
    if (UI(r)) {
      if (!!!Pm(e7, r.facetId).length)
        return;
      t.push({ ...a, ...GI(e7, r.facetId), facetType: o, state: "selected" });
      return;
    }
    r.currentValues.forEach((i, s) => {
      if (i.state === "idle")
        return;
      let c = Hh(i, s + 1, o), u = BI(r) ? zh(i) : $I(i);
      t.push({ ...a, ...c, ...u });
    });
  }), jI(e7).forEach((r, n) => {
    let o = WI(r, n + 1);
    r.values.forEach((a, i) => {
      if (a.state === "idle")
        return;
      let s = Hh(a, i + 1, "specific"), c = zh(a);
      t.push({ ...o, ...s, ...c });
    });
  }), t;
};
var BI = (e7) => e7.type === "specific";
var UI = (e7) => e7.type === "hierarchical";
var _I = (e7) => [...Object.values(e7.facetSet), ...Object.values(e7.categoryFacetSet), ...Object.values(e7.dateFacetSet), ...Object.values(e7.numericFacetSet)].map((t) => t.request);
var jI = (e7) => [...Object.values(e7.automaticFacetSet.set)].map((t) => t.response);
var Hh = (e7, t, r) => ({ state: e7.state, valuePosition: t, facetType: r });
var $I = (e7) => ({ displayValue: `${e7.start}..${e7.end}`, value: `${e7.start}..${e7.end}`, start: e7.start, end: e7.end, endInclusive: e7.endInclusive });
var zh = (e7) => ({ displayValue: e7.value, value: e7.value });
var Kh = (e7, t) => Pm(e7, t).map((n) => n.value).join(";");
var GI = (e7, t) => {
  let n = Kh(e7, t);
  return { value: n, valuePosition: 1, displayValue: n };
};
var WI = (e7, t) => ({ title: Im(e7.field, e7.field), field: e7.field, id: e7.field, facetPosition: t });
var HI = (e7, t) => ({ title: Im(e7.field, e7.facetId), field: e7.field, id: e7.facetId, facetPosition: t });
var Im = (e7, t) => `${e7}_${t}`;
var Yh = (e7, t) => e7.facetSet[t]?.request || e7.categoryFacetSet[t]?.request || e7.dateFacetSet[t]?.request || e7.numericFacetSet[t]?.request || e7.automaticFacetSet.set[t]?.response;
var Jh = (e7, t) => {
  let r = Yh(e7, t);
  return r ? r.type : "specific";
};
var Fe = () => ({ q: "", enableQuerySyntax: false });
var nu = ((r) => (r.Ascending = "ascending", r.Descending = "descending", r))(nu || {});
var Xo = ((a) => (a.Relevancy = "relevancy", a.QRE = "qre", a.Date = "date", a.Field = "field", a.NoSort = "nosort", a))(Xo || {});
var Er = (e7) => {
  if (isArray(e7))
    return e7.map((t) => Er(t)).join(",");
  switch (e7.by) {
    case "relevancy":
    case "qre":
    case "nosort":
      return e7.by;
    case "date":
      return `date ${e7.order}`;
    case "field":
      return `@${e7.field} ${e7.order}`;
    default:
      return "";
  }
};
var ys = () => ({ by: "relevancy" });
function pt() {
  return Er(ys());
}
var Cs = class Cs2 extends Zn {
  constructor() {
    super(...arguments);
    Ce(this, "getFacetRequest", (r) => this.state.facetSet?.[r]?.request || this.state.categoryFacetSet?.[r]?.request || this.state.dateFacetSet?.[r]?.request || this.state.numericFacetSet?.[r]?.request || this.state.automaticFacetSet?.set[r]?.response);
  }
  getFacetState() {
    return wm(nt(this.getState()));
  }
  getPipeline() {
    return this.state.pipeline || this.state.search?.response.pipeline || Cs2.fallbackPipelineName;
  }
  getSearchEventRequestPayload() {
    return { queryText: this.queryText, responseTime: this.responseTime, results: this.resultURIs, numberOfResults: this.numberOfResults };
  }
  getSearchUID() {
    let r = this.getState();
    return r.search?.searchResponseId || r.search?.response.searchUid || et().response.searchUid;
  }
  getSplitTestRunName() {
    return this.state.search?.response.splitTestRun;
  }
  getSplitTestRunVersion() {
    let r = !!this.getSplitTestRunName(), n = this.state.search?.response.pipeline || this.state.pipeline || Cs2.fallbackPipelineName;
    return r ? n : void 0;
  }
  getBaseMetadata() {
    let r = this.getState(), n = super.getBaseMetadata(), o = r.search?.response?.extendedResults?.generativeQuestionAnsweringId;
    return o && (n.generativeQuestionAnsweringId = o), n;
  }
  getFacetMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: a, facetValue: n, facetTitle: `${a}_${r}` };
  }
  getFacetClearAllMetadata(r) {
    let o = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: o, facetTitle: `${o}_${r}` };
  }
  getFacetUpdateSortMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: a, criteria: n, facetTitle: `${a}_${r}` };
  }
  getRangeBreadcrumbFacetMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: a, facetRangeEnd: n.end, facetRangeEndInclusive: n.endInclusive, facetRangeStart: n.start, facetTitle: `${a}_${r}` };
  }
  getResultSortMetadata() {
    return { ...this.getBaseMetadata(), resultsSortBy: this.state.sortCriteria ?? pt() };
  }
  getStaticFilterToggleMetadata(r, n) {
    return { ...this.getBaseMetadata(), staticFilterId: r, staticFilterValue: n };
  }
  getStaticFilterClearAllMetadata(r) {
    return { ...this.getBaseMetadata(), staticFilterId: r };
  }
  getUndoTriggerQueryMetadata(r) {
    return { ...this.getBaseMetadata(), undoneQuery: r };
  }
  getCategoryBreadcrumbFacetMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), categoryFacetId: r, categoryFacetField: a, categoryFacetPath: n, categoryFacetTitle: `${a}_${r}` };
  }
  getOmniboxAnalyticsMetadata(r, n) {
    let o = this.state.querySuggest && this.state.querySuggest[r], a = o.completions.map((u) => u.expression), i = o.partialQueries.length - 1, s = o.partialQueries[i] || "", c = o.responseId;
    return { ...this.getBaseMetadata(), suggestionRanking: a.indexOf(n), partialQuery: s, partialQueries: o.partialQueries.length > 0 ? o.partialQueries : "", suggestions: a.length > 0 ? a : "", querySuggestResponseId: c };
  }
  getInterfaceChangeMetadata() {
    return { ...this.getBaseMetadata(), interfaceChangeTo: this.state.configuration.analytics.originLevel2 };
  }
  getOmniboxFromLinkMetadata(r) {
    return { ...this.getBaseMetadata(), ...r };
  }
  getGeneratedAnswerMetadata() {
    let r = this.getState(), n = {};
    return r.generatedAnswer?.isVisible !== void 0 && (n.showGeneratedAnswer = r.generatedAnswer.isVisible), n;
  }
  get resultURIs() {
    return this.results?.map((r) => ({ documentUri: r.uri, documentUriHash: r.raw.urihash }));
  }
  get results() {
    return this.state.search?.response.results;
  }
  get queryText() {
    return this.state.query?.q || Fe().q;
  }
  get responseTime() {
    return this.state.search?.duration || et().duration;
  }
  get numberOfResults() {
    return this.state.search?.response.totalCountFiltered || et().response.totalCountFiltered;
  }
};
Ce(Cs, "fallbackPipelineName", "default");
var Yr = Cs;
var ey = ({ logger: e7, getState: t, analyticsClientMiddleware: r = (a, i) => i, preprocessRequest: n, provider: o = new Yr(t) }) => {
  let a = t(), i = a.configuration.accessToken, s = a.configuration.analytics.apiBaseUrl ?? Me(a.configuration.organizationId, a.configuration.environment, "analytics"), c = a.configuration.analytics.runtimeEnvironment, u = a.configuration.analytics.enabled, l = new Xc({ token: i, endpoint: s, runtimeEnvironment: c, preprocessRequest: fs(e7, n), beforeSendHooks: [gs(e7, r), (m, p) => (e7.info({ ...p, type: m, endpoint: s, token: i }, "Analytics request"), p)] }, o);
  return u || l.disable(), l;
};
var qm = () => {
  let t = dt.getHistory().reverse().find((r) => r.name === "PageView" && r.value);
  return t ? t.value : "";
};
function ou(e7) {
  let t = ty(e7), r = [e7, ...t].filter((o) => o.parentResult).map((o) => o.parentResult);
  return zg([e7, ...t, ...r], (o) => o.uniqueId);
}
function ty(e7) {
  return e7.childResults ? e7.childResults.flatMap((t) => [t, ...ty(t)]) : [];
}
var Tr = () => "";
function ry(e7, t) {
  return { ...new Yr(t).getBaseMetadata(), actionCause: e7, type: e7 };
}
function ZI(e7) {
  return Object.assign(e7, { instantlyCallable: true });
}
function eE(e7, t) {
  let r = (a) => ZI(W(e7, a)), n = r(async (a, { getState: i, extra: s }) => {
    let { analyticsClientMiddleware: c, preprocessRequest: u, logger: l } = s;
    return await (await t({ getState: i, analyticsClientMiddleware: c, preprocessRequest: u, logger: l })).log({ state: i(), extra: s });
  });
  return Object.assign(n, { prepare: async ({ getState: a, analyticsClientMiddleware: i, preprocessRequest: s, logger: c }) => {
    let { description: u, log: l } = await t({ getState: a, analyticsClientMiddleware: i, preprocessRequest: s, logger: c });
    return { description: u, action: r(async (m, { getState: p, extra: d }) => await l({ state: p(), extra: d })) };
  } }), n;
}
var ny = (e7, t, r) => {
  function n(...o) {
    let a = o.length === 1 ? { ...o[0], __legacy__getBuilder: t(o[0].__legacy__getBuilder), analyticsConfigurator: e7, providerClass: r } : { prefix: o[0], __legacy__getBuilder: t(o[1]), __legacy__provider: o[2], analyticsConfigurator: e7, providerClass: r };
    return nE(a);
  }
  return n;
};
var tE = (e7) => e7.configuration.analytics.analyticsMode === "legacy";
var rE = (e7) => e7.configuration.analytics.analyticsMode === "next";
var nE = ({ prefix: e7, __legacy__getBuilder: t, __legacy__provider: r, analyticsPayloadBuilder: n, analyticsType: o, analyticsConfigurator: a, providerClass: i }) => (r ?? (r = (s) => new i(s)), eE(e7, async ({ getState: s, analyticsClientMiddleware: c, preprocessRequest: u, logger: l }) => {
  let m = [], p = { log: async ({ state: g }) => {
    for (let C of m)
      await C(g);
  } }, d = s(), f = a({ getState: s, logger: l, analyticsClientMiddleware: c, preprocessRequest: u, provider: r(s) }), x2 = await t(f, s());
  p.description = x2?.description, m.push(async (g) => {
    tE(g) && await oE(x2, r, g, l, f.coveoAnalyticsClient);
  });
  let { emit: S } = Lo(d);
  return m.push(async (g) => {
    if (rE(g) && o && n) {
      let C = n(g);
      await mE(S, o, C);
    }
  }), p;
}));
async function oE(e7, t, r, n, o) {
  t(() => r);
  let a = await e7?.log({ searchUID: t(() => r).getSearchUID() });
  n.info({ client: o, response: a }, "Analytics response");
}
var L = ny(ey, (e7) => e7, Yr);
var iy = { urihash: new StringValue(), sourcetype: new StringValue(), permanentid: new StringValue() };
var iu = { uniqueId: V, raw: new RecordValue({ values: iy }), title: V, uri: V, clickUri: V, rankingModifier: new StringValue({ required: false, emptyAllowed: true }) };
function cE(e7) {
  return Object.assign({}, ...Object.keys(iy).map((t) => ({ [t]: e7[t] })));
}
function uE(e7) {
  return Object.assign({}, ...Object.keys(iu).map((t) => ({ [t]: e7[t] })), { raw: cE(e7.raw) });
}
var Ke = (e7) => new Schema(iu).validate(uE(e7));
async function mE(e7, t, r) {
  await e7(t, r);
}
var Nm = () => de;
var gy = () => V;
var Ut = h2("configuration/updateBasicConfiguration", (e7) => F(e7, { accessToken: de, environment: new StringValue({ required: false, constrainTo: ["prod", "hipaa", "stg", "dev"] }), organizationId: de }));
var mt = h2("configuration/updateSearchConfiguration", (e7) => F(e7, { proxyBaseUrl: new StringValue({ required: false, url: true }), pipeline: new StringValue({ required: false, emptyAllowed: true }), searchHub: de, timezone: de, locale: de, authenticationProviders: new ArrayValue({ required: false, each: V }) }));
var hE = { enabled: new BooleanValue({ default: true }), originContext: Nm(), originLevel2: Nm(), originLevel3: Nm(), proxyBaseUrl: new StringValue({ required: false, url: true }), runtimeEnvironment: new Value(), anonymous: new BooleanValue({ default: false }), deviceId: de, userDisplayName: de, documentLocation: de, trackingId: de, analyticsMode: new StringValue({ constrainTo: ["legacy", "next"], required: false, default: "next" }), source: new RecordValue({ options: { required: false }, values: ph.reduce((e7, t) => (e7[t] = wS, e7), {}) }) };
var Xr = h2("configuration/updateAnalyticsConfiguration", (e7) => F(e7, hE));
var ea = h2("configuration/analytics/disable");
var ta = h2("configuration/analytics/enable");
var lu = h2("configuration/analytics/originlevel2", (e7) => F(e7, { originLevel2: gy() }));
var du = h2("configuration/analytics/originlevel3", (e7) => F(e7, { originLevel3: gy() }));
var pu = { q: new StringValue(), enableQuerySyntax: new BooleanValue(), aq: new StringValue(), cq: new StringValue(), firstResult: new NumberValue({ min: 0 }), numberOfResults: new NumberValue({ min: 0 }), sortCriteria: new StringValue(), f: new RecordValue(), fExcluded: new RecordValue(), cf: new RecordValue(), nf: new RecordValue(), mnf: new RecordValue(), df: new RecordValue(), debug: new BooleanValue(), sf: new RecordValue(), tab: new StringValue(), af: new RecordValue() };
var ie = h2("searchParameters/restore", (e7) => F(e7, pu));
var en = h2("debug/enable");
var ra = h2("debug/disable");
var tn = () => false;
$(tn(), (e7) => {
  e7.addCase(en, () => true).addCase(ra, () => false).addCase(ie, (t, r) => r.payload.debug ?? t);
});
var Mm = h2("history/undo");
var Qm = h2("history/redo");
var ot = h2("history/snapshot");
W("history/back", async (e7, { dispatch: t }) => {
  t(Mm()), await t(ae());
});
W("history/forward", async (e7, { dispatch: t }) => {
  t(Qm()), await t(ae());
});
var ae = W("history/change", async (e7, { getState: t }) => t().history.present);
var oa = h2("pipeline/set", (e7) => F(e7, new StringValue({ required: true, emptyAllowed: true })));
$(Tr(), (e7) => {
  e7.addCase(oa, (t, r) => r.payload).addCase(ae.fulfilled, (t, r) => r.payload?.pipeline ?? t).addCase(mt, (t, r) => r.payload.pipeline || t);
});
var ia = h2("searchHub/set", (e7) => F(e7, new StringValue({ required: true, emptyAllowed: true })));
$(Kr(), (e7) => {
  e7.addCase(ia, (t, r) => r.payload).addCase(ae.fulfilled, (t, r) => r.payload?.searchHub ?? t).addCase(mt, (t, r) => r.payload.searchHub || t);
});
var Se = h2("breadcrumb/deselectAll");
var _t = h2("breadcrumb/deselectAllNonBreadcrumbs");
var ft = h2("facet/updateFacetAutoSelection", (e7) => F(e7, { allow: new BooleanValue({ required: true }) }));
var Rs = class extends Yr {
  constructor(r) {
    super(r);
    this.getState = r;
  }
  get activeInstantResultQuery() {
    let r = this.getState().instantResults;
    for (let n in r)
      for (let o in r[n].cache)
        if (r[n].cache[o].isActive)
          return r[n].q;
    return null;
  }
  get activeInstantResultCache() {
    let r = this.getState().instantResults;
    for (let n in r)
      for (let o in r[n].cache)
        if (r[n].cache[o].isActive)
          return r[n].cache[o];
    return null;
  }
  get results() {
    return this.activeInstantResultCache?.results;
  }
  get queryText() {
    return this.activeInstantResultQuery ?? Fe().q;
  }
  get responseTime() {
    return this.activeInstantResultCache?.duration ?? et().duration;
  }
  get numberOfResults() {
    return this.activeInstantResultCache?.totalCountFiltered ?? et().response.totalCountFiltered;
  }
  getSearchUID() {
    return this.activeInstantResultCache?.searchUid || super.getSearchUID();
  }
};
var Cy = () => L("analytics/instantResult/searchboxAsYouType", (e7) => e7.makeSearchboxAsYouType(), (e7) => new Rs(e7));
var xy = () => ({ actionCause: "searchboxAsYouType" });
var Lm = { id: V };
var AE = { ...Lm, q: ce };
var ca = h2("instantResults/register", (e7) => F(e7, Lm));
var jt = h2("instantResults/updateQuery", (e7) => F(e7, AE));
var ua = h2("instantResults/clearExpired", (e7) => F(e7, Lm));
var fu = new NumberValue({ required: true, min: 0 });
var la = h2("pagination/registerNumberOfResults", (e7) => F(e7, fu));
var da = h2("pagination/updateNumberOfResults", (e7) => F(e7, fu));
var pa = h2("pagination/registerPage", (e7) => F(e7, fu));
var gt = h2("pagination/updatePage", (e7) => F(e7, fu));
var ma = h2("pagination/nextPage");
var fa = h2("pagination/previousPage");
var Le = h2("query/updateQuery", (e7) => F(e7, { q: new StringValue(), enableQuerySyntax: new BooleanValue() }));
var ga = (e7, t, r) => ({ analytics: { clientId: t.clientId, clientTimestamp: (/* @__PURE__ */ new Date()).toISOString(), documentReferrer: t.referrer, documentLocation: t.location, originContext: e7.originContext, ...r && { actionCause: r.actionCause }, ...r && { customData: r.customData }, ...e7.userDisplayName && { userDisplayName: e7.userDisplayName }, ...e7.deviceId && { deviceId: e7.deviceId }, ...e7.trackingId && { trackingId: e7.trackingId }, capture: t.capture ?? t.clientId !== "", source: Hr(e7) } });
var Sa = (e7, t, r) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: e7.configuration.search.apiBaseUrl ?? ve(e7.configuration.organizationId, e7.configuration.environment), locale: e7.configuration.search.locale, debug: e7.debug, tab: e7.configuration.analytics.originLevel2, referrer: t.referrer, timezone: e7.configuration.search.timezone, ...e7.advancedSearchQueries?.aq && { aq: e7.advancedSearchQueries.aq }, ...e7.advancedSearchQueries?.cq && { cq: e7.advancedSearchQueries.cq }, ...e7.advancedSearchQueries?.lq && { lq: e7.advancedSearchQueries.lq }, ...e7.advancedSearchQueries?.dq && { dq: e7.advancedSearchQueries.dq }, ...e7.context && { context: e7.context.contextValues }, ...e7.fields && !e7.fields.fetchAllFields && { fieldsToInclude: e7.fields.fieldsToInclude }, ...e7.dictionaryFieldContext && { dictionaryFieldContext: e7.dictionaryFieldContext.contextValues }, ...e7.pipeline && { pipeline: e7.pipeline }, ...e7.query && { q: e7.query.q, enableQuerySyntax: e7.query.enableQuerySyntax }, ...e7.searchHub && { searchHub: e7.searchHub }, ...e7.sortCriteria && { sortCriteria: e7.sortCriteria }, ...e7.configuration.analytics.enabled && ga(e7.configuration.analytics, t, r), ...e7.excerptLength && !isNullOrUndefined(e7.excerptLength.length) && { excerptLength: e7.excerptLength.length }, ...e7.configuration.search.authenticationProviders.length && { authentication: e7.configuration.search.authenticationProviders.join(",") } });
var ha = async (e7, t) => {
  let r = e7.analyticsMode === "next";
  return { analytics: { clientId: await Lh(e7), clientTimestamp: (/* @__PURE__ */ new Date()).toISOString(), documentReferrer: e7.originLevel3, originContext: e7.originContext, ...t && { actionCause: t.actionCause, customData: t.customData }, ...t && !r && { customData: t.customData }, ...e7.userDisplayName && { userDisplayName: e7.userDisplayName }, ...e7.documentLocation && { documentLocation: e7.documentLocation }, ...e7.deviceId && { deviceId: e7.deviceId }, ...qm() && { pageId: qm() }, ...r && e7.trackingId && { trackingId: e7.trackingId }, capture: r, ...r && { source: Hr(e7) } } };
};
var rn = async (e7, t) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: e7.configuration.search.apiBaseUrl ?? ve(e7.configuration.organizationId, e7.configuration.environment), locale: e7.configuration.search.locale, debug: e7.debug, tab: e7.configuration.analytics.originLevel2, referrer: e7.configuration.analytics.originLevel3, timezone: e7.configuration.search.timezone, ...e7.configuration.analytics.enabled && { actionsHistory: dt.getHistory() }, ...e7.advancedSearchQueries?.aq && { aq: e7.advancedSearchQueries.aq }, ...e7.advancedSearchQueries?.cq && { cq: e7.advancedSearchQueries.cq }, ...e7.advancedSearchQueries?.lq && { lq: e7.advancedSearchQueries.lq }, ...e7.advancedSearchQueries?.dq && { dq: e7.advancedSearchQueries.dq }, ...e7.context && { context: e7.context.contextValues }, ...e7.fields && !e7.fields.fetchAllFields && { fieldsToInclude: e7.fields.fieldsToInclude }, ...e7.dictionaryFieldContext && { dictionaryFieldContext: e7.dictionaryFieldContext.contextValues }, ...e7.pipeline && { pipeline: e7.pipeline }, ...e7.query && { q: e7.query.q, enableQuerySyntax: e7.query.enableQuerySyntax }, ...e7.searchHub && { searchHub: e7.searchHub }, ...e7.sortCriteria && { sortCriteria: e7.sortCriteria }, ...e7.configuration.analytics.enabled && await ha(e7.configuration.analytics, t), ...e7.excerptLength && !isNullOrUndefined(e7.excerptLength.length) && { excerptLength: e7.excerptLength.length }, ...e7.configuration.search.authenticationProviders.length && { authentication: e7.configuration.search.authenticationProviders.join(",") } });
var It = () => ({ cq: "", cqWasSet: false, aq: "", aqWasSet: false, lq: "", lqWasSet: false, dq: "", dqWasSet: false, defaultFilters: { cq: "", aq: "", lq: "", dq: "" } });
var Bm = () => L("search/logFetchMoreResults", (e7) => e7.makeFetchMoreResults());
var nn = (e7) => L("search/queryError", (t, r) => t.makeQueryError({ query: r.query?.q || Fe().q, aq: r.advancedSearchQueries?.aq || It().aq, cq: r.advancedSearchQueries?.cq || It().cq, dq: r.advancedSearchQueries?.dq || It().dq, errorType: e7.type, errorMessage: e7.message }));
var Ps = Vt(gu());
var Py = Vt(Ay());
var Su = Vt(gu());
var Ry = Vt(Fy());
Su.default.extend(Ry.default);
var bs = "YYYY/MM/DD@HH:mm:ss";
var wE = "1401-01-01";
function eo(e7, t) {
  let r = (0, Su.default)(e7, t);
  return !r.isValid() && !t ? (0, Su.default)(e7, bs) : r;
}
function vs(e7) {
  return e7.format(bs);
}
function hu(e7, t) {
  let r = eo(e7, t);
  if (!r.isValid()) {
    let n = ". Please provide a date format string in the configuration options. See https://day.js.org/docs/en/parse/string-format for more information.", o = ` with the format "${t}"`;
    throw new Error(`Could not parse the provided date "${e7}"${t ? o : n}`);
  }
  Hm(r);
}
function Hm(e7) {
  if (e7.isBefore(wE))
    throw new Error(`Date is before year 1401, which is unsupported by the API: ${e7}`);
}
Ps.default.extend(Py.default);
var wy = ["past", "now", "next"];
var Iy = ["minute", "hour", "day", "week", "month", "quarter", "year"];
var TE = (e7) => {
  let t = e7 === "now";
  return { amount: new NumberValue({ required: !t, min: 1 }), unit: new StringValue({ required: !t, constrainTo: Iy }), period: new StringValue({ required: true, constrainTo: wy }) };
};
function to(e7) {
  if (typeof e7 == "string" && !$t(e7))
    throw new Error(`The value "${e7}" is not respecting the relative date format "period-amount-unit"`);
  let t = typeof e7 == "string" ? zm(e7) : e7;
  new Schema(TE(t.period)).validate(t);
  let r = Ty(t), n = JSON.stringify(t);
  if (!r.isValid())
    throw new Error(`Date is invalid: ${n}`);
  Hm(r);
}
function Ey(e7) {
  let { period: t, amount: r, unit: n } = e7;
  switch (t) {
    case "past":
    case "next":
      return `${t}-${r}-${n}`;
    case "now":
      return t;
  }
}
function Ty(e7) {
  let { period: t, amount: r, unit: n } = e7;
  switch (t) {
    case "past":
      return (0, Ps.default)().subtract(r, n);
    case "next":
      return (0, Ps.default)().add(r, n);
    case "now":
      return (0, Ps.default)();
  }
}
function ws(e7) {
  return vs(Ty(zm(e7)));
}
function ky(e7) {
  return e7.toLocaleLowerCase().split("-");
}
function $t(e7) {
  let [t, r, n] = ky(e7);
  if (t === "now")
    return true;
  if (!wy.includes(t) || !Iy.includes(n))
    return false;
  let o = parseInt(r);
  return !(isNaN(o) || o <= 0);
}
function Oy(e7) {
  return !!e7 && typeof e7 == "object" && "period" in e7;
}
function zm(e7) {
  let [t, r, n] = ky(e7);
  return t === "now" ? { period: "now" } : { period: t, amount: r ? parseInt(r) : void 0, unit: n || void 0 };
}
function qy(e7) {
  return e7.type === "dateRange";
}
function Dy(e7) {
  return `start${e7}`;
}
function Vy(e7) {
  return `end${e7}`;
}
var Km = () => ({ dateFacetValueMap: {} });
function OE(e7, t, r) {
  let n = e7.start, o = e7.end;
  return $t(n) && (n = ws(n), r.dateFacetValueMap[t][Dy(n)] = e7.start), $t(o) && (o = ws(o), r.dateFacetValueMap[t][Vy(o)] = e7.end), { ...e7, start: n, end: o };
}
function Ym(e7, t) {
  if (qy(e7)) {
    let { facetId: r, currentValues: n } = e7;
    return t.dateFacetValueMap[r] = {}, { ...e7, currentValues: n.map((o) => OE(o, r, t)) };
  }
  return e7;
}
function on(e7) {
  let t = Km();
  return { request: { ...e7, facets: e7.facets?.map((n) => Ym(n, t)) }, mappings: t };
}
function qE(e7, t, r) {
  return { ...e7, start: r.dateFacetValueMap[t][Dy(e7.start)] || e7.start, end: r.dateFacetValueMap[t][Vy(e7.end)] || e7.end };
}
function DE(e7, t) {
  return e7.facetId in t.dateFacetValueMap;
}
function VE(e7, t) {
  return DE(e7, t) ? { ...e7, values: e7.values.map((r) => qE(r, e7.facetId, t)) } : e7;
}
function yu(e7, t) {
  return "success" in e7 ? { success: { ...e7.success, facets: e7.success.facets?.map((n) => VE(n, t)) } } : e7;
}
var ya = h2("didYouMean/enable");
var Cu = h2("didYouMean/disable");
var Ca = h2("didYouMean/automaticCorrections/disable");
var xu = h2("didYouMean/automaticCorrections/enable");
var St = h2("didYouMean/correction", (e7) => F(e7, V));
var ro = h2("didYouMean/automaticCorrections/mode", (e7) => F(e7, new StringValue({ constrainTo: ["next", "legacy"], emptyAllowed: false, required: true })));
var Jm = () => L("analytics/didyoumean/automatic", (e7) => e7.makeDidYouMeanAutomatic());
var My = () => ({ actionCause: "didYouMeanAutomatic" });
function Fu() {
  return { contextValues: {} };
}
function Ru() {
  return { contextValues: {} };
}
function Xm() {
  return { enabled: true, tabs: {} };
}
function bu() {
  return { freezeFacetOrder: false, facets: {} };
}
function xa() {
  return [];
}
function ht() {
  return { firstResult: 0, defaultNumberOfResults: 10, numberOfResults: 10, totalCountFiltered: 0 };
}
function vu() {
  return {};
}
function Pu() {
  return {};
}
function wu() {
  return {};
}
function Qy() {
  return Et({});
}
function Et(e7) {
  return { context: e7.context || Fu(), dictionaryFieldContext: e7.dictionaryFieldContext || Ru(), facetSet: e7.facetSet || Ko(), numericFacetSet: e7.numericFacetSet || zo(), dateFacetSet: e7.dateFacetSet || Ho(), categoryFacetSet: e7.categoryFacetSet || Wo(), automaticFacetSet: e7.automaticFacetSet ?? Go(), pagination: e7.pagination || ht(), query: e7.query || Fe(), tabSet: e7.tabSet || wu(), advancedSearchQueries: e7.advancedSearchQueries || It(), staticFilterSet: e7.staticFilterSet || Pu(), querySet: e7.querySet || vu(), sortCriteria: e7.sortCriteria || pt(), pipeline: e7.pipeline || Tr(), searchHub: e7.searchHub || Kr(), facetOptions: e7.facetOptions || bu(), facetOrder: e7.facetOrder ?? xa(), debug: e7.debug ?? tn() };
}
var Iu = () => L("analytics/trigger/query", (e7, t) => t.triggers?.queryModification.newQuery ? e7.makeTriggerQuery() : null);
var an = h2("trigger/query/ignore", (e7) => F(e7, new StringValue({ emptyAllowed: true, required: true })));
var Aa = h2("trigger/query/modification", (e7) => F(e7, new RecordValue({ values: { originalQuery: de, modification: de } })));
function sn(e7) {
  return Object.values(e7).map((t) => t.request);
}
function Is(e7, t) {
  let r = {};
  e7.forEach((a) => r[a.facetId] = a);
  let n = [];
  t.forEach((a) => {
    a in r && (n.push(r[a]), delete r[a]);
  });
  let o = Object.values(r);
  return [...n, ...o];
}
function Ly(e7) {
  return sn(e7).map((t) => {
    let n = t.currentValues.some(({ state: o }) => o !== "idle");
    return t.generateAutomaticRanges && !n ? { ...t, currentValues: [] } : t;
  });
}
var Zm = { alphanumericDescending: { type: "alphanumeric", order: "descending" }, alphanumericNaturalDescending: { type: "alphanumericNatural", order: "descending" } };
function UE(e7) {
  return sn(e7).map((t) => {
    let r = Zm[t.sortCriteria];
    return r ? { ...t, sortCriteria: r } : t;
  });
}
function _E(e7) {
  return [...UE(e7.facetSet ?? {}), ...Ly(e7.numericFacetSet ?? {}), ...Ly(e7.dateFacetSet ?? {}), ...sn(e7.categoryFacetSet ?? {})];
}
function jE(e7) {
  return _E(e7).filter(({ facetId: t }) => e7.facetOptions?.facets[t]?.enabled ?? true);
}
function qu(e7) {
  return Is(jE(e7), e7.facetOrder ?? []);
}
var cn = async (e7, t) => {
  let r = WE(e7), n = qu(e7), o = $E(e7), a = await rn(e7, t), i = () => e7.pagination ? e7.pagination.firstResult + e7.pagination.numberOfResults > 5e3 ? 5e3 - e7.pagination.firstResult : e7.pagination.numberOfResults : void 0;
  return on({ ...a, ...e7.didYouMean && { queryCorrection: { enabled: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "next", options: { automaticallyCorrect: e7.didYouMean.automaticallyCorrectQuery ? "whenNoResults" : "never" } }, enableDidYouMean: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "legacy" }, ...r && { cq: r }, ...n.length && { facets: n }, ...e7.pagination && { numberOfResults: i(), firstResult: e7.pagination.firstResult }, ...e7.facetOptions && { facetOptions: { freezeFacetOrder: e7.facetOptions.freezeFacetOrder } }, ...e7.folding?.enabled && { filterField: e7.folding.fields.collection, childField: e7.folding.fields.parent, parentField: e7.folding.fields.child, filterFieldRange: e7.folding.filterFieldRange }, ...e7.automaticFacetSet && { generateAutomaticFacets: { desiredCount: e7.automaticFacetSet.desiredCount, numberOfValues: e7.automaticFacetSet.numberOfValues, currentFacets: o } }, ...e7.generatedAnswer && { pipelineRuleParameters: { mlGenerativeQuestionAnswering: { responseFormat: e7.generatedAnswer.responseFormat, citationsFieldToInclude: e7.generatedAnswer.fieldsToIncludeInCitations } } } });
};
function $E(e7) {
  let t = e7.automaticFacetSet?.set;
  return t ? Object.values(t).map((r) => r.response).map(GE).filter((r) => r.currentValues.length > 0) : void 0;
}
function GE(e7) {
  let { field: t, label: r, values: n } = e7, o = n.filter((a) => a.state === "selected");
  return { field: t, label: r, currentValues: o };
}
function WE(e7) {
  let t = e7.advancedSearchQueries?.cq.trim() || "", n = Object.values(e7.tabSet || {}).find((a) => a.isActive)?.expression.trim() || "", o = HE(e7);
  return [t, n, ...o].filter((a) => !!a).join(" AND ");
}
function HE(e7) {
  return Object.values(e7.staticFilterSet || {}).map((r) => {
    let n = r.values.filter((a) => a.state === "selected" && !!a.expression.trim()), o = n.map((a) => a.expression).join(" OR ");
    return n.length > 1 ? `(${o})` : o;
  });
}
var un = class {
  constructor(t, r = (n) => {
    this.dispatch(Le({ q: n }));
  }) {
    this.config = t;
    this.onUpdateQueryForCorrection = r;
  }
  async fetchFromAPI({ mappings: t, request: r }, n) {
    let o = (/* @__PURE__ */ new Date()).getTime(), a = yu(await this.extra.apiClient.search(r, n), t), i = (/* @__PURE__ */ new Date()).getTime() - o, s = this.getState().query?.q || "";
    return { response: a, duration: i, queryExecuted: s, requestExecuted: r };
  }
  async process(t) {
    return this.processQueryErrorOrContinue(t) ?? await this.processQueryCorrectionsOrContinue(t) ?? await this.processQueryTriggersOrContinue(t) ?? this.processSuccessResponse(t);
  }
  processQueryErrorOrContinue(t) {
    return we(t.response) ? (this.dispatch(nn(t.response.error)), this.rejectWithValue(t.response.error)) : null;
  }
  async processQueryCorrectionsOrContinue(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    if (!n || !r.didYouMean)
      return null;
    let { enableDidYouMean: o, automaticallyCorrectQuery: a } = r.didYouMean, { results: i, queryCorrections: s, queryCorrection: c } = n;
    if (!o || !a)
      return null;
    let u = i.length === 0 && s && s.length !== 0, l = !isNullOrUndefined(c) && !isNullOrUndefined(c.correctedQuery);
    if (!u && !l)
      return null;
    let p = u ? await this.processLegacyDidYouMeanAutoCorrection(t) : this.processModernDidYouMeanAutoCorrection(t);
    return this.dispatch(ot(Et(this.getState()))), p;
  }
  async processLegacyDidYouMeanAutoCorrection(t) {
    let r = this.getCurrentQuery(), n = this.getSuccessResponse(t);
    if (!n.queryCorrections)
      return null;
    let { correctedQuery: o } = n.queryCorrections[0], a = await this.automaticallyRetryQueryWithCorrection(o);
    return we(a.response) ? (this.dispatch(nn(a.response.error)), this.rejectWithValue(a.response.error)) : (this.logOriginalAnalyticsQueryBeforeAutoCorrection(t), this.dispatch(ot(Et(this.getState()))), { ...a, response: { ...a.response.success, queryCorrections: n.queryCorrections }, automaticallyCorrected: true, originalQuery: r, analyticsAction: Jm() });
  }
  processModernDidYouMeanAutoCorrection(t) {
    let r = this.getSuccessResponse(t), { correctedQuery: n, originalQuery: o } = r.queryCorrection;
    return this.onUpdateQueryForCorrection(n), { ...t, response: { ...r }, queryExecuted: n, automaticallyCorrected: true, originalQuery: o, analyticsAction: Jm() };
  }
  logOriginalAnalyticsQueryBeforeAutoCorrection(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    this.analyticsAction && this.analyticsAction()(this.dispatch, () => this.getStateAfterResponse(t.queryExecuted, t.duration, r, n), this.extra);
  }
  async processQueryTriggersOrContinue(t) {
    let r = this.getSuccessResponse(t);
    if (!r)
      return null;
    let n = r.triggers.find((s) => s.type === "query")?.content || "";
    if (!n)
      return null;
    if (this.getState().triggers?.queryModification.queryToIgnore === n)
      return this.dispatch(an("")), null;
    this.analyticsAction && await this.dispatch(this.analyticsAction);
    let a = this.getCurrentQuery(), i = await this.automaticallyRetryQueryWithTriggerModification(n);
    return we(i.response) ? (this.dispatch(nn(i.response.error)), this.rejectWithValue(i.response.error)) : (this.dispatch(ot(Et(this.getState()))), { ...i, response: { ...i.response.success }, automaticallyCorrected: false, originalQuery: a, analyticsAction: Iu() });
  }
  getStateAfterResponse(t, r, n, o) {
    return { ...n, query: { q: t, enableQuerySyntax: n.query?.enableQuerySyntax ?? Fe().enableQuerySyntax }, search: { ...et(), duration: r, response: o, results: o.results } };
  }
  processSuccessResponse(t) {
    return this.dispatch(ot(Et(this.getState()))), { ...t, response: this.getSuccessResponse(t), automaticallyCorrected: false, originalQuery: this.getCurrentQuery(), analyticsAction: this.analyticsAction };
  }
  getSuccessResponse(t) {
    return Ec(t.response) ? t.response.success : null;
  }
  async automaticallyRetryQueryWithCorrection(t) {
    this.onUpdateQueryForCorrection(t);
    let r = await this.fetchFromAPI(await cn(this.getState()), { origin: "mainSearch" });
    return this.dispatch(St(t)), r;
  }
  async automaticallyRetryQueryWithTriggerModification(t) {
    return this.dispatch(Aa({ newQuery: t, originalQuery: this.getCurrentQuery() })), this.onUpdateQueryForCorrection(t), await this.fetchFromAPI(await cn(this.getState()), { origin: "mainSearch" });
  }
  getCurrentQuery() {
    let t = this.getState();
    return t.query?.q !== void 0 ? t.query.q : "";
  }
  get extra() {
    return this.config.extra;
  }
  getState() {
    return this.config.getState();
  }
  get dispatch() {
    return this.config.dispatch;
  }
  get analyticsAction() {
    return this.config.analyticsAction;
  }
  get rejectWithValue() {
    return this.config.rejectWithValue;
  }
};
W("search/prepareForSearchWithQuery", (e7, t) => {
  let { dispatch: r } = t;
  F(e7, { q: new StringValue(), enableQuerySyntax: new BooleanValue(), clearFilters: new BooleanValue() }), e7.clearFilters && (r(Se()), r(_t())), r(ft({ allow: true })), r(Le({ q: e7.q, enableQuerySyntax: e7.enableQuerySyntax })), r(gt(1));
});
var Fa = W("search/executeSearch", async (e7, t) => {
  let r = t.getState();
  return await Vu(r, t, e7);
});
var Ra = W("search/fetchPage", async (e7, t) => {
  let r = t.getState();
  return await tf(r, t, e7);
});
var ba = W("search/fetchMoreResults", async (e7, t) => {
  let r = t.getState();
  return await rf(t, r);
});
var Du = W("search/fetchFacetValues", async (e7, t) => {
  let r = t.getState();
  return await XE(t, e7, r);
});
W("search/fetchInstantResults", async (e7, t) => ef(e7, t));
var KE = async (e7, t) => {
  let r = await cn(e7, t);
  return r.request = { ...r.request, firstResult: (e7.pagination?.firstResult ?? 0) + (e7.search?.results.length ?? 0) }, r;
};
var YE = async (e7, t, r) => {
  let n = await rn(e7);
  return on({ ...n, ...e7.didYouMean && { enableDidYouMean: e7.didYouMean.enableDidYouMean }, numberOfResults: r, q: t });
};
var JE = async (e7, t) => {
  let r = await cn(e7, t);
  return r.request.numberOfResults = 0, r;
};
var $y = (e7) => {
  e7.configuration.analytics.enabled && dt.addElement({ name: "Query", ...e7.query?.q && { value: e7.query.q }, time: JSON.stringify(/* @__PURE__ */ new Date()) });
};
async function ef(e7, t) {
  F(e7, { id: V, q: V, maxResultsPerQuery: new NumberValue({ required: true, min: 1 }), cacheTimeout: new NumberValue() });
  let { q: r, maxResultsPerQuery: n } = e7, o = t.getState(), a = new un({ ...t, analyticsAction: Cy() }, (u) => {
    t.dispatch(jt({ q: u, id: e7.id }));
  }), i = await YE(o, r, n), s = await a.fetchFromAPI(i, { origin: "instantResults", disableAbortWarning: true }), c = await a.process(s);
  return "response" in c ? { results: c.response.results, searchUid: c.response.searchUid, analyticsAction: c.analyticsAction, totalCountFiltered: c.response.totalCountFiltered, duration: c.duration } : c;
}
async function tf(e7, t, r) {
  $y(e7);
  let { analyticsClientMiddleware: n, preprocessRequest: o, logger: a } = t.extra, { description: i } = await r.prepare({ getState: () => t.getState(), analyticsClientMiddleware: n, preprocessRequest: o, logger: a }), s = new un({ ...t, analyticsAction: r }), c = await cn(e7, i), u = await s.fetchFromAPI(c, { origin: "mainSearch" });
  return await s.process(u);
}
async function rf(e7, t) {
  let { analyticsClientMiddleware: r, preprocessRequest: n, logger: o } = e7.extra, { description: a } = await Bm().prepare({ getState: () => e7.getState(), analyticsClientMiddleware: r, preprocessRequest: n, logger: o }), i = new un({ ...e7, analyticsAction: Bm() }), s = await KE(t, a), c = await i.fetchFromAPI(s, { origin: "mainSearch" });
  return await i.process(c);
}
async function XE(e7, t, r) {
  let { analyticsClientMiddleware: n, preprocessRequest: o, logger: a } = e7.extra, { description: i } = await t.prepare({ getState: () => e7.getState(), analyticsClientMiddleware: n, preprocessRequest: o, logger: a }), s = new un({ ...e7, analyticsAction: t }), c = await JE(r, i), u = await s.fetchFromAPI(c, { origin: "facetValues" });
  return await s.process(u);
}
async function Vu(e7, t, r) {
  $y(e7);
  let { analyticsClientMiddleware: n, preprocessRequest: o, logger: a } = t.extra, { description: i } = await r.prepare({ getState: () => t.getState(), analyticsClientMiddleware: n, preprocessRequest: o, logger: a }), s = await cn(e7, i), c = new un({ ...t, analyticsAction: r }), u = await c.fetchFromAPI(s, { origin: "mainSearch" });
  return await c.process(u);
}
var yt = async (e7, t, r) => {
  let n = aT(e7), o = ZE(e7), a = eT(e7), i = e7.configuration.analytics.analyticsMode === "legacy" ? await rn(e7, r) : Sa(e7, t, r), s = () => e7.pagination ? e7.pagination.firstResult + e7.pagination.numberOfResults > 5e3 ? 5e3 - e7.pagination.firstResult : e7.pagination.numberOfResults : void 0;
  return on({ ...i, ...e7.didYouMean && { queryCorrection: { enabled: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "next", options: { automaticallyCorrect: e7.didYouMean.automaticallyCorrectQuery ? "whenNoResults" : "never" } }, enableDidYouMean: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "legacy" }, ...n && { cq: n }, ...o.length && { facets: o }, ...e7.pagination && { numberOfResults: s(), firstResult: e7.pagination.firstResult }, ...e7.facetOptions && { facetOptions: { freezeFacetOrder: e7.facetOptions.freezeFacetOrder } }, ...e7.folding?.enabled && { filterField: e7.folding.fields.collection, childField: e7.folding.fields.parent, parentField: e7.folding.fields.child, filterFieldRange: e7.folding.filterFieldRange }, ...e7.automaticFacetSet && { generateAutomaticFacets: { desiredCount: e7.automaticFacetSet.desiredCount, numberOfValues: e7.automaticFacetSet.numberOfValues, currentFacets: a } }, ...e7.generatedAnswer && { pipelineRuleParameters: { mlGenerativeQuestionAnswering: { responseFormat: e7.generatedAnswer.responseFormat, citationsFieldToInclude: e7.generatedAnswer.fieldsToIncludeInCitations } } } });
};
function ZE(e7) {
  return Is(rT(e7), e7.facetOrder ?? []);
}
function eT(e7) {
  let t = e7.automaticFacetSet?.set;
  return t ? Object.values(t).map((r) => r.response).map(tT).filter((r) => r.currentValues.length > 0) : void 0;
}
function tT(e7) {
  let { field: t, label: r, values: n } = e7, o = n.filter((a) => a.state === "selected");
  return { field: t, label: r, currentValues: o };
}
function rT(e7) {
  return nT(e7).filter(({ facetId: t }) => e7.facetOptions?.facets[t]?.enabled ?? true);
}
function nT(e7) {
  return [...oT(e7.facetSet ?? {}), ...Gy(e7.numericFacetSet ?? {}), ...Gy(e7.dateFacetSet ?? {}), ...sn(e7.categoryFacetSet ?? {})];
}
function oT(e7) {
  return sn(e7).map((t) => {
    let r = Zm[t.sortCriteria];
    return r ? { ...t, sortCriteria: r } : t;
  });
}
function Gy(e7) {
  return sn(e7).map((t) => {
    let n = t.currentValues.some(({ state: o }) => o !== "idle");
    return t.generateAutomaticRanges && !n ? { ...t, currentValues: [] } : t;
  });
}
function aT(e7) {
  let t = e7.advancedSearchQueries?.cq.trim() || "", n = Object.values(e7.tabSet || {}).find((a) => a.isActive)?.expression.trim() || "", o = iT(e7);
  return [t, n, ...o].filter((a) => !!a).join(" AND ");
}
function iT(e7) {
  return Object.values(e7.staticFilterSet || {}).map((r) => {
    let n = r.values.filter((a) => a.state === "selected" && !!a.expression.trim()), o = n.map((a) => a.expression).join(" OR ");
    return n.length > 1 ? `(${o})` : o;
  });
}
var ln = class {
  constructor(t, r = (n) => {
    this.dispatch(Le({ q: n }));
  }) {
    this.config = t;
    this.onUpdateQueryForCorrection = r;
  }
  async fetchFromAPI({ mappings: t, request: r }, n) {
    let o = (/* @__PURE__ */ new Date()).getTime(), a = yu(await this.extra.apiClient.search(r, n), t), i = (/* @__PURE__ */ new Date()).getTime() - o, s = this.getState().query?.q || "";
    return { response: a, duration: i, queryExecuted: s, requestExecuted: r };
  }
  async process(t) {
    return this.processQueryErrorOrContinue(t) ?? await this.processQueryCorrectionsOrContinue(t) ?? await this.processQueryTriggersOrContinue(t) ?? this.processSuccessResponse(t);
  }
  processQueryErrorOrContinue(t) {
    return we(t.response) ? (this.dispatch(nn(t.response.error)), this.rejectWithValue(t.response.error)) : null;
  }
  async processQueryCorrectionsOrContinue(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    if (!n || !r.didYouMean)
      return null;
    let { enableDidYouMean: o, automaticallyCorrectQuery: a } = r.didYouMean, { results: i, queryCorrections: s, queryCorrection: c } = n;
    if (!o || !a)
      return null;
    let u = i.length === 0 && s && s.length !== 0, l = !isNullOrUndefined(c) && !isNullOrUndefined(c.correctedQuery);
    if (!u && !l)
      return null;
    let p = u ? await this.processLegacyDidYouMeanAutoCorrection(t) : this.processModernDidYouMeanAutoCorrection(t);
    return this.dispatch(ot(Et(this.getState()))), p;
  }
  async processLegacyDidYouMeanAutoCorrection(t) {
    let r = this.getCurrentQuery(), n = this.getSuccessResponse(t);
    if (!n.queryCorrections)
      return null;
    let { correctedQuery: o } = n.queryCorrections[0], a = await this.automaticallyRetryQueryWithCorrection(o);
    return we(a.response) ? (this.dispatch(nn(a.response.error)), this.rejectWithValue(a.response.error)) : (this.dispatch(ot(Et(this.getState()))), { ...a, response: { ...a.response.success, queryCorrections: n.queryCorrections }, automaticallyCorrected: true, originalQuery: r });
  }
  processModernDidYouMeanAutoCorrection(t) {
    let r = this.getSuccessResponse(t), { correctedQuery: n, originalQuery: o } = r.queryCorrection;
    return this.onUpdateQueryForCorrection(n), { ...t, response: { ...r }, queryExecuted: n, automaticallyCorrected: true, originalQuery: o };
  }
  async processQueryTriggersOrContinue(t) {
    let r = this.getSuccessResponse(t);
    if (!r)
      return null;
    let n = r.triggers.find((s) => s.type === "query")?.content || "";
    if (!n)
      return null;
    if (this.getState().triggers?.queryModification.queryToIgnore === n)
      return this.dispatch(an("")), null;
    let a = this.getCurrentQuery(), i = await this.automaticallyRetryQueryWithTriggerModification(n);
    return we(i.response) ? (this.dispatch(nn(i.response.error)), this.rejectWithValue(i.response.error)) : (this.dispatch(ot(Et(this.getState()))), { ...i, response: { ...i.response.success }, automaticallyCorrected: false, originalQuery: a });
  }
  processSuccessResponse(t) {
    return this.dispatch(ot(Et(this.getState()))), { ...t, response: this.getSuccessResponse(t), automaticallyCorrected: false, originalQuery: this.getCurrentQuery() };
  }
  getSuccessResponse(t) {
    return Ec(t.response) ? t.response.success : null;
  }
  async automaticallyRetryQueryWithCorrection(t) {
    this.onUpdateQueryForCorrection(t);
    let r = this.getState(), { actionCause: n } = My(), o = await this.fetchFromAPI(await yt(r, this.extra.navigatorContext, { actionCause: n }), { origin: "mainSearch" });
    return this.dispatch(St(t)), o;
  }
  async automaticallyRetryQueryWithTriggerModification(t) {
    return this.dispatch(Aa({ newQuery: t, originalQuery: this.getCurrentQuery() })), this.onUpdateQueryForCorrection(t), await this.fetchFromAPI(await yt(this.getState(), this.extra.navigatorContext), { origin: "mainSearch" });
  }
  getCurrentQuery() {
    let t = this.getState();
    return t.query?.q !== void 0 ? t.query.q : "";
  }
  get extra() {
    return this.config.extra;
  }
  getState() {
    return this.config.getState();
  }
  get dispatch() {
    return this.config.dispatch;
  }
  get rejectWithValue() {
    return this.config.rejectWithValue;
  }
};
W("search/prepareForSearchWithQuery", (e7, t) => {
  let { dispatch: r } = t;
  F(e7, { q: new StringValue(), enableQuerySyntax: new BooleanValue(), clearFilters: new BooleanValue() }), e7.clearFilters && (r(Se()), r(_t())), r(ft({ allow: true })), r(Le({ q: e7.q, enableQuerySyntax: e7.enableQuerySyntax })), r(gt(1));
});
var N = W("search/executeSearch", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return Vu(r, t, e7.legacy);
  Ky(r);
  let n = e7.next ? Yy(e7.next) : void 0, o = await yt(r, t.extra.navigatorContext, n), a = new ln({ ...t, analyticsAction: n ?? {} }), i = await a.fetchFromAPI(o, { origin: "mainSearch" });
  return await a.process(i);
});
var Wt = W("search/fetchPage", async (e7, t) => {
  let r = t.getState();
  if (Ky(r), r.configuration.analytics.analyticsMode === "legacy" || !e7.next)
    return tf(r, t, e7.legacy);
  let n = new ln({ ...t, analyticsAction: e7.next }), o = await yt(r, t.extra.navigatorContext, e7.next), a = await n.fetchFromAPI(o, { origin: "mainSearch" });
  return await n.process(a);
});
var dn = W("search/fetchMoreResults", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return rf(t, r);
  let n = ry("browseResults", t.getState), o = new ln({ ...t, analyticsAction: n }), a = await cT(r, t.extra.navigatorContext, n), i = await o.fetchFromAPI(a, { origin: "mainSearch" });
  return await o.process(i);
});
var Ht = W("search/fetchFacetValues", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return Vu(r, t, e7.legacy);
  let n = new ln({ ...t, analyticsAction: {} }), o = await lT(r, t.extra.navigatorContext), a = await n.fetchFromAPI(o, { origin: "facetValues" });
  return await n.process(a);
});
var Pa = W("search/fetchInstantResults", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return ef(e7, t);
  F(e7, { id: V, q: V, maxResultsPerQuery: new NumberValue({ required: true, min: 1 }), cacheTimeout: new NumberValue() });
  let { q: n, maxResultsPerQuery: o } = e7, a = Yy(xy()), i = await uT(r, t.extra.navigatorContext, n, o, a), s = new ln({ ...t, analyticsAction: a }, (l) => {
    t.dispatch(jt({ q: l, id: e7.id }));
  }), c = await s.fetchFromAPI(i, { origin: "instantResults", disableAbortWarning: true }), u = await s.process(c);
  return "response" in u ? { results: u.response.results, searchUid: u.response.searchUid, totalCountFiltered: u.response.totalCountFiltered, duration: u.duration } : u;
});
var cT = async (e7, t, r) => {
  let n = await yt(e7, t, r);
  return n.request = { ...n.request, firstResult: (e7.pagination?.firstResult ?? 0) + (e7.search?.results.length ?? 0) }, n;
};
var uT = async (e7, t, r, n, o) => {
  let a = Sa(e7, t, o);
  return on({ ...a, ...e7.didYouMean && { enableDidYouMean: e7.didYouMean.enableDidYouMean }, numberOfResults: n, q: r });
};
var lT = async (e7, t, r) => {
  let n = await yt(e7, t, r);
  return n.request.numberOfResults = 0, n;
};
var Ky = (e7) => {
  e7.configuration.analytics.enabled && dt.addElement({ name: "Query", ...e7.query?.q && { value: e7.query.q }, time: JSON.stringify(/* @__PURE__ */ new Date()) });
};
var Yy = (e7) => ({ actionCause: e7.actionCause, type: e7.actionCause });
function nf(e7, t) {
  let r = t.payload ?? null;
  r && (e7.response = et().response, e7.results = [], e7.questionAnswer = qo()), e7.error = r, e7.isLoading = false;
}
function af(e7, t) {
  e7.error = null, e7.response = t.payload.response, e7.queryExecuted = t.payload.queryExecuted, e7.duration = t.payload.duration, e7.isLoading = false;
}
function ST(e7, t) {
  af(e7, t), e7.results = t.payload.response.results.map((r) => ({ ...r, searchUid: t.payload.response.searchUid })), e7.searchResponseId = t.payload.response.searchUid, e7.questionAnswer = t.payload.response.questionAnswer, e7.extendedResults = t.payload.response.extendedResults;
}
function of(e7, t) {
  e7.isLoading = true, e7.requestId = t.meta.requestId;
}
$(et(), (e7) => {
  e7.addCase(Fa.rejected, (t, r) => nf(t, r)), e7.addCase(ba.rejected, (t, r) => nf(t, r)), e7.addCase(Ra.rejected, (t, r) => nf(t, r)), e7.addCase(Fa.fulfilled, (t, r) => {
    ST(t, r);
  }), e7.addCase(ba.fulfilled, (t, r) => {
    af(t, r), t.results = [...t.results, ...r.payload.response.results.map((n) => ({ ...n, searchUid: r.payload.response.searchUid }))];
  }), e7.addCase(Ra.fulfilled, (t, r) => {
    af(t, r), t.results = [...r.payload.response.results.map((n) => ({ ...n, searchUid: r.payload.response.searchUid }))];
  }), e7.addCase(Du.fulfilled, (t, r) => {
    t.response.facets = r.payload.response.facets, t.response.searchUid = r.payload.response.searchUid;
  }), e7.addCase(Fa.pending, of), e7.addCase(ba.pending, of), e7.addCase(Ra.pending, of);
});
var Ts = Y((e7) => e7.query, (e7) => e7);
var Ct = (e7) => CT(e7) ? { answerAPIEnabled: true, id: Os(e7).data?.answerId } : yT(e7) ? { answerAPIEnabled: false, id: e7.search.response.extendedResults.generativeQuestionAnsweringId } : { answerAPIEnabled: false, id: void 0 };
var yT = (e7) => "search" in e7;
var CT = (e7) => "answer" in e7 && "generatedAnswer" in e7 && !isNullOrUndefined(e7.generatedAnswer?.answerConfigurationId);
var Zy = (e7) => e7.generatedAnswer?.fieldsToIncludeInCitations;
Y((e7) => e7.generatedAnswer?.citations, (e7, t) => t, (e7, t) => e7?.find((r) => r.id === t));
Y((e7) => Ts(e7)?.q, (e7) => e7.search.requestId, (e7, t) => ({ q: e7, requestId: t }));
var qs = (e7) => L({ prefix: "analytics/generatedAnswer/streamEnd", __legacy__getBuilder: (t, r) => {
  let { id: n, answerAPIEnabled: o } = Ct(r), a = e7 ? !r.generatedAnswer?.answer || !r.generatedAnswer?.answer.length : void 0;
  return n ? t.makeGeneratedAnswerStreamEnd({ ...o ? { answerAPIStreamId: n } : { generativeQuestionAnsweringId: n }, answerGenerated: e7, answerTextIsEmpty: a }) : null;
}, analyticsType: "Rga.AnswerReceived", analyticsPayloadBuilder: (t) => ({ answerId: t.search?.response.searchUid || "", answerGenerated: e7 ?? false }) });
var eC = async (e7) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: Me(e7.configuration.organizationId, e7.configuration.environment), streamId: e7.search.extendedResults?.generativeQuestionAnsweringId });
var tC = ["text/plain", "text/markdown"];
var wa = new StringValue({ required: true });
var nC = new StringValue();
var Ia = new BooleanValue({ required: true });
var DT = { id: wa, title: wa, uri: wa, permanentid: wa, clickUri: nC };
var oC = new StringValue({ required: true, constrainTo: tC });
var Ea = h2("generatedAnswer/setIsVisible", (e7) => F(e7, Ia));
var Ns = h2("generatedAnswer/setIsEnabled", (e7) => F(e7, Ia));
var Ms = h2("generatedAnswer/updateMessage", (e7) => F(e7, { textDelta: wa }));
var Qs = h2("generatedAnswer/updateCitations", (e7) => F(e7, { citations: new ArrayValue({ required: true, each: new RecordValue({ values: DT }) }) }));
var sf = h2("generatedAnswer/updateError", (e7) => F(e7, { message: nC, code: new NumberValue({ min: 0 }) }));
var zt = h2("generatedAnswer/resetAnswer");
var Bu = h2("generatedAnswer/like");
var Uu = h2("generatedAnswer/dislike");
var _u = h2("generatedAnswer/feedbackModal/open");
var Ls = h2("generatedAnswer/expand");
var ju = h2("generatedAnswer/collapse");
var $u = h2("generatedAnswer/setId", (e7) => F(e7, { id: new StringValue({ required: true }) }));
var Gu = h2("generatedAnswer/feedbackModal/close");
var Ta = h2("generatedAnswer/sendFeedback");
var Vs = h2("generatedAnswer/setIsLoading", (e7) => F(e7, Ia));
var Qu = h2("generatedAnswer/setIsStreaming", (e7) => F(e7, Ia));
var Bs = h2("generatedAnswer/setAnswerContentFormat", (e7) => F(e7, oC));
var Wu = h2("generatedAnswer/updateResponseFormat", (e7) => F(e7, { contentFormat: new ArrayValue({ each: oC, default: ["text/plain"] }) }));
var Hu = h2("knowledge/updateAnswerConfigurationId", (e7) => F(e7, wa));
var zu = h2("generatedAnswer/registerFieldsToIncludeInCitations", (e7) => F(e7, Tc));
var cf = h2("generatedAnswer/setIsAnswerGenerated", (e7) => F(e7, Ia));
var no = h2("generatedAnswer/setCannotAnswer", (e7) => F(e7, Ia));
W("generatedAnswer/streamAnswer", async (e7, t) => {
  let r = t.getState(), { dispatch: n, extra: o, getState: a } = t, { search: i } = a(), { queryExecuted: s } = i, { setAbortControllerRef: c } = e7, u = await eC(r), l = (d, f) => {
    switch (d) {
      case "genqa.headerMessageType": {
        let x2 = JSON.parse(f);
        n(Bs(x2.contentFormat));
        break;
      }
      case "genqa.messageType":
        n(Ms(JSON.parse(f)));
        break;
      case "genqa.citationsType":
        n(Qs(JSON.parse(f)));
        break;
      case "genqa.endOfStreamType": {
        let x2 = JSON.parse(f).answerGenerated, S = s.length !== 0 && !x2;
        n(no(S)), n(Qu(false)), n(cf(x2)), n(qs(x2));
        break;
      }
      default:
        r.debug && o.logger.warn(`Unknown payloadType: "${d}"`);
    }
  };
  n(Vs(true));
  let m = (d) => d.streamId === t.getState().search.extendedResults.generativeQuestionAnsweringId, p = o.streamingClient?.streamGeneratedAnswer(u, { write: (d) => {
    m(u) && (n(Vs(false)), d.payload && d.payloadType && l(d.payloadType, d.payload));
  }, abort: (d) => {
    m(u) && n(sf(d));
  }, close: () => {
    m(u) && n(Qu(false));
  }, resetAnswer: () => {
    m(u) && n(zt());
  } });
  p ? c(p) : n(Vs(false));
});
var iC = Y((e7) => e7.pipeline, (e7) => e7);
var sC = Y((e7) => e7.searchHub, (e7) => e7);
function cC(e7) {
  return { status: e7, isUninitialized: e7 === "uninitialized", isLoading: e7 === "pending", isSuccess: e7 === "fulfilled", isError: e7 === "rejected" };
}
var uC = Nt;
function AC(e7, t) {
  if (e7 === t || !(uC(e7) && uC(t) || Array.isArray(e7) && Array.isArray(t)))
    return t;
  let r = Object.keys(t), n = Object.keys(e7), o = r.length === n.length, a = Array.isArray(t) ? [] : {};
  for (let i of r)
    a[i] = AC(e7[i], t[i]), o && (o = e7[i] === a[i]);
  return o ? e7 : a;
}
function ka(e7) {
  let t = 0;
  for (let r in e7)
    t++;
  return t;
}
var lC = (e7) => [].concat(...e7);
function VT(e7) {
  return new RegExp("(^|:)//").test(e7);
}
function NT() {
  return typeof document > "u" ? true : document.visibilityState !== "hidden";
}
function Ju(e7) {
  return e7 != null;
}
function MT() {
  return typeof navigator > "u" || navigator.onLine === void 0 ? true : navigator.onLine;
}
var QT = (e7) => e7.replace(/\/$/, "");
var LT = (e7) => e7.replace(/^\//, "");
function BT(e7, t) {
  if (!e7)
    return t;
  if (!t)
    return e7;
  if (VT(t))
    return t;
  let r = e7.endsWith("/") || !t.startsWith("?") ? "/" : "";
  return e7 = QT(e7), t = LT(t), `${e7}${r}${t}`;
}
function UT(e7, t, r) {
  return e7.has(t) ? e7.get(t) : e7.set(t, r).get(t);
}
var dC = (...e7) => fetch(...e7);
var _T = (e7) => e7.status >= 200 && e7.status <= 299;
var jT = (e7) => /ion\/(vnd\.api\+)?json/.test(e7.get("content-type") || "");
function pC(e7) {
  if (!Nt(e7))
    return e7;
  let t = { ...e7 };
  for (let [r, n] of Object.entries(t))
    n === void 0 && delete t[r];
  return t;
}
function FC({ baseUrl: e7, prepareHeaders: t = (m) => m, fetchFn: r = dC, paramsSerializer: n, isJsonContentType: o = jT, jsonContentType: a = "application/json", jsonReplacer: i, timeout: s, responseHandler: c, validateStatus: u, ...l } = {}) {
  return typeof fetch > "u" && r === dC && console.warn("Warning: `fetch` is not available. Please supply a custom `fetchFn` property to use `fetchBaseQuery` on SSR environments."), async (p, d, f) => {
    let { getState: x2, extra: S, endpoint: g, forced: C, type: y } = d, A, { url: I, headers: v = new Headers(l.headers), params: R = void 0, responseHandler: b = c ?? "json", validateStatus: P = u ?? _T, timeout: T = s, ...B } = typeof p == "string" ? { url: p } : p, D, O = d.signal;
    T && (D = new AbortController(), d.signal.addEventListener("abort", D.abort), O = D.signal);
    let k = { ...l, signal: O, ...B };
    v = new Headers(pC(v)), k.headers = await t(v, { getState: x2, arg: p, extra: S, endpoint: g, forced: C, type: y, extraOptions: f }) || v;
    let Q = (J) => typeof J == "object" && (Nt(J) || Array.isArray(J) || typeof J.toJSON == "function");
    if (!k.headers.has("content-type") && Q(k.body) && k.headers.set("content-type", a), Q(k.body) && o(k.headers) && (k.body = JSON.stringify(k.body, i)), R) {
      let J = ~I.indexOf("?") ? "&" : "?", re = n ? n(R) : new URLSearchParams(pC(R));
      I += J + re;
    }
    I = BT(e7, I);
    let q = new Request(I, k);
    A = { request: new Request(I, k) };
    let _, H2 = false, ee = D && setTimeout(() => {
      H2 = true, D.abort();
    }, T);
    try {
      _ = await r(q);
    } catch (J) {
      return { error: { status: H2 ? "TIMEOUT_ERROR" : "FETCH_ERROR", error: String(J) }, meta: A };
    } finally {
      ee && clearTimeout(ee), D?.signal.removeEventListener("abort", D.abort);
    }
    let oe = _.clone();
    A.response = oe;
    let X, te = "";
    try {
      let J;
      if (await Promise.all([m(_, b).then((re) => X = re, (re) => J = re), oe.text().then((re) => te = re, () => {
      })]), J)
        throw J;
    } catch (J) {
      return { error: { status: "PARSING_ERROR", originalStatus: _.status, data: te, error: String(J) }, meta: A };
    }
    return P(_, X) ? { data: X, meta: A } : { error: { status: _.status, data: X }, meta: A };
  };
  async function m(p, d) {
    if (typeof d == "function")
      return d(p);
    if (d === "content-type" && (d = o(p.headers) ? "json" : "text"), d === "json") {
      let f = await p.text();
      return f.length ? JSON.parse(f) : null;
    }
    return p.text();
  }
}
var Oa = class {
  constructor(e7, t = void 0) {
    this.value = e7, this.meta = t;
  }
};
async function $T(e7 = 0, t = 5) {
  let r = Math.min(e7, t), n = ~~((Math.random() + 0.4) * (300 << r));
  await new Promise((o) => setTimeout((a) => o(a), n));
}
function GT(e7, t) {
  throw Object.assign(new Oa({ error: e7, meta: t }), { throwImmediately: true });
}
var mC = {};
var WT = (e7, t) => async (r, n, o) => {
  let a = [5, (t || mC).maxRetries, (o || mC).maxRetries].filter((l) => l !== void 0), [i] = a.slice(-1), c = { maxRetries: i, backoff: $T, retryCondition: (l, m, { attempt: p }) => p <= i, ...t, ...o }, u = 0;
  for (; ; )
    try {
      let l = await e7(r, n, o);
      if (l.error)
        throw new Oa(l);
      return l;
    } catch (l) {
      if (u++, l.throwImmediately) {
        if (l instanceof Oa)
          return l.value;
        throw l;
      }
      if (l instanceof Oa && !c.retryCondition(l.value.error, r, { attempt: u, baseQueryApi: n, extraOptions: o }))
        return l.value;
      await c.backoff(u, c.maxRetries);
    }
};
var RC = Object.assign(WT, { fail: GT });
var mf = h2("__rtkq/focused");
var bC = h2("__rtkq/unfocused");
var ff = h2("__rtkq/online");
var vC = h2("__rtkq/offline");
function gf(e7) {
  return e7.type === "query";
}
function HT(e7) {
  return e7.type === "mutation";
}
function Sf(e7) {
  return e7.type === "infinitequery";
}
function hf(e7, t, r, n, o, a) {
  return zT(e7) ? e7(t, r, n, o).filter(Ju).map(lf).map(a) : Array.isArray(e7) ? e7.map(lf).map(a) : [];
}
function zT(e7) {
  return typeof e7 == "function";
}
function lf(e7) {
  return typeof e7 == "string" ? { type: e7 } : e7;
}
function KT(e7, t) {
  return e7.catch(t);
}
var _s = Symbol("forceQueryFn");
var df = (e7) => typeof e7[_s] == "function";
function YT({ serializeQueryArgs: e7, queryThunk: t, infiniteQueryThunk: r, mutationThunk: n, api: o, context: a }) {
  let i = /* @__PURE__ */ new Map(), s = /* @__PURE__ */ new Map(), { unsubscribeQueryResult: c, removeMutationResult: u, updateSubscriptionOptions: l } = o.internalActions;
  return { buildInitiateQuery: g, buildInitiateInfiniteQuery: C, buildInitiateMutation: y, getRunningQueryThunk: m, getRunningMutationThunk: p, getRunningQueriesThunk: d, getRunningMutationsThunk: f };
  function m(A, I) {
    return (v) => {
      let R = a.endpointDefinitions[A], b = e7({ queryArgs: I, endpointDefinition: R, endpointName: A });
      return i.get(v)?.[b];
    };
  }
  function p(A, I) {
    return (v) => s.get(v)?.[I];
  }
  function d() {
    return (A) => Object.values(i.get(A) || {}).filter(Ju);
  }
  function f() {
    return (A) => Object.values(s.get(A) || {}).filter(Ju);
  }
  function S(A, I) {
    let v = (R, { subscribe: b = true, forceRefetch: P, subscriptionOptions: T, [_s]: B, ...D } = {}) => (O, k) => {
      let Q = e7({ queryArgs: R, endpointDefinition: I, endpointName: A }), q, U = { ...D, type: "query", subscribe: b, forceRefetch: P, subscriptionOptions: T, endpointName: A, originalArgs: R, queryCacheKey: Q, [_s]: B };
      if (gf(I))
        q = t(U);
      else {
        let { direction: se2, initialPageParam: fe } = D;
        q = r({ ...U, direction: se2, initialPageParam: fe });
      }
      let _ = o.endpoints[A].select(R), H2 = O(q), ee = _(k());
      let { requestId: oe, abort: X } = H2, te = ee.requestId !== oe, J = i.get(O)?.[Q], re = () => _(k()), ge = Object.assign(B ? H2.then(re) : te && !J ? Promise.resolve(ee) : Promise.all([J, H2]).then(re), { arg: R, requestId: oe, subscriptionOptions: T, queryCacheKey: Q, abort: X, async unwrap() {
        let se2 = await ge;
        if (se2.isError)
          throw se2.error;
        return se2.data;
      }, refetch: () => O(v(R, { subscribe: false, forceRefetch: true })), unsubscribe() {
        b && O(c({ queryCacheKey: Q, requestId: oe }));
      }, updateSubscriptionOptions(se2) {
        ge.subscriptionOptions = se2, O(l({ endpointName: A, requestId: oe, queryCacheKey: Q, options: se2 }));
      } });
      if (!J && !te && !B) {
        let se2 = UT(i, O, {});
        se2[Q] = ge, ge.then(() => {
          delete se2[Q], ka(se2) || i.delete(O);
        });
      }
      return ge;
    };
    return v;
  }
  function g(A, I) {
    return S(A, I);
  }
  function C(A, I) {
    return S(A, I);
  }
  function y(A) {
    return (I, { track: v = true, fixedCacheKey: R } = {}) => (b, P) => {
      let T = n({ type: "mutation", endpointName: A, originalArgs: I, track: v, fixedCacheKey: R }), B = b(T);
      let { requestId: D, abort: O, unwrap: k } = B, Q = KT(B.unwrap().then((H2) => ({ data: H2 })), (H2) => ({ error: H2 })), q = () => {
        b(u({ requestId: D, fixedCacheKey: R }));
      }, U = Object.assign(Q, { arg: B.arg, requestId: D, abort: O, unwrap: k, reset: q }), _ = s.get(b) || {};
      return s.set(b, _), _[D] = U, U.then(() => {
        delete _[D], ka(_) || s.delete(b);
      }), R && (_[R] = U, U.then(() => {
        _[R] === U && (delete _[R], ka(_) || s.delete(b));
      })), U;
    };
  }
}
function JT(e7) {
  return e7;
}
var Ku = (e7 = {}) => ({ ...e7, [ss]: true });
function XT({ reducerPath: e7, baseQuery: t, context: { endpointDefinitions: r }, serializeQueryArgs: n, api: o, assertTagType: a, selectors: i }) {
  let s = (b, P, T, B) => (D, O) => {
    let k = r[b], Q = n({ queryArgs: P, endpointDefinition: k, endpointName: b });
    if (D(o.internalActions.queryResultPatched({ queryCacheKey: Q, patches: T })), !B)
      return;
    let q = o.endpoints[b].select(P)(O()), U = hf(k.providesTags, q.data, void 0, P, {}, a);
    D(o.internalActions.updateProvidedBy({ queryCacheKey: Q, providedTags: U }));
  };
  function c(b, P, T = 0) {
    let B = [P, ...b];
    return T && B.length > T ? B.slice(0, -1) : B;
  }
  function u(b, P, T = 0) {
    let B = [...b, P];
    return T && B.length > T ? B.slice(1) : B;
  }
  let l = (b, P, T, B = true) => (D, O) => {
    let Q = o.endpoints[b].select(P)(O()), q = { patches: [], inversePatches: [], undo: () => D(o.util.patchQueryData(b, P, q.inversePatches, B)) };
    if (Q.status === "uninitialized")
      return q;
    let U;
    if ("data" in Q)
      if (He(Q.data)) {
        let [_, H2, ee] = Mc(Q.data, T);
        q.patches.push(...H2), q.inversePatches.push(...ee), U = _;
      } else
        U = T(Q.data), q.patches.push({ op: "replace", path: [], value: U }), q.inversePatches.push({ op: "replace", path: [], value: Q.data });
    return q.patches.length === 0 || D(o.util.patchQueryData(b, P, q.patches, B)), q;
  }, m = (b, P, T) => (B) => B(o.endpoints[b].initiate(P, { subscribe: false, forceRefetch: true, [_s]: () => ({ data: T }) })), p = (b, P) => b.query && b[P] ? b[P] : JT, d = async (b, { signal: P, abort: T, rejectWithValue: B, fulfillWithValue: D, dispatch: O, getState: k, extra: Q }) => {
    let q = r[b.endpointName];
    try {
      let U = p(q, "transformResponse"), _ = { signal: P, abort: T, dispatch: O, getState: k, extra: Q, endpoint: b.endpointName, type: b.type, forced: b.type === "query" ? f(b, k()) : void 0, queryCacheKey: b.type === "query" ? b.queryCacheKey : void 0 }, H2 = b.type === "query" ? b[_s] : void 0, ee, oe = async (te, J, re, ge) => {
        if (J == null && te.pages.length)
          return Promise.resolve({ data: te });
        let se2 = { queryArg: b.originalArgs, pageParam: J }, fe = await X(se2), ye = ge ? c : u;
        return { data: { pages: ye(te.pages, fe.data, re), pageParams: ye(te.pageParams, J, re) } };
      };
      async function X(te) {
        let J, { extraOptions: re } = q;
        if (H2 ? J = H2() : q.query ? J = await t(q.query(te), _, re) : J = await q.queryFn(te, _, re, (se2) => t(se2, _, re)), J.error)
          throw new Oa(J.error, J.meta);
        let ge = await U(J.data, J.meta, te);
        return { ...J, data: ge };
      }
      if (b.type === "query" && "infiniteQueryOptions" in q) {
        let { infiniteQueryOptions: te } = q, { maxPages: J = 1 / 0 } = te, re, ge = { pages: [], pageParams: [] }, se2 = i.selectQueryEntry(k(), b.queryCacheKey)?.data, ye = f(b, k()) && !b.direction || !se2 ? ge : se2;
        if ("direction" in b && b.direction && ye.pages.length) {
          let Ge = b.direction === "backward", Ur = (Ge ? PC : pf)(te, ye);
          re = await oe(ye, Ur, J, Ge);
        } else {
          let { initialPageParam: Ge = te.initialPageParam } = b, it = se2?.pageParams ?? [], Ur = it[0] ?? Ge, Io2 = it.length;
          re = await oe(ye, Ur, J), H2 && (re = { data: re.data.pages[0] });
          for (let Eo = 1; Eo < Io2; Eo++) {
            let Wi = pf(te, re.data);
            re = await oe(re.data, Wi, J);
          }
        }
        ee = re;
      } else
        ee = await X(b.originalArgs);
      return D(ee.data, Ku({ fulfilledTimeStamp: Date.now(), baseQueryMeta: ee.meta }));
    } catch (U) {
      let _ = U;
      if (_ instanceof Oa) {
        let H2 = p(q, "transformErrorResponse");
        try {
          return B(await H2(_.value, _.meta, b.originalArgs), Ku({ baseQueryMeta: _.meta }));
        } catch (ee) {
          _ = ee;
        }
      }
      throw console.error(_), _;
    }
  };
  function f(b, P) {
    let T = i.selectQueryEntry(P, b.queryCacheKey), B = i.selectConfig(P).refetchOnMountOrArgChange, D = T?.fulfilledTimeStamp, O = b.forceRefetch ?? (b.subscribe && B);
    return O ? O === true || (Number(/* @__PURE__ */ new Date()) - Number(D)) / 1e3 >= O : false;
  }
  let x2 = () => W(`${e7}/executeQuery`, d, { getPendingMeta({ arg: P }) {
    let T = r[P.endpointName];
    return Ku({ startedTimeStamp: Date.now(), ...Sf(T) ? { direction: P.direction } : {} });
  }, condition(P, { getState: T }) {
    let B = T(), D = i.selectQueryEntry(B, P.queryCacheKey), O = D?.fulfilledTimeStamp, k = P.originalArgs, Q = D?.originalArgs, q = r[P.endpointName], U = P.direction;
    return df(P) ? true : D?.status === "pending" ? false : f(P, B) || gf(q) && q?.forceRefetch?.({ currentArg: k, previousArg: Q, endpointState: D, state: B }) ? true : !(O && !U);
  }, dispatchConditionRejection: true }), S = x2(), g = x2(), C = W(`${e7}/executeMutation`, d, { getPendingMeta() {
    return Ku({ startedTimeStamp: Date.now() });
  } }), y = (b) => "force" in b, A = (b) => "ifOlderThan" in b, I = (b, P, T) => (B, D) => {
    let O = y(T) && T.force, k = A(T) && T.ifOlderThan, Q = (U = true) => {
      let _ = { forceRefetch: U, isPrefetch: true };
      return o.endpoints[b].initiate(P, _);
    }, q = o.endpoints[b].select(P)(D());
    if (O)
      B(Q());
    else if (k) {
      let U = q?.fulfilledTimeStamp;
      if (!U) {
        B(Q());
        return;
      }
      (Number(/* @__PURE__ */ new Date()) - Number(new Date(U))) / 1e3 >= k && B(Q());
    } else
      B(Q(false));
  };
  function v(b) {
    return (P) => P?.meta?.arg?.endpointName === b;
  }
  function R(b, P) {
    return { matchPending: Mo(Uc(b), v(P)), matchFulfilled: Mo(Pr(b), v(P)), matchRejected: Mo(Kn(b), v(P)) };
  }
  return { queryThunk: S, mutationThunk: C, infiniteQueryThunk: g, prefetch: I, updateQueryData: l, upsertQueryData: m, patchQueryData: s, buildMatchThunkActions: R };
}
function pf(e7, { pages: t, pageParams: r }) {
  let n = t.length - 1;
  return e7.getNextPageParam(t[n], t, r[n], r);
}
function PC(e7, { pages: t, pageParams: r }) {
  return e7.getPreviousPageParam?.(t[0], t, r[0], r);
}
function wC(e7, t, r, n) {
  return hf(r[e7.meta.arg.endpointName][t], Pr(e7) ? e7.payload : void 0, us(e7) ? e7.payload : void 0, e7.meta.arg.originalArgs, "baseQueryMeta" in e7.meta ? e7.meta.baseQueryMeta : void 0, n);
}
function Yu(e7, t, r) {
  let n = e7[t];
  n && r(n);
}
function js(e7) {
  return ("arg" in e7 ? e7.arg.fixedCacheKey : e7.fixedCacheKey) ?? e7.requestId;
}
function fC(e7, t, r) {
  let n = e7[js(t)];
  n && r(n);
}
var Us = {};
function ZT({ reducerPath: e7, queryThunk: t, mutationThunk: r, serializeQueryArgs: n, context: { endpointDefinitions: o, apiUid: a, extractRehydrationInfo: i, hasRehydrationInfo: s }, assertTagType: c, config: u }) {
  let l = h2(`${e7}/resetApiState`);
  function m(v, R, b, P) {
    var T;
    v[T = R.queryCacheKey] ?? (v[T] = { status: "uninitialized", endpointName: R.endpointName }), Yu(v, R.queryCacheKey, (B) => {
      B.status = "pending", B.requestId = b && B.requestId ? B.requestId : P.requestId, R.originalArgs !== void 0 && (B.originalArgs = R.originalArgs), B.startedTimeStamp = P.startedTimeStamp;
      let D = o[P.arg.endpointName];
      Sf(D) && "direction" in R && (B.direction = R.direction);
    });
  }
  function p(v, R, b, P) {
    Yu(v, R.arg.queryCacheKey, (T) => {
      if (T.requestId !== R.requestId && !P)
        return;
      let { merge: B } = o[R.arg.endpointName];
      if (T.status = "fulfilled", B)
        if (T.data !== void 0) {
          let { fulfilledTimeStamp: D, arg: O, baseQueryMeta: k, requestId: Q } = R, q = vr(T.data, (U) => B(U, b, { arg: O.originalArgs, baseQueryMeta: k, fulfilledTimeStamp: D, requestId: Q }));
          T.data = q;
        } else
          T.data = b;
      else
        T.data = o[R.arg.endpointName].structuralSharing ?? true ? AC(tt(T.data) ? Xp(T.data) : T.data, b) : b;
      delete T.error, T.fulfilledTimeStamp = R.fulfilledTimeStamp;
    });
  }
  let d = Yn({ name: `${e7}/queries`, initialState: Us, reducers: { removeQueryResult: { reducer(v, { payload: { queryCacheKey: R } }) {
    delete v[R];
  }, prepare: Qo() }, cacheEntriesUpserted: { reducer(v, R) {
    for (let b of R.payload) {
      let { queryDescription: P, value: T } = b;
      m(v, P, true, { arg: P, requestId: R.meta.requestId, startedTimeStamp: R.meta.timestamp }), p(v, { arg: P, requestId: R.meta.requestId, fulfilledTimeStamp: R.meta.timestamp, baseQueryMeta: {} }, T, true);
    }
  }, prepare: (v) => ({ payload: v.map((P) => {
    let { endpointName: T, arg: B, value: D } = P, O = o[T];
    return { queryDescription: { type: "query", endpointName: T, originalArgs: P.arg, queryCacheKey: n({ queryArgs: B, endpointDefinition: O, endpointName: T }) }, value: D };
  }), meta: { [ss]: true, requestId: jc(), timestamp: Date.now() } }) }, queryResultPatched: { reducer(v, { payload: { queryCacheKey: R, patches: b } }) {
    Yu(v, R, (P) => {
      P.data = em(P.data, b.concat());
    });
  }, prepare: Qo() } }, extraReducers(v) {
    v.addCase(t.pending, (R, { meta: b, meta: { arg: P } }) => {
      let T = df(P);
      m(R, P, T, b);
    }).addCase(t.fulfilled, (R, { meta: b, payload: P }) => {
      let T = df(b.arg);
      p(R, b, P, T);
    }).addCase(t.rejected, (R, { meta: { condition: b, arg: P, requestId: T }, error: B, payload: D }) => {
      Yu(R, P.queryCacheKey, (O) => {
        if (!b) {
          if (O.requestId !== T)
            return;
          O.status = "rejected", O.error = D ?? B;
        }
      });
    }).addMatcher(s, (R, b) => {
      let { queries: P } = i(b);
      for (let [T, B] of Object.entries(P))
        (B?.status === "fulfilled" || B?.status === "rejected") && (R[T] = B);
    });
  } }), f = Yn({ name: `${e7}/mutations`, initialState: Us, reducers: { removeMutationResult: { reducer(v, { payload: R }) {
    let b = js(R);
    b in v && delete v[b];
  }, prepare: Qo() } }, extraReducers(v) {
    v.addCase(r.pending, (R, { meta: b, meta: { requestId: P, arg: T, startedTimeStamp: B } }) => {
      T.track && (R[js(b)] = { requestId: P, status: "pending", endpointName: T.endpointName, startedTimeStamp: B });
    }).addCase(r.fulfilled, (R, { payload: b, meta: P }) => {
      P.arg.track && fC(R, P, (T) => {
        T.requestId === P.requestId && (T.status = "fulfilled", T.data = b, T.fulfilledTimeStamp = P.fulfilledTimeStamp);
      });
    }).addCase(r.rejected, (R, { payload: b, error: P, meta: T }) => {
      T.arg.track && fC(R, T, (B) => {
        B.requestId === T.requestId && (B.status = "rejected", B.error = b ?? P);
      });
    }).addMatcher(s, (R, b) => {
      let { mutations: P } = i(b);
      for (let [T, B] of Object.entries(P))
        (B?.status === "fulfilled" || B?.status === "rejected") && T !== B?.requestId && (R[T] = B);
    });
  } }), x2 = Yn({ name: `${e7}/invalidation`, initialState: Us, reducers: { updateProvidedBy: { reducer(v, R) {
    var T, B;
    let { queryCacheKey: b, providedTags: P } = R.payload;
    for (let D of Object.values(v))
      for (let O of Object.values(D)) {
        let k = O.indexOf(b);
        k !== -1 && O.splice(k, 1);
      }
    for (let { type: D, id: O } of P) {
      let k = (T = v[D] ?? (v[D] = {}))[B = O || "__internal_without_id"] ?? (T[B] = []);
      k.includes(b) || k.push(b);
    }
  }, prepare: Qo() } }, extraReducers(v) {
    v.addCase(d.actions.removeQueryResult, (R, { payload: { queryCacheKey: b } }) => {
      for (let P of Object.values(R))
        for (let T of Object.values(P)) {
          let B = T.indexOf(b);
          B !== -1 && T.splice(B, 1);
        }
    }).addMatcher(s, (R, b) => {
      var T, B;
      let { provided: P } = i(b);
      for (let [D, O] of Object.entries(P))
        for (let [k, Q] of Object.entries(O)) {
          let q = (T = R[D] ?? (R[D] = {}))[B = k || "__internal_without_id"] ?? (T[B] = []);
          for (let U of Q)
            q.includes(U) || q.push(U);
        }
    }).addMatcher(Mt(Pr(t), us(t)), (R, b) => {
      let P = wC(b, "providesTags", o, c), { queryCacheKey: T } = b.meta.arg;
      x2.caseReducers.updateProvidedBy(R, x2.actions.updateProvidedBy({ queryCacheKey: T, providedTags: P }));
    });
  } }), S = Yn({ name: `${e7}/subscriptions`, initialState: Us, reducers: { updateSubscriptionOptions(v, R) {
  }, unsubscribeQueryResult(v, R) {
  }, internal_getRTKQSubscriptions() {
  } } }), g = Yn({ name: `${e7}/internalSubscriptions`, initialState: Us, reducers: { subscriptionsUpdated: { reducer(v, R) {
    return em(v, R.payload);
  }, prepare: Qo() } } }), C = Yn({ name: `${e7}/config`, initialState: { online: MT(), focused: NT(), middlewareRegistered: false, ...u }, reducers: { middlewareRegistered(v, { payload: R }) {
    v.middlewareRegistered = v.middlewareRegistered === "conflict" || a !== R ? "conflict" : true;
  } }, extraReducers: (v) => {
    v.addCase(ff, (R) => {
      R.online = true;
    }).addCase(vC, (R) => {
      R.online = false;
    }).addCase(mf, (R) => {
      R.focused = true;
    }).addCase(bC, (R) => {
      R.focused = false;
    }).addMatcher(s, (R) => ({ ...R }));
  } }), y = Do({ queries: d.reducer, mutations: f.reducer, provided: x2.reducer, subscriptions: g.reducer, config: C.reducer }), A = (v, R) => y(l.match(R) ? void 0 : v, R), I = { ...C.actions, ...d.actions, ...S.actions, ...g.actions, ...f.actions, ...x2.actions, resetApiState: l };
  return { reducer: A, actions: I };
}
var uf = Symbol.for("RTKQ/skipToken");
var IC = { status: "uninitialized" };
var gC = vr(IC, () => {
});
var SC = vr(IC, () => {
});
function ek({ serializeQueryArgs: e7, reducerPath: t, createSelector: r }) {
  let n = (y) => gC, o = (y) => SC;
  return { buildQuerySelector: p, buildInfiniteQuerySelector: d, buildMutationSelector: f, selectInvalidatedBy: x2, selectCachedArgsForQuery: S, selectApiState: i, selectQueries: s, selectMutations: u, selectQueryEntry: c, selectConfig: l };
  function a(y) {
    return { ...y, ...cC(y.status) };
  }
  function i(y) {
    return y[t];
  }
  function s(y) {
    return i(y)?.queries;
  }
  function c(y, A) {
    return s(y)?.[A];
  }
  function u(y) {
    return i(y)?.mutations;
  }
  function l(y) {
    return i(y)?.config;
  }
  function m(y, A, I) {
    return (v) => {
      if (v === uf)
        return r(n, I);
      let R = e7({ queryArgs: v, endpointDefinition: A, endpointName: y });
      return r((P) => c(P, R) ?? gC, I);
    };
  }
  function p(y, A) {
    return m(y, A, a);
  }
  function d(y, A) {
    let { infiniteQueryOptions: I } = A;
    function v(R) {
      let b = { ...R, ...cC(R.status) }, { isLoading: P, isError: T, direction: B } = b, D = B === "forward", O = B === "backward";
      return { ...b, hasNextPage: g(I, b.data), hasPreviousPage: C(I, b.data), isFetchingNextPage: P && D, isFetchingPreviousPage: P && O, isFetchNextPageError: T && D, isFetchPreviousPageError: T && O };
    }
    return m(y, A, v);
  }
  function f() {
    return (y) => {
      let A;
      return typeof y == "object" ? A = js(y) ?? uf : A = y, r(A === uf ? o : (R) => i(R)?.mutations?.[A] ?? SC, a);
    };
  }
  function x2(y, A) {
    let I = y[t], v = /* @__PURE__ */ new Set();
    for (let R of A.filter(Ju).map(lf)) {
      let b = I.provided[R.type];
      if (!b)
        continue;
      let P = (R.id !== void 0 ? b[R.id] : lC(Object.values(b))) ?? [];
      for (let T of P)
        v.add(T);
    }
    return lC(Array.from(v.values()).map((R) => {
      let b = I.queries[R];
      return b ? [{ queryCacheKey: R, endpointName: b.endpointName, originalArgs: b.originalArgs }] : [];
    }));
  }
  function S(y, A) {
    return Object.values(s(y)).filter((I) => I?.endpointName === A && I.status !== "uninitialized").map((I) => I.originalArgs);
  }
  function g(y, A) {
    return A ? pf(y, A) != null : false;
  }
  function C(y, A) {
    return !A || !y.getPreviousPageParam ? false : PC(y, A) != null;
  }
}
var hC = WeakMap ? /* @__PURE__ */ new WeakMap() : void 0;
var yC = ({ endpointName: e7, queryArgs: t }) => {
  let r = "", n = hC?.get(t);
  if (typeof n == "string")
    r = n;
  else {
    let o = JSON.stringify(t, (a, i) => (i = typeof i == "bigint" ? { $bigint: i.toString() } : i, i = Nt(i) ? Object.keys(i).sort().reduce((s, c) => (s[c] = i[c], s), {}) : i, i));
    Nt(t) && hC?.set(t, o), r = o;
  }
  return `${e7}(${r})`;
};
function tk(...e7) {
  return function(r) {
    let n = No((u) => r.extractRehydrationInfo?.(u, { reducerPath: r.reducerPath ?? "api" })), o = { reducerPath: "api", keepUnusedDataFor: 60, refetchOnMountOrArgChange: false, refetchOnFocus: false, refetchOnReconnect: false, invalidationBehavior: "delayed", ...r, extractRehydrationInfo: n, serializeQueryArgs(u) {
      let l = yC;
      if ("serializeQueryArgs" in u.endpointDefinition) {
        let m = u.endpointDefinition.serializeQueryArgs;
        l = (p) => {
          let d = m(p);
          return typeof d == "string" ? d : yC({ ...p, queryArgs: d });
        };
      } else
        r.serializeQueryArgs && (l = r.serializeQueryArgs);
      return l(u);
    }, tagTypes: [...r.tagTypes || []] }, a = { endpointDefinitions: {}, batch(u) {
      u();
    }, apiUid: jc(), extractRehydrationInfo: n, hasRehydrationInfo: No((u) => n(u) != null) }, i = { injectEndpoints: c, enhanceEndpoints({ addTagTypes: u, endpoints: l }) {
      if (u)
        for (let m of u)
          o.tagTypes.includes(m) || o.tagTypes.push(m);
      if (l)
        for (let [m, p] of Object.entries(l))
          typeof p == "function" ? p(a.endpointDefinitions[m]) : Object.assign(a.endpointDefinitions[m] || {}, p);
      return i;
    } }, s = e7.map((u) => u.init(i, o, a));
    function c(u) {
      let l = u.endpoints({ query: (m) => ({ ...m, type: "query" }), mutation: (m) => ({ ...m, type: "mutation" }), infiniteQuery: (m) => ({ ...m, type: "infinitequery" }) });
      for (let [m, p] of Object.entries(l)) {
        if (u.overrideExisting !== true && m in a.endpointDefinitions) {
          if (u.overrideExisting === "throw")
            throw new Error(Pt(39));
          continue;
        }
        a.endpointDefinitions[m] = p;
        for (let d of s)
          d.injectEndpoint(m, p);
      }
      return i;
    }
    return i.injectEndpoints({ endpoints: r.endpoints });
  };
}
function kr(e7, ...t) {
  return Object.assign(e7, ...t);
}
var rk = ({ api: e7, queryThunk: t, internalState: r }) => {
  let n = `${e7.reducerPath}/subscriptions`, o = null, a = null, { updateSubscriptionOptions: i, unsubscribeQueryResult: s } = e7.internalActions, c = (d, f) => {
    var S, g;
    if (i.match(f)) {
      let { queryCacheKey: C, requestId: y, options: A } = f.payload;
      return d?.[C]?.[y] && (d[C][y] = A), true;
    }
    if (s.match(f)) {
      let { queryCacheKey: C, requestId: y } = f.payload;
      return d[C] && delete d[C][y], true;
    }
    if (e7.internalActions.removeQueryResult.match(f))
      return delete d[f.payload.queryCacheKey], true;
    if (t.pending.match(f)) {
      let { meta: { arg: C, requestId: y } } = f, A = d[S = C.queryCacheKey] ?? (d[S] = {});
      return A[`${y}_running`] = {}, C.subscribe && (A[y] = C.subscriptionOptions ?? A[y] ?? {}), true;
    }
    let x2 = false;
    if (t.fulfilled.match(f) || t.rejected.match(f)) {
      let C = d[f.meta.arg.queryCacheKey] || {}, y = `${f.meta.requestId}_running`;
      x2 || (x2 = !!C[y]), delete C[y];
    }
    if (t.rejected.match(f)) {
      let { meta: { condition: C, arg: y, requestId: A } } = f;
      if (C && y.subscribe) {
        let I = d[g = y.queryCacheKey] ?? (d[g] = {});
        I[A] = y.subscriptionOptions ?? I[A] ?? {}, x2 = true;
      }
    }
    return x2;
  }, u = () => r.currentSubscriptions, p = { getSubscriptions: u, getSubscriptionCount: (d) => {
    let x2 = u()[d] ?? {};
    return ka(x2);
  }, isRequestSubscribed: (d, f) => !!u()?.[d]?.[f] };
  return (d, f) => {
    if (o || (o = JSON.parse(JSON.stringify(r.currentSubscriptions))), e7.util.resetApiState.match(d))
      return o = r.currentSubscriptions = {}, a = null, [true, false];
    if (e7.internalActions.internal_getRTKQSubscriptions.match(d))
      return [false, p];
    let x2 = c(r.currentSubscriptions, d), S = true;
    if (x2) {
      a || (a = setTimeout(() => {
        let y = JSON.parse(JSON.stringify(r.currentSubscriptions)), [, A] = Mc(o, () => y);
        f.next(e7.internalActions.subscriptionsUpdated(A)), o = y, a = null;
      }, 500));
      let g = typeof d.type == "string" && !!d.type.startsWith(n), C = t.rejected.match(d) && d.meta.condition && !!d.meta.arg.subscribe;
      S = !g && !C;
    }
    return [S, false];
  };
};
function nk(e7) {
  for (let t in e7)
    return false;
  return true;
}
var ok2 = 2147483647 / 1e3 - 1;
var ak = ({ reducerPath: e7, api: t, queryThunk: r, context: n, internalState: o, selectors: { selectQueryEntry: a, selectConfig: i } }) => {
  let { removeQueryResult: s, unsubscribeQueryResult: c, cacheEntriesUpserted: u } = t.internalActions, l = Mt(c.match, r.fulfilled, r.rejected, u.match);
  function m(S) {
    let g = o.currentSubscriptions[S];
    return !!g && !nk(g);
  }
  let p = {}, d = (S, g, C) => {
    let y = g.getState(), A = i(y);
    if (l(S)) {
      let I;
      if (u.match(S))
        I = S.payload.map((v) => v.queryDescription.queryCacheKey);
      else {
        let { queryCacheKey: v } = c.match(S) ? S.payload : S.meta.arg;
        I = [v];
      }
      f(I, g, A);
    }
    if (t.util.resetApiState.match(S))
      for (let [I, v] of Object.entries(p))
        v && clearTimeout(v), delete p[I];
    if (n.hasRehydrationInfo(S)) {
      let { queries: I } = n.extractRehydrationInfo(S);
      f(Object.keys(I), g, A);
    }
  };
  function f(S, g, C) {
    let y = g.getState();
    for (let A of S) {
      let I = a(y, A);
      x2(A, I?.endpointName, g, C);
    }
  }
  function x2(S, g, C, y) {
    let I = n.endpointDefinitions[g]?.keepUnusedDataFor ?? y.keepUnusedDataFor;
    if (I === 1 / 0)
      return;
    let v = Math.max(0, Math.min(I, ok2));
    if (!m(S)) {
      let R = p[S];
      R && clearTimeout(R), p[S] = setTimeout(() => {
        m(S) || C.dispatch(s({ queryCacheKey: S })), delete p[S];
      }, v * 1e3);
    }
  }
  return d;
};
var CC = new Error("Promise never resolved before cacheEntryRemoved.");
var ik = ({ api: e7, reducerPath: t, context: r, queryThunk: n, mutationThunk: o, internalState: a, selectors: { selectQueryEntry: i, selectApiState: s } }) => {
  let c = _c(n), u = _c(o), l = Pr(n, o), m = {};
  function p(g, C, y) {
    let A = m[g];
    A?.valueResolved && (A.valueResolved({ data: C, meta: y }), delete A.valueResolved);
  }
  function d(g) {
    let C = m[g];
    C && (delete m[g], C.cacheEntryRemoved());
  }
  let f = (g, C, y) => {
    let A = x2(g);
    function I(v, R, b, P) {
      let T = i(y, R), B = i(C.getState(), R);
      !T && B && S(v, P, R, C, b);
    }
    if (n.pending.match(g))
      I(g.meta.arg.endpointName, A, g.meta.requestId, g.meta.arg.originalArgs);
    else if (e7.internalActions.cacheEntriesUpserted.match(g))
      for (let { queryDescription: v, value: R } of g.payload) {
        let { endpointName: b, originalArgs: P, queryCacheKey: T } = v;
        I(b, T, g.meta.requestId, P), p(T, R, {});
      }
    else if (o.pending.match(g))
      C.getState()[t].mutations[A] && S(g.meta.arg.endpointName, g.meta.arg.originalArgs, A, C, g.meta.requestId);
    else if (l(g))
      p(A, g.payload, g.meta.baseQueryMeta);
    else if (e7.internalActions.removeQueryResult.match(g) || e7.internalActions.removeMutationResult.match(g))
      d(A);
    else if (e7.util.resetApiState.match(g))
      for (let v of Object.keys(m))
        d(v);
  };
  function x2(g) {
    return c(g) ? g.meta.arg.queryCacheKey : u(g) ? g.meta.arg.fixedCacheKey ?? g.meta.requestId : e7.internalActions.removeQueryResult.match(g) ? g.payload.queryCacheKey : e7.internalActions.removeMutationResult.match(g) ? js(g.payload) : "";
  }
  function S(g, C, y, A, I) {
    let v = r.endpointDefinitions[g], R = v?.onCacheEntryAdded;
    if (!R)
      return;
    let b = {}, P = new Promise((Q) => {
      b.cacheEntryRemoved = Q;
    }), T = Promise.race([new Promise((Q) => {
      b.valueResolved = Q;
    }), P.then(() => {
      throw CC;
    })]);
    T.catch(() => {
    }), m[y] = b;
    let B = e7.endpoints[g].select(v.type === "query" ? C : y), D = A.dispatch((Q, q, U) => U), O = { ...A, getCacheEntry: () => B(A.getState()), requestId: I, extra: D, updateCachedData: v.type === "query" ? (Q) => A.dispatch(e7.util.updateQueryData(g, C, Q)) : void 0, cacheDataLoaded: T, cacheEntryRemoved: P }, k = R(C, O);
    Promise.resolve(k).catch((Q) => {
      if (Q !== CC)
        throw Q;
    });
  }
  return f;
};
var sk = ({ api: e7, context: { apiUid: t }, reducerPath: r }) => (n, o) => {
  e7.util.resetApiState.match(n) && o.dispatch(e7.internalActions.middlewareRegistered(t));
};
var ck = ({ reducerPath: e7, context: t, context: { endpointDefinitions: r }, mutationThunk: n, queryThunk: o, api: a, assertTagType: i, refetchQuery: s, internalState: c }) => {
  let { removeQueryResult: u } = a.internalActions, l = Mt(Pr(n), us(n)), m = Mt(Pr(n, o), Kn(n, o)), p = [], d = (S, g) => {
    l(S) ? x2(wC(S, "invalidatesTags", r, i), g) : m(S) ? x2([], g) : a.util.invalidateTags.match(S) && x2(hf(S.payload, void 0, void 0, void 0, void 0, i), g);
  };
  function f(S) {
    let { queries: g, mutations: C } = S;
    for (let y of [g, C])
      for (let A in y)
        if (y[A]?.status === "pending")
          return true;
    return false;
  }
  function x2(S, g) {
    let C = g.getState(), y = C[e7];
    if (p.push(...S), y.config.invalidationBehavior === "delayed" && f(y))
      return;
    let A = p;
    if (p = [], A.length === 0)
      return;
    let I = a.util.selectInvalidatedBy(C, A);
    t.batch(() => {
      let v = Array.from(I.values());
      for (let { queryCacheKey: R } of v) {
        let b = y.queries[R], P = c.currentSubscriptions[R] ?? {};
        b && (ka(P) === 0 ? g.dispatch(u({ queryCacheKey: R })) : b.status !== "uninitialized" && g.dispatch(s(b)));
      }
    });
  }
  return d;
};
var uk = ({ reducerPath: e7, queryThunk: t, api: r, refetchQuery: n, internalState: o }) => {
  let a = {}, i = (d, f) => {
    (r.internalActions.updateSubscriptionOptions.match(d) || r.internalActions.unsubscribeQueryResult.match(d)) && u(d.payload, f), (t.pending.match(d) || t.rejected.match(d) && d.meta.condition) && u(d.meta.arg, f), (t.fulfilled.match(d) || t.rejected.match(d) && !d.meta.condition) && c(d.meta.arg, f), r.util.resetApiState.match(d) && m();
  };
  function c({ queryCacheKey: d }, f) {
    let x2 = f.getState()[e7], S = x2.queries[d], g = o.currentSubscriptions[d];
    if (!S || S.status === "uninitialized")
      return;
    let { lowestPollingInterval: C, skipPollingIfUnfocused: y } = p(g);
    if (!Number.isFinite(C))
      return;
    let A = a[d];
    A?.timeout && (clearTimeout(A.timeout), A.timeout = void 0);
    let I = Date.now() + C;
    a[d] = { nextPollTimestamp: I, pollingInterval: C, timeout: setTimeout(() => {
      (x2.config.focused || !y) && f.dispatch(n(S)), c({ queryCacheKey: d }, f);
    }, C) };
  }
  function u({ queryCacheKey: d }, f) {
    let S = f.getState()[e7].queries[d], g = o.currentSubscriptions[d];
    if (!S || S.status === "uninitialized")
      return;
    let { lowestPollingInterval: C } = p(g);
    if (!Number.isFinite(C)) {
      l(d);
      return;
    }
    let y = a[d], A = Date.now() + C;
    (!y || A < y.nextPollTimestamp) && c({ queryCacheKey: d }, f);
  }
  function l(d) {
    let f = a[d];
    f?.timeout && clearTimeout(f.timeout), delete a[d];
  }
  function m() {
    for (let d of Object.keys(a))
      l(d);
  }
  function p(d = {}) {
    let f = false, x2 = Number.POSITIVE_INFINITY;
    for (let S in d)
      d[S].pollingInterval && (x2 = Math.min(d[S].pollingInterval, x2), f = d[S].skipPollingIfUnfocused || f);
    return { lowestPollingInterval: x2, skipPollingIfUnfocused: f };
  }
  return i;
};
var lk = ({ api: e7, context: t, queryThunk: r, mutationThunk: n }) => {
  let o = Uc(r, n), a = Kn(r, n), i = Pr(r, n), s = {};
  return (u, l) => {
    if (o(u)) {
      let { requestId: m, arg: { endpointName: p, originalArgs: d } } = u.meta, f = t.endpointDefinitions[p], x2 = f?.onQueryStarted;
      if (x2) {
        let S = {}, g = new Promise((I, v) => {
          S.resolve = I, S.reject = v;
        });
        g.catch(() => {
        }), s[m] = S;
        let C = e7.endpoints[p].select(f.type === "query" ? d : m), y = l.dispatch((I, v, R) => R), A = { ...l, getCacheEntry: () => C(l.getState()), requestId: m, extra: y, updateCachedData: f.type === "query" ? (I) => l.dispatch(e7.util.updateQueryData(p, d, I)) : void 0, queryFulfilled: g };
        x2(d, A);
      }
    } else if (i(u)) {
      let { requestId: m, baseQueryMeta: p } = u.meta;
      s[m]?.resolve({ data: u.payload, meta: p }), delete s[m];
    } else if (a(u)) {
      let { requestId: m, rejectedWithValue: p, baseQueryMeta: d } = u.meta;
      s[m]?.reject({ error: u.payload ?? u.error, isUnhandledError: !p, meta: d }), delete s[m];
    }
  };
};
var dk = ({ reducerPath: e7, context: t, api: r, refetchQuery: n, internalState: o }) => {
  let { removeQueryResult: a } = r.internalActions, i = (c, u) => {
    mf.match(c) && s(u, "refetchOnFocus"), ff.match(c) && s(u, "refetchOnReconnect");
  };
  function s(c, u) {
    let l = c.getState()[e7], m = l.queries, p = o.currentSubscriptions;
    t.batch(() => {
      for (let d of Object.keys(p)) {
        let f = m[d], x2 = p[d];
        if (!x2 || !f)
          continue;
        (Object.values(x2).some((g) => g[u] === true) || Object.values(x2).every((g) => g[u] === void 0) && l.config[u]) && (ka(x2) === 0 ? c.dispatch(a({ queryCacheKey: d })) : f.status !== "uninitialized" && c.dispatch(n(f)));
      }
    });
  }
  return i;
};
function pk(e7) {
  let { reducerPath: t, api: n, context: o } = e7, { apiUid: a } = o, i = { invalidateTags: h2(`${t}/invalidateTags`) }, s = (m) => m.type.startsWith(`${t}/`), c = [sk, ak, ck, uk, ik, lk];
  return { middleware: (m) => {
    let p = false, f = { ...e7, internalState: { currentSubscriptions: {} }, refetchQuery: l, isThisApiSliceAction: s }, x2 = c.map((C) => C(f)), S = rk(f), g = dk(f);
    return (C) => (y) => {
      if (!Oc(y))
        return C(y);
      p || (p = true, m.dispatch(n.internalActions.middlewareRegistered(a)));
      let A = { ...m, next: C }, I = m.getState(), [v, R] = S(y, A, I), b;
      if (v ? b = C(y) : b = R, m.getState()[t] && (g(y, A, I), s(y) || o.hasRehydrationInfo(y)))
        for (let P of x2)
          P(y, A, I);
      return b;
    };
  }, actions: i };
  function l(m) {
    return e7.api.endpoints[m.endpointName].initiate(m.originalArgs, { subscribe: false, forceRefetch: true });
  }
}
var xC = Symbol();
var mk = ({ createSelector: e7 = Y } = {}) => ({ name: xC, init(t, { baseQuery: r, tagTypes: n, reducerPath: o, serializeQueryArgs: a, keepUnusedDataFor: i, refetchOnMountOrArgChange: s, refetchOnFocus: c, refetchOnReconnect: u, invalidationBehavior: l }, m) {
  US();
  let p = (X) => X;
  Object.assign(t, { reducerPath: o, endpoints: {}, internalActions: { onOnline: ff, onOffline: vC, onFocus: mf, onFocusLost: bC }, util: {} });
  let d = ek({ serializeQueryArgs: a, reducerPath: o, createSelector: e7 }), { selectInvalidatedBy: f, selectCachedArgsForQuery: x2, buildQuerySelector: S, buildInfiniteQuerySelector: g, buildMutationSelector: C } = d;
  kr(t.util, { selectInvalidatedBy: f, selectCachedArgsForQuery: x2 });
  let { queryThunk: y, infiniteQueryThunk: A, mutationThunk: I, patchQueryData: v, updateQueryData: R, upsertQueryData: b, prefetch: P, buildMatchThunkActions: T } = XT({ baseQuery: r, reducerPath: o, context: m, api: t, serializeQueryArgs: a, assertTagType: p, selectors: d }), { reducer: B, actions: D } = ZT({ context: m, queryThunk: y, mutationThunk: I, serializeQueryArgs: a, reducerPath: o, assertTagType: p, config: { refetchOnFocus: c, refetchOnReconnect: u, refetchOnMountOrArgChange: s, keepUnusedDataFor: i, reducerPath: o, invalidationBehavior: l } });
  kr(t.util, { patchQueryData: v, updateQueryData: R, upsertQueryData: b, prefetch: P, resetApiState: D.resetApiState, upsertQueryEntries: D.cacheEntriesUpserted }), kr(t.internalActions, D);
  let { middleware: O, actions: k } = pk({ reducerPath: o, context: m, queryThunk: y, mutationThunk: I, infiniteQueryThunk: A, api: t, assertTagType: p, selectors: d });
  kr(t.util, k), kr(t, { reducer: B, middleware: O });
  let { buildInitiateQuery: Q, buildInitiateInfiniteQuery: q, buildInitiateMutation: U, getRunningMutationThunk: _, getRunningMutationsThunk: H2, getRunningQueriesThunk: ee, getRunningQueryThunk: oe } = YT({ queryThunk: y, mutationThunk: I, infiniteQueryThunk: A, api: t, serializeQueryArgs: a, context: m });
  return kr(t.util, { getRunningMutationThunk: _, getRunningMutationsThunk: H2, getRunningQueryThunk: oe, getRunningQueriesThunk: ee }), { name: xC, injectEndpoint(X, te) {
    var ge;
    let re = (ge = t.endpoints)[X] ?? (ge[X] = {});
    gf(te) && kr(re, { name: X, select: S(X, te), initiate: Q(X, te) }, T(y, X)), HT(te) && kr(re, { name: X, select: C(), initiate: U(X) }, T(I, X)), Sf(te) && kr(re, { name: X, select: g(X, te), initiate: q(X, te) }, T(y, X));
  } };
} });
var EC = tk(mk());
var fk = async (e7, t, r) => {
  let n = t.getState(), { accessToken: o, environment: a, organizationId: i } = n.configuration, s = n.generatedAnswer.answerConfigurationId, c = { ...e7, headers: { ...e7?.headers || {}, Authorization: `Bearer ${o}` } };
  try {
    let u = Me(i, a);
    return { data: FC({ baseUrl: `${u}/rest/organizations/${i}/answer/v1/configs/${s}` })(c, t, r) };
  } catch (u) {
    return { error: u };
  }
};
var Xu = EC({ reducerPath: "answer", baseQuery: RC(fk, { maxRetries: 3 }), endpoints: () => ({}) });
var gk = (e7, t) => {
  let { contentFormat: r } = t;
  e7.contentFormat = r, e7.isStreaming = true, e7.isLoading = false;
};
var Sk = (e7, t) => {
  e7.answer === void 0 ? e7.answer = t.textDelta : typeof t.textDelta == "string" && (e7.answer = e7.answer.concat(t.textDelta));
};
var hk = (e7, t) => {
  e7.citations = t.citations;
};
var yk = (e7, t) => {
  e7.generated = t.answerGenerated, e7.isStreaming = false;
};
var Ck = (e7, t) => {
  e7.error = { message: t.errorMessage, code: t.code }, e7.isStreaming = false, e7.isLoading = false, console.error(`${t.errorMessage} - code ${t.code}`);
};
var xk = (e7, t, r) => {
  let n = JSON.parse(e7.data);
  n.finishReason === "ERROR" && n.errorMessage && Ck(t, n);
  let o = n.payload.length ? JSON.parse(n.payload) : {};
  switch (n.payloadType) {
    case "genqa.headerMessageType":
      o.contentFormat && (gk(t, o), r(Bs(o.contentFormat)));
      break;
    case "genqa.messageType":
      o.textDelta && (Sk(t, o), r(Ms({ textDelta: o.textDelta })));
      break;
    case "genqa.citationsType":
      o.citations && (hk(t, o), r(Qs({ citations: o.citations })));
      break;
    case "genqa.endOfStreamType":
      yk(t, o), r(qs(o.answerGenerated ?? false));
      break;
  }
};
var oo = Xu.injectEndpoints({ overrideExisting: true, endpoints: (e7) => ({ getAnswer: e7.query({ queryFn: () => ({ data: { contentFormat: void 0, answer: void 0, citations: void 0, error: void 0, generated: false, isStreaming: true, isLoading: true } }), async onCacheEntryAdded(t, { getState: r, cacheDataLoaded: n, updateCachedData: o, dispatch: a }) {
  await n;
  let { configuration: i, generatedAnswer: s, insightConfiguration: c } = r(), { organizationId: u, environment: l, accessToken: m } = i, p = Me(u, l), d = `${p}/rest/organizations/${u}/insight/v1/configs/${c?.insightId}/answer/${s.answerConfigurationId}/generate`, f = `${p}/rest/organizations/${u}/answer/v1/configs/${s.answerConfigurationId}/generate`;
  await bc(c ? d : f, { method: "POST", body: JSON.stringify(t), headers: { Authorization: `Bearer ${m}`, Accept: "application/json", "Content-Type": "application/json", "Accept-Encoding": "*" }, fetch, onopen: async (x2) => {
    let S = x2.headers.get("x-answer-id");
    S && o((g) => {
      g.answerId = S;
    });
  }, onmessage: (x2) => {
    o((S) => {
      xk(x2, S, a);
    });
  }, onerror: (x2) => {
    throw x2;
  }, onclose: () => {
    o((x2) => {
      a(no(!x2.generated));
    });
  } });
} }) }) });
Y((e7) => Ts(e7)?.q, (e7) => e7.search.requestId, (e7, t) => ({ q: e7, requestId: t }));
var Zu = {};
var Fk = (e7) => e7.pagination ? e7.pagination.firstResult + e7.pagination.numberOfResults > 5e3 ? 5e3 - e7.pagination.firstResult : e7.pagination.numberOfResults : void 0;
var kC = (e7, t) => {
  let r = Ts(e7)?.q, n = sC(e7), o = iC(e7), a = Zy(e7) ?? [];
  return { q: r, pipelineRuleParameters: { mlGenerativeQuestionAnswering: { responseFormat: e7.generatedAnswer.responseFormat, citationsFieldToInclude: a } }, ...n?.length && { searchHub: n }, ...o?.length && { pipeline: o }, ...Zu[r]?.length && { facets: Zu[r] }, ...e7.fields && { fieldsToInclude: e7.fields.fieldsToInclude }, ...e7.didYouMean && { queryCorrection: { enabled: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "next", options: { automaticallyCorrect: e7.didYouMean.automaticallyCorrectQuery ? "whenNoResults" : "never" } }, enableDidYouMean: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "legacy" }, ...e7.pagination && { numberOfResults: Fk(e7), firstResult: e7.pagination.firstResult }, tab: e7.configuration.analytics.originLevel2 };
};
var Os = (e7) => oo.endpoints.getAnswer.select(kC(e7))(e7);
$(Jn, (e7) => e7);
var UC = Vt(NC());
var qa = h2("tab/register", (e7) => {
  let t = new RecordValue({ values: { id: V, expression: ce } });
  return F(e7, t);
});
var Ye = h2("tab/updateActiveTab", (e7) => F(e7, V));
var el = Vt(gu());
var LC = Vt(MC());
var BC = Vt(QC());
el.default.extend(BC.default);
el.default.extend(LC.default);
var Da = () => ({ organizationId: "", accessToken: "", search: { locale: "en-US", timezone: el.default.tz.guess(), authenticationProviders: [] }, analytics: { enabled: true, originContext: "Search", originLevel2: "default", originLevel3: "default", anonymous: false, deviceId: "", userDisplayName: "", documentLocation: "", trackingId: "", analyticsMode: "next", source: {} }, knowledge: { answerConfigurationId: "" }, environment: "prod" });
$(Da(), (e7) => e7.addCase(Ut, (t, r) => {
  wk(t, r.payload);
}).addCase(mt, (t, r) => {
  Ik(t, r.payload);
}).addCase(Xr, (t, r) => {
  Ek(t, r.payload);
}).addCase(ea, (t) => {
  t.analytics.enabled = false;
}).addCase(ta, (t) => {
  t.analytics.enabled = true;
}).addCase(lu, (t, r) => {
  t.analytics.originLevel2 = r.payload.originLevel2;
}).addCase(du, (t, r) => {
  t.analytics.originLevel3 = r.payload.originLevel3;
}).addCase(Ye, (t, r) => {
  t.analytics.originLevel2 = r.payload;
}).addCase(ie, (t, r) => {
  t.analytics.originLevel2 = r.payload.tab || t.analytics.originLevel2;
}));
function wk(e7, t) {
  isNullOrUndefined(t.accessToken) || (e7.accessToken = t.accessToken), e7.environment = t.environment ?? "prod", isNullOrUndefined(t.organizationId) || (e7.organizationId = t.organizationId);
}
function Ik(e7, t) {
  isNullOrUndefined(t.proxyBaseUrl) || (e7.search.apiBaseUrl = t.proxyBaseUrl), isNullOrUndefined(t.locale) || (e7.search.locale = t.locale), isNullOrUndefined(t.timezone) || (e7.search.timezone = t.timezone), isNullOrUndefined(t.authenticationProviders) || (e7.search.authenticationProviders = t.authenticationProviders);
}
function Ek(e7, t) {
  isNullOrUndefined(t.enabled) || (e7.analytics.enabled = t.enabled), isNullOrUndefined(t.originContext) || (e7.analytics.originContext = t.originContext), isNullOrUndefined(t.originLevel2) || (e7.analytics.originLevel2 = t.originLevel2), isNullOrUndefined(t.originLevel3) || (e7.analytics.originLevel3 = t.originLevel3), isNullOrUndefined(t.proxyBaseUrl) || (e7.analytics.apiBaseUrl = t.proxyBaseUrl), isNullOrUndefined(t.trackingId) || (e7.analytics.trackingId = t.trackingId), isNullOrUndefined(t.analyticsMode) || (e7.analytics.analyticsMode = t.analyticsMode), isNullOrUndefined(t.source) || (e7.analytics.source = t.source);
  let r = (0, UC.default)();
  r && (e7.analytics.analyticsMode = "next", e7.analytics.trackingId = r), isNullOrUndefined(t.runtimeEnvironment) || (e7.analytics.runtimeEnvironment = t.runtimeEnvironment), isNullOrUndefined(t.anonymous) || (e7.analytics.anonymous = t.anonymous), isNullOrUndefined(t.deviceId) || (e7.analytics.deviceId = t.deviceId), isNullOrUndefined(t.userDisplayName) || (e7.analytics.userDisplayName = t.userDisplayName), isNullOrUndefined(t.documentLocation) || (e7.analytics.documentLocation = t.documentLocation);
}
Vt(rx());
var Sn = h2("fields/registerFieldsToInclude", (e7) => F(e7, Tc));
var Na = h2("fields/fetchall/enable");
var io = h2("fields/fetchall/disable");
var Ma = W("fields/fetchDescription", async (e7, { extra: t, getState: r, rejectWithValue: n }) => {
  let o = r(), { accessToken: a, environment: i, organizationId: s } = o.configuration, { apiBaseUrl: c } = o.configuration.search, u = await t.apiClient.fieldDescriptions({ accessToken: a, organizationId: s, url: c ?? ve(s, i) });
  return we(u) ? n(u.error) : u.success.fields;
});
var Nf = { collectionField: new StringValue({ emptyAllowed: false, required: false }), parentField: new StringValue({ emptyAllowed: false, required: false }), childField: new StringValue({ emptyAllowed: false, required: false }), numberOfFoldedResults: new NumberValue({ min: 0, required: false }) };
var hn = h2("folding/register", (e7) => F(e7, Nf));
var yn = W("folding/loadCollection", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, navigatorContext: o } }) => {
  let a = t(), i = a.configuration.analytics.analyticsMode === "legacy" ? await rn(a) : Sa(a, o), s = await n.search({ ...i, q: yO(a), enableQuerySyntax: true, cq: `@${a.folding.fields.collection}="${e7}"`, filterField: a.folding.fields.collection, childField: a.folding.fields.parent, parentField: a.folding.fields.child, filterFieldRange: 100 }, { origin: "foldingCollection" });
  return we(s) ? r(s.error) : { collectionId: e7, results: s.success.results, searchUid: s.success.searchUid, rootResult: a.folding.collections[e7].result };
});
function yO(e7) {
  return e7.query.q === "" ? "" : e7.query.enableQuerySyntax ? `${e7.query.q} OR @uri` : `( <@- ${e7.query.q} -@> ) OR @uri`;
}
var al = () => ({ enabled: false, fields: { collection: "foldingcollection", parent: "foldingparent", child: "foldingchild" }, filterFieldRange: 2, collections: {} });
var Mf = ["author", "language", "urihash", "objecttype", "collection", "source", "permanentid"];
var Fx = () => ({ fieldsToInclude: Mf, fetchAllFields: false, fieldsDescription: [] });
$(Fx(), (e7) => e7.addCase(Sn, (t, r) => {
  t.fieldsToInclude = [...new Set(t.fieldsToInclude.concat(r.payload))];
}).addCase(Na, (t) => {
  t.fetchAllFields = true;
}).addCase(io, (t) => {
  t.fetchAllFields = false;
}).addCase(Ma.fulfilled, (t, { payload: r }) => {
  t.fieldsDescription = r;
}).addCase(hn, (t, { payload: r }) => {
  let n = al().fields;
  t.fieldsToInclude.push(r.collectionField ?? n.collection, r.parentField ?? n.parent, r.childField ?? n.child);
}));
var wO = new ArrayValue({ each: V, required: true });
var Rx = (e7, t) => (F(e7, V), isString(t) ? F(t, V) : F(t, wO), { payload: { contextKey: e7, contextValue: t } });
var so = h2("context/set", (e7) => {
  for (let [t, r] of Object.entries(e7))
    Rx(t, r);
  return { payload: e7 };
});
var co = h2("context/add", (e7) => Rx(e7.contextKey, e7.contextValue));
var uo = h2("context/remove", (e7) => F(e7, V));
$(Fu(), (e7) => {
  e7.addCase(so, (t, r) => {
    t.contextValues = r.payload;
  }).addCase(co, (t, r) => {
    t.contextValues[r.payload.contextKey] = r.payload.contextValue;
  }).addCase(uo, (t, r) => {
    delete t.contextValues[r.payload];
  }).addCase(ae.fulfilled, (t, r) => {
    r.payload && (t.contextValues = r.payload.context.contextValues);
  });
});
var Qa = h2("dictionaryFieldContext/set", (e7) => {
  let t = new RecordValue({ options: { required: true } }), r = F(e7, t).error;
  if (r)
    return { payload: e7, error: r };
  let n = Object.values(e7), o = new ArrayValue({ each: ce }), a = F(n, o).error;
  return a ? { payload: e7, error: a } : { payload: e7 };
});
var La = h2("dictionaryFieldContext/add", (e7) => {
  let t = new RecordValue({ options: { required: true }, values: { field: ce, key: ce } });
  return F(e7, t);
});
var Ba = h2("dictionaryFieldContext/remove", (e7) => F(e7, ce));
$(Ru(), (e7) => {
  e7.addCase(Qa, (t, r) => {
    t.contextValues = r.payload;
  }).addCase(La, (t, r) => {
    let { field: n, key: o } = r.payload;
    t.contextValues[n] = o;
  }).addCase(Ba, (t, r) => {
    delete t.contextValues[r.payload];
  }).addCase(ae.fulfilled, (t, r) => {
    r.payload && (t.contextValues = r.payload.dictionaryFieldContext.contextValues);
  });
});
Y((e7) => e7.queryCorrection.correctedQuery !== "" || e7.wasCorrectedTo !== "", (e7) => e7);
var cl = () => ({ correctedQuery: "", wordCorrections: [], originalQuery: "" });
var wx = () => ({ correctedQuery: "", corrections: [], originalQuery: "" });
function Ix() {
  return { enableDidYouMean: false, wasCorrectedTo: "", wasAutomaticallyCorrected: false, queryCorrection: cl(), originalQuery: "", automaticallyCorrectQuery: true, queryCorrectionMode: "legacy" };
}
var Ex = (e7, t) => {
  let r = { ...wx(), ...t, correctedQuery: t?.correctedQuery || t?.corrections[0]?.correctedQuery || "" };
  e7.queryCorrection = r, e7.wasCorrectedTo = r.correctedQuery;
};
$(Ix(), (e7) => {
  e7.addCase(ya, (t) => {
    t.enableDidYouMean = true;
  }).addCase(Cu, (t) => {
    t.enableDidYouMean = false;
  }).addCase(xu, (t) => {
    t.automaticallyCorrectQuery = true;
  }).addCase(Ca, (t) => {
    t.automaticallyCorrectQuery = false;
  }).addCase(N.pending, (t) => {
    t.queryCorrection = cl(), t.wasAutomaticallyCorrected = false, t.wasCorrectedTo = "";
  }).addCase(N.fulfilled, (t, r) => {
    let { queryCorrection: n, queryCorrections: o } = r.payload.response;
    if (t.queryCorrectionMode === "legacy") {
      let a = o && o[0] ? o[0] : cl();
      t.queryCorrection = a;
    }
    t.queryCorrectionMode === "next" && Ex(t, n), t.wasAutomaticallyCorrected = r.payload.automaticallyCorrected, t.originalQuery = r.payload.originalQuery;
  }).addCase(St, (t, r) => {
    t.wasCorrectedTo = r.payload;
  }).addCase(ro, (t, r) => {
    t.queryCorrectionMode = r.payload;
  });
});
var K = V;
var Z = h2("facetOptions/update", (e7 = { freezeFacetOrder: true }) => F(e7, { freezeFacetOrder: new BooleanValue({ required: false }) }));
var Be = h2("facetOptions/facet/enable", (e7) => F(e7, K));
var pe = h2("facetOptions/facet/disable", (e7) => F(e7, K));
var Hs = { facetId: K, captions: new RecordValue({ options: { required: false } }), numberOfValues: new NumberValue({ required: false, min: 1 }), query: new StringValue({ required: false, emptyAllowed: true }) };
var KO = { path: new ArrayValue({ required: true, each: V }), displayValue: ce, rawValue: ce, count: new NumberValue({ required: true, min: 0 }) };
var Ua = h2("categoryFacet/selectSearchResult", (e7) => F(e7, { facetId: K, value: new RecordValue({ values: KO }) }));
var _a = h2("categoryFacetSearch/register", (e7) => F(e7, Hs));
function ja(e7, t) {
  let { facetId: r, criterion: n } = t, o = e7[r]?.request;
  o && (o.sortCriteria = n);
}
function zs(e7) {
  e7 && (e7.currentValues = e7.currentValues.map((t) => ({ ...t, state: "idle" })), e7.preventAutoSelect = true);
}
function ll(e7, t) {
  e7 && (e7.numberOfValues = t);
}
function dl(e7, t) {
  let r = e7[t];
  r && (r.request.numberOfValues = r.initialNumberOfValues, r.request.currentValues = [], r.request.preventAutoSelect = true);
}
function Lf(e7, t, r) {
  e7.currentValues = YO(t, r), e7.numberOfValues = t.length ? 1 : r, e7.preventAutoSelect = true;
}
function YO(e7, t) {
  if (!e7.length)
    return [];
  let r = kx(e7[0], t), n = r;
  for (let o of e7.splice(1)) {
    let a = kx(o, t);
    n.children.push(a), n = a;
  }
  return n.state = "selected", n.retrieveChildren = true, [r];
}
function kx(e7, t) {
  return { value: e7, retrieveCount: t, children: [], state: "idle", retrieveChildren: false };
}
var rq = { state: new Value({ required: true }), numberOfResults: new NumberValue({ required: true, min: 0 }), value: new StringValue({ required: true, emptyAllowed: true }), path: new ArrayValue({ required: true, each: V }), moreValuesAvailable: new BooleanValue({ required: false }) };
function Bf(e7) {
  e7.children.forEach((t) => {
    Bf(t);
  }), ct({ state: e7.state, numberOfResults: e7.numberOfResults, value: e7.value, path: e7.path, moreValuesAvailable: e7.moreValuesAvailable }, rq);
}
var $a = { facetId: K, field: V, tabs: new RecordValue({ options: { required: false }, values: { included: new ArrayValue({ each: new StringValue() }), excluded: new ArrayValue({ each: new StringValue() }) } }), activeTab: new StringValue({ required: false }), delimitingCharacter: new StringValue({ required: false, emptyAllowed: true }), filterFacetCount: new BooleanValue({ required: false }), injectionDepth: new NumberValue({ required: false, min: 0 }), numberOfValues: new NumberValue({ required: false, min: 1 }), sortCriteria: new Value({ required: false }), basePath: new ArrayValue({ required: false, each: V }), filterByBasePath: new BooleanValue({ required: false }) };
var Kt = h2("categoryFacet/register", (e7) => F(e7, $a));
var xn = h2("categoryFacet/toggleSelectValue", (e7) => {
  try {
    return ct(e7.facetId, V), Bf(e7.selection), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br(t) };
  }
});
var Yt = h2("categoryFacet/deselectAll", (e7) => F(e7, $a.facetId));
var lo = h2("categoryFacet/updateNumberOfValues", (e7) => F(e7, { facetId: $a.facetId, numberOfValues: $a.numberOfValues }));
var Ga = h2("categoryFacet/updateSortCriterion", (e7) => F(e7, { facetId: $a.facetId, criterion: new Value() }));
var fl = h2("categoryFacet/updateBasePath", (e7) => F(e7, { facetId: $a.facetId, basePath: new ArrayValue({ each: V }) }));
$(Wo(), (e7) => {
  e7.addCase(Kt, (t, r) => {
    let n = r.payload, { facetId: o } = n;
    if (o in t)
      return;
    let a = aq(n), i = a.numberOfValues;
    t[o] = { request: a, initialNumberOfValues: i };
  }).addCase(ae.fulfilled, (t, r) => r.payload?.categoryFacetSet ?? t).addCase(ie, (t, r) => {
    let n = r.payload.cf || {};
    Object.keys(t).forEach((o) => {
      let a = t[o].request, i = n[o] || [];
      (i.length || a.currentValues.length) && Lf(a, i, t[o].initialNumberOfValues);
    });
  }).addCase(Ga, (t, r) => {
    let { facetId: n, criterion: o } = r.payload, a = t[n]?.request;
    a && (a.sortCriteria = o);
  }).addCase(fl, (t, r) => {
    let { facetId: n, basePath: o } = r.payload, a = t[n]?.request;
    a && (a.basePath = [...o]);
  }).addCase(xn, (t, r) => {
    let { facetId: n, selection: o, retrieveCount: a } = r.payload, i = t[n]?.request;
    if (!i)
      return;
    let { path: s } = o, c = s.slice(0, s.length - 1), u = oq(i, c, a);
    if (u.length) {
      let m = u[0];
      m.retrieveChildren = true, m.state = "selected", m.children = [];
      return;
    }
    let l = Nx(o.value, a);
    l.state = "selected", u.push(l), i.numberOfValues = 1;
  }).addCase(Yt, (t, r) => {
    let n = r.payload;
    dl(t, n);
  }).addCase(Se, (t) => {
    Object.keys(t).forEach((r) => dl(t, r));
  }).addCase(ft, (t, r) => Object.keys(t).forEach((n) => {
    t[n].request.preventAutoSelect = !r.payload.allow;
  })).addCase(lo, (t, r) => {
    let { facetId: n, numberOfValues: o } = r.payload, a = t[n]?.request;
    if (a) {
      if (!a.currentValues.length)
        return ll(a, o);
      iq(t, r.payload);
    }
  }).addCase(Ua, (t, r) => {
    let { facetId: n, value: o } = r.payload, a = t[n];
    if (!a)
      return;
    let i = [...o.path, o.rawValue];
    Lf(a.request, i, a.initialNumberOfValues);
  }).addCase(Ht.fulfilled, (t, r) => {
    Vx(t, r.payload.response.facets);
  }).addCase(N.fulfilled, (t, r) => {
    Vx(t, r.payload.response.facets);
  }).addCase(pe, (t, r) => {
    dl(t, r.payload);
  });
});
var Ks = { delimitingCharacter: ";", filterFacetCount: true, injectionDepth: 1e3, numberOfValues: 5, sortCriteria: "occurrences", basePath: [], filterByBasePath: true, resultsMustMatch: "atLeastOneValue" };
function oq(e7, t, r) {
  let n = e7.currentValues;
  for (let o of t) {
    let a = n[0];
    (!a || o !== a.value) && (a = Nx(o, r), n.length = 0, n.push(a)), a.retrieveChildren = false, a.state = "idle", n = a.children;
  }
  return n;
}
function aq(e7) {
  return { ...Ks, currentValues: [], preventAutoSelect: false, type: "hierarchical", ...e7 };
}
function Nx(e7, t) {
  return { value: e7, state: "idle", children: [], retrieveChildren: true, retrieveCount: t };
}
function Vx(e7, t) {
  t.forEach((r) => {
    if (!sq(e7, r))
      return;
    let n = r.facetId, o = e7[n]?.request;
    if (!o)
      return;
    let a = cq(o, r);
    o.currentValues = a ? [] : o.currentValues, o.preventAutoSelect = false;
  });
}
function iq(e7, t) {
  let { facetId: r, numberOfValues: n } = t, o = e7[r]?.request.currentValues[0];
  if (o) {
    for (; o.children.length && o?.state !== "selected"; )
      o = o.children[0];
    o.retrieveCount = n;
  }
}
function sq(e7, t) {
  return t.facetId in e7;
}
function cq(e7, t) {
  let r = ze(e7.currentValues), n = ze(t.values);
  return r.length !== n.length;
}
var Ys = ((r) => (r.Relevance = "relevance", r.Fields = "fields", r))(Ys || {});
var gl = ((r) => (r.Ascending = "asc", r.Descending = "desc", r))(gl || {});
var Tt = (e7) => e7.error !== void 0;
function _x(e7, t = "prod") {
  return `${Me(e7, t)}/rest/organizations/${e7}/commerce/v2`;
}
var jx = (e7) => fq(e7.cartItems, e7.cart);
function fq(e7, t) {
  let r = e7.reduce((n, o) => {
    let { productId: a, quantity: i } = t[o];
    return a in n || (n[a] = { productId: a, quantity: 0 }), n[a].quantity += i, n;
  }, {});
  return [...Object.values(r)];
}
var Wa = (e7, t) => {
  let { view: r, location: n, ...o } = e7.commerceContext;
  return { accessToken: e7.configuration.accessToken, url: e7.configuration.commerce.apiBaseUrl ?? _x(e7.configuration.organizationId, e7.configuration.environment), organizationId: e7.configuration.organizationId, trackingId: e7.configuration.analytics.trackingId, ...o, ...e7.configuration.analytics.enabled ? { clientId: t.clientId } : {}, context: { user: { ...n, ...t.userAgent ? { userAgent: t.userAgent } : {} }, view: { ...r, ...t.referrer ? { referrer: t.referrer } : {} }, capture: t.capture ?? e7.configuration.analytics.enabled, cart: jx(e7.cart), source: Hr(e7.configuration.analytics) } };
};
var $x = (e7, t, r) => ({ ...Wa(e7, t), ...gq(e7, r) });
var gq = (e7, t) => {
  let r = t ? e7.commercePagination?.recommendations[t] : e7.commercePagination?.principal;
  return r && { page: r.page, ...r.perPage && { perPage: r.perPage } };
};
var xt = (e7, t) => ({ ...$x(e7, t), facets: [...Sq(e7)], ...e7.commerceSort && { sort: hq(e7.commerceSort.appliedSort) } });
function Sq(e7) {
  return !e7.facetOrder || !e7.commerceFacetSet ? [] : e7.facetOrder.filter((t) => e7.commerceFacetSet?.[t]).map((t) => e7.manualNumericFacetSet?.[t]?.manualRange ? { facetId: t, field: t, numberOfValues: 1, isFieldExpanded: false, preventAutoSelect: true, type: "numericalRange", values: [e7.manualNumericFacetSet[t].manualRange], initialNumberOfValues: 1 } : e7.commerceFacetSet[t].request).filter((t) => t && t.values.length > 0);
}
function hq(e7) {
  return e7.by === "relevance" ? { sortCriteria: "relevance" } : { sortCriteria: "fields", fields: e7.fields.map(({ name: t, direction: r }) => ({ field: t, direction: r })) };
}
var Gx = (e7, t, r, n) => {
  let o = t.categoryFacetSearchSet[e7].options.query, a = `*${o}*`, i = t.commerceFacetSet[Js(e7)]?.request, s = i && yq(i) ? i && Cq(i) : [], c = s.length ? [s] : [], u = r ? o : t.commerceQuery?.query, { url: l, accessToken: m, organizationId: p, trackingId: d, language: f, country: x2, currency: S, clientId: g, context: C, ...y } = xt(t, n);
  return { url: l, accessToken: m, organizationId: p, facetId: Js(e7), facetQuery: r ? "*" : a, ignorePaths: c, trackingId: d, language: f, country: x2, currency: S, clientId: g, context: C, query: u, ...!r && { ...y } };
};
function yq(e7) {
  return e7.type === "hierarchical";
}
var Cq = (e7) => {
  let t = [], r = e7.values[0];
  for (; r; )
    t.push(r.value), r = r.children[0];
  return t;
};
var Wx = (e7, t, r, n) => {
  let o = t.facetSearchSet[e7].options.query, a = `*${o}*`, i = r ? o : t.commerceQuery?.query, { url: s, accessToken: c, organizationId: u, trackingId: l, language: m, country: p, currency: d, clientId: f, context: x2, ...S } = xt(t, n);
  return { url: s, accessToken: c, organizationId: u, facetId: Js(e7), facetQuery: r ? "*" : a, trackingId: l, language: m, country: p, currency: d, clientId: f, context: x2, query: i, ...!r && { ...S } };
};
var Hx = (e7) => async ({ facetId: t, facetSearchType: r }, { getState: n, extra: { validatePayload: o, navigatorContext: a, apiClient: i } }) => {
  let s = n();
  o(t, V);
  let c = xq(s, t) || Aq(s, t) ? Wx(t, s, e7, a) : Gx(t, s, e7, a), u = await i.facetSearch(c, r);
  return { facetId: t, response: u };
};
var An = W("commerce/facetSearch/executeSearch", Hx(false));
var Fn = W("commerce/facetSearch/facetFieldSuggest", Hx(true));
var xq = (e7, t) => "facetSearchSet" in e7 && e7.facetSearchSet[t] !== void 0 && e7.commerceFacetSet[t] !== void 0;
var Aq = (e7, t) => "fieldSuggestionsOrder" in e7 ? e7.fieldSuggestionsOrder.some((r) => r.facetId === t && r.type === "regular") : false;
var Sl = "field_suggestion:";
function Js(e7) {
  return e7.startsWith(Sl) ? e7.slice(Sl.length) : e7;
}
function Rn(e7) {
  return e7.startsWith(Sl) ? e7 : `${Sl}${e7}`;
}
var hl = Y((e7) => e7.commercePagination?.principal.perPage || 0, (e7) => e7);
Y((e7, t) => e7.commercePagination?.recommendations[t]?.perPage || 0, (e7) => e7);
var yl = Y((e7) => e7.commercePagination?.principal.totalEntries || 0, (e7) => e7);
Y((e7, t) => e7.commercePagination?.recommendations[t]?.totalEntries || 0, (e7) => e7);
Y((e7) => e7.commercePagination?.principal.page || 0, (e7) => e7);
Y((e7, t) => e7.commercePagination?.recommendations[t]?.page || 0, (e7) => e7);
var Fq = "coveo-headless-internal-state";
var bn = Symbol.for(Fq);
Y((e7) => e7[bn].productListing.responseId, (e7) => e7);
Y((e7) => e7.productListing.responseId, (e7) => e7);
Y((e7) => e7.productListing.requestId, (e7) => e7);
var Uf = Y((e7) => e7.productListing?.products.length || 0, (e7) => e7);
var zx = Y((e7) => ({ total: yl(e7), current: Uf(e7) }), ({ current: e7, total: t }) => e7 < t);
Y((e7) => e7.productListing?.isLoading, (e7) => isNullOrUndefined(e7) ? false : e7);
Y((e7) => e7.productListing?.error, (e7) => e7 ?? null);
var Ha = W("commerce/productListing/fetch", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, navigatorContext: o } }) => {
  let a = t(), i = await n.getProductListing(xt(a, o));
  return Tt(i) ? r(i.error) : { response: i.success };
});
W("commerce/productListing/fetchMoreProducts", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, navigatorContext: o } }) => {
  let a = t();
  if (!zx(a))
    return null;
  let s = hl(a), u = Uf(a) / s, l = await n.getProductListing({ ...xt(a, o), page: u });
  return Tt(l) ? r(l.error) : { response: l.success };
});
var Pq = { child: new RecordValue({ options: { required: true }, values: { permanentid: new StringValue({ required: true }) } }) };
h2("commerce/productListing/promoteChildToParent", (e7) => F(e7, Pq));
var Kx = (e7, t, r) => ({ ...Wa(t, r), query: t.querySet[e7] });
var Yx = h2("commerce/querySuggest/clear", (e7) => F(e7, { id: V }));
var vn = W("commerce/querySuggest/fetch", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, validatePayload: o, navigatorContext: a } }) => {
  o(e7, { id: V });
  let i = t(), s = Kx(e7.id, i, a), c = await n.querySuggest(s);
  return Tt(c) ? r(c.error) : { id: e7.id, query: s.query, ...c.success };
});
var Jx = h2("commerce/querySuggest/register", (e7) => F(e7, { id: V, count: new NumberValue({ min: 0 }) }));
var Xx = h2("commerce/querySuggest/selectSuggestion", (e7) => F(e7, { id: V, expression: ce }));
h2("commerce/facets/core/updateNumberOfValues", (e7) => F(e7, { facetId: V, numberOfValues: new NumberValue({ required: true, min: 1 }) }));
h2("commerce/facets/core/updateIsFieldExpanded", (e7) => F(e7, { facetId: V, isFieldExpanded: new BooleanValue({ required: true }) }));
var Zx = h2("commerce/facets/core/clearAll");
h2("commerce/facets/core/deselectAllValues", (e7) => F(e7, { facetId: V }));
h2("commerce/facets/core/updateFreezeCurrentValues", (e7) => F(e7, { facetId: V, freezeCurrentValues: new BooleanValue({ required: true }) }));
var eA = h2("commerce/facets/core/updateAutoSelectionForAll", (e7) => F(e7, { allow: new BooleanValue({ required: true }) }));
var Cl = { slotId: PS };
var Eq = { ...Cl, pageSize: new NumberValue({ required: true, min: 0 }) };
h2("commerce/pagination/setPageSize", (e7) => F(e7, Eq));
var Tq = { ...Cl, page: new NumberValue({ required: true, min: 0 }) };
var rA = h2("commerce/pagination/selectPage", (e7) => F(e7, Tq));
h2("commerce/pagination/nextPage", (e7) => F(e7, Cl));
h2("commerce/pagination/previousPage", (e7) => F(e7, Cl));
h2("commerce/pagination/registerRecommendationsSlot", (e7) => F(e7, { slotId: V }));
var xl = h2("commerce/query/update", (e7) => F(e7, { query: new StringValue() }));
var nA = h2("commerce/triggers/query/updateIgnore", (e7) => F(e7, { q: new StringValue({ emptyAllowed: true, required: true }) }));
var oA = h2("commerce/triggers/query/applyModification", (e7) => F(e7, new RecordValue({ values: { originalQuery: de, modification: de } })));
Y((e7) => e7[bn].commerceSearch.responseId, (e7) => e7);
Y((e7) => e7.commerceSearch.responseId, (e7) => e7);
Y((e7) => e7.commerceSearch.requestId, (e7) => e7);
var Gf = Y((e7) => e7.commerceSearch?.products.length || 0, (e7) => e7);
var iA = Y((e7) => ({ total: yl(e7), current: Gf(e7) }), ({ current: e7, total: t }) => e7 < t);
Y((e7) => e7.commerceSearch?.isLoading, (e7) => isNullOrUndefined(e7) ? false : e7);
Y((e7) => e7.commerceSearch?.error, (e7) => e7 ?? null);
var Al = Y((e7) => e7.commerceQuery?.query, (e7) => e7 ?? "");
Y((e7) => e7.commerceSearch?.queryExecuted, (e7) => e7);
var sA = (e7, t) => isNullOrUndefined(t.queryCorrection?.correctedQuery) ? Al(e7) : t.queryCorrection.correctedQuery;
var Xs = class {
  constructor(t) {
    this.config = t;
  }
  async process(t) {
    return this.processQueryErrorOrContinue(t) ?? await this.processQueryCorrectionsOrContinue(t) ?? await this.processQueryTriggersOrContinue(t) ?? this.processSuccessResponse(t);
  }
  async fetchFromAPI(t) {
    let r = (/* @__PURE__ */ new Date()).getTime(), n = await this.extra.apiClient.search(t), o = (/* @__PURE__ */ new Date()).getTime() - r, a = this.getState().commerceQuery.query || "";
    return { response: n, duration: o, queryExecuted: a, requestExecuted: t };
  }
  processSuccessResponse(t) {
    return { ...t, response: this.getSuccessResponse(t), originalQuery: this.getCurrentQuery() };
  }
  processQueryErrorOrContinue(t) {
    return Tt(t.response) ? this.rejectWithValue(t.response.error) : null;
  }
  async processQueryCorrectionsOrContinue(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    if (!n || !r.didYouMean)
      return null;
    let { queryCorrection: o } = n;
    if (!(!isNullOrUndefined(o) && !isNullOrUndefined(o.correctedQuery)))
      return null;
    let { correctedQuery: i, originalQuery: s } = n.queryCorrection;
    return this.onUpdateQueryForCorrection(i ?? ""), { ...t, response: { ...n }, queryExecuted: sA(r, n), originalQuery: s ?? "" };
  }
  async processQueryTriggersOrContinue(t) {
    let r = this.getSuccessResponse(t);
    if (!r)
      return null;
    let n = r.triggers.find((s) => s.type === "query")?.content || "";
    if (!n)
      return null;
    if (this.getState().triggers?.queryModification.queryToIgnore === n)
      return this.dispatch(nA({ q: "" })), null;
    let a = this.getCurrentQuery(), i = await this.automaticallyRetryQueryWithTriggerModification(n);
    return Tt(i.response) ? this.rejectWithValue(i.response.error) : { ...i, response: { ...i.response.success }, originalQuery: a };
  }
  async automaticallyRetryQueryWithTriggerModification(t) {
    return this.dispatch(oA({ newQuery: t, originalQuery: this.getCurrentQuery() })), this.onUpdateQueryForCorrection(t), await this.fetchFromAPI({ ...xt(this.getState(), this.navigatorContext), query: t });
  }
  get dispatch() {
    return this.config.dispatch;
  }
  get rejectWithValue() {
    return this.config.rejectWithValue;
  }
  getState() {
    return this.config.getState();
  }
  get navigatorContext() {
    return this.config.extra.navigatorContext;
  }
  getCurrentQuery() {
    let t = this.getState();
    return t.commerceQuery.query !== void 0 ? t.commerceQuery.query : "";
  }
  getSuccessResponse(t) {
    return Tt(t.response) ? null : t.response.success;
  }
  get extra() {
    return this.config.extra;
  }
  onUpdateQueryForCorrection(t) {
    this.dispatch(xl({ query: t }));
  }
};
var Pn = W("commerce/search/executeSearch", async (e7, t) => {
  let { getState: r } = t, n = r(), { navigatorContext: o } = t.extra, a = xt(n, o), i = Al(n), s = new Xs(t), c = await s.fetchFromAPI({ ...a, query: i });
  return s.process(c);
});
W("commerce/search/fetchMoreProducts", async (e7, t) => {
  let { getState: r } = t, n = r(), { navigatorContext: o } = t.extra;
  if (!iA(n))
    return null;
  let i = hl(n), c = Gf(n) / i, u = Al(n), l = xt(n, o), m = new Xs(t), p = await m.fetchFromAPI({ ...l, query: u, page: c });
  return m.process(p);
});
W("commerce/search/prepareForSearchWithQuery", (e7, t) => {
  let { dispatch: r } = t;
  F(e7, { query: new StringValue(), clearFilters: new BooleanValue() }), e7.clearFilters && (r(Zx()), r(_t())), r(eA({ allow: true })), r(xl({ query: e7.query })), r(rA({ page: 0 }));
});
W("commerce/search/fetchInstantProducts", async (e7, { getState: t, rejectWithValue: r, extra: n }) => {
  let o = t(), { apiClient: a, navigatorContext: i } = n, { q: s } = e7, c = await a.productSuggestions({ ...Wa(o, i), query: s });
  return Tt(c) ? r(c.error) : { response: { ...c.success, products: c.success.products } };
});
var Nq = { child: new RecordValue({ options: { required: true }, values: { permanentid: new StringValue({ required: true }) } }) };
h2("commerce/search/promoteChildToParent", (e7) => F(e7, Nq));
function Zs(e7, t, r) {
  let { facetId: n } = t;
  if (e7[n])
    return;
  let o = false, a = { ...Je, ...t }, i = r();
  e7[n] = { options: a, isLoading: o, response: i, initialNumberOfValues: a.numberOfValues, requestId: "" };
}
function Fl(e7, t) {
  let { facetId: r, ...n } = t, o = e7[r];
  o && (o.options = { ...o.options, ...n });
}
function wn(e7, t, r) {
  let n = e7[t];
  n && (n.requestId = r, n.isLoading = true);
}
function In(e7, t) {
  let r = e7[t];
  r && (r.isLoading = false);
}
function Rl(e7, t, r) {
  let { facetId: n, response: o } = t, a = e7[n];
  a && a.requestId === r && (a.isLoading = false, a.response = o);
}
function bl(e7, t, r) {
  let { facetId: n, response: o } = t, a = e7[n];
  a && a.requestId === r && (a.isLoading = false, "success" in o && (a.response = o.success));
}
function vl(e7, t, r, n) {
  let { facetId: o, response: a } = t, i = Rn(o), s = e7[i];
  if (!s)
    Zs(e7, { facetId: i }, n), s = e7[i];
  else if (s.requestId !== r)
    return;
  s.isLoading = false, "success" in a && (s.response = a.success);
}
function lA(e7, t, r, n) {
  if (t.fieldSuggestionsFacets)
    for (let o of t.fieldSuggestionsFacets)
      o.facetId in e7 || o.type !== "regular" || (e7[o.facetId] = { options: { ...Je, query: t.query ?? "" }, isLoading: false, response: n(), initialNumberOfValues: Je.numberOfValues, requestId: r });
}
function dA(e7, t, r, n) {
  if (t.fieldSuggestionsFacets)
    for (let o of t.fieldSuggestionsFacets) {
      let a = Rn(o.facetId);
      a in e7 || o.type !== "hierarchical" || (e7[a] = { options: { ...Je, query: t.query ?? "" }, isLoading: false, response: n(), initialNumberOfValues: Je.numberOfValues, requestId: r });
    }
}
function ec(e7, t, r) {
  let { facetId: n } = t, o = e7[n];
  o && (o.requestId = "", o.isLoading = false, o.response = r(), o.options.numberOfValues = o.initialNumberOfValues, o.options.query = Je.query);
}
function qr(e7, t) {
  Object.keys(e7).forEach((r) => ec(e7, { facetId: r }, t));
}
var Je = { captions: {}, numberOfValues: 10, query: "" };
var pA = async (e7, t, r, n) => {
  let o = t.categoryFacetSearchSet[e7].options, a = t.categoryFacetSet[e7].request, { captions: i, query: s, numberOfValues: c } = o, { field: u, delimitingCharacter: l, basePath: m, filterFacetCount: p } = a, d = Mq(a), f = d.length ? [d] : [], x2 = `*${s}*`;
  return { url: t.configuration.search.apiBaseUrl ?? ve(t.configuration.organizationId, t.configuration.environment), accessToken: t.configuration.accessToken, organizationId: t.configuration.organizationId, ...t.configuration.search.authenticationProviders.length && { authentication: t.configuration.search.authenticationProviders.join(",") }, basePath: m, captions: i, numberOfValues: c, query: x2, field: u, delimitingCharacter: l, ignorePaths: f, filterFacetCount: p, type: "hierarchical", ...n ? {} : { searchContext: (await yt(t, r)).request } };
};
var Mq = (e7) => {
  let t = [], r = e7.currentValues[0];
  for (; r; )
    t.push(r.value), r = r.children[0];
  return t;
};
var mA = async (e7, t, r, n) => {
  let { captions: o, query: a, numberOfValues: i } = t.facetSearchSet[e7].options, { field: s, currentValues: c, filterFacetCount: u } = t.facetSet[e7].request, l = c.filter((p) => p.state !== "idle").map((p) => p.value), m = `*${a}*`;
  return { url: t.configuration.search.apiBaseUrl ?? ve(t.configuration.organizationId, t.configuration.environment), accessToken: t.configuration.accessToken, organizationId: t.configuration.organizationId, ...t.configuration.search.authenticationProviders && { authentication: t.configuration.search.authenticationProviders.join(",") }, captions: o, numberOfValues: i, query: m, field: s, ignoreValues: l, filterFacetCount: u, type: "specific", ...n ? {} : { searchContext: (await yt(t, r)).request } };
};
var fA = (e7) => async (t, { getState: r, extra: { apiClient: n, validatePayload: o, navigatorContext: a } }) => {
  let i = r(), s;
  o(t, V), Qq(i, t) ? s = await mA(t, i, a, e7) : s = await pA(t, i, a, e7);
  let c = await n.facetSearch(s);
  return { facetId: t, response: c };
};
var Ie = W("facetSearch/executeSearch", fA(false));
W("facetSearch/executeSearch", fA(true));
var za = h2("facetSearch/clearResults", (e7) => F(e7, { facetId: K }));
var Qq = (e7, t) => e7.facetSearchSet !== void 0 && e7.facetSet !== void 0 && e7.facetSet[t] !== void 0;
var gA = { facetId: K, value: new RecordValue({ values: { displayValue: ce, rawValue: ce, count: new NumberValue({ required: true, min: 0 }) } }) };
var Pl = h2("facetSearch/register", (e7) => F(e7, Hs));
var En = h2("facetSearch/update", (e7) => F(e7, Hs));
var mo = h2("facetSearch/toggleSelectValue", (e7) => F(e7, gA));
var fo = h2("facetSearch/toggleExcludeValue", (e7) => F(e7, gA));
function SA() {
  return {};
}
$(SA(), (e7) => {
  e7.addCase(_a, (t, r) => {
    let n = r.payload;
    Zs(t, n, go);
  }).addCase(En, (t, r) => {
    Fl(t, r.payload);
  }).addCase(An.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn(t, n, r.meta.requestId);
  }).addCase(Fn.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn(t, n, r.meta.requestId);
  }).addCase(Ie.pending, (t, r) => {
    let n = r.meta.arg;
    wn(t, n, r.meta.requestId);
  }).addCase(An.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In(t, n);
  }).addCase(Fn.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In(t, Rn(n));
  }).addCase(Ie.rejected, (t, r) => {
    let n = r.meta.arg;
    In(t, n);
  }).addCase(An.fulfilled, (t, r) => {
    bl(t, r.payload, r.meta.requestId);
  }).addCase(Fn.fulfilled, (t, r) => {
    vl(t, r.payload, r.meta.requestId, go);
  }).addCase(vn.fulfilled, (t, r) => {
    dA(t, r.payload, r.meta.requestId, go);
  }).addCase(Ie.fulfilled, (t, r) => {
    Rl(t, r.payload, r.meta.requestId);
  }).addCase(za, (t, { payload: { facetId: r } }) => {
    ec(t, { facetId: r }, go);
  }).addCase(Ha.fulfilled, (t) => qr(t, go)).addCase(Pn.fulfilled, (t) => qr(t, go)).addCase(N.fulfilled, (t) => {
    qr(t, go);
  });
});
function go() {
  return { moreValuesAvailable: false, values: [] };
}
var Tl = new RecordValue({ options: { required: false }, values: { type: new StringValue({ constrainTo: ["simple"], emptyAllowed: false, required: true }), values: new ArrayValue({ required: true, max: 25, each: new StringValue({ emptyAllowed: false, required: true }) }) } });
var kl = new ArrayValue({ min: 1, max: 25, required: false, each: new StringValue({ emptyAllowed: false, required: true }) });
var So = { value: V, numberOfResults: new NumberValue({ min: 0 }), state: V };
var Wq = { facetId: K, field: new StringValue({ required: true, emptyAllowed: true }), tabs: new RecordValue({ options: { required: false }, values: { included: new ArrayValue({ each: new StringValue() }), excluded: new ArrayValue({ each: new StringValue() }) } }), activeTab: new StringValue({ required: false }), filterFacetCount: new BooleanValue({ required: false }), injectionDepth: new NumberValue({ required: false, min: 0 }), numberOfValues: new NumberValue({ required: false, min: 1 }), sortCriteria: new Value({ required: false }), resultsMustMatch: new Value({ required: false }), allowedValues: Tl, customSort: kl };
var ir = h2("facet/register", (e7) => F(e7, Wq));
var sr = h2("facet/toggleSelectValue", (e7) => F(e7, { facetId: K, selection: new RecordValue({ values: So }) }));
var cr = h2("facet/toggleExcludeValue", (e7) => F(e7, { facetId: K, selection: new RecordValue({ values: So }) }));
var me = h2("facet/deselectAll", (e7) => F(e7, K));
var ei = h2("facet/updateSortCriterion", (e7) => F(e7, { facetId: K, criterion: new Value({ required: true }) }));
var ho = h2("facet/updateNumberOfValues", (e7) => F(e7, { facetId: K, numberOfValues: new NumberValue({ required: true, min: 1 }) }));
var yo = h2("facet/updateIsFieldExpanded", (e7) => F(e7, { facetId: K, isFieldExpanded: new BooleanValue({ required: true }) }));
var Nr = h2("facet/updateFreezeCurrentValues", (e7) => F(e7, { facetId: K, freezeCurrentValues: new BooleanValue({ required: true }) }));
function Co(e7) {
  let t = RA(e7.start, e7), r = RA(e7.end, e7), n = e7.endInclusive ?? false, o = e7.state ?? "idle";
  return { start: t, end: r, endInclusive: n, state: o };
}
function RA(e7, t) {
  let { dateFormat: r } = t;
  return Oy(e7) ? (to(e7), Ey(e7)) : typeof e7 == "string" && $t(e7) ? (to(e7), e7) : (hu(e7, r), vs(eo(e7, r)));
}
var ti = h2("rangeFacet/updateSortCriterion", (e7) => F(e7, { facetId: K, criterion: new Value({ required: true }) }));
var xo = { state: V, start: new NumberValue({ required: true }), end: new NumberValue({ required: true }), endInclusive: new BooleanValue({ required: true }), numberOfResults: new NumberValue({ required: true, min: 0 }) };
var Ao = { start: V, end: V, endInclusive: new BooleanValue({ required: true }), state: V, numberOfResults: new NumberValue({ required: true, min: 0 }) };
var Fo = (e7) => ({ facetId: K, selection: typeof e7.start == "string" ? new RecordValue({ values: Ao }) : new RecordValue({ values: xo }) });
var zq = { start: V, end: V, endInclusive: new BooleanValue({ required: true }), state: V };
var Kq = { facetId: K, field: V, tabs: new RecordValue({ options: { required: false }, values: { included: new ArrayValue({ each: new StringValue() }), excluded: new ArrayValue({ each: new StringValue() }) } }), activeTab: new StringValue({ required: false }), currentValues: new ArrayValue({ required: false, each: new RecordValue({ values: zq }) }), generateAutomaticRanges: new BooleanValue({ required: true }), filterFacetCount: new BooleanValue({ required: false }), injectionDepth: new NumberValue({ required: false, min: 0 }), numberOfValues: new NumberValue({ required: false, min: 1 }), sortCriteria: new Value({ required: false }), rangeAlgorithm: new Value({ required: false }) };
function IA(e7) {
  return $t(e7) ? ws(e7) : e7;
}
function Vl(e7) {
  e7.currentValues && e7.currentValues.forEach((t) => {
    let { start: r, end: n } = Co(t);
    if (eo(IA(r)).isAfter(eo(IA(n))))
      throw new Error(`The start value is greater than the end value for the date range ${t.start} to ${t.end}`);
  });
}
var ur = h2("dateFacet/register", (e7) => {
  try {
    return ct(e7, Kq), Vl(e7), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br(t) };
  }
});
var lr = h2("dateFacet/toggleSelectValue", (e7) => F(e7, { facetId: K, selection: new RecordValue({ values: Ao }) }));
var dr = h2("dateFacet/toggleExcludeValue", (e7) => F(e7, { facetId: K, selection: new RecordValue({ values: Ao }) }));
var Mr = h2("dateFacet/updateFacetValues", (e7) => {
  try {
    return ct(e7, { facetId: K, values: new ArrayValue({ each: new RecordValue({ values: Ao }) }) }), Vl({ currentValues: e7.values }), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br(t) };
  }
});
var Nl = ti;
var Ml = me;
var Yq = { state: V, start: new NumberValue({ required: true }), end: new NumberValue({ required: true }), endInclusive: new BooleanValue({ required: true }) };
var Jq = { facetId: K, field: V, tabs: new RecordValue({ options: { required: false }, values: { included: new ArrayValue({ each: new StringValue() }), excluded: new ArrayValue({ each: new StringValue() }) } }), activeTab: new StringValue({ required: false }), currentValues: new ArrayValue({ required: false, each: new RecordValue({ values: Yq }) }), generateAutomaticRanges: new BooleanValue({ required: true }), filterFacetCount: new BooleanValue({ required: false }), injectionDepth: new NumberValue({ required: false, min: 0 }), numberOfValues: new NumberValue({ required: false, min: 1 }), sortCriteria: new Value({ required: false }), rangeAlgorithm: new Value({ required: false }) };
function Bl(e7) {
  e7.currentValues && e7.currentValues.forEach(({ start: t, end: r }) => {
    if (t > r)
      throw new Error(`The start value is greater than the end value for the numeric range ${t} to ${r}`);
  });
}
var pr = h2("numericFacet/register", (e7) => {
  try {
    return F(e7, Jq), Bl(e7), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br(t) };
  }
});
var mr = h2("numericFacet/toggleSelectValue", (e7) => F(e7, { facetId: K, selection: new RecordValue({ values: xo }) }));
var fr = h2("numericFacet/toggleExcludeValue", (e7) => F(e7, { facetId: K, selection: new RecordValue({ values: xo }) }));
var Qr = h2("numericFacet/updateFacetValues", (e7) => {
  try {
    return ct(e7, { facetId: K, values: new ArrayValue({ each: new RecordValue({ values: xo }) }) }), Bl({ currentValues: e7.values }), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br(t) };
  }
});
var Ul = ti;
var _l = me;
var jl = (e7, t) => typeof e7 == "object" && Object.keys({ ...e7 }).length === 0 || !t || !e7 ? true : e7.excluded && e7.excluded.includes(t) ? false : !!(e7.included && (e7.included.length === 0 || e7.included.includes(t)));
$(bu(), (e7) => {
  e7.addCase(Z, (t, r) => ({ ...t, ...r.payload })).addCase(N.fulfilled, (t) => {
    t.freezeFacetOrder = false;
  }).addCase(N.rejected, (t) => {
    t.freezeFacetOrder = false;
  }).addCase(Ye, (t, r) => {
    for (let n in t.facets) {
      let o = t.facets[n];
      Object.keys({ ...o.tabs }).length > 0 && (o.enabled = jl(o.tabs, r.payload));
    }
  }).addCase(ae.fulfilled, (t, r) => r.payload?.facetOptions ?? t).addCase(Kt, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    $l(o, a, t, n);
  }).addCase(ir, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    $l(o, a, t, n);
  }).addCase(ur, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    $l(o, a, t, n);
  }).addCase(pr, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    $l(o, a, t, n);
  }).addCase(Be, (t, r) => {
    t.facets[r.payload].enabled = true;
  }).addCase(pe, (t, r) => {
    t.facets[r.payload].enabled = false;
  }).addCase(ie, (t, r) => {
    r.payload.tab && Object.entries(t.facets).forEach(([, n]) => {
      Object.keys(n.tabs ?? {}).length > 0 && (n.enabled = jl(n.tabs, r.payload.tab));
    }), [...Object.keys(r.payload.f ?? {}), ...Object.keys(r.payload.fExcluded ?? {}), ...Object.keys(r.payload.cf ?? {}), ...Object.keys(r.payload.nf ?? {}), ...Object.keys(r.payload.df ?? {})].forEach((n) => {
      n in t || (t.facets[n] = Xm()), t.facets[n].enabled = true;
    });
  });
});
function $l(e7, t, r, n) {
  let o = { ...Xm(), tabs: e7 ?? {} };
  e7 && Object.keys(e7).length > 0 && (o.enabled = jl(e7, t)), r.facets[n] = o;
}
Y((e7) => e7, (e7) => {
  if (!e7)
    return "";
  for (let t in e7)
    if (e7[t].isActive)
      return e7[t].id;
  return "";
});
var dD = Intl.supportedValuesOf("currency");
var pD = new StringValue({ required: true, emptyAllowed: false, constrainTo: dD });
var og = { url: V };
var ag = { latitude: new NumberValue({ min: -90, max: 90, required: true }), longitude: new NumberValue({ min: -180, max: 180, required: true }) };
var ig = { language: V, country: V, currency: pD, view: new RecordValue({ options: { required: true }, values: og }), location: new RecordValue({ options: { required: false }, values: ag }) };
var LA = h2("commerce/context/set", (e7) => F(e7, ig));
var Wl = h2("commerce/context/setView", (e7) => F(e7, og));
h2("commerce/context/setLocation", (e7) => F(e7, ag));
function BA() {
  return {};
}
$(BA(), (e7) => {
  e7.addCase(Pl, (t, r) => {
    let n = r.payload;
    Zs(t, n, kn);
  }).addCase(En, (t, r) => {
    Fl(t, r.payload);
  }).addCase(An.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn(t, n, r.meta.requestId);
  }).addCase(Fn.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn(t, Rn(n), r.meta.requestId);
  }).addCase(Ie.pending, (t, r) => {
    let n = r.meta.arg;
    wn(t, n, r.meta.requestId);
  }).addCase(An.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In(t, n);
  }).addCase(Fn.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In(t, Rn(n));
  }).addCase(Ie.rejected, (t, r) => {
    let n = r.meta.arg;
    In(t, n);
  }).addCase(An.fulfilled, (t, r) => {
    bl(t, r.payload, r.meta.requestId);
  }).addCase(Fn.fulfilled, (t, r) => {
    vl(t, r.payload, r.meta.requestId, kn);
  }).addCase(vn.fulfilled, (t, r) => {
    lA(t, r.payload, r.meta.requestId, kn);
  }).addCase(Ie.fulfilled, (t, r) => {
    Rl(t, r.payload, r.meta.requestId);
  }).addCase(za, (t, { payload: r }) => {
    ec(t, r, kn);
  }).addCase(N.fulfilled, (t) => {
    qr(t, kn);
  }).addCase(Ha.fulfilled, (t) => qr(t, kn)).addCase(Pn.fulfilled, (t) => qr(t, kn)).addCase(Wl, (t) => qr(t, kn));
});
function kn() {
  return { moreValuesAvailable: false, values: [] };
}
$(Ko(), (e7) => {
  e7.addCase(ir, (t, r) => {
    let { facetId: n } = r.payload;
    n in t || (t[n] = Wh(mD(r.payload)));
  }).addCase(ae.fulfilled, (t, r) => {
    if (r.payload && Object.keys(r.payload.facetSet).length !== 0)
      return r.payload.facetSet;
  }).addCase(ie, (t, r) => {
    let n = r.payload.f || {}, o = r.payload.fExcluded || {};
    Object.keys(t).forEach((i) => {
      let { request: s } = t[i], c = n[i] || [], u = o[i] || [], l = c.length + u.length, m = s.currentValues.filter((p) => !c.includes(p.value) && !u.includes(p.value));
      s.currentValues = [...c.map(_A), ...u.map(jA), ...m.map(gD)], s.preventAutoSelect = l > 0, s.numberOfValues = Math.max(l, s.numberOfValues);
    });
  }).addCase(sr, (t, r) => {
    let { facetId: n, selection: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    a.preventAutoSelect = true;
    let i = a.currentValues.find((c) => c.value === o.value);
    if (!i) {
      Hl(a, o);
      return;
    }
    let s = i.state === "selected";
    i.state = s ? "idle" : "selected", a.freezeCurrentValues = true;
  }).addCase(cr, (t, r) => {
    let { facetId: n, selection: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    a.preventAutoSelect = true;
    let i = a.currentValues.find((c) => c.value === o.value);
    if (!i) {
      Hl(a, o);
      return;
    }
    let s = i.state === "excluded";
    i.state = s ? "idle" : "excluded", a.freezeCurrentValues = true;
  }).addCase(Nr, (t, r) => {
    let { facetId: n, freezeCurrentValues: o } = r.payload, a = t[n]?.request;
    a && (a.freezeCurrentValues = o);
  }).addCase(me, (t, r) => {
    zs(t[r.payload]?.request);
  }).addCase(Se, (t) => {
    Object.values(t).filter((r) => r.hasBreadcrumbs).forEach(({ request: r }) => zs(r));
  }).addCase(_t, (t) => {
    Object.values(t).filter((r) => !r.hasBreadcrumbs).forEach(({ request: r }) => zs(r));
  }).addCase(ft, (t, r) => Object.values(t).forEach((n) => {
    n.request.preventAutoSelect = !r.payload.allow;
  })).addCase(ei, (t, r) => {
    ja(t, r.payload);
  }).addCase(ho, (t, r) => {
    let { facetId: n, numberOfValues: o } = r.payload;
    ll(t[n]?.request, o);
  }).addCase(yo, (t, r) => {
    let { facetId: n, isFieldExpanded: o } = r.payload, a = t[n]?.request;
    a && (a.isFieldExpanded = o);
  }).addCase(N.fulfilled, (t, r) => {
    r.payload.response.facets.forEach((o) => UA(t[o.facetId]?.request, o));
  }).addCase(Ht.fulfilled, (t, r) => {
    r.payload.response.facets.forEach((o) => UA(t[o.facetId]?.request, o));
  }).addCase(mo, (t, r) => {
    let { facetId: n, value: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    let { rawValue: i } = o, { currentValues: s } = a, c = s.find((l) => l.value === i);
    if (c) {
      c.state = "selected";
      return;
    }
    let u = _A(i);
    Hl(a, u), a.freezeCurrentValues = true, a.preventAutoSelect = true;
  }).addCase(fo, (t, r) => {
    let { facetId: n, value: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    let { rawValue: i } = o, { currentValues: s } = a, c = s.find((l) => l.value === i);
    if (c) {
      c.state = "excluded";
      return;
    }
    let u = jA(i);
    Hl(a, u), a.freezeCurrentValues = true, a.preventAutoSelect = true;
  }).addCase(pe, (t, r) => {
    if (!(r.payload in t))
      return;
    let { request: n } = t[r.payload];
    zs(n);
  });
});
function Hl(e7, t) {
  let { currentValues: r } = e7, n = r.findIndex((s) => s.state === "idle"), o = n === -1 ? r.length : n, a = r.slice(0, o), i = r.slice(o + 1);
  e7.currentValues = [...a, t, ...i], e7.numberOfValues = e7.currentValues.length;
}
function UA(e7, t) {
  e7 && (e7.currentValues = t.values.map(fD), e7.freezeCurrentValues = false, e7.preventAutoSelect = false);
}
var nc = { filterFacetCount: true, injectionDepth: 1e3, numberOfValues: 8, sortCriteria: "automatic", resultsMustMatch: "atLeastOneValue" };
function mD(e7) {
  return { ...nc, type: "specific", currentValues: [], freezeCurrentValues: false, isFieldExpanded: false, preventAutoSelect: false, ...e7 };
}
function fD(e7) {
  let { value: t, state: r } = e7;
  return { value: t, state: r };
}
function _A(e7) {
  return { value: e7, state: "selected" };
}
function jA(e7) {
  return { value: e7, state: "excluded" };
}
function gD(e7) {
  return { ...e7, state: "idle" };
}
var WA = { facetId: K, selection: new RecordValue({ values: So }) };
W("facet/executeToggleSelect", ({ facetId: e7, selection: t }, r) => {
  let { dispatch: n, extra: { validatePayload: o } } = r;
  o({ facetId: e7, selection: t }, WA), n(sr({ facetId: e7, selection: t })), n(Z());
});
W("facet/executeToggleExclude", ({ facetId: e7, selection: t }, r) => {
  let { dispatch: n, extra: { validatePayload: o } } = r;
  o({ facetId: e7, selection: t }, WA), n(cr({ facetId: e7, selection: t })), n(Z());
});
var ad = h2("rangeFacet/executeToggleSelect", (e7) => F(e7, Fo(e7.selection)));
var id = h2("rangeFacet/executeToggleExclude", (e7) => F(e7, Fo(e7.selection)));
var tF = { facetId: K, selection: new RecordValue({ values: Ao }) };
W("dateFacet/executeToggleSelect", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, tF), t(lr(e7)), t(ad(e7)), t(Z());
});
W("dateFacet/executeToggleExclude", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, tF), t(dr(e7)), t(id(e7)), t(Z());
});
var cd = { filterFacetCount: true, injectionDepth: 1e3, numberOfValues: 8, sortCriteria: "ascending", rangeAlgorithm: "even", resultsMustMatch: "atLeastOneValue" };
function ud(e7, t) {
  let { request: r } = t, { facetId: n } = r;
  if (n in e7)
    return;
  let o = oF(r);
  r.numberOfValues = o, e7[n] = t;
}
function ld(e7, t, r) {
  let n = e7[t]?.request;
  n && (n.currentValues = r, n.numberOfValues = oF(n));
}
function dd(e7, t, r) {
  let n = e7[t]?.request;
  if (!n)
    return;
  let o = sd(n.currentValues, r);
  if (!o)
    return;
  let a = o.state === "selected";
  o.state = a ? "idle" : "selected", n.preventAutoSelect = true;
}
function pd(e7, t, r) {
  let n = e7[t]?.request;
  if (!n)
    return;
  let o = sd(n.currentValues, r);
  if (!o)
    return;
  let a = o.state === "excluded";
  o.state = a ? "idle" : "excluded", n.preventAutoSelect = true;
}
function On(e7, t) {
  let r = e7[t]?.request;
  r && r.currentValues.forEach((n) => n.state = "idle");
}
function md(e7, t) {
  Object.entries(e7).forEach(([r, { request: n }]) => {
    let o = t[r] || [];
    n.currentValues.forEach((s) => {
      let c = !!sd(o, s);
      return s.state = c ? "selected" : "idle", s;
    });
    let a = o.filter((s) => !sd(n.currentValues, s)), i = n.currentValues;
    i.push(...a), n.numberOfValues = Math.max(n.numberOfValues, i.length);
  });
}
function fd(e7, t, r) {
  t.forEach((n) => {
    let o = n.facetId, a = e7[o]?.request;
    if (!a)
      return;
    let i = r(n.values);
    a.currentValues = i, a.preventAutoSelect = false;
  });
}
function sd(e7, t) {
  let { start: r, end: n } = t;
  return e7.find((o) => o.start === r && o.end === n);
}
function oF(e7) {
  let { generateAutomaticRanges: t, currentValues: r, numberOfValues: n } = e7;
  return t ? Math.max(n, r.length) : r.length;
}
$(Ho(), (e7) => {
  e7.addCase(ur, (t, r) => {
    let { payload: n } = r, o = vD(n);
    ud(t, $h(o));
  }).addCase(ae.fulfilled, (t, r) => r.payload?.dateFacetSet ?? t).addCase(ie, (t, r) => {
    let n = r.payload.df || {};
    md(t, n);
  }).addCase(lr, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    dd(t, n, o);
  }).addCase(dr, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    pd(t, n, o);
  }).addCase(Mr, (t, r) => {
    let { facetId: n, values: o } = r.payload;
    ld(t, n, o);
  }).addCase(Ml, (t, r) => {
    On(t, r.payload);
  }).addCase(Se, (t) => {
    Object.keys(t).forEach((r) => {
      On(t, r);
    });
  }).addCase(Nl, (t, r) => {
    ja(t, r.payload);
  }).addCase(N.fulfilled, (t, r) => {
    let n = r.payload.response.facets;
    fd(t, n, PD);
  }).addCase(pe, (t, r) => {
    On(t, r.payload);
  });
});
function vD(e7) {
  return { ...cd, currentValues: [], preventAutoSelect: false, type: "dateRange", ...e7 };
}
function PD(e7) {
  return e7.map((t) => {
    let { numberOfResults: r, ...n } = t;
    return n;
  });
}
$(zo(), (e7) => {
  e7.addCase(pr, (t, r) => {
    let { payload: n } = r, o = qD(n);
    ud(t, Gh(o));
  }).addCase(ae.fulfilled, (t, r) => r.payload?.numericFacetSet ?? t).addCase(ie, (t, r) => {
    let n = r.payload.nf || {};
    md(t, n);
  }).addCase(mr, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    dd(t, n, o);
  }).addCase(fr, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    pd(t, n, o);
  }).addCase(Qr, (t, r) => {
    let { facetId: n, values: o } = r.payload;
    ld(t, n, o);
  }).addCase(_l, (t, r) => {
    On(t, r.payload);
  }).addCase(Se, (t) => {
    Object.keys(t).forEach((r) => {
      On(t, r);
    });
  }).addCase(Ul, (t, r) => {
    ja(t, r.payload);
  }).addCase(N.fulfilled, (t, r) => {
    let n = r.payload.response.facets;
    fd(t, n, DD);
  }).addCase(pe, (t, r) => {
    On(t, r.payload);
  });
});
function qD(e7) {
  return { ...cd, currentValues: [], preventAutoSelect: false, type: "numericalRange", ...e7 };
}
function DD(e7) {
  return e7.map((t) => {
    let { numberOfResults: r, ...n } = t;
    return n;
  });
}
var sF = { facetId: K, selection: new RecordValue({ values: xo }) };
W("numericFacet/executeToggleSelect", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, sF), t(mr(e7)), t(ad(e7)), t(Z());
});
W("numericFacet/executeToggleExclude", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, sF), t(fr(e7)), t(id(e7)), t(Z());
});
var Fd = { f: new RecordValue(), fExcluded: new RecordValue(), lf: new RecordValue(), cf: new RecordValue(), nf: new RecordValue(), nfExcluded: new RecordValue(), mnf: new RecordValue(), mnfExcluded: new RecordValue(), df: new RecordValue(), dfExcluded: new RecordValue(), sortCriteria: new RecordValue(), page: new NumberValue({ min: 0 }), perPage: new NumberValue({ min: 1 }) };
var AF = h2("commerce/productListingParameters/restore", (e7) => F(e7, Fd));
var FF = { q: new StringValue(), ...Fd };
var Rd = h2("commerce/searchParameters/restore", (e7) => F(e7, FF));
$(xa(), (e7) => {
  e7.addCase(N.fulfilled, lg).addCase(Ha.fulfilled, lg).addCase(Pn.fulfilled, lg).addCase(Rd, RF).addCase(AF, RF).addCase(ae.fulfilled, (t, r) => r.payload?.facetOrder ?? t).addCase(Wl, () => xa()).addCase(LA, () => xa());
});
function lg(e7, t) {
  return t.payload.response.facets.map((r) => r.facetId);
}
function RF(e7, t) {
  return [...Object.keys(t.payload.f ?? {}), ...Object.keys(t.payload.lf ?? {}), ...Object.keys(t.payload.nf ?? {}), ...Object.keys(t.payload.df ?? {}), ...Object.keys(t.payload.cf ?? {}), ...Object.keys(t.payload.mnf ?? {})];
}
var rV = Object.getOwnPropertyNames;
var nV = Object.getOwnPropertySymbols;
var oV = Object.prototype.hasOwnProperty;
function PF(e7, t) {
  return function(n, o, a) {
    return e7(n, o, a) && t(n, o, a);
  };
}
function Id(e7) {
  return function(r, n, o) {
    if (!r || !n || typeof r != "object" || typeof n != "object")
      return e7(r, n, o);
    var a = o.cache, i = a.get(r), s = a.get(n);
    if (i && s)
      return i === n && s === r;
    a.set(r, n), a.set(n, r);
    var c = e7(r, n, o);
    return a.delete(r), a.delete(n), c;
  };
}
function wF(e7) {
  return rV(e7).concat(nV(e7));
}
var DF = Object.hasOwn || function(e7, t) {
  return oV.call(e7, t);
};
function ii(e7, t) {
  return e7 || t ? e7 === t : e7 === t || e7 !== e7 && t !== t;
}
var VF = "_owner";
var IF = Object.getOwnPropertyDescriptor;
var EF = Object.keys;
function aV(e7, t, r) {
  var n = e7.length;
  if (t.length !== n)
    return false;
  for (; n-- > 0; )
    if (!r.equals(e7[n], t[n], n, n, e7, t, r))
      return false;
  return true;
}
function iV(e7, t) {
  return ii(e7.getTime(), t.getTime());
}
function TF(e7, t, r) {
  if (e7.size !== t.size)
    return false;
  for (var n = {}, o = e7.entries(), a = 0, i, s; (i = o.next()) && !i.done; ) {
    for (var c = t.entries(), u = false, l = 0; (s = c.next()) && !s.done; ) {
      var m = i.value, p = m[0], d = m[1], f = s.value, x2 = f[0], S = f[1];
      !u && !n[l] && (u = r.equals(p, x2, a, l, e7, t, r) && r.equals(d, S, p, x2, e7, t, r)) && (n[l] = true), l++;
    }
    if (!u)
      return false;
    a++;
  }
  return true;
}
function sV(e7, t, r) {
  var n = EF(e7), o = n.length;
  if (EF(t).length !== o)
    return false;
  for (var a; o-- > 0; )
    if (a = n[o], a === VF && (e7.$$typeof || t.$$typeof) && e7.$$typeof !== t.$$typeof || !DF(t, a) || !r.equals(e7[a], t[a], a, a, e7, t, r))
      return false;
  return true;
}
function ac(e7, t, r) {
  var n = wF(e7), o = n.length;
  if (wF(t).length !== o)
    return false;
  for (var a, i, s; o-- > 0; )
    if (a = n[o], a === VF && (e7.$$typeof || t.$$typeof) && e7.$$typeof !== t.$$typeof || !DF(t, a) || !r.equals(e7[a], t[a], a, a, e7, t, r) || (i = IF(e7, a), s = IF(t, a), (i || s) && (!i || !s || i.configurable !== s.configurable || i.enumerable !== s.enumerable || i.writable !== s.writable)))
      return false;
  return true;
}
function cV(e7, t) {
  return ii(e7.valueOf(), t.valueOf());
}
function uV(e7, t) {
  return e7.source === t.source && e7.flags === t.flags;
}
function kF(e7, t, r) {
  if (e7.size !== t.size)
    return false;
  for (var n = {}, o = e7.values(), a, i; (a = o.next()) && !a.done; ) {
    for (var s = t.values(), c = false, u = 0; (i = s.next()) && !i.done; )
      !c && !n[u] && (c = r.equals(a.value, i.value, a.value, i.value, e7, t, r)) && (n[u] = true), u++;
    if (!c)
      return false;
  }
  return true;
}
function lV(e7, t) {
  var r = e7.length;
  if (t.length !== r)
    return false;
  for (; r-- > 0; )
    if (e7[r] !== t[r])
      return false;
  return true;
}
var dV = "[object Arguments]";
var pV = "[object Boolean]";
var mV = "[object Date]";
var fV = "[object Map]";
var gV = "[object Number]";
var SV = "[object Object]";
var hV = "[object RegExp]";
var yV = "[object Set]";
var CV = "[object String]";
var xV = Array.isArray;
var OF = typeof ArrayBuffer == "function" && ArrayBuffer.isView ? ArrayBuffer.isView : null;
var qF = Object.assign;
var AV = Object.prototype.toString.call.bind(Object.prototype.toString);
function FV(e7) {
  var t = e7.areArraysEqual, r = e7.areDatesEqual, n = e7.areMapsEqual, o = e7.areObjectsEqual, a = e7.arePrimitiveWrappersEqual, i = e7.areRegExpsEqual, s = e7.areSetsEqual, c = e7.areTypedArraysEqual;
  return function(l, m, p) {
    if (l === m)
      return true;
    if (l == null || m == null || typeof l != "object" || typeof m != "object")
      return l !== l && m !== m;
    var d = l.constructor;
    if (d !== m.constructor)
      return false;
    if (d === Object)
      return o(l, m, p);
    if (xV(l))
      return t(l, m, p);
    if (OF != null && OF(l))
      return c(l, m, p);
    if (d === Date)
      return r(l, m, p);
    if (d === RegExp)
      return i(l, m, p);
    if (d === Map)
      return n(l, m, p);
    if (d === Set)
      return s(l, m, p);
    var f = AV(l);
    return f === mV ? r(l, m, p) : f === hV ? i(l, m, p) : f === fV ? n(l, m, p) : f === yV ? s(l, m, p) : f === SV ? typeof l.then != "function" && typeof m.then != "function" && o(l, m, p) : f === dV ? o(l, m, p) : f === pV || f === gV || f === CV ? a(l, m, p) : false;
  };
}
function RV(e7) {
  var t = e7.circular, r = e7.createCustomConfig, n = e7.strict, o = { areArraysEqual: n ? ac : aV, areDatesEqual: iV, areMapsEqual: n ? PF(TF, ac) : TF, areObjectsEqual: n ? ac : sV, arePrimitiveWrappersEqual: cV, areRegExpsEqual: uV, areSetsEqual: n ? PF(kF, ac) : kF, areTypedArraysEqual: n ? ac : lV };
  if (r && (o = qF({}, o, r(o))), t) {
    var a = Id(o.areArraysEqual), i = Id(o.areMapsEqual), s = Id(o.areObjectsEqual), c = Id(o.areSetsEqual);
    o = qF({}, o, { areArraysEqual: a, areMapsEqual: i, areObjectsEqual: s, areSetsEqual: c });
  }
  return o;
}
function bV(e7) {
  return function(t, r, n, o, a, i, s) {
    return e7(t, r, s);
  };
}
function vV(e7) {
  var t = e7.circular, r = e7.comparator, n = e7.createState, o = e7.equals, a = e7.strict;
  if (n)
    return function(c, u) {
      var l = n(), m = l.cache, p = m === void 0 ? t ? /* @__PURE__ */ new WeakMap() : void 0 : m, d = l.meta;
      return r(c, u, { cache: p, equals: o, meta: d, strict: a });
    };
  if (t)
    return function(c, u) {
      return r(c, u, { cache: /* @__PURE__ */ new WeakMap(), equals: o, meta: void 0, strict: a });
    };
  var i = { cache: void 0, equals: o, meta: void 0, strict: a };
  return function(c, u) {
    return r(c, u, i);
  };
}
hr();
hr({ strict: true });
hr({ circular: true });
hr({ circular: true, strict: true });
hr({ createInternalComparator: function() {
  return ii;
} });
hr({ strict: true, createInternalComparator: function() {
  return ii;
} });
hr({ circular: true, createInternalComparator: function() {
  return ii;
} });
hr({ circular: true, createInternalComparator: function() {
  return ii;
}, strict: true });
function hr(e7) {
  e7 === void 0 && (e7 = {});
  var t = e7.circular, r = t === void 0 ? false : t, n = e7.createInternalComparator, o = e7.createState, a = e7.strict, i = a === void 0 ? false : a, s = RV(e7), c = FV(s), u = n ? n(c) : bV(c);
  return vV({ circular: r, comparator: c, createState: o, equals: u, strict: i });
}
function bo(e7, t, r = (n, o) => n === o) {
  return e7.length === t.length && e7.findIndex((n, o) => !r(t[o], n)) === -1;
}
function PV(e7, t) {
  return e7.length !== t.length ? false : e7.every((r) => t.findIndex((n) => ic(r, n)) !== -1);
}
var ic = hr({ createCustomConfig: (e7) => ({ ...e7, areArraysEqual: PV }) });
$(Qy(), (e7) => {
  e7.addCase(ot, (t, r) => IV(t, r.payload) ? void 0 : r.payload);
});
var IV = (e7, t) => EV(e7.context, t.context) && TV(e7.dictionaryFieldContext, t.dictionaryFieldContext) && MV(e7.advancedSearchQueries, t.advancedSearchQueries) && kV(e7.tabSet, t.tabSet) && OV(e7.staticFilterSet, t.staticFilterSet) && dg(e7.facetSet, t.facetSet) && dg(e7.dateFacetSet, t.dateFacetSet) && dg(e7.numericFacetSet, t.numericFacetSet) && DV(e7.automaticFacetSet, t.automaticFacetSet) && qV(e7.categoryFacetSet, t.categoryFacetSet) && VV(e7.pagination, t.pagination) && NV(e7.query, t.query) && QV(e7, t) && LV(e7.pipeline, t.pipeline) && BV(e7.searchHub, t.searchHub) && UV(e7.facetOrder, t.facetOrder) && _V(e7.debug, t.debug);
var EV = (e7, t) => JSON.stringify(e7.contextValues) === JSON.stringify(t.contextValues);
var TV = (e7, t) => JSON.stringify(e7.contextValues) === JSON.stringify(t.contextValues);
var kV = (e7, t) => {
  let r = NF(e7), n = NF(t);
  return r?.id === n?.id;
};
var NF = (e7) => Object.values(e7).find((t) => t.isActive);
var OV = (e7, t) => {
  for (let [r, n] of Object.entries(t)) {
    if (!e7[r])
      return false;
    let o = MF(e7[r]), a = MF(n);
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var MF = (e7) => e7.values.filter((t) => t.state !== "idle");
var dg = (e7, t) => {
  for (let [r, n] of Object.entries(t)) {
    if (!e7[r])
      return false;
    let o = e7[r].request.currentValues.filter((i) => i.state !== "idle"), a = n.request.currentValues.filter((i) => i.state !== "idle");
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var qV = (e7, t) => {
  for (let [r, n] of Object.entries(t)) {
    if (!e7[r])
      return false;
    let o = ze(e7[r]?.request.currentValues).map(({ value: i }) => i), a = ze(n?.request.currentValues).map(({ value: i }) => i);
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var DV = (e7, t) => {
  for (let [r, n] of Object.entries(t.set)) {
    if (!e7.set[r])
      return false;
    let o = e7.set[r].response.values.filter((i) => i.state !== "idle"), a = n.response.values.filter((i) => i.state !== "idle");
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var VV = (e7, t) => e7.firstResult === t.firstResult && e7.numberOfResults === t.numberOfResults;
var NV = (e7, t) => JSON.stringify(e7) === JSON.stringify(t);
var MV = (e7, t) => JSON.stringify(e7) === JSON.stringify(t);
var QV = (e7, t) => e7.sortCriteria === t.sortCriteria;
var LV = (e7, t) => e7 === t;
var BV = (e7, t) => e7 === t;
var UV = (e7, t) => bo(e7, t);
var _V = (e7, t) => e7 === t;
var YV = new NumberValue({ min: 1, default: 8, required: false });
var JV = new NumberValue({ min: 1, max: 20, default: 5, required: false });
var XV = { desiredCount: JV, numberOfValues: YV };
var Td = h2("automaticFacet/setOptions", (e7) => F(e7, XV));
var kd = h2("automaticFacet/deselectAll", (e7) => F(e7, K));
var ZV = V;
var qn = h2("automaticFacet/toggleSelectValue", (e7) => F(e7, { field: ZV, selection: new RecordValue({ values: So }) }));
$(ht(), (e7) => {
  e7.addCase(la, (t, r) => {
    let n = pg(t), o = r.payload;
    t.defaultNumberOfResults = t.numberOfResults = o, t.firstResult = sc(n, o);
  }).addCase(da, (t, r) => {
    t.numberOfResults = r.payload, t.firstResult = 0;
  }).addCase(Ye, (t) => {
    t.firstResult = 0;
  }).addCase(pa, (t, r) => {
    let n = r.payload;
    t.firstResult = sc(n, t.numberOfResults);
  }).addCase(gt, (t, r) => {
    let n = r.payload;
    t.firstResult = sc(n, t.numberOfResults);
  }).addCase(fa, (t) => {
    let r = pg(t), n = Math.max(r - 1, 1);
    t.firstResult = sc(n, t.numberOfResults);
  }).addCase(ma, (t) => {
    let r = pg(t), n = eN(t), o = Math.min(r + 1, n);
    t.firstResult = sc(o, t.numberOfResults);
  }).addCase(ae.fulfilled, (t, r) => {
    r.payload && (t.numberOfResults = r.payload.pagination.numberOfResults, t.firstResult = r.payload.pagination.firstResult);
  }).addCase(ie, (t, r) => {
    t.firstResult = r.payload.firstResult ?? t.firstResult, t.numberOfResults = r.payload.numberOfResults ?? t.defaultNumberOfResults;
  }).addCase(N.fulfilled, (t, r) => {
    let { response: n } = r.payload;
    t.totalCountFiltered = n.totalCountFiltered;
  }).addCase(me, (t) => {
    je(t);
  }).addCase(dr, (t) => {
    je(t);
  }).addCase(cr, (t) => {
    je(t);
  }).addCase(fr, (t) => {
    je(t);
  }).addCase(fo, (t) => {
    je(t);
  }).addCase(sr, (t) => {
    je(t);
  }).addCase(Yt, (t) => {
    je(t);
  }).addCase(xn, (t) => {
    je(t);
  }).addCase(Ua, (t) => {
    je(t);
  }).addCase(lr, (t) => {
    je(t);
  }).addCase(mr, (t) => {
    je(t);
  }).addCase(Se, (t) => {
    je(t);
  }).addCase(Mr, (t) => {
    je(t);
  }).addCase(Qr, (t) => {
    je(t);
  }).addCase(mo, (t) => {
    je(t);
  }).addCase(qn, (t) => {
    je(t);
  });
});
function je(e7) {
  e7.firstResult = ht().firstResult;
}
function pg(e7) {
  let { firstResult: t, numberOfResults: r } = e7;
  return mg(t, r);
}
function eN(e7) {
  let { totalCountFiltered: t, numberOfResults: r } = e7;
  return fg(t, r);
}
function sc(e7, t) {
  return (e7 - 1) * t;
}
function mg(e7, t) {
  return Math.round(e7 / t) + 1;
}
function fg(e7, t) {
  let r = Math.min(e7, 5e3);
  return Math.ceil(r / t);
}
var vN = { results: new ArrayValue({ required: true, each: new RecordValue({ values: iu }) }), maxLength: new NumberValue({ required: true, min: 1, default: 10 }) };
var pi = h2("recentResults/registerRecentResults", (e7) => F(e7, vN));
var Rt = h2("recentResults/pushRecentResult", (e7) => (Ke(e7), { payload: e7 }));
var mi = h2("recentResults/clearRecentResults");
var cc = { id: V };
var fi = h2("querySuggest/register", (e7) => F(e7, { ...cc, count: new NumberValue({ min: 0 }) }));
var WF = h2("querySuggest/unregister", (e7) => F(e7, cc));
var Cr = h2("querySuggest/selectSuggestion", (e7) => F(e7, { ...cc, expression: ce }));
var Vn = h2("querySuggest/clear", (e7) => F(e7, cc));
var Nn = W("querySuggest/fetch", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, validatePayload: o, navigatorContext: a } }) => {
  o(e7, cc);
  let i = e7.id, s = await NN(i, t(), a), c = await n.querySuggest(s);
  return we(c) ? r(c.error) : { id: i, q: s.q, ...c.success };
});
var NN = async (e7, t, r) => ({ accessToken: t.configuration.accessToken, organizationId: t.configuration.organizationId, url: t.configuration.search.apiBaseUrl ?? ve(t.configuration.organizationId, t.configuration.environment), count: t.querySuggest[e7].count, q: t.querySet[e7], locale: t.configuration.search.locale, timezone: t.configuration.search.timezone, actionsHistory: t.configuration.analytics.enabled ? dt.getHistory() : [], ...t.context && { context: t.context.contextValues }, ...t.pipeline && { pipeline: t.pipeline }, ...t.searchHub && { searchHub: t.searchHub }, tab: t.configuration.analytics.originLevel2, ...t.configuration.analytics.enabled && { ...t.configuration.analytics.enabled && t.configuration.analytics.analyticsMode === "legacy" ? await ha(t.configuration.analytics) : ga(t.configuration.analytics, r) }, ...t.configuration.search.authenticationProviders.length && { authentication: t.configuration.search.authenticationProviders.join(",") } });
var uc = { id: V, query: ce };
var gi = h2("querySet/register", (e7) => F(e7, uc));
var vo = h2("querySet/update", (e7) => F(e7, uc));
var HF = h2("commerce/querySet/register", (e7) => F(e7, uc));
var zF = h2("commerce/querySet/update", (e7) => F(e7, uc));
$(vu(), (e7) => {
  e7.addCase(gi, (t, r) => YF(t, r.payload)).addCase(HF, (t, r) => YF(t, r.payload)).addCase(vo, (t, r) => {
    let { id: n, query: o } = r.payload;
    lc(t, n, o);
  }).addCase(zF, (t, r) => {
    let { id: n, query: o } = r.payload;
    lc(t, n, o);
  }).addCase(Cr, (t, r) => {
    let { id: n, expression: o } = r.payload;
    lc(t, n, o);
  }).addCase(Xx, (t, r) => {
    let { id: n, expression: o } = r.payload;
    lc(t, n, o);
  }).addCase(Pn.fulfilled, (t, r) => {
    let { queryExecuted: n } = r.payload;
    Sg(t, n);
  }).addCase(N.fulfilled, (t, r) => {
    let { queryExecuted: n } = r.payload;
    Sg(t, n);
  }).addCase(ie, KF).addCase(Rd, KF).addCase(ae.fulfilled, (t, r) => {
    if (r.payload)
      for (let [n, o] of Object.entries(r.payload.querySet))
        lc(t, n, o);
  });
});
function KF(e7, t) {
  isNullOrUndefined(t.payload.q) || Sg(e7, t.payload.q);
}
function Sg(e7, t) {
  Object.keys(e7).forEach((r) => e7[r] = t);
}
var lc = (e7, t, r) => {
  t in e7 && (e7[t] = r);
};
var YF = (e7, t) => {
  let { id: r, query: n } = t;
  r in e7 || (e7[r] = n);
};
var XF = () => ({});
$(XF(), (e7) => e7.addCase(fi, (t, r) => {
  ZF(t, r.payload);
}).addCase(Jx, (t, r) => {
  ZF(t, r.payload);
}).addCase(WF, (t, r) => {
  delete t[r.payload.id];
}).addCase(Nn.pending, eR).addCase(Nn.fulfilled, (t, r) => {
  let n = t[r.meta.arg.id];
  if (!n || r.meta.requestId !== n.currentRequestId)
    return;
  let { q: o } = r.payload;
  o && n.partialQueries.push(o.replace(/;/, encodeURIComponent(";"))), n.responseId = r.payload.responseId, n.completions = r.payload.completions, n.isLoading = false, n.error = null;
}).addCase(Nn.rejected, tR).addCase(vn.pending, eR).addCase(vn.fulfilled, (t, r) => {
  let n = t[r.meta.arg.id];
  if (!n || r.meta.requestId !== n.currentRequestId)
    return;
  let { query: o } = r.payload;
  o && n.partialQueries.push(o.replace(/;/, encodeURIComponent(";"))), n.responseId = r.payload.responseId, n.completions = r.payload.completions.map((a) => ({ expression: a.expression, highlighted: a.highlighted, score: 0, executableConfidence: 0 })), n.isLoading = false, n.error = null;
}).addCase(vn.rejected, tR).addCase(Vn, (t, r) => {
  rR(t, r.payload);
}).addCase(Yx, (t, r) => {
  rR(t, r.payload);
}));
function ZF(e7, t) {
  let r = t.id;
  r in e7 || (e7[r] = QN(t));
}
function QN(e7) {
  return { id: "", completions: [], responseId: "", count: 5, currentRequestId: "", error: null, partialQueries: [], isLoading: false, ...e7 };
}
function eR(e7, t) {
  let r = e7[t.meta.arg.id];
  r && (r.currentRequestId = t.meta.requestId, r.isLoading = true);
}
function tR(e7, t) {
  let r = e7[t.meta.arg.id];
  r && (r.error = t.payload || null, r.isLoading = false);
}
function rR(e7, t) {
  let r = e7[t.id];
  r && (r.responseId = "", r.completions = [], r.partialQueries = []);
}
$(Fe(), (e7) => e7.addCase(Le, (t, r) => ({ ...t, ...r.payload })).addCase(St, (t, r) => {
  t.q = r.payload;
}).addCase(Cr, (t, r) => {
  t.q = r.payload.expression;
}).addCase(ae.fulfilled, (t, r) => r.payload?.query ?? t).addCase(ie, (t, r) => {
  t.q = r.payload.q ?? t.q, t.enableQuerySyntax = r.payload.enableQuerySyntax ?? t.enableQuerySyntax;
}));
function Ud(e7) {
  return e7 ? e7.expiresAt && Date.now() >= e7.expiresAt : false;
}
var sR = (e7, t) => {
  let { id: r } = e7;
  if (!t[r])
    return t[r] = { q: "", cache: {} }, t;
};
var cR = (e7, t) => {
  let { q: r, id: n } = e7;
  r && (t[n].q = r);
};
var uR = (e7, t) => {
  let { id: r } = e7;
  Object.entries(t[r].cache).forEach(([n, o]) => {
    Ud(o) && delete t[r].cache[n];
  });
};
var lR = (e7, t, r) => {
  for (let o in t)
    for (let a in t[o].cache)
      t[o].cache[a].isActive = false;
  if (!Ag(e7, t)) {
    jN(e7, t, r);
    return;
  }
  let n = Ag(e7, t);
  n.isLoading = true, n.isActive = true, n.error = null;
};
var dR = (e7, t, r) => {
  let { id: n, q: o, searchUid: a, cacheTimeout: i, totalCountFiltered: s, duration: c } = e7;
  t[n].cache[o] = { ...Ag(e7, t), ...r, isActive: true, searchUid: a, isLoading: false, error: null, expiresAt: i ? i + Date.now() : 0, totalCountFiltered: s, duration: c };
};
var pR = (e7, t) => {
  let { id: r, q: n, error: o } = e7;
  t[r].cache[n].error = o || null, t[r].cache[n].isLoading = false, t[r].cache[n].isActive = false;
};
var Ag = (e7, t) => {
  let { q: r, id: n } = e7;
  return t[n].cache[r] || null;
};
var jN = (e7, t, r) => {
  let { q: n, id: o } = e7;
  t[o].cache[n] = { isLoading: true, error: null, expiresAt: 0, isActive: true, searchUid: "", totalCountFiltered: 0, duration: 0, ...r };
};
function mR() {
  return {};
}
$(mR(), (e7) => {
  e7.addCase(ca, (t, r) => {
    sR(r.payload, t);
  }), e7.addCase(jt, (t, r) => {
    cR(r.payload, t);
  }), e7.addCase(ua, (t, r) => {
    uR(r.payload, t);
  }), e7.addCase(Pa.pending, (t, r) => {
    lR(r.meta.arg, t, { results: [] });
  }), e7.addCase(Pa.fulfilled, (t, r) => {
    let n = r.payload.results.map((o) => ({ ...o, searchUid: r.payload.searchUid }));
    dR({ ...r.payload, ...r.meta.arg }, t, { results: n });
  }), e7.addCase(Pa.rejected, (t, r) => {
    pR(r.meta.arg, t);
  });
});
var SR = { by: new EnumValue({ enum: Xo, required: true }) };
var Ci = h2("sortCriteria/register", (e7) => hR(e7));
var xi = h2("sortCriteria/update", (e7) => hR(e7));
var hR = (e7) => isArray(e7) ? (e7.forEach((t) => F(t, SR)), { payload: e7 }) : F(e7, SR);
$(pt(), (e7) => {
  e7.addCase(Ci, (t, r) => Er(r.payload)).addCase(xi, (t, r) => Er(r.payload)).addCase(ae.fulfilled, (t, r) => r.payload?.sortCriteria ?? t).addCase(ie, (t, r) => r.payload.sortCriteria ?? t);
});
var Po = V;
var Gd = new RecordValue({ options: { required: true }, values: { caption: ce, expression: ce, state: new StringValue({ constrainTo: ["idle", "selected", "excluded"] }) } });
var Wd = new ArrayValue({ required: true, each: Gd });
var Ai = h2("staticFilter/register", (e7) => F(e7, { id: Po, values: Wd }));
var Lr = h2("staticFilter/toggleSelect", (e7) => F(e7, { id: Po, value: Gd }));
var Br = h2("staticFilter/toggleExclude", (e7) => F(e7, { id: Po, value: Gd }));
var Qn = h2("staticFilter/deselectAllFilterValues", (e7) => F(e7, Po));
$(Pu(), (e7) => e7.addCase(Ai, (t, r) => {
  let n = r.payload, { id: o } = n;
  o in t || (t[o] = n);
}).addCase(Lr, (t, r) => {
  let { id: n, value: o } = r.payload, a = t[n];
  if (!a)
    return;
  let i = a.values.find((c) => c.caption === o.caption);
  if (!i)
    return;
  let s = i.state === "selected";
  i.state = s ? "idle" : "selected";
}).addCase(Br, (t, r) => {
  let { id: n, value: o } = r.payload, a = t[n];
  if (!a)
    return;
  let i = a.values.find((c) => c.caption === o.caption);
  if (!i)
    return;
  let s = i.state === "excluded";
  i.state = s ? "idle" : "excluded";
}).addCase(Qn, (t, r) => {
  let n = r.payload, o = t[n];
  o && o.values.forEach((a) => a.state = "idle");
}).addCase(Se, (t) => {
  Object.values(t).forEach((r) => {
    r.values.forEach((n) => n.state = "idle");
  });
}).addCase(ie, (t, r) => {
  let n = r.payload.sf || {};
  Object.entries(t).forEach(([o, a]) => {
    let i = n[o] || [];
    a.values.forEach((s) => {
      s.state = i.includes(s.caption) ? "selected" : "idle";
    });
  });
}));
$(wu(), (e7) => {
  e7.addCase(qa, (t, r) => {
    let n = r.payload, { id: o } = n;
    o in t || (t[o] = { ...n, isActive: false });
  }).addCase(Ye, (t, r) => {
    let n = r.payload;
    xR(t, n);
  }).addCase(ie, (t, r) => {
    let n = r.payload.tab || "";
    xR(t, n), Ye(n);
  }).addCase(ae.fulfilled, (t, r) => r.payload?.tabSet ?? t);
});
function xR(e7, t) {
  t in e7 && Object.keys(e7).forEach((n) => {
    e7[n].isActive = n === t;
  });
}
function IR(e7) {
  return e7.type === "redirect";
}
var rp = class {
  constructor(t) {
    this.response = t;
  }
  get basicExpression() {
    return this.response.parsedInput.basicExpression;
  }
  get largeExpression() {
    return this.response.parsedInput.largeExpression;
  }
  get redirectionUrl() {
    let t = this.response.preprocessingOutput.triggers.filter(IR);
    return t.length ? t[0].content : null;
  }
};
var bi = h2("standaloneSearchBox/register", (e7) => F(e7, { id: V, redirectionUrl: V, overwrite: new BooleanValue({ required: false }) }));
var vi = h2("standaloneSearchBox/updateRedirectionUrl", (e7) => F(e7, { id: V, redirectionUrl: V }));
var Pi = h2("standaloneSearchBox/reset", (e7) => F(e7, { id: V }));
var wi = h2("standaloneSearchBox/updateAnalyticsToSearchFromLink", (e7) => F(e7, { id: V }));
var Ii = h2("standaloneSearchBox/updateAnalyticsToOmniboxFromLink");
var Ln = W("standaloneSearchBox/fetchRedirect", async (e7, { dispatch: t, getState: r, rejectWithValue: n, extra: { apiClient: o, validatePayload: a, navigatorContext: i } }) => {
  a(e7, { id: new StringValue({ emptyAllowed: false }) });
  let s = await wM(r(), i), c = await o.plan(s);
  if (we(c))
    return n(c.error);
  let { redirectionUrl: u } = new rp(c.success);
  return u && t(PM(u)), u || "";
});
var PM = (e7) => L("analytics/standaloneSearchBox/redirect", (t) => t.makeTriggerRedirect({ redirectedTo: e7 }));
var wM = async (e7, t) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: e7.configuration.search.apiBaseUrl ?? ve(e7.configuration.organizationId, e7.configuration.environment), locale: e7.configuration.search.locale, timezone: e7.configuration.search.timezone, q: e7.query.q, ...e7.context && { context: e7.context.contextValues }, ...e7.pipeline && { pipeline: e7.pipeline }, ...e7.searchHub && { searchHub: e7.searchHub }, ...e7.configuration.analytics.enabled && e7.configuration.analytics.analyticsMode === "legacy" ? await ha(e7.configuration.analytics) : ga(e7.configuration.analytics, t), ...e7.configuration.search.authenticationProviders.length && { authentication: e7.configuration.search.authenticationProviders.join(",") } });
function ER() {
  return {};
}
$(ER(), (e7) => e7.addCase(bi, (t, r) => {
  let { id: n, redirectionUrl: o, overwrite: a } = r.payload;
  !a && n in t || (t[n] = bg(o));
}).addCase(Pi, (t, r) => {
  let { id: n } = r.payload, o = t[n];
  if (o) {
    t[n] = bg(o.defaultRedirectionUrl);
    return;
  }
}).addCase(vi, (t, r) => {
  let { id: n, redirectionUrl: o } = r.payload;
  n in t && (t[n] = bg(o));
}).addCase(Ln.pending, (t, r) => {
  let n = t[r.meta.arg.id];
  n && (n.isLoading = true);
}).addCase(Ln.fulfilled, (t, r) => {
  let n = r.payload, o = t[r.meta.arg.id];
  o && (o.redirectTo = n || o.defaultRedirectionUrl, o.isLoading = false);
}).addCase(Ln.rejected, (t, r) => {
  let n = t[r.meta.arg.id];
  n && (n.isLoading = false);
}).addCase(wi, (t, r) => {
  let n = t[r.payload.id];
  n && (n.analytics.cause = "searchFromLink");
}).addCase(Ii, (t, r) => {
  let n = t[r.payload.id];
  n && (n.analytics.cause = "omniboxFromLink", n.analytics.metadata = r.payload.metadata);
}));
function bg(e7) {
  return { defaultRedirectionUrl: e7, redirectTo: "", isLoading: false, analytics: { cause: "", metadata: null } };
}
async function cp(e7, t) {
  let { search: r, accessToken: n, organizationId: o } = e7.configuration, a = e7.query?.q || "";
  return { url: r.apiBaseUrl ?? ve(e7.configuration.organizationId, e7.configuration.environment), accessToken: n, organizationId: o, enableNavigation: false, q: a, ...t, requestedOutputSize: t.requestedOutputSize || 0, ...r.authenticationProviders.length && { authentication: r.authenticationProviders.join(",") } };
}
var wo = W("resultPreview/fetchResultContent", async (e7, { extra: t, getState: r, rejectWithValue: n }) => {
  let o = r(), a = await cp(o, e7), i = await t.apiClient.html(a);
  return we(i) ? n(i.error) : { content: i.success, uniqueId: e7.uniqueId };
});
var ki = h2("resultPreview/next");
var Oi = h2("resultPreview/previous");
var qi = h2("resultPreview/prepare", (e7) => F(e7, { results: new ArrayValue({ required: true }) }));
var $R = 2048;
var Di = W("resultPreview/updateContentURL", async (e7, { getState: t, extra: r }) => {
  let n = t(), o = FS(await e7.buildResultPreviewRequest(n, { uniqueId: e7.uniqueId, requestedOutputSize: e7.requestedOutputSize }), e7.path);
  return o?.length > $R && r.logger.error(`The content URL was truncated as it exceeds the maximum allowed length of ${$R} characters.`), { contentURL: o };
});
function Eg() {
  return { uniqueId: "", content: "", isLoading: false, position: -1, resultsWithPreview: [] };
}
var Tg = (e7) => {
  let { content: t, isLoading: r, uniqueId: n, contentURL: o } = Eg();
  e7.content = t, e7.isLoading = r, e7.uniqueId = n, e7.contentURL = o;
};
var kg = (e7) => e7.filter((t) => t.hasHtmlVersion).map((t) => t.uniqueId);
$(Eg(), (e7) => {
  e7.addCase(wo.pending, (t) => {
    t.isLoading = true;
  }).addCase(wo.fulfilled, (t, r) => {
    let { content: n, uniqueId: o } = r.payload;
    t.position = t.resultsWithPreview.indexOf(o), t.content = n, t.uniqueId = o, t.isLoading = false;
  }).addCase(N.fulfilled, (t, r) => {
    Tg(t), t.resultsWithPreview = kg(r.payload.response.results);
  }).addCase(dn.fulfilled, (t, r) => {
    Tg(t), t.resultsWithPreview = t.resultsWithPreview.concat(kg(r.payload.response.results));
  }).addCase(Wt.fulfilled, Tg).addCase(qi, (t, r) => {
    t.resultsWithPreview = kg(r.payload.results);
  }).addCase(ki, (t) => {
    if (t.isLoading)
      return;
    let r = t.position + 1;
    r > t.resultsWithPreview.length - 1 && (r = 0), t.position = r;
  }).addCase(Oi, (t) => {
    if (t.isLoading)
      return;
    let r = t.position - 1;
    r < 0 && (r = t.resultsWithPreview.length - 1), t.position = r;
  }).addCase(Di.fulfilled, (t, r) => {
    t.contentURL = r.payload.contentURL;
  });
});
function qQ(e7, t) {
  return e7.raw[t.collection];
}
function Og(e7, t) {
  return e7.raw[t.parent];
}
function hc(e7, t) {
  let r = e7.raw[t.child];
  return Ac(r) ? r[0] : r;
}
function DQ(e7, t) {
  return (e7 || t) !== void 0 && e7 === t;
}
function KR(e7, t, r, n = []) {
  let o = hc(e7, r);
  return o ? n.indexOf(o) !== -1 ? [] : t.filter((a) => {
    let i = hc(a, r) === hc(e7, r);
    return Og(a, r) === o && !i;
  }).map((a) => {
    let i = { ...a, searchUid: e7.searchUid };
    return { result: i, children: KR(i, t, r, [...n, o]) };
  }) : [];
}
function VQ(e7, t) {
  return e7.find((r) => {
    let n = Og(r, t) === void 0, o = DQ(Og(r, t), hc(r, t));
    return n || o;
  });
}
function YR(e7) {
  return e7.parentResult ? YR(e7.parentResult) : e7;
}
function NQ(e7, t, r, n) {
  let o = ou(e7), i = { ...n ?? VQ(o, t) ?? YR(e7), searchUid: r };
  return { result: i, children: KR(i, o, t), moreResultsAvailable: e7.totalNumberOfChildResults > 1, isLoadingMoreResults: false };
}
function lp(e7, t, r, n) {
  let o = {};
  return e7.forEach((a) => {
    let i = qQ(a, t);
    i && (!hc(a, t) && !a.parentResult || (o[i] = NQ(a, t, r, n)));
  }), o;
}
function zR(e7, t) {
  if (!e7.collections[t])
    throw new Error(`Missing collection ${t} from ${Object.keys(e7.collections)}: Folding most probably in an invalid state...`);
  return e7.collections[t];
}
$(al(), (e7) => e7.addCase(N.fulfilled, (t, { payload: r }) => {
  t.collections = t.enabled ? lp(r.response.results, t.fields, r.response.searchUid) : {};
}).addCase(Wt.fulfilled, (t, { payload: r }) => {
  t.collections = t.enabled ? lp(r.response.results, t.fields, r.response.searchUid) : {};
}).addCase(dn.fulfilled, (t, { payload: r }) => {
  t.collections = t.enabled ? { ...t.collections, ...lp(r.response.results, t.fields, r.response.searchUid) } : {};
}).addCase(hn, (t, { payload: r }) => t.enabled ? t : { enabled: true, collections: {}, fields: { collection: r.collectionField ?? t.fields.collection, parent: r.parentField ?? t.fields.parent, child: r.childField ?? t.fields.child }, filterFieldRange: r.numberOfFoldedResults ?? t.filterFieldRange }).addCase(yn.pending, (t, { meta: r }) => {
  let n = r.arg;
  zR(t, n).isLoadingMoreResults = true;
}).addCase(yn.rejected, (t, { meta: r }) => {
  let n = r.arg;
  zR(t, n).isLoadingMoreResults = false;
}).addCase(yn.fulfilled, (t, { payload: { collectionId: r, results: n, rootResult: o, searchUid: a } }) => {
  let i = lp(n, t.fields, a, o);
  if (!i || !i[r])
    throw new Error(`Unable to create collection ${r} from received results: ${JSON.stringify(n)}. Folding most probably in an invalid state... `);
  t.collections[r] = i[r], t.collections[r].moreResultsAvailable = false;
}));
function XR(e7) {
  return e7.query = "", e7.queryModification = { originalQuery: "", newQuery: "", queryToIgnore: e7.queryModification.queryToIgnore }, e7;
}
function ZR(e7, t) {
  let r = [], o = [], a = [];
  return t.forEach((i) => {
    switch (i.type) {
      case "redirect":
        r.push(i.content);
        break;
      case "query":
        break;
      case "execute":
        o.push({ functionName: i.content.name, params: i.content.params });
        break;
      case "notify":
        a.push(i.content);
        break;
    }
  }), e7.redirectTo = r[0] ?? "", e7.query = e7.queryModification.newQuery, e7.executions = o, e7.notifications = a, e7;
}
function eb(e7, t) {
  return e7.queryModification = { ...t, queryToIgnore: "" }, e7;
}
function tb(e7, t) {
  return e7.queryModification.queryToIgnore = t, e7;
}
var rb = () => ({ redirectTo: "", query: "", executions: [], notifications: [], queryModification: { originalQuery: "", newQuery: "", queryToIgnore: "" } });
$(rb(), (e7) => e7.addCase(N.pending, XR).addCase(N.fulfilled, (t, r) => ZR(t, r.payload.response.triggers)).addCase(Aa, (t, r) => eb(t, r.payload)).addCase(an, (t, r) => tb(t, r.payload)));
var pp = () => new RecordValue({ values: { questionAnswerId: V }, options: { required: true } });
function Vi(e7) {
  return F(e7, pp());
}
var Ni = h2("smartSnippet/expand");
var Mi = h2("smartSnippet/collapse");
var Qi = h2("smartSnippet/like");
var Li = h2("smartSnippet/dislike");
var Bi = h2("smartSnippet/feedbackModal/open");
var Un = h2("smartSnippet/feedbackModal/close");
var Ui = h2("smartSnippet/related/expand", (e7) => Vi(e7));
var _i = h2("smartSnippet/related/collapse", (e7) => Vi(e7));
var Wg = () => ({ liked: false, disliked: false, expanded: false, feedbackModalOpen: false, relatedQuestions: [] });
var ab = (e7, t) => e7.findIndex((r) => r.questionAnswerId === t.questionAnswerId);
function ib({ question: e7, answerSnippet: t, documentId: { contentIdKey: r, contentIdValue: n } }) {
  return To({ question: e7, answerSnippet: t, contentIdKey: r, contentIdValue: n });
}
function YQ(e7, t) {
  let r = ib(e7);
  return t && r === t.questionAnswerId ? t : { contentIdKey: e7.documentId.contentIdKey, contentIdValue: e7.documentId.contentIdValue, expanded: false, questionAnswerId: r };
}
$(Wg(), (e7) => e7.addCase(Ni, (t) => {
  t.expanded = true;
}).addCase(Mi, (t) => {
  t.expanded = false;
}).addCase(Qi, (t) => {
  t.liked = true, t.disliked = false, t.feedbackModalOpen = false;
}).addCase(Li, (t) => {
  t.liked = false, t.disliked = true;
}).addCase(Bi, (t) => {
  t.feedbackModalOpen = true;
}).addCase(Un, (t) => {
  t.feedbackModalOpen = false;
}).addCase(N.fulfilled, (t, r) => {
  let n = r.payload.response.questionAnswer.relatedQuestions.map((a, i) => YQ(a, t.relatedQuestions[i])), o = ib(r.payload.response.questionAnswer);
  return t.questionAnswerId === o ? { ...t, relatedQuestions: n } : { ...Wg(), relatedQuestions: n, questionAnswerId: o };
}).addCase(Ui, (t, r) => {
  let n = ab(t.relatedQuestions, r.payload);
  n !== -1 && (t.relatedQuestions[n].expanded = true);
}).addCase(_i, (t, r) => {
  let n = ab(t.relatedQuestions, r.payload);
  n !== -1 && (t.relatedQuestions[n].expanded = false);
}));
var iL = { queries: new ArrayValue({ required: true, each: new StringValue({ emptyAllowed: false }) }), maxLength: new NumberValue({ required: true, min: 1, default: 10 }) };
var ji = h2("recentQueries/registerRecentQueries", (e7) => F(e7, iL));
var $i = h2("recentQueries/clearRecentQueries");
function pb() {
  return { queries: [], maxLength: 10 };
}
$(pb(), (e7) => {
  e7.addCase(ji, sL).addCase($i, cL).addCase(N.fulfilled, (t, r) => {
    let n = r.payload.queryExecuted, o = r.payload.response.results;
    !n.length || !o.length || uL(n, t);
  });
});
function sL(e7, t) {
  e7.queries = Array.from(new Set(t.payload.queries.map((r) => r.trim().toLowerCase()))).slice(0, t.payload.maxLength), e7.maxLength = t.payload.maxLength;
}
function cL(e7) {
  e7.queries = [];
}
function uL(e7, t) {
  let r = e7.trim().toLowerCase();
  if (r === "")
    return;
  let n = Array.from(new Set(t.queries.filter((o) => o.trim().toLowerCase() !== r))).slice(0, t.maxLength - 1);
  t.queries = [r, ...n];
}
function hb() {
  return { results: [], maxLength: 10 };
}
$(hb(), (e7) => {
  e7.addCase(pi, (t, r) => {
    t.results = r.payload.results.slice(0, r.payload.maxLength), t.maxLength = r.payload.maxLength;
  }).addCase(mi, (t) => {
    t.results = [];
  }).addCase(Rt, (t, r) => {
    let n = r.payload;
    t.results = t.results.filter((a) => a.uniqueId !== n.uniqueId);
    let o = t.results.slice(0, t.maxLength - 1);
    t.results = [n, ...o];
  });
});
$(Go(), (e7) => {
  e7.addCase(N.fulfilled, (t, r) => {
    t.set = {}, r.payload.response.generateAutomaticFacets?.facets?.forEach((o) => {
      t.set[o.field] = { response: o };
    });
  }).addCase(Td, (t, r) => {
    r.payload.desiredCount && (t.desiredCount = r.payload.desiredCount), r.payload.numberOfValues && (t.numberOfValues = r.payload.numberOfValues);
  }).addCase(qn, (t, r) => {
    let { field: n, selection: o } = r.payload, a = t.set[n]?.response;
    if (!a)
      return;
    let i = a.values.find((c) => c.value === o.value);
    if (!i)
      return;
    let s = i.state === "selected";
    i.state = s ? "idle" : "selected";
  }).addCase(kd, (t, r) => {
    let n = r.payload, o = t.set[n]?.response;
    if (o)
      for (let a of o.values)
        a.state = "idle";
  }).addCase(ie, (t, r) => {
    let n = r.payload.af ?? {}, o = Object.keys(t.set);
    for (let a in n)
      if (!t.set[a]) {
        let i = VL(a), s = n[a].map((c) => Cb(c));
        i.values.push(...s), t.set[a] = { response: i };
      }
    for (let a of o)
      if (!(a in n)) {
        let i = t.set[a]?.response;
        for (let s of i.values)
          s.state = "idle";
      }
    for (let a in n) {
      let i = t.set[a]?.response;
      if (i) {
        let s = i.values, c = new Set(n[a]);
        for (let u of s)
          c.has(u.value) ? (u.state = "selected", c.delete(u.value)) : u.state = "idle";
        for (let u of c)
          i.values.push(Cb(u));
      }
    }
  }).addCase(ae.fulfilled, (t, r) => {
    if (r.payload && Object.keys(r.payload.automaticFacetSet.set).length !== 0)
      return r.payload.automaticFacetSet;
  }).addCase(Se, (t) => {
    Object.values(t.set).forEach(({ response: r }) => {
      r.values.forEach((n) => n.state = "idle");
    });
  });
});
function VL(e7) {
  return { field: e7, values: [], moreValuesAvailable: false, label: "", indexScore: 0 };
}
function Cb(e7) {
  return { value: e7, state: "selected", numberOfResults: 0 };
}
function Hg() {
  return { id: "", isVisible: true, isEnabled: true, isLoading: false, isStreaming: false, citations: [], liked: false, disliked: false, responseFormat: { contentFormat: ["text/plain"] }, feedbackModalOpen: false, feedbackSubmitted: false, fieldsToIncludeInCitations: [], isAnswerGenerated: false, expanded: false, cannotAnswer: false };
}
$(Hg(), (e7) => e7.addCase(Ea, (t, { payload: r }) => {
  t.isVisible = r;
}).addCase(Ns, (t, { payload: r }) => {
  t.isEnabled = r;
}).addCase($u, (t, { payload: r }) => {
  t.id = r.id;
}).addCase(Ms, (t, { payload: r }) => {
  t.isLoading = false, t.isStreaming = true, t.answer || (t.answer = ""), t.answer += r.textDelta, delete t.error;
}).addCase(Qs, (t, { payload: r }) => {
  t.isLoading = false, t.isStreaming = true;
  let n = /* @__PURE__ */ new Map();
  for (let o of [t.citations, r.citations])
    for (let a of o)
      n.set(a.uri, a);
  t.citations = Array.from(n.values()), delete t.error;
}).addCase(sf, (t, { payload: r }) => {
  t.isLoading = false, t.isStreaming = false, t.error = { ...r, isRetryable: r.code === Tp }, t.citations = [], delete t.answer;
}).addCase(Bu, (t) => {
  t.liked = true, t.disliked = false;
}).addCase(Uu, (t) => {
  t.liked = false, t.disliked = true;
}).addCase(_u, (t) => {
  t.feedbackModalOpen = true;
}).addCase(Gu, (t) => {
  t.feedbackModalOpen = false;
}).addCase(Ta, (t) => {
  t.feedbackSubmitted = true;
}).addCase(zt, (t) => ({ ...Hg(), ...t.answerConfigurationId ? { answerConfigurationId: t.answerConfigurationId } : {}, responseFormat: t.responseFormat, fieldsToIncludeInCitations: t.fieldsToIncludeInCitations, isVisible: t.isVisible, id: t.id })).addCase(Vs, (t, { payload: r }) => {
  t.isLoading = r;
}).addCase(Qu, (t, { payload: r }) => {
  t.isStreaming = r;
}).addCase(Bs, (t, { payload: r }) => {
  t.answerContentFormat = r;
}).addCase(Wu, (t, { payload: r }) => {
  t.responseFormat = r;
}).addCase(zu, (t, r) => {
  t.fieldsToIncludeInCitations = [...new Set(t.fieldsToIncludeInCitations.concat(r.payload))];
}).addCase(cf, (t, { payload: r }) => {
  t.isAnswerGenerated = r;
}).addCase(Ls, (t) => {
  t.expanded = true;
}).addCase(ju, (t) => {
  t.expanded = false;
}).addCase(Hu, (t, { payload: r }) => {
  t.answerConfigurationId = r;
}).addCase(no, (t, { payload: r }) => {
  t.cannotAnswer = r;
}));
Xu.injectEndpoints({ endpoints: (e7) => ({ post: e7.mutation({ query: (t) => ({ url: "/evaluations", method: "POST", body: t }) }) }) });
var _n = () => new StringValue({ required: false, emptyAllowed: true });
var xp = h2("advancedSearchQueries/update", (e7) => F(e7, { aq: _n(), cq: _n(), lq: _n(), dq: _n() }));
var Ap = h2("advancedSearchQueries/register", (e7) => F(e7, { aq: _n(), cq: _n(), lq: _n(), dq: _n() }));
$(It(), (e7) => {
  e7.addCase(xp, (t, r) => {
    let { aq: n, cq: o, lq: a, dq: i } = r.payload;
    isUndefined(n) || (t.aq = n, t.aqWasSet = true), isUndefined(o) || (t.cq = o, t.cqWasSet = true), isUndefined(a) || (t.lq = a, t.lqWasSet = true), isUndefined(i) || (t.dq = i, t.dqWasSet = true);
  }).addCase(Ap, (t, r) => {
    let { aq: n, cq: o, lq: a, dq: i } = r.payload;
    isUndefined(n) || (t.defaultFilters.aq = n, t.aqWasSet || (t.aq = n)), isUndefined(o) || (t.defaultFilters.cq = o, t.cqWasSet || (t.cq = o)), isUndefined(a) || (t.defaultFilters.lq = a, t.lqWasSet || (t.lq = a)), isUndefined(i) || (t.defaultFilters.dq = i, t.dqWasSet || (t.dq = i));
  }).addCase(ae.fulfilled, (t, r) => r.payload?.advancedSearchQueries ?? t).addCase(ie, (t, r) => {
    let { aq: n, cq: o } = r.payload;
    isUndefined(n) || (t.aq = n, t.aqWasSet = true), isUndefined(o) || (t.cq = o, t.cqWasSet = true);
  });
});
var Fp = h2("excerptLength/set", (e7) => F(e7, new NumberValue({ min: 0, required: true })));
function Ib() {
  return { length: void 0 };
}
$(Ib(), (e7) => {
  e7.addCase(Fp, (t, r) => {
    t.length = r.payload;
  });
});
W("analytics/addPageViewEntry", async (e7, { getState: t }) => {
  t().configuration.analytics.enabled && dt.addElement({ name: "PageView", value: e7, time: JSON.stringify(/* @__PURE__ */ new Date()) });
});

// dist/components/p-vJHeHmgm.js
var MissingParentError = class extends Error {
  constructor(elementName, parentName) {
    super(`The "${elementName}" element must be the child of an "${parentName}" element.`);
  }
};
var itemContextEventName = "atomic/resolveResult";
function itemContext(element, parentName) {
  return new Promise((resolve, reject) => {
    const event = buildCustomEvent(itemContextEventName, (item) => {
      return resolve(item);
    });
    element.dispatchEvent(event);
    if (!closest(element, parentName)) {
      reject(new MissingParentError(element.nodeName.toLowerCase(), parentName));
    }
  });
}
function resultContext(element) {
  return itemContext(element, "atomic-result");
}

// dist/components/contenttype-badge.js
var ContentTypeBadge = /* @__PURE__ */ proxyCustomElement(class ContentTypeBadge2 extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
    this.field = "commoncontenttype";
  }
  // Fetch the result context using the `connectedCallback` lifecycle method
  async connectedCallback() {
    try {
      this.result = await resultContext(this.host);
    } catch (error) {
      console.error(error);
      this.host.remove();
    }
  }
  render() {
    if (!this.result?.raw[this.field]) {
      return;
    }
    const values = Array.isArray(this.result.raw[this.field]) ? this.result.raw[this.field] : [this.result.raw[this.field]];
    const filteredValues = this.field === "commoncontenttype" ? values.filter((value) => value !== "Everything") : values;
    if (filteredValues.length === 0) {
      return;
    }
    return h("div", { class: "badge-container" }, filteredValues.map((value) => h("span", { class: "badge" }, value)));
  }
  get host() {
    return this;
  }
  static get style() {
    return ".badge-container {\n      display: flex;\n      gap: 8px;\n      flex-wrap: wrap;\n    }\n    \n    .badge {\n      display: inline-flex;\n      align-items: center;\n      justify-content: center;\n      background-color: var(--atomic-background);\n      color: #717171;\n      border: 1px solid var(--atomic-neutral);\n      border-radius: 4px;\n      padding: 4px 8px;\n      font-size: 12px;\n    }\n    @media (max-width: 990px) {\n      .badge {\n        font-size: 10px;       \n      }";
  }
}, [257, "contenttype-badge", {
  "field": [1],
  "result": [32]
}]);
var ContenttypeBadge = ContentTypeBadge;

// dist/components/directions-link.js
var DirectionsLink$1 = /* @__PURE__ */ proxyCustomElement(class DirectionsLink extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
    this.baseUrl = "https://maps.sydney.edu.au/?to=";
  }
  // Fetch the result context using the `connectedCallback` lifecycle method
  async connectedCallback() {
    try {
      this.result = await resultContext(this.host);
    } catch (error) {
      console.error(error);
      this.host.remove();
    }
  }
  render() {
    if (!this.result || !this.codeField) {
      return;
    }
    const locationCode = this.result.raw[this.codeField];
    if (!locationCode) {
      return;
    }
    const directionsUrl = `${this.baseUrl}${locationCode}&from=my-addr`;
    return h("a", { href: directionsUrl, class: "directions-link", target: "_blank", rel: "noopener noreferrer", role: "button" }, h("img", { src: "/etc.clientlibs/corporate-commons/clientlibs/corporate-search/resources/icons/icon-location.svg", alt: "Directions", width: "16", height: "16" }), "Directions");
  }
  get host() {
    return this;
  }
  static get style() {
    return ".directions-link {\n      font-size: var(--atomic-text-sm);\n      line-height: 1;\n      color: var(--atomic-primary);\n      text-decoration: none;\n      display: inline-flex;\n      align-items: center;\n      gap: 8px;\n      padding: 8px 12px;\n      border-radius: 4px;\n      cursor: pointer;\n      transition: background-color 0.2s ease;\n      width: fit-content;\n    }\n    \n    .directions-link:hover {\n      background-color: #FDEDEA;\n      transition: background-color 0.2s ease;\n    }";
  }
}, [257, "directions-link", {
  "codeField": [1, "code-field"],
  "result": [32]
}]);
var DirectionsLink2 = DirectionsLink$1;

// dist/components/facet-buttons-controller.js
var FacetButtonsController$1 = /* @__PURE__ */ proxyCustomElement(class FacetButtonsController extends H {
  constructor() {
    super();
    this.__registerHost();
  }
  componentDidLoad() {
    this.initializeObserver();
  }
  disconnectedCallback() {
    if (this.facetObserver) {
      this.facetObserver.disconnect();
    }
    if (this.searchInterfaceObserver) {
      this.searchInterfaceObserver.disconnect();
    }
  }
  initializeObserver() {
    const searchInterface = document.querySelector('atomic-search-interface[search-hub="corporate-search"]');
    if (searchInterface) {
      this.setupFacetObserver(searchInterface);
    } else {
      this.searchInterfaceObserver = new MutationObserver(() => {
        const searchInterface2 = document.querySelector('atomic-search-interface[search-hub="corporate-search"]');
        if (searchInterface2) {
          this.searchInterfaceObserver?.disconnect();
          this.setupFacetObserver(searchInterface2);
        }
      });
      this.searchInterfaceObserver.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }
  setupFacetObserver(searchInterface) {
    const manageFacetButtons = () => {
      const facets = searchInterface.querySelectorAll("atomic-facet");
      facets.forEach((facet) => {
        if (facet.shadowRoot) {
          const showMoreBtn = facet.shadowRoot.querySelector('[part="show-more"]');
          const showLessBtn = facet.shadowRoot.querySelector('[part="show-less"]');
          if (showMoreBtn && showLessBtn) {
            const isShowMoreHidden = showMoreBtn.classList.contains("hidden");
            if (isShowMoreHidden) {
              showLessBtn.style.display = "";
            } else {
              showLessBtn.style.display = "none";
            }
            if (!showMoreBtn.hasAttribute("data-listener-added")) {
              showMoreBtn.setAttribute("data-listener-added", "true");
              showMoreBtn.addEventListener("click", () => {
                [100, 200, 300, 500].forEach((delay) => {
                  setTimeout(manageFacetButtons, delay);
                });
              });
            }
            if (!showLessBtn.hasAttribute("data-listener-added")) {
              showLessBtn.setAttribute("data-listener-added", "true");
              showLessBtn.addEventListener("click", () => {
                [100, 200, 300, 500].forEach((delay) => {
                  setTimeout(manageFacetButtons, delay);
                });
              });
            }
          } else if (showLessBtn && !showMoreBtn) {
            showLessBtn.style.display = "";
            if (!showLessBtn.hasAttribute("data-listener-added")) {
              showLessBtn.setAttribute("data-listener-added", "true");
              showLessBtn.addEventListener("click", () => {
                [100, 200, 300, 500].forEach((delay) => {
                  setTimeout(manageFacetButtons, delay);
                });
              });
            }
          }
        }
      });
    };
    manageFacetButtons();
    this.facetObserver = new MutationObserver(() => {
      manageFacetButtons();
    });
    this.facetObserver.observe(searchInterface, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["hidden"]
    });
  }
  render() {
    return null;
  }
  get el() {
    return this;
  }
}, [256, "facet-buttons-controller"]);
var FacetButtonsController2 = FacetButtonsController$1;

// dist/components/qualifications-link.js
var QualificationsLink$1 = /* @__PURE__ */ proxyCustomElement(class QualificationsLink extends H {
  constructor() {
    super();
    this.__registerHost();
    this.modalWasActuallyShown = false;
  }
  connectedCallback() {
    if (!this.host.querySelector('[data-m-el="m-js-qualification-dropdown"]')) {
      const dropdownDiv = document.createElement("div");
      dropdownDiv.setAttribute("data-m-el", "m-js-qualification-dropdown");
      this.host.appendChild(dropdownDiv);
    }
    if (!this.host.hasAttribute("data-injected-into-modal")) {
      this.setupModalObserver();
    }
  }
  disconnectedCallback() {
    if (this.modalObserver) {
      this.modalObserver.disconnect();
    }
  }
  setupModalObserver() {
    this.modalObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === "childList") {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node;
              if (element.closest && element.closest("atomic-refine-modal")) {
                setTimeout(() => {
                  this.injectIntoModal();
                }, 100);
              }
            }
          });
          mutation.removedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node;
              if (element.tagName === "ATOMIC-REFINE-MODAL") {
                this.modalWasActuallyShown = false;
                setTimeout(() => {
                  this.restoreDropdownToOriginalLocation();
                }, 100);
              }
            }
          });
        }
        if (mutation.type === "attributes" && mutation.target.nodeType === Node.ELEMENT_NODE) {
          const element = mutation.target;
          if (element.tagName === "ATOMIC-REFINE-MODAL") {
            const isOpen = element.hasAttribute("open");
            const ariaHidden = element.getAttribute("aria-hidden");
            if (!isOpen && ariaHidden === "true" && this.modalWasActuallyShown) {
              this.modalWasActuallyShown = false;
              setTimeout(() => {
                this.restoreDropdownToOriginalLocation();
              }, 100);
            }
          }
        }
      });
    });
    this.modalObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["open", "aria-hidden", "class"]
    });
  }
  injectIntoModal() {
    const modal = document.querySelector("ATOMIC-REFINE-MODAL");
    if (!modal)
      return;
    const existingDropdown = document.querySelector('[data-m-el="m-js-qualification-dropdown"][data-mounted-on-state="success"]');
    if (!existingDropdown) {
      return;
    }
    const facetsContainer = this.findFacetsContainer(modal);
    if (!facetsContainer) {
      return;
    }
    if (facetsContainer.contains(existingDropdown)) {
      return;
    }
    this.originalParent = existingDropdown.parentElement || void 0;
    this.originalNextSibling = existingDropdown.nextElementSibling;
    const accordionToAppend = `<div class="accordion" id="qual-facet">
        <div class="accordion-section">
          <div class="accordion-header" onclick="toggleAccordion(this)">
            <span>Qualifications</span>
              <span class="accordion-icon minus-icon" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g clip-path="url(#clip0_5096_6706)">
                  <path d="M0.75 12H23.25" stroke="#141414" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
                </g>
                <defs>
                  <clipPath id="clip0_5096_6706">
                    <rect width="24" height="24" fill="white"></rect>
                  </clipPath>
                </defs>
              </svg>
            </span>
            <span class="accordion-icon plus-icon" aria-hidden="true">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g clip-path="url(#clip0_5096_6706)">
                  <path d="M0.75 12H23.25" stroke="#141414" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
                  <path d="M12 0.75V23.25" stroke="#141414" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path>
                </g>
                <defs>
                  <clipPath id="clip0_5096_6706">
                    <rect width="24" height="24" fill="white"></rect>
                  </clipPath>
                </defs>
              </svg>
            </span>
          </div>
          <div class="accordion-content">
          </div>
        </div>
      </div>`;
    facetsContainer.insertAdjacentHTML("beforeend", accordionToAppend);
    const accordionContent = document.querySelector("#qual-facet .accordion-content");
    if (accordionContent) {
      accordionContent.appendChild(existingDropdown);
    }
    this.modalWasActuallyShown = true;
  }
  restoreDropdownToOriginalLocation() {
    const existingDropdown = document.querySelector('[data-m-el="m-js-qualification-dropdown"][data-mounted-on-state="success"]');
    if (!existingDropdown || !this.originalParent) {
      return;
    }
    const isInModal = existingDropdown.closest("atomic-refine-modal");
    if (!isInModal) {
      return;
    }
    if (this.originalNextSibling && this.originalNextSibling.parentElement === this.originalParent) {
      this.originalParent.insertBefore(existingDropdown, this.originalNextSibling);
    } else {
      this.originalParent.appendChild(existingDropdown);
    }
    this.originalParent = void 0;
    this.originalNextSibling = void 0;
  }
  findFacetsContainer(modal) {
    let facetsContainer = modal.shadowRoot?.querySelector('div[slot="facets"]');
    if (!facetsContainer) {
      facetsContainer = modal.querySelector('div[slot="facets"]');
    }
    if (!facetsContainer) {
      const atomicModal = modal.shadowRoot?.querySelector("atomic-modal") || modal.querySelector("atomic-modal");
      if (atomicModal) {
        facetsContainer = atomicModal.shadowRoot?.querySelector('div[slot="facets"]') || atomicModal.querySelector('div[slot="facets"]');
      }
    }
    return facetsContainer || null;
  }
  render() {
    const existingElement = this.host.querySelector('[data-m-el="m-js-qualification-dropdown"]');
    if (existingElement) {
      return null;
    }
    return h("div", { "data-m-el": "m-js-qualification-dropdown" });
  }
  get host() {
    return this;
  }
  static get style() {
    return "atomic-refine-modal .m-entry-score-guide__title .m-tool-tip {\n      top: 3px;\n    }";
  }
}, [256, "qualifications-link"]);
var QualificationsLink2 = QualificationsLink$1;

// dist/components/result-field-link.js
var ResultFieldLink$1 = /* @__PURE__ */ proxyCustomElement(class ResultFieldLink extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
  }
  // Fetch the result context using the `connectedCallback` lifecycle method
  async connectedCallback() {
    try {
      this.result = await resultContext(this.host);
    } catch (error) {
      console.error(error);
      this.host.remove();
    }
  }
  render() {
    if (!this.result?.clickUri) {
      return;
    }
    const fieldName = this.field;
    const fieldHTML = this.result.raw[fieldName];
    if (!fieldHTML) {
      return;
    }
    const fieldHref = fieldHTML.indexOf("@") != -1 ? "mailto:" + fieldHTML : fieldHTML;
    return h("a", { href: fieldHref, target: "_blank", part: "link" }, fieldHTML);
  }
  get host() {
    return this;
  }
  static get style() {
    return "a {\n      color: var(--atomic-link-color);\n    }";
  }
}, [257, "result-field-link", {
  "field": [1],
  "result": [32]
}]);
var ResultFieldLink2 = ResultFieldLink$1;

// dist/components/result-url.js
var ResultUrl$1 = /* @__PURE__ */ proxyCustomElement(class ResultUrl extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
  }
  // Fetch the result context using the `connectedCallback` lifecycle method
  async connectedCallback() {
    try {
      this.result = await resultContext(this.host);
    } catch (error) {
      console.error(error);
      this.host.remove();
    }
  }
  // Format the URL by removing the https:// and www. prefixes
  formatUrl(url) {
    let formattedUrl = url.replace(/^https?:\/\//i, "");
    formattedUrl = formattedUrl.replace(/^www\./i, "");
    return formattedUrl;
  }
  render() {
    if (!this.result?.clickUri) {
      return;
    }
    const formattedUrl = this.formatUrl(this.result.clickUri);
    return h("span", { class: "formatted-url" }, formattedUrl);
  }
  get host() {
    return this;
  }
  static get style() {
    return ".formatted-url {\n      font-size: var(--atomic-text-sm);\n      line-height: 1;\n      color: var(--atomic-primary);\n      text-decoration: none;\n      word-break: break-all;\n    }";
  }
}, [257, "result-url", {
  "result": [32]
}]);
var ResultUrl2 = ResultUrl$1;

// dist/components/unisyd-map.js
var UnisydMap$1 = /* @__PURE__ */ proxyCustomElement(class UnisydMap extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
  }
  // Fetch the result context using the `connectedCallback` lifecycle method
  async connectedCallback() {
    try {
      this.result = await resultContext(this.host);
    } catch (error) {
      console.error(error);
      this.host.remove();
    }
  }
  getMapHtml(lat, lng, campus) {
    return `<!DOCTYPE html>
<head>
    <meta name="viewport" id="vp" content="initial-scale=1.0,user-scalable=no,maximum-scale=1,width=device-width" />
    <meta charset="utf-8" />
    <link rel="stylesheet" href="https://api.mazemap.com/js/v2.2.1/mazemap.min.css">
    <script type='text/javascript' src='https://api.mazemap.com/js/v2.2.1/mazemap.min.js'><\/script>
    <style>
        body { margin:0px; padding:0px; width: 100%; height:100%; }
    </style>
</head>
<body>
    <div id="map" class="mazemap"></div>
    <script>
        var map = new Mazemap.Map({
            container: 'map',
            campuses: '${campus}',
            center: {lng: ${lng}, lat: ${lat}},
            zoom: 16,
            zLevel: 3
        });

        var lngLat = map.getCenter();

        var marker = new Mazemap.MazeMarker({
            color: "MazeBlue",
            size: 36,
        }).setLngLat(lngLat).addTo(map);

        map.addControl(new Mazemap.mapboxgl.NavigationControl());
    <\/script>
</body>`;
  }
  render() {
    if (!this.result?.raw["usyd_latitude"] || !this.result?.raw["usyd_longitude"] || !this.result?.raw["usyd_campus_code"]) {
      return;
    }
    const iframeLat = String(this.result?.raw["usyd_latitude"]);
    const iframeLng = String(this.result?.raw["usyd_longitude"]);
    const iframeCampus = String(this.result?.raw["usyd_campus_code"]);
    const htmlContent = this.getMapHtml(iframeLat, iframeLng, iframeCampus);
    const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`;
    return h("iframe", { width: "440", height: "270", src: dataUrl, title: "Campus Map" });
  }
  get host() {
    return this;
  }
  static get style() {
    return "iframe {\n      border: 0;\n      max-width: 440px;\n      width: 100%;\n      height: auto;\n      aspect-ratio: 440 / 270;\n    }";
  }
}, [257, "unisyd-map", {
  "result": [32]
}]);
var UnisydMap2 = UnisydMap$1;

// dist/components/p-CEjCN7mV.js
function buildSchemaValidationError2(errors, context) {
  const message = `
  The following properties are invalid:

    ${errors.join("\n	")}

  ${context}
  `;
  return new SchemaValidationError2(message);
}
var SchemaValidationError2 = class extends Error {
  constructor(message) {
    super(message);
    this.name = "SchemaValidationError";
  }
};
var Schema2 = class {
  constructor(definition) {
    this.definition = definition;
  }
  validate(values = {}, message = "") {
    const mergedValues = {
      ...this.default,
      ...values
    };
    const errors = [];
    for (const property in this.definition) {
      const error = this.definition[property].validate(mergedValues[property]);
      error && errors.push(`${property}: ${error}`);
    }
    if (errors.length) {
      throw buildSchemaValidationError2(errors, message);
    }
    return mergedValues;
  }
  get default() {
    const defaultValues = {};
    for (const property in this.definition) {
      const defaultValue = this.definition[property].default;
      if (defaultValue !== void 0) {
        defaultValues[property] = defaultValue;
      }
    }
    return defaultValues;
  }
};
var Value2 = class {
  constructor(baseConfig = {}) {
    this.baseConfig = baseConfig;
  }
  validate(value) {
    if (this.baseConfig.required && isNullOrUndefined2(value)) {
      return "value is required.";
    }
    return null;
  }
  get default() {
    return this.baseConfig.default instanceof Function ? this.baseConfig.default() : this.baseConfig.default;
  }
  get required() {
    return this.baseConfig.required === true;
  }
};
function isUndefined2(value) {
  return value === void 0;
}
function isNull2(value) {
  return value === null;
}
function isNullOrUndefined2(value) {
  return isUndefined2(value) || isNull2(value);
}
var NumberValue2 = class {
  constructor(config = {}) {
    __publicField(this, "value");
    this.config = config;
    this.value = new Value2(config);
  }
  validate(value) {
    const valueValidation = this.value.validate(value);
    if (valueValidation) {
      return valueValidation;
    }
    if (!isNumberOrUndefined2(value)) {
      return "value is not a number.";
    }
    if (value < this.config.min) {
      return `minimum value of ${this.config.min} not respected.`;
    }
    if (value > this.config.max) {
      return `maximum value of ${this.config.max} not respected.`;
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
function isNumberOrUndefined2(value) {
  return isUndefined2(value) || isNumber2(value);
}
function isNumber2(value) {
  return typeof value === "number" && !isNaN(value);
}
var BooleanValue2 = class {
  constructor(config = {}) {
    __publicField(this, "value");
    this.value = new Value2(config);
  }
  validate(value) {
    const valueValidation = this.value.validate(value);
    if (valueValidation) {
      return valueValidation;
    }
    if (!isBooleanOrUndefined2(value)) {
      return "value is not a boolean.";
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
function isBooleanOrUndefined2(value) {
  return isUndefined2(value) || isBoolean2(value);
}
function isBoolean2(value) {
  return typeof value === "boolean";
}
var ISODateStringRegex2 = /^\d{4}(-\d\d(-\d\d(T\d\d:\d\d(:\d\d)?(\.\d+)?(([+-]\d\d:\d\d)|Z)?)?)?)?$/i;
var StringValue2 = class {
  constructor(config = {}) {
    __publicField(this, "value");
    __publicField(this, "config");
    this.config = {
      emptyAllowed: true,
      url: false,
      ...config
    };
    this.value = new Value2(this.config);
  }
  validate(value) {
    const { emptyAllowed, url, regex, constrainTo, ISODate } = this.config;
    const valueValidation = this.value.validate(value);
    if (valueValidation) {
      return valueValidation;
    }
    if (isUndefined2(value)) {
      return null;
    }
    if (!isString2(value)) {
      return "value is not a string.";
    }
    if (!emptyAllowed && !value.length) {
      return "value is an empty string.";
    }
    if (url) {
      try {
        new URL(value);
      } catch (e7) {
        return "value is not a valid URL.";
      }
    }
    if (regex && !regex.test(value)) {
      return `value did not match provided regex ${regex}`;
    }
    if (constrainTo && !constrainTo.includes(value)) {
      const values = constrainTo.join(", ");
      return `value should be one of: ${values}.`;
    }
    if (ISODate && !(ISODateStringRegex2.test(value) && new Date(value).toString() !== "Invalid Date")) {
      return "value is not a valid ISO8601 date string";
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
function isString2(value) {
  return Object.prototype.toString.call(value) === "[object String]";
}
var RecordValue2 = class {
  constructor(config = {}) {
    __publicField(this, "config");
    this.config = {
      options: { required: false },
      values: {},
      ...config
    };
  }
  validate(input) {
    if (isUndefined2(input)) {
      return this.config.options.required ? "value is required and is currently undefined" : null;
    }
    if (!isRecord2(input)) {
      return "value is not an object";
    }
    for (const [k, v] of Object.entries(this.config.values)) {
      if (v.required && isNullOrUndefined2(input[k])) {
        return `value does not contain ${k}`;
      }
    }
    let out = "";
    for (const [key, validator] of Object.entries(this.config.values)) {
      const value = input[key];
      const invalidValue = validator.validate(value);
      if (invalidValue !== null) {
        out += " " + invalidValue;
      }
    }
    return out === "" ? null : out;
  }
  get default() {
    return void 0;
  }
  get required() {
    return !!this.config.options.required;
  }
};
function isRecord2(value) {
  return value !== void 0 && typeof value === "object";
}
var ArrayValue2 = class {
  constructor(config = {}) {
    __publicField(this, "value");
    this.config = config;
    this.value = new Value2(this.config);
  }
  validate(input) {
    if (!isNullOrUndefined2(input) && !Array.isArray(input)) {
      return "value is not an array";
    }
    const invalid = this.value.validate(input);
    if (invalid !== null) {
      return invalid;
    }
    if (isNullOrUndefined2(input)) {
      return null;
    }
    if (this.config.max !== void 0 && input.length > this.config.max) {
      return `value contains more than ${this.config.max}`;
    }
    if (this.config.min !== void 0 && input.length < this.config.min) {
      return `value contains less than ${this.config.min}`;
    }
    if (this.config.each !== void 0) {
      let out = "";
      input.forEach((el3) => {
        if (this.config.each.required && isNullOrUndefined2(el3)) {
          out = `value is null or undefined: ${input.join(",")}`;
        }
        const isInvalid = this.validatePrimitiveValue(el3, this.config.each);
        if (isInvalid !== null) {
          out += " " + isInvalid;
        }
      });
      return out === "" ? null : out;
    }
    return null;
  }
  validatePrimitiveValue(v, validator) {
    if (isBoolean2(v)) {
      return validator.validate(v);
    } else if (isString2(v)) {
      return validator.validate(v);
    } else if (isNumber2(v)) {
      return validator.validate(v);
    } else if (isRecord2(v)) {
      return validator.validate(v);
    }
    return "value is not a primitive value";
  }
  get default() {
    return void 0;
  }
  get required() {
    return this.value.required;
  }
};
function isArray2(value) {
  return Array.isArray(value);
}
var EnumValue2 = class {
  constructor(config) {
    __publicField(this, "value");
    this.config = config;
    this.value = new Value2(config);
  }
  validate(value) {
    const invalid = this.value.validate(value);
    if (invalid !== null) {
      return invalid;
    }
    if (isUndefined2(value)) {
      return null;
    }
    const valueInEnum = Object.values(this.config.enum).find(
      (enumValue) => enumValue === value
    );
    if (!valueInEnum) {
      return "value is not in enum.";
    }
    return null;
  }
  get default() {
    return this.value.default;
  }
  get required() {
    return this.value.required;
  }
};
var Wb2 = Object.create;
var Ac2 = Object.defineProperty;
var Hb2 = Object.getOwnPropertyDescriptor;
var zb2 = Object.getOwnPropertyNames;
var Kb2 = Object.getPrototypeOf;
var Yb2 = Object.prototype.hasOwnProperty;
var Jb2 = (e7, t, r) => t in e7 ? Ac2(e7, t, { enumerable: true, configurable: true, writable: true, value: r }) : e7[t] = r;
var Oe2 = (e7, t) => () => (t || e7((t = { exports: {} }).exports, t), t.exports);
var Xb2 = (e7, t) => {
  for (var r in t)
    Ac2(e7, r, { get: t[r], enumerable: true });
};
var Zb = (e7, t, r, n) => {
  if (t && typeof t == "object" || typeof t == "function")
    for (let o of zb2(t))
      !Yb2.call(e7, o) && o !== r && Ac2(e7, o, { get: () => t[o], enumerable: !(n = Hb2(t, o)) || n.enumerable });
  return e7;
};
var Vt2 = (e7, t, r) => (r = e7 != null ? Wb2(Kb2(e7)) : {}, Zb(Ac2(r, "default", { value: e7, enumerable: true }), e7));
var Ce2 = (e7, t, r) => Jb2(e7, typeof t != "symbol" ? t + "" : t, r);
var sS2 = Oe2((Ki) => {
  var wc = Ki && Ki.__assign || function() {
    return wc = Object.assign || function(e7) {
      for (var t, r = 1, n = arguments.length; r < n; r++) {
        t = arguments[r];
        for (var o in t)
          Object.prototype.hasOwnProperty.call(t, o) && (e7[o] = t[o]);
      }
      return e7;
    }, wc.apply(this, arguments);
  };
  Object.defineProperty(Ki, "__esModule", { value: true });
  var dv = { delayFirstAttempt: false, jitter: "none", maxDelay: 1 / 0, numOfAttempts: 10, retry: function() {
    return true;
  }, startingDelay: 100, timeMultiple: 2 };
  function pv(e7) {
    var t = wc(wc({}, dv), e7);
    return t.numOfAttempts < 1 && (t.numOfAttempts = 1), t;
  }
  Ki.getSanitizedOptions = pv;
});
var cS2 = Oe2((Op) => {
  Object.defineProperty(Op, "__esModule", { value: true });
  function mv(e7) {
    var t = Math.random() * e7;
    return Math.round(t);
  }
  Op.fullJitter = mv;
});
var uS2 = Oe2((qp) => {
  Object.defineProperty(qp, "__esModule", { value: true });
  function fv(e7) {
    return e7;
  }
  qp.noJitter = fv;
});
var lS2 = Oe2((Dp) => {
  Object.defineProperty(Dp, "__esModule", { value: true });
  var gv = cS2(), Sv = uS2();
  function hv(e7) {
    switch (e7.jitter) {
      case "full":
        return gv.fullJitter;
      case "none":
      default:
        return Sv.noJitter;
    }
  }
  Dp.JitterFactory = hv;
});
var Np = Oe2((Vp2) => {
  Object.defineProperty(Vp2, "__esModule", { value: true });
  var yv = lS2(), Cv = function() {
    function e7(t) {
      this.options = t, this.attempt = 0;
    }
    return e7.prototype.apply = function() {
      var t = this;
      return new Promise(function(r) {
        return setTimeout(r, t.jitteredDelay);
      });
    }, e7.prototype.setAttemptNumber = function(t) {
      this.attempt = t;
    }, Object.defineProperty(e7.prototype, "jitteredDelay", { get: function() {
      var t = yv.JitterFactory(this.options);
      return t(this.delay);
    }, enumerable: true, configurable: true }), Object.defineProperty(e7.prototype, "delay", { get: function() {
      var t = this.options.startingDelay, r = this.options.timeMultiple, n = this.numOfDelayedAttempts, o = t * Math.pow(r, n);
      return Math.min(o, this.options.maxDelay);
    }, enumerable: true, configurable: true }), Object.defineProperty(e7.prototype, "numOfDelayedAttempts", { get: function() {
      return this.attempt;
    }, enumerable: true, configurable: true }), e7;
  }();
  Vp2.Delay = Cv;
});
var dS2 = Oe2((Fr) => {
  var xv = Fr && Fr.__extends || function() {
    var e7 = function(t, r) {
      return e7 = Object.setPrototypeOf || { __proto__: [] } instanceof Array && function(n, o) {
        n.__proto__ = o;
      } || function(n, o) {
        for (var a in o)
          o.hasOwnProperty(a) && (n[a] = o[a]);
      }, e7(t, r);
    };
    return function(t, r) {
      e7(t, r);
      function n() {
        this.constructor = t;
      }
      t.prototype = r === null ? Object.create(r) : (n.prototype = r.prototype, new n());
    };
  }(), Av = Fr && Fr.__awaiter || function(e7, t, r, n) {
    function o(a) {
      return a instanceof r ? a : new r(function(i) {
        i(a);
      });
    }
    return new (r || (r = Promise))(function(a, i) {
      function s(l) {
        try {
          u(n.next(l));
        } catch (m) {
          i(m);
        }
      }
      function c(l) {
        try {
          u(n.throw(l));
        } catch (m) {
          i(m);
        }
      }
      function u(l) {
        l.done ? a(l.value) : o(l.value).then(s, c);
      }
      u((n = n.apply(e7, t || [])).next());
    });
  }, Fv = Fr && Fr.__generator || function(e7, t) {
    var r = { label: 0, sent: function() {
      if (a[0] & 1)
        throw a[1];
      return a[1];
    }, trys: [], ops: [] }, n, o, a, i;
    return i = { next: s(0), throw: s(1), return: s(2) }, typeof Symbol == "function" && (i[Symbol.iterator] = function() {
      return this;
    }), i;
    function s(u) {
      return function(l) {
        return c([u, l]);
      };
    }
    function c(u) {
      if (n)
        throw new TypeError("Generator is already executing.");
      for (; r; )
        try {
          if (n = 1, o && (a = u[0] & 2 ? o.return : u[0] ? o.throw || ((a = o.return) && a.call(o), 0) : o.next) && !(a = a.call(o, u[1])).done)
            return a;
          switch (o = 0, a && (u = [u[0] & 2, a.value]), u[0]) {
            case 0:
            case 1:
              a = u;
              break;
            case 4:
              return r.label++, { value: u[1], done: false };
            case 5:
              r.label++, o = u[1], u = [0];
              continue;
            case 7:
              u = r.ops.pop(), r.trys.pop();
              continue;
            default:
              if (a = r.trys, !(a = a.length > 0 && a[a.length - 1]) && (u[0] === 6 || u[0] === 2)) {
                r = 0;
                continue;
              }
              if (u[0] === 3 && (!a || u[1] > a[0] && u[1] < a[3])) {
                r.label = u[1];
                break;
              }
              if (u[0] === 6 && r.label < a[1]) {
                r.label = a[1], a = u;
                break;
              }
              if (a && r.label < a[2]) {
                r.label = a[2], r.ops.push(u);
                break;
              }
              a[2] && r.ops.pop(), r.trys.pop();
              continue;
          }
          u = t.call(e7, r);
        } catch (l) {
          u = [6, l], o = 0;
        } finally {
          n = a = 0;
        }
      if (u[0] & 5)
        throw u[1];
      return { value: u[0] ? u[1] : void 0, done: true };
    }
  };
  Object.defineProperty(Fr, "__esModule", { value: true });
  var Rv = Np(), bv = function(e7) {
    xv(t, e7);
    function t() {
      return e7 !== null && e7.apply(this, arguments) || this;
    }
    return t.prototype.apply = function() {
      return Av(this, void 0, void 0, function() {
        return Fv(this, function(r) {
          return [2, this.isFirstAttempt ? true : e7.prototype.apply.call(this)];
        });
      });
    }, Object.defineProperty(t.prototype, "isFirstAttempt", { get: function() {
      return this.attempt === 0;
    }, enumerable: true, configurable: true }), Object.defineProperty(t.prototype, "numOfDelayedAttempts", { get: function() {
      return this.attempt - 1;
    }, enumerable: true, configurable: true }), t;
  }(Rv.Delay);
  Fr.SkipFirstDelay = bv;
});
var pS2 = Oe2((Yi) => {
  var vv = Yi && Yi.__extends || function() {
    var e7 = function(t, r) {
      return e7 = Object.setPrototypeOf || { __proto__: [] } instanceof Array && function(n, o) {
        n.__proto__ = o;
      } || function(n, o) {
        for (var a in o)
          o.hasOwnProperty(a) && (n[a] = o[a]);
      }, e7(t, r);
    };
    return function(t, r) {
      e7(t, r);
      function n() {
        this.constructor = t;
      }
      t.prototype = r === null ? Object.create(r) : (n.prototype = r.prototype, new n());
    };
  }();
  Object.defineProperty(Yi, "__esModule", { value: true });
  var Pv = Np(), wv = function(e7) {
    vv(t, e7);
    function t() {
      return e7 !== null && e7.apply(this, arguments) || this;
    }
    return t;
  }(Pv.Delay);
  Yi.AlwaysDelay = wv;
});
var mS2 = Oe2((Mp) => {
  Object.defineProperty(Mp, "__esModule", { value: true });
  var Iv = dS2(), Ev = pS2();
  function Tv(e7, t) {
    var r = kv(e7);
    return r.setAttemptNumber(t), r;
  }
  Mp.DelayFactory = Tv;
  function kv(e7) {
    return e7.delayFirstAttempt ? new Ev.AlwaysDelay(e7) : new Iv.SkipFirstDelay(e7);
  }
});
var fS = Oe2((jn) => {
  var Qp = jn && jn.__awaiter || function(e7, t, r, n) {
    function o(a) {
      return a instanceof r ? a : new r(function(i) {
        i(a);
      });
    }
    return new (r || (r = Promise))(function(a, i) {
      function s(l) {
        try {
          u(n.next(l));
        } catch (m) {
          i(m);
        }
      }
      function c(l) {
        try {
          u(n.throw(l));
        } catch (m) {
          i(m);
        }
      }
      function u(l) {
        l.done ? a(l.value) : o(l.value).then(s, c);
      }
      u((n = n.apply(e7, t || [])).next());
    });
  }, Lp2 = jn && jn.__generator || function(e7, t) {
    var r = { label: 0, sent: function() {
      if (a[0] & 1)
        throw a[1];
      return a[1];
    }, trys: [], ops: [] }, n, o, a, i;
    return i = { next: s(0), throw: s(1), return: s(2) }, typeof Symbol == "function" && (i[Symbol.iterator] = function() {
      return this;
    }), i;
    function s(u) {
      return function(l) {
        return c([u, l]);
      };
    }
    function c(u) {
      if (n)
        throw new TypeError("Generator is already executing.");
      for (; r; )
        try {
          if (n = 1, o && (a = u[0] & 2 ? o.return : u[0] ? o.throw || ((a = o.return) && a.call(o), 0) : o.next) && !(a = a.call(o, u[1])).done)
            return a;
          switch (o = 0, a && (u = [u[0] & 2, a.value]), u[0]) {
            case 0:
            case 1:
              a = u;
              break;
            case 4:
              return r.label++, { value: u[1], done: false };
            case 5:
              r.label++, o = u[1], u = [0];
              continue;
            case 7:
              u = r.ops.pop(), r.trys.pop();
              continue;
            default:
              if (a = r.trys, !(a = a.length > 0 && a[a.length - 1]) && (u[0] === 6 || u[0] === 2)) {
                r = 0;
                continue;
              }
              if (u[0] === 3 && (!a || u[1] > a[0] && u[1] < a[3])) {
                r.label = u[1];
                break;
              }
              if (u[0] === 6 && r.label < a[1]) {
                r.label = a[1], a = u;
                break;
              }
              if (a && r.label < a[2]) {
                r.label = a[2], r.ops.push(u);
                break;
              }
              a[2] && r.ops.pop(), r.trys.pop();
              continue;
          }
          u = t.call(e7, r);
        } catch (l) {
          u = [6, l], o = 0;
        } finally {
          n = a = 0;
        }
      if (u[0] & 5)
        throw u[1];
      return { value: u[0] ? u[1] : void 0, done: true };
    }
  };
  Object.defineProperty(jn, "__esModule", { value: true });
  var Ov = sS2(), qv = mS2();
  function Dv(e7, t) {
    return t === void 0 && (t = {}), Qp(this, void 0, void 0, function() {
      var r, n;
      return Lp2(this, function(o) {
        switch (o.label) {
          case 0:
            return r = Ov.getSanitizedOptions(t), n = new Vv(e7, r), [4, n.execute()];
          case 1:
            return [2, o.sent()];
        }
      });
    });
  }
  jn.backOff = Dv;
  var Vv = function() {
    function e7(t, r) {
      this.request = t, this.options = r, this.attemptNumber = 0;
    }
    return e7.prototype.execute = function() {
      return Qp(this, void 0, void 0, function() {
        var t, r;
        return Lp2(this, function(n) {
          switch (n.label) {
            case 0:
              if (this.attemptLimitReached)
                return [3, 7];
              n.label = 1;
            case 1:
              return n.trys.push([1, 4, , 6]), [4, this.applyDelay()];
            case 2:
              return n.sent(), [4, this.request()];
            case 3:
              return [2, n.sent()];
            case 4:
              return t = n.sent(), this.attemptNumber++, [4, this.options.retry(t, this.attemptNumber)];
            case 5:
              if (r = n.sent(), !r || this.attemptLimitReached)
                throw t;
              return [3, 6];
            case 6:
              return [3, 0];
            case 7:
              throw new Error("Something went wrong.");
          }
        });
      });
    }, Object.defineProperty(e7.prototype, "attemptLimitReached", { get: function() {
      return this.attemptNumber >= this.options.numOfAttempts;
    }, enumerable: true, configurable: true }), e7.prototype.applyDelay = function() {
      return Qp(this, void 0, void 0, function() {
        var t;
        return Lp2(this, function(r) {
          switch (r.label) {
            case 0:
              return t = qv.DelayFactory(this.options, this.attemptNumber), [4, t.apply()];
            case 1:
              return r.sent(), [2];
          }
        });
      });
    }, e7;
  }();
});
var Su2 = Oe2((_m, jm) => {
  (function(e7, t) {
    typeof _m == "object" && typeof jm < "u" ? jm.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs = t();
  })(_m, function() {
    var e7 = 1e3, t = 6e4, r = 36e5, n = "millisecond", o = "second", a = "minute", i = "hour", s = "day", c = "week", u = "month", l = "quarter", m = "year", p = "date", d = "Invalid Date", f = /^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/, A = /\[([^\]]+)]|Y{1,4}|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g, S = { name: "en", weekdays: "Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_"), months: "January_February_March_April_May_June_July_August_September_October_November_December".split("_"), ordinal: function(D) {
      var O = ["th", "st", "nd", "rd"], k = D % 100;
      return "[" + D + (O[(k - 20) % 10] || O[k] || O[0]) + "]";
    } }, g = function(D, O, k) {
      var Q = String(D);
      return !Q || Q.length >= O ? D : "" + Array(O + 1 - Q.length).join(k) + D;
    }, C = { s: g, z: function(D) {
      var O = -D.utcOffset(), k = Math.abs(O), Q = Math.floor(k / 60), q = k % 60;
      return (O <= 0 ? "+" : "-") + g(Q, 2, "0") + ":" + g(q, 2, "0");
    }, m: function D(O, k) {
      if (O.date() < k.date())
        return -D(k, O);
      var Q = 12 * (k.year() - O.year()) + (k.month() - O.month()), q = O.clone().add(Q, u), U = k - q < 0, _ = O.clone().add(Q + (U ? -1 : 1), u);
      return +(-(Q + (k - q) / (U ? q - _ : _ - q)) || 0);
    }, a: function(D) {
      return D < 0 ? Math.ceil(D) || 0 : Math.floor(D);
    }, p: function(D) {
      return { M: u, y: m, w: c, d: s, D: p, h: i, m: a, s: o, ms: n, Q: l }[D] || String(D || "").toLowerCase().replace(/s$/, "");
    }, u: function(D) {
      return D === void 0;
    } }, y = "en", F2 = {};
    F2[y] = S;
    var I = "$isDayjsObject", v = function(D) {
      return D instanceof T || !(!D || !D[I]);
    }, R = function D(O, k, Q) {
      var q;
      if (!O)
        return y;
      if (typeof O == "string") {
        var U = O.toLowerCase();
        F2[U] && (q = U), k && (F2[U] = k, q = U);
        var _ = O.split("-");
        if (!q && _.length > 1)
          return D(_[0]);
      } else {
        var H2 = O.name;
        F2[H2] = O, q = H2;
      }
      return !Q && q && (y = q), q || !Q && y;
    }, b = function(D, O) {
      if (v(D))
        return D.clone();
      var k = typeof O == "object" ? O : {};
      return k.date = D, k.args = arguments, new T(k);
    }, P = C;
    P.l = R, P.i = v, P.w = function(D, O) {
      return b(D, { locale: O.$L, utc: O.$u, x: O.$x, $offset: O.$offset });
    };
    var T = function() {
      function D(k) {
        this.$L = R(k.locale, null, true), this.parse(k), this.$x = this.$x || k.x || {}, this[I] = true;
      }
      var O = D.prototype;
      return O.parse = function(k) {
        this.$d = function(Q) {
          var q = Q.date, U = Q.utc;
          if (q === null)
            return /* @__PURE__ */ new Date(NaN);
          if (P.u(q))
            return /* @__PURE__ */ new Date();
          if (q instanceof Date)
            return new Date(q);
          if (typeof q == "string" && !/Z$/i.test(q)) {
            var _ = q.match(f);
            if (_) {
              var H2 = _[2] - 1 || 0, ee = (_[7] || "0").substring(0, 3);
              return U ? new Date(Date.UTC(_[1], H2, _[3] || 1, _[4] || 0, _[5] || 0, _[6] || 0, ee)) : new Date(_[1], H2, _[3] || 1, _[4] || 0, _[5] || 0, _[6] || 0, ee);
            }
          }
          return new Date(q);
        }(k), this.init();
      }, O.init = function() {
        var k = this.$d;
        this.$y = k.getFullYear(), this.$M = k.getMonth(), this.$D = k.getDate(), this.$W = k.getDay(), this.$H = k.getHours(), this.$m = k.getMinutes(), this.$s = k.getSeconds(), this.$ms = k.getMilliseconds();
      }, O.$utils = function() {
        return P;
      }, O.isValid = function() {
        return this.$d.toString() !== d;
      }, O.isSame = function(k, Q) {
        var q = b(k);
        return this.startOf(Q) <= q && q <= this.endOf(Q);
      }, O.isAfter = function(k, Q) {
        return b(k) < this.startOf(Q);
      }, O.isBefore = function(k, Q) {
        return this.endOf(Q) < b(k);
      }, O.$g = function(k, Q, q) {
        return P.u(k) ? this[Q] : this.set(q, k);
      }, O.unix = function() {
        return Math.floor(this.valueOf() / 1e3);
      }, O.valueOf = function() {
        return this.$d.getTime();
      }, O.startOf = function(k, Q) {
        var q = this, U = !!P.u(Q) || Q, _ = P.p(k), H2 = function(ie2, fe) {
          var ye = P.w(q.$u ? Date.UTC(q.$y, fe, ie2) : new Date(q.$y, fe, ie2), q);
          return U ? ye : ye.endOf(s);
        }, ee = function(ie2, fe) {
          return P.w(q.toDate()[ie2].apply(q.toDate("s"), (U ? [0, 0, 0, 0] : [23, 59, 59, 999]).slice(fe)), q);
        }, oe = this.$W, X = this.$M, te = this.$D, J = "set" + (this.$u ? "UTC" : "");
        switch (_) {
          case m:
            return U ? H2(1, 0) : H2(31, 11);
          case u:
            return U ? H2(1, X) : H2(0, X + 1);
          case c:
            var re = this.$locale().weekStart || 0, ge = (oe < re ? oe + 7 : oe) - re;
            return H2(U ? te - ge : te + (6 - ge), X);
          case s:
          case p:
            return ee(J + "Hours", 0);
          case i:
            return ee(J + "Minutes", 1);
          case a:
            return ee(J + "Seconds", 2);
          case o:
            return ee(J + "Milliseconds", 3);
          default:
            return this.clone();
        }
      }, O.endOf = function(k) {
        return this.startOf(k, false);
      }, O.$set = function(k, Q) {
        var q, U = P.p(k), _ = "set" + (this.$u ? "UTC" : ""), H2 = (q = {}, q[s] = _ + "Date", q[p] = _ + "Date", q[u] = _ + "Month", q[m] = _ + "FullYear", q[i] = _ + "Hours", q[a] = _ + "Minutes", q[o] = _ + "Seconds", q[n] = _ + "Milliseconds", q)[U], ee = U === s ? this.$D + (Q - this.$W) : Q;
        if (U === u || U === m) {
          var oe = this.clone().set(p, 1);
          oe.$d[H2](ee), oe.init(), this.$d = oe.set(p, Math.min(this.$D, oe.daysInMonth())).$d;
        } else
          H2 && this.$d[H2](ee);
        return this.init(), this;
      }, O.set = function(k, Q) {
        return this.clone().$set(k, Q);
      }, O.get = function(k) {
        return this[P.p(k)]();
      }, O.add = function(k, Q) {
        var q, U = this;
        k = Number(k);
        var _ = P.p(Q), H2 = function(X) {
          var te = b(U);
          return P.w(te.date(te.date() + Math.round(X * k)), U);
        };
        if (_ === u)
          return this.set(u, this.$M + k);
        if (_ === m)
          return this.set(m, this.$y + k);
        if (_ === s)
          return H2(1);
        if (_ === c)
          return H2(7);
        var ee = (q = {}, q[a] = t, q[i] = r, q[o] = e7, q)[_] || 1, oe = this.$d.getTime() + k * ee;
        return P.w(oe, this);
      }, O.subtract = function(k, Q) {
        return this.add(-1 * k, Q);
      }, O.format = function(k) {
        var Q = this, q = this.$locale();
        if (!this.isValid())
          return q.invalidDate || d;
        var U = k || "YYYY-MM-DDTHH:mm:ssZ", _ = P.z(this), H2 = this.$H, ee = this.$m, oe = this.$M, X = q.weekdays, te = q.months, J = q.meridiem, re = function(fe, ye, Ge, it) {
          return fe && (fe[ye] || fe(Q, U)) || Ge[ye].slice(0, it);
        }, ge = function(fe) {
          return P.s(H2 % 12 || 12, fe, "0");
        }, ie2 = J || function(fe, ye, Ge) {
          var it = fe < 12 ? "AM" : "PM";
          return Ge ? it.toLowerCase() : it;
        };
        return U.replace(A, function(fe, ye) {
          return ye || function(Ge) {
            switch (Ge) {
              case "YY":
                return String(Q.$y).slice(-2);
              case "YYYY":
                return P.s(Q.$y, 4, "0");
              case "M":
                return oe + 1;
              case "MM":
                return P.s(oe + 1, 2, "0");
              case "MMM":
                return re(q.monthsShort, oe, te, 3);
              case "MMMM":
                return re(te, oe);
              case "D":
                return Q.$D;
              case "DD":
                return P.s(Q.$D, 2, "0");
              case "d":
                return String(Q.$W);
              case "dd":
                return re(q.weekdaysMin, Q.$W, X, 2);
              case "ddd":
                return re(q.weekdaysShort, Q.$W, X, 3);
              case "dddd":
                return X[Q.$W];
              case "H":
                return String(H2);
              case "HH":
                return P.s(H2, 2, "0");
              case "h":
                return ge(1);
              case "hh":
                return ge(2);
              case "a":
                return ie2(H2, ee, true);
              case "A":
                return ie2(H2, ee, false);
              case "m":
                return String(ee);
              case "mm":
                return P.s(ee, 2, "0");
              case "s":
                return String(Q.$s);
              case "ss":
                return P.s(Q.$s, 2, "0");
              case "SSS":
                return P.s(Q.$ms, 3, "0");
              case "Z":
                return _;
            }
            return null;
          }(fe) || _.replace(":", "");
        });
      }, O.utcOffset = function() {
        return 15 * -Math.round(this.$d.getTimezoneOffset() / 15);
      }, O.diff = function(k, Q, q) {
        var U, _ = this, H2 = P.p(Q), ee = b(k), oe = (ee.utcOffset() - this.utcOffset()) * t, X = this - ee, te = function() {
          return P.m(_, ee);
        };
        switch (H2) {
          case m:
            U = te() / 12;
            break;
          case u:
            U = te();
            break;
          case l:
            U = te() / 3;
            break;
          case c:
            U = (X - oe) / 6048e5;
            break;
          case s:
            U = (X - oe) / 864e5;
            break;
          case i:
            U = X / r;
            break;
          case a:
            U = X / t;
            break;
          case o:
            U = X / e7;
            break;
          default:
            U = X;
        }
        return q ? U : P.a(U);
      }, O.daysInMonth = function() {
        return this.endOf(u).$D;
      }, O.$locale = function() {
        return F2[this.$L];
      }, O.locale = function(k, Q) {
        if (!k)
          return this.$L;
        var q = this.clone(), U = R(k, Q, true);
        return U && (q.$L = U), q;
      }, O.clone = function() {
        return P.w(this.$d, this);
      }, O.toDate = function() {
        return new Date(this.valueOf());
      }, O.toJSON = function() {
        return this.isValid() ? this.toISOString() : null;
      }, O.toISOString = function() {
        return this.$d.toISOString();
      }, O.toString = function() {
        return this.$d.toUTCString();
      }, D;
    }(), B = T.prototype;
    return b.prototype = B, [["$ms", n], ["$s", o], ["$m", a], ["$H", i], ["$W", s], ["$M", u], ["$y", m], ["$D", p]].forEach(function(D) {
      B[D[1]] = function(O) {
        return this.$g(O, D[0], D[1]);
      };
    }), b.extend = function(D, O) {
      return D.$i || (D(O, T, b), D.$i = true), b;
    }, b.locale = R, b.isDayjs = v, b.unix = function(D) {
      return b(1e3 * D);
    }, b.en = F2[y], b.Ls = F2, b.p = {}, b;
  });
});
var Fy2 = Oe2(($m, Gm) => {
  (function(e7, t) {
    typeof $m == "object" && typeof Gm < "u" ? Gm.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_quarterOfYear = t();
  })($m, function() {
    var e7 = "month", t = "quarter";
    return function(r, n) {
      var o = n.prototype;
      o.quarter = function(s) {
        return this.$utils().u(s) ? Math.ceil((this.month() + 1) / 3) : this.month(this.month() % 3 + 3 * (s - 1));
      };
      var a = o.add;
      o.add = function(s, c) {
        return s = Number(s), this.$utils().p(c) === t ? this.add(3 * s, e7) : a.bind(this)(s, c);
      };
      var i = o.startOf;
      o.startOf = function(s, c) {
        var u = this.$utils(), l = !!u.u(c) || c;
        if (u.p(s) === t) {
          var m = this.quarter() - 1;
          return l ? this.month(3 * m).startOf(e7).startOf("day") : this.month(3 * m + 2).endOf(e7).endOf("day");
        }
        return i.bind(this)(s, c);
      };
    };
  });
});
var Ry2 = Oe2((Wm, Hm2) => {
  (function(e7, t) {
    typeof Wm == "object" && typeof Hm2 < "u" ? Hm2.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_customParseFormat = t();
  })(Wm, function() {
    var e7 = { LTS: "h:mm:ss A", LT: "h:mm A", L: "MM/DD/YYYY", LL: "MMMM D, YYYY", LLL: "MMMM D, YYYY h:mm A", LLLL: "dddd, MMMM D, YYYY h:mm A" }, t = /(\[[^[]*\])|([-_:/.,()\s]+)|(A|a|Q|YYYY|YY?|ww?|MM?M?M?|Do|DD?|hh?|HH?|mm?|ss?|S{1,3}|z|ZZ?)/g, r = /\d/, n = /\d\d/, o = /\d\d?/, a = /\d*[^-_:/,()\s\d]+/, i = {}, s = function(f) {
      return (f = +f) + (f > 68 ? 1900 : 2e3);
    }, c = function(f) {
      return function(A) {
        this[f] = +A;
      };
    }, u = [/[+-]\d\d:?(\d\d)?|Z/, function(f) {
      (this.zone || (this.zone = {})).offset = function(A) {
        if (!A || A === "Z")
          return 0;
        var S = A.match(/([+-]|\d\d)/g), g = 60 * S[1] + (+S[2] || 0);
        return g === 0 ? 0 : S[0] === "+" ? -g : g;
      }(f);
    }], l = function(f) {
      var A = i[f];
      return A && (A.indexOf ? A : A.s.concat(A.f));
    }, m = function(f, A) {
      var S, g = i.meridiem;
      if (g) {
        for (var C = 1; C <= 24; C += 1)
          if (f.indexOf(g(C, 0, A)) > -1) {
            S = C > 12;
            break;
          }
      } else
        S = f === (A ? "pm" : "PM");
      return S;
    }, p = { A: [a, function(f) {
      this.afternoon = m(f, false);
    }], a: [a, function(f) {
      this.afternoon = m(f, true);
    }], Q: [r, function(f) {
      this.month = 3 * (f - 1) + 1;
    }], S: [r, function(f) {
      this.milliseconds = 100 * +f;
    }], SS: [n, function(f) {
      this.milliseconds = 10 * +f;
    }], SSS: [/\d{3}/, function(f) {
      this.milliseconds = +f;
    }], s: [o, c("seconds")], ss: [o, c("seconds")], m: [o, c("minutes")], mm: [o, c("minutes")], H: [o, c("hours")], h: [o, c("hours")], HH: [o, c("hours")], hh: [o, c("hours")], D: [o, c("day")], DD: [n, c("day")], Do: [a, function(f) {
      var A = i.ordinal, S = f.match(/\d+/);
      if (this.day = S[0], A)
        for (var g = 1; g <= 31; g += 1)
          A(g).replace(/\[|\]/g, "") === f && (this.day = g);
    }], w: [o, c("week")], ww: [n, c("week")], M: [o, c("month")], MM: [n, c("month")], MMM: [a, function(f) {
      var A = l("months"), S = (l("monthsShort") || A.map(function(g) {
        return g.slice(0, 3);
      })).indexOf(f) + 1;
      if (S < 1)
        throw new Error();
      this.month = S % 12 || S;
    }], MMMM: [a, function(f) {
      var A = l("months").indexOf(f) + 1;
      if (A < 1)
        throw new Error();
      this.month = A % 12 || A;
    }], Y: [/[+-]?\d+/, c("year")], YY: [n, function(f) {
      this.year = s(f);
    }], YYYY: [/\d{4}/, c("year")], Z: u, ZZ: u };
    function d(f) {
      var A, S;
      A = f, S = i && i.formats;
      for (var g = (f = A.replace(/(\[[^\]]+])|(LTS?|l{1,4}|L{1,4})/g, function(b, P, T) {
        var B = T && T.toUpperCase();
        return P || S[T] || e7[T] || S[B].replace(/(\[[^\]]+])|(MMMM|MM|DD|dddd)/g, function(D, O, k) {
          return O || k.slice(1);
        });
      })).match(t), C = g.length, y = 0; y < C; y += 1) {
        var F2 = g[y], I = p[F2], v = I && I[0], R = I && I[1];
        g[y] = R ? { regex: v, parser: R } : F2.replace(/^\[|\]$/g, "");
      }
      return function(b) {
        for (var P = {}, T = 0, B = 0; T < C; T += 1) {
          var D = g[T];
          if (typeof D == "string")
            B += D.length;
          else {
            var O = D.regex, k = D.parser, Q = b.slice(B), q = O.exec(Q)[0];
            k.call(P, q), b = b.replace(q, "");
          }
        }
        return function(U) {
          var _ = U.afternoon;
          if (_ !== void 0) {
            var H2 = U.hours;
            _ ? H2 < 12 && (U.hours += 12) : H2 === 12 && (U.hours = 0), delete U.afternoon;
          }
        }(P), P;
      };
    }
    return function(f, A, S) {
      S.p.customParseFormat = true, f && f.parseTwoDigitYear && (s = f.parseTwoDigitYear);
      var g = A.prototype, C = g.parse;
      g.parse = function(y) {
        var F2 = y.date, I = y.utc, v = y.args;
        this.$u = I;
        var R = v[1];
        if (typeof R == "string") {
          var b = v[2] === true, P = v[3] === true, T = b || P, B = v[2];
          P && (B = v[2]), i = this.$locale(), !b && B && (i = S.Ls[B]), this.$d = function(Q, q, U, _) {
            try {
              if (["x", "X"].indexOf(q) > -1)
                return new Date((q === "X" ? 1e3 : 1) * Q);
              var H2 = d(q)(Q), ee = H2.year, oe = H2.month, X = H2.day, te = H2.hours, J = H2.minutes, re = H2.seconds, ge = H2.milliseconds, ie2 = H2.zone, fe = H2.week, ye = /* @__PURE__ */ new Date(), Ge = X || (ee || oe ? 1 : ye.getDate()), it = ee || ye.getFullYear(), Ur = 0;
              ee && !oe || (Ur = oe > 0 ? oe - 1 : ye.getMonth());
              var Eo, To2 = te || 0, Wi = J || 0, bp = re || 0, vp2 = ge || 0;
              return ie2 ? new Date(Date.UTC(it, Ur, Ge, To2, Wi, bp, vp2 + 60 * ie2.offset * 1e3)) : U ? new Date(Date.UTC(it, Ur, Ge, To2, Wi, bp, vp2)) : (Eo = new Date(it, Ur, Ge, To2, Wi, bp, vp2), fe && (Eo = _(Eo).week(fe).toDate()), Eo);
            } catch {
              return /* @__PURE__ */ new Date("");
            }
          }(F2, R, I, S), this.init(), B && B !== true && (this.$L = this.locale(B).$L), T && F2 != this.format(R) && (this.$d = /* @__PURE__ */ new Date("")), i = {};
        } else if (R instanceof Array)
          for (var D = R.length, O = 1; O <= D; O += 1) {
            v[1] = R[O - 1];
            var k = S.apply(this, v);
            if (k.isValid()) {
              this.$d = k.$d, this.$L = k.$L, this.init();
              break;
            }
            O === D && (this.$d = /* @__PURE__ */ new Date(""));
          }
        else
          C.call(this, y);
      };
    };
  });
});
var MC2 = Oe2((oz, NC2) => {
  var wk2 = /(^|; )Coveo-Pendragon=([^;]*)/;
  NC2.exports = () => wk2.exec(document.cookie)?.pop() || null;
});
var QC2 = Oe2((Af, Ff) => {
  (function(e7, t) {
    typeof Af == "object" && typeof Ff < "u" ? Ff.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_timezone = t();
  })(Af, function() {
    var e7 = { year: 0, month: 1, day: 2, hour: 3, minute: 4, second: 5 }, t = {};
    return function(r, n, o) {
      var a, i = function(l, m, p) {
        p === void 0 && (p = {});
        var d = new Date(l), f = function(A, S) {
          S === void 0 && (S = {});
          var g = S.timeZoneName || "short", C = A + "|" + g, y = t[C];
          return y || (y = new Intl.DateTimeFormat("en-US", { hour12: false, timeZone: A, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZoneName: g }), t[C] = y), y;
        }(m, p);
        return f.formatToParts(d);
      }, s = function(l, m) {
        for (var p = i(l, m), d = [], f = 0; f < p.length; f += 1) {
          var A = p[f], S = A.type, g = A.value, C = e7[S];
          C >= 0 && (d[C] = parseInt(g, 10));
        }
        var y = d[3], F2 = y === 24 ? 0 : y, I = d[0] + "-" + d[1] + "-" + d[2] + " " + F2 + ":" + d[4] + ":" + d[5] + ":000", v = +l;
        return (o.utc(I).valueOf() - (v -= v % 1e3)) / 6e4;
      }, c = n.prototype;
      c.tz = function(l, m) {
        l === void 0 && (l = a);
        var p, d = this.utcOffset(), f = this.toDate(), A = f.toLocaleString("en-US", { timeZone: l }), S = Math.round((f - new Date(A)) / 1e3 / 60), g = 15 * -Math.round(f.getTimezoneOffset() / 15) - S;
        if (!Number(g))
          p = this.utcOffset(0, m);
        else if (p = o(A, { locale: this.$L }).$set("millisecond", this.$ms).utcOffset(g, true), m) {
          var C = p.utcOffset();
          p = p.add(d - C, "minute");
        }
        return p.$x.$timezone = l, p;
      }, c.offsetName = function(l) {
        var m = this.$x.$timezone || o.tz.guess(), p = i(this.valueOf(), m, { timeZoneName: l }).find(function(d) {
          return d.type.toLowerCase() === "timezonename";
        });
        return p && p.value;
      };
      var u = c.startOf;
      c.startOf = function(l, m) {
        if (!this.$x || !this.$x.$timezone)
          return u.call(this, l, m);
        var p = o(this.format("YYYY-MM-DD HH:mm:ss:SSS"), { locale: this.$L });
        return u.call(p, l, m).tz(this.$x.$timezone, true);
      }, o.tz = function(l, m, p) {
        var d = p && m, f = p || m || a, A = s(+o(), f);
        if (typeof l != "string")
          return o(l).tz(f);
        var S = function(F2, I, v) {
          var R = F2 - 60 * I * 1e3, b = s(R, v);
          if (I === b)
            return [R, I];
          var P = s(R -= 60 * (b - I) * 1e3, v);
          return b === P ? [R, b] : [F2 - 60 * Math.min(b, P) * 1e3, Math.max(b, P)];
        }(o.utc(l, d).valueOf(), A, f), g = S[0], C = S[1], y = o(g).utcOffset(C);
        return y.$x.$timezone = f, y;
      }, o.tz.guess = function() {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
      }, o.tz.setDefault = function(l) {
        a = l;
      };
    };
  });
});
var LC2 = Oe2((Rf, bf) => {
  (function(e7, t) {
    typeof Rf == "object" && typeof bf < "u" ? bf.exports = t() : typeof define == "function" && define.amd ? define(t) : (e7 = typeof globalThis < "u" ? globalThis : e7 || self).dayjs_plugin_utc = t();
  })(Rf, function() {
    var e7 = "minute", t = /[+-]\d\d(?::?\d\d)?/g, r = /([+-]|\d\d)/g;
    return function(n, o, a) {
      var i = o.prototype;
      a.utc = function(d) {
        var f = { date: d, utc: true, args: arguments };
        return new o(f);
      }, i.utc = function(d) {
        var f = a(this.toDate(), { locale: this.$L, utc: true });
        return d ? f.add(this.utcOffset(), e7) : f;
      }, i.local = function() {
        return a(this.toDate(), { locale: this.$L, utc: false });
      };
      var s = i.parse;
      i.parse = function(d) {
        d.utc && (this.$u = true), this.$utils().u(d.$offset) || (this.$offset = d.$offset), s.call(this, d);
      };
      var c = i.init;
      i.init = function() {
        if (this.$u) {
          var d = this.$d;
          this.$y = d.getUTCFullYear(), this.$M = d.getUTCMonth(), this.$D = d.getUTCDate(), this.$W = d.getUTCDay(), this.$H = d.getUTCHours(), this.$m = d.getUTCMinutes(), this.$s = d.getUTCSeconds(), this.$ms = d.getUTCMilliseconds();
        } else
          c.call(this);
      };
      var u = i.utcOffset;
      i.utcOffset = function(d, f) {
        var A = this.$utils().u;
        if (A(d))
          return this.$u ? 0 : A(this.$offset) ? u.call(this) : this.$offset;
        if (typeof d == "string" && (d = function(y) {
          y === void 0 && (y = "");
          var F2 = y.match(t);
          if (!F2)
            return null;
          var I = ("" + F2[0]).match(r) || ["-", 0, 0], v = I[0], R = 60 * +I[1] + +I[2];
          return R === 0 ? 0 : v === "+" ? R : -R;
        }(d), d === null))
          return this;
        var S = Math.abs(d) <= 16 ? 60 * d : d, g = this;
        if (f)
          return g.$offset = S, g.$u = d === 0, g;
        if (d !== 0) {
          var C = this.$u ? this.toDate().getTimezoneOffset() : -1 * this.utcOffset();
          (g = this.local().add(S + C, e7)).$offset = S, g.$x.$localOffset = C;
        } else
          g = this.utc();
        return g;
      };
      var l = i.format;
      i.format = function(d) {
        var f = d || (this.$u ? "YYYY-MM-DDTHH:mm:ss[Z]" : "");
        return l.call(this, f);
      }, i.valueOf = function() {
        var d = this.$utils().u(this.$offset) ? 0 : this.$offset + (this.$x.$localOffset || this.$d.getTimezoneOffset());
        return this.$d.valueOf() - 6e4 * d;
      }, i.isUTC = function() {
        return !!this.$u;
      }, i.toISOString = function() {
        return this.toDate().toISOString();
      }, i.toString = function() {
        return this.toDate().toUTCString();
      };
      var m = i.toDate;
      i.toDate = function(d) {
        return d === "s" && this.$offset ? a(this.format("YYYY-MM-DD HH:mm:ss:SSS")).toDate() : m.call(this);
      };
      var p = i.diff;
      i.diff = function(d, f, A) {
        if (d && this.$u === d.$u)
          return p.call(this, d, f, A);
        var S = this.local(), g = a(d).local();
        return p.call(S, g, f, A);
      };
    };
  });
});
var JC = Oe2((pK, YC2) => {
  function Bk(e7) {
    try {
      return JSON.stringify(e7);
    } catch {
      return '"[Circular]"';
    }
  }
  YC2.exports = Uk;
  function Uk(e7, t, r) {
    var n = r && r.stringify || Bk, o = 1;
    if (typeof e7 == "object" && e7 !== null) {
      var a = t.length + o;
      if (a === 1)
        return e7;
      var i = new Array(a);
      i[0] = n(e7);
      for (var s = 1; s < a; s++)
        i[s] = n(t[s]);
      return i.join(" ");
    }
    if (typeof e7 != "string")
      return e7;
    var c = t.length;
    if (c === 0)
      return e7;
    for (var u = "", l = 1 - o, m = -1, p = e7 && e7.length || 0, d = 0; d < p; ) {
      if (e7.charCodeAt(d) === 37 && d + 1 < p) {
        switch (m = m > -1 ? m : 0, e7.charCodeAt(d + 1)) {
          case 100:
          case 102:
            if (l >= c || t[l] == null)
              break;
            m < d && (u += e7.slice(m, d)), u += Number(t[l]), m = d + 2, d++;
            break;
          case 105:
            if (l >= c || t[l] == null)
              break;
            m < d && (u += e7.slice(m, d)), u += Math.floor(Number(t[l])), m = d + 2, d++;
            break;
          case 79:
          case 111:
          case 106:
            if (l >= c || t[l] === void 0)
              break;
            m < d && (u += e7.slice(m, d));
            var f = typeof t[l];
            if (f === "string") {
              u += "'" + t[l] + "'", m = d + 2, d++;
              break;
            }
            if (f === "function") {
              u += t[l].name || "<anonymous>", m = d + 2, d++;
              break;
            }
            u += n(t[l]), m = d + 2, d++;
            break;
          case 115:
            if (l >= c)
              break;
            m < d && (u += e7.slice(m, d)), u += String(t[l]), m = d + 2, d++;
            break;
          case 37:
            m < d && (u += e7.slice(m, d)), u += "%", m = d + 2, d++, l--;
            break;
        }
        ++l;
      }
      ++d;
    }
    return m === -1 ? e7 : (m < p && (u += e7.slice(m)), u);
  }
});
var nx = Oe2((mK, al2) => {
  var XC = JC();
  al2.exports = Or;
  var Gs = rO().console || {}, _k = { mapHttpRequest: ol, mapHttpResponse: ol, wrapRequestSerializer: If, wrapResponseSerializer: If, wrapErrorSerializer: If, req: ol, res: ol, err: ex, errWithCause: ex };
  function fn(e7, t) {
    return e7 === "silent" ? 1 / 0 : t.levels.values[e7];
  }
  var kf = Symbol("pino.logFuncs"), Ef = Symbol("pino.hierarchy"), jk = { error: "log", fatal: "error", warn: "error", info: "log", debug: "log", trace: "log" };
  function ZC(e7, t) {
    let r = { logger: t, parent: e7[Ef] };
    t[Ef] = r;
  }
  function $k(e7, t, r) {
    let n = {};
    t.forEach((o) => {
      n[o] = r[o] ? r[o] : Gs[o] || Gs[jk[o] || "log"] || Na2;
    }), e7[kf] = n;
  }
  function Gk(e7, t) {
    return Array.isArray(e7) ? e7.filter(function(n) {
      return n !== "!stdSerializers.err";
    }) : e7 === true ? Object.keys(t) : false;
  }
  function Or(e7) {
    e7 = e7 || {}, e7.browser = e7.browser || {};
    let t = e7.browser.transmit;
    if (t && typeof t.send != "function")
      throw Error("pino: transmit option must have a send function");
    let r = e7.browser.write || Gs;
    e7.browser.write && (e7.browser.asObject = true);
    let n = e7.serializers || {}, o = Gk(e7.browser.serialize, n), a = e7.browser.serialize;
    Array.isArray(e7.browser.serialize) && e7.browser.serialize.indexOf("!stdSerializers.err") > -1 && (a = false);
    let i = Object.keys(e7.customLevels || {}), s = ["error", "fatal", "warn", "info", "debug", "trace"].concat(i);
    typeof r == "function" && s.forEach(function(A) {
      r[A] = r;
    }), (e7.enabled === false || e7.browser.disabled) && (e7.level = "silent");
    let c = e7.level || "info", u = Object.create(r);
    u.log || (u.log = Na2), $k(u, s, r), ZC({}, u), Object.defineProperty(u, "levelVal", { get: m }), Object.defineProperty(u, "level", { get: p, set: d });
    let l = { transmit: t, serialize: o, asObject: e7.browser.asObject, formatters: e7.browser.formatters, levels: s, timestamp: Zk(e7), messageKey: e7.messageKey || "msg", onChild: e7.onChild || Na2 };
    u.levels = Wk(e7), u.level = c, u.setMaxListeners = u.getMaxListeners = u.emit = u.addListener = u.on = u.prependListener = u.once = u.prependOnceListener = u.removeListener = u.removeAllListeners = u.listeners = u.listenerCount = u.eventNames = u.write = u.flush = Na2, u.serializers = n, u._serialize = o, u._stdErrSerialize = a, u.child = function(...A) {
      return f.call(this, l, ...A);
    }, t && (u._logEvent = Tf());
    function m() {
      return fn(this.level, this);
    }
    function p() {
      return this._level;
    }
    function d(A) {
      if (A !== "silent" && !this.levels.values[A])
        throw Error("unknown level " + A);
      this._level = A, ao(this, l, u, "error"), ao(this, l, u, "fatal"), ao(this, l, u, "warn"), ao(this, l, u, "info"), ao(this, l, u, "debug"), ao(this, l, u, "trace"), i.forEach((S) => {
        ao(this, l, u, S);
      });
    }
    function f(A, S, g) {
      if (!S)
        throw new Error("missing bindings for child Pino");
      g = g || {}, o && S.serializers && (g.serializers = S.serializers);
      let C = g.serializers;
      if (o && C) {
        var y = Object.assign({}, n, C), F2 = e7.browser.serialize === true ? Object.keys(y) : o;
        delete S.serializers, Of([S], F2, y, this._stdErrSerialize);
      }
      function I(R) {
        this._childLevel = (R._childLevel | 0) + 1, this.bindings = S, y && (this.serializers = y, this._serialize = F2), t && (this._logEvent = Tf([].concat(R._logEvent.bindings, S)));
      }
      I.prototype = this;
      let v = new I(this);
      return ZC(this, v), v.child = function(...R) {
        return f.call(this, A, ...R);
      }, v.level = g.level || this.level, A.onChild(v), v;
    }
    return u;
  }
  function Wk(e7) {
    let t = e7.customLevels || {}, r = Object.assign({}, Or.levels.values, t), n = Object.assign({}, Or.levels.labels, Hk(t));
    return { values: r, labels: n };
  }
  function Hk(e7) {
    let t = {};
    return Object.keys(e7).forEach(function(r) {
      t[e7[r]] = r;
    }), t;
  }
  Or.levels = { values: { fatal: 60, error: 50, warn: 40, info: 30, debug: 20, trace: 10 }, labels: { 10: "trace", 20: "debug", 30: "info", 40: "warn", 50: "error", 60: "fatal" } };
  Or.stdSerializers = _k;
  Or.stdTimeFunctions = Object.assign({}, { nullTime: tx, epochTime: rx2, unixTime: eO, isoTime: tO });
  function zk(e7) {
    let t = [];
    e7.bindings && t.push(e7.bindings);
    let r = e7[Ef];
    for (; r.parent; )
      r = r.parent, r.logger.bindings && t.push(r.logger.bindings);
    return t.reverse();
  }
  function ao(e7, t, r, n) {
    if (Object.defineProperty(e7, n, { value: fn(e7.level, r) > fn(n, r) ? Na2 : r[kf][n], writable: true, enumerable: true, configurable: true }), e7[n] === Na2) {
      if (!t.transmit)
        return;
      let a = t.transmit.level || e7.level, i = fn(a, r);
      if (fn(n, r) < i)
        return;
    }
    e7[n] = Yk(e7, t, r, n);
    let o = zk(e7);
    o.length !== 0 && (e7[n] = Kk(o, e7[n]));
  }
  function Kk(e7, t) {
    return function() {
      return t.apply(this, [...e7, ...arguments]);
    };
  }
  function Yk(e7, t, r, n) {
    return function(o) {
      return function() {
        let i = t.timestamp(), s = new Array(arguments.length), c = Object.getPrototypeOf && Object.getPrototypeOf(this) === Gs ? Gs : this;
        for (var u = 0; u < s.length; u++)
          s[u] = arguments[u];
        var l = false;
        if (t.serialize && (Of(s, this._serialize, this.serializers, this._stdErrSerialize), l = true), t.asObject || t.formatters ? o.call(c, Jk(this, n, s, i, t)) : o.apply(c, s), t.transmit) {
          let m = t.transmit.level || e7._level, p = fn(m, r), d = fn(n, r);
          if (d < p)
            return;
          Xk(this, { ts: i, methodLevel: n, methodValue: d, send: t.transmit.send, val: fn(e7._level, r) }, s, l);
        }
      };
    }(e7[kf][n]);
  }
  function Jk(e7, t, r, n, o) {
    let { level: a, log: i = (p) => p } = o.formatters || {}, s = r.slice(), c = s[0], u = {};
    if (n && (u.time = n), a) {
      let p = a(t, e7.levels.values[t]);
      Object.assign(u, p);
    } else
      u.level = e7.levels.values[t];
    let l = (e7._childLevel | 0) + 1;
    if (l < 1 && (l = 1), c !== null && typeof c == "object") {
      for (; l-- && typeof s[0] == "object"; )
        Object.assign(u, s.shift());
      c = s.length ? XC(s.shift(), s) : void 0;
    } else
      typeof c == "string" && (c = XC(s.shift(), s));
    return c !== void 0 && (u[o.messageKey] = c), i(u);
  }
  function Of(e7, t, r, n) {
    for (let o in e7)
      if (n && e7[o] instanceof Error)
        e7[o] = Or.stdSerializers.err(e7[o]);
      else if (typeof e7[o] == "object" && !Array.isArray(e7[o]) && t)
        for (let a in e7[o])
          t.indexOf(a) > -1 && a in r && (e7[o][a] = r[a](e7[o][a]));
  }
  function Xk(e7, t, r, n = false) {
    let o = t.send, a = t.ts, i = t.methodLevel, s = t.methodValue, c = t.val, u = e7._logEvent.bindings;
    n || Of(r, e7._serialize || Object.keys(e7.serializers), e7.serializers, e7._stdErrSerialize === void 0 ? true : e7._stdErrSerialize), e7._logEvent.ts = a, e7._logEvent.messages = r.filter(function(l) {
      return u.indexOf(l) === -1;
    }), e7._logEvent.level.label = i, e7._logEvent.level.value = s, o(i, e7._logEvent, c), e7._logEvent = Tf(u);
  }
  function Tf(e7) {
    return { ts: 0, messages: [], bindings: e7 || [], level: { label: "", value: 0 } };
  }
  function ex(e7) {
    let t = { type: e7.constructor.name, msg: e7.message, stack: e7.stack };
    for (let r in e7)
      t[r] === void 0 && (t[r] = e7[r]);
    return t;
  }
  function Zk(e7) {
    return typeof e7.timestamp == "function" ? e7.timestamp : e7.timestamp === false ? tx : rx2;
  }
  function ol() {
    return {};
  }
  function If(e7) {
    return e7;
  }
  function Na2() {
  }
  function tx() {
    return false;
  }
  function rx2() {
    return Date.now();
  }
  function eO() {
    return Math.round(Date.now() / 1e3);
  }
  function tO() {
    return new Date(Date.now()).toISOString();
  }
  function rO() {
    function e7(t) {
      return typeof t < "u" && t;
    }
    try {
      return typeof globalThis < "u" || Object.defineProperty(Object.prototype, "globalThis", { get: function() {
        return delete Object.prototype.globalThis, this.globalThis = this;
      }, configurable: true }), globalThis;
    } catch {
      return e7(self) || e7(window) || e7(this) || {};
    }
  }
  al2.exports.default = Or;
  al2.exports.pino = Or;
});
var Zg2 = {};
Xb2(Zg2, { escape: () => Oo, getHighlightedSuggestion: () => wp2, highlightString: () => nv2 });
function Fc2(e7) {
  return Array.isArray(e7);
}
function Rc(e7) {
  return e7.trim() === "";
}
function Kg(e7, t) {
  return [...e7.reduce((r, n) => {
    let o = t(n);
    return r.has(o) || r.set(o, n), r;
  }, /* @__PURE__ */ new Map()).values()];
}
function ev(e7) {
  return btoa(encodeURI(e7));
}
function ko2(e7) {
  return ev(JSON.stringify(e7));
}
function Hi2(e7) {
  if (typeof e7 != "object" || !e7)
    return e7;
  try {
    return JSON.parse(JSON.stringify(e7));
  } catch {
    return e7;
  }
}
function nv2(e7) {
  if (Rc(e7.openingDelimiter) || Rc(e7.closingDelimiter))
    throw Error("delimiters should be a non-empty string");
  if (isNullOrUndefined2(e7.content) || Rc(e7.content))
    return e7.content;
  if (e7.highlights.length === 0)
    return Oo(e7.content);
  let t = e7.content.length, r = "", n = 0;
  for (let o = 0; o < e7.highlights.length; o++) {
    let a = e7.highlights[o], i = a.offset, s = i + a.length;
    if (s > t)
      break;
    r += Oo(e7.content.slice(n, i)), r += e7.openingDelimiter, r += Oo(e7.content.slice(i, s)), r += e7.closingDelimiter, n = s;
  }
  return n !== t && (r += Oo(e7.content.slice(n))), r;
}
function wp2(e7, t) {
  return e7 = Oo(e7), e7.replace(/\[(.*?)\]|\{(.*?)\}|\((.*?)\)/g, (r, n, o, a) => n ? Pp2(n, t.notMatchDelimiters) : o ? Pp2(o, t.exactMatchDelimiters) : a ? Pp2(a, t.correctionDelimiters) : r);
}
function Pp2(e7, t) {
  return t ? t.open + e7 + t.close : e7;
}
function Oo(e7) {
  let t = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;", "`": "&#x60;" }, r = "(?:" + Object.keys(t).join("|") + ")", n = RegExp(r), o = RegExp(r, "g");
  return n.test(e7) ? e7.replace(o, (a) => t[a]) : e7;
}
async function tS2(e7, t) {
  let r = e7.getReader(), n;
  for (; !(n = await r.read()).done; )
    t(n.value);
}
function rS2(e7) {
  let t, r, n, o = false;
  return function(i) {
    t === void 0 ? (t = i, r = 0, n = -1) : t = av2(t, i);
    let s = t.length, c = 0;
    for (; r < s; ) {
      o && (t[r] === 10 && (c = ++r), o = false);
      let u = -1;
      for (; r < s && u === -1; ++r)
        switch (t[r]) {
          case 58:
            n === -1 && (n = r - c);
            break;
          case 13:
            o = true, u = r;
            break;
          case 10:
            u = r;
            break;
        }
      if (u === -1)
        break;
      e7(t.subarray(c, u), n), c = r, n = -1;
    }
    c === s ? t = void 0 : c !== 0 && (t = t.subarray(c), r -= c);
  };
}
function nS2(e7, t, r) {
  let n = eS2(), o = new TextDecoder();
  return function(i, s) {
    if (i.length === 0)
      r?.(n), n = eS2();
    else if (s > 0) {
      let c = o.decode(i.subarray(0, s)), u = s + (i[s + 1] === 32 ? 2 : 1), l = o.decode(i.subarray(u));
      switch (c) {
        case "data":
          n.data = n.data ? n.data + `
` + l : l;
          break;
        case "event":
          n.event = l;
          break;
        case "id":
          e7(n.id = l);
          break;
        case "retry":
          ov2(l, n, t);
          break;
      }
    }
  };
}
function ov2(e7, t, r) {
  let n = parseInt(e7, 10);
  isNaN(n) || r(t.retry = n);
}
function av2(e7, t) {
  let r = new Uint8Array(e7.length + t.length);
  return r.set(e7), r.set(t, e7.length), r;
}
function eS2() {
  return { data: "", event: "", id: "", retry: void 0 };
}
var Ip = "text/event-stream";
var iv = 1e3;
var oS2 = "last-event-id";
function aS() {
  return typeof window < "u";
}
function vc(e7, { signal: t, headers: r, onopen: n, onmessage: o, onclose: a, onerror: i, openWhenHidden: s, fetch: c, ...u }) {
  return new Promise((l, m) => {
    let p = { ...r };
    p.accept || (p.accept = Ip);
    let d;
    function f() {
      d?.abort(), document.hidden || F2();
    }
    !s && aS() && document.addEventListener("visibilitychange", f);
    let A = iv, S;
    function g() {
      aS() && document.removeEventListener("visibilitychange", f), clearTimeout(S), d?.abort();
    }
    t?.addEventListener("abort", () => {
      g(), l();
    });
    let C = c ?? fetch, y = n ?? sv;
    async function F2() {
      d = AbortController ? new AbortController() : null;
      try {
        let I = await C(e7, { ...u, headers: p, signal: d?.signal });
        await y(I), await tS2(I.body, rS2(nS2((v) => {
          v ? p[oS2] = v : delete p[oS2];
        }, (v) => {
          A = v;
        }, o))), a?.(), g(), l();
      } catch (I) {
        if (!d?.signal?.aborted)
          try {
            let v = i?.(I) ?? A;
            clearTimeout(S), S = setTimeout(F2, v);
          } catch (v) {
            g(), m(v);
          }
      }
    }
    F2();
  });
}
function sv(e7) {
  let t = e7.headers.get("content-type");
  if (!t?.startsWith(Ip))
    throw new Error(`Expected content-type to be ${Ip}, Actual: ${t}`);
}
var jr2 = class {
  constructor(t) {
    Ce2(this, "_basePath");
    Ce2(this, "_params", {});
    this._basePath = t;
  }
  addParam(t, r) {
    this._params = { ...this.params, [t]: r };
  }
  get basePath() {
    return this._basePath;
  }
  get params() {
    return this._params;
  }
  get hasParams() {
    return Object.entries(this._params).length;
  }
  get href() {
    return this.hasParams ? `${this.basePath}?${Object.entries(this.params).map(([t, r]) => `${t}=${encodeURIComponent(r)}`).join("&")}` : this.basePath;
  }
};
var kp = 1;
Vt2(fS());
function Me2(e7, t = "prod", r = "platform") {
  let n = t === "prod" ? "" : t, o = r === "platform" ? "" : `.${r}`;
  return `https://${e7}${o}.org${n}.coveo.com`;
}
function ve2(e7, t = "prod") {
  return `${Me2(e7, t)}/rest/search/v2`;
}
function Bp2(e7, t = "prod") {
  return `${Me2(e7, t, "analytics")}/rest/organizations/${e7}/events/v1`;
}
function Do2() {
  return { answerSnippet: "", documentId: { contentIdKey: "", contentIdValue: "" }, question: "", relatedQuestions: [], score: 0 };
}
function Ze() {
  return { response: { results: [], searchUid: "", totalCountFiltered: 0, facets: [], generateAutomaticFacets: { facets: [] }, queryCorrections: [], triggers: [], questionAnswer: Do2(), pipeline: "", splitTestRun: "", termsToHighlight: {}, phrasesToHighlight: {}, extendedResults: {} }, duration: 0, queryExecuted: "", error: null, automaticallyCorrected: false, isLoading: false, results: [], searchResponseId: "", requestId: "", questionAnswer: Do2(), extendedResults: {} };
}
var RS = (e7, t) => {
  let r = new jr2(`${e7.url}${t}`);
  return r.addParam("access_token", e7.accessToken), r.addParam("organizationId", e7.organizationId), r.addParam("uniqueId", e7.uniqueId), e7.authentication && r.addParam("authentication", e7.authentication), e7.q !== void 0 && r.addParam("q", e7.q), e7.enableNavigation !== void 0 && r.addParam("enableNavigation", `${e7.enableNavigation}`), e7.requestedOutputSize !== void 0 && r.addParam("requestedOutputSize", `${e7.requestedOutputSize}`), r.href;
};
var Tc2 = (e7) => e7.success !== void 0;
var we2 = (e7) => e7.error !== void 0;
var V2 = new StringValue2({ required: true, emptyAllowed: false });
var de2 = new StringValue2({ required: false, emptyAllowed: false });
var se = new StringValue2({ required: true, emptyAllowed: true });
var wS2 = new StringValue2({ required: false, emptyAllowed: true });
var kc2 = new ArrayValue2({ each: V2, required: true });
var IS = new StringValue2({ required: false, emptyAllowed: false, regex: /^\d+\.\d+\.\d+$/ });
var br2 = ({ message: e7, name: t, stack: r }) => ({ message: e7, name: t, stack: r });
var ct2 = (e7, t) => {
  if ("required" in t)
    return { payload: new Schema2({ value: t }).validate({ value: e7 }).value };
  let o = new RecordValue2({ options: { required: true }, values: t }).validate(e7);
  if (o)
    throw new SchemaValidationError2(o);
  return { payload: e7 };
};
var x = (e7, t) => {
  try {
    return ct2(e7, t);
  } catch (r) {
    return { payload: e7, error: br2(r) };
  }
};
var Ae = (e7, t, r, n) => {
  let o = `Check the initialState of ${n}`;
  return ES(e7, t, r, o, "Controller initialization error");
};
var ue = (e7, t, r, n) => {
  let o = `Check the options of ${n}`;
  return ES(e7, t, r, o, "Controller initialization error");
};
var ES = (e7, t, r, n, o) => {
  try {
    return t.validate(r, n);
  } catch (a) {
    throw e7.logger.error(a, o), a;
  }
};
function qe2(e7) {
  return `Minified Redux error #${e7}; visit https://redux.js.org/Errors?code=${e7} for the full message or use the non-minified dev environment for full errors. `;
}
var Up = () => Math.random().toString(36).substring(7).split("").join(".");
var nP2 = { INIT: `@@redux/INIT${Up()}`, REPLACE: `@@redux/REPLACE${Up()}`, PROBE_UNKNOWN_ACTION: () => `@@redux/PROBE_UNKNOWN_ACTION${Up()}` };
var Oc2 = nP2;
function Nt2(e7) {
  if (typeof e7 != "object" || e7 === null)
    return false;
  let t = e7;
  for (; Object.getPrototypeOf(t) !== null; )
    t = Object.getPrototypeOf(t);
  return Object.getPrototypeOf(e7) === t || Object.getPrototypeOf(e7) === null;
}
function oP2(e7) {
  Object.keys(e7).forEach((t) => {
    let r = e7[t];
    if (typeof r(void 0, { type: Oc2.INIT }) > "u")
      throw new Error(qe2(12));
    if (typeof r(void 0, { type: Oc2.PROBE_UNKNOWN_ACTION() }) > "u")
      throw new Error(qe2(13));
  });
}
function Vo(e7) {
  let t = Object.keys(e7), r = {};
  for (let i = 0; i < t.length; i++) {
    let s = t[i];
    typeof e7[s] == "function" && (r[s] = e7[s]);
  }
  let n = Object.keys(r), a;
  try {
    oP2(r);
  } catch (i) {
    a = i;
  }
  return function(s = {}, c) {
    if (a)
      throw a;
    let u = false, l = {};
    for (let m = 0; m < n.length; m++) {
      let p = n[m], d = r[p], f = s[p], A = d(f, c);
      if (typeof A > "u") {
        throw new Error(qe2(14));
      }
      l[p] = A, u = u || A !== f;
    }
    return u = u || n.length !== Object.keys(s).length, u ? l : s;
  };
}
function qc2(e7) {
  return Nt2(e7) && "type" in e7 && typeof e7.type == "string";
}
var Xp2 = Symbol.for("immer-nothing");
var Zi2 = Symbol.for("immer-draftable");
var We2 = Symbol.for("immer-state");
function De2(e7, ...t) {
  throw new Error(`[Immer] minified error nr: ${e7}. Full error at: https://bit.ly/3cXEKWf`);
}
var Wn2 = Object.getPrototypeOf;
function et2(e7) {
  return !!e7 && !!e7[We2];
}
function He2(e7) {
  return e7 ? NS2(e7) || Array.isArray(e7) || !!e7[Zi2] || !!e7.constructor?.[Zi2] || os2(e7) || as2(e7) : false;
}
var aP2 = Object.prototype.constructor.toString();
function NS2(e7) {
  if (!e7 || typeof e7 != "object")
    return false;
  let t = Wn2(e7);
  if (t === null)
    return true;
  let r = Object.hasOwnProperty.call(t, "constructor") && t.constructor;
  return r === Object ? true : typeof r == "function" && Function.toString.call(r) === aP2;
}
function Zp2(e7) {
  return et2(e7) || De2(15, e7), e7[We2].base_;
}
function es2(e7, t) {
  Hn2(e7) === 0 ? Reflect.ownKeys(e7).forEach((r) => {
    t(r, e7[r], e7);
  }) : e7.forEach((r, n) => t(n, r, e7));
}
function Hn2(e7) {
  let t = e7[We2];
  return t ? t.type_ : Array.isArray(e7) ? 1 : os2(e7) ? 2 : as2(e7) ? 3 : 0;
}
function ts2(e7, t) {
  return Hn2(e7) === 2 ? e7.has(t) : Object.prototype.hasOwnProperty.call(e7, t);
}
function jp2(e7, t) {
  return Hn2(e7) === 2 ? e7.get(t) : e7[t];
}
function MS2(e7, t, r) {
  let n = Hn2(e7);
  n === 2 ? e7.set(t, r) : n === 3 ? e7.add(r) : e7[t] = r;
}
function iP2(e7, t) {
  return e7 === t ? e7 !== 0 || 1 / e7 === 1 / t : e7 !== e7 && t !== t;
}
function os2(e7) {
  return e7 instanceof Map;
}
function as2(e7) {
  return e7 instanceof Set;
}
function Gn2(e7) {
  return e7.copy_ || e7.base_;
}
function Wp2(e7, t) {
  if (os2(e7))
    return new Map(e7);
  if (as2(e7))
    return new Set(e7);
  if (Array.isArray(e7))
    return Array.prototype.slice.call(e7);
  let r = NS2(e7);
  if (t === true || t === "class_only" && !r) {
    let n = Object.getOwnPropertyDescriptors(e7);
    delete n[We2];
    let o = Reflect.ownKeys(n);
    for (let a = 0; a < o.length; a++) {
      let i = o[a], s = n[i];
      s.writable === false && (s.writable = true, s.configurable = true), (s.get || s.set) && (n[i] = { configurable: true, writable: true, enumerable: s.enumerable, value: e7[i] });
    }
    return Object.create(Wn2(e7), n);
  } else {
    let n = Wn2(e7);
    if (n !== null && r)
      return { ...e7 };
    let o = Object.create(n);
    return Object.assign(o, e7);
  }
}
function Nc2(e7, t = false) {
  return Mc2(e7) || et2(e7) || !He2(e7) || (Hn2(e7) > 1 && (e7.set = e7.add = e7.clear = e7.delete = sP2), Object.freeze(e7), t && Object.entries(e7).forEach(([r, n]) => Nc2(n, true))), e7;
}
function sP2() {
  De2(2);
}
function Mc2(e7) {
  return Object.isFrozen(e7);
}
var Hp2 = {};
function zn2(e7) {
  let t = Hp2[e7];
  return t || De2(0, e7), t;
}
function cP2(e7, t) {
  Hp2[e7] || (Hp2[e7] = t);
}
var rs2;
function QS2() {
  return rs2;
}
function uP2(e7, t) {
  return { drafts_: [], parent_: e7, immer_: t, canAutoFreeze_: true, unfinalizedDrafts_: 0 };
}
function OS2(e7, t) {
  t && (zn2("Patches"), e7.patches_ = [], e7.inversePatches_ = [], e7.patchListener_ = t);
}
function zp2(e7) {
  Kp2(e7), e7.drafts_.forEach(lP2), e7.drafts_ = null;
}
function Kp2(e7) {
  e7 === rs2 && (rs2 = e7.parent_);
}
function qS2(e7) {
  return rs2 = uP2(rs2, e7);
}
function lP2(e7) {
  let t = e7[We2];
  t.type_ === 0 || t.type_ === 1 ? t.revoke_() : t.revoked_ = true;
}
function DS2(e7, t) {
  t.unfinalizedDrafts_ = t.drafts_.length;
  let r = t.drafts_[0];
  return e7 !== void 0 && e7 !== r ? (r[We2].modified_ && (zp2(t), De2(4)), He2(e7) && (e7 = Dc2(t, e7), t.parent_ || Vc2(t, e7)), t.patches_ && zn2("Patches").generateReplacementPatches_(r[We2].base_, e7, t.patches_, t.inversePatches_)) : e7 = Dc2(t, r, []), zp2(t), t.patches_ && t.patchListener_(t.patches_, t.inversePatches_), e7 !== Xp2 ? e7 : void 0;
}
function Dc2(e7, t, r) {
  if (Mc2(t))
    return t;
  let n = t[We2];
  if (!n)
    return es2(t, (o, a) => VS2(e7, n, t, o, a, r)), t;
  if (n.scope_ !== e7)
    return t;
  if (!n.modified_)
    return Vc2(e7, n.base_, true), n.base_;
  if (!n.finalized_) {
    n.finalized_ = true, n.scope_.unfinalizedDrafts_--;
    let o = n.copy_, a = o, i = false;
    n.type_ === 3 && (a = new Set(o), o.clear(), i = true), es2(a, (s, c) => VS2(e7, n, o, s, c, r, i)), Vc2(e7, o, false), r && e7.patches_ && zn2("Patches").generatePatches_(n, r, e7.patches_, e7.inversePatches_);
  }
  return n.copy_;
}
function VS2(e7, t, r, n, o, a, i) {
  if (et2(o)) {
    let s = a && t && t.type_ !== 3 && !ts2(t.assigned_, n) ? a.concat(n) : void 0, c = Dc2(e7, o, s);
    if (MS2(r, n, c), et2(c))
      e7.canAutoFreeze_ = false;
    else
      return;
  } else
    i && r.add(o);
  if (He2(o) && !Mc2(o)) {
    if (!e7.immer_.autoFreeze_ && e7.unfinalizedDrafts_ < 1)
      return;
    Dc2(e7, o), (!t || !t.scope_.parent_) && typeof n != "symbol" && Object.prototype.propertyIsEnumerable.call(r, n) && Vc2(e7, o);
  }
}
function Vc2(e7, t, r = false) {
  !e7.parent_ && e7.immer_.autoFreeze_ && e7.canAutoFreeze_ && Nc2(t, r);
}
function dP2(e7, t) {
  let r = Array.isArray(e7), n = { type_: r ? 1 : 0, scope_: t ? t.scope_ : QS2(), modified_: false, finalized_: false, assigned_: {}, parent_: t, base_: e7, draft_: null, copy_: null, revoke_: null, isManual_: false }, o = n, a = em2;
  r && (o = [n], a = ns2);
  let { revoke: i, proxy: s } = Proxy.revocable(o, a);
  return n.draft_ = s, n.revoke_ = i, s;
}
var em2 = { get(e7, t) {
  if (t === We2)
    return e7;
  let r = Gn2(e7);
  if (!ts2(r, t))
    return pP2(e7, r, t);
  let n = r[t];
  return e7.finalized_ || !He2(n) ? n : n === $p2(e7.base_, t) ? (Gp2(e7), e7.copy_[t] = Jp2(n, e7)) : n;
}, has(e7, t) {
  return t in Gn2(e7);
}, ownKeys(e7) {
  return Reflect.ownKeys(Gn2(e7));
}, set(e7, t, r) {
  let n = LS2(Gn2(e7), t);
  if (n?.set)
    return n.set.call(e7.draft_, r), true;
  if (!e7.modified_) {
    let o = $p2(Gn2(e7), t), a = o?.[We2];
    if (a && a.base_ === r)
      return e7.copy_[t] = r, e7.assigned_[t] = false, true;
    if (iP2(r, o) && (r !== void 0 || ts2(e7.base_, t)))
      return true;
    Gp2(e7), Yp2(e7);
  }
  return e7.copy_[t] === r && (r !== void 0 || t in e7.copy_) || Number.isNaN(r) && Number.isNaN(e7.copy_[t]) || (e7.copy_[t] = r, e7.assigned_[t] = true), true;
}, deleteProperty(e7, t) {
  return $p2(e7.base_, t) !== void 0 || t in e7.base_ ? (e7.assigned_[t] = false, Gp2(e7), Yp2(e7)) : delete e7.assigned_[t], e7.copy_ && delete e7.copy_[t], true;
}, getOwnPropertyDescriptor(e7, t) {
  let r = Gn2(e7), n = Reflect.getOwnPropertyDescriptor(r, t);
  return n && { writable: true, configurable: e7.type_ !== 1 || t !== "length", enumerable: n.enumerable, value: r[t] };
}, defineProperty() {
  De2(11);
}, getPrototypeOf(e7) {
  return Wn2(e7.base_);
}, setPrototypeOf() {
  De2(12);
} };
var ns2 = {};
es2(em2, (e7, t) => {
  ns2[e7] = function() {
    return arguments[0] = arguments[0][0], t.apply(this, arguments);
  };
});
ns2.deleteProperty = function(e7, t) {
  return ns2.set.call(this, e7, t, void 0);
};
ns2.set = function(e7, t, r) {
  return em2.set.call(this, e7[0], t, r, e7[0]);
};
function $p2(e7, t) {
  let r = e7[We2];
  return (r ? Gn2(r) : e7)[t];
}
function pP2(e7, t, r) {
  let n = LS2(t, r);
  return n ? "value" in n ? n.value : n.get?.call(e7.draft_) : void 0;
}
function LS2(e7, t) {
  if (!(t in e7))
    return;
  let r = Wn2(e7);
  for (; r; ) {
    let n = Object.getOwnPropertyDescriptor(r, t);
    if (n)
      return n;
    r = Wn2(r);
  }
}
function Yp2(e7) {
  e7.modified_ || (e7.modified_ = true, e7.parent_ && Yp2(e7.parent_));
}
function Gp2(e7) {
  e7.copy_ || (e7.copy_ = Wp2(e7.base_, e7.scope_.immer_.useStrictShallowCopy_));
}
var mP2 = class {
  constructor(e7) {
    this.autoFreeze_ = true, this.useStrictShallowCopy_ = false, this.produce = (t, r, n) => {
      if (typeof t == "function" && typeof r != "function") {
        let a = r;
        r = t;
        let i = this;
        return function(c = a, ...u) {
          return i.produce(c, (l) => r.call(this, l, ...u));
        };
      }
      typeof r != "function" && De2(6), n !== void 0 && typeof n != "function" && De2(7);
      let o;
      if (He2(t)) {
        let a = qS2(this), i = Jp2(t, void 0), s = true;
        try {
          o = r(i), s = false;
        } finally {
          s ? zp2(a) : Kp2(a);
        }
        return OS2(a, n), DS2(o, a);
      } else if (!t || typeof t != "object") {
        if (o = r(t), o === void 0 && (o = t), o === Xp2 && (o = void 0), this.autoFreeze_ && Nc2(o, true), n) {
          let a = [], i = [];
          zn2("Patches").generateReplacementPatches_(t, o, a, i), n(a, i);
        }
        return o;
      } else
        De2(1, t);
    }, this.produceWithPatches = (t, r) => {
      if (typeof t == "function")
        return (i, ...s) => this.produceWithPatches(i, (c) => t(c, ...s));
      let n, o;
      return [this.produce(t, r, (i, s) => {
        n = i, o = s;
      }), n, o];
    }, typeof e7?.autoFreeze == "boolean" && this.setAutoFreeze(e7.autoFreeze), typeof e7?.useStrictShallowCopy == "boolean" && this.setUseStrictShallowCopy(e7.useStrictShallowCopy);
  }
  createDraft(e7) {
    He2(e7) || De2(8), et2(e7) && (e7 = BS2(e7));
    let t = qS2(this), r = Jp2(e7, void 0);
    return r[We2].isManual_ = true, Kp2(t), r;
  }
  finishDraft(e7, t) {
    let r = e7 && e7[We2];
    (!r || !r.isManual_) && De2(9);
    let { scope_: n } = r;
    return OS2(n, t), DS2(void 0, n);
  }
  setAutoFreeze(e7) {
    this.autoFreeze_ = e7;
  }
  setUseStrictShallowCopy(e7) {
    this.useStrictShallowCopy_ = e7;
  }
  applyPatches(e7, t) {
    let r;
    for (r = t.length - 1; r >= 0; r--) {
      let o = t[r];
      if (o.path.length === 0 && o.op === "replace") {
        e7 = o.value;
        break;
      }
    }
    r > -1 && (t = t.slice(r + 1));
    let n = zn2("Patches").applyPatches_;
    return et2(e7) ? n(e7, t) : this.produce(e7, (o) => n(o, t));
  }
};
function Jp2(e7, t) {
  let r = os2(e7) ? zn2("MapSet").proxyMap_(e7, t) : as2(e7) ? zn2("MapSet").proxySet_(e7, t) : dP2(e7, t);
  return (t ? t.scope_ : QS2()).drafts_.push(r), r;
}
function BS2(e7) {
  return et2(e7) || De2(10, e7), US2(e7);
}
function US2(e7) {
  if (!He2(e7) || Mc2(e7))
    return e7;
  let t = e7[We2], r;
  if (t) {
    if (!t.modified_)
      return t.base_;
    t.finalized_ = true, r = Wp2(e7, t.scope_.immer_.useStrictShallowCopy_);
  } else
    r = Wp2(e7, true);
  return es2(r, (n, o) => {
    MS2(r, n, US2(o));
  }), t && (t.finalized_ = false), r;
}
function _S2() {
  let t = "replace", r = "add", n = "remove";
  function o(p, d, f, A) {
    switch (p.type_) {
      case 0:
      case 2:
        return i(p, d, f, A);
      case 1:
        return a(p, d, f, A);
      case 3:
        return s(p, d, f, A);
    }
  }
  function a(p, d, f, A) {
    let { base_: S, assigned_: g } = p, C = p.copy_;
    C.length < S.length && ([S, C] = [C, S], [f, A] = [A, f]);
    for (let y = 0; y < S.length; y++)
      if (g[y] && C[y] !== S[y]) {
        let F2 = d.concat([y]);
        f.push({ op: t, path: F2, value: m(C[y]) }), A.push({ op: t, path: F2, value: m(S[y]) });
      }
    for (let y = S.length; y < C.length; y++) {
      let F2 = d.concat([y]);
      f.push({ op: r, path: F2, value: m(C[y]) });
    }
    for (let y = C.length - 1; S.length <= y; --y) {
      let F2 = d.concat([y]);
      A.push({ op: n, path: F2 });
    }
  }
  function i(p, d, f, A) {
    let { base_: S, copy_: g } = p;
    es2(p.assigned_, (C, y) => {
      let F2 = jp2(S, C), I = jp2(g, C), v = y ? ts2(S, C) ? t : r : n;
      if (F2 === I && v === t)
        return;
      let R = d.concat(C);
      f.push(v === n ? { op: v, path: R } : { op: v, path: R, value: I }), A.push(v === r ? { op: n, path: R } : v === n ? { op: r, path: R, value: m(F2) } : { op: t, path: R, value: m(F2) });
    });
  }
  function s(p, d, f, A) {
    let { base_: S, copy_: g } = p, C = 0;
    S.forEach((y) => {
      if (!g.has(y)) {
        let F2 = d.concat([C]);
        f.push({ op: n, path: F2, value: y }), A.unshift({ op: r, path: F2, value: y });
      }
      C++;
    }), C = 0, g.forEach((y) => {
      if (!S.has(y)) {
        let F2 = d.concat([C]);
        f.push({ op: r, path: F2, value: y }), A.unshift({ op: n, path: F2, value: y });
      }
      C++;
    });
  }
  function c(p, d, f, A) {
    f.push({ op: t, path: [], value: d === Xp2 ? void 0 : d }), A.push({ op: t, path: [], value: p });
  }
  function u(p, d) {
    return d.forEach((f) => {
      let { path: A, op: S } = f, g = p;
      for (let I = 0; I < A.length - 1; I++) {
        let v = Hn2(g), R = A[I];
        typeof R != "string" && typeof R != "number" && (R = "" + R), (v === 0 || v === 1) && (R === "__proto__" || R === "constructor") && De2(19), typeof g == "function" && R === "prototype" && De2(19), g = jp2(g, R), typeof g != "object" && De2(18, A.join("/"));
      }
      let C = Hn2(g), y = l(f.value), F2 = A[A.length - 1];
      switch (S) {
        case t:
          switch (C) {
            case 2:
              return g.set(F2, y);
            case 3:
              De2(16);
            default:
              return g[F2] = y;
          }
        case r:
          switch (C) {
            case 1:
              return F2 === "-" ? g.push(y) : g.splice(F2, 0, y);
            case 2:
              return g.set(F2, y);
            case 3:
              return g.add(y);
            default:
              return g[F2] = y;
          }
        case n:
          switch (C) {
            case 1:
              return g.splice(F2, 1);
            case 2:
              return g.delete(F2);
            case 3:
              return g.delete(f.value);
            default:
              return delete g[F2];
          }
        default:
          De2(17, S);
      }
    }), p;
  }
  function l(p) {
    if (!He2(p))
      return p;
    if (Array.isArray(p))
      return p.map(l);
    if (os2(p))
      return new Map(Array.from(p.entries()).map(([f, A]) => [f, l(A)]));
    if (as2(p))
      return new Set(Array.from(p).map(l));
    let d = Object.create(Wn2(p));
    for (let f in p)
      d[f] = l(p[f]);
    return ts2(p, Zi2) && (d[Zi2] = p[Zi2]), d;
  }
  function m(p) {
    return et2(p) ? l(p) : p;
  }
  cP2("Patches", { applyPatches_: u, generatePatches_: o, generateReplacementPatches_: c });
}
var tt2 = new mP2();
var vr2 = tt2.produce;
var Qc2 = tt2.produceWithPatches.bind(tt2);
tt2.setAutoFreeze.bind(tt2);
tt2.setUseStrictShallowCopy.bind(tt2);
var tm2 = tt2.applyPatches.bind(tt2);
tt2.createDraft.bind(tt2);
tt2.finishDraft.bind(tt2);
function fP2(e7, t = `expected a function, instead received ${typeof e7}`) {
  if (typeof e7 != "function")
    throw new TypeError(t);
}
function gP2(e7, t = `expected an object, instead received ${typeof e7}`) {
  if (typeof e7 != "object")
    throw new TypeError(t);
}
function SP2(e7, t = "expected all items to be functions, instead received the following types: ") {
  if (!e7.every((r) => typeof r == "function")) {
    let r = e7.map((n) => typeof n == "function" ? `function ${n.name || "unnamed"}()` : typeof n).join(", ");
    throw new TypeError(`${t}[${r}]`);
  }
}
var jS2 = (e7) => Array.isArray(e7) ? e7 : [e7];
function hP2(e7) {
  let t = Array.isArray(e7[0]) ? e7[0] : e7;
  return SP2(t, "createSelector expects all input-selectors to be functions, but received the following types: "), t;
}
function yP2(e7, t) {
  let r = [], { length: n } = e7;
  for (let o = 0; o < n; o++)
    r.push(e7[o].apply(null, t));
  return r;
}
var CP2 = class {
  constructor(e7) {
    this.value = e7;
  }
  deref() {
    return this.value;
  }
};
var xP2 = typeof WeakRef < "u" ? WeakRef : CP2;
var AP = 0;
var $S2 = 1;
function Lc2() {
  return { s: AP, v: void 0, o: null, p: null };
}
function Mo2(e7, t = {}) {
  let r = Lc2(), { resultEqualityCheck: n } = t, o, a = 0;
  function i() {
    let s = r, { length: c } = arguments;
    for (let m = 0, p = c; m < p; m++) {
      let d = arguments[m];
      if (typeof d == "function" || typeof d == "object" && d !== null) {
        let f = s.o;
        f === null && (s.o = f = /* @__PURE__ */ new WeakMap());
        let A = f.get(d);
        A === void 0 ? (s = Lc2(), f.set(d, s)) : s = A;
      } else {
        let f = s.p;
        f === null && (s.p = f = /* @__PURE__ */ new Map());
        let A = f.get(d);
        A === void 0 ? (s = Lc2(), f.set(d, s)) : s = A;
      }
    }
    let u = s, l;
    if (s.s === $S2)
      l = s.v;
    else if (l = e7.apply(null, arguments), a++, n) {
      let m = o?.deref?.() ?? o;
      m != null && n(m, l) && (l = m, a !== 0 && a--), o = typeof l == "object" && l !== null || typeof l == "function" ? new xP2(l) : l;
    }
    return u.s = $S2, u.v = l, l;
  }
  return i.clearCache = () => {
    r = Lc2(), i.resetResultsCount();
  }, i.resultsCount = () => a, i.resetResultsCount = () => {
    a = 0;
  }, i;
}
function GS(e7, ...t) {
  let r = typeof e7 == "function" ? { memoize: e7, memoizeOptions: t } : e7, n = (...o) => {
    let a = 0, i = 0, s, c = {}, u = o.pop();
    typeof u == "object" && (c = u, u = o.pop()), fP2(u, `createSelector expects an output function after the inputs, but received: [${typeof u}]`);
    let l = { ...r, ...c }, { memoize: m, memoizeOptions: p = [], argsMemoize: d = Mo2, argsMemoizeOptions: f = [] } = l, S = jS2(p), g = jS2(f), C = hP2(o), y = m(function() {
      return a++, u.apply(null, arguments);
    }, ...S), I = d(function() {
      i++;
      let R = yP2(C, arguments);
      return s = y.apply(null, R), s;
    }, ...g);
    return Object.assign(I, { resultFunc: u, memoizedResultFunc: y, dependencies: C, dependencyRecomputations: () => i, resetDependencyRecomputations: () => {
      i = 0;
    }, lastResult: () => s, recomputations: () => a, resetRecomputations: () => {
      a = 0;
    }, memoize: m, argsMemoize: d });
  };
  return Object.assign(n, { withTypes: () => n }), n;
}
var Y2 = GS(Mo2);
var FP2 = Object.assign((e7, t = Y2) => {
  gP2(e7, `createStructuredSelector expects first argument to be an object where each property is a selector, instead received a ${typeof e7}`);
  let r = Object.keys(e7), n = r.map((a) => e7[a]);
  return t(n, (...a) => a.reduce((i, s, c) => (i[r[c]] = s, i), {}));
}, { withTypes: () => FP2 });
var bP = (e7) => e7 && typeof e7.match == "function";
function h3(e7, t) {
  function r(...n) {
    if (t) {
      let o = t(...n);
      if (!o)
        throw new Error(Pt2(0));
      return { type: e7, payload: o.payload, ..."meta" in o && { meta: o.meta }, ..."error" in o && { error: o.error } };
    }
    return { type: e7, payload: n[0] };
  }
  return r.toString = () => `${e7}`, r.type = e7, r.match = (n) => qc2(n) && n.type === e7, r;
}
function KS2(e7) {
  return He2(e7) ? vr2(e7, () => {
  }) : e7;
}
function YS(e7, t, r) {
  return e7.has(t) ? e7.get(t) : e7.set(t, r(t)).get(t);
}
var ss2 = "RTK_autoBatch";
var Lo2 = () => (e7) => ({ payload: e7, meta: { [ss2]: true } });
function th2(e7) {
  let t = {}, r = [], n, o = { addCase(a, i) {
    let s = typeof a == "string" ? a : a.type;
    if (!s)
      throw new Error(Pt2(28));
    if (s in t)
      throw new Error(Pt2(29));
    return t[s] = i, o;
  }, addMatcher(a, i) {
    return r.push({ matcher: a, reducer: i }), o;
  }, addDefaultCase(a) {
    return n = a, o;
  } };
  return e7(o), [t, r, n];
}
function EP2(e7) {
  return typeof e7 == "function";
}
function $2(e7, t) {
  let [r, n, o] = th2(t), a;
  if (EP2(e7))
    a = () => KS2(e7());
  else {
    let s = KS2(e7);
    a = () => s;
  }
  function i(s = a(), c) {
    let u = [r[c.type], ...n.filter(({ matcher: l }) => l(c)).map(({ reducer: l }) => l)];
    return u.filter((l) => !!l).length === 0 && (u = [o]), u.reduce((l, m) => {
      if (m)
        if (et2(l)) {
          let d = m(l, c);
          return d === void 0 ? l : d;
        } else {
          if (He2(l))
            return vr2(l, (p) => m(p, c));
          {
            let p = m(l, c);
            if (p === void 0) {
              if (l === null)
                return l;
              throw Error("A case reducer on a non-draftable value must not return undefined");
            }
            return p;
          }
        }
      return l;
    }, s);
  }
  return i.getInitialState = a, i;
}
var rh2 = (e7, t) => bP(e7) ? e7.match(t) : e7(t);
function Mt2(...e7) {
  return (t) => e7.some((r) => rh2(r, t));
}
function Qo2(...e7) {
  return (t) => e7.every((r) => rh2(r, t));
}
function Uc2(e7, t) {
  if (!e7 || !e7.meta)
    return false;
  let r = typeof e7.meta.requestId == "string", n = t.indexOf(e7.meta.requestStatus) > -1;
  return r && n;
}
function cs2(e7) {
  return typeof e7[0] == "function" && "pending" in e7[0] && "fulfilled" in e7[0] && "rejected" in e7[0];
}
function _c2(...e7) {
  return e7.length === 0 ? (t) => Uc2(t, ["pending"]) : cs2(e7) ? Mt2(...e7.map((t) => t.pending)) : _c2()(e7[0]);
}
function Kn2(...e7) {
  return e7.length === 0 ? (t) => Uc2(t, ["rejected"]) : cs2(e7) ? Mt2(...e7.map((t) => t.rejected)) : Kn2()(e7[0]);
}
function us2(...e7) {
  let t = (r) => r && r.meta && r.meta.rejectedWithValue;
  return e7.length === 0 ? Qo2(Kn2(...e7), t) : cs2(e7) ? Qo2(Kn2(...e7), t) : us2()(e7[0]);
}
function Pr2(...e7) {
  return e7.length === 0 ? (t) => Uc2(t, ["fulfilled"]) : cs2(e7) ? Mt2(...e7.map((t) => t.fulfilled)) : Pr2()(e7[0]);
}
function jc2(...e7) {
  return e7.length === 0 ? (t) => Uc2(t, ["pending", "fulfilled", "rejected"]) : cs2(e7) ? Mt2(...e7.flatMap((t) => [t.pending, t.rejected, t.fulfilled])) : jc2()(e7[0]);
}
var TP2 = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW";
var $c2 = (e7 = 21) => {
  let t = "", r = e7;
  for (; r--; )
    t += TP2[Math.random() * 64 | 0];
  return t;
};
var kP2 = ["name", "message", "stack", "code"];
var rm2 = class {
  constructor(e7, t) {
    Ce2(this, "_type");
    this.payload = e7, this.meta = t;
  }
};
var XS = class {
  constructor(e7, t) {
    Ce2(this, "_type");
    this.payload = e7, this.meta = t;
  }
};
var OP2 = (e7) => {
  if (typeof e7 == "object" && e7 !== null) {
    let t = {};
    for (let r of kP2)
      typeof e7[r] == "string" && (t[r] = e7[r]);
    return t;
  }
  return { message: String(e7) };
};
var W2 = (() => {
  function e7(t, r, n) {
    let o = h3(t + "/fulfilled", (c, u, l, m) => ({ payload: c, meta: { ...m || {}, arg: l, requestId: u, requestStatus: "fulfilled" } })), a = h3(t + "/pending", (c, u, l) => ({ payload: void 0, meta: { ...l || {}, arg: u, requestId: c, requestStatus: "pending" } })), i = h3(t + "/rejected", (c, u, l, m, p) => ({ payload: m, error: (n && n.serializeError || OP2)(c || "Rejected"), meta: { ...p || {}, arg: l, requestId: u, rejectedWithValue: !!m, requestStatus: "rejected", aborted: c?.name === "AbortError", condition: c?.name === "ConditionError" } }));
    function s(c) {
      return (u, l, m) => {
        let p = n?.idGenerator ? n.idGenerator(c) : $c2(), d = new AbortController(), f, A;
        function S(C) {
          A = C, d.abort();
        }
        let g = async function() {
          let C;
          try {
            let F2 = n?.condition?.(c, { getState: l, extra: m });
            if (DP2(F2) && (F2 = await F2), F2 === false || d.signal.aborted)
              throw { name: "ConditionError", message: "Aborted due to condition callback returning false." };
            let I = new Promise((v, R) => {
              f = () => {
                R({ name: "AbortError", message: A || "Aborted" });
              }, d.signal.addEventListener("abort", f);
            });
            u(a(p, c, n?.getPendingMeta?.({ requestId: p, arg: c }, { getState: l, extra: m }))), C = await Promise.race([I, Promise.resolve(r(c, { dispatch: u, getState: l, extra: m, requestId: p, signal: d.signal, abort: S, rejectWithValue: (v, R) => new rm2(v, R), fulfillWithValue: (v, R) => new XS(v, R) })).then((v) => {
              if (v instanceof rm2)
                throw v;
              return v instanceof XS ? o(v.payload, p, c, v.meta) : o(v, p, c);
            })]);
          } catch (F2) {
            C = F2 instanceof rm2 ? i(null, p, c, F2.payload, F2.meta) : i(F2, p, c);
          } finally {
            f && d.signal.removeEventListener("abort", f);
          }
          return n && !n.dispatchConditionRejection && i.match(C) && C.meta.condition || u(C), C;
        }();
        return Object.assign(g, { abort: S, requestId: p, arg: c, unwrap() {
          return g.then(qP2);
        } });
      };
    }
    return Object.assign(s, { pending: a, rejected: i, fulfilled: o, settled: Mt2(i, o), typePrefix: t });
  }
  return e7.withTypes = () => e7, e7;
})();
function qP2(e7) {
  if (e7.meta && e7.meta.rejectedWithValue)
    throw e7.payload;
  if (e7.error)
    throw e7.error;
  return e7.payload;
}
function DP2(e7) {
  return e7 !== null && typeof e7 == "object" && typeof e7.then == "function";
}
var nh = Symbol.for("rtk-slice-createasyncthunk");
function VP2(e7, t) {
  return `${e7}/${t}`;
}
function NP2({ creators: e7 } = {}) {
  let t = e7?.asyncThunk?.[nh];
  return function(n) {
    let { name: o, reducerPath: a = o } = n;
    if (!o)
      throw new Error(Pt2(11));
    let i = (typeof n.reducers == "function" ? n.reducers(QP2()) : n.reducers) || {}, s = Object.keys(i), c = { sliceCaseReducersByName: {}, sliceCaseReducersByType: {}, actionCreators: {}, sliceMatchers: [] }, u = { addCase(C, y) {
      let F2 = typeof C == "string" ? C : C.type;
      if (!F2)
        throw new Error(Pt2(12));
      if (F2 in c.sliceCaseReducersByType)
        throw new Error(Pt2(13));
      return c.sliceCaseReducersByType[F2] = y, u;
    }, addMatcher(C, y) {
      return c.sliceMatchers.push({ matcher: C, reducer: y }), u;
    }, exposeAction(C, y) {
      return c.actionCreators[C] = y, u;
    }, exposeCaseReducer(C, y) {
      return c.sliceCaseReducersByName[C] = y, u;
    } };
    s.forEach((C) => {
      let y = i[C], F2 = { reducerName: C, type: VP2(o, C), createNotation: typeof n.reducers == "function" };
      BP2(y) ? _P2(F2, y, u, t) : LP2(F2, y, u);
    });
    function l() {
      let [C = {}, y = [], F2 = void 0] = typeof n.extraReducers == "function" ? th2(n.extraReducers) : [n.extraReducers], I = { ...C, ...c.sliceCaseReducersByType };
      return $2(n.initialState, (v) => {
        for (let R in I)
          v.addCase(R, I[R]);
        for (let R of c.sliceMatchers)
          v.addMatcher(R.matcher, R.reducer);
        for (let R of y)
          v.addMatcher(R.matcher, R.reducer);
        F2 && v.addDefaultCase(F2);
      });
    }
    let m = (C) => C, p = /* @__PURE__ */ new Map(), d;
    function f(C, y) {
      return d || (d = l()), d(C, y);
    }
    function A() {
      return d || (d = l()), d.getInitialState();
    }
    function S(C, y = false) {
      function F2(v) {
        let R = v[C];
        return typeof R > "u" && y && (R = A()), R;
      }
      function I(v = m) {
        let R = YS(p, y, () => /* @__PURE__ */ new WeakMap());
        return YS(R, v, () => {
          let b = {};
          for (let [P, T] of Object.entries(n.selectors ?? {}))
            b[P] = MP2(T, v, A, y);
          return b;
        });
      }
      return { reducerPath: C, getSelectors: I, get selectors() {
        return I(F2);
      }, selectSlice: F2 };
    }
    let g = { name: o, reducer: f, actions: c.actionCreators, caseReducers: c.sliceCaseReducersByName, getInitialState: A, ...S(a), injectInto(C, { reducerPath: y, ...F2 } = {}) {
      let I = y ?? a;
      return C.inject({ reducerPath: I, reducer: f }, F2), { ...g, ...S(I, true) };
    } };
    return g;
  };
}
function MP2(e7, t, r, n) {
  function o(a, ...i) {
    let s = t(a);
    return typeof s > "u" && n && (s = r()), e7(s, ...i);
  }
  return o.unwrapped = e7, o;
}
var Yn2 = NP2();
function QP2() {
  function e7(t, r) {
    return { _reducerDefinitionType: "asyncThunk", payloadCreator: t, ...r };
  }
  return e7.withTypes = () => e7, { reducer(t) {
    return Object.assign({ [t.name](...r) {
      return t(...r);
    } }[t.name], { _reducerDefinitionType: "reducer" });
  }, preparedReducer(t, r) {
    return { _reducerDefinitionType: "reducerWithPrepare", prepare: t, reducer: r };
  }, asyncThunk: e7 };
}
function LP2({ type: e7, reducerName: t, createNotation: r }, n, o) {
  let a, i;
  if ("reducer" in n) {
    if (r && !UP2(n))
      throw new Error(Pt2(17));
    a = n.reducer, i = n.prepare;
  } else
    a = n;
  o.addCase(e7, a).exposeCaseReducer(t, a).exposeAction(t, i ? h3(e7, i) : h3(e7));
}
function BP2(e7) {
  return e7._reducerDefinitionType === "asyncThunk";
}
function UP2(e7) {
  return e7._reducerDefinitionType === "reducerWithPrepare";
}
function _P2({ type: e7, reducerName: t }, r, n, o) {
  if (!o)
    throw new Error(Pt2(18));
  let { payloadCreator: a, fulfilled: i, pending: s, rejected: c, settled: u, options: l } = r, m = o(e7, a, l);
  n.exposeAction(t, m), i && n.addCase(m.fulfilled, i), s && n.addCase(m.pending, s), c && n.addCase(m.rejected, c), u && n.addMatcher(m.settled, u), n.exposeCaseReducer(t, { fulfilled: i || Bc2, pending: s || Bc2, rejected: c || Bc2, settled: u || Bc2 });
}
function Bc2() {
}
var { assign: sh2 } = Object;
var nm2 = "listenerMiddleware";
var jP2 = sh2(h3(`${nm2}/add`), { withTypes: () => jP2 });
h3(`${nm2}/removeAll`);
var $P2 = sh2(h3(`${nm2}/remove`), { withTypes: () => $P2 });
function Pt2(e7) {
  return `Minified Redux Toolkit error #${e7}; visit https://redux-toolkit.js.org/Errors?code=${e7} for the full message or use the non-minified dev environment for full errors. `;
}
function GP2({ config: e7, environment: t, event: r, listenerManager: n }) {
  let { url: o, token: a, mode: i } = e7;
  i !== "disabled" && (n.call(r), t.send(o, a, r));
}
var WP2 = /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|00000000-0000-0000-0000-000000000000|ffffffff-ffff-ffff-ffff-ffffffffffff)$/i;
function HP2(e7) {
  return typeof e7 == "string" && WP2.test(e7);
}
var Ve2 = [];
for (let e7 = 0; e7 < 256; ++e7)
  Ve2.push((e7 + 256).toString(16).slice(1));
function zP2(e7, t = 0) {
  return (Ve2[e7[t + 0]] + Ve2[e7[t + 1]] + Ve2[e7[t + 2]] + Ve2[e7[t + 3]] + "-" + Ve2[e7[t + 4]] + Ve2[e7[t + 5]] + "-" + Ve2[e7[t + 6]] + Ve2[e7[t + 7]] + "-" + Ve2[e7[t + 8]] + Ve2[e7[t + 9]] + "-" + Ve2[e7[t + 10]] + Ve2[e7[t + 11]] + Ve2[e7[t + 12]] + Ve2[e7[t + 13]] + Ve2[e7[t + 14]] + Ve2[e7[t + 15]]).toLowerCase();
}
var om2;
var KP2 = new Uint8Array(16);
function YP2() {
  if (!om2) {
    if (typeof crypto > "u" || !crypto.getRandomValues)
      throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");
    om2 = crypto.getRandomValues.bind(crypto);
  }
  return om2(KP2);
}
var JP2 = typeof crypto < "u" && crypto.randomUUID && crypto.randomUUID.bind(crypto);
var ch2 = { randomUUID: JP2 };
function XP2(e7, t, r) {
  if (ch2.randomUUID && !e7)
    return ch2.randomUUID();
  e7 = e7 || {};
  let n = e7.random ?? e7.rng?.() ?? YP2();
  if (n.length < 16)
    throw new Error("Random bytes length must be >= 16");
  return n[6] = n[6] & 15 | 64, n[8] = n[8] & 63 | 128, zP2(n);
}
function ZP2(e7) {
  return { getClientId: () => {
    let t = "visitorId", r = e7.get(), n = r.storage, o = n.getItem(t), a = o && HP2(o) ? o : r.generateUUID();
    return n.setItem(t, a), a;
  } };
}
var lh2 = "1.0.0";
function ew2(e7) {
  let { trackingId: t } = e7;
  return { trackingId: t };
}
function tw2(e7) {
  return (e7.source || []).concat([`relay@${lh2}`]);
}
function dh2(e7, t, r, n) {
  let { getReferrer: o, getLocation: a, getUserAgent: i } = r, s = ew2(t), c = n.getClientId();
  return Object.freeze({ type: e7, config: s, ts: Date.now(), source: tw2(t), clientId: c, userAgent: i(), referrer: o(), location: a() });
}
function rw2(e7, t, r, n, o) {
  return { ...t, meta: dh2(e7, r, n, o) };
}
var nw2 = "*";
function ow2() {
  let e7 = [];
  function t({ type: c, callback: u }) {
    return e7.findIndex((l) => l.type === c && l.callback === u);
  }
  function r(c, u) {
    return c.type === "*" || u === c.type;
  }
  function n(c) {
    return t(c) < 0 && e7.push(c), () => s(c.type, c.callback);
  }
  function o(c) {
    e7.forEach((u) => {
      if (r(u, c.meta.type))
        try {
          u.callback(c);
        } catch (l) {
          console.error(l);
        }
    });
  }
  function a(c) {
    if (c === nw2)
      e7.length = 0;
    else
      for (let u = e7.length - 1; u >= 0; u--)
        e7[u].type === c && e7.splice(u, 1);
  }
  function i(c) {
    let u = t(c);
    u >= 0 && e7.splice(u, 1);
  }
  function s(c, u) {
    u ? i({ type: c, callback: u }) : a(c);
  }
  return { add: n, call: o, remove: s };
}
function uh2({ url: e7, token: t, trackingId: r, ...n }) {
  return Object.freeze({ url: e7, token: t, trackingId: r, ...!!n.mode && { mode: n.mode }, ...!!n.source && { source: n.source } });
}
function aw2(e7) {
  let t = uh2(e7);
  return { get: () => t, update: (r) => {
    t = uh2({ ...t, ...r });
  } };
}
function iw2() {
  let e7 = typeof window < "u";
  return { sendMessage(t) {
    e7 && window.postMessage(t, "*");
  } };
}
var am2 = sw2();
function sw2() {
  let e7 = "coveo_", t = (r) => {
    let n = r.split(".").slice(-2);
    return n.length == 2 ? n.join(".") : "";
  };
  return { getItem(r) {
    let n = `${e7}${r}=`, o = document.cookie.split(";");
    for (let a of o) {
      let i = a.replace(/^\s+/, "");
      if (i.lastIndexOf(n, 0) === 0)
        return i.substring(n.length, i.length);
    }
    return null;
  }, setItem(r, n, o) {
    let a = t(window.location.hostname), i = `;expires=${new Date((/* @__PURE__ */ new Date()).getTime() + o).toUTCString()}`, s = a ? `;domain=${a}` : "";
    document.cookie = `${e7}${r}=${n}${i}${s};path=/;SameSite=Lax`;
  }, removeItem(r) {
    this.setItem(r, "", -1);
  } };
}
function cw2() {
  return { getItem(e7) {
    return am2.getItem(e7) || localStorage.getItem(e7);
  }, removeItem(e7) {
    am2.removeItem(e7), localStorage.removeItem(e7);
  }, setItem(e7, t) {
    localStorage.setItem(e7, t), am2.setItem(e7, t, 31556952e3);
  } };
}
function uw2() {
  let e7 = document.referrer;
  return e7 === "" ? null : e7;
}
function lw2() {
  return { runtime: "browser", send: (e7, t, r) => {
    let n = navigator.sendBeacon(`${e7}?access_token=${t}`, new Blob([JSON.stringify([r])], { type: "application/json" }));
    if (iw2().sendMessage({ kind: "EVENT_PROTOCOL", event: r, url: e7, token: t }), !n)
      throw new Error("Failed to send the event(s) because the payload size exceeded the maximum allowed size (32 KB). Please contact support if the problem persists.");
  }, getReferrer: () => uw2(), getLocation: () => window.location.href, getUserAgent: () => navigator.userAgent, generateUUID: () => XP2(), storage: cw2() };
}
function dw2() {
  try {
    let e7 = "__storage_test__";
    return localStorage.setItem(e7, e7), localStorage.removeItem(e7), true;
  } catch (e7) {
    return e7 instanceof DOMException && e7.name === "QuotaExceededError" && localStorage && localStorage.length !== 0;
  }
}
function pw2() {
  return { getItem() {
    return null;
  }, removeItem() {
  }, setItem() {
  } };
}
function mw2() {
  return { runtime: "null", send: () => {
  }, getReferrer: () => null, getLocation: () => null, getUserAgent: () => null, generateUUID: () => "", storage: pw2() };
}
function fw2(e7) {
  return e7.get().mode !== "disabled" && gw2() && dw2() ? lw2() : mw2();
}
function gw2() {
  try {
    return typeof window == "object";
  } catch {
    return false;
  }
}
function Sw2(e7) {
  return { get: () => Object.freeze(fw2(e7)) };
}
function ph2(e7) {
  let t = aw2(e7), r = ow2(), n = Sw2(t), o = ZP2(n);
  return { emit: (a, i) => {
    let s = t.get(), c = n.get(), u = rw2(a, i, s, c, o);
    return GP2({ config: s, environment: c, event: u, listenerManager: r });
  }, getMeta: (a) => dh2(a, t.get(), n.get(), o), on: (a, i) => r.add({ type: a, callback: i }), off: (a, i) => r.remove(a, i), updateConfig: (a) => t.update(a), version: lh2 };
}
var Jn2 = "3.21.0";
var mh2 = ["@coveo/atomic", "@coveo/quantic"];
var Hr2 = Y2((e7) => e7.source, (e7) => Object.entries(e7).map(([t, r]) => `${t}@${r}`).concat(`@coveo/headless@${Jn2}`));
var Bo2 = Y2((e7) => e7.configuration.organizationId, (e7) => e7.configuration.environment, (e7) => e7.configuration.accessToken, (e7) => e7.configuration.analytics, (e7) => Hr2(e7.configuration.analytics), (e7, t, r, { trackingId: n, apiBaseUrl: o, enabled: a }, i) => ph2({ mode: a ? "emit" : "disabled", url: o ?? Bp2(e7, t), token: r, trackingId: n, source: i }));
function wr2(e7, t) {
  var r = {};
  for (var n in e7)
    Object.prototype.hasOwnProperty.call(e7, n) && t.indexOf(n) < 0 && (r[n] = e7[n]);
  if (e7 != null && typeof Object.getOwnPropertySymbols == "function")
    for (var o = 0, n = Object.getOwnPropertySymbols(e7); o < n.length; o++)
      t.indexOf(n[o]) < 0 && Object.prototype.propertyIsEnumerable.call(e7, n[o]) && (r[n[o]] = e7[n[o]]);
  return r;
}
function w2(e7, t, r, n) {
  function o(a) {
    return a instanceof r ? a : new r(function(i) {
      i(a);
    });
  }
  return new (r || (r = Promise))(function(a, i) {
    function s(l) {
      try {
        u(n.next(l));
      } catch (m) {
        i(m);
      }
    }
    function c(l) {
      try {
        u(n.throw(l));
      } catch (m) {
        i(m);
      }
    }
    function u(l) {
      l.done ? a(l.value) : o(l.value).then(s, c);
    }
    u((n = n.apply(e7, [])).next());
  });
}
var ne2;
(function(e7) {
  e7.search = "search", e7.click = "click", e7.custom = "custom", e7.view = "view", e7.collect = "collect";
})(ne2 || (ne2 = {}));
function cm2() {
  return typeof window < "u";
}
function Am() {
  return typeof navigator < "u";
}
function Uo() {
  return typeof document < "u";
}
function um2() {
  try {
    return typeof localStorage < "u";
  } catch {
    return false;
  }
}
function hw2() {
  try {
    return typeof sessionStorage < "u";
  } catch {
    return false;
  }
}
function wh2() {
  return Am() && navigator.cookieEnabled;
}
var yw2 = [ne2.click, ne2.custom, ne2.search, ne2.view];
var Cw2 = (e7, t) => yw2.indexOf(e7) !== -1 ? Object.assign({ language: Uo() ? document.documentElement.lang : "unknown", userAgent: Am() ? navigator.userAgent : "unknown" }, t) : t;
var ps2 = class e4 {
  static set(t, r, n) {
    var o, a, i, s;
    n && (a = /* @__PURE__ */ new Date(), a.setTime(a.getTime() + n)), s = window.location.hostname, s.indexOf(".") === -1 ? fh2(t, r, a) : (i = s.split("."), o = i[i.length - 2] + "." + i[i.length - 1], fh2(t, r, a, o));
  }
  static get(t) {
    for (var r = t + "=", n = document.cookie.split(";"), o = 0; o < n.length; o++) {
      var a = n[o];
      if (a = a.replace(/^\s+/, ""), a.lastIndexOf(r, 0) === 0)
        return a.substring(r.length, a.length);
    }
    return null;
  }
  static erase(t) {
    e4.set(t, "", -1);
  }
};
function fh2(e7, t, r, n) {
  document.cookie = `${e7}=${t}` + (r ? `;expires=${r.toUTCString()}` : "") + (n ? `;domain=${n}` : "") + ";path=/;SameSite=Lax";
}
function xw2() {
  return um2() ? localStorage : wh2() ? new ms2() : hw2() ? sessionStorage : new jo2();
}
var ms2 = class e5 {
  getItem(t) {
    return ps2.get(`${e5.prefix}${t}`);
  }
  removeItem(t) {
    ps2.erase(`${e5.prefix}${t}`);
  }
  setItem(t, r, n) {
    ps2.set(`${e5.prefix}${t}`, r, n);
  }
};
ms2.prefix = "coveo_";
var lm = class {
  constructor() {
    this.cookieStorage = new ms2();
  }
  getItem(t) {
    return localStorage.getItem(t) || this.cookieStorage.getItem(t);
  }
  removeItem(t) {
    this.cookieStorage.removeItem(t), localStorage.removeItem(t);
  }
  setItem(t, r) {
    localStorage.setItem(t, r), this.cookieStorage.setItem(t, r, 31556926e3);
  }
};
var jo2 = class {
  getItem(t) {
    return null;
  }
  removeItem(t) {
  }
  setItem(t, r) {
  }
};
var ls2 = "__coveo.analytics.history";
var Ih2 = 20;
var Eh2 = 1e3 * 60;
var Th2 = 75;
var $o2 = class {
  constructor(t) {
    this.store = t || xw2();
  }
  addElement(t) {
    t.internalTime = (/* @__PURE__ */ new Date()).getTime(), t = this.cropQueryElement(this.stripEmptyQuery(t));
    let r = this.getHistoryWithInternalTime();
    r != null ? this.isValidEntry(t) && this.setHistory([t].concat(r)) : this.setHistory([t]);
  }
  addElementAsync(t) {
    return w2(this, void 0, void 0, function* () {
      t.internalTime = (/* @__PURE__ */ new Date()).getTime(), t = this.cropQueryElement(this.stripEmptyQuery(t));
      let r = yield this.getHistoryWithInternalTimeAsync();
      r != null ? this.isValidEntry(t) && this.setHistory([t].concat(r)) : this.setHistory([t]);
    });
  }
  getHistory() {
    let t = this.getHistoryWithInternalTime();
    return this.stripEmptyQueries(this.stripInternalTime(t));
  }
  getHistoryAsync() {
    return w2(this, void 0, void 0, function* () {
      let t = yield this.getHistoryWithInternalTimeAsync();
      return this.stripEmptyQueries(this.stripInternalTime(t));
    });
  }
  getHistoryWithInternalTime() {
    try {
      let t = this.store.getItem(ls2);
      return t && typeof t == "string" ? JSON.parse(t) : [];
    } catch {
      return [];
    }
  }
  getHistoryWithInternalTimeAsync() {
    return w2(this, void 0, void 0, function* () {
      try {
        let t = yield this.store.getItem(ls2);
        return t ? JSON.parse(t) : [];
      } catch {
        return [];
      }
    });
  }
  setHistory(t) {
    try {
      this.store.setItem(ls2, JSON.stringify(t.slice(0, Ih2)));
    } catch {
    }
  }
  clear() {
    try {
      this.store.removeItem(ls2);
    } catch {
    }
  }
  getMostRecentElement() {
    let t = this.getHistoryWithInternalTime();
    return Array.isArray(t) ? t.sort((n, o) => (o.internalTime || 0) - (n.internalTime || 0))[0] : null;
  }
  cropQueryElement(t) {
    return t.name && t.value && t.name.toLowerCase() === "query" && (t.value = t.value.slice(0, Th2)), t;
  }
  isValidEntry(t) {
    let r = this.getMostRecentElement();
    return r && r.value == t.value ? (t.internalTime || 0) - (r.internalTime || 0) > Eh2 : true;
  }
  stripInternalTime(t) {
    return Array.isArray(t) ? t.map((r) => {
      let { name: n, time: o, value: a } = r;
      return { name: n, time: o, value: a };
    }) : [];
  }
  stripEmptyQuery(t) {
    let { name: r, time: n, value: o } = t;
    return r && typeof o == "string" && r.toLowerCase() === "query" && o.trim() === "" ? { name: r, time: n } : t;
  }
  stripEmptyQueries(t) {
    return t.map((r) => this.stripEmptyQuery(r));
  }
};
var kh2 = Object.freeze({ __proto__: null, HistoryStore: $o2, MAX_NUMBER_OF_HISTORY_ELEMENTS: Ih2, MAX_VALUE_SIZE: Th2, MIN_THRESHOLD_FOR_DUPLICATE_VALUE: Eh2, STORE_KEY: ls2, default: $o2 });
var Aw2 = (e7, t) => w2(void 0, void 0, void 0, function* () {
  return e7 === ne2.view ? (yield Fw2(t.contentIdValue), Object.assign({ location: window.location.toString(), referrer: document.referrer, title: document.title }, t)) : t;
});
var Fw2 = (e7) => w2(void 0, void 0, void 0, function* () {
  let t = new $o2(), r = { name: "PageView", value: e7, time: (/* @__PURE__ */ new Date()).toISOString() };
  yield t.addElementAsync(r);
});
var Gc2;
var Rw2 = new Uint8Array(16);
function bw2() {
  if (!Gc2 && (Gc2 = typeof crypto < "u" && crypto.getRandomValues && crypto.getRandomValues.bind(crypto), !Gc2))
    throw new Error("crypto.getRandomValues() not supported. See https://github.com/uuidjs/uuid#getrandomvalues-not-supported");
  return Gc2(Rw2);
}
var vw2 = /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|00000000-0000-0000-0000-000000000000)$/i;
function Hc(e7) {
  return typeof e7 == "string" && vw2.test(e7);
}
var Ne2 = [];
for (let e7 = 0; e7 < 256; ++e7)
  Ne2.push((e7 + 256).toString(16).slice(1));
function Oh2(e7, t = 0) {
  return (Ne2[e7[t + 0]] + Ne2[e7[t + 1]] + Ne2[e7[t + 2]] + Ne2[e7[t + 3]] + "-" + Ne2[e7[t + 4]] + Ne2[e7[t + 5]] + "-" + Ne2[e7[t + 6]] + Ne2[e7[t + 7]] + "-" + Ne2[e7[t + 8]] + Ne2[e7[t + 9]] + "-" + Ne2[e7[t + 10]] + Ne2[e7[t + 11]] + Ne2[e7[t + 12]] + Ne2[e7[t + 13]] + Ne2[e7[t + 14]] + Ne2[e7[t + 15]]).toLowerCase();
}
function Pw2(e7) {
  if (!Hc(e7))
    throw TypeError("Invalid UUID");
  let t, r = new Uint8Array(16);
  return r[0] = (t = parseInt(e7.slice(0, 8), 16)) >>> 24, r[1] = t >>> 16 & 255, r[2] = t >>> 8 & 255, r[3] = t & 255, r[4] = (t = parseInt(e7.slice(9, 13), 16)) >>> 8, r[5] = t & 255, r[6] = (t = parseInt(e7.slice(14, 18), 16)) >>> 8, r[7] = t & 255, r[8] = (t = parseInt(e7.slice(19, 23), 16)) >>> 8, r[9] = t & 255, r[10] = (t = parseInt(e7.slice(24, 36), 16)) / 1099511627776 & 255, r[11] = t / 4294967296 & 255, r[12] = t >>> 24 & 255, r[13] = t >>> 16 & 255, r[14] = t >>> 8 & 255, r[15] = t & 255, r;
}
function ww2(e7) {
  e7 = unescape(encodeURIComponent(e7));
  let t = [];
  for (let r = 0; r < e7.length; ++r)
    t.push(e7.charCodeAt(r));
  return t;
}
var Iw2 = "6ba7b810-9dad-11d1-80b4-00c04fd430c8";
var Ew2 = "6ba7b811-9dad-11d1-80b4-00c04fd430c8";
function Tw2(e7, t, r) {
  function n(o, a, i, s) {
    var c;
    if (typeof o == "string" && (o = ww2(o)), typeof a == "string" && (a = Pw2(a)), ((c = a) === null || c === void 0 ? void 0 : c.length) !== 16)
      throw TypeError("Namespace must be array-like (16 iterable integer values, 0-255)");
    let u = new Uint8Array(16 + o.length);
    if (u.set(a), u.set(o, a.length), u = r(u), u[6] = u[6] & 15 | t, u[8] = u[8] & 63 | 128, i) {
      s = s || 0;
      for (let l = 0; l < 16; ++l)
        i[s + l] = u[l];
      return i;
    }
    return Oh2(u);
  }
  try {
    n.name = e7;
  } catch {
  }
  return n.DNS = Iw2, n.URL = Ew2, n;
}
var kw2 = typeof crypto < "u" && crypto.randomUUID && crypto.randomUUID.bind(crypto);
var gh2 = { randomUUID: kw2 };
function Xn2(e7, t, r) {
  if (gh2.randomUUID && true && !e7)
    return gh2.randomUUID();
  e7 = e7 || {};
  let n = e7.random || (e7.rng || bw2)();
  if (n[6] = n[6] & 15 | 64, n[8] = n[8] & 63 | 128, t)
    ;
  return Oh2(n);
}
function Ow2(e7, t, r, n) {
  switch (e7) {
    case 0:
      return t & r ^ ~t & n;
    case 1:
      return t ^ r ^ n;
    case 2:
      return t & r ^ t & n ^ r & n;
    case 3:
      return t ^ r ^ n;
  }
}
function im2(e7, t) {
  return e7 << t | e7 >>> 32 - t;
}
function qw2(e7) {
  let t = [1518500249, 1859775393, 2400959708, 3395469782], r = [1732584193, 4023233417, 2562383102, 271733878, 3285377520];
  if (typeof e7 == "string") {
    let i = unescape(encodeURIComponent(e7));
    e7 = [];
    for (let s = 0; s < i.length; ++s)
      e7.push(i.charCodeAt(s));
  } else
    Array.isArray(e7) || (e7 = Array.prototype.slice.call(e7));
  e7.push(128);
  let n = e7.length / 4 + 2, o = Math.ceil(n / 16), a = new Array(o);
  for (let i = 0; i < o; ++i) {
    let s = new Uint32Array(16);
    for (let c = 0; c < 16; ++c)
      s[c] = e7[i * 64 + c * 4] << 24 | e7[i * 64 + c * 4 + 1] << 16 | e7[i * 64 + c * 4 + 2] << 8 | e7[i * 64 + c * 4 + 3];
    a[i] = s;
  }
  a[o - 1][14] = (e7.length - 1) * 8 / Math.pow(2, 32), a[o - 1][14] = Math.floor(a[o - 1][14]), a[o - 1][15] = (e7.length - 1) * 8 & 4294967295;
  for (let i = 0; i < o; ++i) {
    let s = new Uint32Array(80);
    for (let d = 0; d < 16; ++d)
      s[d] = a[i][d];
    for (let d = 16; d < 80; ++d)
      s[d] = im2(s[d - 3] ^ s[d - 8] ^ s[d - 14] ^ s[d - 16], 1);
    let c = r[0], u = r[1], l = r[2], m = r[3], p = r[4];
    for (let d = 0; d < 80; ++d) {
      let f = Math.floor(d / 20), A = im2(c, 5) + Ow2(f, u, l, m) + p + t[f] + s[d] >>> 0;
      p = m, m = l, l = im2(u, 30) >>> 0, u = c, c = A;
    }
    r[0] = r[0] + c >>> 0, r[1] = r[1] + u >>> 0, r[2] = r[2] + l >>> 0, r[3] = r[3] + m >>> 0, r[4] = r[4] + p >>> 0;
  }
  return [r[0] >> 24 & 255, r[0] >> 16 & 255, r[0] >> 8 & 255, r[0] & 255, r[1] >> 24 & 255, r[1] >> 16 & 255, r[1] >> 8 & 255, r[1] & 255, r[2] >> 24 & 255, r[2] >> 16 & 255, r[2] >> 8 & 255, r[2] & 255, r[3] >> 24 & 255, r[3] >> 16 & 255, r[3] >> 8 & 255, r[3] & 255, r[4] >> 24 & 255, r[4] >> 16 & 255, r[4] >> 8 & 255, r[4] & 255];
}
var Dw2 = Tw2("v5", 80, qw2);
var Sh = Dw2;
var qh2 = "2.30.45";
var ds2 = { pageview: "pageview", event: "event" };
var zr2 = class e6 {
  constructor(t, r) {
    if (!Hc(t))
      throw Error("Not a valid uuid");
    this.clientId = t, this.creationDate = Math.floor(r / 1e3);
  }
  toString() {
    return this.clientId.replace(/-/g, "") + "." + this.creationDate.toString();
  }
  get expired() {
    let t = Math.floor(Date.now() / 1e3) - this.creationDate;
    return t < 0 || t > e6.expirationTime;
  }
  validate(t, r) {
    return !this.expired && this.matchReferrer(t, r);
  }
  matchReferrer(t, r) {
    try {
      let n = new URL(t);
      return r.some((o) => new RegExp(o.replace(/\\/g, "\\\\").replace(/\./g, "\\.").replace(/\*/g, ".*") + "$").test(n.host));
    } catch {
      return false;
    }
  }
  static fromString(t) {
    let r = t.split(".");
    if (r.length !== 2)
      return null;
    let [n, o] = r;
    if (n.length !== 32 || isNaN(parseInt(o)))
      return null;
    let a = n.substring(0, 8) + "-" + n.substring(8, 12) + "-" + n.substring(12, 16) + "-" + n.substring(16, 20) + "-" + n.substring(20, 32);
    return Hc(a) ? new e6(a, Number.parseInt(o) * 1e3) : null;
  }
};
zr2.cvo_cid = "cvo_cid";
zr2.expirationTime = 120;
var lt2 = Object.keys;
function Wc2(e7) {
  return e7 !== null && typeof e7 == "object" && !Array.isArray(e7);
}
var sm2 = 128;
var Dh2 = 192;
var yh2 = 224;
var Ch2 = 240;
function Vw2(e7) {
  return (e7 & 248) === Ch2 ? 4 : (e7 & Ch2) === yh2 ? 3 : (e7 & yh2) === Dh2 ? 2 : 1;
}
function Nw2(e7, t) {
  if (t < 0 || e7.length <= t)
    return e7;
  let r = e7.indexOf("%", t - 2);
  for (r < 0 || r > t ? r = t : t = r; r > 2 && e7.charAt(r - 3) == "%"; ) {
    let n = Number.parseInt(e7.substring(r - 2, r), 16);
    if ((n & sm2) != sm2)
      break;
    if (r -= 3, (n & Dh2) != sm2) {
      t - r >= Vw2(n) * 3 && (r = t);
      break;
    }
  }
  return e7.substring(0, r);
}
var mm2 = { id: "svc_ticket_id", subject: "svc_ticket_subject", description: "svc_ticket_description", category: "svc_ticket_category", productId: "svc_ticket_product_id", custom: "svc_ticket_custom" };
var Mw2 = lt2(mm2).map((e7) => mm2[e7]);
var Qw2 = [...Mw2].join("|");
var Lw = new RegExp(`^(${Qw2}$)`);
var Bw2 = { svcAction: "svc_action", svcActionData: "svc_action_data" };
var _w2 = (e7) => Lw.test(e7);
var jw2 = [_w2];
var xh2 = { id: "id", name: "nm", brand: "br", category: "ca", variant: "va", price: "pr", quantity: "qt", coupon: "cc", position: "ps", group: "group" };
var Ah2 = { id: "id", name: "nm", brand: "br", category: "ca", variant: "va", position: "ps", price: "pr", group: "group" };
var Qe2 = { action: "pa", list: "pal", listSource: "pls" };
var Kc2 = { id: "ti", revenue: "tr", tax: "tt", shipping: "ts", coupon: "tcc", affiliation: "ta", step: "cos", option: "col" };
var $w2 = ["loyaltyCardId", "loyaltyTier", "thirdPartyPersona", "companyName", "favoriteStore", "storeName", "userIndustry", "userRole", "userDepartment", "businessUnit"];
var fm2 = { id: "quoteId", affiliation: "quoteAffiliation" };
var gm2 = { id: "reviewId", rating: "reviewRating", comment: "reviewComment" };
var Gw2 = { add: Qe2, bookmark_add: Qe2, bookmark_remove: Qe2, click: Qe2, checkout: Qe2, checkout_option: Qe2, detail: Qe2, impression: Qe2, remove: Qe2, refund: Object.assign(Object.assign({}, Qe2), Kc2), purchase: Object.assign(Object.assign({}, Qe2), Kc2), quickview: Qe2, quote: Object.assign(Object.assign({}, Qe2), fm2), review: Object.assign(Object.assign({}, Qe2), gm2) };
var Ww2 = lt2(xh2).map((e7) => xh2[e7]);
var Hw2 = lt2(Ah2).map((e7) => Ah2[e7]);
var zw2 = lt2(Qe2).map((e7) => Qe2[e7]);
var Kw2 = lt2(Kc2).map((e7) => Kc2[e7]);
var Yw2 = lt2(gm2).map((e7) => gm2[e7]);
var Jw2 = lt2(fm2).map((e7) => fm2[e7]);
var Xw2 = [...Ww2, "custom"].join("|");
var Zw2 = [...Hw2, "custom"].join("|");
var Vh2 = "(pr[0-9]+)";
var Nh2 = "(il[0-9]+pi[0-9]+)";
var eI2 = new RegExp(`^${Vh2}(${Xw2})$`);
var tI2 = new RegExp(`^(${Nh2}(${Zw2}))|(il[0-9]+nm)$`);
var rI2 = new RegExp(`^(${zw2.join("|")})$`);
var nI2 = new RegExp(`^(${Kw2.join("|")})$`);
var oI2 = new RegExp(`^${Vh2}custom$`);
var aI2 = new RegExp(`^${Nh2}custom$`);
var iI2 = new RegExp(`^(${[...$w2, ...Yw2, ...Jw2].join("|")})$`);
var sI2 = (e7) => eI2.test(e7);
var cI2 = (e7) => tI2.test(e7);
var uI2 = (e7) => rI2.test(e7);
var lI2 = (e7) => nI2.test(e7);
var dI2 = (e7) => iI2.test(e7);
var pI2 = [cI2, sI2, uI2, lI2, dI2];
var mI2 = [oI2, aI2];
var fI2 = { anonymizeIp: "aip" };
var gI2 = { eventCategory: "ec", eventAction: "ea", eventLabel: "el", eventValue: "ev", page: "dp", visitorId: "cid", clientId: "cid", userId: "uid", currencyCode: "cu" };
var SI2 = { hitType: "t", pageViewId: "pid", encoding: "de", location: "dl", referrer: "dr", screenColor: "sd", screenResolution: "sr", title: "dt", userAgent: "ua", language: "ul", eventId: "z", time: "tm" };
var hI2 = ["contentId", "contentIdKey", "contentType", "searchHub", "tab", "searchUid", "permanentId", "contentLocale", "trackingId"];
var yI2 = Object.assign(Object.assign(Object.assign(Object.assign({}, fI2), gI2), SI2), hI2.reduce((e7, t) => Object.assign(Object.assign({}, e7), { [t]: t }), {}));
var Sm2 = Object.assign(Object.assign({}, yI2), Bw2);
var CI2 = (e7) => {
  let t = !!e7.action && Gw2[e7.action] || {};
  return lt2(e7).reduce((r, n) => {
    let o = t[n] || Sm2[n] || n;
    return Object.assign(Object.assign({}, r), { [o]: e7[n] });
  }, {});
};
var xI2 = lt2(Sm2).map((e7) => Sm2[e7]);
var AI2 = (e7) => xI2.indexOf(e7) !== -1;
var FI2 = (e7) => e7 === "custom";
var RI2 = (e7) => [...pI2, ...jw2, AI2, FI2].some((t) => t(e7));
var bI2 = (e7) => lt2(e7).reduce((t, r) => {
  let n = vI2(r);
  return n ? Object.assign(Object.assign({}, t), PI2(n, e7[r])) : Object.assign(Object.assign({}, t), { [r]: e7[r] });
}, {});
var vI2 = (e7) => {
  let t;
  return [...mI2].every((r) => {
    var n;
    return t = (n = r.exec(e7)) === null || n === void 0 ? void 0 : n[1], !t;
  }), t;
};
var PI2 = (e7, t) => lt2(t).reduce((r, n) => Object.assign(Object.assign({}, r), { [`${e7}${n}`]: t[n] }), {});
var hm2 = class {
  constructor(t) {
    this.opts = t;
  }
  sendEvent(t, r) {
    return w2(this, void 0, void 0, function* () {
      if (!this.isAvailable())
        throw new Error('navigator.sendBeacon is not supported in this browser. Consider adding a polyfill like "sendbeacon-polyfill".');
      let { baseUrl: n, preprocessRequest: o } = this.opts, a = yield this.getQueryParamsForEventType(t), { url: i, payload: s } = yield this.preProcessRequestAsPotentialJSONString(`${n}/analytics/${t}?${a}`, r, o), c = this.encodeForEventType(t, s), u = new Blob([c], { type: "application/x-www-form-urlencoded" });
      navigator.sendBeacon(i, u);
    });
  }
  isAvailable() {
    return "sendBeacon" in navigator;
  }
  deleteHttpCookieVisitorId() {
    return Promise.resolve();
  }
  preProcessRequestAsPotentialJSONString(t, r, n) {
    return w2(this, void 0, void 0, function* () {
      let o = t, a = r;
      if (n) {
        let i = yield n({ url: t, body: JSON.stringify(r) }, "analyticsBeacon"), { url: s, body: c } = i;
        o = s || t;
        try {
          a = JSON.parse(c);
        } catch (u) {
          console.error("Unable to process the request body as a JSON string", u);
        }
      }
      return { payload: a, url: o };
    });
  }
  encodeForEventType(t, r) {
    return this.isEventTypeLegacy(t) ? this.encodeEventToJson(t, r) : this.encodeEventToJson(t, r, this.opts.token);
  }
  getQueryParamsForEventType(t) {
    return w2(this, void 0, void 0, function* () {
      let { token: r, visitorIdProvider: n } = this.opts, o = yield n.getCurrentVisitorId();
      return [r && this.isEventTypeLegacy(t) ? `access_token=${r}` : "", o ? `visitorId=${o}` : "", "discardVisitInfo=true"].filter((a) => !!a).join("&");
    });
  }
  isEventTypeLegacy(t) {
    return [ne2.click, ne2.custom, ne2.search, ne2.view].indexOf(t) !== -1;
  }
  encodeEventToJson(t, r, n) {
    let o = `${t}Event=${encodeURIComponent(JSON.stringify(r))}`;
    return n && (o = `access_token=${encodeURIComponent(n)}&${o}`), o;
  }
};
var ym2 = class {
  sendEvent(t, r) {
    return w2(this, void 0, void 0, function* () {
      return Promise.resolve();
    });
  }
  deleteHttpCookieVisitorId() {
    return w2(this, void 0, void 0, function* () {
      return Promise.resolve();
    });
  }
};
var Fh2 = globalThis.fetch;
var Yc2 = class {
  constructor(t) {
    this.opts = t;
  }
  sendEvent(t, r) {
    return w2(this, void 0, void 0, function* () {
      let { baseUrl: n, visitorIdProvider: o, preprocessRequest: a } = this.opts, i = this.shouldAppendVisitorId(t) ? yield this.getVisitorIdParam() : "", s = { url: `${n}/analytics/${t}${i}`, credentials: "include", mode: "cors", headers: this.getHeaders(), method: "POST", body: JSON.stringify(r) }, c = Object.assign(Object.assign({}, s), a ? yield a(s, "analyticsFetch") : {}), { url: u } = c, l = wr2(c, ["url"]), m;
      try {
        m = yield Fh2(u, l);
      } catch (p) {
        console.error("An error has occured when sending the event.", p);
        return;
      }
      if (m.ok) {
        let p = yield m.json();
        return p.visitorId && o.setCurrentVisitorId(p.visitorId), p;
      } else {
        try {
          m.json();
        } catch {
        }
        throw console.error(`An error has occured when sending the "${t}" event.`, m, r), new Error(`An error has occurred when sending the "${t}" event. Check the console logs for more details.`);
      }
    });
  }
  deleteHttpCookieVisitorId() {
    return w2(this, void 0, void 0, function* () {
      let { baseUrl: t } = this.opts, r = `${t}/analytics/visit`;
      yield Fh2(r, { headers: this.getHeaders(), method: "DELETE" });
    });
  }
  shouldAppendVisitorId(t) {
    return [ne2.click, ne2.custom, ne2.search, ne2.view].indexOf(t) !== -1;
  }
  getVisitorIdParam() {
    return w2(this, void 0, void 0, function* () {
      let { visitorIdProvider: t } = this.opts, r = yield t.getCurrentVisitorId();
      return r ? `?visitor=${r}` : "";
    });
  }
  getHeaders() {
    let { token: t } = this.opts;
    return Object.assign(Object.assign({}, t ? { Authorization: `Bearer ${t}` } : {}), { "Content-Type": "application/json" });
  }
};
var Cm2 = class {
  constructor(t, r) {
    um2() && wh2() ? this.storage = new lm() : um2() ? this.storage = localStorage : (console.warn("BrowserRuntime detected no valid storage available.", this), this.storage = new jo2()), this.client = new Yc2(t), this.beaconClient = new hm2(t), window.addEventListener("beforeunload", () => {
      let n = r();
      for (let { eventType: o, payload: a } of n)
        this.beaconClient.sendEvent(o, a);
    });
  }
  getClientDependingOnEventType(t) {
    return t === "click" && this.beaconClient.isAvailable() ? this.beaconClient : this.client;
  }
};
var xm2 = class {
  constructor(t, r) {
    this.storage = r || new jo2(), this.client = new Yc2(t);
  }
  getClientDependingOnEventType(t) {
    return this.client;
  }
};
var Jc2 = class {
  constructor() {
    this.storage = new jo2(), this.client = new ym2();
  }
  getClientDependingOnEventType(t) {
    return this.client;
  }
};
var wI2 = "xx";
var II2 = (e7) => e7?.startsWith(wI2) || false;
var EI2 = `
        We've detected you're using React Native but have not provided the corresponding runtime,
        for an optimal experience please use the "coveo.analytics/react-native" subpackage.
        Follow the Readme on how to set it up: https://github.com/coveo/coveo.analytics.js#using-react-native
    `;
function TI2() {
  return typeof navigator < "u" && navigator.product == "ReactNative";
}
var kI2 = ["1", 1, "yes", true];
function Xc2() {
  let e7 = [];
  return cm2() && e7.push(window.doNotTrack), Am() && e7.push(navigator.doNotTrack, navigator.msDoNotTrack, navigator.globalPrivacyControl), e7.some((t) => kI2.indexOf(t) !== -1);
}
var Mh2 = "v15";
var Qh2 = { default: "https://analytics.cloud.coveo.com/rest/ua" };
function OI2(e7 = Qh2.default, t = Mh2, r = false) {
  if (e7 = e7.replace(/\/$/, ""), r)
    return `${e7}/${t}`;
  let n = e7.endsWith("/rest") || e7.endsWith("/rest/ua");
  return `${e7}${n ? "" : "/rest"}/${t}`;
}
var qI2 = "38824e1f-37f5-42d3-8372-a4b8fa9df946";
var Qt2 = class {
  get defaultOptions() {
    return { endpoint: Qh2.default, isCustomEndpoint: false, token: "", version: Mh2, beforeSendHooks: [], afterSendHooks: [] };
  }
  get version() {
    return qh2;
  }
  constructor(t) {
    if (this.acceptedLinkReferrers = [], !t)
      throw new Error("You have to pass options to this constructor");
    this.options = Object.assign(Object.assign({}, this.defaultOptions), t), this.visitorId = "", this.bufferedRequests = [], this.beforeSendHooks = [Aw2, Cw2].concat(this.options.beforeSendHooks), this.afterSendHooks = this.options.afterSendHooks, this.eventTypeMapping = {};
    let r = { baseUrl: this.baseUrl, token: this.options.token, visitorIdProvider: this, preprocessRequest: this.options.preprocessRequest };
    Xc2() ? this.runtime = new Jc2() : this.runtime = this.options.runtimeEnvironment || this.initRuntime(r), this.addEventTypeMapping(ne2.view, { newEventType: ne2.view, addClientIdParameter: true }), this.addEventTypeMapping(ne2.click, { newEventType: ne2.click, addClientIdParameter: true }), this.addEventTypeMapping(ne2.custom, { newEventType: ne2.custom, addClientIdParameter: true }), this.addEventTypeMapping(ne2.search, { newEventType: ne2.search, addClientIdParameter: true });
  }
  initRuntime(t) {
    return cm2() && Uo() ? new Cm2(t, () => {
      let r = [...this.bufferedRequests];
      return this.bufferedRequests = [], r;
    }) : (TI2() && console.warn(EI2), new xm2(t));
  }
  get storage() {
    return this.runtime.storage;
  }
  determineVisitorId() {
    return w2(this, void 0, void 0, function* () {
      try {
        return cm2() && this.extractClientIdFromLink(window.location.href) || (yield this.storage.getItem("visitorId")) || Xn2();
      } catch (t) {
        return console.log("Could not get visitor ID from the current runtime environment storage. Using a random ID instead.", t), Xn2();
      }
    });
  }
  getCurrentVisitorId() {
    return w2(this, void 0, void 0, function* () {
      if (!this.visitorId) {
        let t = yield this.determineVisitorId();
        yield this.setCurrentVisitorId(t);
      }
      return this.visitorId;
    });
  }
  setCurrentVisitorId(t) {
    return w2(this, void 0, void 0, function* () {
      this.visitorId = t, yield this.storage.setItem("visitorId", t);
    });
  }
  setClientId(t, r) {
    return w2(this, void 0, void 0, function* () {
      if (Hc(t))
        this.setCurrentVisitorId(t.toLowerCase());
      else {
        if (!r)
          throw Error("Cannot generate uuid client id without a specific namespace string.");
        this.setCurrentVisitorId(Sh(t, Sh(r, qI2)));
      }
    });
  }
  getParameters(t, ...r) {
    return w2(this, void 0, void 0, function* () {
      return yield this.resolveParameters(t, ...r);
    });
  }
  getPayload(t, ...r) {
    return w2(this, void 0, void 0, function* () {
      let n = yield this.resolveParameters(t, ...r);
      return yield this.resolvePayloadForParameters(t, n);
    });
  }
  get currentVisitorId() {
    return typeof (this.visitorId || this.storage.getItem("visitorId")) != "string" && this.setCurrentVisitorId(Xn2()), this.visitorId;
  }
  set currentVisitorId(t) {
    this.visitorId = t, this.storage.setItem("visitorId", t);
  }
  extractClientIdFromLink(t) {
    if (Xc2())
      return null;
    try {
      let r = new URL(t).searchParams.get(zr2.cvo_cid);
      if (r == null)
        return null;
      let n = zr2.fromString(r);
      return !n || !Uo() || !n.validate(document.referrer, this.acceptedLinkReferrers) ? null : n.clientId;
    } catch {
    }
    return null;
  }
  resolveParameters(t, ...r) {
    return w2(this, void 0, void 0, function* () {
      let { variableLengthArgumentsNames: n = [], addVisitorIdParameter: o = false, usesMeasurementProtocol: a = false, addClientIdParameter: i = false } = this.eventTypeMapping[t] || {};
      return yield [(d) => n.length > 0 ? this.parseVariableArgumentsPayload(n, d) : d[0], (d) => w2(this, void 0, void 0, function* () {
        return Object.assign(Object.assign({}, d), { visitorId: o ? yield this.getCurrentVisitorId() : "" });
      }), (d) => w2(this, void 0, void 0, function* () {
        return i ? Object.assign(Object.assign({}, d), { clientId: yield this.getCurrentVisitorId() }) : d;
      }), (d) => a ? this.ensureAnonymousUserWhenUsingApiKey(d) : d, (d) => this.beforeSendHooks.reduce((f, A) => w2(this, void 0, void 0, function* () {
        let S = yield f;
        return yield A(t, S);
      }), d)].reduce((d, f) => w2(this, void 0, void 0, function* () {
        let A = yield d;
        return yield f(A);
      }), Promise.resolve(r));
    });
  }
  resolvePayloadForParameters(t, r) {
    return w2(this, void 0, void 0, function* () {
      let { usesMeasurementProtocol: n = false } = this.eventTypeMapping[t] || {};
      return yield [(m) => this.setTrackingIdIfTrackingIdNotPresent(m), (m) => this.removeEmptyPayloadValues(m, t), (m) => this.validateParams(m, t), (m) => n ? CI2(m) : m, (m) => n ? this.removeUnknownParameters(m) : m, (m) => n ? this.processCustomParameters(m) : this.mapCustomParametersToCustomData(m)].reduce((m, p) => w2(this, void 0, void 0, function* () {
        let d = yield m;
        return yield p(d);
      }), Promise.resolve(r));
    });
  }
  makeEvent(t, ...r) {
    return w2(this, void 0, void 0, function* () {
      let { newEventType: n = t } = this.eventTypeMapping[t] || {}, o = yield this.resolveParameters(t, ...r), a = yield this.resolvePayloadForParameters(t, o);
      return { eventType: n, payload: a, log: (i) => w2(this, void 0, void 0, function* () {
        return this.bufferedRequests.push({ eventType: n, payload: Object.assign(Object.assign({}, a), i) }), yield Promise.all(this.afterSendHooks.map((s) => s(t, Object.assign(Object.assign({}, o), i)))), yield this.deferExecution(), yield this.sendFromBuffer();
      }) };
    });
  }
  sendEvent(t, ...r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeEvent(t, ...r)).log({});
    });
  }
  deferExecution() {
    return new Promise((t) => setTimeout(t, 0));
  }
  sendFromBuffer() {
    return w2(this, void 0, void 0, function* () {
      let t = this.bufferedRequests.shift();
      if (t) {
        let { eventType: r, payload: n } = t;
        return this.runtime.getClientDependingOnEventType(r).sendEvent(r, n);
      }
    });
  }
  clear() {
    this.storage.removeItem("visitorId"), new $o2().clear();
  }
  deleteHttpOnlyVisitorId() {
    this.runtime.client.deleteHttpCookieVisitorId();
  }
  makeSearchEvent(t) {
    return w2(this, void 0, void 0, function* () {
      return this.makeEvent(ne2.search, t);
    });
  }
  sendSearchEvent(t) {
    var { searchQueryUid: r } = t, n = wr2(t, ["searchQueryUid"]);
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSearchEvent(n)).log({ searchQueryUid: r });
    });
  }
  makeClickEvent(t) {
    return w2(this, void 0, void 0, function* () {
      return this.makeEvent(ne2.click, t);
    });
  }
  sendClickEvent(t) {
    var { searchQueryUid: r } = t, n = wr2(t, ["searchQueryUid"]);
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeClickEvent(n)).log({ searchQueryUid: r });
    });
  }
  makeCustomEvent(t) {
    return w2(this, void 0, void 0, function* () {
      return this.makeEvent(ne2.custom, t);
    });
  }
  sendCustomEvent(t) {
    var { lastSearchQueryUid: r } = t, n = wr2(t, ["lastSearchQueryUid"]);
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCustomEvent(n)).log({ lastSearchQueryUid: r });
    });
  }
  makeViewEvent(t) {
    return w2(this, void 0, void 0, function* () {
      return this.makeEvent(ne2.view, t);
    });
  }
  sendViewEvent(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeViewEvent(t)).log({});
    });
  }
  getVisit() {
    return w2(this, void 0, void 0, function* () {
      let r = yield (yield fetch(`${this.baseUrl}/analytics/visit`)).json();
      return this.visitorId = r.visitorId, r;
    });
  }
  getHealth() {
    return w2(this, void 0, void 0, function* () {
      return yield (yield fetch(`${this.baseUrl}/analytics/monitoring/health`)).json();
    });
  }
  registerBeforeSendEventHook(t) {
    this.beforeSendHooks.push(t);
  }
  registerAfterSendEventHook(t) {
    this.afterSendHooks.push(t);
  }
  addEventTypeMapping(t, r) {
    this.eventTypeMapping[t] = r;
  }
  setAcceptedLinkReferrers(t) {
    if (Array.isArray(t) && t.every((r) => typeof r == "string"))
      this.acceptedLinkReferrers = t;
    else
      throw Error("Parameter should be an array of domain strings");
  }
  parseVariableArgumentsPayload(t, r) {
    let n = {};
    for (let o = 0, a = r.length; o < a; o++) {
      let i = r[o];
      if (typeof i == "string")
        n[t[o]] = i;
      else if (typeof i == "object")
        return Object.assign(Object.assign({}, n), i);
    }
    return n;
  }
  isKeyAllowedEmpty(t, r) {
    return ({ [ne2.search]: ["queryText"] }[t] || []).indexOf(r) !== -1;
  }
  removeEmptyPayloadValues(t, r) {
    let n = (o) => typeof o < "u" && o !== null && o !== "";
    return Object.keys(t).filter((o) => this.isKeyAllowedEmpty(r, o) || n(t[o])).reduce((o, a) => Object.assign(Object.assign({}, o), { [a]: t[a] }), {});
  }
  removeUnknownParameters(t) {
    return Object.keys(t).filter((n) => {
      if (RI2(n))
        return true;
      console.log(n, "is not processed by coveoua");
    }).reduce((n, o) => Object.assign(Object.assign({}, n), { [o]: t[o] }), {});
  }
  processCustomParameters(t) {
    let { custom: r } = t, n = wr2(t, ["custom"]), o = {};
    r && Wc2(r) && (o = this.lowercaseKeys(r));
    let a = bI2(n);
    return Object.assign(Object.assign({}, o), a);
  }
  mapCustomParametersToCustomData(t) {
    let { custom: r } = t, n = wr2(t, ["custom"]);
    if (r && Wc2(r)) {
      let o = this.lowercaseKeys(r);
      return Object.assign(Object.assign({}, n), { customData: Object.assign(Object.assign({}, o), t.customData) });
    } else
      return t;
  }
  lowercaseKeys(t) {
    let r = Object.keys(t), n = {};
    return r.forEach((o) => {
      n[o.toLowerCase()] = t[o];
    }), n;
  }
  validateParams(t, r) {
    let { anonymizeIp: n } = t, o = wr2(t, ["anonymizeIp"]);
    return n !== void 0 && ["0", "false", "undefined", "null", "{}", "[]", ""].indexOf(`${n}`.toLowerCase()) == -1 && (o.anonymizeIp = 1), (r == ne2.view || r == ne2.click || r == ne2.search || r == ne2.custom) && (o.originLevel3 = this.limit(o.originLevel3, 1024)), r == ne2.view && (o.location = this.limit(o.location, 1024)), (r == "pageview" || r == "event") && (o.referrer = this.limit(o.referrer, 2048), o.location = this.limit(o.location, 2048), o.page = this.limit(o.page, 2048)), o;
  }
  ensureAnonymousUserWhenUsingApiKey(t) {
    let { userId: r } = t, n = wr2(t, ["userId"]);
    return II2(this.options.token) && !r ? (n.userId = "anonymous", n) : t;
  }
  setTrackingIdIfTrackingIdNotPresent(t) {
    let { trackingId: r } = t, n = wr2(t, ["trackingId"]);
    return r ? t : (n.hasOwnProperty("custom") && Wc2(n.custom) && (n.custom.hasOwnProperty("context_website") || n.custom.hasOwnProperty("siteName")) && (n.trackingId = n.custom.context_website || n.custom.siteName), n.hasOwnProperty("customData") && Wc2(n.customData) && (n.customData.hasOwnProperty("context_website") || n.customData.hasOwnProperty("siteName")) && (n.trackingId = n.customData.context_website || n.customData.siteName), n);
  }
  limit(t, r) {
    return typeof t == "string" ? Nw2(t, r) : t;
  }
  get baseUrl() {
    return OI2(this.options.endpoint, this.options.version, this.options.isCustomEndpoint);
  }
};
var Ir2;
(function(e7) {
  e7.contextChanged = "contextChanged", e7.expandToFullUI = "expandToFullUI", e7.openUserActions = "openUserActions", e7.showPrecedingSessions = "showPrecedingSessions", e7.showFollowingSessions = "showFollowingSessions", e7.clickViewedDocument = "clickViewedDocument", e7.clickPageView = "clickPageView", e7.createArticle = "createArticle";
})(Ir2 || (Ir2 = {}));
var E2;
(function(e7) {
  e7.interfaceLoad = "interfaceLoad", e7.interfaceChange = "interfaceChange", e7.didyoumeanAutomatic = "didyoumeanAutomatic", e7.didyoumeanClick = "didyoumeanClick", e7.resultsSort = "resultsSort", e7.searchboxSubmit = "searchboxSubmit", e7.searchboxClear = "searchboxClear", e7.searchboxAsYouType = "searchboxAsYouType", e7.breadcrumbFacet = "breadcrumbFacet", e7.breadcrumbResetAll = "breadcrumbResetAll", e7.documentQuickview = "documentQuickview", e7.documentOpen = "documentOpen", e7.omniboxAnalytics = "omniboxAnalytics", e7.omniboxFromLink = "omniboxFromLink", e7.searchFromLink = "searchFromLink", e7.triggerNotify = "notify", e7.triggerExecute = "execute", e7.triggerQuery = "query", e7.undoTriggerQuery = "undoQuery", e7.triggerRedirect = "redirect", e7.pagerResize = "pagerResize", e7.pagerNumber = "pagerNumber", e7.pagerNext = "pagerNext", e7.pagerPrevious = "pagerPrevious", e7.pagerScrolling = "pagerScrolling", e7.staticFilterClearAll = "staticFilterClearAll", e7.staticFilterSelect = "staticFilterSelect", e7.staticFilterDeselect = "staticFilterDeselect", e7.facetClearAll = "facetClearAll", e7.facetSearch = "facetSearch", e7.facetSelect = "facetSelect", e7.facetSelectAll = "facetSelectAll", e7.facetDeselect = "facetDeselect", e7.facetExclude = "facetExclude", e7.facetUnexclude = "facetUnexclude", e7.facetUpdateSort = "facetUpdateSort", e7.facetShowMore = "showMoreFacetResults", e7.facetShowLess = "showLessFacetResults", e7.queryError = "query", e7.queryErrorBack = "errorBack", e7.queryErrorClear = "errorClearQuery", e7.queryErrorRetry = "errorRetry", e7.recommendation = "recommendation", e7.recommendationInterfaceLoad = "recommendationInterfaceLoad", e7.recommendationOpen = "recommendationOpen", e7.likeSmartSnippet = "likeSmartSnippet", e7.dislikeSmartSnippet = "dislikeSmartSnippet", e7.expandSmartSnippet = "expandSmartSnippet", e7.collapseSmartSnippet = "collapseSmartSnippet", e7.openSmartSnippetFeedbackModal = "openSmartSnippetFeedbackModal", e7.closeSmartSnippetFeedbackModal = "closeSmartSnippetFeedbackModal", e7.sendSmartSnippetReason = "sendSmartSnippetReason", e7.expandSmartSnippetSuggestion = "expandSmartSnippetSuggestion", e7.collapseSmartSnippetSuggestion = "collapseSmartSnippetSuggestion", e7.showMoreSmartSnippetSuggestion = "showMoreSmartSnippetSuggestion", e7.showLessSmartSnippetSuggestion = "showLessSmartSnippetSuggestion", e7.openSmartSnippetSource = "openSmartSnippetSource", e7.openSmartSnippetSuggestionSource = "openSmartSnippetSuggestionSource", e7.openSmartSnippetInlineLink = "openSmartSnippetInlineLink", e7.openSmartSnippetSuggestionInlineLink = "openSmartSnippetSuggestionInlineLink", e7.recentQueryClick = "recentQueriesClick", e7.clearRecentQueries = "clearRecentQueries", e7.recentResultClick = "recentResultClick", e7.clearRecentResults = "clearRecentResults", e7.noResultsBack = "noResultsBack", e7.showMoreFoldedResults = "showMoreFoldedResults", e7.showLessFoldedResults = "showLessFoldedResults", e7.copyToClipboard = "copyToClipboard", e7.caseSendEmail = "Case.SendEmail", e7.feedItemTextPost = "FeedItem.TextPost", e7.caseAttach = "caseAttach", e7.caseDetach = "caseDetach", e7.retryGeneratedAnswer = "retryGeneratedAnswer", e7.likeGeneratedAnswer = "likeGeneratedAnswer", e7.dislikeGeneratedAnswer = "dislikeGeneratedAnswer", e7.openGeneratedAnswerSource = "openGeneratedAnswerSource", e7.generatedAnswerStreamEnd = "generatedAnswerStreamEnd", e7.generatedAnswerSourceHover = "generatedAnswerSourceHover", e7.generatedAnswerCopyToClipboard = "generatedAnswerCopyToClipboard", e7.generatedAnswerHideAnswers = "generatedAnswerHideAnswers", e7.generatedAnswerShowAnswers = "generatedAnswerShowAnswers", e7.generatedAnswerExpand = "generatedAnswerExpand", e7.generatedAnswerCollapse = "generatedAnswerCollapse", e7.generatedAnswerFeedbackSubmit = "generatedAnswerFeedbackSubmit", e7.rephraseGeneratedAnswer = "rephraseGeneratedAnswer", e7.generatedAnswerFeedbackSubmitV2 = "generatedAnswerFeedbackSubmitV2", e7.generatedAnswerCitationClick = "generatedAnswerCitationClick";
})(E2 || (E2 = {}));
var Rh2 = { [E2.triggerNotify]: "queryPipelineTriggers", [E2.triggerExecute]: "queryPipelineTriggers", [E2.triggerQuery]: "queryPipelineTriggers", [E2.triggerRedirect]: "queryPipelineTriggers", [E2.queryError]: "errors", [E2.queryErrorBack]: "errors", [E2.queryErrorClear]: "errors", [E2.queryErrorRetry]: "errors", [E2.pagerNext]: "getMoreResults", [E2.pagerPrevious]: "getMoreResults", [E2.pagerNumber]: "getMoreResults", [E2.pagerResize]: "getMoreResults", [E2.pagerScrolling]: "getMoreResults", [E2.facetSearch]: "facet", [E2.facetShowLess]: "facet", [E2.facetShowMore]: "facet", [E2.recommendation]: "recommendation", [E2.likeSmartSnippet]: "smartSnippet", [E2.dislikeSmartSnippet]: "smartSnippet", [E2.expandSmartSnippet]: "smartSnippet", [E2.collapseSmartSnippet]: "smartSnippet", [E2.openSmartSnippetFeedbackModal]: "smartSnippet", [E2.closeSmartSnippetFeedbackModal]: "smartSnippet", [E2.sendSmartSnippetReason]: "smartSnippet", [E2.expandSmartSnippetSuggestion]: "smartSnippetSuggestions", [E2.collapseSmartSnippetSuggestion]: "smartSnippetSuggestions", [E2.showMoreSmartSnippetSuggestion]: "smartSnippetSuggestions", [E2.showLessSmartSnippetSuggestion]: "smartSnippetSuggestions", [E2.clearRecentQueries]: "recentQueries", [E2.recentResultClick]: "recentlyClickedDocuments", [E2.clearRecentResults]: "recentlyClickedDocuments", [E2.showLessFoldedResults]: "folding", [E2.caseDetach]: "case", [E2.likeGeneratedAnswer]: "generatedAnswer", [E2.dislikeGeneratedAnswer]: "generatedAnswer", [E2.openGeneratedAnswerSource]: "generatedAnswer", [E2.generatedAnswerStreamEnd]: "generatedAnswer", [E2.generatedAnswerSourceHover]: "generatedAnswer", [E2.generatedAnswerCopyToClipboard]: "generatedAnswer", [E2.generatedAnswerHideAnswers]: "generatedAnswer", [E2.generatedAnswerShowAnswers]: "generatedAnswer", [E2.generatedAnswerExpand]: "generatedAnswer", [E2.generatedAnswerCollapse]: "generatedAnswer", [E2.generatedAnswerFeedbackSubmit]: "generatedAnswer", [E2.generatedAnswerFeedbackSubmitV2]: "generatedAnswer", [Ir2.expandToFullUI]: "interface", [Ir2.openUserActions]: "User Actions", [Ir2.showPrecedingSessions]: "User Actions", [Ir2.showFollowingSessions]: "User Actions", [Ir2.clickViewedDocument]: "User Actions", [Ir2.clickPageView]: "User Actions", [Ir2.createArticle]: "createArticle" };
var Go2 = class {
  constructor() {
    this.runtime = new Jc2(), this.currentVisitorId = "";
  }
  getPayload() {
    return Promise.resolve();
  }
  getParameters() {
    return Promise.resolve();
  }
  makeEvent(t) {
    return Promise.resolve({ eventType: t, payload: null, log: () => Promise.resolve() });
  }
  sendEvent() {
    return Promise.resolve();
  }
  makeSearchEvent() {
    return this.makeEvent(ne2.search);
  }
  sendSearchEvent() {
    return Promise.resolve();
  }
  makeClickEvent() {
    return this.makeEvent(ne2.click);
  }
  sendClickEvent() {
    return Promise.resolve();
  }
  makeCustomEvent() {
    return this.makeEvent(ne2.custom);
  }
  sendCustomEvent() {
    return Promise.resolve();
  }
  makeViewEvent() {
    return this.makeEvent(ne2.view);
  }
  sendViewEvent() {
    return Promise.resolve();
  }
  getVisit() {
    return Promise.resolve({ id: "", visitorId: "" });
  }
  getHealth() {
    return Promise.resolve({ status: "" });
  }
  registerBeforeSendEventHook() {
  }
  registerAfterSendEventHook() {
  }
  addEventTypeMapping() {
  }
  get version() {
    return qh2;
  }
};
function DI2(e7) {
  let t = "";
  return e7.filter((r) => {
    let n = r !== t;
    return t = r, n;
  });
}
function VI(e7) {
  return e7.map((t) => t.replace(/;/g, ""));
}
function Lh2(e7) {
  let r = e7.join(";");
  return r.length <= 256 ? r : Lh2(e7.slice(1));
}
var bh2 = (e7) => {
  let t = VI(e7), r = DI2(t);
  return Lh2(r);
};
function vh(e7) {
  let t = typeof e7.partialQueries == "string" ? e7.partialQueries : bh2(e7.partialQueries), r = typeof e7.suggestions == "string" ? e7.suggestions : bh2(e7.suggestions);
  return Object.assign(Object.assign({}, e7), { partialQueries: t, suggestions: r });
}
var Zc2 = class {
  constructor(t, r) {
    this.opts = t, this.provider = r;
    let n = t.enableAnalytics === false || Xc2();
    this.coveoAnalyticsClient = n ? new Go2() : new Qt2(t);
  }
  disable() {
    this.coveoAnalyticsClient = new Go2();
  }
  enable() {
    this.coveoAnalyticsClient = new Qt2(this.opts);
  }
  makeInterfaceLoad() {
    return this.makeSearchEvent(E2.interfaceLoad);
  }
  logInterfaceLoad() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeInterfaceLoad()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecommendationInterfaceLoad() {
    return this.makeSearchEvent(E2.recommendationInterfaceLoad);
  }
  logRecommendationInterfaceLoad() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRecommendationInterfaceLoad()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecommendation() {
    return this.makeCustomEvent(E2.recommendation);
  }
  logRecommendation() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRecommendation()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecommendationOpen(t, r) {
    return this.makeClickEvent(E2.recommendationOpen, t, r);
  }
  logRecommendationOpen(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRecommendationOpen(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeStaticFilterClearAll(t) {
    return this.makeSearchEvent(E2.staticFilterClearAll, t);
  }
  logStaticFilterClearAll(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeStaticFilterClearAll(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeStaticFilterSelect(t) {
    return this.makeSearchEvent(E2.staticFilterSelect, t);
  }
  logStaticFilterSelect(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeStaticFilterSelect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeStaticFilterDeselect(t) {
    return this.makeSearchEvent(E2.staticFilterDeselect, t);
  }
  logStaticFilterDeselect(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeStaticFilterDeselect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFetchMoreResults() {
    return this.makeCustomEvent(E2.pagerScrolling, { type: "getMoreResults" });
  }
  logFetchMoreResults() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFetchMoreResults()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeInterfaceChange(t) {
    return this.makeSearchEvent(E2.interfaceChange, t);
  }
  logInterfaceChange(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeInterfaceChange(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDidYouMeanAutomatic() {
    return this.makeSearchEvent(E2.didyoumeanAutomatic);
  }
  logDidYouMeanAutomatic() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeDidYouMeanAutomatic()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDidYouMeanClick() {
    return this.makeSearchEvent(E2.didyoumeanClick);
  }
  logDidYouMeanClick() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeDidYouMeanClick()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeResultsSort(t) {
    return this.makeSearchEvent(E2.resultsSort, t);
  }
  logResultsSort(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeResultsSort(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchboxSubmit() {
    return this.makeSearchEvent(E2.searchboxSubmit);
  }
  logSearchboxSubmit() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSearchboxSubmit()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchboxClear() {
    return this.makeSearchEvent(E2.searchboxClear);
  }
  logSearchboxClear() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSearchboxClear()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchboxAsYouType() {
    return this.makeSearchEvent(E2.searchboxAsYouType);
  }
  logSearchboxAsYouType() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSearchboxAsYouType()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeBreadcrumbFacet(t) {
    return this.makeSearchEvent(E2.breadcrumbFacet, t);
  }
  logBreadcrumbFacet(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeBreadcrumbFacet(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeBreadcrumbResetAll() {
    return this.makeSearchEvent(E2.breadcrumbResetAll);
  }
  logBreadcrumbResetAll() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeBreadcrumbResetAll()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDocumentQuickview(t, r) {
    return this.makeClickEvent(E2.documentQuickview, t, r);
  }
  logDocumentQuickview(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeDocumentQuickview(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDocumentOpen(t, r) {
    return this.makeClickEvent(E2.documentOpen, t, r);
  }
  logDocumentOpen(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeDocumentOpen(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOmniboxAnalytics(t) {
    return this.makeSearchEvent(E2.omniboxAnalytics, vh(t));
  }
  logOmniboxAnalytics(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOmniboxAnalytics(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOmniboxFromLink(t) {
    return this.makeSearchEvent(E2.omniboxFromLink, vh(t));
  }
  logOmniboxFromLink(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOmniboxFromLink(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchFromLink() {
    return this.makeSearchEvent(E2.searchFromLink);
  }
  logSearchFromLink() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSearchFromLink()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerNotify(t) {
    return this.makeCustomEvent(E2.triggerNotify, t);
  }
  logTriggerNotify(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeTriggerNotify(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerExecute(t) {
    return this.makeCustomEvent(E2.triggerExecute, t);
  }
  logTriggerExecute(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeTriggerExecute(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerQuery() {
    return this.makeCustomEvent(E2.triggerQuery, { query: this.provider.getSearchEventRequestPayload().queryText }, "queryPipelineTriggers");
  }
  logTriggerQuery() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeTriggerQuery()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeUndoTriggerQuery(t) {
    return this.makeSearchEvent(E2.undoTriggerQuery, t);
  }
  logUndoTriggerQuery(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeUndoTriggerQuery(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeTriggerRedirect(t) {
    return this.makeCustomEvent(E2.triggerRedirect, Object.assign(Object.assign({}, t), { query: this.provider.getSearchEventRequestPayload().queryText }));
  }
  logTriggerRedirect(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeTriggerRedirect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerResize(t) {
    return this.makeCustomEvent(E2.pagerResize, t);
  }
  logPagerResize(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makePagerResize(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerNumber(t) {
    return this.makeCustomEvent(E2.pagerNumber, t);
  }
  logPagerNumber(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makePagerNumber(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerNext(t) {
    return this.makeCustomEvent(E2.pagerNext, t);
  }
  logPagerNext(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makePagerNext(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerPrevious(t) {
    return this.makeCustomEvent(E2.pagerPrevious, t);
  }
  logPagerPrevious(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makePagerPrevious(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makePagerScrolling() {
    return this.makeCustomEvent(E2.pagerScrolling);
  }
  logPagerScrolling() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makePagerScrolling()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetClearAll(t) {
    return this.makeSearchEvent(E2.facetClearAll, t);
  }
  logFacetClearAll(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetClearAll(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetSearch(t) {
    return this.makeSearchEvent(E2.facetSearch, t);
  }
  logFacetSearch(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetSearch(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetSelect(t) {
    return this.makeSearchEvent(E2.facetSelect, t);
  }
  logFacetSelect(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetSelect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetDeselect(t) {
    return this.makeSearchEvent(E2.facetDeselect, t);
  }
  logFacetDeselect(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetDeselect(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetExclude(t) {
    return this.makeSearchEvent(E2.facetExclude, t);
  }
  logFacetExclude(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetExclude(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetUnexclude(t) {
    return this.makeSearchEvent(E2.facetUnexclude, t);
  }
  logFacetUnexclude(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetUnexclude(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetSelectAll(t) {
    return this.makeSearchEvent(E2.facetSelectAll, t);
  }
  logFacetSelectAll(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetSelectAll(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetUpdateSort(t) {
    return this.makeSearchEvent(E2.facetUpdateSort, t);
  }
  logFacetUpdateSort(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetUpdateSort(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetShowMore(t) {
    return this.makeCustomEvent(E2.facetShowMore, t);
  }
  logFacetShowMore(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetShowMore(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeFacetShowLess(t) {
    return this.makeCustomEvent(E2.facetShowLess, t);
  }
  logFacetShowLess(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeFacetShowLess(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryError(t) {
    return this.makeCustomEvent(E2.queryError, t);
  }
  logQueryError(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeQueryError(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryErrorBack() {
    return w2(this, void 0, void 0, function* () {
      let t = yield this.makeCustomEvent(E2.queryErrorBack);
      return { description: t.description, log: () => w2(this, void 0, void 0, function* () {
        return yield t.log({ searchUID: this.provider.getSearchUID() }), this.logSearchEvent(E2.queryErrorBack);
      }) };
    });
  }
  logQueryErrorBack() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeQueryErrorBack()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryErrorRetry() {
    return w2(this, void 0, void 0, function* () {
      let t = yield this.makeCustomEvent(E2.queryErrorRetry);
      return { description: t.description, log: () => w2(this, void 0, void 0, function* () {
        return yield t.log({ searchUID: this.provider.getSearchUID() }), this.logSearchEvent(E2.queryErrorRetry);
      }) };
    });
  }
  logQueryErrorRetry() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeQueryErrorRetry()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeQueryErrorClear() {
    return w2(this, void 0, void 0, function* () {
      let t = yield this.makeCustomEvent(E2.queryErrorClear);
      return { description: t.description, log: () => w2(this, void 0, void 0, function* () {
        return yield t.log({ searchUID: this.provider.getSearchUID() }), this.logSearchEvent(E2.queryErrorClear);
      }) };
    });
  }
  logQueryErrorClear() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeQueryErrorClear()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeLikeSmartSnippet() {
    return this.makeCustomEvent(E2.likeSmartSnippet);
  }
  logLikeSmartSnippet() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeLikeSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDislikeSmartSnippet() {
    return this.makeCustomEvent(E2.dislikeSmartSnippet);
  }
  logDislikeSmartSnippet() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeDislikeSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeExpandSmartSnippet() {
    return this.makeCustomEvent(E2.expandSmartSnippet);
  }
  logExpandSmartSnippet() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeExpandSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCollapseSmartSnippet() {
    return this.makeCustomEvent(E2.collapseSmartSnippet);
  }
  logCollapseSmartSnippet() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCollapseSmartSnippet()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetFeedbackModal() {
    return this.makeCustomEvent(E2.openSmartSnippetFeedbackModal);
  }
  logOpenSmartSnippetFeedbackModal() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetFeedbackModal()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCloseSmartSnippetFeedbackModal() {
    return this.makeCustomEvent(E2.closeSmartSnippetFeedbackModal);
  }
  logCloseSmartSnippetFeedbackModal() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCloseSmartSnippetFeedbackModal()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSmartSnippetFeedbackReason(t, r) {
    return this.makeCustomEvent(E2.sendSmartSnippetReason, { reason: t, details: r });
  }
  logSmartSnippetFeedbackReason(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSmartSnippetFeedbackReason(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeExpandSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E2.expandSmartSnippetSuggestion, "documentId" in t ? t : { documentId: t });
  }
  logExpandSmartSnippetSuggestion(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeExpandSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCollapseSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E2.collapseSmartSnippetSuggestion, "documentId" in t ? t : { documentId: t });
  }
  logCollapseSmartSnippetSuggestion(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCollapseSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowMoreSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E2.showMoreSmartSnippetSuggestion, t);
  }
  logShowMoreSmartSnippetSuggestion(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeShowMoreSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowLessSmartSnippetSuggestion(t) {
    return this.makeCustomEvent(E2.showLessSmartSnippetSuggestion, t);
  }
  logShowLessSmartSnippetSuggestion(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeShowLessSmartSnippetSuggestion(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetSource(t, r) {
    return this.makeClickEvent(E2.openSmartSnippetSource, t, r);
  }
  logOpenSmartSnippetSource(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetSource(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetSuggestionSource(t, r) {
    return this.makeClickEvent(E2.openSmartSnippetSuggestionSource, t, { contentIDKey: r.documentId.contentIdKey, contentIDValue: r.documentId.contentIdValue }, r);
  }
  makeCopyToClipboard(t, r) {
    return this.makeClickEvent(E2.copyToClipboard, t, r);
  }
  logCopyToClipboard(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCopyToClipboard(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  logOpenSmartSnippetSuggestionSource(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetSuggestionSource(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetInlineLink(t, r) {
    return this.makeClickEvent(E2.openSmartSnippetInlineLink, t, { contentIDKey: r.contentIDKey, contentIDValue: r.contentIDValue }, r);
  }
  logOpenSmartSnippetInlineLink(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetInlineLink(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenSmartSnippetSuggestionInlineLink(t, r) {
    return this.makeClickEvent(E2.openSmartSnippetSuggestionInlineLink, t, { contentIDKey: r.documentId.contentIdKey, contentIDValue: r.documentId.contentIdValue }, r);
  }
  logOpenSmartSnippetSuggestionInlineLink(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOpenSmartSnippetSuggestionInlineLink(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecentQueryClick() {
    return this.makeSearchEvent(E2.recentQueryClick);
  }
  logRecentQueryClick() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRecentQueryClick()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeClearRecentQueries() {
    return this.makeCustomEvent(E2.clearRecentQueries);
  }
  logClearRecentQueries() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeClearRecentQueries()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRecentResultClick(t, r) {
    return this.makeCustomEvent(E2.recentResultClick, { info: t, identifier: r });
  }
  logRecentResultClick(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRecentResultClick(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeClearRecentResults() {
    return this.makeCustomEvent(E2.clearRecentResults);
  }
  logClearRecentResults() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeClearRecentResults()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeNoResultsBack() {
    return this.makeSearchEvent(E2.noResultsBack);
  }
  logNoResultsBack() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeNoResultsBack()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowMoreFoldedResults(t, r) {
    return this.makeClickEvent(E2.showMoreFoldedResults, t, r);
  }
  logShowMoreFoldedResults(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeShowMoreFoldedResults(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeShowLessFoldedResults() {
    return this.makeCustomEvent(E2.showLessFoldedResults);
  }
  logShowLessFoldedResults() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeShowLessFoldedResults()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeEventDescription(t, r) {
    var n;
    return { actionCause: r, customData: (n = t.payload) === null || n === void 0 ? void 0 : n.customData };
  }
  makeCustomEvent(t, r, n = Rh2[t]) {
    return w2(this, void 0, void 0, function* () {
      let o = Object.assign(Object.assign({}, this.provider.getBaseMetadata()), r), a = Object.assign(Object.assign({}, yield this.getBaseEventRequest(o)), { eventType: n, eventValue: t }), i = yield this.coveoAnalyticsClient.makeCustomEvent(a);
      return { description: this.makeEventDescription(i, t), log: ({ searchUID: s }) => i.log({ lastSearchQueryUid: s }) };
    });
  }
  logCustomEvent(t, r, n = Rh2[t]) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCustomEvent(t, r, n)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeCustomEventWithType(t, r, n) {
    return w2(this, void 0, void 0, function* () {
      let o = Object.assign(Object.assign({}, this.provider.getBaseMetadata()), n), a = Object.assign(Object.assign({}, yield this.getBaseEventRequest(o)), { eventType: r, eventValue: t }), i = yield this.coveoAnalyticsClient.makeCustomEvent(a);
      return { description: this.makeEventDescription(i, t), log: ({ searchUID: s }) => i.log({ lastSearchQueryUid: s }) };
    });
  }
  logCustomEventWithType(t, r, n) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeCustomEventWithType(t, r, n)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  logSearchEvent(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeSearchEvent(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeSearchEvent(t, r) {
    return w2(this, void 0, void 0, function* () {
      let n = yield this.getBaseSearchEventRequest(t, r), o = yield this.coveoAnalyticsClient.makeSearchEvent(n);
      return { description: this.makeEventDescription(o, t), log: ({ searchUID: a }) => o.log({ searchQueryUid: a }) };
    });
  }
  makeClickEvent(t, r, n, o) {
    return w2(this, void 0, void 0, function* () {
      let a = Object.assign(Object.assign(Object.assign({}, r), yield this.getBaseEventRequest(Object.assign(Object.assign({}, n), o))), { queryPipeline: this.provider.getPipeline(), actionCause: t }), i = yield this.coveoAnalyticsClient.makeClickEvent(a);
      return { description: this.makeEventDescription(i, t), log: ({ searchUID: s }) => i.log({ searchQueryUid: s }) };
    });
  }
  logClickEvent(t, r, n, o) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeClickEvent(t, r, n, o)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  getBaseSearchEventRequest(t, r) {
    var n, o;
    return w2(this, void 0, void 0, function* () {
      return Object.assign(Object.assign(Object.assign({}, yield this.getBaseEventRequest(Object.assign(Object.assign({}, r), (o = (n = this.provider).getGeneratedAnswerMetadata) === null || o === void 0 ? void 0 : o.call(n)))), this.provider.getSearchEventRequestPayload()), { queryPipeline: this.provider.getPipeline(), actionCause: t });
    });
  }
  getBaseEventRequest(t) {
    return w2(this, void 0, void 0, function* () {
      let r = Object.assign(Object.assign({}, this.provider.getBaseMetadata()), t);
      return Object.assign(Object.assign(Object.assign({}, this.getOrigins()), this.getSplitTestRun()), { customData: r, language: this.provider.getLanguage(), facetState: this.provider.getFacetState ? this.provider.getFacetState() : [], anonymous: this.provider.getIsAnonymous(), clientId: yield this.getClientId() });
    });
  }
  getOrigins() {
    var t, r;
    return { originContext: (r = (t = this.provider).getOriginContext) === null || r === void 0 ? void 0 : r.call(t), originLevel1: this.provider.getOriginLevel1(), originLevel2: this.provider.getOriginLevel2(), originLevel3: this.provider.getOriginLevel3() };
  }
  getClientId() {
    return this.coveoAnalyticsClient instanceof Qt2 ? this.coveoAnalyticsClient.getCurrentVisitorId() : void 0;
  }
  getSplitTestRun() {
    let t = this.provider.getSplitTestRunName ? this.provider.getSplitTestRunName() : "", r = this.provider.getSplitTestRunVersion ? this.provider.getSplitTestRunVersion() : "";
    return Object.assign(Object.assign({}, t && { splitTestRunName: t }), r && { splitTestRunVersion: r });
  }
  makeLikeGeneratedAnswer(t) {
    return this.makeCustomEvent(E2.likeGeneratedAnswer, t);
  }
  logLikeGeneratedAnswer(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeLikeGeneratedAnswer(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeDislikeGeneratedAnswer(t) {
    return this.makeCustomEvent(E2.dislikeGeneratedAnswer, t);
  }
  logDislikeGeneratedAnswer(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeDislikeGeneratedAnswer(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeOpenGeneratedAnswerSource(t) {
    return this.makeCustomEvent(E2.openGeneratedAnswerSource, t);
  }
  logOpenGeneratedAnswerSource(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeOpenGeneratedAnswerSource(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerCitationClick(t, r) {
    return this.makeClickEvent(E2.generatedAnswerCitationClick, Object.assign(Object.assign({}, t), { documentPosition: 1 }), { contentIDKey: r.documentId.contentIdKey, contentIDValue: r.documentId.contentIdValue }, r);
  }
  logGeneratedAnswerCitationClick(t, r) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerCitationClick(t, r)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerSourceHover(t) {
    return this.makeCustomEvent(E2.generatedAnswerSourceHover, t);
  }
  logGeneratedAnswerSourceHover(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerSourceHover(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerCopyToClipboard(t) {
    return this.makeCustomEvent(E2.generatedAnswerCopyToClipboard, t);
  }
  logGeneratedAnswerCopyToClipboard(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerCopyToClipboard(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerHideAnswers(t) {
    return this.makeCustomEvent(E2.generatedAnswerHideAnswers, t);
  }
  logGeneratedAnswerHideAnswers(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerHideAnswers(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerShowAnswers(t) {
    return this.makeCustomEvent(E2.generatedAnswerShowAnswers, t);
  }
  logGeneratedAnswerShowAnswers(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerShowAnswers(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerExpand(t) {
    return this.makeCustomEvent(E2.generatedAnswerExpand, t);
  }
  logGeneratedAnswerExpand(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerExpand(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerCollapse(t) {
    return this.makeCustomEvent(E2.generatedAnswerCollapse, t);
  }
  logGeneratedAnswerCollapse(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerCollapse(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerFeedbackSubmit(t) {
    return this.makeCustomEvent(E2.generatedAnswerFeedbackSubmit, t);
  }
  logGeneratedAnswerFeedbackSubmit(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerFeedbackSubmit(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerFeedbackSubmitV2(t) {
    return this.makeCustomEvent(E2.generatedAnswerFeedbackSubmitV2, t);
  }
  logGeneratedAnswerFeedbackSubmitV2(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerFeedbackSubmitV2(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRephraseGeneratedAnswer(t) {
    return this.makeSearchEvent(E2.rephraseGeneratedAnswer, t);
  }
  logRephraseGeneratedAnswer(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRephraseGeneratedAnswer(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeRetryGeneratedAnswer() {
    return this.makeSearchEvent(E2.retryGeneratedAnswer);
  }
  logRetryGeneratedAnswer() {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeRetryGeneratedAnswer()).log({ searchUID: this.provider.getSearchUID() });
    });
  }
  makeGeneratedAnswerStreamEnd(t) {
    return this.makeCustomEvent(E2.generatedAnswerStreamEnd, t);
  }
  logGeneratedAnswerStreamEnd(t) {
    return w2(this, void 0, void 0, function* () {
      return (yield this.makeGeneratedAnswerStreamEnd(t)).log({ searchUID: this.provider.getSearchUID() });
    });
  }
};
var eu2 = Object.assign({}, ds2);
Object.keys(eu2).map((e7) => eu2[e7]);
var tu2;
(function(e7) {
  e7.click = "click", e7.flowStart = "flowStart";
})(tu2 || (tu2 = {}));
var ut2;
(function(e7) {
  e7.enterInterface = "ticket_create_start", e7.fieldUpdate = "ticket_field_update", e7.fieldSuggestionClick = "ticket_classification_click", e7.documentSuggestionClick = "documentSuggestionClick", e7.documentSuggestionQuickview = "documentSuggestionQuickview", e7.suggestionRate = "suggestion_rate", e7.nextCaseStep = "ticket_next_stage", e7.caseCancelled = "ticket_cancel", e7.caseSolved = "ticket_cancel", e7.caseCreated = "ticket_create";
})(ut2 || (ut2 = {}));
var ru;
(function(e7) {
  e7.quit = "Quit", e7.solved = "Solved";
})(ru || (ru = {}));
var Kr2 = () => "default";
var NI = (e7) => {
  let t = e7.configuration.search.locale.split("-")[0];
  return !t || t.length !== 2 ? "en" : t;
};
var Zn2 = class {
  constructor(t) {
    this.getState = t;
    Ce2(this, "state");
    this.state = t();
  }
  getLanguage() {
    return NI(this.state);
  }
  getBaseMetadata() {
    let { context: t, configuration: r } = this.state, n = t?.contextValues || {}, o = {};
    for (let [a, i] of Object.entries(n)) {
      let s = `context_${a}`;
      o[s] = i;
    }
    return r.analytics.analyticsMode === "legacy" && (o.coveoHeadlessVersion = Jn2), o;
  }
  getOriginContext() {
    return this.state.configuration.analytics.originContext;
  }
  getOriginLevel1() {
    return this.state.searchHub || Kr2();
  }
  getOriginLevel2() {
    return this.state.configuration.analytics.originLevel2;
  }
  getOriginLevel3() {
    return this.state.configuration.analytics.originLevel3;
  }
  getIsAnonymous() {
    return this.state.configuration.analytics.anonymous;
  }
};
var Bh = (e7) => new Qt2(e7).getCurrentVisitorId();
var dt2 = new kh2.HistoryStore();
var fs2 = (e7, t) => typeof t == "function" ? (...r) => {
  let n = Hi2(r[0]);
  try {
    return t.apply(t, r);
  } catch (o) {
    return e7.error(o, "Error in analytics preprocessRequest. Returning original request."), n;
  }
} : void 0;
var gs2 = (e7, t) => (...r) => {
  let n = Hi2(r[1]);
  try {
    return t.apply(t, r);
  } catch (o) {
    return e7.error(o, "Error in analytics hook. Returning original request."), n;
  }
};
function Wo2() {
  return { desiredCount: 5, numberOfValues: 8, set: {} };
}
function ze2(e7) {
  let { activeValue: t, ancestryMap: r } = LI(e7);
  return t ? BI2(t, r) : [];
}
function LI(e7) {
  let t = [...e7], r = /* @__PURE__ */ new Map();
  for (; t.length > 0; ) {
    let n = t.shift();
    if (n.state === "selected")
      return { activeValue: n, ancestryMap: r };
    if (r)
      for (let o of n.children)
        r.set(o, n);
    t.unshift(...n.children);
  }
  return {};
}
function BI2(e7, t) {
  let r = [];
  if (!e7)
    return [];
  let n = e7;
  do
    r.unshift(n), n = t.get(n);
  while (n);
  return r;
}
var Pm2 = (e7, t) => e7.categoryFacetSet[t]?.request;
var wm2 = (e7, t) => {
  let r = Pm2(e7, t);
  return ze2(r?.currentValues ?? []);
};
function Ho2() {
  return {};
}
function Gh2(e7) {
  return { request: e7 };
}
function zo2() {
  return {};
}
function Wh2(e7) {
  return { request: e7 };
}
function Ko2() {
  return {};
}
function Hh2(e7) {
  return { request: e7, hasBreadcrumbs: true };
}
function Yo() {
  return {};
}
function rt2(e7) {
  return { facetSet: e7.facetSet ?? Yo(), categoryFacetSet: e7.categoryFacetSet ?? Ho2(), dateFacetSet: e7.dateFacetSet ?? zo2(), numericFacetSet: e7.numericFacetSet ?? Ko2(), automaticFacetSet: e7.automaticFacetSet ?? Wo2() };
}
var Im2 = (e7) => {
  let t = [];
  return $I2(e7).forEach((r, n) => {
    let o = Xh(e7, r.facetId), a = KI(r, n + 1);
    if (jI2(r)) {
      if (!!!wm2(e7, r.facetId).length)
        return;
      t.push({ ...a, ...HI2(e7, r.facetId), facetType: o, state: "selected" });
      return;
    }
    r.currentValues.forEach((i, s) => {
      if (i.state === "idle")
        return;
      let c = zh2(i, s + 1, o), u = _I2(r) ? Kh2(i) : WI2(i);
      t.push({ ...a, ...c, ...u });
    });
  }), GI2(e7).forEach((r, n) => {
    let o = zI(r, n + 1);
    r.values.forEach((a, i) => {
      if (a.state === "idle")
        return;
      let s = zh2(a, i + 1, "specific"), c = Kh2(a);
      t.push({ ...o, ...s, ...c });
    });
  }), t;
};
var _I2 = (e7) => e7.type === "specific";
var jI2 = (e7) => e7.type === "hierarchical";
var $I2 = (e7) => [...Object.values(e7.facetSet), ...Object.values(e7.categoryFacetSet), ...Object.values(e7.dateFacetSet), ...Object.values(e7.numericFacetSet)].map((t) => t.request);
var GI2 = (e7) => [...Object.values(e7.automaticFacetSet.set)].map((t) => t.response);
var zh2 = (e7, t, r) => ({ state: e7.state, valuePosition: t, facetType: r });
var WI2 = (e7) => ({ displayValue: `${e7.start}..${e7.end}`, value: `${e7.start}..${e7.end}`, start: e7.start, end: e7.end, endInclusive: e7.endInclusive });
var Kh2 = (e7) => ({ displayValue: e7.value, value: e7.value });
var Yh2 = (e7, t) => wm2(e7, t).map((n) => n.value).join(";");
var HI2 = (e7, t) => {
  let n = Yh2(e7, t);
  return { value: n, valuePosition: 1, displayValue: n };
};
var zI = (e7, t) => ({ title: Em(e7.field, e7.field), field: e7.field, id: e7.field, facetPosition: t });
var KI = (e7, t) => ({ title: Em(e7.field, e7.facetId), field: e7.field, id: e7.facetId, facetPosition: t });
var Em = (e7, t) => `${e7}_${t}`;
var Jh2 = (e7, t) => e7.facetSet[t]?.request || e7.categoryFacetSet[t]?.request || e7.dateFacetSet[t]?.request || e7.numericFacetSet[t]?.request || e7.automaticFacetSet.set[t]?.response;
var Xh = (e7, t) => {
  let r = Jh2(e7, t);
  return r ? r.type : "specific";
};
var Fe2 = () => ({ q: "", enableQuerySyntax: false });
var ou2 = ((r) => (r.Ascending = "ascending", r.Descending = "descending", r))(ou2 || {});
var Zo = ((a) => (a.Relevancy = "relevancy", a.QRE = "qre", a.Date = "date", a.Field = "field", a.NoSort = "nosort", a))(Zo || {});
var Er2 = (e7) => {
  if (isArray2(e7))
    return e7.map((t) => Er2(t)).join(",");
  switch (e7.by) {
    case "relevancy":
    case "qre":
    case "nosort":
      return e7.by;
    case "date":
      return `date ${e7.order}`;
    case "field":
      return `@${e7.field} ${e7.order}`;
    default:
      return "";
  }
};
var ys2 = () => ({ by: "relevancy" });
function pt2() {
  return Er2(ys2());
}
var Cs3 = class Cs4 extends Zn2 {
  constructor() {
    super(...arguments);
    Ce2(this, "getFacetRequest", (r) => this.state.facetSet?.[r]?.request || this.state.categoryFacetSet?.[r]?.request || this.state.dateFacetSet?.[r]?.request || this.state.numericFacetSet?.[r]?.request || this.state.automaticFacetSet?.set[r]?.response);
  }
  getFacetState() {
    return Im2(rt2(this.getState()));
  }
  getPipeline() {
    return this.state.pipeline || this.state.search?.response.pipeline || Cs4.fallbackPipelineName;
  }
  getSearchEventRequestPayload() {
    return { queryText: this.queryText, responseTime: this.responseTime, results: this.resultURIs, numberOfResults: this.numberOfResults };
  }
  getSearchUID() {
    let r = this.getState();
    return r.search?.searchResponseId || r.search?.response.searchUid || Ze().response.searchUid;
  }
  getSplitTestRunName() {
    return this.state.search?.response.splitTestRun;
  }
  getSplitTestRunVersion() {
    let r = !!this.getSplitTestRunName(), n = this.state.search?.response.pipeline || this.state.pipeline || Cs4.fallbackPipelineName;
    return r ? n : void 0;
  }
  getBaseMetadata() {
    let r = this.getState(), n = super.getBaseMetadata(), o = r.search?.response?.extendedResults?.generativeQuestionAnsweringId;
    return o && (n.generativeQuestionAnsweringId = o), n;
  }
  getFacetMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: a, facetValue: n, facetTitle: `${a}_${r}` };
  }
  getFacetClearAllMetadata(r) {
    let o = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: o, facetTitle: `${o}_${r}` };
  }
  getFacetUpdateSortMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: a, criteria: n, facetTitle: `${a}_${r}` };
  }
  getRangeBreadcrumbFacetMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), facetId: r, facetField: a, facetRangeEnd: n.end, facetRangeEndInclusive: n.endInclusive, facetRangeStart: n.start, facetTitle: `${a}_${r}` };
  }
  getResultSortMetadata() {
    return { ...this.getBaseMetadata(), resultsSortBy: this.state.sortCriteria ?? pt2() };
  }
  getStaticFilterToggleMetadata(r, n) {
    return { ...this.getBaseMetadata(), staticFilterId: r, staticFilterValue: n };
  }
  getStaticFilterClearAllMetadata(r) {
    return { ...this.getBaseMetadata(), staticFilterId: r };
  }
  getUndoTriggerQueryMetadata(r) {
    return { ...this.getBaseMetadata(), undoneQuery: r };
  }
  getCategoryBreadcrumbFacetMetadata(r, n) {
    let a = this.getFacetRequest(r)?.field ?? "";
    return { ...this.getBaseMetadata(), categoryFacetId: r, categoryFacetField: a, categoryFacetPath: n, categoryFacetTitle: `${a}_${r}` };
  }
  getOmniboxAnalyticsMetadata(r, n) {
    let o = this.state.querySuggest && this.state.querySuggest[r], a = o.completions.map((u) => u.expression), i = o.partialQueries.length - 1, s = o.partialQueries[i] || "", c = o.responseId;
    return { ...this.getBaseMetadata(), suggestionRanking: a.indexOf(n), partialQuery: s, partialQueries: o.partialQueries.length > 0 ? o.partialQueries : "", suggestions: a.length > 0 ? a : "", querySuggestResponseId: c };
  }
  getInterfaceChangeMetadata() {
    return { ...this.getBaseMetadata(), interfaceChangeTo: this.state.configuration.analytics.originLevel2 };
  }
  getOmniboxFromLinkMetadata(r) {
    return { ...this.getBaseMetadata(), ...r };
  }
  getGeneratedAnswerMetadata() {
    let r = this.getState(), n = {};
    return r.generatedAnswer?.isVisible !== void 0 && (n.showGeneratedAnswer = r.generatedAnswer.isVisible), n;
  }
  get resultURIs() {
    return this.results?.map((r) => ({ documentUri: r.uri, documentUriHash: r.raw.urihash }));
  }
  get results() {
    return this.state.search?.response.results;
  }
  get queryText() {
    return this.state.query?.q || Fe2().q;
  }
  get responseTime() {
    return this.state.search?.duration || Ze().duration;
  }
  get numberOfResults() {
    return this.state.search?.response.totalCountFiltered || Ze().response.totalCountFiltered;
  }
};
Ce2(Cs3, "fallbackPipelineName", "default");
var Yr2 = Cs3;
var ty2 = ({ logger: e7, getState: t, analyticsClientMiddleware: r = (a, i) => i, preprocessRequest: n, provider: o = new Yr2(t) }) => {
  let a = t(), i = a.configuration.accessToken, s = a.configuration.analytics.apiBaseUrl ?? Me2(a.configuration.organizationId, a.configuration.environment, "analytics"), c = a.configuration.analytics.runtimeEnvironment, u = a.configuration.analytics.enabled, l = new Zc2({ token: i, endpoint: s, runtimeEnvironment: c, preprocessRequest: fs2(e7, n), beforeSendHooks: [gs2(e7, r), (m, p) => (e7.info({ ...p, type: m, endpoint: s, token: i }, "Analytics request"), p)] }, o);
  return u || l.disable(), l;
};
var Dm = () => {
  let t = dt2.getHistory().reverse().find((r) => r.name === "PageView" && r.value);
  return t ? t.value : "";
};
function au(e7) {
  let t = ry2(e7), r = [e7, ...t].filter((o) => o.parentResult).map((o) => o.parentResult);
  return Kg([e7, ...t, ...r], (o) => o.uniqueId);
}
function ry2(e7) {
  return e7.childResults ? e7.childResults.flatMap((t) => [t, ...ry2(t)]) : [];
}
var Tr2 = () => "";
function ny2(e7, t) {
  return { ...new Yr2(t).getBaseMetadata(), actionCause: e7, type: e7 };
}
function tE2(e7) {
  return Object.assign(e7, { instantlyCallable: true });
}
function rE2(e7, t) {
  let r = (a) => tE2(W2(e7, a)), n = r(async (a, { getState: i, extra: s }) => {
    let { analyticsClientMiddleware: c, preprocessRequest: u, logger: l } = s;
    return await (await t({ getState: i, analyticsClientMiddleware: c, preprocessRequest: u, logger: l })).log({ state: i(), extra: s });
  });
  return Object.assign(n, { prepare: async ({ getState: a, analyticsClientMiddleware: i, preprocessRequest: s, logger: c }) => {
    let { description: u, log: l } = await t({ getState: a, analyticsClientMiddleware: i, preprocessRequest: s, logger: c });
    return { description: u, action: r(async (m, { getState: p, extra: d }) => await l({ state: p(), extra: d })) };
  } }), n;
}
var oy = (e7, t, r) => {
  function n(...o) {
    let a = o.length === 1 ? { ...o[0], __legacy__getBuilder: t(o[0].__legacy__getBuilder), analyticsConfigurator: e7, providerClass: r } : { prefix: o[0], __legacy__getBuilder: t(o[1]), __legacy__provider: o[2], analyticsConfigurator: e7, providerClass: r };
    return aE(a);
  }
  return n;
};
var nE2 = (e7) => e7.configuration.analytics.analyticsMode === "legacy";
var oE2 = (e7) => e7.configuration.analytics.analyticsMode === "next";
var aE = ({ prefix: e7, __legacy__getBuilder: t, __legacy__provider: r, analyticsPayloadBuilder: n, analyticsType: o, analyticsConfigurator: a, providerClass: i }) => (r ?? (r = (s) => new i(s)), rE2(e7, async ({ getState: s, analyticsClientMiddleware: c, preprocessRequest: u, logger: l }) => {
  let m = [], p = { log: async ({ state: g }) => {
    for (let C of m)
      await C(g);
  } }, d = s(), f = a({ getState: s, logger: l, analyticsClientMiddleware: c, preprocessRequest: u, provider: r(s) }), A = await t(f, s());
  p.description = A?.description, m.push(async (g) => {
    nE2(g) && await iE(A, r, g, l, f.coveoAnalyticsClient);
  });
  let { emit: S } = Bo2(d);
  return m.push(async (g) => {
    if (oE2(g) && o && n) {
      let C = n(g);
      await gE(S, o, C);
    }
  }), p;
}));
async function iE(e7, t, r, n, o) {
  t(() => r);
  let a = await e7?.log({ searchUID: t(() => r).getSearchUID() });
  n.info({ client: o, response: a }, "Analytics response");
}
var L2 = oy(ty2, (e7) => e7, Yr2);
var sy = { urihash: new StringValue2(), sourcetype: new StringValue2(), permanentid: new StringValue2() };
var su = { uniqueId: V2, raw: new RecordValue2({ values: sy }), title: V2, uri: V2, clickUri: V2, rankingModifier: new StringValue2({ required: false, emptyAllowed: true }) };
function lE(e7) {
  return Object.assign({}, ...Object.keys(sy).map((t) => ({ [t]: e7[t] })));
}
function dE(e7) {
  return Object.assign({}, ...Object.keys(su).map((t) => ({ [t]: e7[t] })), { raw: lE(e7.raw) });
}
var Ke2 = (e7) => new Schema2(su).validate(dE(e7));
async function gE(e7, t, r) {
  await e7(t, r);
}
var Jr = () => L2("analytics/interface/change", (e7, t) => e7.makeInterfaceChange({ interfaceChangeTo: t.configuration.analytics.originLevel2 }));
var ea2 = () => ({ actionCause: "interfaceChange" });
var Mm2 = () => de2;
var Sy = () => V2;
var Ut2 = h3("configuration/updateBasicConfiguration", (e7) => x(e7, { accessToken: de2, environment: new StringValue2({ required: false, constrainTo: ["prod", "hipaa", "stg", "dev"] }), organizationId: de2 }));
var mt2 = h3("configuration/updateSearchConfiguration", (e7) => x(e7, { proxyBaseUrl: new StringValue2({ required: false, url: true }), pipeline: new StringValue2({ required: false, emptyAllowed: true }), searchHub: de2, timezone: de2, locale: de2, authenticationProviders: new ArrayValue2({ required: false, each: V2 }) }));
var CE = { enabled: new BooleanValue2({ default: true }), originContext: Mm2(), originLevel2: Mm2(), originLevel3: Mm2(), proxyBaseUrl: new StringValue2({ required: false, url: true }), runtimeEnvironment: new Value2(), anonymous: new BooleanValue2({ default: false }), deviceId: de2, userDisplayName: de2, documentLocation: de2, trackingId: de2, analyticsMode: new StringValue2({ constrainTo: ["legacy", "next"], required: false, default: "next" }), source: new RecordValue2({ options: { required: false }, values: mh2.reduce((e7, t) => (e7[t] = IS, e7), {}) }) };
var Xr2 = h3("configuration/updateAnalyticsConfiguration", (e7) => x(e7, CE));
var ta2 = h3("configuration/analytics/disable");
var ra2 = h3("configuration/analytics/enable");
var du2 = h3("configuration/analytics/originlevel2", (e7) => x(e7, { originLevel2: Sy() }));
var pu2 = h3("configuration/analytics/originlevel3", (e7) => x(e7, { originLevel3: Sy() }));
var mu = { q: new StringValue2(), enableQuerySyntax: new BooleanValue2(), aq: new StringValue2(), cq: new StringValue2(), firstResult: new NumberValue2({ min: 0 }), numberOfResults: new NumberValue2({ min: 0 }), sortCriteria: new StringValue2(), f: new RecordValue2(), fExcluded: new RecordValue2(), cf: new RecordValue2(), nf: new RecordValue2(), mnf: new RecordValue2(), df: new RecordValue2(), debug: new BooleanValue2(), sf: new RecordValue2(), tab: new StringValue2(), af: new RecordValue2() };
var ce2 = h3("searchParameters/restore", (e7) => x(e7, mu));
var Fs = h3("searchParameters/restoreTab", (e7) => x(e7, V2));
var en2 = h3("debug/enable");
var na = h3("debug/disable");
var tn2 = () => false;
$2(tn2(), (e7) => {
  e7.addCase(en2, () => true).addCase(na, () => false).addCase(ce2, (t, r) => r.payload.debug ?? t);
});
var Qm2 = h3("history/undo");
var Lm2 = h3("history/redo");
var nt2 = h3("history/snapshot");
W2("history/back", async (e7, { dispatch: t }) => {
  t(Qm2()), await t(ae2());
});
W2("history/forward", async (e7, { dispatch: t }) => {
  t(Lm2()), await t(ae2());
});
var ae2 = W2("history/change", async (e7, { getState: t }) => t().history.present);
var aa = h3("pipeline/set", (e7) => x(e7, new StringValue2({ required: true, emptyAllowed: true })));
$2(Tr2(), (e7) => {
  e7.addCase(aa, (t, r) => r.payload).addCase(ae2.fulfilled, (t, r) => r.payload?.pipeline ?? t).addCase(mt2, (t, r) => r.payload.pipeline || t);
});
var sa = h3("searchHub/set", (e7) => x(e7, new StringValue2({ required: true, emptyAllowed: true })));
$2(Kr2(), (e7) => {
  e7.addCase(sa, (t, r) => r.payload).addCase(ae2.fulfilled, (t, r) => r.payload?.searchHub ?? t).addCase(mt2, (t, r) => r.payload.searchHub || t);
});
var Se2 = h3("breadcrumb/deselectAll");
var _t2 = h3("breadcrumb/deselectAllNonBreadcrumbs");
var ft2 = h3("facet/updateFacetAutoSelection", (e7) => x(e7, { allow: new BooleanValue2({ required: true }) }));
var bs2 = class extends Yr2 {
  constructor(r) {
    super(r);
    this.getState = r;
  }
  get activeInstantResultQuery() {
    let r = this.getState().instantResults;
    for (let n in r)
      for (let o in r[n].cache)
        if (r[n].cache[o].isActive)
          return r[n].q;
    return null;
  }
  get activeInstantResultCache() {
    let r = this.getState().instantResults;
    for (let n in r)
      for (let o in r[n].cache)
        if (r[n].cache[o].isActive)
          return r[n].cache[o];
    return null;
  }
  get results() {
    return this.activeInstantResultCache?.results;
  }
  get queryText() {
    return this.activeInstantResultQuery ?? Fe2().q;
  }
  get responseTime() {
    return this.activeInstantResultCache?.duration ?? Ze().duration;
  }
  get numberOfResults() {
    return this.activeInstantResultCache?.totalCountFiltered ?? Ze().response.totalCountFiltered;
  }
  getSearchUID() {
    return this.activeInstantResultCache?.searchUid || super.getSearchUID();
  }
};
var xy2 = () => L2("analytics/instantResult/searchboxAsYouType", (e7) => e7.makeSearchboxAsYouType(), (e7) => new bs2(e7));
var Ay2 = () => ({ actionCause: "searchboxAsYouType" });
var Bm2 = { id: V2 };
var RE = { ...Bm2, q: se };
var ua2 = h3("instantResults/register", (e7) => x(e7, Bm2));
var jt2 = h3("instantResults/updateQuery", (e7) => x(e7, RE));
var la2 = h3("instantResults/clearExpired", (e7) => x(e7, Bm2));
var gu2 = new NumberValue2({ required: true, min: 0 });
var da2 = h3("pagination/registerNumberOfResults", (e7) => x(e7, gu2));
var pa2 = h3("pagination/updateNumberOfResults", (e7) => x(e7, gu2));
var ma2 = h3("pagination/registerPage", (e7) => x(e7, gu2));
var gt2 = h3("pagination/updatePage", (e7) => x(e7, gu2));
var fa2 = h3("pagination/nextPage");
var ga2 = h3("pagination/previousPage");
var Le2 = h3("query/updateQuery", (e7) => x(e7, { q: new StringValue2(), enableQuerySyntax: new BooleanValue2() }));
var Sa2 = (e7, t, r) => ({ analytics: { clientId: t.clientId, clientTimestamp: (/* @__PURE__ */ new Date()).toISOString(), documentReferrer: t.referrer, documentLocation: t.location, originContext: e7.originContext, ...r && { actionCause: r.actionCause }, ...r && { customData: r.customData }, ...e7.userDisplayName && { userDisplayName: e7.userDisplayName }, ...e7.deviceId && { deviceId: e7.deviceId }, ...e7.trackingId && { trackingId: e7.trackingId }, capture: t.capture ?? t.clientId !== "", source: Hr2(e7) } });
var ha2 = (e7, t, r) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: e7.configuration.search.apiBaseUrl ?? ve2(e7.configuration.organizationId, e7.configuration.environment), locale: e7.configuration.search.locale, debug: e7.debug, tab: e7.configuration.analytics.originLevel2, referrer: t.referrer, timezone: e7.configuration.search.timezone, ...e7.advancedSearchQueries?.aq && { aq: e7.advancedSearchQueries.aq }, ...e7.advancedSearchQueries?.cq && { cq: e7.advancedSearchQueries.cq }, ...e7.advancedSearchQueries?.lq && { lq: e7.advancedSearchQueries.lq }, ...e7.advancedSearchQueries?.dq && { dq: e7.advancedSearchQueries.dq }, ...e7.context && { context: e7.context.contextValues }, ...e7.fields && !e7.fields.fetchAllFields && { fieldsToInclude: e7.fields.fieldsToInclude }, ...e7.dictionaryFieldContext && { dictionaryFieldContext: e7.dictionaryFieldContext.contextValues }, ...e7.pipeline && { pipeline: e7.pipeline }, ...e7.query && { q: e7.query.q, enableQuerySyntax: e7.query.enableQuerySyntax }, ...e7.searchHub && { searchHub: e7.searchHub }, ...e7.sortCriteria && { sortCriteria: e7.sortCriteria }, ...e7.configuration.analytics.enabled && Sa2(e7.configuration.analytics, t, r), ...e7.excerptLength && !isNullOrUndefined2(e7.excerptLength.length) && { excerptLength: e7.excerptLength.length }, ...e7.configuration.search.authenticationProviders.length && { authentication: e7.configuration.search.authenticationProviders.join(",") } });
var ya2 = async (e7, t) => {
  let r = e7.analyticsMode === "next";
  return { analytics: { clientId: await Bh(e7), clientTimestamp: (/* @__PURE__ */ new Date()).toISOString(), documentReferrer: e7.originLevel3, originContext: e7.originContext, ...t && { actionCause: t.actionCause, customData: t.customData }, ...t && !r && { customData: t.customData }, ...e7.userDisplayName && { userDisplayName: e7.userDisplayName }, ...e7.documentLocation && { documentLocation: e7.documentLocation }, ...e7.deviceId && { deviceId: e7.deviceId }, ...Dm() && { pageId: Dm() }, ...r && e7.trackingId && { trackingId: e7.trackingId }, capture: r, ...r && { source: Hr2(e7) } } };
};
var rn2 = async (e7, t) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: e7.configuration.search.apiBaseUrl ?? ve2(e7.configuration.organizationId, e7.configuration.environment), locale: e7.configuration.search.locale, debug: e7.debug, tab: e7.configuration.analytics.originLevel2, referrer: e7.configuration.analytics.originLevel3, timezone: e7.configuration.search.timezone, ...e7.configuration.analytics.enabled && { actionsHistory: dt2.getHistory() }, ...e7.advancedSearchQueries?.aq && { aq: e7.advancedSearchQueries.aq }, ...e7.advancedSearchQueries?.cq && { cq: e7.advancedSearchQueries.cq }, ...e7.advancedSearchQueries?.lq && { lq: e7.advancedSearchQueries.lq }, ...e7.advancedSearchQueries?.dq && { dq: e7.advancedSearchQueries.dq }, ...e7.context && { context: e7.context.contextValues }, ...e7.fields && !e7.fields.fetchAllFields && { fieldsToInclude: e7.fields.fieldsToInclude }, ...e7.dictionaryFieldContext && { dictionaryFieldContext: e7.dictionaryFieldContext.contextValues }, ...e7.pipeline && { pipeline: e7.pipeline }, ...e7.query && { q: e7.query.q, enableQuerySyntax: e7.query.enableQuerySyntax }, ...e7.searchHub && { searchHub: e7.searchHub }, ...e7.sortCriteria && { sortCriteria: e7.sortCriteria }, ...e7.configuration.analytics.enabled && await ya2(e7.configuration.analytics, t), ...e7.excerptLength && !isNullOrUndefined2(e7.excerptLength.length) && { excerptLength: e7.excerptLength.length }, ...e7.configuration.search.authenticationProviders.length && { authentication: e7.configuration.search.authenticationProviders.join(",") } });
var It2 = () => ({ cq: "", cqWasSet: false, aq: "", aqWasSet: false, lq: "", lqWasSet: false, dq: "", dqWasSet: false, defaultFilters: { cq: "", aq: "", lq: "", dq: "" } });
var Um = () => L2("search/logFetchMoreResults", (e7) => e7.makeFetchMoreResults());
var nn2 = (e7) => L2("search/queryError", (t, r) => t.makeQueryError({ query: r.query?.q || Fe2().q, aq: r.advancedSearchQueries?.aq || It2().aq, cq: r.advancedSearchQueries?.cq || It2().cq, dq: r.advancedSearchQueries?.dq || It2().dq, errorType: e7.type, errorMessage: e7.message }));
var ws2 = Vt2(Su2());
var wy2 = Vt2(Fy2());
var hu2 = Vt2(Su2());
var by = Vt2(Ry2());
hu2.default.extend(by.default);
var vs2 = "YYYY/MM/DD@HH:mm:ss";
var EE = "1401-01-01";
function eo2(e7, t) {
  let r = (0, hu2.default)(e7, t);
  return !r.isValid() && !t ? (0, hu2.default)(e7, vs2) : r;
}
function Ps2(e7) {
  return e7.format(vs2);
}
function yu2(e7, t) {
  let r = eo2(e7, t);
  if (!r.isValid()) {
    let n = ". Please provide a date format string in the configuration options. See https://day.js.org/docs/en/parse/string-format for more information.", o = ` with the format "${t}"`;
    throw new Error(`Could not parse the provided date "${e7}"${t ? o : n}`);
  }
  zm2(r);
}
function zm2(e7) {
  if (e7.isBefore(EE))
    throw new Error(`Date is before year 1401, which is unsupported by the API: ${e7}`);
}
ws2.default.extend(wy2.default);
var Iy2 = ["past", "now", "next"];
var Ey2 = ["minute", "hour", "day", "week", "month", "quarter", "year"];
var OE2 = (e7) => {
  let t = e7 === "now";
  return { amount: new NumberValue2({ required: !t, min: 1 }), unit: new StringValue2({ required: !t, constrainTo: Ey2 }), period: new StringValue2({ required: true, constrainTo: Iy2 }) };
};
function to2(e7) {
  if (typeof e7 == "string" && !$t2(e7))
    throw new Error(`The value "${e7}" is not respecting the relative date format "period-amount-unit"`);
  let t = typeof e7 == "string" ? Km2(e7) : e7;
  new Schema2(OE2(t.period)).validate(t);
  let r = ky2(t), n = JSON.stringify(t);
  if (!r.isValid())
    throw new Error(`Date is invalid: ${n}`);
  zm2(r);
}
function Ty2(e7) {
  let { period: t, amount: r, unit: n } = e7;
  switch (t) {
    case "past":
    case "next":
      return `${t}-${r}-${n}`;
    case "now":
      return t;
  }
}
function ky2(e7) {
  let { period: t, amount: r, unit: n } = e7;
  switch (t) {
    case "past":
      return (0, ws2.default)().subtract(r, n);
    case "next":
      return (0, ws2.default)().add(r, n);
    case "now":
      return (0, ws2.default)();
  }
}
function Is2(e7) {
  return Ps2(ky2(Km2(e7)));
}
function Oy2(e7) {
  return e7.toLocaleLowerCase().split("-");
}
function $t2(e7) {
  let [t, r, n] = Oy2(e7);
  if (t === "now")
    return true;
  if (!Iy2.includes(t) || !Ey2.includes(n))
    return false;
  let o = parseInt(r);
  return !(isNaN(o) || o <= 0);
}
function qy2(e7) {
  return !!e7 && typeof e7 == "object" && "period" in e7;
}
function Km2(e7) {
  let [t, r, n] = Oy2(e7);
  return t === "now" ? { period: "now" } : { period: t, amount: r ? parseInt(r) : void 0, unit: n || void 0 };
}
function Dy2(e7) {
  return e7.type === "dateRange";
}
function Vy2(e7) {
  return `start${e7}`;
}
function Ny(e7) {
  return `end${e7}`;
}
var Ym2 = () => ({ dateFacetValueMap: {} });
function DE2(e7, t, r) {
  let n = e7.start, o = e7.end;
  return $t2(n) && (n = Is2(n), r.dateFacetValueMap[t][Vy2(n)] = e7.start), $t2(o) && (o = Is2(o), r.dateFacetValueMap[t][Ny(o)] = e7.end), { ...e7, start: n, end: o };
}
function Jm2(e7, t) {
  if (Dy2(e7)) {
    let { facetId: r, currentValues: n } = e7;
    return t.dateFacetValueMap[r] = {}, { ...e7, currentValues: n.map((o) => DE2(o, r, t)) };
  }
  return e7;
}
function on2(e7) {
  let t = Ym2();
  return { request: { ...e7, facets: e7.facets?.map((n) => Jm2(n, t)) }, mappings: t };
}
function VE2(e7, t, r) {
  return { ...e7, start: r.dateFacetValueMap[t][Vy2(e7.start)] || e7.start, end: r.dateFacetValueMap[t][Ny(e7.end)] || e7.end };
}
function NE(e7, t) {
  return e7.facetId in t.dateFacetValueMap;
}
function ME(e7, t) {
  return NE(e7, t) ? { ...e7, values: e7.values.map((r) => VE2(r, e7.facetId, t)) } : e7;
}
function Cu2(e7, t) {
  return "success" in e7 ? { success: { ...e7.success, facets: e7.success.facets?.map((n) => ME(n, t)) } } : e7;
}
var Ca2 = h3("didYouMean/enable");
var xu2 = h3("didYouMean/disable");
var xa2 = h3("didYouMean/automaticCorrections/disable");
var Au = h3("didYouMean/automaticCorrections/enable");
var St2 = h3("didYouMean/correction", (e7) => x(e7, V2));
var ro2 = h3("didYouMean/automaticCorrections/mode", (e7) => x(e7, new StringValue2({ constrainTo: ["next", "legacy"], emptyAllowed: false, required: true })));
var Xm2 = () => L2("analytics/didyoumean/automatic", (e7) => e7.makeDidYouMeanAutomatic());
var Qy2 = () => ({ actionCause: "didYouMeanAutomatic" });
function Ru2() {
  return { contextValues: {} };
}
function bu2() {
  return { contextValues: {} };
}
function Zm2() {
  return { enabled: true, tabs: {} };
}
function vu2() {
  return { freezeFacetOrder: false, facets: {} };
}
function Aa2() {
  return [];
}
function ht2() {
  return { firstResult: 0, defaultNumberOfResults: 10, numberOfResults: 10, totalCountFiltered: 0 };
}
function Pu2() {
  return {};
}
function wu2() {
  return {};
}
function Iu2() {
  return {};
}
function Ly2() {
  return Et2({});
}
function Et2(e7) {
  return { context: e7.context || Ru2(), dictionaryFieldContext: e7.dictionaryFieldContext || bu2(), facetSet: e7.facetSet || Yo(), numericFacetSet: e7.numericFacetSet || Ko2(), dateFacetSet: e7.dateFacetSet || zo2(), categoryFacetSet: e7.categoryFacetSet || Ho2(), automaticFacetSet: e7.automaticFacetSet ?? Wo2(), pagination: e7.pagination || ht2(), query: e7.query || Fe2(), tabSet: e7.tabSet || Iu2(), advancedSearchQueries: e7.advancedSearchQueries || It2(), staticFilterSet: e7.staticFilterSet || wu2(), querySet: e7.querySet || Pu2(), sortCriteria: e7.sortCriteria || pt2(), pipeline: e7.pipeline || Tr2(), searchHub: e7.searchHub || Kr2(), facetOptions: e7.facetOptions || vu2(), facetOrder: e7.facetOrder ?? Aa2(), debug: e7.debug ?? tn2() };
}
var Eu = () => L2("analytics/trigger/query", (e7, t) => t.triggers?.queryModification.newQuery ? e7.makeTriggerQuery() : null);
var an2 = h3("trigger/query/ignore", (e7) => x(e7, new StringValue2({ emptyAllowed: true, required: true })));
var Fa2 = h3("trigger/query/modification", (e7) => x(e7, new RecordValue2({ values: { originalQuery: de2, modification: de2 } })));
function sn2(e7) {
  return Object.values(e7).map((t) => t.request);
}
function Es(e7, t) {
  let r = {};
  e7.forEach((a) => r[a.facetId] = a);
  let n = [];
  t.forEach((a) => {
    a in r && (n.push(r[a]), delete r[a]);
  });
  let o = Object.values(r);
  return [...n, ...o];
}
function By(e7) {
  return sn2(e7).map((t) => {
    let n = t.currentValues.some(({ state: o }) => o !== "idle");
    return t.generateAutomaticRanges && !n ? { ...t, currentValues: [] } : t;
  });
}
var ef2 = { alphanumericDescending: { type: "alphanumeric", order: "descending" }, alphanumericNaturalDescending: { type: "alphanumericNatural", order: "descending" } };
function jE2(e7) {
  return sn2(e7).map((t) => {
    let r = ef2[t.sortCriteria];
    return r ? { ...t, sortCriteria: r } : t;
  });
}
function $E2(e7) {
  return [...jE2(e7.facetSet ?? {}), ...By(e7.numericFacetSet ?? {}), ...By(e7.dateFacetSet ?? {}), ...sn2(e7.categoryFacetSet ?? {})];
}
function GE2(e7) {
  return $E2(e7).filter(({ facetId: t }) => e7.facetOptions?.facets[t]?.enabled ?? true);
}
function Du2(e7) {
  return Es(GE2(e7), e7.facetOrder ?? []);
}
var cn2 = async (e7, t) => {
  let r = zE(e7), n = Du2(e7), o = WE2(e7), a = await rn2(e7, t), i = () => e7.pagination ? e7.pagination.firstResult + e7.pagination.numberOfResults > 5e3 ? 5e3 - e7.pagination.firstResult : e7.pagination.numberOfResults : void 0;
  return on2({ ...a, ...e7.didYouMean && { queryCorrection: { enabled: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "next", options: { automaticallyCorrect: e7.didYouMean.automaticallyCorrectQuery ? "whenNoResults" : "never" } }, enableDidYouMean: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "legacy" }, ...r && { cq: r }, ...n.length && { facets: n }, ...e7.pagination && { numberOfResults: i(), firstResult: e7.pagination.firstResult }, ...e7.facetOptions && { facetOptions: { freezeFacetOrder: e7.facetOptions.freezeFacetOrder } }, ...e7.folding?.enabled && { filterField: e7.folding.fields.collection, childField: e7.folding.fields.parent, parentField: e7.folding.fields.child, filterFieldRange: e7.folding.filterFieldRange }, ...e7.automaticFacetSet && { generateAutomaticFacets: { desiredCount: e7.automaticFacetSet.desiredCount, numberOfValues: e7.automaticFacetSet.numberOfValues, currentFacets: o } }, ...e7.generatedAnswer && { pipelineRuleParameters: { mlGenerativeQuestionAnswering: { responseFormat: e7.generatedAnswer.responseFormat, citationsFieldToInclude: e7.generatedAnswer.fieldsToIncludeInCitations } } } });
};
function WE2(e7) {
  let t = e7.automaticFacetSet?.set;
  return t ? Object.values(t).map((r) => r.response).map(HE2).filter((r) => r.currentValues.length > 0) : void 0;
}
function HE2(e7) {
  let { field: t, label: r, values: n } = e7, o = n.filter((a) => a.state === "selected");
  return { field: t, label: r, currentValues: o };
}
function zE(e7) {
  let t = e7.advancedSearchQueries?.cq.trim() || "", n = Object.values(e7.tabSet || {}).find((a) => a.isActive)?.expression.trim() || "", o = KE2(e7);
  return [t, n, ...o].filter((a) => !!a).join(" AND ");
}
function KE2(e7) {
  return Object.values(e7.staticFilterSet || {}).map((r) => {
    let n = r.values.filter((a) => a.state === "selected" && !!a.expression.trim()), o = n.map((a) => a.expression).join(" OR ");
    return n.length > 1 ? `(${o})` : o;
  });
}
var un2 = class {
  constructor(t, r = (n) => {
    this.dispatch(Le2({ q: n }));
  }) {
    this.config = t;
    this.onUpdateQueryForCorrection = r;
  }
  async fetchFromAPI({ mappings: t, request: r }, n) {
    let o = (/* @__PURE__ */ new Date()).getTime(), a = Cu2(await this.extra.apiClient.search(r, n), t), i = (/* @__PURE__ */ new Date()).getTime() - o, s = this.getState().query?.q || "";
    return { response: a, duration: i, queryExecuted: s, requestExecuted: r };
  }
  async process(t) {
    return this.processQueryErrorOrContinue(t) ?? await this.processQueryCorrectionsOrContinue(t) ?? await this.processQueryTriggersOrContinue(t) ?? this.processSuccessResponse(t);
  }
  processQueryErrorOrContinue(t) {
    return we2(t.response) ? (this.dispatch(nn2(t.response.error)), this.rejectWithValue(t.response.error)) : null;
  }
  async processQueryCorrectionsOrContinue(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    if (!n || !r.didYouMean)
      return null;
    let { enableDidYouMean: o, automaticallyCorrectQuery: a } = r.didYouMean, { results: i, queryCorrections: s, queryCorrection: c } = n;
    if (!o || !a)
      return null;
    let u = i.length === 0 && s && s.length !== 0, l = !isNullOrUndefined2(c) && !isNullOrUndefined2(c.correctedQuery);
    if (!u && !l)
      return null;
    let p = u ? await this.processLegacyDidYouMeanAutoCorrection(t) : this.processModernDidYouMeanAutoCorrection(t);
    return this.dispatch(nt2(Et2(this.getState()))), p;
  }
  async processLegacyDidYouMeanAutoCorrection(t) {
    let r = this.getCurrentQuery(), n = this.getSuccessResponse(t);
    if (!n.queryCorrections)
      return null;
    let { correctedQuery: o } = n.queryCorrections[0], a = await this.automaticallyRetryQueryWithCorrection(o);
    return we2(a.response) ? (this.dispatch(nn2(a.response.error)), this.rejectWithValue(a.response.error)) : (this.logOriginalAnalyticsQueryBeforeAutoCorrection(t), this.dispatch(nt2(Et2(this.getState()))), { ...a, response: { ...a.response.success, queryCorrections: n.queryCorrections }, automaticallyCorrected: true, originalQuery: r, analyticsAction: Xm2() });
  }
  processModernDidYouMeanAutoCorrection(t) {
    let r = this.getSuccessResponse(t), { correctedQuery: n, originalQuery: o } = r.queryCorrection;
    return this.onUpdateQueryForCorrection(n), { ...t, response: { ...r }, queryExecuted: n, automaticallyCorrected: true, originalQuery: o, analyticsAction: Xm2() };
  }
  logOriginalAnalyticsQueryBeforeAutoCorrection(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    this.analyticsAction && this.analyticsAction()(this.dispatch, () => this.getStateAfterResponse(t.queryExecuted, t.duration, r, n), this.extra);
  }
  async processQueryTriggersOrContinue(t) {
    let r = this.getSuccessResponse(t);
    if (!r)
      return null;
    let n = r.triggers.find((s) => s.type === "query")?.content || "";
    if (!n)
      return null;
    if (this.getState().triggers?.queryModification.queryToIgnore === n)
      return this.dispatch(an2("")), null;
    this.analyticsAction && await this.dispatch(this.analyticsAction);
    let a = this.getCurrentQuery(), i = await this.automaticallyRetryQueryWithTriggerModification(n);
    return we2(i.response) ? (this.dispatch(nn2(i.response.error)), this.rejectWithValue(i.response.error)) : (this.dispatch(nt2(Et2(this.getState()))), { ...i, response: { ...i.response.success }, automaticallyCorrected: false, originalQuery: a, analyticsAction: Eu() });
  }
  getStateAfterResponse(t, r, n, o) {
    return { ...n, query: { q: t, enableQuerySyntax: n.query?.enableQuerySyntax ?? Fe2().enableQuerySyntax }, search: { ...Ze(), duration: r, response: o, results: o.results } };
  }
  processSuccessResponse(t) {
    return this.dispatch(nt2(Et2(this.getState()))), { ...t, response: this.getSuccessResponse(t), automaticallyCorrected: false, originalQuery: this.getCurrentQuery(), analyticsAction: this.analyticsAction };
  }
  getSuccessResponse(t) {
    return Tc2(t.response) ? t.response.success : null;
  }
  async automaticallyRetryQueryWithCorrection(t) {
    this.onUpdateQueryForCorrection(t);
    let r = await this.fetchFromAPI(await cn2(this.getState()), { origin: "mainSearch" });
    return this.dispatch(St2(t)), r;
  }
  async automaticallyRetryQueryWithTriggerModification(t) {
    return this.dispatch(Fa2({ newQuery: t, originalQuery: this.getCurrentQuery() })), this.onUpdateQueryForCorrection(t), await this.fetchFromAPI(await cn2(this.getState()), { origin: "mainSearch" });
  }
  getCurrentQuery() {
    let t = this.getState();
    return t.query?.q !== void 0 ? t.query.q : "";
  }
  get extra() {
    return this.config.extra;
  }
  getState() {
    return this.config.getState();
  }
  get dispatch() {
    return this.config.dispatch;
  }
  get analyticsAction() {
    return this.config.analyticsAction;
  }
  get rejectWithValue() {
    return this.config.rejectWithValue;
  }
};
W2("search/prepareForSearchWithQuery", (e7, t) => {
  let { dispatch: r } = t;
  x(e7, { q: new StringValue2(), enableQuerySyntax: new BooleanValue2(), clearFilters: new BooleanValue2() }), e7.clearFilters && (r(Se2()), r(_t2())), r(ft2({ allow: true })), r(Le2({ q: e7.q, enableQuerySyntax: e7.enableQuerySyntax })), r(gt2(1));
});
var Ra2 = W2("search/executeSearch", async (e7, t) => {
  let r = t.getState();
  return await Nu(r, t, e7);
});
var ba2 = W2("search/fetchPage", async (e7, t) => {
  let r = t.getState();
  return await rf2(r, t, e7);
});
var va = W2("search/fetchMoreResults", async (e7, t) => {
  let r = t.getState();
  return await nf2(t, r);
});
var Vu2 = W2("search/fetchFacetValues", async (e7, t) => {
  let r = t.getState();
  return await eT2(t, e7, r);
});
W2("search/fetchInstantResults", async (e7, t) => tf2(e7, t));
var JE2 = async (e7, t) => {
  let r = await cn2(e7, t);
  return r.request = { ...r.request, firstResult: (e7.pagination?.firstResult ?? 0) + (e7.search?.results.length ?? 0) }, r;
};
var XE2 = async (e7, t, r) => {
  let n = await rn2(e7);
  return on2({ ...n, ...e7.didYouMean && { enableDidYouMean: e7.didYouMean.enableDidYouMean }, numberOfResults: r, q: t });
};
var ZE2 = async (e7, t) => {
  let r = await cn2(e7, t);
  return r.request.numberOfResults = 0, r;
};
var Gy2 = (e7) => {
  e7.configuration.analytics.enabled && dt2.addElement({ name: "Query", ...e7.query?.q && { value: e7.query.q }, time: JSON.stringify(/* @__PURE__ */ new Date()) });
};
async function tf2(e7, t) {
  x(e7, { id: V2, q: V2, maxResultsPerQuery: new NumberValue2({ required: true, min: 1 }), cacheTimeout: new NumberValue2() });
  let { q: r, maxResultsPerQuery: n } = e7, o = t.getState(), a = new un2({ ...t, analyticsAction: xy2() }, (u) => {
    t.dispatch(jt2({ q: u, id: e7.id }));
  }), i = await XE2(o, r, n), s = await a.fetchFromAPI(i, { origin: "instantResults", disableAbortWarning: true }), c = await a.process(s);
  return "response" in c ? { results: c.response.results, searchUid: c.response.searchUid, analyticsAction: c.analyticsAction, totalCountFiltered: c.response.totalCountFiltered, duration: c.duration } : c;
}
async function rf2(e7, t, r) {
  Gy2(e7);
  let { analyticsClientMiddleware: n, preprocessRequest: o, logger: a } = t.extra, { description: i } = await r.prepare({ getState: () => t.getState(), analyticsClientMiddleware: n, preprocessRequest: o, logger: a }), s = new un2({ ...t, analyticsAction: r }), c = await cn2(e7, i), u = await s.fetchFromAPI(c, { origin: "mainSearch" });
  return await s.process(u);
}
async function nf2(e7, t) {
  let { analyticsClientMiddleware: r, preprocessRequest: n, logger: o } = e7.extra, { description: a } = await Um().prepare({ getState: () => e7.getState(), analyticsClientMiddleware: r, preprocessRequest: n, logger: o }), i = new un2({ ...e7, analyticsAction: Um() }), s = await JE2(t, a), c = await i.fetchFromAPI(s, { origin: "mainSearch" });
  return await i.process(c);
}
async function eT2(e7, t, r) {
  let { analyticsClientMiddleware: n, preprocessRequest: o, logger: a } = e7.extra, { description: i } = await t.prepare({ getState: () => e7.getState(), analyticsClientMiddleware: n, preprocessRequest: o, logger: a }), s = new un2({ ...e7, analyticsAction: t }), c = await ZE2(r, i), u = await s.fetchFromAPI(c, { origin: "facetValues" });
  return await s.process(u);
}
async function Nu(e7, t, r) {
  Gy2(e7);
  let { analyticsClientMiddleware: n, preprocessRequest: o, logger: a } = t.extra, { description: i } = await r.prepare({ getState: () => t.getState(), analyticsClientMiddleware: n, preprocessRequest: o, logger: a }), s = await cn2(e7, i), c = new un2({ ...t, analyticsAction: r }), u = await c.fetchFromAPI(s, { origin: "mainSearch" });
  return await c.process(u);
}
var yt2 = async (e7, t, r) => {
  let n = sT(e7), o = tT2(e7), a = rT2(e7), i = e7.configuration.analytics.analyticsMode === "legacy" ? await rn2(e7, r) : ha2(e7, t, r), s = () => e7.pagination ? e7.pagination.firstResult + e7.pagination.numberOfResults > 5e3 ? 5e3 - e7.pagination.firstResult : e7.pagination.numberOfResults : void 0;
  return on2({ ...i, ...e7.didYouMean && { queryCorrection: { enabled: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "next", options: { automaticallyCorrect: e7.didYouMean.automaticallyCorrectQuery ? "whenNoResults" : "never" } }, enableDidYouMean: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "legacy" }, ...n && { cq: n }, ...o.length && { facets: o }, ...e7.pagination && { numberOfResults: s(), firstResult: e7.pagination.firstResult }, ...e7.facetOptions && { facetOptions: { freezeFacetOrder: e7.facetOptions.freezeFacetOrder } }, ...e7.folding?.enabled && { filterField: e7.folding.fields.collection, childField: e7.folding.fields.parent, parentField: e7.folding.fields.child, filterFieldRange: e7.folding.filterFieldRange }, ...e7.automaticFacetSet && { generateAutomaticFacets: { desiredCount: e7.automaticFacetSet.desiredCount, numberOfValues: e7.automaticFacetSet.numberOfValues, currentFacets: a } }, ...e7.generatedAnswer && { pipelineRuleParameters: { mlGenerativeQuestionAnswering: { responseFormat: e7.generatedAnswer.responseFormat, citationsFieldToInclude: e7.generatedAnswer.fieldsToIncludeInCitations } } } });
};
function tT2(e7) {
  return Es(oT2(e7), e7.facetOrder ?? []);
}
function rT2(e7) {
  let t = e7.automaticFacetSet?.set;
  return t ? Object.values(t).map((r) => r.response).map(nT2).filter((r) => r.currentValues.length > 0) : void 0;
}
function nT2(e7) {
  let { field: t, label: r, values: n } = e7, o = n.filter((a) => a.state === "selected");
  return { field: t, label: r, currentValues: o };
}
function oT2(e7) {
  return aT2(e7).filter(({ facetId: t }) => e7.facetOptions?.facets[t]?.enabled ?? true);
}
function aT2(e7) {
  return [...iT2(e7.facetSet ?? {}), ...Wy(e7.numericFacetSet ?? {}), ...Wy(e7.dateFacetSet ?? {}), ...sn2(e7.categoryFacetSet ?? {})];
}
function iT2(e7) {
  return sn2(e7).map((t) => {
    let r = ef2[t.sortCriteria];
    return r ? { ...t, sortCriteria: r } : t;
  });
}
function Wy(e7) {
  return sn2(e7).map((t) => {
    let n = t.currentValues.some(({ state: o }) => o !== "idle");
    return t.generateAutomaticRanges && !n ? { ...t, currentValues: [] } : t;
  });
}
function sT(e7) {
  let t = e7.advancedSearchQueries?.cq.trim() || "", n = Object.values(e7.tabSet || {}).find((a) => a.isActive)?.expression.trim() || "", o = cT2(e7);
  return [t, n, ...o].filter((a) => !!a).join(" AND ");
}
function cT2(e7) {
  return Object.values(e7.staticFilterSet || {}).map((r) => {
    let n = r.values.filter((a) => a.state === "selected" && !!a.expression.trim()), o = n.map((a) => a.expression).join(" OR ");
    return n.length > 1 ? `(${o})` : o;
  });
}
var ln2 = class {
  constructor(t, r = (n) => {
    this.dispatch(Le2({ q: n }));
  }) {
    this.config = t;
    this.onUpdateQueryForCorrection = r;
  }
  async fetchFromAPI({ mappings: t, request: r }, n) {
    let o = (/* @__PURE__ */ new Date()).getTime(), a = Cu2(await this.extra.apiClient.search(r, n), t), i = (/* @__PURE__ */ new Date()).getTime() - o, s = this.getState().query?.q || "";
    return { response: a, duration: i, queryExecuted: s, requestExecuted: r };
  }
  async process(t) {
    return this.processQueryErrorOrContinue(t) ?? await this.processQueryCorrectionsOrContinue(t) ?? await this.processQueryTriggersOrContinue(t) ?? this.processSuccessResponse(t);
  }
  processQueryErrorOrContinue(t) {
    return we2(t.response) ? (this.dispatch(nn2(t.response.error)), this.rejectWithValue(t.response.error)) : null;
  }
  async processQueryCorrectionsOrContinue(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    if (!n || !r.didYouMean)
      return null;
    let { enableDidYouMean: o, automaticallyCorrectQuery: a } = r.didYouMean, { results: i, queryCorrections: s, queryCorrection: c } = n;
    if (!o || !a)
      return null;
    let u = i.length === 0 && s && s.length !== 0, l = !isNullOrUndefined2(c) && !isNullOrUndefined2(c.correctedQuery);
    if (!u && !l)
      return null;
    let p = u ? await this.processLegacyDidYouMeanAutoCorrection(t) : this.processModernDidYouMeanAutoCorrection(t);
    return this.dispatch(nt2(Et2(this.getState()))), p;
  }
  async processLegacyDidYouMeanAutoCorrection(t) {
    let r = this.getCurrentQuery(), n = this.getSuccessResponse(t);
    if (!n.queryCorrections)
      return null;
    let { correctedQuery: o } = n.queryCorrections[0], a = await this.automaticallyRetryQueryWithCorrection(o);
    return we2(a.response) ? (this.dispatch(nn2(a.response.error)), this.rejectWithValue(a.response.error)) : (this.dispatch(nt2(Et2(this.getState()))), { ...a, response: { ...a.response.success, queryCorrections: n.queryCorrections }, automaticallyCorrected: true, originalQuery: r });
  }
  processModernDidYouMeanAutoCorrection(t) {
    let r = this.getSuccessResponse(t), { correctedQuery: n, originalQuery: o } = r.queryCorrection;
    return this.onUpdateQueryForCorrection(n), { ...t, response: { ...r }, queryExecuted: n, automaticallyCorrected: true, originalQuery: o };
  }
  async processQueryTriggersOrContinue(t) {
    let r = this.getSuccessResponse(t);
    if (!r)
      return null;
    let n = r.triggers.find((s) => s.type === "query")?.content || "";
    if (!n)
      return null;
    if (this.getState().triggers?.queryModification.queryToIgnore === n)
      return this.dispatch(an2("")), null;
    let a = this.getCurrentQuery(), i = await this.automaticallyRetryQueryWithTriggerModification(n);
    return we2(i.response) ? (this.dispatch(nn2(i.response.error)), this.rejectWithValue(i.response.error)) : (this.dispatch(nt2(Et2(this.getState()))), { ...i, response: { ...i.response.success }, automaticallyCorrected: false, originalQuery: a });
  }
  processSuccessResponse(t) {
    return this.dispatch(nt2(Et2(this.getState()))), { ...t, response: this.getSuccessResponse(t), automaticallyCorrected: false, originalQuery: this.getCurrentQuery() };
  }
  getSuccessResponse(t) {
    return Tc2(t.response) ? t.response.success : null;
  }
  async automaticallyRetryQueryWithCorrection(t) {
    this.onUpdateQueryForCorrection(t);
    let r = this.getState(), { actionCause: n } = Qy2(), o = await this.fetchFromAPI(await yt2(r, this.extra.navigatorContext, { actionCause: n }), { origin: "mainSearch" });
    return this.dispatch(St2(t)), o;
  }
  async automaticallyRetryQueryWithTriggerModification(t) {
    return this.dispatch(Fa2({ newQuery: t, originalQuery: this.getCurrentQuery() })), this.onUpdateQueryForCorrection(t), await this.fetchFromAPI(await yt2(this.getState(), this.extra.navigatorContext), { origin: "mainSearch" });
  }
  getCurrentQuery() {
    let t = this.getState();
    return t.query?.q !== void 0 ? t.query.q : "";
  }
  get extra() {
    return this.config.extra;
  }
  getState() {
    return this.config.getState();
  }
  get dispatch() {
    return this.config.dispatch;
  }
  get rejectWithValue() {
    return this.config.rejectWithValue;
  }
};
var Pa2 = W2("search/prepareForSearchWithQuery", (e7, t) => {
  let { dispatch: r } = t;
  x(e7, { q: new StringValue2(), enableQuerySyntax: new BooleanValue2(), clearFilters: new BooleanValue2() }), e7.clearFilters && (r(Se2()), r(_t2())), r(ft2({ allow: true })), r(Le2({ q: e7.q, enableQuerySyntax: e7.enableQuerySyntax })), r(gt2(1));
});
var N2 = W2("search/executeSearch", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return Nu(r, t, e7.legacy);
  Yy2(r);
  let n = e7.next ? Jy(e7.next) : void 0, o = await yt2(r, t.extra.navigatorContext, n), a = new ln2({ ...t, analyticsAction: n ?? {} }), i = await a.fetchFromAPI(o, { origin: "mainSearch" });
  return await a.process(i);
});
var Wt2 = W2("search/fetchPage", async (e7, t) => {
  let r = t.getState();
  if (Yy2(r), r.configuration.analytics.analyticsMode === "legacy" || !e7.next)
    return rf2(r, t, e7.legacy);
  let n = new ln2({ ...t, analyticsAction: e7.next }), o = await yt2(r, t.extra.navigatorContext, e7.next), a = await n.fetchFromAPI(o, { origin: "mainSearch" });
  return await n.process(a);
});
var dn2 = W2("search/fetchMoreResults", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return nf2(t, r);
  let n = ny2("browseResults", t.getState), o = new ln2({ ...t, analyticsAction: n }), a = await lT2(r, t.extra.navigatorContext, n), i = await o.fetchFromAPI(a, { origin: "mainSearch" });
  return await o.process(i);
});
var Ht2 = W2("search/fetchFacetValues", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return Nu(r, t, e7.legacy);
  let n = new ln2({ ...t, analyticsAction: {} }), o = await pT(r, t.extra.navigatorContext), a = await n.fetchFromAPI(o, { origin: "facetValues" });
  return await n.process(a);
});
var wa2 = W2("search/fetchInstantResults", async (e7, t) => {
  let r = t.getState();
  if (r.configuration.analytics.analyticsMode === "legacy")
    return tf2(e7, t);
  x(e7, { id: V2, q: V2, maxResultsPerQuery: new NumberValue2({ required: true, min: 1 }), cacheTimeout: new NumberValue2() });
  let { q: n, maxResultsPerQuery: o } = e7, a = Jy(Ay2()), i = await dT(r, t.extra.navigatorContext, n, o, a), s = new ln2({ ...t, analyticsAction: a }, (l) => {
    t.dispatch(jt2({ q: l, id: e7.id }));
  }), c = await s.fetchFromAPI(i, { origin: "instantResults", disableAbortWarning: true }), u = await s.process(c);
  return "response" in u ? { results: u.response.results, searchUid: u.response.searchUid, totalCountFiltered: u.response.totalCountFiltered, duration: u.duration } : u;
});
var lT2 = async (e7, t, r) => {
  let n = await yt2(e7, t, r);
  return n.request = { ...n.request, firstResult: (e7.pagination?.firstResult ?? 0) + (e7.search?.results.length ?? 0) }, n;
};
var dT = async (e7, t, r, n, o) => {
  let a = ha2(e7, t, o);
  return on2({ ...a, ...e7.didYouMean && { enableDidYouMean: e7.didYouMean.enableDidYouMean }, numberOfResults: n, q: r });
};
var pT = async (e7, t, r) => {
  let n = await yt2(e7, t, r);
  return n.request.numberOfResults = 0, n;
};
var Yy2 = (e7) => {
  e7.configuration.analytics.enabled && dt2.addElement({ name: "Query", ...e7.query?.q && { value: e7.query.q }, time: JSON.stringify(/* @__PURE__ */ new Date()) });
};
var Jy = (e7) => ({ actionCause: e7.actionCause, type: e7.actionCause });
function Ts2(e7) {
  return e7.search.response.searchUid !== "";
}
function of2(e7, t) {
  let r = t.payload ?? null;
  r && (e7.response = Ze().response, e7.results = [], e7.questionAnswer = Do2()), e7.error = r, e7.isLoading = false;
}
function sf2(e7, t) {
  e7.error = null, e7.response = t.payload.response, e7.queryExecuted = t.payload.queryExecuted, e7.duration = t.payload.duration, e7.isLoading = false;
}
function yT2(e7, t) {
  sf2(e7, t), e7.results = t.payload.response.results.map((r) => ({ ...r, searchUid: t.payload.response.searchUid })), e7.searchResponseId = t.payload.response.searchUid, e7.questionAnswer = t.payload.response.questionAnswer, e7.extendedResults = t.payload.response.extendedResults;
}
function af2(e7, t) {
  e7.isLoading = true, e7.requestId = t.meta.requestId;
}
var z = $2(Ze(), (e7) => {
  e7.addCase(Ra2.rejected, (t, r) => of2(t, r)), e7.addCase(va.rejected, (t, r) => of2(t, r)), e7.addCase(ba2.rejected, (t, r) => of2(t, r)), e7.addCase(Ra2.fulfilled, (t, r) => {
    yT2(t, r);
  }), e7.addCase(va.fulfilled, (t, r) => {
    sf2(t, r), t.results = [...t.results, ...r.payload.response.results.map((n) => ({ ...n, searchUid: r.payload.response.searchUid }))];
  }), e7.addCase(ba2.fulfilled, (t, r) => {
    sf2(t, r), t.results = [...r.payload.response.results.map((n) => ({ ...n, searchUid: r.payload.response.searchUid }))];
  }), e7.addCase(Vu2.fulfilled, (t, r) => {
    t.response.facets = r.payload.response.facets, t.response.searchUid = r.payload.response.searchUid;
  }), e7.addCase(Ra2.pending, af2), e7.addCase(va.pending, af2), e7.addCase(ba2.pending, af2);
});
var ks = Y2((e7) => e7.query, (e7) => e7);
var Ct2 = (e7) => AT(e7) ? { answerAPIEnabled: true, id: qs2(e7).data?.answerId } : xT(e7) ? { answerAPIEnabled: false, id: e7.search.response.extendedResults.generativeQuestionAnsweringId } : { answerAPIEnabled: false, id: void 0 };
var xT = (e7) => "search" in e7;
var AT = (e7) => "answer" in e7 && "generatedAnswer" in e7 && !isNullOrUndefined2(e7.generatedAnswer?.answerConfigurationId);
var eC2 = (e7) => e7.generatedAnswer?.fieldsToIncludeInCitations;
Y2((e7) => e7.generatedAnswer?.citations, (e7, t) => t, (e7, t) => e7?.find((r) => r.id === t));
Y2((e7) => ks(e7)?.q, (e7) => e7.search.requestId, (e7, t) => ({ q: e7, requestId: t }));
var Ds = (e7) => L2({ prefix: "analytics/generatedAnswer/streamEnd", __legacy__getBuilder: (t, r) => {
  let { id: n, answerAPIEnabled: o } = Ct2(r), a = e7 ? !r.generatedAnswer?.answer || !r.generatedAnswer?.answer.length : void 0;
  return n ? t.makeGeneratedAnswerStreamEnd({ ...o ? { answerAPIStreamId: n } : { generativeQuestionAnsweringId: n }, answerGenerated: e7, answerTextIsEmpty: a }) : null;
}, analyticsType: "Rga.AnswerReceived", analyticsPayloadBuilder: (t) => ({ answerId: t.search?.response.searchUid || "", answerGenerated: e7 ?? false }) });
var tC2 = async (e7) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: Me2(e7.configuration.organizationId, e7.configuration.environment), streamId: e7.search.extendedResults?.generativeQuestionAnsweringId });
var rC = ["text/plain", "text/markdown"];
var Ia2 = new StringValue2({ required: true });
var oC2 = new StringValue2();
var Ea2 = new BooleanValue2({ required: true });
var NT2 = { id: Ia2, title: Ia2, uri: Ia2, permanentid: Ia2, clickUri: oC2 };
var aC = new StringValue2({ required: true, constrainTo: rC });
var Ta2 = h3("generatedAnswer/setIsVisible", (e7) => x(e7, Ea2));
var Ms2 = h3("generatedAnswer/setIsEnabled", (e7) => x(e7, Ea2));
var Qs2 = h3("generatedAnswer/updateMessage", (e7) => x(e7, { textDelta: Ia2 }));
var Ls2 = h3("generatedAnswer/updateCitations", (e7) => x(e7, { citations: new ArrayValue2({ required: true, each: new RecordValue2({ values: NT2 }) }) }));
var cf2 = h3("generatedAnswer/updateError", (e7) => x(e7, { message: oC2, code: new NumberValue2({ min: 0 }) }));
var zt2 = h3("generatedAnswer/resetAnswer");
var Uu2 = h3("generatedAnswer/like");
var _u2 = h3("generatedAnswer/dislike");
var ju2 = h3("generatedAnswer/feedbackModal/open");
var Bs2 = h3("generatedAnswer/expand");
var $u2 = h3("generatedAnswer/collapse");
var Gu2 = h3("generatedAnswer/setId", (e7) => x(e7, { id: new StringValue2({ required: true }) }));
var Wu2 = h3("generatedAnswer/feedbackModal/close");
var ka2 = h3("generatedAnswer/sendFeedback");
var Ns2 = h3("generatedAnswer/setIsLoading", (e7) => x(e7, Ea2));
var Lu = h3("generatedAnswer/setIsStreaming", (e7) => x(e7, Ea2));
var Us2 = h3("generatedAnswer/setAnswerContentFormat", (e7) => x(e7, aC));
var Hu2 = h3("generatedAnswer/updateResponseFormat", (e7) => x(e7, { contentFormat: new ArrayValue2({ each: aC, default: ["text/plain"] }) }));
var zu2 = h3("knowledge/updateAnswerConfigurationId", (e7) => x(e7, Ia2));
var Ku2 = h3("generatedAnswer/registerFieldsToIncludeInCitations", (e7) => x(e7, kc2));
var uf2 = h3("generatedAnswer/setIsAnswerGenerated", (e7) => x(e7, Ea2));
var no2 = h3("generatedAnswer/setCannotAnswer", (e7) => x(e7, Ea2));
W2("generatedAnswer/streamAnswer", async (e7, t) => {
  let r = t.getState(), { dispatch: n, extra: o, getState: a } = t, { search: i } = a(), { queryExecuted: s } = i, { setAbortControllerRef: c } = e7, u = await tC2(r), l = (d, f) => {
    switch (d) {
      case "genqa.headerMessageType": {
        let A = JSON.parse(f);
        n(Us2(A.contentFormat));
        break;
      }
      case "genqa.messageType":
        n(Qs2(JSON.parse(f)));
        break;
      case "genqa.citationsType":
        n(Ls2(JSON.parse(f)));
        break;
      case "genqa.endOfStreamType": {
        let A = JSON.parse(f).answerGenerated, S = s.length !== 0 && !A;
        n(no2(S)), n(Lu(false)), n(uf2(A)), n(Ds(A));
        break;
      }
      default:
        r.debug && o.logger.warn(`Unknown payloadType: "${d}"`);
    }
  };
  n(Ns2(true));
  let m = (d) => d.streamId === t.getState().search.extendedResults.generativeQuestionAnsweringId, p = o.streamingClient?.streamGeneratedAnswer(u, { write: (d) => {
    m(u) && (n(Ns2(false)), d.payload && d.payloadType && l(d.payloadType, d.payload));
  }, abort: (d) => {
    m(u) && n(cf2(d));
  }, close: () => {
    m(u) && n(Lu(false));
  }, resetAnswer: () => {
    m(u) && n(zt2());
  } });
  p ? c(p) : n(Ns2(false));
});
var sC2 = Y2((e7) => e7.pipeline, (e7) => e7);
var cC2 = Y2((e7) => e7.searchHub, (e7) => e7);
function uC2(e7) {
  return { status: e7, isUninitialized: e7 === "uninitialized", isLoading: e7 === "pending", isSuccess: e7 === "fulfilled", isError: e7 === "rejected" };
}
var lC2 = Nt2;
function FC2(e7, t) {
  if (e7 === t || !(lC2(e7) && lC2(t) || Array.isArray(e7) && Array.isArray(t)))
    return t;
  let r = Object.keys(t), n = Object.keys(e7), o = r.length === n.length, a = Array.isArray(t) ? [] : {};
  for (let i of r)
    a[i] = FC2(e7[i], t[i]), o && (o = e7[i] === a[i]);
  return o ? e7 : a;
}
function Oa2(e7) {
  let t = 0;
  for (let r in e7)
    t++;
  return t;
}
var dC2 = (e7) => [].concat(...e7);
function MT2(e7) {
  return new RegExp("(^|:)//").test(e7);
}
function QT2() {
  return typeof document > "u" ? true : document.visibilityState !== "hidden";
}
function Xu2(e7) {
  return e7 != null;
}
function LT2() {
  return typeof navigator > "u" || navigator.onLine === void 0 ? true : navigator.onLine;
}
var BT2 = (e7) => e7.replace(/\/$/, "");
var UT2 = (e7) => e7.replace(/^\//, "");
function _T2(e7, t) {
  if (!e7)
    return t;
  if (!t)
    return e7;
  if (MT2(t))
    return t;
  let r = e7.endsWith("/") || !t.startsWith("?") ? "/" : "";
  return e7 = BT2(e7), t = UT2(t), `${e7}${r}${t}`;
}
function jT2(e7, t, r) {
  return e7.has(t) ? e7.get(t) : e7.set(t, r).get(t);
}
var pC2 = (...e7) => fetch(...e7);
var $T2 = (e7) => e7.status >= 200 && e7.status <= 299;
var GT2 = (e7) => /ion\/(vnd\.api\+)?json/.test(e7.get("content-type") || "");
function mC2(e7) {
  if (!Nt2(e7))
    return e7;
  let t = { ...e7 };
  for (let [r, n] of Object.entries(t))
    n === void 0 && delete t[r];
  return t;
}
function RC2({ baseUrl: e7, prepareHeaders: t = (m) => m, fetchFn: r = pC2, paramsSerializer: n, isJsonContentType: o = GT2, jsonContentType: a = "application/json", jsonReplacer: i, timeout: s, responseHandler: c, validateStatus: u, ...l } = {}) {
  return typeof fetch > "u" && r === pC2 && console.warn("Warning: `fetch` is not available. Please supply a custom `fetchFn` property to use `fetchBaseQuery` on SSR environments."), async (p, d, f) => {
    let { getState: A, extra: S, endpoint: g, forced: C, type: y } = d, F2, { url: I, headers: v = new Headers(l.headers), params: R = void 0, responseHandler: b = c ?? "json", validateStatus: P = u ?? $T2, timeout: T = s, ...B } = typeof p == "string" ? { url: p } : p, D, O = d.signal;
    T && (D = new AbortController(), d.signal.addEventListener("abort", D.abort), O = D.signal);
    let k = { ...l, signal: O, ...B };
    v = new Headers(mC2(v)), k.headers = await t(v, { getState: A, arg: p, extra: S, endpoint: g, forced: C, type: y, extraOptions: f }) || v;
    let Q = (J) => typeof J == "object" && (Nt2(J) || Array.isArray(J) || typeof J.toJSON == "function");
    if (!k.headers.has("content-type") && Q(k.body) && k.headers.set("content-type", a), Q(k.body) && o(k.headers) && (k.body = JSON.stringify(k.body, i)), R) {
      let J = ~I.indexOf("?") ? "&" : "?", re = n ? n(R) : new URLSearchParams(mC2(R));
      I += J + re;
    }
    I = _T2(e7, I);
    let q = new Request(I, k);
    F2 = { request: new Request(I, k) };
    let _, H2 = false, ee = D && setTimeout(() => {
      H2 = true, D.abort();
    }, T);
    try {
      _ = await r(q);
    } catch (J) {
      return { error: { status: H2 ? "TIMEOUT_ERROR" : "FETCH_ERROR", error: String(J) }, meta: F2 };
    } finally {
      ee && clearTimeout(ee), D?.signal.removeEventListener("abort", D.abort);
    }
    let oe = _.clone();
    F2.response = oe;
    let X, te = "";
    try {
      let J;
      if (await Promise.all([m(_, b).then((re) => X = re, (re) => J = re), oe.text().then((re) => te = re, () => {
      })]), J)
        throw J;
    } catch (J) {
      return { error: { status: "PARSING_ERROR", originalStatus: _.status, data: te, error: String(J) }, meta: F2 };
    }
    return P(_, X) ? { data: X, meta: F2 } : { error: { status: _.status, data: X }, meta: F2 };
  };
  async function m(p, d) {
    if (typeof d == "function")
      return d(p);
    if (d === "content-type" && (d = o(p.headers) ? "json" : "text"), d === "json") {
      let f = await p.text();
      return f.length ? JSON.parse(f) : null;
    }
    return p.text();
  }
}
var qa2 = class {
  constructor(e7, t = void 0) {
    this.value = e7, this.meta = t;
  }
};
async function WT2(e7 = 0, t = 5) {
  let r = Math.min(e7, t), n = ~~((Math.random() + 0.4) * (300 << r));
  await new Promise((o) => setTimeout((a) => o(a), n));
}
function HT2(e7, t) {
  throw Object.assign(new qa2({ error: e7, meta: t }), { throwImmediately: true });
}
var fC2 = {};
var zT2 = (e7, t) => async (r, n, o) => {
  let a = [5, (t || fC2).maxRetries, (o || fC2).maxRetries].filter((l) => l !== void 0), [i] = a.slice(-1), c = { maxRetries: i, backoff: WT2, retryCondition: (l, m, { attempt: p }) => p <= i, ...t, ...o }, u = 0;
  for (; ; )
    try {
      let l = await e7(r, n, o);
      if (l.error)
        throw new qa2(l);
      return l;
    } catch (l) {
      if (u++, l.throwImmediately) {
        if (l instanceof qa2)
          return l.value;
        throw l;
      }
      if (l instanceof qa2 && !c.retryCondition(l.value.error, r, { attempt: u, baseQueryApi: n, extraOptions: o }))
        return l.value;
      await c.backoff(u, c.maxRetries);
    }
};
var bC2 = Object.assign(zT2, { fail: HT2 });
var ff2 = h3("__rtkq/focused");
var vC2 = h3("__rtkq/unfocused");
var gf2 = h3("__rtkq/online");
var PC2 = h3("__rtkq/offline");
function Sf2(e7) {
  return e7.type === "query";
}
function KT2(e7) {
  return e7.type === "mutation";
}
function hf2(e7) {
  return e7.type === "infinitequery";
}
function yf(e7, t, r, n, o, a) {
  return YT2(e7) ? e7(t, r, n, o).filter(Xu2).map(df2).map(a) : Array.isArray(e7) ? e7.map(df2).map(a) : [];
}
function YT2(e7) {
  return typeof e7 == "function";
}
function df2(e7) {
  return typeof e7 == "string" ? { type: e7 } : e7;
}
function JT2(e7, t) {
  return e7.catch(t);
}
var js2 = Symbol("forceQueryFn");
var pf2 = (e7) => typeof e7[js2] == "function";
function XT2({ serializeQueryArgs: e7, queryThunk: t, infiniteQueryThunk: r, mutationThunk: n, api: o, context: a }) {
  let i = /* @__PURE__ */ new Map(), s = /* @__PURE__ */ new Map(), { unsubscribeQueryResult: c, removeMutationResult: u, updateSubscriptionOptions: l } = o.internalActions;
  return { buildInitiateQuery: g, buildInitiateInfiniteQuery: C, buildInitiateMutation: y, getRunningQueryThunk: m, getRunningMutationThunk: p, getRunningQueriesThunk: d, getRunningMutationsThunk: f };
  function m(F2, I) {
    return (v) => {
      let R = a.endpointDefinitions[F2], b = e7({ queryArgs: I, endpointDefinition: R, endpointName: F2 });
      return i.get(v)?.[b];
    };
  }
  function p(F2, I) {
    return (v) => s.get(v)?.[I];
  }
  function d() {
    return (F2) => Object.values(i.get(F2) || {}).filter(Xu2);
  }
  function f() {
    return (F2) => Object.values(s.get(F2) || {}).filter(Xu2);
  }
  function S(F2, I) {
    let v = (R, { subscribe: b = true, forceRefetch: P, subscriptionOptions: T, [js2]: B, ...D } = {}) => (O, k) => {
      let Q = e7({ queryArgs: R, endpointDefinition: I, endpointName: F2 }), q, U = { ...D, type: "query", subscribe: b, forceRefetch: P, subscriptionOptions: T, endpointName: F2, originalArgs: R, queryCacheKey: Q, [js2]: B };
      if (Sf2(I))
        q = t(U);
      else {
        let { direction: ie2, initialPageParam: fe } = D;
        q = r({ ...U, direction: ie2, initialPageParam: fe });
      }
      let _ = o.endpoints[F2].select(R), H2 = O(q), ee = _(k());
      let { requestId: oe, abort: X } = H2, te = ee.requestId !== oe, J = i.get(O)?.[Q], re = () => _(k()), ge = Object.assign(B ? H2.then(re) : te && !J ? Promise.resolve(ee) : Promise.all([J, H2]).then(re), { arg: R, requestId: oe, subscriptionOptions: T, queryCacheKey: Q, abort: X, async unwrap() {
        let ie2 = await ge;
        if (ie2.isError)
          throw ie2.error;
        return ie2.data;
      }, refetch: () => O(v(R, { subscribe: false, forceRefetch: true })), unsubscribe() {
        b && O(c({ queryCacheKey: Q, requestId: oe }));
      }, updateSubscriptionOptions(ie2) {
        ge.subscriptionOptions = ie2, O(l({ endpointName: F2, requestId: oe, queryCacheKey: Q, options: ie2 }));
      } });
      if (!J && !te && !B) {
        let ie2 = jT2(i, O, {});
        ie2[Q] = ge, ge.then(() => {
          delete ie2[Q], Oa2(ie2) || i.delete(O);
        });
      }
      return ge;
    };
    return v;
  }
  function g(F2, I) {
    return S(F2, I);
  }
  function C(F2, I) {
    return S(F2, I);
  }
  function y(F2) {
    return (I, { track: v = true, fixedCacheKey: R } = {}) => (b, P) => {
      let T = n({ type: "mutation", endpointName: F2, originalArgs: I, track: v, fixedCacheKey: R }), B = b(T);
      let { requestId: D, abort: O, unwrap: k } = B, Q = JT2(B.unwrap().then((H2) => ({ data: H2 })), (H2) => ({ error: H2 })), q = () => {
        b(u({ requestId: D, fixedCacheKey: R }));
      }, U = Object.assign(Q, { arg: B.arg, requestId: D, abort: O, unwrap: k, reset: q }), _ = s.get(b) || {};
      return s.set(b, _), _[D] = U, U.then(() => {
        delete _[D], Oa2(_) || s.delete(b);
      }), R && (_[R] = U, U.then(() => {
        _[R] === U && (delete _[R], Oa2(_) || s.delete(b));
      })), U;
    };
  }
}
function ZT2(e7) {
  return e7;
}
var Yu2 = (e7 = {}) => ({ ...e7, [ss2]: true });
function ek2({ reducerPath: e7, baseQuery: t, context: { endpointDefinitions: r }, serializeQueryArgs: n, api: o, assertTagType: a, selectors: i }) {
  let s = (b, P, T, B) => (D, O) => {
    let k = r[b], Q = n({ queryArgs: P, endpointDefinition: k, endpointName: b });
    if (D(o.internalActions.queryResultPatched({ queryCacheKey: Q, patches: T })), !B)
      return;
    let q = o.endpoints[b].select(P)(O()), U = yf(k.providesTags, q.data, void 0, P, {}, a);
    D(o.internalActions.updateProvidedBy({ queryCacheKey: Q, providedTags: U }));
  };
  function c(b, P, T = 0) {
    let B = [P, ...b];
    return T && B.length > T ? B.slice(0, -1) : B;
  }
  function u(b, P, T = 0) {
    let B = [...b, P];
    return T && B.length > T ? B.slice(1) : B;
  }
  let l = (b, P, T, B = true) => (D, O) => {
    let Q = o.endpoints[b].select(P)(O()), q = { patches: [], inversePatches: [], undo: () => D(o.util.patchQueryData(b, P, q.inversePatches, B)) };
    if (Q.status === "uninitialized")
      return q;
    let U;
    if ("data" in Q)
      if (He2(Q.data)) {
        let [_, H2, ee] = Qc2(Q.data, T);
        q.patches.push(...H2), q.inversePatches.push(...ee), U = _;
      } else
        U = T(Q.data), q.patches.push({ op: "replace", path: [], value: U }), q.inversePatches.push({ op: "replace", path: [], value: Q.data });
    return q.patches.length === 0 || D(o.util.patchQueryData(b, P, q.patches, B)), q;
  }, m = (b, P, T) => (B) => B(o.endpoints[b].initiate(P, { subscribe: false, forceRefetch: true, [js2]: () => ({ data: T }) })), p = (b, P) => b.query && b[P] ? b[P] : ZT2, d = async (b, { signal: P, abort: T, rejectWithValue: B, fulfillWithValue: D, dispatch: O, getState: k, extra: Q }) => {
    let q = r[b.endpointName];
    try {
      let U = p(q, "transformResponse"), _ = { signal: P, abort: T, dispatch: O, getState: k, extra: Q, endpoint: b.endpointName, type: b.type, forced: b.type === "query" ? f(b, k()) : void 0, queryCacheKey: b.type === "query" ? b.queryCacheKey : void 0 }, H2 = b.type === "query" ? b[js2] : void 0, ee, oe = async (te, J, re, ge) => {
        if (J == null && te.pages.length)
          return Promise.resolve({ data: te });
        let ie2 = { queryArg: b.originalArgs, pageParam: J }, fe = await X(ie2), ye = ge ? c : u;
        return { data: { pages: ye(te.pages, fe.data, re), pageParams: ye(te.pageParams, J, re) } };
      };
      async function X(te) {
        let J, { extraOptions: re } = q;
        if (H2 ? J = H2() : q.query ? J = await t(q.query(te), _, re) : J = await q.queryFn(te, _, re, (ie2) => t(ie2, _, re)), J.error)
          throw new qa2(J.error, J.meta);
        let ge = await U(J.data, J.meta, te);
        return { ...J, data: ge };
      }
      if (b.type === "query" && "infiniteQueryOptions" in q) {
        let { infiniteQueryOptions: te } = q, { maxPages: J = 1 / 0 } = te, re, ge = { pages: [], pageParams: [] }, ie2 = i.selectQueryEntry(k(), b.queryCacheKey)?.data, ye = f(b, k()) && !b.direction || !ie2 ? ge : ie2;
        if ("direction" in b && b.direction && ye.pages.length) {
          let Ge = b.direction === "backward", Ur = (Ge ? wC2 : mf2)(te, ye);
          re = await oe(ye, Ur, J, Ge);
        } else {
          let { initialPageParam: Ge = te.initialPageParam } = b, it = ie2?.pageParams ?? [], Ur = it[0] ?? Ge, Eo = it.length;
          re = await oe(ye, Ur, J), H2 && (re = { data: re.data.pages[0] });
          for (let To2 = 1; To2 < Eo; To2++) {
            let Wi = mf2(te, re.data);
            re = await oe(re.data, Wi, J);
          }
        }
        ee = re;
      } else
        ee = await X(b.originalArgs);
      return D(ee.data, Yu2({ fulfilledTimeStamp: Date.now(), baseQueryMeta: ee.meta }));
    } catch (U) {
      let _ = U;
      if (_ instanceof qa2) {
        let H2 = p(q, "transformErrorResponse");
        try {
          return B(await H2(_.value, _.meta, b.originalArgs), Yu2({ baseQueryMeta: _.meta }));
        } catch (ee) {
          _ = ee;
        }
      }
      throw console.error(_), _;
    }
  };
  function f(b, P) {
    let T = i.selectQueryEntry(P, b.queryCacheKey), B = i.selectConfig(P).refetchOnMountOrArgChange, D = T?.fulfilledTimeStamp, O = b.forceRefetch ?? (b.subscribe && B);
    return O ? O === true || (Number(/* @__PURE__ */ new Date()) - Number(D)) / 1e3 >= O : false;
  }
  let A = () => W2(`${e7}/executeQuery`, d, { getPendingMeta({ arg: P }) {
    let T = r[P.endpointName];
    return Yu2({ startedTimeStamp: Date.now(), ...hf2(T) ? { direction: P.direction } : {} });
  }, condition(P, { getState: T }) {
    let B = T(), D = i.selectQueryEntry(B, P.queryCacheKey), O = D?.fulfilledTimeStamp, k = P.originalArgs, Q = D?.originalArgs, q = r[P.endpointName], U = P.direction;
    return pf2(P) ? true : D?.status === "pending" ? false : f(P, B) || Sf2(q) && q?.forceRefetch?.({ currentArg: k, previousArg: Q, endpointState: D, state: B }) ? true : !(O && !U);
  }, dispatchConditionRejection: true }), S = A(), g = A(), C = W2(`${e7}/executeMutation`, d, { getPendingMeta() {
    return Yu2({ startedTimeStamp: Date.now() });
  } }), y = (b) => "force" in b, F2 = (b) => "ifOlderThan" in b, I = (b, P, T) => (B, D) => {
    let O = y(T) && T.force, k = F2(T) && T.ifOlderThan, Q = (U = true) => {
      let _ = { forceRefetch: U, isPrefetch: true };
      return o.endpoints[b].initiate(P, _);
    }, q = o.endpoints[b].select(P)(D());
    if (O)
      B(Q());
    else if (k) {
      let U = q?.fulfilledTimeStamp;
      if (!U) {
        B(Q());
        return;
      }
      (Number(/* @__PURE__ */ new Date()) - Number(new Date(U))) / 1e3 >= k && B(Q());
    } else
      B(Q(false));
  };
  function v(b) {
    return (P) => P?.meta?.arg?.endpointName === b;
  }
  function R(b, P) {
    return { matchPending: Qo2(_c2(b), v(P)), matchFulfilled: Qo2(Pr2(b), v(P)), matchRejected: Qo2(Kn2(b), v(P)) };
  }
  return { queryThunk: S, mutationThunk: C, infiniteQueryThunk: g, prefetch: I, updateQueryData: l, upsertQueryData: m, patchQueryData: s, buildMatchThunkActions: R };
}
function mf2(e7, { pages: t, pageParams: r }) {
  let n = t.length - 1;
  return e7.getNextPageParam(t[n], t, r[n], r);
}
function wC2(e7, { pages: t, pageParams: r }) {
  return e7.getPreviousPageParam?.(t[0], t, r[0], r);
}
function IC2(e7, t, r, n) {
  return yf(r[e7.meta.arg.endpointName][t], Pr2(e7) ? e7.payload : void 0, us2(e7) ? e7.payload : void 0, e7.meta.arg.originalArgs, "baseQueryMeta" in e7.meta ? e7.meta.baseQueryMeta : void 0, n);
}
function Ju2(e7, t, r) {
  let n = e7[t];
  n && r(n);
}
function $s(e7) {
  return ("arg" in e7 ? e7.arg.fixedCacheKey : e7.fixedCacheKey) ?? e7.requestId;
}
function gC2(e7, t, r) {
  let n = e7[$s(t)];
  n && r(n);
}
var _s2 = {};
function tk2({ reducerPath: e7, queryThunk: t, mutationThunk: r, serializeQueryArgs: n, context: { endpointDefinitions: o, apiUid: a, extractRehydrationInfo: i, hasRehydrationInfo: s }, assertTagType: c, config: u }) {
  let l = h3(`${e7}/resetApiState`);
  function m(v, R, b, P) {
    var T;
    v[T = R.queryCacheKey] ?? (v[T] = { status: "uninitialized", endpointName: R.endpointName }), Ju2(v, R.queryCacheKey, (B) => {
      B.status = "pending", B.requestId = b && B.requestId ? B.requestId : P.requestId, R.originalArgs !== void 0 && (B.originalArgs = R.originalArgs), B.startedTimeStamp = P.startedTimeStamp;
      let D = o[P.arg.endpointName];
      hf2(D) && "direction" in R && (B.direction = R.direction);
    });
  }
  function p(v, R, b, P) {
    Ju2(v, R.arg.queryCacheKey, (T) => {
      if (T.requestId !== R.requestId && !P)
        return;
      let { merge: B } = o[R.arg.endpointName];
      if (T.status = "fulfilled", B)
        if (T.data !== void 0) {
          let { fulfilledTimeStamp: D, arg: O, baseQueryMeta: k, requestId: Q } = R, q = vr2(T.data, (U) => B(U, b, { arg: O.originalArgs, baseQueryMeta: k, fulfilledTimeStamp: D, requestId: Q }));
          T.data = q;
        } else
          T.data = b;
      else
        T.data = o[R.arg.endpointName].structuralSharing ?? true ? FC2(et2(T.data) ? Zp2(T.data) : T.data, b) : b;
      delete T.error, T.fulfilledTimeStamp = R.fulfilledTimeStamp;
    });
  }
  let d = Yn2({ name: `${e7}/queries`, initialState: _s2, reducers: { removeQueryResult: { reducer(v, { payload: { queryCacheKey: R } }) {
    delete v[R];
  }, prepare: Lo2() }, cacheEntriesUpserted: { reducer(v, R) {
    for (let b of R.payload) {
      let { queryDescription: P, value: T } = b;
      m(v, P, true, { arg: P, requestId: R.meta.requestId, startedTimeStamp: R.meta.timestamp }), p(v, { arg: P, requestId: R.meta.requestId, fulfilledTimeStamp: R.meta.timestamp, baseQueryMeta: {} }, T, true);
    }
  }, prepare: (v) => ({ payload: v.map((P) => {
    let { endpointName: T, arg: B, value: D } = P, O = o[T];
    return { queryDescription: { type: "query", endpointName: T, originalArgs: P.arg, queryCacheKey: n({ queryArgs: B, endpointDefinition: O, endpointName: T }) }, value: D };
  }), meta: { [ss2]: true, requestId: $c2(), timestamp: Date.now() } }) }, queryResultPatched: { reducer(v, { payload: { queryCacheKey: R, patches: b } }) {
    Ju2(v, R, (P) => {
      P.data = tm2(P.data, b.concat());
    });
  }, prepare: Lo2() } }, extraReducers(v) {
    v.addCase(t.pending, (R, { meta: b, meta: { arg: P } }) => {
      let T = pf2(P);
      m(R, P, T, b);
    }).addCase(t.fulfilled, (R, { meta: b, payload: P }) => {
      let T = pf2(b.arg);
      p(R, b, P, T);
    }).addCase(t.rejected, (R, { meta: { condition: b, arg: P, requestId: T }, error: B, payload: D }) => {
      Ju2(R, P.queryCacheKey, (O) => {
        if (!b) {
          if (O.requestId !== T)
            return;
          O.status = "rejected", O.error = D ?? B;
        }
      });
    }).addMatcher(s, (R, b) => {
      let { queries: P } = i(b);
      for (let [T, B] of Object.entries(P))
        (B?.status === "fulfilled" || B?.status === "rejected") && (R[T] = B);
    });
  } }), f = Yn2({ name: `${e7}/mutations`, initialState: _s2, reducers: { removeMutationResult: { reducer(v, { payload: R }) {
    let b = $s(R);
    b in v && delete v[b];
  }, prepare: Lo2() } }, extraReducers(v) {
    v.addCase(r.pending, (R, { meta: b, meta: { requestId: P, arg: T, startedTimeStamp: B } }) => {
      T.track && (R[$s(b)] = { requestId: P, status: "pending", endpointName: T.endpointName, startedTimeStamp: B });
    }).addCase(r.fulfilled, (R, { payload: b, meta: P }) => {
      P.arg.track && gC2(R, P, (T) => {
        T.requestId === P.requestId && (T.status = "fulfilled", T.data = b, T.fulfilledTimeStamp = P.fulfilledTimeStamp);
      });
    }).addCase(r.rejected, (R, { payload: b, error: P, meta: T }) => {
      T.arg.track && gC2(R, T, (B) => {
        B.requestId === T.requestId && (B.status = "rejected", B.error = b ?? P);
      });
    }).addMatcher(s, (R, b) => {
      let { mutations: P } = i(b);
      for (let [T, B] of Object.entries(P))
        (B?.status === "fulfilled" || B?.status === "rejected") && T !== B?.requestId && (R[T] = B);
    });
  } }), A = Yn2({ name: `${e7}/invalidation`, initialState: _s2, reducers: { updateProvidedBy: { reducer(v, R) {
    var T, B;
    let { queryCacheKey: b, providedTags: P } = R.payload;
    for (let D of Object.values(v))
      for (let O of Object.values(D)) {
        let k = O.indexOf(b);
        k !== -1 && O.splice(k, 1);
      }
    for (let { type: D, id: O } of P) {
      let k = (T = v[D] ?? (v[D] = {}))[B = O || "__internal_without_id"] ?? (T[B] = []);
      k.includes(b) || k.push(b);
    }
  }, prepare: Lo2() } }, extraReducers(v) {
    v.addCase(d.actions.removeQueryResult, (R, { payload: { queryCacheKey: b } }) => {
      for (let P of Object.values(R))
        for (let T of Object.values(P)) {
          let B = T.indexOf(b);
          B !== -1 && T.splice(B, 1);
        }
    }).addMatcher(s, (R, b) => {
      var T, B;
      let { provided: P } = i(b);
      for (let [D, O] of Object.entries(P))
        for (let [k, Q] of Object.entries(O)) {
          let q = (T = R[D] ?? (R[D] = {}))[B = k || "__internal_without_id"] ?? (T[B] = []);
          for (let U of Q)
            q.includes(U) || q.push(U);
        }
    }).addMatcher(Mt2(Pr2(t), us2(t)), (R, b) => {
      let P = IC2(b, "providesTags", o, c), { queryCacheKey: T } = b.meta.arg;
      A.caseReducers.updateProvidedBy(R, A.actions.updateProvidedBy({ queryCacheKey: T, providedTags: P }));
    });
  } }), S = Yn2({ name: `${e7}/subscriptions`, initialState: _s2, reducers: { updateSubscriptionOptions(v, R) {
  }, unsubscribeQueryResult(v, R) {
  }, internal_getRTKQSubscriptions() {
  } } }), g = Yn2({ name: `${e7}/internalSubscriptions`, initialState: _s2, reducers: { subscriptionsUpdated: { reducer(v, R) {
    return tm2(v, R.payload);
  }, prepare: Lo2() } } }), C = Yn2({ name: `${e7}/config`, initialState: { online: LT2(), focused: QT2(), middlewareRegistered: false, ...u }, reducers: { middlewareRegistered(v, { payload: R }) {
    v.middlewareRegistered = v.middlewareRegistered === "conflict" || a !== R ? "conflict" : true;
  } }, extraReducers: (v) => {
    v.addCase(gf2, (R) => {
      R.online = true;
    }).addCase(PC2, (R) => {
      R.online = false;
    }).addCase(ff2, (R) => {
      R.focused = true;
    }).addCase(vC2, (R) => {
      R.focused = false;
    }).addMatcher(s, (R) => ({ ...R }));
  } }), y = Vo({ queries: d.reducer, mutations: f.reducer, provided: A.reducer, subscriptions: g.reducer, config: C.reducer }), F2 = (v, R) => y(l.match(R) ? void 0 : v, R), I = { ...C.actions, ...d.actions, ...S.actions, ...g.actions, ...f.actions, ...A.actions, resetApiState: l };
  return { reducer: F2, actions: I };
}
var lf2 = Symbol.for("RTKQ/skipToken");
var EC2 = { status: "uninitialized" };
var SC2 = vr2(EC2, () => {
});
var hC2 = vr2(EC2, () => {
});
function rk2({ serializeQueryArgs: e7, reducerPath: t, createSelector: r }) {
  let n = (y) => SC2, o = (y) => hC2;
  return { buildQuerySelector: p, buildInfiniteQuerySelector: d, buildMutationSelector: f, selectInvalidatedBy: A, selectCachedArgsForQuery: S, selectApiState: i, selectQueries: s, selectMutations: u, selectQueryEntry: c, selectConfig: l };
  function a(y) {
    return { ...y, ...uC2(y.status) };
  }
  function i(y) {
    return y[t];
  }
  function s(y) {
    return i(y)?.queries;
  }
  function c(y, F2) {
    return s(y)?.[F2];
  }
  function u(y) {
    return i(y)?.mutations;
  }
  function l(y) {
    return i(y)?.config;
  }
  function m(y, F2, I) {
    return (v) => {
      if (v === lf2)
        return r(n, I);
      let R = e7({ queryArgs: v, endpointDefinition: F2, endpointName: y });
      return r((P) => c(P, R) ?? SC2, I);
    };
  }
  function p(y, F2) {
    return m(y, F2, a);
  }
  function d(y, F2) {
    let { infiniteQueryOptions: I } = F2;
    function v(R) {
      let b = { ...R, ...uC2(R.status) }, { isLoading: P, isError: T, direction: B } = b, D = B === "forward", O = B === "backward";
      return { ...b, hasNextPage: g(I, b.data), hasPreviousPage: C(I, b.data), isFetchingNextPage: P && D, isFetchingPreviousPage: P && O, isFetchNextPageError: T && D, isFetchPreviousPageError: T && O };
    }
    return m(y, F2, v);
  }
  function f() {
    return (y) => {
      let F2;
      return typeof y == "object" ? F2 = $s(y) ?? lf2 : F2 = y, r(F2 === lf2 ? o : (R) => i(R)?.mutations?.[F2] ?? hC2, a);
    };
  }
  function A(y, F2) {
    let I = y[t], v = /* @__PURE__ */ new Set();
    for (let R of F2.filter(Xu2).map(df2)) {
      let b = I.provided[R.type];
      if (!b)
        continue;
      let P = (R.id !== void 0 ? b[R.id] : dC2(Object.values(b))) ?? [];
      for (let T of P)
        v.add(T);
    }
    return dC2(Array.from(v.values()).map((R) => {
      let b = I.queries[R];
      return b ? [{ queryCacheKey: R, endpointName: b.endpointName, originalArgs: b.originalArgs }] : [];
    }));
  }
  function S(y, F2) {
    return Object.values(s(y)).filter((I) => I?.endpointName === F2 && I.status !== "uninitialized").map((I) => I.originalArgs);
  }
  function g(y, F2) {
    return F2 ? mf2(y, F2) != null : false;
  }
  function C(y, F2) {
    return !F2 || !y.getPreviousPageParam ? false : wC2(y, F2) != null;
  }
}
var yC2 = WeakMap ? /* @__PURE__ */ new WeakMap() : void 0;
var CC2 = ({ endpointName: e7, queryArgs: t }) => {
  let r = "", n = yC2?.get(t);
  if (typeof n == "string")
    r = n;
  else {
    let o = JSON.stringify(t, (a, i) => (i = typeof i == "bigint" ? { $bigint: i.toString() } : i, i = Nt2(i) ? Object.keys(i).sort().reduce((s, c) => (s[c] = i[c], s), {}) : i, i));
    Nt2(t) && yC2?.set(t, o), r = o;
  }
  return `${e7}(${r})`;
};
function nk2(...e7) {
  return function(r) {
    let n = Mo2((u) => r.extractRehydrationInfo?.(u, { reducerPath: r.reducerPath ?? "api" })), o = { reducerPath: "api", keepUnusedDataFor: 60, refetchOnMountOrArgChange: false, refetchOnFocus: false, refetchOnReconnect: false, invalidationBehavior: "delayed", ...r, extractRehydrationInfo: n, serializeQueryArgs(u) {
      let l = CC2;
      if ("serializeQueryArgs" in u.endpointDefinition) {
        let m = u.endpointDefinition.serializeQueryArgs;
        l = (p) => {
          let d = m(p);
          return typeof d == "string" ? d : CC2({ ...p, queryArgs: d });
        };
      } else
        r.serializeQueryArgs && (l = r.serializeQueryArgs);
      return l(u);
    }, tagTypes: [...r.tagTypes || []] }, a = { endpointDefinitions: {}, batch(u) {
      u();
    }, apiUid: $c2(), extractRehydrationInfo: n, hasRehydrationInfo: Mo2((u) => n(u) != null) }, i = { injectEndpoints: c, enhanceEndpoints({ addTagTypes: u, endpoints: l }) {
      if (u)
        for (let m of u)
          o.tagTypes.includes(m) || o.tagTypes.push(m);
      if (l)
        for (let [m, p] of Object.entries(l))
          typeof p == "function" ? p(a.endpointDefinitions[m]) : Object.assign(a.endpointDefinitions[m] || {}, p);
      return i;
    } }, s = e7.map((u) => u.init(i, o, a));
    function c(u) {
      let l = u.endpoints({ query: (m) => ({ ...m, type: "query" }), mutation: (m) => ({ ...m, type: "mutation" }), infiniteQuery: (m) => ({ ...m, type: "infinitequery" }) });
      for (let [m, p] of Object.entries(l)) {
        if (u.overrideExisting !== true && m in a.endpointDefinitions) {
          if (u.overrideExisting === "throw")
            throw new Error(Pt2(39));
          continue;
        }
        a.endpointDefinitions[m] = p;
        for (let d of s)
          d.injectEndpoint(m, p);
      }
      return i;
    }
    return i.injectEndpoints({ endpoints: r.endpoints });
  };
}
function kr2(e7, ...t) {
  return Object.assign(e7, ...t);
}
var ok3 = ({ api: e7, queryThunk: t, internalState: r }) => {
  let n = `${e7.reducerPath}/subscriptions`, o = null, a = null, { updateSubscriptionOptions: i, unsubscribeQueryResult: s } = e7.internalActions, c = (d, f) => {
    var S, g;
    if (i.match(f)) {
      let { queryCacheKey: C, requestId: y, options: F2 } = f.payload;
      return d?.[C]?.[y] && (d[C][y] = F2), true;
    }
    if (s.match(f)) {
      let { queryCacheKey: C, requestId: y } = f.payload;
      return d[C] && delete d[C][y], true;
    }
    if (e7.internalActions.removeQueryResult.match(f))
      return delete d[f.payload.queryCacheKey], true;
    if (t.pending.match(f)) {
      let { meta: { arg: C, requestId: y } } = f, F2 = d[S = C.queryCacheKey] ?? (d[S] = {});
      return F2[`${y}_running`] = {}, C.subscribe && (F2[y] = C.subscriptionOptions ?? F2[y] ?? {}), true;
    }
    let A = false;
    if (t.fulfilled.match(f) || t.rejected.match(f)) {
      let C = d[f.meta.arg.queryCacheKey] || {}, y = `${f.meta.requestId}_running`;
      A || (A = !!C[y]), delete C[y];
    }
    if (t.rejected.match(f)) {
      let { meta: { condition: C, arg: y, requestId: F2 } } = f;
      if (C && y.subscribe) {
        let I = d[g = y.queryCacheKey] ?? (d[g] = {});
        I[F2] = y.subscriptionOptions ?? I[F2] ?? {}, A = true;
      }
    }
    return A;
  }, u = () => r.currentSubscriptions, p = { getSubscriptions: u, getSubscriptionCount: (d) => {
    let A = u()[d] ?? {};
    return Oa2(A);
  }, isRequestSubscribed: (d, f) => !!u()?.[d]?.[f] };
  return (d, f) => {
    if (o || (o = JSON.parse(JSON.stringify(r.currentSubscriptions))), e7.util.resetApiState.match(d))
      return o = r.currentSubscriptions = {}, a = null, [true, false];
    if (e7.internalActions.internal_getRTKQSubscriptions.match(d))
      return [false, p];
    let A = c(r.currentSubscriptions, d), S = true;
    if (A) {
      a || (a = setTimeout(() => {
        let y = JSON.parse(JSON.stringify(r.currentSubscriptions)), [, F2] = Qc2(o, () => y);
        f.next(e7.internalActions.subscriptionsUpdated(F2)), o = y, a = null;
      }, 500));
      let g = typeof d.type == "string" && !!d.type.startsWith(n), C = t.rejected.match(d) && d.meta.condition && !!d.meta.arg.subscribe;
      S = !g && !C;
    }
    return [S, false];
  };
};
function ak2(e7) {
  for (let t in e7)
    return false;
  return true;
}
var ik2 = 2147483647 / 1e3 - 1;
var sk2 = ({ reducerPath: e7, api: t, queryThunk: r, context: n, internalState: o, selectors: { selectQueryEntry: a, selectConfig: i } }) => {
  let { removeQueryResult: s, unsubscribeQueryResult: c, cacheEntriesUpserted: u } = t.internalActions, l = Mt2(c.match, r.fulfilled, r.rejected, u.match);
  function m(S) {
    let g = o.currentSubscriptions[S];
    return !!g && !ak2(g);
  }
  let p = {}, d = (S, g, C) => {
    let y = g.getState(), F2 = i(y);
    if (l(S)) {
      let I;
      if (u.match(S))
        I = S.payload.map((v) => v.queryDescription.queryCacheKey);
      else {
        let { queryCacheKey: v } = c.match(S) ? S.payload : S.meta.arg;
        I = [v];
      }
      f(I, g, F2);
    }
    if (t.util.resetApiState.match(S))
      for (let [I, v] of Object.entries(p))
        v && clearTimeout(v), delete p[I];
    if (n.hasRehydrationInfo(S)) {
      let { queries: I } = n.extractRehydrationInfo(S);
      f(Object.keys(I), g, F2);
    }
  };
  function f(S, g, C) {
    let y = g.getState();
    for (let F2 of S) {
      let I = a(y, F2);
      A(F2, I?.endpointName, g, C);
    }
  }
  function A(S, g, C, y) {
    let I = n.endpointDefinitions[g]?.keepUnusedDataFor ?? y.keepUnusedDataFor;
    if (I === 1 / 0)
      return;
    let v = Math.max(0, Math.min(I, ik2));
    if (!m(S)) {
      let R = p[S];
      R && clearTimeout(R), p[S] = setTimeout(() => {
        m(S) || C.dispatch(s({ queryCacheKey: S })), delete p[S];
      }, v * 1e3);
    }
  }
  return d;
};
var xC2 = new Error("Promise never resolved before cacheEntryRemoved.");
var ck2 = ({ api: e7, reducerPath: t, context: r, queryThunk: n, mutationThunk: o, internalState: a, selectors: { selectQueryEntry: i, selectApiState: s } }) => {
  let c = jc2(n), u = jc2(o), l = Pr2(n, o), m = {};
  function p(g, C, y) {
    let F2 = m[g];
    F2?.valueResolved && (F2.valueResolved({ data: C, meta: y }), delete F2.valueResolved);
  }
  function d(g) {
    let C = m[g];
    C && (delete m[g], C.cacheEntryRemoved());
  }
  let f = (g, C, y) => {
    let F2 = A(g);
    function I(v, R, b, P) {
      let T = i(y, R), B = i(C.getState(), R);
      !T && B && S(v, P, R, C, b);
    }
    if (n.pending.match(g))
      I(g.meta.arg.endpointName, F2, g.meta.requestId, g.meta.arg.originalArgs);
    else if (e7.internalActions.cacheEntriesUpserted.match(g))
      for (let { queryDescription: v, value: R } of g.payload) {
        let { endpointName: b, originalArgs: P, queryCacheKey: T } = v;
        I(b, T, g.meta.requestId, P), p(T, R, {});
      }
    else if (o.pending.match(g))
      C.getState()[t].mutations[F2] && S(g.meta.arg.endpointName, g.meta.arg.originalArgs, F2, C, g.meta.requestId);
    else if (l(g))
      p(F2, g.payload, g.meta.baseQueryMeta);
    else if (e7.internalActions.removeQueryResult.match(g) || e7.internalActions.removeMutationResult.match(g))
      d(F2);
    else if (e7.util.resetApiState.match(g))
      for (let v of Object.keys(m))
        d(v);
  };
  function A(g) {
    return c(g) ? g.meta.arg.queryCacheKey : u(g) ? g.meta.arg.fixedCacheKey ?? g.meta.requestId : e7.internalActions.removeQueryResult.match(g) ? g.payload.queryCacheKey : e7.internalActions.removeMutationResult.match(g) ? $s(g.payload) : "";
  }
  function S(g, C, y, F2, I) {
    let v = r.endpointDefinitions[g], R = v?.onCacheEntryAdded;
    if (!R)
      return;
    let b = {}, P = new Promise((Q) => {
      b.cacheEntryRemoved = Q;
    }), T = Promise.race([new Promise((Q) => {
      b.valueResolved = Q;
    }), P.then(() => {
      throw xC2;
    })]);
    T.catch(() => {
    }), m[y] = b;
    let B = e7.endpoints[g].select(v.type === "query" ? C : y), D = F2.dispatch((Q, q, U) => U), O = { ...F2, getCacheEntry: () => B(F2.getState()), requestId: I, extra: D, updateCachedData: v.type === "query" ? (Q) => F2.dispatch(e7.util.updateQueryData(g, C, Q)) : void 0, cacheDataLoaded: T, cacheEntryRemoved: P }, k = R(C, O);
    Promise.resolve(k).catch((Q) => {
      if (Q !== xC2)
        throw Q;
    });
  }
  return f;
};
var uk2 = ({ api: e7, context: { apiUid: t }, reducerPath: r }) => (n, o) => {
  e7.util.resetApiState.match(n) && o.dispatch(e7.internalActions.middlewareRegistered(t));
};
var lk2 = ({ reducerPath: e7, context: t, context: { endpointDefinitions: r }, mutationThunk: n, queryThunk: o, api: a, assertTagType: i, refetchQuery: s, internalState: c }) => {
  let { removeQueryResult: u } = a.internalActions, l = Mt2(Pr2(n), us2(n)), m = Mt2(Pr2(n, o), Kn2(n, o)), p = [], d = (S, g) => {
    l(S) ? A(IC2(S, "invalidatesTags", r, i), g) : m(S) ? A([], g) : a.util.invalidateTags.match(S) && A(yf(S.payload, void 0, void 0, void 0, void 0, i), g);
  };
  function f(S) {
    let { queries: g, mutations: C } = S;
    for (let y of [g, C])
      for (let F2 in y)
        if (y[F2]?.status === "pending")
          return true;
    return false;
  }
  function A(S, g) {
    let C = g.getState(), y = C[e7];
    if (p.push(...S), y.config.invalidationBehavior === "delayed" && f(y))
      return;
    let F2 = p;
    if (p = [], F2.length === 0)
      return;
    let I = a.util.selectInvalidatedBy(C, F2);
    t.batch(() => {
      let v = Array.from(I.values());
      for (let { queryCacheKey: R } of v) {
        let b = y.queries[R], P = c.currentSubscriptions[R] ?? {};
        b && (Oa2(P) === 0 ? g.dispatch(u({ queryCacheKey: R })) : b.status !== "uninitialized" && g.dispatch(s(b)));
      }
    });
  }
  return d;
};
var dk2 = ({ reducerPath: e7, queryThunk: t, api: r, refetchQuery: n, internalState: o }) => {
  let a = {}, i = (d, f) => {
    (r.internalActions.updateSubscriptionOptions.match(d) || r.internalActions.unsubscribeQueryResult.match(d)) && u(d.payload, f), (t.pending.match(d) || t.rejected.match(d) && d.meta.condition) && u(d.meta.arg, f), (t.fulfilled.match(d) || t.rejected.match(d) && !d.meta.condition) && c(d.meta.arg, f), r.util.resetApiState.match(d) && m();
  };
  function c({ queryCacheKey: d }, f) {
    let A = f.getState()[e7], S = A.queries[d], g = o.currentSubscriptions[d];
    if (!S || S.status === "uninitialized")
      return;
    let { lowestPollingInterval: C, skipPollingIfUnfocused: y } = p(g);
    if (!Number.isFinite(C))
      return;
    let F2 = a[d];
    F2?.timeout && (clearTimeout(F2.timeout), F2.timeout = void 0);
    let I = Date.now() + C;
    a[d] = { nextPollTimestamp: I, pollingInterval: C, timeout: setTimeout(() => {
      (A.config.focused || !y) && f.dispatch(n(S)), c({ queryCacheKey: d }, f);
    }, C) };
  }
  function u({ queryCacheKey: d }, f) {
    let S = f.getState()[e7].queries[d], g = o.currentSubscriptions[d];
    if (!S || S.status === "uninitialized")
      return;
    let { lowestPollingInterval: C } = p(g);
    if (!Number.isFinite(C)) {
      l(d);
      return;
    }
    let y = a[d], F2 = Date.now() + C;
    (!y || F2 < y.nextPollTimestamp) && c({ queryCacheKey: d }, f);
  }
  function l(d) {
    let f = a[d];
    f?.timeout && clearTimeout(f.timeout), delete a[d];
  }
  function m() {
    for (let d of Object.keys(a))
      l(d);
  }
  function p(d = {}) {
    let f = false, A = Number.POSITIVE_INFINITY;
    for (let S in d)
      d[S].pollingInterval && (A = Math.min(d[S].pollingInterval, A), f = d[S].skipPollingIfUnfocused || f);
    return { lowestPollingInterval: A, skipPollingIfUnfocused: f };
  }
  return i;
};
var pk2 = ({ api: e7, context: t, queryThunk: r, mutationThunk: n }) => {
  let o = _c2(r, n), a = Kn2(r, n), i = Pr2(r, n), s = {};
  return (u, l) => {
    if (o(u)) {
      let { requestId: m, arg: { endpointName: p, originalArgs: d } } = u.meta, f = t.endpointDefinitions[p], A = f?.onQueryStarted;
      if (A) {
        let S = {}, g = new Promise((I, v) => {
          S.resolve = I, S.reject = v;
        });
        g.catch(() => {
        }), s[m] = S;
        let C = e7.endpoints[p].select(f.type === "query" ? d : m), y = l.dispatch((I, v, R) => R), F2 = { ...l, getCacheEntry: () => C(l.getState()), requestId: m, extra: y, updateCachedData: f.type === "query" ? (I) => l.dispatch(e7.util.updateQueryData(p, d, I)) : void 0, queryFulfilled: g };
        A(d, F2);
      }
    } else if (i(u)) {
      let { requestId: m, baseQueryMeta: p } = u.meta;
      s[m]?.resolve({ data: u.payload, meta: p }), delete s[m];
    } else if (a(u)) {
      let { requestId: m, rejectedWithValue: p, baseQueryMeta: d } = u.meta;
      s[m]?.reject({ error: u.payload ?? u.error, isUnhandledError: !p, meta: d }), delete s[m];
    }
  };
};
var mk2 = ({ reducerPath: e7, context: t, api: r, refetchQuery: n, internalState: o }) => {
  let { removeQueryResult: a } = r.internalActions, i = (c, u) => {
    ff2.match(c) && s(u, "refetchOnFocus"), gf2.match(c) && s(u, "refetchOnReconnect");
  };
  function s(c, u) {
    let l = c.getState()[e7], m = l.queries, p = o.currentSubscriptions;
    t.batch(() => {
      for (let d of Object.keys(p)) {
        let f = m[d], A = p[d];
        if (!A || !f)
          continue;
        (Object.values(A).some((g) => g[u] === true) || Object.values(A).every((g) => g[u] === void 0) && l.config[u]) && (Oa2(A) === 0 ? c.dispatch(a({ queryCacheKey: d })) : f.status !== "uninitialized" && c.dispatch(n(f)));
      }
    });
  }
  return i;
};
function fk2(e7) {
  let { reducerPath: t, api: n, context: o } = e7, { apiUid: a } = o, i = { invalidateTags: h3(`${t}/invalidateTags`) }, s = (m) => m.type.startsWith(`${t}/`), c = [uk2, sk2, lk2, dk2, ck2, pk2];
  return { middleware: (m) => {
    let p = false, f = { ...e7, internalState: { currentSubscriptions: {} }, refetchQuery: l, isThisApiSliceAction: s }, A = c.map((C) => C(f)), S = ok3(f), g = mk2(f);
    return (C) => (y) => {
      if (!qc2(y))
        return C(y);
      p || (p = true, m.dispatch(n.internalActions.middlewareRegistered(a)));
      let F2 = { ...m, next: C }, I = m.getState(), [v, R] = S(y, F2, I), b;
      if (v ? b = C(y) : b = R, m.getState()[t] && (g(y, F2, I), s(y) || o.hasRehydrationInfo(y)))
        for (let P of A)
          P(y, F2, I);
      return b;
    };
  }, actions: i };
  function l(m) {
    return e7.api.endpoints[m.endpointName].initiate(m.originalArgs, { subscribe: false, forceRefetch: true });
  }
}
var AC2 = Symbol();
var gk2 = ({ createSelector: e7 = Y2 } = {}) => ({ name: AC2, init(t, { baseQuery: r, tagTypes: n, reducerPath: o, serializeQueryArgs: a, keepUnusedDataFor: i, refetchOnMountOrArgChange: s, refetchOnFocus: c, refetchOnReconnect: u, invalidationBehavior: l }, m) {
  _S2();
  let p = (X) => X;
  Object.assign(t, { reducerPath: o, endpoints: {}, internalActions: { onOnline: gf2, onOffline: PC2, onFocus: ff2, onFocusLost: vC2 }, util: {} });
  let d = rk2({ serializeQueryArgs: a, reducerPath: o, createSelector: e7 }), { selectInvalidatedBy: f, selectCachedArgsForQuery: A, buildQuerySelector: S, buildInfiniteQuerySelector: g, buildMutationSelector: C } = d;
  kr2(t.util, { selectInvalidatedBy: f, selectCachedArgsForQuery: A });
  let { queryThunk: y, infiniteQueryThunk: F2, mutationThunk: I, patchQueryData: v, updateQueryData: R, upsertQueryData: b, prefetch: P, buildMatchThunkActions: T } = ek2({ baseQuery: r, reducerPath: o, context: m, api: t, serializeQueryArgs: a, assertTagType: p, selectors: d }), { reducer: B, actions: D } = tk2({ context: m, queryThunk: y, mutationThunk: I, serializeQueryArgs: a, reducerPath: o, assertTagType: p, config: { refetchOnFocus: c, refetchOnReconnect: u, refetchOnMountOrArgChange: s, keepUnusedDataFor: i, reducerPath: o, invalidationBehavior: l } });
  kr2(t.util, { patchQueryData: v, updateQueryData: R, upsertQueryData: b, prefetch: P, resetApiState: D.resetApiState, upsertQueryEntries: D.cacheEntriesUpserted }), kr2(t.internalActions, D);
  let { middleware: O, actions: k } = fk2({ reducerPath: o, context: m, queryThunk: y, mutationThunk: I, infiniteQueryThunk: F2, api: t, assertTagType: p, selectors: d });
  kr2(t.util, k), kr2(t, { reducer: B, middleware: O });
  let { buildInitiateQuery: Q, buildInitiateInfiniteQuery: q, buildInitiateMutation: U, getRunningMutationThunk: _, getRunningMutationsThunk: H2, getRunningQueriesThunk: ee, getRunningQueryThunk: oe } = XT2({ queryThunk: y, mutationThunk: I, infiniteQueryThunk: F2, api: t, serializeQueryArgs: a, context: m });
  return kr2(t.util, { getRunningMutationThunk: _, getRunningMutationsThunk: H2, getRunningQueryThunk: oe, getRunningQueriesThunk: ee }), { name: AC2, injectEndpoint(X, te) {
    var ge;
    let re = (ge = t.endpoints)[X] ?? (ge[X] = {});
    Sf2(te) && kr2(re, { name: X, select: S(X, te), initiate: Q(X, te) }, T(y, X)), KT2(te) && kr2(re, { name: X, select: C(), initiate: U(X) }, T(I, X)), hf2(te) && kr2(re, { name: X, select: g(X, te), initiate: q(X, te) }, T(y, X));
  } };
} });
var TC = nk2(gk2());
var Sk2 = async (e7, t, r) => {
  let n = t.getState(), { accessToken: o, environment: a, organizationId: i } = n.configuration, s = n.generatedAnswer.answerConfigurationId, c = { ...e7, headers: { ...e7?.headers || {}, Authorization: `Bearer ${o}` } };
  try {
    let u = Me2(i, a);
    return { data: RC2({ baseUrl: `${u}/rest/organizations/${i}/answer/v1/configs/${s}` })(c, t, r) };
  } catch (u) {
    return { error: u };
  }
};
var Zu2 = TC({ reducerPath: "answer", baseQuery: bC2(Sk2, { maxRetries: 3 }), endpoints: () => ({}) });
var hk2 = (e7, t) => {
  let { contentFormat: r } = t;
  e7.contentFormat = r, e7.isStreaming = true, e7.isLoading = false;
};
var yk2 = (e7, t) => {
  e7.answer === void 0 ? e7.answer = t.textDelta : typeof t.textDelta == "string" && (e7.answer = e7.answer.concat(t.textDelta));
};
var Ck2 = (e7, t) => {
  e7.citations = t.citations;
};
var xk2 = (e7, t) => {
  e7.generated = t.answerGenerated, e7.isStreaming = false;
};
var Ak = (e7, t) => {
  e7.error = { message: t.errorMessage, code: t.code }, e7.isStreaming = false, e7.isLoading = false, console.error(`${t.errorMessage} - code ${t.code}`);
};
var Fk2 = (e7, t, r) => {
  let n = JSON.parse(e7.data);
  n.finishReason === "ERROR" && n.errorMessage && Ak(t, n);
  let o = n.payload.length ? JSON.parse(n.payload) : {};
  switch (n.payloadType) {
    case "genqa.headerMessageType":
      o.contentFormat && (hk2(t, o), r(Us2(o.contentFormat)));
      break;
    case "genqa.messageType":
      o.textDelta && (yk2(t, o), r(Qs2({ textDelta: o.textDelta })));
      break;
    case "genqa.citationsType":
      o.citations && (Ck2(t, o), r(Ls2({ citations: o.citations })));
      break;
    case "genqa.endOfStreamType":
      xk2(t, o), r(Ds(o.answerGenerated ?? false));
      break;
  }
};
var oo2 = Zu2.injectEndpoints({ overrideExisting: true, endpoints: (e7) => ({ getAnswer: e7.query({ queryFn: () => ({ data: { contentFormat: void 0, answer: void 0, citations: void 0, error: void 0, generated: false, isStreaming: true, isLoading: true } }), async onCacheEntryAdded(t, { getState: r, cacheDataLoaded: n, updateCachedData: o, dispatch: a }) {
  await n;
  let { configuration: i, generatedAnswer: s, insightConfiguration: c } = r(), { organizationId: u, environment: l, accessToken: m } = i, p = Me2(u, l), d = `${p}/rest/organizations/${u}/insight/v1/configs/${c?.insightId}/answer/${s.answerConfigurationId}/generate`, f = `${p}/rest/organizations/${u}/answer/v1/configs/${s.answerConfigurationId}/generate`;
  await vc(c ? d : f, { method: "POST", body: JSON.stringify(t), headers: { Authorization: `Bearer ${m}`, Accept: "application/json", "Content-Type": "application/json", "Accept-Encoding": "*" }, fetch, onopen: async (A) => {
    let S = A.headers.get("x-answer-id");
    S && o((g) => {
      g.answerId = S;
    });
  }, onmessage: (A) => {
    o((S) => {
      Fk2(A, S, a);
    });
  }, onerror: (A) => {
    throw A;
  }, onclose: () => {
    o((A) => {
      a(no2(!A.generated));
    });
  } });
} }) }) });
Y2((e7) => ks(e7)?.q, (e7) => e7.search.requestId, (e7, t) => ({ q: e7, requestId: t }));
var el2 = {};
var bk = (e7) => e7.pagination ? e7.pagination.firstResult + e7.pagination.numberOfResults > 5e3 ? 5e3 - e7.pagination.firstResult : e7.pagination.numberOfResults : void 0;
var OC = (e7, t) => {
  let r = ks(e7)?.q, n = cC2(e7), o = sC2(e7), a = eC2(e7) ?? [];
  return { q: r, pipelineRuleParameters: { mlGenerativeQuestionAnswering: { responseFormat: e7.generatedAnswer.responseFormat, citationsFieldToInclude: a } }, ...n?.length && { searchHub: n }, ...o?.length && { pipeline: o }, ...el2[r]?.length && { facets: el2[r] }, ...e7.fields && { fieldsToInclude: e7.fields.fieldsToInclude }, ...e7.didYouMean && { queryCorrection: { enabled: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "next", options: { automaticallyCorrect: e7.didYouMean.automaticallyCorrectQuery ? "whenNoResults" : "never" } }, enableDidYouMean: e7.didYouMean.enableDidYouMean && e7.didYouMean.queryCorrectionMode === "legacy" }, ...e7.pagination && { numberOfResults: bk(e7), firstResult: e7.pagination.firstResult }, tab: e7.configuration.analytics.originLevel2 };
};
var qs2 = (e7) => oo2.endpoints.getAnswer.select(OC(e7))(e7);
$2(Jn2, (e7) => e7);
var _C = Vt2(MC2());
var Da2 = h3("tab/register", (e7) => {
  let t = new RecordValue2({ values: { id: V2, expression: se } });
  return x(e7, t);
});
var ot2 = h3("tab/updateActiveTab", (e7) => x(e7, V2));
var tl = Vt2(Su2());
var BC2 = Vt2(QC2());
var UC2 = Vt2(LC2());
tl.default.extend(UC2.default);
tl.default.extend(BC2.default);
var Va = () => ({ organizationId: "", accessToken: "", search: { locale: "en-US", timezone: tl.default.tz.guess(), authenticationProviders: [] }, analytics: { enabled: true, originContext: "Search", originLevel2: "default", originLevel3: "default", anonymous: false, deviceId: "", userDisplayName: "", documentLocation: "", trackingId: "", analyticsMode: "next", source: {} }, knowledge: { answerConfigurationId: "" }, environment: "prod" });
var rl = $2(Va(), (e7) => e7.addCase(Ut2, (t, r) => {
  Ek2(t, r.payload);
}).addCase(mt2, (t, r) => {
  Tk(t, r.payload);
}).addCase(Xr2, (t, r) => {
  kk(t, r.payload);
}).addCase(ta2, (t) => {
  t.analytics.enabled = false;
}).addCase(ra2, (t) => {
  t.analytics.enabled = true;
}).addCase(du2, (t, r) => {
  t.analytics.originLevel2 = r.payload.originLevel2;
}).addCase(pu2, (t, r) => {
  t.analytics.originLevel3 = r.payload.originLevel3;
}).addCase(ot2, (t, r) => {
  t.analytics.originLevel2 = r.payload;
}).addCase(ce2, (t, r) => {
  t.analytics.originLevel2 = r.payload.tab || t.analytics.originLevel2;
}));
function Ek2(e7, t) {
  isNullOrUndefined2(t.accessToken) || (e7.accessToken = t.accessToken), e7.environment = t.environment ?? "prod", isNullOrUndefined2(t.organizationId) || (e7.organizationId = t.organizationId);
}
function Tk(e7, t) {
  isNullOrUndefined2(t.proxyBaseUrl) || (e7.search.apiBaseUrl = t.proxyBaseUrl), isNullOrUndefined2(t.locale) || (e7.search.locale = t.locale), isNullOrUndefined2(t.timezone) || (e7.search.timezone = t.timezone), isNullOrUndefined2(t.authenticationProviders) || (e7.search.authenticationProviders = t.authenticationProviders);
}
function kk(e7, t) {
  isNullOrUndefined2(t.enabled) || (e7.analytics.enabled = t.enabled), isNullOrUndefined2(t.originContext) || (e7.analytics.originContext = t.originContext), isNullOrUndefined2(t.originLevel2) || (e7.analytics.originLevel2 = t.originLevel2), isNullOrUndefined2(t.originLevel3) || (e7.analytics.originLevel3 = t.originLevel3), isNullOrUndefined2(t.proxyBaseUrl) || (e7.analytics.apiBaseUrl = t.proxyBaseUrl), isNullOrUndefined2(t.trackingId) || (e7.analytics.trackingId = t.trackingId), isNullOrUndefined2(t.analyticsMode) || (e7.analytics.analyticsMode = t.analyticsMode), isNullOrUndefined2(t.source) || (e7.analytics.source = t.source);
  let r = (0, _C.default)();
  r && (e7.analytics.analyticsMode = "next", e7.analytics.trackingId = r), isNullOrUndefined2(t.runtimeEnvironment) || (e7.analytics.runtimeEnvironment = t.runtimeEnvironment), isNullOrUndefined2(t.anonymous) || (e7.analytics.anonymous = t.anonymous), isNullOrUndefined2(t.deviceId) || (e7.analytics.deviceId = t.deviceId), isNullOrUndefined2(t.userDisplayName) || (e7.analytics.userDisplayName = t.userDisplayName), isNullOrUndefined2(t.documentLocation) || (e7.analytics.documentLocation = t.documentLocation);
}
var G = rl;
Vt2(nx());
function j(e7) {
  let t, r = /* @__PURE__ */ new Map(), n = () => r.size === 0, o = (a) => {
    try {
      let i = JSON.stringify(a), s = t !== i;
      return t = i, s;
    } catch (i) {
      return console.warn('Could not detect if state has changed, check the controller "get state method"', i), true;
    }
  };
  return { subscribe(a) {
    a();
    let i = Symbol(), s;
    return n() && (t = JSON.stringify(this.state), s = e7.subscribe(() => {
      o(this.state) && r.forEach((c) => c());
    })), r.set(i, a), () => {
      r.delete(i), n() && s && s();
    };
  }, get state() {
    return {};
  } };
}
var Sn2 = h3("fields/registerFieldsToInclude", (e7) => x(e7, kc2));
var Ma2 = h3("fields/fetchall/enable");
var io2 = h3("fields/fetchall/disable");
var Qa2 = W2("fields/fetchDescription", async (e7, { extra: t, getState: r, rejectWithValue: n }) => {
  let o = r(), { accessToken: a, environment: i, organizationId: s } = o.configuration, { apiBaseUrl: c } = o.configuration.search, u = await t.apiClient.fieldDescriptions({ accessToken: a, organizationId: s, url: c ?? ve2(s, i) });
  return we2(u) ? n(u.error) : u.success.fields;
});
var Mf2 = { collectionField: new StringValue2({ emptyAllowed: false, required: false }), parentField: new StringValue2({ emptyAllowed: false, required: false }), childField: new StringValue2({ emptyAllowed: false, required: false }), numberOfFoldedResults: new NumberValue2({ min: 0, required: false }) };
var hn2 = h3("folding/register", (e7) => x(e7, Mf2));
var yn2 = W2("folding/loadCollection", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, navigatorContext: o } }) => {
  let a = t(), i = a.configuration.analytics.analyticsMode === "legacy" ? await rn2(a) : ha2(a, o), s = await n.search({ ...i, q: xO(a), enableQuerySyntax: true, cq: `@${a.folding.fields.collection}="${e7}"`, filterField: a.folding.fields.collection, childField: a.folding.fields.parent, parentField: a.folding.fields.child, filterFieldRange: 100 }, { origin: "foldingCollection" });
  return we2(s) ? r(s.error) : { collectionId: e7, results: s.success.results, searchUid: s.success.searchUid, rootResult: a.folding.collections[e7].result };
});
function xO(e7) {
  return e7.query.q === "" ? "" : e7.query.enableQuerySyntax ? `${e7.query.q} OR @uri` : `( <@- ${e7.query.q} -@> ) OR @uri`;
}
var il = () => ({ enabled: false, fields: { collection: "foldingcollection", parent: "foldingparent", child: "foldingchild" }, filterFieldRange: 2, collections: {} });
var Qf = ["author", "language", "urihash", "objecttype", "collection", "source", "permanentid"];
var Rx2 = () => ({ fieldsToInclude: Qf, fetchAllFields: false, fieldsDescription: [] });
$2(Rx2(), (e7) => e7.addCase(Sn2, (t, r) => {
  t.fieldsToInclude = [...new Set(t.fieldsToInclude.concat(r.payload))];
}).addCase(Ma2, (t) => {
  t.fetchAllFields = true;
}).addCase(io2, (t) => {
  t.fetchAllFields = false;
}).addCase(Qa2.fulfilled, (t, { payload: r }) => {
  t.fieldsDescription = r;
}).addCase(hn2, (t, { payload: r }) => {
  let n = il().fields;
  t.fieldsToInclude.push(r.collectionField ?? n.collection, r.parentField ?? n.parent, r.childField ?? n.child);
}));
var EO = new ArrayValue2({ each: V2, required: true });
var bx = (e7, t) => (x(e7, V2), isString2(t) ? x(t, V2) : x(t, EO), { payload: { contextKey: e7, contextValue: t } });
var so2 = h3("context/set", (e7) => {
  for (let [t, r] of Object.entries(e7))
    bx(t, r);
  return { payload: e7 };
});
var co2 = h3("context/add", (e7) => bx(e7.contextKey, e7.contextValue));
var uo2 = h3("context/remove", (e7) => x(e7, V2));
$2(Ru2(), (e7) => {
  e7.addCase(so2, (t, r) => {
    t.contextValues = r.payload;
  }).addCase(co2, (t, r) => {
    t.contextValues[r.payload.contextKey] = r.payload.contextValue;
  }).addCase(uo2, (t, r) => {
    delete t.contextValues[r.payload];
  }).addCase(ae2.fulfilled, (t, r) => {
    r.payload && (t.contextValues = r.payload.context.contextValues);
  });
});
var La2 = h3("dictionaryFieldContext/set", (e7) => {
  let t = new RecordValue2({ options: { required: true } }), r = x(e7, t).error;
  if (r)
    return { payload: e7, error: r };
  let n = Object.values(e7), o = new ArrayValue2({ each: se }), a = x(n, o).error;
  return a ? { payload: e7, error: a } : { payload: e7 };
});
var Ba2 = h3("dictionaryFieldContext/add", (e7) => {
  let t = new RecordValue2({ options: { required: true }, values: { field: se, key: se } });
  return x(e7, t);
});
var Ua2 = h3("dictionaryFieldContext/remove", (e7) => x(e7, se));
$2(bu2(), (e7) => {
  e7.addCase(La2, (t, r) => {
    t.contextValues = r.payload;
  }).addCase(Ba2, (t, r) => {
    let { field: n, key: o } = r.payload;
    t.contextValues[n] = o;
  }).addCase(Ua2, (t, r) => {
    delete t.contextValues[r.payload];
  }).addCase(ae2.fulfilled, (t, r) => {
    r.payload && (t.contextValues = r.payload.dictionaryFieldContext.contextValues);
  });
});
Y2((e7) => e7.queryCorrection.correctedQuery !== "" || e7.wasCorrectedTo !== "", (e7) => e7);
var ul = () => ({ correctedQuery: "", wordCorrections: [], originalQuery: "" });
var Ix2 = () => ({ correctedQuery: "", corrections: [], originalQuery: "" });
function Ex2() {
  return { enableDidYouMean: false, wasCorrectedTo: "", wasAutomaticallyCorrected: false, queryCorrection: ul(), originalQuery: "", automaticallyCorrectQuery: true, queryCorrectionMode: "legacy" };
}
var Tx = (e7, t) => {
  let r = { ...Ix2(), ...t, correctedQuery: t?.correctedQuery || t?.corrections[0]?.correctedQuery || "" };
  e7.queryCorrection = r, e7.wasCorrectedTo = r.correctedQuery;
};
$2(Ex2(), (e7) => {
  e7.addCase(Ca2, (t) => {
    t.enableDidYouMean = true;
  }).addCase(xu2, (t) => {
    t.enableDidYouMean = false;
  }).addCase(Au, (t) => {
    t.automaticallyCorrectQuery = true;
  }).addCase(xa2, (t) => {
    t.automaticallyCorrectQuery = false;
  }).addCase(N2.pending, (t) => {
    t.queryCorrection = ul(), t.wasAutomaticallyCorrected = false, t.wasCorrectedTo = "";
  }).addCase(N2.fulfilled, (t, r) => {
    let { queryCorrection: n, queryCorrections: o } = r.payload.response;
    if (t.queryCorrectionMode === "legacy") {
      let a = o && o[0] ? o[0] : ul();
      t.queryCorrection = a;
    }
    t.queryCorrectionMode === "next" && Tx(t, n), t.wasAutomaticallyCorrected = r.payload.automaticallyCorrected, t.originalQuery = r.payload.originalQuery;
  }).addCase(St2, (t, r) => {
    t.wasCorrectedTo = r.payload;
  }).addCase(ro2, (t, r) => {
    t.queryCorrectionMode = r.payload;
  });
});
var K2 = V2;
var Z2 = h3("facetOptions/update", (e7 = { freezeFacetOrder: true }) => x(e7, { freezeFacetOrder: new BooleanValue2({ required: false }) }));
var Be2 = h3("facetOptions/facet/enable", (e7) => x(e7, K2));
var pe2 = h3("facetOptions/facet/disable", (e7) => x(e7, K2));
var zs2 = { facetId: K2, captions: new RecordValue2({ options: { required: false } }), numberOfValues: new NumberValue2({ required: false, min: 1 }), query: new StringValue2({ required: false, emptyAllowed: true }) };
var JO = { path: new ArrayValue2({ required: true, each: V2 }), displayValue: se, rawValue: se, count: new NumberValue2({ required: true, min: 0 }) };
var _a2 = h3("categoryFacet/selectSearchResult", (e7) => x(e7, { facetId: K2, value: new RecordValue2({ values: JO }) }));
var ja2 = h3("categoryFacetSearch/register", (e7) => x(e7, zs2));
function $a2(e7, t) {
  let { facetId: r, criterion: n } = t, o = e7[r]?.request;
  o && (o.sortCriteria = n);
}
function Ks2(e7) {
  e7 && (e7.currentValues = e7.currentValues.map((t) => ({ ...t, state: "idle" })), e7.preventAutoSelect = true);
}
function dl2(e7, t) {
  e7 && (e7.numberOfValues = t);
}
function pl(e7, t) {
  let r = e7[t];
  r && (r.request.numberOfValues = r.initialNumberOfValues, r.request.currentValues = [], r.request.preventAutoSelect = true);
}
function Bf2(e7, t, r) {
  e7.currentValues = XO(t, r), e7.numberOfValues = t.length ? 1 : r, e7.preventAutoSelect = true;
}
function XO(e7, t) {
  if (!e7.length)
    return [];
  let r = Ox(e7[0], t), n = r;
  for (let o of e7.splice(1)) {
    let a = Ox(o, t);
    n.children.push(a), n = a;
  }
  return n.state = "selected", n.retrieveChildren = true, [r];
}
function Ox(e7, t) {
  return { value: e7, retrieveCount: t, children: [], state: "idle", retrieveChildren: false };
}
var oq2 = { state: new Value2({ required: true }), numberOfResults: new NumberValue2({ required: true, min: 0 }), value: new StringValue2({ required: true, emptyAllowed: true }), path: new ArrayValue2({ required: true, each: V2 }), moreValuesAvailable: new BooleanValue2({ required: false }) };
function Uf2(e7) {
  e7.children.forEach((t) => {
    Uf2(t);
  }), ct2({ state: e7.state, numberOfResults: e7.numberOfResults, value: e7.value, path: e7.path, moreValuesAvailable: e7.moreValuesAvailable }, oq2);
}
var Ga2 = { facetId: K2, field: V2, tabs: new RecordValue2({ options: { required: false }, values: { included: new ArrayValue2({ each: new StringValue2() }), excluded: new ArrayValue2({ each: new StringValue2() }) } }), activeTab: new StringValue2({ required: false }), delimitingCharacter: new StringValue2({ required: false, emptyAllowed: true }), filterFacetCount: new BooleanValue2({ required: false }), injectionDepth: new NumberValue2({ required: false, min: 0 }), numberOfValues: new NumberValue2({ required: false, min: 1 }), sortCriteria: new Value2({ required: false }), basePath: new ArrayValue2({ required: false, each: V2 }), filterByBasePath: new BooleanValue2({ required: false }) };
var Kt2 = h3("categoryFacet/register", (e7) => x(e7, Ga2));
var xn2 = h3("categoryFacet/toggleSelectValue", (e7) => {
  try {
    return ct2(e7.facetId, V2), Uf2(e7.selection), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br2(t) };
  }
});
var Yt2 = h3("categoryFacet/deselectAll", (e7) => x(e7, Ga2.facetId));
var lo2 = h3("categoryFacet/updateNumberOfValues", (e7) => x(e7, { facetId: Ga2.facetId, numberOfValues: Ga2.numberOfValues }));
var Wa2 = h3("categoryFacet/updateSortCriterion", (e7) => x(e7, { facetId: Ga2.facetId, criterion: new Value2() }));
var gl2 = h3("categoryFacet/updateBasePath", (e7) => x(e7, { facetId: Ga2.facetId, basePath: new ArrayValue2({ each: V2 }) }));
$2(Ho2(), (e7) => {
  e7.addCase(Kt2, (t, r) => {
    let n = r.payload, { facetId: o } = n;
    if (o in t)
      return;
    let a = sq2(n), i = a.numberOfValues;
    t[o] = { request: a, initialNumberOfValues: i };
  }).addCase(ae2.fulfilled, (t, r) => r.payload?.categoryFacetSet ?? t).addCase(ce2, (t, r) => {
    let n = r.payload.cf || {};
    Object.keys(t).forEach((o) => {
      let a = t[o].request, i = n[o] || [];
      (i.length || a.currentValues.length) && Bf2(a, i, t[o].initialNumberOfValues);
    });
  }).addCase(Wa2, (t, r) => {
    let { facetId: n, criterion: o } = r.payload, a = t[n]?.request;
    a && (a.sortCriteria = o);
  }).addCase(gl2, (t, r) => {
    let { facetId: n, basePath: o } = r.payload, a = t[n]?.request;
    a && (a.basePath = [...o]);
  }).addCase(xn2, (t, r) => {
    let { facetId: n, selection: o, retrieveCount: a } = r.payload, i = t[n]?.request;
    if (!i)
      return;
    let { path: s } = o, c = s.slice(0, s.length - 1), u = iq2(i, c, a);
    if (u.length) {
      let m = u[0];
      m.retrieveChildren = true, m.state = "selected", m.children = [];
      return;
    }
    let l = Mx(o.value, a);
    l.state = "selected", u.push(l), i.numberOfValues = 1;
  }).addCase(Yt2, (t, r) => {
    let n = r.payload;
    pl(t, n);
  }).addCase(Se2, (t) => {
    Object.keys(t).forEach((r) => pl(t, r));
  }).addCase(ft2, (t, r) => Object.keys(t).forEach((n) => {
    t[n].request.preventAutoSelect = !r.payload.allow;
  })).addCase(lo2, (t, r) => {
    let { facetId: n, numberOfValues: o } = r.payload, a = t[n]?.request;
    if (a) {
      if (!a.currentValues.length)
        return dl2(a, o);
      cq2(t, r.payload);
    }
  }).addCase(_a2, (t, r) => {
    let { facetId: n, value: o } = r.payload, a = t[n];
    if (!a)
      return;
    let i = [...o.path, o.rawValue];
    Bf2(a.request, i, a.initialNumberOfValues);
  }).addCase(Ht2.fulfilled, (t, r) => {
    Nx2(t, r.payload.response.facets);
  }).addCase(N2.fulfilled, (t, r) => {
    Nx2(t, r.payload.response.facets);
  }).addCase(pe2, (t, r) => {
    pl(t, r.payload);
  });
});
var Ys2 = { delimitingCharacter: ";", filterFacetCount: true, injectionDepth: 1e3, numberOfValues: 5, sortCriteria: "occurrences", basePath: [], filterByBasePath: true, resultsMustMatch: "atLeastOneValue" };
function iq2(e7, t, r) {
  let n = e7.currentValues;
  for (let o of t) {
    let a = n[0];
    (!a || o !== a.value) && (a = Mx(o, r), n.length = 0, n.push(a)), a.retrieveChildren = false, a.state = "idle", n = a.children;
  }
  return n;
}
function sq2(e7) {
  return { ...Ys2, currentValues: [], preventAutoSelect: false, type: "hierarchical", ...e7 };
}
function Mx(e7, t) {
  return { value: e7, state: "idle", children: [], retrieveChildren: true, retrieveCount: t };
}
function Nx2(e7, t) {
  t.forEach((r) => {
    if (!uq(e7, r))
      return;
    let n = r.facetId, o = e7[n]?.request;
    if (!o)
      return;
    let a = lq(o, r);
    o.currentValues = a ? [] : o.currentValues, o.preventAutoSelect = false;
  });
}
function cq2(e7, t) {
  let { facetId: r, numberOfValues: n } = t, o = e7[r]?.request.currentValues[0];
  if (o) {
    for (; o.children.length && o?.state !== "selected"; )
      o = o.children[0];
    o.retrieveCount = n;
  }
}
function uq(e7, t) {
  return t.facetId in e7;
}
function lq(e7, t) {
  let r = ze2(e7.currentValues), n = ze2(t.values);
  return r.length !== n.length;
}
var Js2 = ((r) => (r.Relevance = "relevance", r.Fields = "fields", r))(Js2 || {});
var Sl2 = ((r) => (r.Ascending = "asc", r.Descending = "desc", r))(Sl2 || {});
var Tt2 = (e7) => e7.error !== void 0;
function jx2(e7, t = "prod") {
  return `${Me2(e7, t)}/rest/organizations/${e7}/commerce/v2`;
}
var $x2 = (e7) => Sq2(e7.cartItems, e7.cart);
function Sq2(e7, t) {
  let r = e7.reduce((n, o) => {
    let { productId: a, quantity: i } = t[o];
    return a in n || (n[a] = { productId: a, quantity: 0 }), n[a].quantity += i, n;
  }, {});
  return [...Object.values(r)];
}
var Ha2 = (e7, t) => {
  let { view: r, location: n, ...o } = e7.commerceContext;
  return { accessToken: e7.configuration.accessToken, url: e7.configuration.commerce.apiBaseUrl ?? jx2(e7.configuration.organizationId, e7.configuration.environment), organizationId: e7.configuration.organizationId, trackingId: e7.configuration.analytics.trackingId, ...o, ...e7.configuration.analytics.enabled ? { clientId: t.clientId } : {}, context: { user: { ...n, ...t.userAgent ? { userAgent: t.userAgent } : {} }, view: { ...r, ...t.referrer ? { referrer: t.referrer } : {} }, capture: t.capture ?? e7.configuration.analytics.enabled, cart: $x2(e7.cart), source: Hr2(e7.configuration.analytics) } };
};
var Gx2 = (e7, t, r) => ({ ...Ha2(e7, t), ...hq2(e7, r) });
var hq2 = (e7, t) => {
  let r = t ? e7.commercePagination?.recommendations[t] : e7.commercePagination?.principal;
  return r && { page: r.page, ...r.perPage && { perPage: r.perPage } };
};
var xt2 = (e7, t) => ({ ...Gx2(e7, t), facets: [...yq2(e7)], ...e7.commerceSort && { sort: Cq2(e7.commerceSort.appliedSort) } });
function yq2(e7) {
  return !e7.facetOrder || !e7.commerceFacetSet ? [] : e7.facetOrder.filter((t) => e7.commerceFacetSet?.[t]).map((t) => e7.manualNumericFacetSet?.[t]?.manualRange ? { facetId: t, field: t, numberOfValues: 1, isFieldExpanded: false, preventAutoSelect: true, type: "numericalRange", values: [e7.manualNumericFacetSet[t].manualRange], initialNumberOfValues: 1 } : e7.commerceFacetSet[t].request).filter((t) => t && t.values.length > 0);
}
function Cq2(e7) {
  return e7.by === "relevance" ? { sortCriteria: "relevance" } : { sortCriteria: "fields", fields: e7.fields.map(({ name: t, direction: r }) => ({ field: t, direction: r })) };
}
var Wx2 = (e7, t, r, n) => {
  let o = t.categoryFacetSearchSet[e7].options.query, a = `*${o}*`, i = t.commerceFacetSet[Xs2(e7)]?.request, s = i && xq2(i) ? i && Aq2(i) : [], c = s.length ? [s] : [], u = r ? o : t.commerceQuery?.query, { url: l, accessToken: m, organizationId: p, trackingId: d, language: f, country: A, currency: S, clientId: g, context: C, ...y } = xt2(t, n);
  return { url: l, accessToken: m, organizationId: p, facetId: Xs2(e7), facetQuery: r ? "*" : a, ignorePaths: c, trackingId: d, language: f, country: A, currency: S, clientId: g, context: C, query: u, ...!r && { ...y } };
};
function xq2(e7) {
  return e7.type === "hierarchical";
}
var Aq2 = (e7) => {
  let t = [], r = e7.values[0];
  for (; r; )
    t.push(r.value), r = r.children[0];
  return t;
};
var Hx2 = (e7, t, r, n) => {
  let o = t.facetSearchSet[e7].options.query, a = `*${o}*`, i = r ? o : t.commerceQuery?.query, { url: s, accessToken: c, organizationId: u, trackingId: l, language: m, country: p, currency: d, clientId: f, context: A, ...S } = xt2(t, n);
  return { url: s, accessToken: c, organizationId: u, facetId: Xs2(e7), facetQuery: r ? "*" : a, trackingId: l, language: m, country: p, currency: d, clientId: f, context: A, query: i, ...!r && { ...S } };
};
var zx2 = (e7) => async ({ facetId: t, facetSearchType: r }, { getState: n, extra: { validatePayload: o, navigatorContext: a, apiClient: i } }) => {
  let s = n();
  o(t, V2);
  let c = Fq2(s, t) || Rq(s, t) ? Hx2(t, s, e7, a) : Wx2(t, s, e7, a), u = await i.facetSearch(c, r);
  return { facetId: t, response: u };
};
var An2 = W2("commerce/facetSearch/executeSearch", zx2(false));
var Fn2 = W2("commerce/facetSearch/facetFieldSuggest", zx2(true));
var Fq2 = (e7, t) => "facetSearchSet" in e7 && e7.facetSearchSet[t] !== void 0 && e7.commerceFacetSet[t] !== void 0;
var Rq = (e7, t) => "fieldSuggestionsOrder" in e7 ? e7.fieldSuggestionsOrder.some((r) => r.facetId === t && r.type === "regular") : false;
var hl2 = "field_suggestion:";
function Xs2(e7) {
  return e7.startsWith(hl2) ? e7.slice(hl2.length) : e7;
}
function Rn2(e7) {
  return e7.startsWith(hl2) ? e7 : `${hl2}${e7}`;
}
var yl2 = Y2((e7) => e7.commercePagination?.principal.perPage || 0, (e7) => e7);
Y2((e7, t) => e7.commercePagination?.recommendations[t]?.perPage || 0, (e7) => e7);
var Cl2 = Y2((e7) => e7.commercePagination?.principal.totalEntries || 0, (e7) => e7);
Y2((e7, t) => e7.commercePagination?.recommendations[t]?.totalEntries || 0, (e7) => e7);
Y2((e7) => e7.commercePagination?.principal.page || 0, (e7) => e7);
Y2((e7, t) => e7.commercePagination?.recommendations[t]?.page || 0, (e7) => e7);
var bq = "coveo-headless-internal-state";
var bn2 = Symbol.for(bq);
Y2((e7) => e7[bn2].productListing.responseId, (e7) => e7);
Y2((e7) => e7.productListing.responseId, (e7) => e7);
Y2((e7) => e7.productListing.requestId, (e7) => e7);
var _f = Y2((e7) => e7.productListing?.products.length || 0, (e7) => e7);
var Kx2 = Y2((e7) => ({ total: Cl2(e7), current: _f(e7) }), ({ current: e7, total: t }) => e7 < t);
Y2((e7) => e7.productListing?.isLoading, (e7) => isNullOrUndefined2(e7) ? false : e7);
Y2((e7) => e7.productListing?.error, (e7) => e7 ?? null);
var za2 = W2("commerce/productListing/fetch", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, navigatorContext: o } }) => {
  let a = t(), i = await n.getProductListing(xt2(a, o));
  return Tt2(i) ? r(i.error) : { response: i.success };
});
W2("commerce/productListing/fetchMoreProducts", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, navigatorContext: o } }) => {
  let a = t();
  if (!Kx2(a))
    return null;
  let s = yl2(a), u = _f(a) / s, l = await n.getProductListing({ ...xt2(a, o), page: u });
  return Tt2(l) ? r(l.error) : { response: l.success };
});
var Iq = { child: new RecordValue2({ options: { required: true }, values: { permanentid: new StringValue2({ required: true }) } }) };
h3("commerce/productListing/promoteChildToParent", (e7) => x(e7, Iq));
var Yx2 = (e7, t, r) => ({ ...Ha2(t, r), query: t.querySet[e7] });
var Jx2 = h3("commerce/querySuggest/clear", (e7) => x(e7, { id: V2 }));
var vn2 = W2("commerce/querySuggest/fetch", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, validatePayload: o, navigatorContext: a } }) => {
  o(e7, { id: V2 });
  let i = t(), s = Yx2(e7.id, i, a), c = await n.querySuggest(s);
  return Tt2(c) ? r(c.error) : { id: e7.id, query: s.query, ...c.success };
});
var Xx2 = h3("commerce/querySuggest/register", (e7) => x(e7, { id: V2, count: new NumberValue2({ min: 0 }) }));
var Zx2 = h3("commerce/querySuggest/selectSuggestion", (e7) => x(e7, { id: V2, expression: se }));
h3("commerce/facets/core/updateNumberOfValues", (e7) => x(e7, { facetId: V2, numberOfValues: new NumberValue2({ required: true, min: 1 }) }));
h3("commerce/facets/core/updateIsFieldExpanded", (e7) => x(e7, { facetId: V2, isFieldExpanded: new BooleanValue2({ required: true }) }));
var eA2 = h3("commerce/facets/core/clearAll");
h3("commerce/facets/core/deselectAllValues", (e7) => x(e7, { facetId: V2 }));
h3("commerce/facets/core/updateFreezeCurrentValues", (e7) => x(e7, { facetId: V2, freezeCurrentValues: new BooleanValue2({ required: true }) }));
var tA = h3("commerce/facets/core/updateAutoSelectionForAll", (e7) => x(e7, { allow: new BooleanValue2({ required: true }) }));
var xl2 = { slotId: wS2 };
var kq = { ...xl2, pageSize: new NumberValue2({ required: true, min: 0 }) };
h3("commerce/pagination/setPageSize", (e7) => x(e7, kq));
var Oq = { ...xl2, page: new NumberValue2({ required: true, min: 0 }) };
var nA2 = h3("commerce/pagination/selectPage", (e7) => x(e7, Oq));
h3("commerce/pagination/nextPage", (e7) => x(e7, xl2));
h3("commerce/pagination/previousPage", (e7) => x(e7, xl2));
h3("commerce/pagination/registerRecommendationsSlot", (e7) => x(e7, { slotId: V2 }));
var Al2 = h3("commerce/query/update", (e7) => x(e7, { query: new StringValue2() }));
var oA2 = h3("commerce/triggers/query/updateIgnore", (e7) => x(e7, { q: new StringValue2({ emptyAllowed: true, required: true }) }));
var aA = h3("commerce/triggers/query/applyModification", (e7) => x(e7, new RecordValue2({ values: { originalQuery: de2, modification: de2 } })));
Y2((e7) => e7[bn2].commerceSearch.responseId, (e7) => e7);
Y2((e7) => e7.commerceSearch.responseId, (e7) => e7);
Y2((e7) => e7.commerceSearch.requestId, (e7) => e7);
var Wf = Y2((e7) => e7.commerceSearch?.products.length || 0, (e7) => e7);
var cA = Y2((e7) => ({ total: Cl2(e7), current: Wf(e7) }), ({ current: e7, total: t }) => e7 < t);
Y2((e7) => e7.commerceSearch?.isLoading, (e7) => isNullOrUndefined2(e7) ? false : e7);
Y2((e7) => e7.commerceSearch?.error, (e7) => e7 ?? null);
var Fl2 = Y2((e7) => e7.commerceQuery?.query, (e7) => e7 ?? "");
Y2((e7) => e7.commerceSearch?.queryExecuted, (e7) => e7);
var uA = (e7, t) => isNullOrUndefined2(t.queryCorrection?.correctedQuery) ? Fl2(e7) : t.queryCorrection.correctedQuery;
var Zs2 = class {
  constructor(t) {
    this.config = t;
  }
  async process(t) {
    return this.processQueryErrorOrContinue(t) ?? await this.processQueryCorrectionsOrContinue(t) ?? await this.processQueryTriggersOrContinue(t) ?? this.processSuccessResponse(t);
  }
  async fetchFromAPI(t) {
    let r = (/* @__PURE__ */ new Date()).getTime(), n = await this.extra.apiClient.search(t), o = (/* @__PURE__ */ new Date()).getTime() - r, a = this.getState().commerceQuery.query || "";
    return { response: n, duration: o, queryExecuted: a, requestExecuted: t };
  }
  processSuccessResponse(t) {
    return { ...t, response: this.getSuccessResponse(t), originalQuery: this.getCurrentQuery() };
  }
  processQueryErrorOrContinue(t) {
    return Tt2(t.response) ? this.rejectWithValue(t.response.error) : null;
  }
  async processQueryCorrectionsOrContinue(t) {
    let r = this.getState(), n = this.getSuccessResponse(t);
    if (!n || !r.didYouMean)
      return null;
    let { queryCorrection: o } = n;
    if (!(!isNullOrUndefined2(o) && !isNullOrUndefined2(o.correctedQuery)))
      return null;
    let { correctedQuery: i, originalQuery: s } = n.queryCorrection;
    return this.onUpdateQueryForCorrection(i ?? ""), { ...t, response: { ...n }, queryExecuted: uA(r, n), originalQuery: s ?? "" };
  }
  async processQueryTriggersOrContinue(t) {
    let r = this.getSuccessResponse(t);
    if (!r)
      return null;
    let n = r.triggers.find((s) => s.type === "query")?.content || "";
    if (!n)
      return null;
    if (this.getState().triggers?.queryModification.queryToIgnore === n)
      return this.dispatch(oA2({ q: "" })), null;
    let a = this.getCurrentQuery(), i = await this.automaticallyRetryQueryWithTriggerModification(n);
    return Tt2(i.response) ? this.rejectWithValue(i.response.error) : { ...i, response: { ...i.response.success }, originalQuery: a };
  }
  async automaticallyRetryQueryWithTriggerModification(t) {
    return this.dispatch(aA({ newQuery: t, originalQuery: this.getCurrentQuery() })), this.onUpdateQueryForCorrection(t), await this.fetchFromAPI({ ...xt2(this.getState(), this.navigatorContext), query: t });
  }
  get dispatch() {
    return this.config.dispatch;
  }
  get rejectWithValue() {
    return this.config.rejectWithValue;
  }
  getState() {
    return this.config.getState();
  }
  get navigatorContext() {
    return this.config.extra.navigatorContext;
  }
  getCurrentQuery() {
    let t = this.getState();
    return t.commerceQuery.query !== void 0 ? t.commerceQuery.query : "";
  }
  getSuccessResponse(t) {
    return Tt2(t.response) ? null : t.response.success;
  }
  get extra() {
    return this.config.extra;
  }
  onUpdateQueryForCorrection(t) {
    this.dispatch(Al2({ query: t }));
  }
};
var Pn2 = W2("commerce/search/executeSearch", async (e7, t) => {
  let { getState: r } = t, n = r(), { navigatorContext: o } = t.extra, a = xt2(n, o), i = Fl2(n), s = new Zs2(t), c = await s.fetchFromAPI({ ...a, query: i });
  return s.process(c);
});
W2("commerce/search/fetchMoreProducts", async (e7, t) => {
  let { getState: r } = t, n = r(), { navigatorContext: o } = t.extra;
  if (!cA(n))
    return null;
  let i = yl2(n), c = Wf(n) / i, u = Fl2(n), l = xt2(n, o), m = new Zs2(t), p = await m.fetchFromAPI({ ...l, query: u, page: c });
  return m.process(p);
});
W2("commerce/search/prepareForSearchWithQuery", (e7, t) => {
  let { dispatch: r } = t;
  x(e7, { query: new StringValue2(), clearFilters: new BooleanValue2() }), e7.clearFilters && (r(eA2()), r(_t2())), r(tA({ allow: true })), r(Al2({ query: e7.query })), r(nA2({ page: 0 }));
});
W2("commerce/search/fetchInstantProducts", async (e7, { getState: t, rejectWithValue: r, extra: n }) => {
  let o = t(), { apiClient: a, navigatorContext: i } = n, { q: s } = e7, c = await a.productSuggestions({ ...Ha2(o, i), query: s });
  return Tt2(c) ? r(c.error) : { response: { ...c.success, products: c.success.products } };
});
var Qq2 = { child: new RecordValue2({ options: { required: true }, values: { permanentid: new StringValue2({ required: true }) } }) };
h3("commerce/search/promoteChildToParent", (e7) => x(e7, Qq2));
function ec2(e7, t, r) {
  let { facetId: n } = t;
  if (e7[n])
    return;
  let o = false, a = { ...Ye2, ...t }, i = r();
  e7[n] = { options: a, isLoading: o, response: i, initialNumberOfValues: a.numberOfValues, requestId: "" };
}
function Rl2(e7, t) {
  let { facetId: r, ...n } = t, o = e7[r];
  o && (o.options = { ...o.options, ...n });
}
function wn2(e7, t, r) {
  let n = e7[t];
  n && (n.requestId = r, n.isLoading = true);
}
function In2(e7, t) {
  let r = e7[t];
  r && (r.isLoading = false);
}
function bl2(e7, t, r) {
  let { facetId: n, response: o } = t, a = e7[n];
  a && a.requestId === r && (a.isLoading = false, a.response = o);
}
function vl2(e7, t, r) {
  let { facetId: n, response: o } = t, a = e7[n];
  a && a.requestId === r && (a.isLoading = false, "success" in o && (a.response = o.success));
}
function Pl2(e7, t, r, n) {
  let { facetId: o, response: a } = t, i = Rn2(o), s = e7[i];
  if (!s)
    ec2(e7, { facetId: i }, n), s = e7[i];
  else if (s.requestId !== r)
    return;
  s.isLoading = false, "success" in a && (s.response = a.success);
}
function pA2(e7, t, r, n) {
  if (t.fieldSuggestionsFacets)
    for (let o of t.fieldSuggestionsFacets)
      o.facetId in e7 || o.type !== "regular" || (e7[o.facetId] = { options: { ...Ye2, query: t.query ?? "" }, isLoading: false, response: n(), initialNumberOfValues: Ye2.numberOfValues, requestId: r });
}
function mA2(e7, t, r, n) {
  if (t.fieldSuggestionsFacets)
    for (let o of t.fieldSuggestionsFacets) {
      let a = Rn2(o.facetId);
      a in e7 || o.type !== "hierarchical" || (e7[a] = { options: { ...Ye2, query: t.query ?? "" }, isLoading: false, response: n(), initialNumberOfValues: Ye2.numberOfValues, requestId: r });
    }
}
function tc(e7, t, r) {
  let { facetId: n } = t, o = e7[n];
  o && (o.requestId = "", o.isLoading = false, o.response = r(), o.options.numberOfValues = o.initialNumberOfValues, o.options.query = Ye2.query);
}
function qr2(e7, t) {
  Object.keys(e7).forEach((r) => tc(e7, { facetId: r }, t));
}
var Ye2 = { captions: {}, numberOfValues: 10, query: "" };
var fA2 = async (e7, t, r, n) => {
  let o = t.categoryFacetSearchSet[e7].options, a = t.categoryFacetSet[e7].request, { captions: i, query: s, numberOfValues: c } = o, { field: u, delimitingCharacter: l, basePath: m, filterFacetCount: p } = a, d = Lq(a), f = d.length ? [d] : [], A = `*${s}*`;
  return { url: t.configuration.search.apiBaseUrl ?? ve2(t.configuration.organizationId, t.configuration.environment), accessToken: t.configuration.accessToken, organizationId: t.configuration.organizationId, ...t.configuration.search.authenticationProviders.length && { authentication: t.configuration.search.authenticationProviders.join(",") }, basePath: m, captions: i, numberOfValues: c, query: A, field: u, delimitingCharacter: l, ignorePaths: f, filterFacetCount: p, type: "hierarchical", ...n ? {} : { searchContext: (await yt2(t, r)).request } };
};
var Lq = (e7) => {
  let t = [], r = e7.currentValues[0];
  for (; r; )
    t.push(r.value), r = r.children[0];
  return t;
};
var gA2 = async (e7, t, r, n) => {
  let { captions: o, query: a, numberOfValues: i } = t.facetSearchSet[e7].options, { field: s, currentValues: c, filterFacetCount: u } = t.facetSet[e7].request, l = c.filter((p) => p.state !== "idle").map((p) => p.value), m = `*${a}*`;
  return { url: t.configuration.search.apiBaseUrl ?? ve2(t.configuration.organizationId, t.configuration.environment), accessToken: t.configuration.accessToken, organizationId: t.configuration.organizationId, ...t.configuration.search.authenticationProviders && { authentication: t.configuration.search.authenticationProviders.join(",") }, captions: o, numberOfValues: i, query: m, field: s, ignoreValues: l, filterFacetCount: u, type: "specific", ...n ? {} : { searchContext: (await yt2(t, r)).request } };
};
var SA2 = (e7) => async (t, { getState: r, extra: { apiClient: n, validatePayload: o, navigatorContext: a } }) => {
  let i = r(), s;
  o(t, V2), Bq(i, t) ? s = await gA2(t, i, a, e7) : s = await fA2(t, i, a, e7);
  let c = await n.facetSearch(s);
  return { facetId: t, response: c };
};
var Ie2 = W2("facetSearch/executeSearch", SA2(false));
W2("facetSearch/executeSearch", SA2(true));
var Ka = h3("facetSearch/clearResults", (e7) => x(e7, { facetId: K2 }));
var Bq = (e7, t) => e7.facetSearchSet !== void 0 && e7.facetSet !== void 0 && e7.facetSet[t] !== void 0;
var hA = { facetId: K2, value: new RecordValue2({ values: { displayValue: se, rawValue: se, count: new NumberValue2({ required: true, min: 0 }) } }) };
var wl = h3("facetSearch/register", (e7) => x(e7, zs2));
var En2 = h3("facetSearch/update", (e7) => x(e7, zs2));
var mo2 = h3("facetSearch/toggleSelectValue", (e7) => x(e7, hA));
var fo2 = h3("facetSearch/toggleExcludeValue", (e7) => x(e7, hA));
function yA() {
  return {};
}
$2(yA(), (e7) => {
  e7.addCase(ja2, (t, r) => {
    let n = r.payload;
    ec2(t, n, go2);
  }).addCase(En2, (t, r) => {
    Rl2(t, r.payload);
  }).addCase(An2.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn2(t, n, r.meta.requestId);
  }).addCase(Fn2.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn2(t, n, r.meta.requestId);
  }).addCase(Ie2.pending, (t, r) => {
    let n = r.meta.arg;
    wn2(t, n, r.meta.requestId);
  }).addCase(An2.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In2(t, n);
  }).addCase(Fn2.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In2(t, Rn2(n));
  }).addCase(Ie2.rejected, (t, r) => {
    let n = r.meta.arg;
    In2(t, n);
  }).addCase(An2.fulfilled, (t, r) => {
    vl2(t, r.payload, r.meta.requestId);
  }).addCase(Fn2.fulfilled, (t, r) => {
    Pl2(t, r.payload, r.meta.requestId, go2);
  }).addCase(vn2.fulfilled, (t, r) => {
    mA2(t, r.payload, r.meta.requestId, go2);
  }).addCase(Ie2.fulfilled, (t, r) => {
    bl2(t, r.payload, r.meta.requestId);
  }).addCase(Ka, (t, { payload: { facetId: r } }) => {
    tc(t, { facetId: r }, go2);
  }).addCase(za2.fulfilled, (t) => qr2(t, go2)).addCase(Pn2.fulfilled, (t) => qr2(t, go2)).addCase(N2.fulfilled, (t) => {
    qr2(t, go2);
  });
});
function go2() {
  return { moreValuesAvailable: false, values: [] };
}
var kl2 = new RecordValue2({ options: { required: false }, values: { type: new StringValue2({ constrainTo: ["simple"], emptyAllowed: false, required: true }), values: new ArrayValue2({ required: true, max: 25, each: new StringValue2({ emptyAllowed: false, required: true }) }) } });
var Ol = new ArrayValue2({ min: 1, max: 25, required: false, each: new StringValue2({ emptyAllowed: false, required: true }) });
var So2 = { value: V2, numberOfResults: new NumberValue2({ min: 0 }), state: V2 };
var zq2 = { facetId: K2, field: new StringValue2({ required: true, emptyAllowed: true }), tabs: new RecordValue2({ options: { required: false }, values: { included: new ArrayValue2({ each: new StringValue2() }), excluded: new ArrayValue2({ each: new StringValue2() }) } }), activeTab: new StringValue2({ required: false }), filterFacetCount: new BooleanValue2({ required: false }), injectionDepth: new NumberValue2({ required: false, min: 0 }), numberOfValues: new NumberValue2({ required: false, min: 1 }), sortCriteria: new Value2({ required: false }), resultsMustMatch: new Value2({ required: false }), allowedValues: kl2, customSort: Ol };
var ir2 = h3("facet/register", (e7) => x(e7, zq2));
var sr2 = h3("facet/toggleSelectValue", (e7) => x(e7, { facetId: K2, selection: new RecordValue2({ values: So2 }) }));
var cr2 = h3("facet/toggleExcludeValue", (e7) => x(e7, { facetId: K2, selection: new RecordValue2({ values: So2 }) }));
var me2 = h3("facet/deselectAll", (e7) => x(e7, K2));
var ti2 = h3("facet/updateSortCriterion", (e7) => x(e7, { facetId: K2, criterion: new Value2({ required: true }) }));
var ho2 = h3("facet/updateNumberOfValues", (e7) => x(e7, { facetId: K2, numberOfValues: new NumberValue2({ required: true, min: 1 }) }));
var yo2 = h3("facet/updateIsFieldExpanded", (e7) => x(e7, { facetId: K2, isFieldExpanded: new BooleanValue2({ required: true }) }));
var Nr2 = h3("facet/updateFreezeCurrentValues", (e7) => x(e7, { facetId: K2, freezeCurrentValues: new BooleanValue2({ required: true }) }));
function Co2(e7) {
  let t = vA(e7.start, e7), r = vA(e7.end, e7), n = e7.endInclusive ?? false, o = e7.state ?? "idle";
  return { start: t, end: r, endInclusive: n, state: o };
}
function vA(e7, t) {
  let { dateFormat: r } = t;
  return qy2(e7) ? (to2(e7), Ty2(e7)) : typeof e7 == "string" && $t2(e7) ? (to2(e7), e7) : (yu2(e7, r), Ps2(eo2(e7, r)));
}
var ri = h3("rangeFacet/updateSortCriterion", (e7) => x(e7, { facetId: K2, criterion: new Value2({ required: true }) }));
var xo2 = { state: V2, start: new NumberValue2({ required: true }), end: new NumberValue2({ required: true }), endInclusive: new BooleanValue2({ required: true }), numberOfResults: new NumberValue2({ required: true, min: 0 }) };
var Ao2 = { start: V2, end: V2, endInclusive: new BooleanValue2({ required: true }), state: V2, numberOfResults: new NumberValue2({ required: true, min: 0 }) };
var Fo2 = (e7) => ({ facetId: K2, selection: typeof e7.start == "string" ? new RecordValue2({ values: Ao2 }) : new RecordValue2({ values: xo2 }) });
var Yq2 = { start: V2, end: V2, endInclusive: new BooleanValue2({ required: true }), state: V2 };
var Jq2 = { facetId: K2, field: V2, tabs: new RecordValue2({ options: { required: false }, values: { included: new ArrayValue2({ each: new StringValue2() }), excluded: new ArrayValue2({ each: new StringValue2() }) } }), activeTab: new StringValue2({ required: false }), currentValues: new ArrayValue2({ required: false, each: new RecordValue2({ values: Yq2 }) }), generateAutomaticRanges: new BooleanValue2({ required: true }), filterFacetCount: new BooleanValue2({ required: false }), injectionDepth: new NumberValue2({ required: false, min: 0 }), numberOfValues: new NumberValue2({ required: false, min: 1 }), sortCriteria: new Value2({ required: false }), rangeAlgorithm: new Value2({ required: false }) };
function TA(e7) {
  return $t2(e7) ? Is2(e7) : e7;
}
function Nl2(e7) {
  e7.currentValues && e7.currentValues.forEach((t) => {
    let { start: r, end: n } = Co2(t);
    if (eo2(TA(r)).isAfter(eo2(TA(n))))
      throw new Error(`The start value is greater than the end value for the date range ${t.start} to ${t.end}`);
  });
}
var ur2 = h3("dateFacet/register", (e7) => {
  try {
    return ct2(e7, Jq2), Nl2(e7), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br2(t) };
  }
});
var lr2 = h3("dateFacet/toggleSelectValue", (e7) => x(e7, { facetId: K2, selection: new RecordValue2({ values: Ao2 }) }));
var dr2 = h3("dateFacet/toggleExcludeValue", (e7) => x(e7, { facetId: K2, selection: new RecordValue2({ values: Ao2 }) }));
var Mr2 = h3("dateFacet/updateFacetValues", (e7) => {
  try {
    return ct2(e7, { facetId: K2, values: new ArrayValue2({ each: new RecordValue2({ values: Ao2 }) }) }), Nl2({ currentValues: e7.values }), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br2(t) };
  }
});
var Ml2 = ri;
var Ql = me2;
var Xq = { state: V2, start: new NumberValue2({ required: true }), end: new NumberValue2({ required: true }), endInclusive: new BooleanValue2({ required: true }) };
var Zq = { facetId: K2, field: V2, tabs: new RecordValue2({ options: { required: false }, values: { included: new ArrayValue2({ each: new StringValue2() }), excluded: new ArrayValue2({ each: new StringValue2() }) } }), activeTab: new StringValue2({ required: false }), currentValues: new ArrayValue2({ required: false, each: new RecordValue2({ values: Xq }) }), generateAutomaticRanges: new BooleanValue2({ required: true }), filterFacetCount: new BooleanValue2({ required: false }), injectionDepth: new NumberValue2({ required: false, min: 0 }), numberOfValues: new NumberValue2({ required: false, min: 1 }), sortCriteria: new Value2({ required: false }), rangeAlgorithm: new Value2({ required: false }) };
function Ul2(e7) {
  e7.currentValues && e7.currentValues.forEach(({ start: t, end: r }) => {
    if (t > r)
      throw new Error(`The start value is greater than the end value for the numeric range ${t} to ${r}`);
  });
}
var pr2 = h3("numericFacet/register", (e7) => {
  try {
    return x(e7, Zq), Ul2(e7), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br2(t) };
  }
});
var mr2 = h3("numericFacet/toggleSelectValue", (e7) => x(e7, { facetId: K2, selection: new RecordValue2({ values: xo2 }) }));
var fr2 = h3("numericFacet/toggleExcludeValue", (e7) => x(e7, { facetId: K2, selection: new RecordValue2({ values: xo2 }) }));
var Qr2 = h3("numericFacet/updateFacetValues", (e7) => {
  try {
    return ct2(e7, { facetId: K2, values: new ArrayValue2({ each: new RecordValue2({ values: xo2 }) }) }), Ul2({ currentValues: e7.values }), { payload: e7, error: null };
  } catch (t) {
    return { payload: e7, error: br2(t) };
  }
});
var _l2 = ri;
var jl2 = me2;
var $l2 = (e7, t) => typeof e7 == "object" && Object.keys({ ...e7 }).length === 0 || !t || !e7 ? true : e7.excluded && e7.excluded.includes(t) ? false : !!(e7.included && (e7.included.length === 0 || e7.included.includes(t)));
$2(vu2(), (e7) => {
  e7.addCase(Z2, (t, r) => ({ ...t, ...r.payload })).addCase(N2.fulfilled, (t) => {
    t.freezeFacetOrder = false;
  }).addCase(N2.rejected, (t) => {
    t.freezeFacetOrder = false;
  }).addCase(ot2, (t, r) => {
    for (let n in t.facets) {
      let o = t.facets[n];
      Object.keys({ ...o.tabs }).length > 0 && (o.enabled = $l2(o.tabs, r.payload));
    }
  }).addCase(ae2.fulfilled, (t, r) => r.payload?.facetOptions ?? t).addCase(Kt2, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    Gl(o, a, t, n);
  }).addCase(ir2, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    Gl(o, a, t, n);
  }).addCase(ur2, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    Gl(o, a, t, n);
  }).addCase(pr2, (t, r) => {
    let { facetId: n, tabs: o, activeTab: a } = r.payload;
    Gl(o, a, t, n);
  }).addCase(Be2, (t, r) => {
    t.facets[r.payload].enabled = true;
  }).addCase(pe2, (t, r) => {
    t.facets[r.payload].enabled = false;
  }).addCase(ce2, (t, r) => {
    r.payload.tab && Object.entries(t.facets).forEach(([, n]) => {
      Object.keys(n.tabs ?? {}).length > 0 && (n.enabled = $l2(n.tabs, r.payload.tab));
    }), [...Object.keys(r.payload.f ?? {}), ...Object.keys(r.payload.fExcluded ?? {}), ...Object.keys(r.payload.cf ?? {}), ...Object.keys(r.payload.nf ?? {}), ...Object.keys(r.payload.df ?? {})].forEach((n) => {
      n in t || (t.facets[n] = Zm2()), t.facets[n].enabled = true;
    });
  });
});
function Gl(e7, t, r, n) {
  let o = { ...Zm2(), tabs: e7 ?? {} };
  e7 && Object.keys(e7).length > 0 && (o.enabled = $l2(e7, t)), r.facets[n] = o;
}
Y2((e7) => e7, (e7) => {
  if (!e7)
    return "";
  for (let t in e7)
    if (e7[t].isActive)
      return e7[t].id;
  return "";
});
var mD2 = Intl.supportedValuesOf("currency");
var fD2 = new StringValue2({ required: true, emptyAllowed: false, constrainTo: mD2 });
var ag2 = { url: V2 };
var ig2 = { latitude: new NumberValue2({ min: -90, max: 90, required: true }), longitude: new NumberValue2({ min: -180, max: 180, required: true }) };
var sg = { language: V2, country: V2, currency: fD2, view: new RecordValue2({ options: { required: true }, values: ag2 }), location: new RecordValue2({ options: { required: false }, values: ig2 }) };
var UA2 = h3("commerce/context/set", (e7) => x(e7, sg));
var Hl2 = h3("commerce/context/setView", (e7) => x(e7, ag2));
h3("commerce/context/setLocation", (e7) => x(e7, ig2));
function _A2() {
  return {};
}
$2(_A2(), (e7) => {
  e7.addCase(wl, (t, r) => {
    let n = r.payload;
    ec2(t, n, kn2);
  }).addCase(En2, (t, r) => {
    Rl2(t, r.payload);
  }).addCase(An2.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn2(t, n, r.meta.requestId);
  }).addCase(Fn2.pending, (t, r) => {
    let { facetId: n } = r.meta.arg;
    wn2(t, Rn2(n), r.meta.requestId);
  }).addCase(Ie2.pending, (t, r) => {
    let n = r.meta.arg;
    wn2(t, n, r.meta.requestId);
  }).addCase(An2.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In2(t, n);
  }).addCase(Fn2.rejected, (t, r) => {
    let { facetId: n } = r.meta.arg;
    In2(t, Rn2(n));
  }).addCase(Ie2.rejected, (t, r) => {
    let n = r.meta.arg;
    In2(t, n);
  }).addCase(An2.fulfilled, (t, r) => {
    vl2(t, r.payload, r.meta.requestId);
  }).addCase(Fn2.fulfilled, (t, r) => {
    Pl2(t, r.payload, r.meta.requestId, kn2);
  }).addCase(vn2.fulfilled, (t, r) => {
    pA2(t, r.payload, r.meta.requestId, kn2);
  }).addCase(Ie2.fulfilled, (t, r) => {
    bl2(t, r.payload, r.meta.requestId);
  }).addCase(Ka, (t, { payload: r }) => {
    tc(t, r, kn2);
  }).addCase(N2.fulfilled, (t) => {
    qr2(t, kn2);
  }).addCase(za2.fulfilled, (t) => qr2(t, kn2)).addCase(Pn2.fulfilled, (t) => qr2(t, kn2)).addCase(Hl2, (t) => qr2(t, kn2));
});
function kn2() {
  return { moreValuesAvailable: false, values: [] };
}
$2(Yo(), (e7) => {
  e7.addCase(ir2, (t, r) => {
    let { facetId: n } = r.payload;
    n in t || (t[n] = Hh2(gD2(r.payload)));
  }).addCase(ae2.fulfilled, (t, r) => {
    if (r.payload && Object.keys(r.payload.facetSet).length !== 0)
      return r.payload.facetSet;
  }).addCase(ce2, (t, r) => {
    let n = r.payload.f || {}, o = r.payload.fExcluded || {};
    Object.keys(t).forEach((i) => {
      let { request: s } = t[i], c = n[i] || [], u = o[i] || [], l = c.length + u.length, m = s.currentValues.filter((p) => !c.includes(p.value) && !u.includes(p.value));
      s.currentValues = [...c.map($A), ...u.map(GA), ...m.map(hD)], s.preventAutoSelect = l > 0, s.numberOfValues = Math.max(l, s.numberOfValues);
    });
  }).addCase(sr2, (t, r) => {
    let { facetId: n, selection: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    a.preventAutoSelect = true;
    let i = a.currentValues.find((c) => c.value === o.value);
    if (!i) {
      zl(a, o);
      return;
    }
    let s = i.state === "selected";
    i.state = s ? "idle" : "selected", a.freezeCurrentValues = true;
  }).addCase(cr2, (t, r) => {
    let { facetId: n, selection: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    a.preventAutoSelect = true;
    let i = a.currentValues.find((c) => c.value === o.value);
    if (!i) {
      zl(a, o);
      return;
    }
    let s = i.state === "excluded";
    i.state = s ? "idle" : "excluded", a.freezeCurrentValues = true;
  }).addCase(Nr2, (t, r) => {
    let { facetId: n, freezeCurrentValues: o } = r.payload, a = t[n]?.request;
    a && (a.freezeCurrentValues = o);
  }).addCase(me2, (t, r) => {
    Ks2(t[r.payload]?.request);
  }).addCase(Se2, (t) => {
    Object.values(t).filter((r) => r.hasBreadcrumbs).forEach(({ request: r }) => Ks2(r));
  }).addCase(_t2, (t) => {
    Object.values(t).filter((r) => !r.hasBreadcrumbs).forEach(({ request: r }) => Ks2(r));
  }).addCase(ft2, (t, r) => Object.values(t).forEach((n) => {
    n.request.preventAutoSelect = !r.payload.allow;
  })).addCase(ti2, (t, r) => {
    $a2(t, r.payload);
  }).addCase(ho2, (t, r) => {
    let { facetId: n, numberOfValues: o } = r.payload;
    dl2(t[n]?.request, o);
  }).addCase(yo2, (t, r) => {
    let { facetId: n, isFieldExpanded: o } = r.payload, a = t[n]?.request;
    a && (a.isFieldExpanded = o);
  }).addCase(N2.fulfilled, (t, r) => {
    r.payload.response.facets.forEach((o) => jA2(t[o.facetId]?.request, o));
  }).addCase(Ht2.fulfilled, (t, r) => {
    r.payload.response.facets.forEach((o) => jA2(t[o.facetId]?.request, o));
  }).addCase(mo2, (t, r) => {
    let { facetId: n, value: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    let { rawValue: i } = o, { currentValues: s } = a, c = s.find((l) => l.value === i);
    if (c) {
      c.state = "selected";
      return;
    }
    let u = $A(i);
    zl(a, u), a.freezeCurrentValues = true, a.preventAutoSelect = true;
  }).addCase(fo2, (t, r) => {
    let { facetId: n, value: o } = r.payload, a = t[n]?.request;
    if (!a)
      return;
    let { rawValue: i } = o, { currentValues: s } = a, c = s.find((l) => l.value === i);
    if (c) {
      c.state = "excluded";
      return;
    }
    let u = GA(i);
    zl(a, u), a.freezeCurrentValues = true, a.preventAutoSelect = true;
  }).addCase(pe2, (t, r) => {
    if (!(r.payload in t))
      return;
    let { request: n } = t[r.payload];
    Ks2(n);
  });
});
function zl(e7, t) {
  let { currentValues: r } = e7, n = r.findIndex((s) => s.state === "idle"), o = n === -1 ? r.length : n, a = r.slice(0, o), i = r.slice(o + 1);
  e7.currentValues = [...a, t, ...i], e7.numberOfValues = e7.currentValues.length;
}
function jA2(e7, t) {
  e7 && (e7.currentValues = t.values.map(SD), e7.freezeCurrentValues = false, e7.preventAutoSelect = false);
}
var oc = { filterFacetCount: true, injectionDepth: 1e3, numberOfValues: 8, sortCriteria: "automatic", resultsMustMatch: "atLeastOneValue" };
function gD2(e7) {
  return { ...oc, type: "specific", currentValues: [], freezeCurrentValues: false, isFieldExpanded: false, preventAutoSelect: false, ...e7 };
}
function SD(e7) {
  let { value: t, state: r } = e7;
  return { value: t, state: r };
}
function $A(e7) {
  return { value: e7, state: "selected" };
}
function GA(e7) {
  return { value: e7, state: "excluded" };
}
function hD(e7) {
  return { ...e7, state: "idle" };
}
var zA = { facetId: K2, selection: new RecordValue2({ values: So2 }) };
W2("facet/executeToggleSelect", ({ facetId: e7, selection: t }, r) => {
  let { dispatch: n, extra: { validatePayload: o } } = r;
  o({ facetId: e7, selection: t }, zA), n(sr2({ facetId: e7, selection: t })), n(Z2());
});
W2("facet/executeToggleExclude", ({ facetId: e7, selection: t }, r) => {
  let { dispatch: n, extra: { validatePayload: o } } = r;
  o({ facetId: e7, selection: t }, zA), n(cr2({ facetId: e7, selection: t })), n(Z2());
});
var id2 = h3("rangeFacet/executeToggleSelect", (e7) => x(e7, Fo2(e7.selection)));
var sd2 = h3("rangeFacet/executeToggleExclude", (e7) => x(e7, Fo2(e7.selection)));
var nF = { facetId: K2, selection: new RecordValue2({ values: Ao2 }) };
W2("dateFacet/executeToggleSelect", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, nF), t(lr2(e7)), t(id2(e7)), t(Z2());
});
W2("dateFacet/executeToggleExclude", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, nF), t(dr2(e7)), t(sd2(e7)), t(Z2());
});
var ud2 = { filterFacetCount: true, injectionDepth: 1e3, numberOfValues: 8, sortCriteria: "ascending", rangeAlgorithm: "even", resultsMustMatch: "atLeastOneValue" };
function ld2(e7, t) {
  let { request: r } = t, { facetId: n } = r;
  if (n in e7)
    return;
  let o = iF(r);
  r.numberOfValues = o, e7[n] = t;
}
function dd2(e7, t, r) {
  let n = e7[t]?.request;
  n && (n.currentValues = r, n.numberOfValues = iF(n));
}
function pd2(e7, t, r) {
  let n = e7[t]?.request;
  if (!n)
    return;
  let o = cd2(n.currentValues, r);
  if (!o)
    return;
  let a = o.state === "selected";
  o.state = a ? "idle" : "selected", n.preventAutoSelect = true;
}
function md2(e7, t, r) {
  let n = e7[t]?.request;
  if (!n)
    return;
  let o = cd2(n.currentValues, r);
  if (!o)
    return;
  let a = o.state === "excluded";
  o.state = a ? "idle" : "excluded", n.preventAutoSelect = true;
}
function On2(e7, t) {
  let r = e7[t]?.request;
  r && r.currentValues.forEach((n) => n.state = "idle");
}
function fd2(e7, t) {
  Object.entries(e7).forEach(([r, { request: n }]) => {
    let o = t[r] || [];
    n.currentValues.forEach((s) => {
      let c = !!cd2(o, s);
      return s.state = c ? "selected" : "idle", s;
    });
    let a = o.filter((s) => !cd2(n.currentValues, s)), i = n.currentValues;
    i.push(...a), n.numberOfValues = Math.max(n.numberOfValues, i.length);
  });
}
function gd(e7, t, r) {
  t.forEach((n) => {
    let o = n.facetId, a = e7[o]?.request;
    if (!a)
      return;
    let i = r(n.values);
    a.currentValues = i, a.preventAutoSelect = false;
  });
}
function cd2(e7, t) {
  let { start: r, end: n } = t;
  return e7.find((o) => o.start === r && o.end === n);
}
function iF(e7) {
  let { generateAutomaticRanges: t, currentValues: r, numberOfValues: n } = e7;
  return t ? Math.max(n, r.length) : r.length;
}
$2(zo2(), (e7) => {
  e7.addCase(ur2, (t, r) => {
    let { payload: n } = r, o = wD(n);
    ld2(t, Gh2(o));
  }).addCase(ae2.fulfilled, (t, r) => r.payload?.dateFacetSet ?? t).addCase(ce2, (t, r) => {
    let n = r.payload.df || {};
    fd2(t, n);
  }).addCase(lr2, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    pd2(t, n, o);
  }).addCase(dr2, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    md2(t, n, o);
  }).addCase(Mr2, (t, r) => {
    let { facetId: n, values: o } = r.payload;
    dd2(t, n, o);
  }).addCase(Ql, (t, r) => {
    On2(t, r.payload);
  }).addCase(Se2, (t) => {
    Object.keys(t).forEach((r) => {
      On2(t, r);
    });
  }).addCase(Ml2, (t, r) => {
    $a2(t, r.payload);
  }).addCase(N2.fulfilled, (t, r) => {
    let n = r.payload.response.facets;
    gd(t, n, ID);
  }).addCase(pe2, (t, r) => {
    On2(t, r.payload);
  });
});
function wD(e7) {
  return { ...ud2, currentValues: [], preventAutoSelect: false, type: "dateRange", ...e7 };
}
function ID(e7) {
  return e7.map((t) => {
    let { numberOfResults: r, ...n } = t;
    return n;
  });
}
$2(Ko2(), (e7) => {
  e7.addCase(pr2, (t, r) => {
    let { payload: n } = r, o = VD(n);
    ld2(t, Wh2(o));
  }).addCase(ae2.fulfilled, (t, r) => r.payload?.numericFacetSet ?? t).addCase(ce2, (t, r) => {
    let n = r.payload.nf || {};
    fd2(t, n);
  }).addCase(mr2, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    pd2(t, n, o);
  }).addCase(fr2, (t, r) => {
    let { facetId: n, selection: o } = r.payload;
    md2(t, n, o);
  }).addCase(Qr2, (t, r) => {
    let { facetId: n, values: o } = r.payload;
    dd2(t, n, o);
  }).addCase(jl2, (t, r) => {
    On2(t, r.payload);
  }).addCase(Se2, (t) => {
    Object.keys(t).forEach((r) => {
      On2(t, r);
    });
  }).addCase(_l2, (t, r) => {
    $a2(t, r.payload);
  }).addCase(N2.fulfilled, (t, r) => {
    let n = r.payload.response.facets;
    gd(t, n, ND);
  }).addCase(pe2, (t, r) => {
    On2(t, r.payload);
  });
});
function VD(e7) {
  return { ...ud2, currentValues: [], preventAutoSelect: false, type: "numericalRange", ...e7 };
}
function ND(e7) {
  return e7.map((t) => {
    let { numberOfResults: r, ...n } = t;
    return n;
  });
}
var uF = { facetId: K2, selection: new RecordValue2({ values: xo2 }) };
W2("numericFacet/executeToggleSelect", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, uF), t(mr2(e7)), t(id2(e7)), t(Z2());
});
W2("numericFacet/executeToggleExclude", (e7, { dispatch: t, extra: { validatePayload: r } }) => {
  r(e7, uF), t(fr2(e7)), t(sd2(e7)), t(Z2());
});
var Rd2 = { f: new RecordValue2(), fExcluded: new RecordValue2(), lf: new RecordValue2(), cf: new RecordValue2(), nf: new RecordValue2(), nfExcluded: new RecordValue2(), mnf: new RecordValue2(), mnfExcluded: new RecordValue2(), df: new RecordValue2(), dfExcluded: new RecordValue2(), sortCriteria: new RecordValue2(), page: new NumberValue2({ min: 0 }), perPage: new NumberValue2({ min: 1 }) };
var RF2 = h3("commerce/productListingParameters/restore", (e7) => x(e7, Rd2));
var bF = { q: new StringValue2(), ...Rd2 };
var bd = h3("commerce/searchParameters/restore", (e7) => x(e7, bF));
$2(Aa2(), (e7) => {
  e7.addCase(N2.fulfilled, dg2).addCase(za2.fulfilled, dg2).addCase(Pn2.fulfilled, dg2).addCase(bd, vF).addCase(RF2, vF).addCase(ae2.fulfilled, (t, r) => r.payload?.facetOrder ?? t).addCase(Hl2, () => Aa2()).addCase(UA2, () => Aa2());
});
function dg2(e7, t) {
  return t.payload.response.facets.map((r) => r.facetId);
}
function vF(e7, t) {
  return [...Object.keys(t.payload.f ?? {}), ...Object.keys(t.payload.lf ?? {}), ...Object.keys(t.payload.nf ?? {}), ...Object.keys(t.payload.df ?? {}), ...Object.keys(t.payload.cf ?? {}), ...Object.keys(t.payload.mnf ?? {})];
}
var oV2 = Object.getOwnPropertyNames;
var aV2 = Object.getOwnPropertySymbols;
var iV2 = Object.prototype.hasOwnProperty;
function IF2(e7, t) {
  return function(n, o, a) {
    return e7(n, o, a) && t(n, o, a);
  };
}
function Ed(e7) {
  return function(r, n, o) {
    if (!r || !n || typeof r != "object" || typeof n != "object")
      return e7(r, n, o);
    var a = o.cache, i = a.get(r), s = a.get(n);
    if (i && s)
      return i === n && s === r;
    a.set(r, n), a.set(n, r);
    var c = e7(r, n, o);
    return a.delete(r), a.delete(n), c;
  };
}
function EF2(e7) {
  return oV2(e7).concat(aV2(e7));
}
var NF2 = Object.hasOwn || function(e7, t) {
  return iV2.call(e7, t);
};
function si(e7, t) {
  return e7 || t ? e7 === t : e7 === t || e7 !== e7 && t !== t;
}
var MF2 = "_owner";
var TF2 = Object.getOwnPropertyDescriptor;
var kF2 = Object.keys;
function sV2(e7, t, r) {
  var n = e7.length;
  if (t.length !== n)
    return false;
  for (; n-- > 0; )
    if (!r.equals(e7[n], t[n], n, n, e7, t, r))
      return false;
  return true;
}
function cV2(e7, t) {
  return si(e7.getTime(), t.getTime());
}
function OF2(e7, t, r) {
  if (e7.size !== t.size)
    return false;
  for (var n = {}, o = e7.entries(), a = 0, i, s; (i = o.next()) && !i.done; ) {
    for (var c = t.entries(), u = false, l = 0; (s = c.next()) && !s.done; ) {
      var m = i.value, p = m[0], d = m[1], f = s.value, A = f[0], S = f[1];
      !u && !n[l] && (u = r.equals(p, A, a, l, e7, t, r) && r.equals(d, S, p, A, e7, t, r)) && (n[l] = true), l++;
    }
    if (!u)
      return false;
    a++;
  }
  return true;
}
function uV2(e7, t, r) {
  var n = kF2(e7), o = n.length;
  if (kF2(t).length !== o)
    return false;
  for (var a; o-- > 0; )
    if (a = n[o], a === MF2 && (e7.$$typeof || t.$$typeof) && e7.$$typeof !== t.$$typeof || !NF2(t, a) || !r.equals(e7[a], t[a], a, a, e7, t, r))
      return false;
  return true;
}
function ic2(e7, t, r) {
  var n = EF2(e7), o = n.length;
  if (EF2(t).length !== o)
    return false;
  for (var a, i, s; o-- > 0; )
    if (a = n[o], a === MF2 && (e7.$$typeof || t.$$typeof) && e7.$$typeof !== t.$$typeof || !NF2(t, a) || !r.equals(e7[a], t[a], a, a, e7, t, r) || (i = TF2(e7, a), s = TF2(t, a), (i || s) && (!i || !s || i.configurable !== s.configurable || i.enumerable !== s.enumerable || i.writable !== s.writable)))
      return false;
  return true;
}
function lV2(e7, t) {
  return si(e7.valueOf(), t.valueOf());
}
function dV2(e7, t) {
  return e7.source === t.source && e7.flags === t.flags;
}
function qF2(e7, t, r) {
  if (e7.size !== t.size)
    return false;
  for (var n = {}, o = e7.values(), a, i; (a = o.next()) && !a.done; ) {
    for (var s = t.values(), c = false, u = 0; (i = s.next()) && !i.done; )
      !c && !n[u] && (c = r.equals(a.value, i.value, a.value, i.value, e7, t, r)) && (n[u] = true), u++;
    if (!c)
      return false;
  }
  return true;
}
function pV2(e7, t) {
  var r = e7.length;
  if (t.length !== r)
    return false;
  for (; r-- > 0; )
    if (e7[r] !== t[r])
      return false;
  return true;
}
var mV2 = "[object Arguments]";
var fV2 = "[object Boolean]";
var gV2 = "[object Date]";
var SV2 = "[object Map]";
var hV2 = "[object Number]";
var yV2 = "[object Object]";
var CV2 = "[object RegExp]";
var xV2 = "[object Set]";
var AV2 = "[object String]";
var FV2 = Array.isArray;
var DF2 = typeof ArrayBuffer == "function" && ArrayBuffer.isView ? ArrayBuffer.isView : null;
var VF2 = Object.assign;
var RV2 = Object.prototype.toString.call.bind(Object.prototype.toString);
function bV2(e7) {
  var t = e7.areArraysEqual, r = e7.areDatesEqual, n = e7.areMapsEqual, o = e7.areObjectsEqual, a = e7.arePrimitiveWrappersEqual, i = e7.areRegExpsEqual, s = e7.areSetsEqual, c = e7.areTypedArraysEqual;
  return function(l, m, p) {
    if (l === m)
      return true;
    if (l == null || m == null || typeof l != "object" || typeof m != "object")
      return l !== l && m !== m;
    var d = l.constructor;
    if (d !== m.constructor)
      return false;
    if (d === Object)
      return o(l, m, p);
    if (FV2(l))
      return t(l, m, p);
    if (DF2 != null && DF2(l))
      return c(l, m, p);
    if (d === Date)
      return r(l, m, p);
    if (d === RegExp)
      return i(l, m, p);
    if (d === Map)
      return n(l, m, p);
    if (d === Set)
      return s(l, m, p);
    var f = RV2(l);
    return f === gV2 ? r(l, m, p) : f === CV2 ? i(l, m, p) : f === SV2 ? n(l, m, p) : f === xV2 ? s(l, m, p) : f === yV2 ? typeof l.then != "function" && typeof m.then != "function" && o(l, m, p) : f === mV2 ? o(l, m, p) : f === fV2 || f === hV2 || f === AV2 ? a(l, m, p) : false;
  };
}
function vV2(e7) {
  var t = e7.circular, r = e7.createCustomConfig, n = e7.strict, o = { areArraysEqual: n ? ic2 : sV2, areDatesEqual: cV2, areMapsEqual: n ? IF2(OF2, ic2) : OF2, areObjectsEqual: n ? ic2 : uV2, arePrimitiveWrappersEqual: lV2, areRegExpsEqual: dV2, areSetsEqual: n ? IF2(qF2, ic2) : qF2, areTypedArraysEqual: n ? ic2 : pV2 };
  if (r && (o = VF2({}, o, r(o))), t) {
    var a = Ed(o.areArraysEqual), i = Ed(o.areMapsEqual), s = Ed(o.areObjectsEqual), c = Ed(o.areSetsEqual);
    o = VF2({}, o, { areArraysEqual: a, areMapsEqual: i, areObjectsEqual: s, areSetsEqual: c });
  }
  return o;
}
function PV2(e7) {
  return function(t, r, n, o, a, i, s) {
    return e7(t, r, s);
  };
}
function wV(e7) {
  var t = e7.circular, r = e7.comparator, n = e7.createState, o = e7.equals, a = e7.strict;
  if (n)
    return function(c, u) {
      var l = n(), m = l.cache, p = m === void 0 ? t ? /* @__PURE__ */ new WeakMap() : void 0 : m, d = l.meta;
      return r(c, u, { cache: p, equals: o, meta: d, strict: a });
    };
  if (t)
    return function(c, u) {
      return r(c, u, { cache: /* @__PURE__ */ new WeakMap(), equals: o, meta: void 0, strict: a });
    };
  var i = { cache: void 0, equals: o, meta: void 0, strict: a };
  return function(c, u) {
    return r(c, u, i);
  };
}
hr2();
hr2({ strict: true });
hr2({ circular: true });
hr2({ circular: true, strict: true });
hr2({ createInternalComparator: function() {
  return si;
} });
hr2({ strict: true, createInternalComparator: function() {
  return si;
} });
hr2({ circular: true, createInternalComparator: function() {
  return si;
} });
hr2({ circular: true, createInternalComparator: function() {
  return si;
}, strict: true });
function hr2(e7) {
  e7 === void 0 && (e7 = {});
  var t = e7.circular, r = t === void 0 ? false : t, n = e7.createInternalComparator, o = e7.createState, a = e7.strict, i = a === void 0 ? false : a, s = vV2(e7), c = bV2(s), u = n ? n(c) : PV2(c);
  return wV({ circular: r, comparator: c, createState: o, equals: u, strict: i });
}
function bo2(e7, t, r = (n, o) => n === o) {
  return e7.length === t.length && e7.findIndex((n, o) => !r(t[o], n)) === -1;
}
function IV2(e7, t) {
  return e7.length !== t.length ? false : e7.every((r) => t.findIndex((n) => sc2(r, n)) !== -1);
}
var sc2 = hr2({ createCustomConfig: (e7) => ({ ...e7, areArraysEqual: IV2 }) });
$2(Ly2(), (e7) => {
  e7.addCase(nt2, (t, r) => TV2(t, r.payload) ? void 0 : r.payload);
});
var TV2 = (e7, t) => kV2(e7.context, t.context) && OV2(e7.dictionaryFieldContext, t.dictionaryFieldContext) && LV2(e7.advancedSearchQueries, t.advancedSearchQueries) && qV2(e7.tabSet, t.tabSet) && DV2(e7.staticFilterSet, t.staticFilterSet) && pg2(e7.facetSet, t.facetSet) && pg2(e7.dateFacetSet, t.dateFacetSet) && pg2(e7.numericFacetSet, t.numericFacetSet) && NV2(e7.automaticFacetSet, t.automaticFacetSet) && VV2(e7.categoryFacetSet, t.categoryFacetSet) && MV2(e7.pagination, t.pagination) && QV2(e7.query, t.query) && BV2(e7, t) && UV2(e7.pipeline, t.pipeline) && _V2(e7.searchHub, t.searchHub) && jV(e7.facetOrder, t.facetOrder) && $V(e7.debug, t.debug);
var kV2 = (e7, t) => JSON.stringify(e7.contextValues) === JSON.stringify(t.contextValues);
var OV2 = (e7, t) => JSON.stringify(e7.contextValues) === JSON.stringify(t.contextValues);
var qV2 = (e7, t) => {
  let r = QF(e7), n = QF(t);
  return r?.id === n?.id;
};
var QF = (e7) => Object.values(e7).find((t) => t.isActive);
var DV2 = (e7, t) => {
  for (let [r, n] of Object.entries(t)) {
    if (!e7[r])
      return false;
    let o = LF(e7[r]), a = LF(n);
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var LF = (e7) => e7.values.filter((t) => t.state !== "idle");
var pg2 = (e7, t) => {
  for (let [r, n] of Object.entries(t)) {
    if (!e7[r])
      return false;
    let o = e7[r].request.currentValues.filter((i) => i.state !== "idle"), a = n.request.currentValues.filter((i) => i.state !== "idle");
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var VV2 = (e7, t) => {
  for (let [r, n] of Object.entries(t)) {
    if (!e7[r])
      return false;
    let o = ze2(e7[r]?.request.currentValues).map(({ value: i }) => i), a = ze2(n?.request.currentValues).map(({ value: i }) => i);
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var NV2 = (e7, t) => {
  for (let [r, n] of Object.entries(t.set)) {
    if (!e7.set[r])
      return false;
    let o = e7.set[r].response.values.filter((i) => i.state !== "idle"), a = n.response.values.filter((i) => i.state !== "idle");
    if (JSON.stringify(o) !== JSON.stringify(a))
      return false;
  }
  return true;
};
var MV2 = (e7, t) => e7.firstResult === t.firstResult && e7.numberOfResults === t.numberOfResults;
var QV2 = (e7, t) => JSON.stringify(e7) === JSON.stringify(t);
var LV2 = (e7, t) => JSON.stringify(e7) === JSON.stringify(t);
var BV2 = (e7, t) => e7.sortCriteria === t.sortCriteria;
var UV2 = (e7, t) => e7 === t;
var _V2 = (e7, t) => e7 === t;
var jV = (e7, t) => bo2(e7, t);
var $V = (e7, t) => e7 === t;
var XV2 = new NumberValue2({ min: 1, default: 8, required: false });
var ZV2 = new NumberValue2({ min: 1, max: 20, default: 5, required: false });
var eN2 = { desiredCount: ZV2, numberOfValues: XV2 };
var kd2 = h3("automaticFacet/setOptions", (e7) => x(e7, eN2));
var Od = h3("automaticFacet/deselectAll", (e7) => x(e7, K2));
var tN = V2;
var qn2 = h3("automaticFacet/toggleSelectValue", (e7) => x(e7, { field: tN, selection: new RecordValue2({ values: So2 }) }));
var yr = $2(ht2(), (e7) => {
  e7.addCase(da2, (t, r) => {
    let n = mg2(t), o = r.payload;
    t.defaultNumberOfResults = t.numberOfResults = o, t.firstResult = cc2(n, o);
  }).addCase(pa2, (t, r) => {
    t.numberOfResults = r.payload, t.firstResult = 0;
  }).addCase(ot2, (t) => {
    t.firstResult = 0;
  }).addCase(ma2, (t, r) => {
    let n = r.payload;
    t.firstResult = cc2(n, t.numberOfResults);
  }).addCase(gt2, (t, r) => {
    let n = r.payload;
    t.firstResult = cc2(n, t.numberOfResults);
  }).addCase(ga2, (t) => {
    let r = mg2(t), n = Math.max(r - 1, 1);
    t.firstResult = cc2(n, t.numberOfResults);
  }).addCase(fa2, (t) => {
    let r = mg2(t), n = rN(t), o = Math.min(r + 1, n);
    t.firstResult = cc2(o, t.numberOfResults);
  }).addCase(ae2.fulfilled, (t, r) => {
    r.payload && (t.numberOfResults = r.payload.pagination.numberOfResults, t.firstResult = r.payload.pagination.firstResult);
  }).addCase(ce2, (t, r) => {
    t.firstResult = r.payload.firstResult ?? t.firstResult, t.numberOfResults = r.payload.numberOfResults ?? t.defaultNumberOfResults;
  }).addCase(N2.fulfilled, (t, r) => {
    let { response: n } = r.payload;
    t.totalCountFiltered = n.totalCountFiltered;
  }).addCase(me2, (t) => {
    je2(t);
  }).addCase(dr2, (t) => {
    je2(t);
  }).addCase(cr2, (t) => {
    je2(t);
  }).addCase(fr2, (t) => {
    je2(t);
  }).addCase(fo2, (t) => {
    je2(t);
  }).addCase(sr2, (t) => {
    je2(t);
  }).addCase(Yt2, (t) => {
    je2(t);
  }).addCase(xn2, (t) => {
    je2(t);
  }).addCase(_a2, (t) => {
    je2(t);
  }).addCase(lr2, (t) => {
    je2(t);
  }).addCase(mr2, (t) => {
    je2(t);
  }).addCase(Se2, (t) => {
    je2(t);
  }).addCase(Mr2, (t) => {
    je2(t);
  }).addCase(Qr2, (t) => {
    je2(t);
  }).addCase(mo2, (t) => {
    je2(t);
  }).addCase(qn2, (t) => {
    je2(t);
  });
});
function je2(e7) {
  e7.firstResult = ht2().firstResult;
}
function mg2(e7) {
  let { firstResult: t, numberOfResults: r } = e7;
  return fg2(t, r);
}
function rN(e7) {
  let { totalCountFiltered: t, numberOfResults: r } = e7;
  return gg(t, r);
}
function cc2(e7, t) {
  return (e7 - 1) * t;
}
function fg2(e7, t) {
  return Math.round(e7 / t) + 1;
}
function gg(e7, t) {
  let r = Math.min(e7, 5e3);
  return Math.ceil(r / t);
}
function nN(e7) {
  return e7.pagination.firstResult;
}
function UF(e7) {
  return e7.pagination.numberOfResults;
}
function oN(e7) {
  return e7.pagination.totalCountFiltered;
}
var Dn = (e7) => {
  let t = nN(e7), r = UF(e7);
  return fg2(t, r);
};
var qd = (e7) => {
  let t = oN(e7), r = UF(e7);
  return gg(t, r);
};
var Sg2 = (e7, t) => {
  let r = Dn(e7), n = qd(e7), o = aN(r, t);
  return o = iN(o), o = sN(o, n), cN(o);
};
function aN(e7, t) {
  let r = t % 2 === 0, n = Math.floor(t / 2), o = r ? n - 1 : n, a = e7 - n, i = e7 + o;
  return { start: a, end: i };
}
function iN(e7) {
  let t = Math.max(1 - e7.start, 0), r = e7.start + t, n = e7.end + t;
  return { start: r, end: n };
}
function sN(e7, t) {
  let r = Math.max(e7.end - t, 0), n = Math.max(e7.start - r, 1), o = e7.end - r;
  return { start: n, end: o };
}
function cN(e7) {
  let t = [];
  for (let r = e7.start; r <= e7.end; ++r)
    t.push(r);
  return t;
}
var li = () => L2("analytics/pager/number", (e7, t) => e7.makePagerNumber({ pagerNumber: Dn(t) }));
var Dd = () => L2("analytics/pager/next", (e7, t) => e7.makePagerNext({ pagerNumber: Dn(t) }));
var Vd = () => L2("analytics/pager/previous", (e7, t) => e7.makePagerPrevious({ pagerNumber: Dn(t) }));
var di = () => ({ actionCause: "browseResults" });
var uN = new Schema2({ numberOfPages: new NumberValue2({ default: 5, min: 0 }) });
var lN = new Schema2({ page: new NumberValue2({ min: 1 }) });
function $F(e7, t = {}) {
  if (!dN(e7))
    ;
  let r = j(e7), { dispatch: n } = e7, o = ue(e7, uN, t.options, "buildPager"), i = Ae(e7, lN, t.initialState, "buildPager").page;
  i && n(ma2(i));
  let s = () => Dn(e7.state), c = () => {
    let { numberOfPages: l } = o;
    return Sg2(e7.state, l);
  }, u = () => qd(e7.state);
  return { ...r, get state() {
    let l = s(), m = u(), p = l > 1 && m > 0, d = l < m;
    return { currentPage: l, currentPages: c(), maxPage: m, hasPreviousPage: p, hasNextPage: d };
  }, selectPage(l) {
    n(gt2(l));
  }, nextPage() {
    n(fa2());
  }, previousPage() {
    n(ga2());
  }, isCurrentPage(l) {
    return l === this.state.currentPage;
  } };
}
function dN(e7) {
  return e7.addReducers({ configuration: G, pagination: yr }), true;
}
function pN(e7, t = {}) {
  let { dispatch: r } = e7, n = $F(e7, t);
  return { ...n, get state() {
    return n.state;
  }, selectPage(o) {
    n.selectPage(o), r(Wt2({ legacy: li(), next: di() }));
  }, nextPage() {
    n.nextPage(), r(Wt2({ legacy: Dd(), next: di() }));
  }, previousPage() {
    n.previousPage(), r(Wt2({ legacy: Vd(), next: di() }));
  } };
}
function pi2(e7) {
  if (!gN(e7))
    ;
  let t = j(e7), r = () => e7.state;
  return { ...t, get state() {
    let n = r();
    return { hasError: n.search.error !== null, isLoading: n.search.isLoading, hasResults: !!n.search.results.length, firstSearchExecuted: Ts2(n) };
  } };
}
function gN(e7) {
  return e7.addReducers({ search: z }), true;
}
var wN = { results: new ArrayValue2({ required: true, each: new RecordValue2({ values: su }) }), maxLength: new NumberValue2({ required: true, min: 1, default: 10 }) };
var mi2 = h3("recentResults/registerRecentResults", (e7) => x(e7, wN));
var Rt2 = h3("recentResults/pushRecentResult", (e7) => (Ke2(e7), { payload: e7 }));
var fi2 = h3("recentResults/clearRecentResults");
var uc2 = { id: V2 };
var gi2 = h3("querySuggest/register", (e7) => x(e7, { ...uc2, count: new NumberValue2({ min: 0 }) }));
var zF2 = h3("querySuggest/unregister", (e7) => x(e7, uc2));
var Cr2 = h3("querySuggest/selectSuggestion", (e7) => x(e7, { ...uc2, expression: se }));
var Vn2 = h3("querySuggest/clear", (e7) => x(e7, uc2));
var Nn2 = W2("querySuggest/fetch", async (e7, { getState: t, rejectWithValue: r, extra: { apiClient: n, validatePayload: o, navigatorContext: a } }) => {
  o(e7, uc2);
  let i = e7.id, s = await QN2(i, t(), a), c = await n.querySuggest(s);
  return we2(c) ? r(c.error) : { id: i, q: s.q, ...c.success };
});
var QN2 = async (e7, t, r) => ({ accessToken: t.configuration.accessToken, organizationId: t.configuration.organizationId, url: t.configuration.search.apiBaseUrl ?? ve2(t.configuration.organizationId, t.configuration.environment), count: t.querySuggest[e7].count, q: t.querySet[e7], locale: t.configuration.search.locale, timezone: t.configuration.search.timezone, actionsHistory: t.configuration.analytics.enabled ? dt2.getHistory() : [], ...t.context && { context: t.context.contextValues }, ...t.pipeline && { pipeline: t.pipeline }, ...t.searchHub && { searchHub: t.searchHub }, tab: t.configuration.analytics.originLevel2, ...t.configuration.analytics.enabled && { ...t.configuration.analytics.enabled && t.configuration.analytics.analyticsMode === "legacy" ? await ya2(t.configuration.analytics) : Sa2(t.configuration.analytics, r) }, ...t.configuration.search.authenticationProviders.length && { authentication: t.configuration.search.authenticationProviders.join(",") } });
var lc2 = { id: V2, query: se };
var Si = h3("querySet/register", (e7) => x(e7, lc2));
var vo2 = h3("querySet/update", (e7) => x(e7, lc2));
var KF2 = h3("commerce/querySet/register", (e7) => x(e7, lc2));
var YF2 = h3("commerce/querySet/update", (e7) => x(e7, lc2));
$2(Pu2(), (e7) => {
  e7.addCase(Si, (t, r) => XF2(t, r.payload)).addCase(KF2, (t, r) => XF2(t, r.payload)).addCase(vo2, (t, r) => {
    let { id: n, query: o } = r.payload;
    dc(t, n, o);
  }).addCase(YF2, (t, r) => {
    let { id: n, query: o } = r.payload;
    dc(t, n, o);
  }).addCase(Cr2, (t, r) => {
    let { id: n, expression: o } = r.payload;
    dc(t, n, o);
  }).addCase(Zx2, (t, r) => {
    let { id: n, expression: o } = r.payload;
    dc(t, n, o);
  }).addCase(Pn2.fulfilled, (t, r) => {
    let { queryExecuted: n } = r.payload;
    hg(t, n);
  }).addCase(N2.fulfilled, (t, r) => {
    let { queryExecuted: n } = r.payload;
    hg(t, n);
  }).addCase(ce2, JF).addCase(bd, JF).addCase(ae2.fulfilled, (t, r) => {
    if (r.payload)
      for (let [n, o] of Object.entries(r.payload.querySet))
        dc(t, n, o);
  });
});
function JF(e7, t) {
  isNullOrUndefined2(t.payload.q) || hg(e7, t.payload.q);
}
function hg(e7, t) {
  Object.keys(e7).forEach((r) => e7[r] = t);
}
var dc = (e7, t, r) => {
  t in e7 && (e7[t] = r);
};
var XF2 = (e7, t) => {
  let { id: r, query: n } = t;
  r in e7 || (e7[r] = n);
};
var eR2 = () => ({});
$2(eR2(), (e7) => e7.addCase(gi2, (t, r) => {
  tR2(t, r.payload);
}).addCase(Xx2, (t, r) => {
  tR2(t, r.payload);
}).addCase(zF2, (t, r) => {
  delete t[r.payload.id];
}).addCase(Nn2.pending, rR2).addCase(Nn2.fulfilled, (t, r) => {
  let n = t[r.meta.arg.id];
  if (!n || r.meta.requestId !== n.currentRequestId)
    return;
  let { q: o } = r.payload;
  o && n.partialQueries.push(o.replace(/;/, encodeURIComponent(";"))), n.responseId = r.payload.responseId, n.completions = r.payload.completions, n.isLoading = false, n.error = null;
}).addCase(Nn2.rejected, nR).addCase(vn2.pending, rR2).addCase(vn2.fulfilled, (t, r) => {
  let n = t[r.meta.arg.id];
  if (!n || r.meta.requestId !== n.currentRequestId)
    return;
  let { query: o } = r.payload;
  o && n.partialQueries.push(o.replace(/;/, encodeURIComponent(";"))), n.responseId = r.payload.responseId, n.completions = r.payload.completions.map((a) => ({ expression: a.expression, highlighted: a.highlighted, score: 0, executableConfidence: 0 })), n.isLoading = false, n.error = null;
}).addCase(vn2.rejected, nR).addCase(Vn2, (t, r) => {
  oR(t, r.payload);
}).addCase(Jx2, (t, r) => {
  oR(t, r.payload);
}));
function tR2(e7, t) {
  let r = t.id;
  r in e7 || (e7[r] = BN(t));
}
function BN(e7) {
  return { id: "", completions: [], responseId: "", count: 5, currentRequestId: "", error: null, partialQueries: [], isLoading: false, ...e7 };
}
function rR2(e7, t) {
  let r = e7[t.meta.arg.id];
  r && (r.currentRequestId = t.meta.requestId, r.isLoading = true);
}
function nR(e7, t) {
  let r = e7[t.meta.arg.id];
  r && (r.error = t.payload || null, r.isLoading = false);
}
function oR(e7, t) {
  let r = e7[t.id];
  r && (r.responseId = "", r.completions = [], r.partialQueries = []);
}
$2(Fe2(), (e7) => e7.addCase(Le2, (t, r) => ({ ...t, ...r.payload })).addCase(St2, (t, r) => {
  t.q = r.payload;
}).addCase(Cr2, (t, r) => {
  t.q = r.payload.expression;
}).addCase(ae2.fulfilled, (t, r) => r.payload?.query ?? t).addCase(ce2, (t, r) => {
  t.q = r.payload.q ?? t.q, t.enableQuerySyntax = r.payload.enableQuerySyntax ?? t.enableQuerySyntax;
}));
function _d(e7) {
  return e7 ? e7.expiresAt && Date.now() >= e7.expiresAt : false;
}
var uR2 = (e7, t) => {
  let { id: r } = e7;
  if (!t[r])
    return t[r] = { q: "", cache: {} }, t;
};
var lR2 = (e7, t) => {
  let { q: r, id: n } = e7;
  r && (t[n].q = r);
};
var dR2 = (e7, t) => {
  let { id: r } = e7;
  Object.entries(t[r].cache).forEach(([n, o]) => {
    _d(o) && delete t[r].cache[n];
  });
};
var pR2 = (e7, t, r) => {
  for (let o in t)
    for (let a in t[o].cache)
      t[o].cache[a].isActive = false;
  if (!Fg(e7, t)) {
    GN(e7, t, r);
    return;
  }
  let n = Fg(e7, t);
  n.isLoading = true, n.isActive = true, n.error = null;
};
var mR2 = (e7, t, r) => {
  let { id: n, q: o, searchUid: a, cacheTimeout: i, totalCountFiltered: s, duration: c } = e7;
  t[n].cache[o] = { ...Fg(e7, t), ...r, isActive: true, searchUid: a, isLoading: false, error: null, expiresAt: i ? i + Date.now() : 0, totalCountFiltered: s, duration: c };
};
var fR = (e7, t) => {
  let { id: r, q: n, error: o } = e7;
  t[r].cache[n].error = o || null, t[r].cache[n].isLoading = false, t[r].cache[n].isActive = false;
};
var Fg = (e7, t) => {
  let { q: r, id: n } = e7;
  return t[n].cache[r] || null;
};
var GN = (e7, t, r) => {
  let { q: n, id: o } = e7;
  t[o].cache[n] = { isLoading: true, error: null, expiresAt: 0, isActive: true, searchUid: "", totalCountFiltered: 0, duration: 0, ...r };
};
function gR() {
  return {};
}
$2(gR(), (e7) => {
  e7.addCase(ua2, (t, r) => {
    uR2(r.payload, t);
  }), e7.addCase(jt2, (t, r) => {
    lR2(r.payload, t);
  }), e7.addCase(la2, (t, r) => {
    dR2(r.payload, t);
  }), e7.addCase(wa2.pending, (t, r) => {
    pR2(r.meta.arg, t, { results: [] });
  }), e7.addCase(wa2.fulfilled, (t, r) => {
    let n = r.payload.results.map((o) => ({ ...o, searchUid: r.payload.searchUid }));
    mR2({ ...r.payload, ...r.meta.arg }, t, { results: n });
  }), e7.addCase(wa2.rejected, (t, r) => {
    fR(r.meta.arg, t);
  });
});
var yR = { by: new EnumValue2({ enum: Zo, required: true }) };
var xi2 = h3("sortCriteria/register", (e7) => CR(e7));
var Ai2 = h3("sortCriteria/update", (e7) => CR(e7));
var CR = (e7) => isArray2(e7) ? (e7.forEach((t) => x(t, yR)), { payload: e7 }) : x(e7, yR);
$2(pt2(), (e7) => {
  e7.addCase(xi2, (t, r) => Er2(r.payload)).addCase(Ai2, (t, r) => Er2(r.payload)).addCase(ae2.fulfilled, (t, r) => r.payload?.sortCriteria ?? t).addCase(ce2, (t, r) => r.payload.sortCriteria ?? t);
});
var Po2 = V2;
var Wd2 = new RecordValue2({ options: { required: true }, values: { caption: se, expression: se, state: new StringValue2({ constrainTo: ["idle", "selected", "excluded"] }) } });
var Hd = new ArrayValue2({ required: true, each: Wd2 });
var Fi = h3("staticFilter/register", (e7) => x(e7, { id: Po2, values: Hd }));
var Lr2 = h3("staticFilter/toggleSelect", (e7) => x(e7, { id: Po2, value: Wd2 }));
var Br2 = h3("staticFilter/toggleExclude", (e7) => x(e7, { id: Po2, value: Wd2 }));
var Qn2 = h3("staticFilter/deselectAllFilterValues", (e7) => x(e7, Po2));
$2(wu2(), (e7) => e7.addCase(Fi, (t, r) => {
  let n = r.payload, { id: o } = n;
  o in t || (t[o] = n);
}).addCase(Lr2, (t, r) => {
  let { id: n, value: o } = r.payload, a = t[n];
  if (!a)
    return;
  let i = a.values.find((c) => c.caption === o.caption);
  if (!i)
    return;
  let s = i.state === "selected";
  i.state = s ? "idle" : "selected";
}).addCase(Br2, (t, r) => {
  let { id: n, value: o } = r.payload, a = t[n];
  if (!a)
    return;
  let i = a.values.find((c) => c.caption === o.caption);
  if (!i)
    return;
  let s = i.state === "excluded";
  i.state = s ? "idle" : "excluded";
}).addCase(Qn2, (t, r) => {
  let n = r.payload, o = t[n];
  o && o.values.forEach((a) => a.state = "idle");
}).addCase(Se2, (t) => {
  Object.values(t).forEach((r) => {
    r.values.forEach((n) => n.state = "idle");
  });
}).addCase(ce2, (t, r) => {
  let n = r.payload.sf || {};
  Object.entries(t).forEach(([o, a]) => {
    let i = n[o] || [];
    a.values.forEach((s) => {
      s.state = i.includes(s.caption) ? "selected" : "idle";
    });
  });
}));
var bi2 = $2(Iu2(), (e7) => {
  e7.addCase(Da2, (t, r) => {
    let n = r.payload, { id: o } = n;
    o in t || (t[o] = { ...n, isActive: false });
  }).addCase(ot2, (t, r) => {
    let n = r.payload;
    FR(t, n);
  }).addCase(Fs, (t, r) => {
    let n = r.payload;
    FR(t, n);
  }).addCase(ae2.fulfilled, (t, r) => r.payload?.tabSet ?? t);
});
function FR(e7, t) {
  t in e7 && Object.keys(e7).forEach((n) => {
    e7[n].isActive = n === t;
  });
}
var pM = new Schema2({ expression: se, id: V2, clearFiltersOnTabChange: new BooleanValue2() });
var mM = new Schema2({ isActive: new BooleanValue2() });
function vR(e7, t) {
  if (gM(t.options.id), !fM(e7))
    ;
  let r = j(e7), { dispatch: n } = e7;
  ue(e7, pM, t.options, "buildTab");
  let o = Ae(e7, mM, t.initialState, "buildTab"), { id: a, expression: i } = t.options;
  return n(Da2({ id: a, expression: i })), Object.keys(e7.state.tabSet).length === 1 && (o.isActive = true), o.isActive && n(ot2(a)), { ...r, select() {
    t.options.clearFiltersOnTabChange && n(Pa2({ q: "", clearFilters: true })), n(ot2(a));
  }, get state() {
    return { isActive: e7.state.tabSet[a]?.isActive };
  } };
}
function fM(e7) {
  return e7.addReducers({ configuration: G, tabSet: bi2 }), true;
}
function gM(e7) {
  let t = Va().analytics.originLevel2;
  if (e7 === t)
    throw new Error(`The #id option on the Tab controller cannot use the reserved value "${t}". Please specify a different value.`);
}
function SM(e7, t) {
  let { dispatch: r } = e7, n = vR(e7, t), o = () => r(N2({ legacy: Jr(), next: ea2() }));
  return { ...n, get state() {
    return n.state;
  }, select() {
    n.select(), o();
  } };
}
function TR(e7) {
  return e7.type === "redirect";
}
var np = class {
  constructor(t) {
    this.response = t;
  }
  get basicExpression() {
    return this.response.parsedInput.basicExpression;
  }
  get largeExpression() {
    return this.response.parsedInput.largeExpression;
  }
  get redirectionUrl() {
    let t = this.response.preprocessingOutput.triggers.filter(TR);
    return t.length ? t[0].content : null;
  }
};
var vi2 = h3("standaloneSearchBox/register", (e7) => x(e7, { id: V2, redirectionUrl: V2, overwrite: new BooleanValue2({ required: false }) }));
var Pi2 = h3("standaloneSearchBox/updateRedirectionUrl", (e7) => x(e7, { id: V2, redirectionUrl: V2 }));
var wi2 = h3("standaloneSearchBox/reset", (e7) => x(e7, { id: V2 }));
var Ii2 = h3("standaloneSearchBox/updateAnalyticsToSearchFromLink", (e7) => x(e7, { id: V2 }));
var Ei = h3("standaloneSearchBox/updateAnalyticsToOmniboxFromLink");
var Ln2 = W2("standaloneSearchBox/fetchRedirect", async (e7, { dispatch: t, getState: r, rejectWithValue: n, extra: { apiClient: o, validatePayload: a, navigatorContext: i } }) => {
  a(e7, { id: new StringValue2({ emptyAllowed: false }) });
  let s = await EM(r(), i), c = await o.plan(s);
  if (we2(c))
    return n(c.error);
  let { redirectionUrl: u } = new np(c.success);
  return u && t(IM(u)), u || "";
});
var IM = (e7) => L2("analytics/standaloneSearchBox/redirect", (t) => t.makeTriggerRedirect({ redirectedTo: e7 }));
var EM = async (e7, t) => ({ accessToken: e7.configuration.accessToken, organizationId: e7.configuration.organizationId, url: e7.configuration.search.apiBaseUrl ?? ve2(e7.configuration.organizationId, e7.configuration.environment), locale: e7.configuration.search.locale, timezone: e7.configuration.search.timezone, q: e7.query.q, ...e7.context && { context: e7.context.contextValues }, ...e7.pipeline && { pipeline: e7.pipeline }, ...e7.searchHub && { searchHub: e7.searchHub }, ...e7.configuration.analytics.enabled && e7.configuration.analytics.analyticsMode === "legacy" ? await ya2(e7.configuration.analytics) : Sa2(e7.configuration.analytics, t), ...e7.configuration.search.authenticationProviders.length && { authentication: e7.configuration.search.authenticationProviders.join(",") } });
function kR() {
  return {};
}
$2(kR(), (e7) => e7.addCase(vi2, (t, r) => {
  let { id: n, redirectionUrl: o, overwrite: a } = r.payload;
  !a && n in t || (t[n] = vg(o));
}).addCase(wi2, (t, r) => {
  let { id: n } = r.payload, o = t[n];
  if (o) {
    t[n] = vg(o.defaultRedirectionUrl);
    return;
  }
}).addCase(Pi2, (t, r) => {
  let { id: n, redirectionUrl: o } = r.payload;
  n in t && (t[n] = vg(o));
}).addCase(Ln2.pending, (t, r) => {
  let n = t[r.meta.arg.id];
  n && (n.isLoading = true);
}).addCase(Ln2.fulfilled, (t, r) => {
  let n = r.payload, o = t[r.meta.arg.id];
  o && (o.redirectTo = n || o.defaultRedirectionUrl, o.isLoading = false);
}).addCase(Ln2.rejected, (t, r) => {
  let n = t[r.meta.arg.id];
  n && (n.isLoading = false);
}).addCase(Ii2, (t, r) => {
  let n = t[r.payload.id];
  n && (n.analytics.cause = "searchFromLink");
}).addCase(Ei, (t, r) => {
  let n = t[r.payload.id];
  n && (n.analytics.cause = "omniboxFromLink", n.analytics.metadata = r.payload.metadata);
}));
function vg(e7) {
  return { defaultRedirectionUrl: e7, redirectTo: "", isLoading: false, analytics: { cause: "", metadata: null } };
}
function PQ(e7) {
  return pi2(e7);
}
async function up(e7, t) {
  let { search: r, accessToken: n, organizationId: o } = e7.configuration, a = e7.query?.q || "";
  return { url: r.apiBaseUrl ?? ve2(e7.configuration.organizationId, e7.configuration.environment), accessToken: n, organizationId: o, enableNavigation: false, q: a, ...t, requestedOutputSize: t.requestedOutputSize || 0, ...r.authenticationProviders.length && { authentication: r.authenticationProviders.join(",") } };
}
var wo2 = W2("resultPreview/fetchResultContent", async (e7, { extra: t, getState: r, rejectWithValue: n }) => {
  let o = r(), a = await up(o, e7), i = await t.apiClient.html(a);
  return we2(i) ? n(i.error) : { content: i.success, uniqueId: e7.uniqueId };
});
var Oi2 = h3("resultPreview/next");
var qi2 = h3("resultPreview/previous");
var Di2 = h3("resultPreview/prepare", (e7) => x(e7, { results: new ArrayValue2({ required: true }) }));
var GR = 2048;
var Vi2 = W2("resultPreview/updateContentURL", async (e7, { getState: t, extra: r }) => {
  let n = t(), o = RS(await e7.buildResultPreviewRequest(n, { uniqueId: e7.uniqueId, requestedOutputSize: e7.requestedOutputSize }), e7.path);
  return o?.length > GR && r.logger.error(`The content URL was truncated as it exceeds the maximum allowed length of ${GR} characters.`), { contentURL: o };
});
function Tg2() {
  return { uniqueId: "", content: "", isLoading: false, position: -1, resultsWithPreview: [] };
}
var kg2 = (e7) => {
  let { content: t, isLoading: r, uniqueId: n, contentURL: o } = Tg2();
  e7.content = t, e7.isLoading = r, e7.uniqueId = n, e7.contentURL = o;
};
var Og2 = (e7) => e7.filter((t) => t.hasHtmlVersion).map((t) => t.uniqueId);
$2(Tg2(), (e7) => {
  e7.addCase(wo2.pending, (t) => {
    t.isLoading = true;
  }).addCase(wo2.fulfilled, (t, r) => {
    let { content: n, uniqueId: o } = r.payload;
    t.position = t.resultsWithPreview.indexOf(o), t.content = n, t.uniqueId = o, t.isLoading = false;
  }).addCase(N2.fulfilled, (t, r) => {
    kg2(t), t.resultsWithPreview = Og2(r.payload.response.results);
  }).addCase(dn2.fulfilled, (t, r) => {
    kg2(t), t.resultsWithPreview = t.resultsWithPreview.concat(Og2(r.payload.response.results));
  }).addCase(Wt2.fulfilled, kg2).addCase(Di2, (t, r) => {
    t.resultsWithPreview = Og2(r.payload.results);
  }).addCase(Oi2, (t) => {
    if (t.isLoading)
      return;
    let r = t.position + 1;
    r > t.resultsWithPreview.length - 1 && (r = 0), t.position = r;
  }).addCase(qi2, (t) => {
    if (t.isLoading)
      return;
    let r = t.position - 1;
    r < 0 && (r = t.resultsWithPreview.length - 1), t.position = r;
  }).addCase(Vi2.fulfilled, (t, r) => {
    t.contentURL = r.payload.contentURL;
  });
});
function qQ2(e7, t) {
  return e7.raw[t.collection];
}
function qg(e7, t) {
  return e7.raw[t.parent];
}
function yc(e7, t) {
  let r = e7.raw[t.child];
  return Fc2(r) ? r[0] : r;
}
function DQ2(e7, t) {
  return (e7 || t) !== void 0 && e7 === t;
}
function YR2(e7, t, r, n = []) {
  let o = yc(e7, r);
  return o ? n.indexOf(o) !== -1 ? [] : t.filter((a) => {
    let i = yc(a, r) === yc(e7, r);
    return qg(a, r) === o && !i;
  }).map((a) => {
    let i = { ...a, searchUid: e7.searchUid };
    return { result: i, children: YR2(i, t, r, [...n, o]) };
  }) : [];
}
function VQ2(e7, t) {
  return e7.find((r) => {
    let n = qg(r, t) === void 0, o = DQ2(qg(r, t), yc(r, t));
    return n || o;
  });
}
function JR(e7) {
  return e7.parentResult ? JR(e7.parentResult) : e7;
}
function NQ2(e7, t, r, n) {
  let o = au(e7), i = { ...n ?? VQ2(o, t) ?? JR(e7), searchUid: r };
  return { result: i, children: YR2(i, o, t), moreResultsAvailable: e7.totalNumberOfChildResults > 1, isLoadingMoreResults: false };
}
function dp(e7, t, r, n) {
  let o = {};
  return e7.forEach((a) => {
    let i = qQ2(a, t);
    i && (!yc(a, t) && !a.parentResult || (o[i] = NQ2(a, t, r, n)));
  }), o;
}
function KR2(e7, t) {
  if (!e7.collections[t])
    throw new Error(`Missing collection ${t} from ${Object.keys(e7.collections)}: Folding most probably in an invalid state...`);
  return e7.collections[t];
}
$2(il(), (e7) => e7.addCase(N2.fulfilled, (t, { payload: r }) => {
  t.collections = t.enabled ? dp(r.response.results, t.fields, r.response.searchUid) : {};
}).addCase(Wt2.fulfilled, (t, { payload: r }) => {
  t.collections = t.enabled ? dp(r.response.results, t.fields, r.response.searchUid) : {};
}).addCase(dn2.fulfilled, (t, { payload: r }) => {
  t.collections = t.enabled ? { ...t.collections, ...dp(r.response.results, t.fields, r.response.searchUid) } : {};
}).addCase(hn2, (t, { payload: r }) => t.enabled ? t : { enabled: true, collections: {}, fields: { collection: r.collectionField ?? t.fields.collection, parent: r.parentField ?? t.fields.parent, child: r.childField ?? t.fields.child }, filterFieldRange: r.numberOfFoldedResults ?? t.filterFieldRange }).addCase(yn2.pending, (t, { meta: r }) => {
  let n = r.arg;
  KR2(t, n).isLoadingMoreResults = true;
}).addCase(yn2.rejected, (t, { meta: r }) => {
  let n = r.arg;
  KR2(t, n).isLoadingMoreResults = false;
}).addCase(yn2.fulfilled, (t, { payload: { collectionId: r, results: n, rootResult: o, searchUid: a } }) => {
  let i = dp(n, t.fields, a, o);
  if (!i || !i[r])
    throw new Error(`Unable to create collection ${r} from received results: ${JSON.stringify(n)}. Folding most probably in an invalid state... `);
  t.collections[r] = i[r], t.collections[r].moreResultsAvailable = false;
}));
function ZR2(e7) {
  return e7.query = "", e7.queryModification = { originalQuery: "", newQuery: "", queryToIgnore: e7.queryModification.queryToIgnore }, e7;
}
function eb2(e7, t) {
  let r = [], o = [], a = [];
  return t.forEach((i) => {
    switch (i.type) {
      case "redirect":
        r.push(i.content);
        break;
      case "query":
        break;
      case "execute":
        o.push({ functionName: i.content.name, params: i.content.params });
        break;
      case "notify":
        a.push(i.content);
        break;
    }
  }), e7.redirectTo = r[0] ?? "", e7.query = e7.queryModification.newQuery, e7.executions = o, e7.notifications = a, e7;
}
function tb2(e7, t) {
  return e7.queryModification = { ...t, queryToIgnore: "" }, e7;
}
function rb2(e7, t) {
  return e7.queryModification.queryToIgnore = t, e7;
}
var nb = () => ({ redirectTo: "", query: "", executions: [], notifications: [], queryModification: { originalQuery: "", newQuery: "", queryToIgnore: "" } });
$2(nb(), (e7) => e7.addCase(N2.pending, ZR2).addCase(N2.fulfilled, (t, r) => eb2(t, r.payload.response.triggers)).addCase(Fa2, (t, r) => tb2(t, r.payload)).addCase(an2, (t, r) => rb2(t, r.payload)));
var mp = () => new RecordValue2({ values: { questionAnswerId: V2 }, options: { required: true } });
function Ni2(e7) {
  return x(e7, mp());
}
var Mi2 = h3("smartSnippet/expand");
var Qi2 = h3("smartSnippet/collapse");
var Li2 = h3("smartSnippet/like");
var Bi2 = h3("smartSnippet/dislike");
var Ui2 = h3("smartSnippet/feedbackModal/open");
var Un2 = h3("smartSnippet/feedbackModal/close");
var _i2 = h3("smartSnippet/related/expand", (e7) => Ni2(e7));
var ji2 = h3("smartSnippet/related/collapse", (e7) => Ni2(e7));
var Hg2 = () => ({ liked: false, disliked: false, expanded: false, feedbackModalOpen: false, relatedQuestions: [] });
var ib2 = (e7, t) => e7.findIndex((r) => r.questionAnswerId === t.questionAnswerId);
function sb({ question: e7, answerSnippet: t, documentId: { contentIdKey: r, contentIdValue: n } }) {
  return ko2({ question: e7, answerSnippet: t, contentIdKey: r, contentIdValue: n });
}
function YQ2(e7, t) {
  let r = sb(e7);
  return t && r === t.questionAnswerId ? t : { contentIdKey: e7.documentId.contentIdKey, contentIdValue: e7.documentId.contentIdValue, expanded: false, questionAnswerId: r };
}
$2(Hg2(), (e7) => e7.addCase(Mi2, (t) => {
  t.expanded = true;
}).addCase(Qi2, (t) => {
  t.expanded = false;
}).addCase(Li2, (t) => {
  t.liked = true, t.disliked = false, t.feedbackModalOpen = false;
}).addCase(Bi2, (t) => {
  t.liked = false, t.disliked = true;
}).addCase(Ui2, (t) => {
  t.feedbackModalOpen = true;
}).addCase(Un2, (t) => {
  t.feedbackModalOpen = false;
}).addCase(N2.fulfilled, (t, r) => {
  let n = r.payload.response.questionAnswer.relatedQuestions.map((a, i) => YQ2(a, t.relatedQuestions[i])), o = sb(r.payload.response.questionAnswer);
  return t.questionAnswerId === o ? { ...t, relatedQuestions: n } : { ...Hg2(), relatedQuestions: n, questionAnswerId: o };
}).addCase(_i2, (t, r) => {
  let n = ib2(t.relatedQuestions, r.payload);
  n !== -1 && (t.relatedQuestions[n].expanded = true);
}).addCase(ji2, (t, r) => {
  let n = ib2(t.relatedQuestions, r.payload);
  n !== -1 && (t.relatedQuestions[n].expanded = false);
}));
var iL2 = { queries: new ArrayValue2({ required: true, each: new StringValue2({ emptyAllowed: false }) }), maxLength: new NumberValue2({ required: true, min: 1, default: 10 }) };
var Io = h3("recentQueries/registerRecentQueries", (e7) => x(e7, iL2));
var $i2 = h3("recentQueries/clearRecentQueries");
function mb() {
  return { queries: [], maxLength: 10 };
}
$2(mb(), (e7) => {
  e7.addCase(Io, sL2).addCase($i2, cL2).addCase(N2.fulfilled, (t, r) => {
    let n = r.payload.queryExecuted, o = r.payload.response.results;
    !n.length || !o.length || uL2(n, t);
  });
});
function sL2(e7, t) {
  e7.queries = Array.from(new Set(t.payload.queries.map((r) => r.trim().toLowerCase()))).slice(0, t.payload.maxLength), e7.maxLength = t.payload.maxLength;
}
function cL2(e7) {
  e7.queries = [];
}
function uL2(e7, t) {
  let r = e7.trim().toLowerCase();
  if (r === "")
    return;
  let n = Array.from(new Set(t.queries.filter((o) => o.trim().toLowerCase() !== r))).slice(0, t.maxLength - 1);
  t.queries = [r, ...n];
}
function Cb2() {
  return { results: [], maxLength: 10 };
}
$2(Cb2(), (e7) => {
  e7.addCase(mi2, (t, r) => {
    t.results = r.payload.results.slice(0, r.payload.maxLength), t.maxLength = r.payload.maxLength;
  }).addCase(fi2, (t) => {
    t.results = [];
  }).addCase(Rt2, (t, r) => {
    let n = r.payload;
    t.results = t.results.filter((a) => a.uniqueId !== n.uniqueId);
    let o = t.results.slice(0, t.maxLength - 1);
    t.results = [n, ...o];
  });
});
$2(Wo2(), (e7) => {
  e7.addCase(N2.fulfilled, (t, r) => {
    t.set = {}, r.payload.response.generateAutomaticFacets?.facets?.forEach((o) => {
      t.set[o.field] = { response: o };
    });
  }).addCase(kd2, (t, r) => {
    r.payload.desiredCount && (t.desiredCount = r.payload.desiredCount), r.payload.numberOfValues && (t.numberOfValues = r.payload.numberOfValues);
  }).addCase(qn2, (t, r) => {
    let { field: n, selection: o } = r.payload, a = t.set[n]?.response;
    if (!a)
      return;
    let i = a.values.find((c) => c.value === o.value);
    if (!i)
      return;
    let s = i.state === "selected";
    i.state = s ? "idle" : "selected";
  }).addCase(Od, (t, r) => {
    let n = r.payload, o = t.set[n]?.response;
    if (o)
      for (let a of o.values)
        a.state = "idle";
  }).addCase(ce2, (t, r) => {
    let n = r.payload.af ?? {}, o = Object.keys(t.set);
    for (let a in n)
      if (!t.set[a]) {
        let i = VL2(a), s = n[a].map((c) => Ab(c));
        i.values.push(...s), t.set[a] = { response: i };
      }
    for (let a of o)
      if (!(a in n)) {
        let i = t.set[a]?.response;
        for (let s of i.values)
          s.state = "idle";
      }
    for (let a in n) {
      let i = t.set[a]?.response;
      if (i) {
        let s = i.values, c = new Set(n[a]);
        for (let u of s)
          c.has(u.value) ? (u.state = "selected", c.delete(u.value)) : u.state = "idle";
        for (let u of c)
          i.values.push(Ab(u));
      }
    }
  }).addCase(ae2.fulfilled, (t, r) => {
    if (r.payload && Object.keys(r.payload.automaticFacetSet.set).length !== 0)
      return r.payload.automaticFacetSet;
  }).addCase(Se2, (t) => {
    Object.values(t.set).forEach(({ response: r }) => {
      r.values.forEach((n) => n.state = "idle");
    });
  });
});
function VL2(e7) {
  return { field: e7, values: [], moreValuesAvailable: false, label: "", indexScore: 0 };
}
function Ab(e7) {
  return { value: e7, state: "selected", numberOfResults: 0 };
}
function zg2() {
  return { id: "", isVisible: true, isEnabled: true, isLoading: false, isStreaming: false, citations: [], liked: false, disliked: false, responseFormat: { contentFormat: ["text/plain"] }, feedbackModalOpen: false, feedbackSubmitted: false, fieldsToIncludeInCitations: [], isAnswerGenerated: false, expanded: false, cannotAnswer: false };
}
$2(zg2(), (e7) => e7.addCase(Ta2, (t, { payload: r }) => {
  t.isVisible = r;
}).addCase(Ms2, (t, { payload: r }) => {
  t.isEnabled = r;
}).addCase(Gu2, (t, { payload: r }) => {
  t.id = r.id;
}).addCase(Qs2, (t, { payload: r }) => {
  t.isLoading = false, t.isStreaming = true, t.answer || (t.answer = ""), t.answer += r.textDelta, delete t.error;
}).addCase(Ls2, (t, { payload: r }) => {
  t.isLoading = false, t.isStreaming = true;
  let n = /* @__PURE__ */ new Map();
  for (let o of [t.citations, r.citations])
    for (let a of o)
      n.set(a.uri, a);
  t.citations = Array.from(n.values()), delete t.error;
}).addCase(cf2, (t, { payload: r }) => {
  t.isLoading = false, t.isStreaming = false, t.error = { ...r, isRetryable: r.code === kp }, t.citations = [], delete t.answer;
}).addCase(Uu2, (t) => {
  t.liked = true, t.disliked = false;
}).addCase(_u2, (t) => {
  t.liked = false, t.disliked = true;
}).addCase(ju2, (t) => {
  t.feedbackModalOpen = true;
}).addCase(Wu2, (t) => {
  t.feedbackModalOpen = false;
}).addCase(ka2, (t) => {
  t.feedbackSubmitted = true;
}).addCase(zt2, (t) => ({ ...zg2(), ...t.answerConfigurationId ? { answerConfigurationId: t.answerConfigurationId } : {}, responseFormat: t.responseFormat, fieldsToIncludeInCitations: t.fieldsToIncludeInCitations, isVisible: t.isVisible, id: t.id })).addCase(Ns2, (t, { payload: r }) => {
  t.isLoading = r;
}).addCase(Lu, (t, { payload: r }) => {
  t.isStreaming = r;
}).addCase(Us2, (t, { payload: r }) => {
  t.answerContentFormat = r;
}).addCase(Hu2, (t, { payload: r }) => {
  t.responseFormat = r;
}).addCase(Ku2, (t, r) => {
  t.fieldsToIncludeInCitations = [...new Set(t.fieldsToIncludeInCitations.concat(r.payload))];
}).addCase(uf2, (t, { payload: r }) => {
  t.isAnswerGenerated = r;
}).addCase(Bs2, (t) => {
  t.expanded = true;
}).addCase($u2, (t) => {
  t.expanded = false;
}).addCase(zu2, (t, { payload: r }) => {
  t.answerConfigurationId = r;
}).addCase(no2, (t, { payload: r }) => {
  t.cannotAnswer = r;
}));
Zu2.injectEndpoints({ endpoints: (e7) => ({ post: e7.mutation({ query: (t) => ({ url: "/evaluations", method: "POST", body: t }) }) }) });
var _n2 = () => new StringValue2({ required: false, emptyAllowed: true });
var Ap2 = h3("advancedSearchQueries/update", (e7) => x(e7, { aq: _n2(), cq: _n2(), lq: _n2(), dq: _n2() }));
var Fp2 = h3("advancedSearchQueries/register", (e7) => x(e7, { aq: _n2(), cq: _n2(), lq: _n2(), dq: _n2() }));
$2(It2(), (e7) => {
  e7.addCase(Ap2, (t, r) => {
    let { aq: n, cq: o, lq: a, dq: i } = r.payload;
    isUndefined2(n) || (t.aq = n, t.aqWasSet = true), isUndefined2(o) || (t.cq = o, t.cqWasSet = true), isUndefined2(a) || (t.lq = a, t.lqWasSet = true), isUndefined2(i) || (t.dq = i, t.dqWasSet = true);
  }).addCase(Fp2, (t, r) => {
    let { aq: n, cq: o, lq: a, dq: i } = r.payload;
    isUndefined2(n) || (t.defaultFilters.aq = n, t.aqWasSet || (t.aq = n)), isUndefined2(o) || (t.defaultFilters.cq = o, t.cqWasSet || (t.cq = o)), isUndefined2(a) || (t.defaultFilters.lq = a, t.lqWasSet || (t.lq = a)), isUndefined2(i) || (t.defaultFilters.dq = i, t.dqWasSet || (t.dq = i));
  }).addCase(ae2.fulfilled, (t, r) => r.payload?.advancedSearchQueries ?? t).addCase(ce2, (t, r) => {
    let { aq: n, cq: o } = r.payload;
    isUndefined2(n) || (t.aq = n, t.aqWasSet = true), isUndefined2(o) || (t.cq = o, t.cqWasSet = true);
  });
});
var Rp = h3("excerptLength/set", (e7) => x(e7, new NumberValue2({ min: 0, required: true })));
function Tb() {
  return { length: void 0 };
}
$2(Tb(), (e7) => {
  e7.addCase(Rp, (t, r) => {
    t.length = r.payload;
  });
});
W2("analytics/addPageViewEntry", async (e7, { getState: t }) => {
  t().configuration.analytics.enabled && dt2.addElement({ name: "PageView", value: e7, time: JSON.stringify(/* @__PURE__ */ new Date()) });
});

// dist/components/unisyd-pager.js
var UnisydPager$1 = /* @__PURE__ */ proxyCustomElement(class UnisydPager extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
    this.pageChanged = createEvent(this, "pageChanged");
    this.numberOfPages = 5;
    this.isInitialized = false;
  }
  async connectedCallback() {
    await this.initializeHeadlessControllers();
  }
  disconnectedCallback() {
    this.unsubscribePager?.();
    this.unsubscribeSearchStatus?.();
  }
  async initializeHeadlessControllers() {
    try {
      await this.waitForSearchInterface();
      const searchInterface = document.querySelector("atomic-search-interface");
      if (!searchInterface) {
        console.error("No atomic-search-interface found");
        return;
      }
      await this.waitForSearchInterfaceInitialization(searchInterface);
      this.engine = searchInterface.engine;
      if (!this.engine) {
        console.error("No engine found on search interface");
        return;
      }
      this.pager = pN(this.engine);
      this.searchStatus = PQ(this.engine);
      this.unsubscribePager = this.pager.subscribe(() => {
        this.pagerState = this.pager.state;
      });
      this.unsubscribeSearchStatus = this.searchStatus.subscribe(() => {
        this.searchStatusState = this.searchStatus.state;
      });
      this.pagerState = this.pager.state;
      this.searchStatusState = this.searchStatus.state;
      this.isInitialized = true;
    } catch (error) {
      console.error("Error initializing unisyd-pager:", error);
    }
  }
  async waitForSearchInterface() {
    return new Promise((resolve) => {
      const checkForSearchInterface = () => {
        const searchInterface = document.querySelector("atomic-search-interface");
        if (searchInterface) {
          resolve();
        } else {
          setTimeout(checkForSearchInterface, 100);
        }
      };
      checkForSearchInterface();
    });
  }
  async waitForSearchInterfaceInitialization(searchInterface) {
    return new Promise((resolve) => {
      const checkForInitialization = () => {
        if (searchInterface.engine) {
          resolve();
        } else {
          setTimeout(checkForInitialization, 100);
        }
      };
      checkForInitialization();
    });
  }
  getPageNumbers() {
    if (!this.pagerState || !this.isInitialized) {
      return [];
    }
    const { currentPage, maxPage } = this.pagerState;
    const pages = [];
    if (maxPage <= 7) {
      for (let i = 1; i <= maxPage; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      if (currentPage <= 4) {
        for (let i = 2; i <= 5; i++) {
          pages.push(i);
        }
        pages.push("ellipsis");
        pages.push(maxPage);
      } else if (currentPage >= maxPage - 3) {
        pages.push("ellipsis");
        for (let i = maxPage - 4; i <= maxPage; i++) {
          pages.push(i);
        }
      } else {
        pages.push("ellipsis");
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push("ellipsis");
        pages.push(maxPage);
      }
    }
    return pages;
  }
  handlePageClick(pageNumber) {
    if (this.pager && pageNumber !== this.pagerState.currentPage) {
      this.pager.selectPage(pageNumber);
      this.pageChanged.emit(pageNumber);
    }
  }
  handlePrevious() {
    if (this.pager && this.pagerState.hasPreviousPage) {
      this.pager.previousPage();
      this.pageChanged.emit(this.pagerState.currentPage - 1);
    }
  }
  handleNext() {
    if (this.pager && this.pagerState.hasNextPage) {
      this.pager.nextPage();
      this.pageChanged.emit(this.pagerState.currentPage + 1);
    }
  }
  renderPageButton(pageNumber) {
    const isSelected = this.pagerState.currentPage === pageNumber;
    return h("button", { type: "button", class: `page-button ${isSelected ? "active" : ""}`, part: `page-button${isSelected ? " active-page-button" : ""}`, "aria-current": isSelected ? "page" : "false", "aria-label": `Page ${pageNumber}`, onClick: () => this.handlePageClick(pageNumber) }, pageNumber);
  }
  renderEllipsis(key) {
    return h("span", { class: "ellipsis", part: "ellipsis", key }, "...");
  }
  renderPreviousButton() {
    const canGoPrevious = this.pagerState?.hasPreviousPage;
    return h("button", { type: "button", class: "nav-button previous-button", part: "previous-button", disabled: !canGoPrevious, "aria-label": "Previous page", onClick: () => this.handlePrevious() }, h("span", { part: "previous-button-icon" }, this.previousButtonIcon || h("svg", { viewBox: "0 0 20 20" }, h("path", { d: "M12 4L6 10L12 16", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", fill: "none" }))));
  }
  renderNextButton() {
    const canGoNext = this.pagerState?.hasNextPage;
    return h("button", { type: "button", class: "nav-button next-button", part: "next-button", disabled: !canGoNext, "aria-label": "Next page", onClick: () => this.handleNext() }, h("span", { part: "next-button-icon" }, this.nextButtonIcon || h("svg", { viewBox: "0 0 20 20" }, h("path", { d: "M8 4L14 10L8 16", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", fill: "none" }))));
  }
  render() {
    if (!this.isInitialized || !this.pagerState || !this.searchStatusState) {
      return null;
    }
    if (!this.searchStatusState.hasResults || this.pagerState.maxPage <= 1) {
      return null;
    }
    const pageNumbers = this.getPageNumbers();
    return h("nav", { "aria-label": "Pagination", class: "pager-wrapper" }, h("div", { part: "buttons", role: "toolbar", class: "pager-container" }, this.renderPreviousButton(), h("div", { part: "page-buttons", class: "page-buttons-container" }, pageNumbers.map((item, index) => {
      if (item === "ellipsis") {
        return this.renderEllipsis(`ellipsis-${index}`);
      }
      return this.renderPageButton(item);
    })), this.renderNextButton()));
  }
  get host() {
    return this;
  }
  static get style() {
    return ":host {\n      display: block;\n    }\n\n    .pager-wrapper {\n      margin: 25px 0 0 0;\n      display: flex;\n      justify-content: center;\n      width: 100%;\n    }\n\n    .pager-container {\n      display: flex;\n      align-items: center;\n      justify-content: center;\n      gap: 8px;\n      flex-wrap: wrap;\n    }\n\n    .page-buttons-container {\n      display: flex;\n      align-items: center;\n      gap: 6px;\n    }\n\n    .page-button {\n      box-sizing: border-box;\n      display: flex;\n      flex-direction: row;\n      justify-content: center;\n      align-items: center;\n      padding: 16px;\n      gap: 8px;\n      width: 44px;\n      height: 44px;\n      border: 1px solid rgba(128, 134, 139, 0.25);\n      color: var(--atomic-on-background);\n      border-radius: 4px;\n      font-family: var(--atomic-font-family);\n      font-weight: 400;\n      font-size: 18px;\n      line-height: 20px;\n      text-decoration: none;\n      margin-right: 4px;\n      background-color: var(--atomic-background);\n      cursor: pointer;\n      transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;\n    }\n\n    .page-button.active {\n      background: var(--atomic-primary);\n      border: 1px solid var(--atomic-primary);\n      color: #FFFFFF;\n      font-weight: 700;\n    }\n\n    .page-button.active:focus-visible {\n      outline: 2px solid #C63A1E;\n      outline-offset: 2px;\n    }\n\n    .page-button.active:focus:not(:focus-visible) {\n      outline: none;\n    }\n\n    .page-button:hover:not(.active) {\n      background: #FDEDEA;\n      border: 1px solid #C63A1E;\n      color: #C63A1E;\n      cursor: pointer;\n      transition: all 0.2s ease;\n    }\n\n    .page-button:focus-visible:not(.active) {\n      outline: 2px solid #C63A1E;\n      outline-offset: 2px;\n      background: #FDEDEA;\n      border: 1px solid #C63A1E;\n      color: #C63A1E;\n    }\n\n    .page-button:focus:not(.active):not(:focus-visible) {\n      outline: none;\n    }\n\n    /* Remove focus styles on touch devices */\n    @media (hover: none) and (pointer: coarse) {\n      .page-button:focus-visible:not(.active) {\n        outline: none;\n        background: var(--atomic-background);\n        border: 1px solid rgba(128, 134, 139, 0.25);\n        color: var(--atomic-on-background);\n      }\n      \n      .page-button.active:focus-visible {\n        outline: none;\n      }\n    }\n\n    .page-button.active:hover {\n      background: #AF2B11;\n      border: 1px solid #AF2B11;\n      color: #FFFFFF;\n    }\n\n    .nav-button {\n      box-sizing: border-box;\n      display: flex;\n      flex-direction: row;\n      justify-content: center;\n      align-items: center;\n      padding: 16px;\n      gap: 8px;\n      width: 44px;\n      height: 44px;\n      background: var(--atomic-background);\n      border: 1px solid rgba(128, 134, 139, 0.25);\n      border-radius: 4px;\n      color: var(--atomic-on-background);\n      margin-right: 4px;\n      text-decoration: none;\n      cursor: pointer;\n      transition: all 0.2s ease;\n    }\n\n    .nav-button:disabled {\n      display: none !important;\n    }\n\n    .nav-button:hover:not(:disabled) {\n      cursor: pointer;\n      border: 1px solid #C63A1E;\n      transition: all 0.2s ease;\n    }\n\n    .nav-button:focus-visible:not(:disabled) {\n      outline: 2px solid #C63A1E;\n      outline-offset: 2px;\n      border: 1px solid #C63A1E;\n    }\n\n    .nav-button:focus:not(:disabled):not(:focus-visible) {\n      outline: none;\n    }\n\n    .nav-button span {\n      width: 24px;\n      height: 24px;\n      display: flex;\n      align-items: center;\n      justify-content: center;\n    }\n\n    .nav-button svg {\n      width: 24px;\n      height: 24px;\n    }\n\n    .ellipsis {\n      display: flex;\n      align-items: center;\n      justify-content: center;\n      width: 44px;\n      height: 44px;\n      color: var(--atomic-on-background);\n      font-family: var(--atomic-font-family);\n      font-size: 18px;\n      font-weight: 500;\n      -webkit-user-select: none;\n      user-select: none;\n      margin-right: 0px;\n      margin-left: -4px;\n    }\n\n    /* Responsive adjustments for mobile */\n    @media (max-width: 990px) {\n      .pager-wrapper {\n        margin: 20px auto 0 auto;\n        max-width: 100%;\n        padding: 0 px;\n        box-sizing: border-box;\n      }\n      \n      .pager-container {\n        gap: 8px;\n        justify-content: center;\n        width: 100%;\n      }\n            \n      .nav-button,\n      .page-button {\n        width: 32px;\n        height: 32px;\n        min-width: 32px;\n        min-height: 32px;\n        font-size: 13px;\n        line-height: 18px;\n        padding: 6px;\n        margin-right: 0px;\n      }\n      \n      .nav-button span {\n        width: 20px;\n        height: 20px;\n      }\n      \n      .nav-button svg {\n        width: 20px;\n        height: 20px;\n      }\n      \n      .ellipsis {\n        width: 32px;\n        height: 32px;\n        font-size: 13px;\n        margin-right: -4px;\n        margin-left: -6px;\n      }\n      \n      .page-button:focus-visible:not(.active) {\n        outline: 2px solid #C63A1E;\n        outline-offset: 1px;\n      }\n      \n      .page-button.active:focus-visible {\n        outline: 2px solid #C63A1E;\n        outline-offset: 1px;\n      }\n      \n      .nav-button:focus-visible:not(:disabled) {\n        outline: 2px solid #C63A1E;\n        outline-offset: 1px;\n      }\n    }\n    \n    /* Extra small screens - further reduce for very narrow displays */\n    @media (max-width: 400px) {\n      .pager-container {\n        gap: 6px;\n      }\n            \n      .nav-button,\n      .page-button {\n        width: 28px;\n        height: 28px;\n        min-width: 28px;\n        min-height: 28px;\n        font-size: 12px;\n        line-height: 16px;\n        padding: 4px;\n        margin-right: 0px;\n      }\n      \n      .nav-button span {\n        width: 18px;\n        height: 18px;\n      }\n      \n      .nav-button svg {\n        width: 18px;\n        height: 18px;\n      }\n      \n      .ellipsis {\n        width: 28px;\n        height: 28px;\n        font-size: 12px;\n        margin-right: -5px;\n        margin-left: -7px;\n      }\n      \n      .page-button:focus-visible:not(.active) {\n        outline: 2px solid #C63A1E;\n        outline-offset: 1px;\n      }\n      \n      .page-button.active:focus-visible {\n        outline: 2px solid #C63A1E;\n        outline-offset: 1px;\n      }\n      \n      .nav-button:focus-visible:not(:disabled) {\n        outline: 2px solid #C63A1E;\n        outline-offset: 1px;\n      }\n    }";
  }
}, [257, "unisyd-pager", {
  "numberOfPages": [2, "number-of-pages"],
  "previousButtonIcon": [1, "previous-button-icon"],
  "nextButtonIcon": [1, "next-button-icon"],
  "pagerState": [32],
  "searchStatusState": [32],
  "isInitialized": [32]
}]);
var UnisydPager2 = UnisydPager$1;

// dist/components/unisyd-tab.js
var MissingInterfaceParentError = class extends Error {
  constructor(elementName) {
    super(`The "${elementName}" element must be the child of the following elements: ${initializableElements.join(", ")}`);
  }
};
var initializableElements = [
  "atomic-recs-interface",
  "atomic-search-interface",
  "atomic-commerce-interface",
  "atomic-commerce-recommendation-interface",
  "atomic-relevance-inspector",
  "atomic-insight-interface",
  "atomic-external"
];
var initializeEventName = "atomic/initializeComponent";
function initializeBindings(element) {
  return new Promise((resolve, reject) => {
    const event = buildCustomEvent(initializeEventName, (bindings) => resolve(bindings));
    element.dispatchEvent(event);
    if (!closest(element, initializableElements.join(", "))) {
      reject(new MissingInterfaceParentError(element.nodeName.toLowerCase()));
    }
  });
}
var UnisydTab$1 = /* @__PURE__ */ proxyCustomElement(class UnisydTab extends H {
  constructor() {
    super();
    this.__registerHost();
    this.__attachShadow();
    this.tabUnsubscribe = () => {
    };
    this.isActive = false;
  }
  async connectedCallback() {
    await customElements.whenDefined("atomic-search-interface");
    try {
      this.bindings = await initializeBindings(this.host);
      this.tabController = SM(this.bindings.engine, {
        options: {
          id: this.tabId,
          expression: this.expression
        },
        initialState: {
          isActive: this.isActive
        }
      });
      this.tabController.subscribe(() => this.updateState());
      this.tabUnsubscribe = this.tabController.subscribe(() => this.tabState = this.tabController.state);
    } catch (error) {
      console.log(this.tabUnsubscribe);
      console.error(error);
      this.error = error;
    }
  }
  onClick() {
    if (this.isActive)
      return;
    else {
      this.tabController.select();
    }
  }
  updateState() {
    this.isActive = this.tabController.state.isActive;
  }
  render() {
    if (this.error) {
      return h("p", null, "Error when initializing the component, please view the console for more information.");
    }
    if (!this.bindings || !this.tabState) {
      return h("div", null);
    }
    const selectedAttribute = this.isActive ? "selected" : "";
    const selectedPart = this.isActive ? "tab-container tab-container-selected" : "tab-container";
    return h("div", { class: selectedAttribute, part: selectedPart }, h("a", { class: "tab", part: "tab", onClick: () => this.onClick() }, h("span", { part: "label" }, this.label)));
  }
  get host() {
    return this;
  }
  static get style() {
    return "a, tab {\n      cursor: pointer;\n    }";
  }
}, [257, "unisyd-tab", {
  "label": [1],
  "tabId": [1, "tab-id"],
  "expression": [1],
  "tabState": [32]
}]);
var UnisydTab2 = UnisydTab$1;

// dist/components/index.js
function waitForAtomic(timeoutMs = 5e3) {
  return new Promise((resolve) => {
    if (customElements.get("atomic-search-interface")) {
      console.log("Atomic search interface already defined");
      return resolve(true);
    }
    const timeout = setTimeout(() => {
      console.warn("Timeout waiting for atomic-search-interface to be defined");
      resolve(false);
    }, timeoutMs);
    customElements.whenDefined("atomic-search-interface").then(() => {
      clearTimeout(timeout);
      console.log("Atomic search interface defined");
      resolve(true);
    }).catch((err3) => {
      clearTimeout(timeout);
      console.error("Error waiting for atomic-search-interface:", err3);
      resolve(false);
    });
  });
}
function triggerCoveoSearchSubmit(searchInterfaceId) {
  const searchBox = document.querySelector(`${searchInterfaceId} atomic-search-box`);
  if (!searchBox) {
    console.error("Atomic Search Box not found for interface:", searchInterfaceId);
    return;
  }
  if (searchBox.shadowRoot) {
    const submitButton = searchBox.shadowRoot.querySelector('button[part="submit-button"]');
    if (submitButton) {
      console.log("Clicking the Atomic submit button");
      submitButton.click();
    } else {
      console.error("Could not find submit button in shadow DOM for:", searchInterfaceId);
    }
  } else {
    console.error("Shadow DOM not accessible for search box:", searchInterfaceId);
  }
}
function isAuthorEnvironment() {
  return window.location.pathname.startsWith("/content/") ||
    window.location.pathname.startsWith("/editor.html/content/");
}

function getSearchBaseUrl() {
  const hostname = window.location.hostname;

  const productionUrl = "https://www.sydney.edu.au/search.html";
  const testUrl = "https://cws-test.sydney.edu.au/search.html";
  const authorUrl = "/content/corporate/search.html";
  const stageUrl = "https://cws-stage.sydney.edu.au/search.html";

  // Author
  if (isAuthorEnvironment()) return authorUrl;
  // Test
  if (hostname.includes("test.") || hostname.includes("cws-test") || hostname.startsWith("test.")) {
    return testUrl;
  }
  if (hostname.includes("stage.") || hostname.includes("cws-stage") || hostname.startsWith("stage.")) {
    return stageUrl;
  }
  // others → Production
  return productionUrl;
}

function initializeSearchControls() {
  const searchInterface = document.querySelector("atomic-search-interface#searchbox");
  const searchBox = searchInterface ? searchInterface.querySelector("atomic-search-box") : null;
  const radioGroupContainer = document.querySelector(".m-radio-group");
  const radioInputs = radioGroupContainer ? radioGroupContainer.querySelectorAll('input[type="radio"][name="f-commoncontenttype"]'): [];

  if (!searchBox || !radioGroupContainer || radioInputs.length === 0) {
    console.error("Required search elements not found.");
    return;
  }

  let latestKeyword = "";
  let reloadScheduled = false;

/**
* The main search page https://www.sydney.edu.au/search.html or cms.sydney.edu.au/content/corporate/search.html
*/
  function isOnSearchPage() {
    return window.location.pathname === "/search.html" ||  window.location.pathname === "/content/corporate/search.html";
  }

  function getCurrentSearchValue() {
    try {
      const input =
        searchBox?.shadowRoot?.querySelector('[part="textarea"]') ||
        searchBox?.shadowRoot?.querySelector("textarea") ||
        searchBox?.shadowRoot?.querySelector("input");

      return input?.value || latestKeyword || "";
    } catch (e) {
      return latestKeyword || "";
    }
  }

  function updateRadioButtonState(input, isChecked) {
    const label = input.closest(".m-radio-group__option");
    if (!label)
      return;

    const textSpan = label.querySelector(".m-radio-group__text");
    if (textSpan) {
      textSpan.setAttribute("data-checked", isChecked ? "true" : "false");
    }

    if (isChecked) {
      label.classList.add("m-radio-group__option--checked", "m-radio-group--cws__option--checked");
    } else {
      label.classList.remove("m-radio-group__option--checked", "m-radio-group--cws__option--checked");
    }
  }

  function buildHash(selectedInput) {
    const filterName = selectedInput ? selectedInput.name : "f-commoncontenttype";
    const filter = selectedInput?.value || "Everything";
    const keyword = getCurrentSearchValue();
    if (keyword) {
      return `q=${encodeURIComponent(keyword)}&${filterName}=${encodeURIComponent(filter)}`;
    }
    return `${filterName}=${encodeURIComponent(filter)}`;
  }

  function updateRedirectionUrl(selectedInput) {
    const hash = buildHash(selectedInput);
    const redirectionUrl = `${getSearchBaseUrl()}#${hash}`;
    searchBox.setAttribute("redirection-url", redirectionUrl);
    console.log("Redirection URL set to:", redirectionUrl);
  }

  // for search page only
  function reloadWithParams(selectedInput) {
    if (reloadScheduled) return;
    reloadScheduled = true;
    latestKeyword = getCurrentSearchValue();
    const hash = buildHash(selectedInput);
    console.log("Reloading with hash:", hash);

    // Set hash in URL then reload
    history.replaceState(null, "", `${window.location.pathname}#${hash}`);
    window.location.reload();
  }

  // Waits for Atomic to finish updating its input, then reloads
  function reloadWithParamsDeferred(selectedInput) {
    if (reloadScheduled) return;
    latestKeyword = getCurrentSearchValue();
    setTimeout(() => {
      latestKeyword = getCurrentSearchValue() || latestKeyword;
      reloadWithParams(selectedInput);
    }, 100);
  }

  function getSelectedInput() {
    return (
      document.querySelector('input[type="radio"][name="f-commoncontenttype"]:checked') ||
      radioInputs[0]
    );
  }


  // ---- Only clear if the input is empty at the time of closing
  function resetSearchKeyword() {
    setTimeout(() => {
      const currentValue = getCurrentSearchValue();
      if (!currentValue) {
        latestKeyword = "";
        if (isOnSearchPage()) {
          reloadScheduled = false;
          reloadWithParams(getSelectedInput());
        }
        console.log("Input is empty on panel close — keyword cleared");
      } else {
        console.log("Input still has value on panel close — keyword retained:", currentValue);
      }
    }, 100);
  }

  radioInputs.forEach((input) => updateRadioButtonState(input, input.checked));
  updateRedirectionUrl(getSelectedInput());

  // ---- Radio change ----
  radioInputs.forEach((input) => {
    input.addEventListener("change", function () {
      radioInputs.forEach((other) => updateRadioButtonState(other, other === input));
      updateRedirectionUrl(input);
    });
  });

  // ---- Input typing ----
  searchBox.addEventListener("input", function () {
    latestKeyword = getCurrentSearchValue();
    updateRedirectionUrl(getSelectedInput());
  });

  // ---- Wait for shadow DOM elements ----
  function waitForShadowElement(host, selector, callback, maxAttempts = 50) {
    let attempts = 0;
    function tryFind() {
      const el = host?.shadowRoot?.querySelector(selector);
      if (el) { callback(el); return; }
      if (++attempts < maxAttempts) requestAnimationFrame(tryFind);
      else console.warn(`Shadow element "${selector}" not found after ${maxAttempts} attempts.`);
    }
    tryFind();
  }

  // ---- Submit button ----
  waitForShadowElement(searchBox, 'button[part="submit-button"]', (btn) => {
    btn.addEventListener("click", function () {
      if (isOnSearchPage()) {
        reloadWithParamsDeferred(getSelectedInput());
      } else {
        updateRedirectionUrl(getSelectedInput());
      }
    });
  });

  // ---- Enter key + suggestion navigation ----
  waitForShadowElement(
    searchBox,
    '[part="textarea"]',
    (atomicInput) => {
      atomicInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          if (isOnSearchPage()) {
            reloadWithParamsDeferred(getSelectedInput());
          } else {
            updateRedirectionUrl(getSelectedInput());
          }
        }
      }, true);
    }
  );

  // ---- Suggestion click ----
  document.addEventListener("click", function (e) {
    if (!isOnSearchPage()) {
      updateRedirectionUrl(getSelectedInput());
      return;
    }

    const path = e.composedPath();
    const isSuggestion = path.some(
      (el) =>
        el?.getAttribute?.("part")?.includes("suggestion") ||
        el?.tagName?.toLowerCase() === "atomic-query-suggestion"
    );

    if (isSuggestion) {
      reloadWithParamsDeferred(getSelectedInput());
    }
  }, true);

  // add placeholder
  function setPlaceholder() {
    const searchBoxTextarea = searchBox?.shadowRoot?.querySelector('[part="textarea"]');
    if (searchBoxTextarea) {
      searchBoxTextarea.placeholder = 'Type to search';
    } else {
      requestAnimationFrame(setPlaceholder);
    }
  }
  setPlaceholder();
  // handle reset of keyword on close of the search panel (if keyword is cleared)
  const openButton = document.querySelector("[data-custom-id='primary-button-open-search']");
  if (openButton) {
    const ariaObserver = new MutationObserver(function(mutations) {
      mutations.forEach(mutation => {
        if (mutation.attributeName === "aria-expanded") {
          const isExpanded = openButton.getAttribute("aria-expanded") === "true";
          if (!isExpanded) {
            resetSearchKeyword();
          }
        }
      });
    });
    ariaObserver.observe(openButton, { attributes: true, attributeFilter: ["aria-expanded"] });
  }
  // for mobile view
  const panelObserver = new MutationObserver(function(mutations) {
  mutations.forEach(mutation => {
    mutation.removedNodes.forEach(node => {
      if (node.nodeType === 1 && (
        node.classList.contains("m-search-primary") ||
        node.querySelector?.(".m-search-primary")
      )) {
        // Only trigger on mobile view
        const isMobileView = !!document.querySelector(".m-global-mobile-nav__icons__search");
        if (isMobileView) {
          console.log("Search panel removed from DOM on mobile — checking keyword");
          resetSearchKeyword();
        }
      }
    });
  });
  });
  panelObserver.observe(document.body, { childList: true, subtree: true });

  }

function coveoSearchBoxInitialize() {
  console.log("Coveo search initialization called");
  initializeSearchControls();
  setTimeout(() => focusShadowInput(), 700); // wait for slide animation to complete
	setTimeout(() => initFocusTrap(), 700)
}

function focusShadowInput() {
  const atomicSearchBox = document.querySelector("atomic-search-box");
  const shadowInput = atomicSearchBox?.shadowRoot?.querySelector('[part="textarea"]')

  if (shadowInput) {
    shadowInput.focus();
  } else {
    console.warn("Search input not found");
  }
}
function initFocusTrap() {
  const container = document.querySelector('.m-search-primary');
  if (!container) return;

  const closeBtn = container.querySelector('[data-testid="close search"]');
  const radioButtons = [...container.querySelectorAll('input[type="radio"]')];

  const atomicSearchBox = container.querySelector('atomic-search-box');
  const shadowInput = atomicSearchBox?.shadowRoot?.querySelector('[part="textarea"]');
  const shadowSubmit = atomicSearchBox?.shadowRoot?.querySelector('[part="submit-button"]');

  const focusable = [
    closeBtn,
    ...radioButtons,
    shadowInput,
    shadowSubmit
  ].filter(Boolean);

  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  container.addEventListener('keydown', function(e) {
    if (e.key !== 'Tab') return;

    const active = e.composedPath()[0];

    if (e.shiftKey) {
      if (active === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (active === last) {
        e.preventDefault();
        first.focus();
      }
    }
  });
}

function triggerLegacyAtomicSearchSubmit(searchInterfaceId) {
  const searchBox = document.querySelector(`${searchInterfaceId} atomic-search-box`);
  if (!searchBox) {
    console.error("Atomic Search Box not found for interface:", searchInterfaceId);
    return;
  }
  if (searchBox.shadowRoot) {
    const submitButton = searchBox.shadowRoot.querySelector('button[part="submit-button"]');
    if (submitButton) {
      console.log("Clicking the Atomic submit button");
      submitButton.click();
    } else {
      console.error("Could not find submit button in shadow DOM for:", searchInterfaceId);
    }
  } else {
    console.error("Shadow DOM not accessible for search box:", searchInterfaceId);
  }
}

function initializeLegacySearchControls() {
  const searchInterface = document.querySelector("atomic-search-interface#legacy-searchbox");
  const searchBox = searchInterface ? searchInterface.querySelector("atomic-search-box") : null;
  const radioGroupContainer = document.querySelector(".m-radio-group");
  const radioInputs = document.querySelectorAll('input[type="radio"][name="f-commoncontenttype"]');


  let latestKeyword = "";

  function getCurrentSearchValue() {
    try {
      const input =
        searchBox?.shadowRoot?.querySelector('[part="textarea"]') ||
        searchBox?.shadowRoot?.querySelector("textarea") ||
        searchBox?.shadowRoot?.querySelector("input");

      return input?.value || latestKeyword || "";
    } catch (e) {
      return latestKeyword || "";
    }
  }

  if (!searchBox || !radioGroupContainer || radioInputs.length === 0) {
    console.error("Required search elements not found.");
    return;
  }

  function updateRadioButtonState(input, isChecked) {
    const label = input.closest(".styledRadioButton");
    if (!label)
      return;
    const radioLabel = label.querySelector(".radioLabel");
    if (radioLabel) {
      if (isChecked) {
        radioLabel.classList.add("checked");
      } else {
        radioLabel.classList.remove("checked");
      }
    }
  }

  function updateRedirectionUrl(selectedInput) {
    const baseUrl = getSearchBaseUrl();
    const filter = selectedInput.value;
    const keyword = encodeURIComponent(getCurrentSearchValue());
    let redirectionUrl = baseUrl;

    if (keyword && filter) {
      redirectionUrl = `${baseUrl}#q=${keyword}&${selectedInput.name}=${encodeURIComponent(filter)}`;
    } else if (keyword) {
      redirectionUrl = `${baseUrl}#q=${keyword}`;
    } else if (filter) {
      redirectionUrl = `${baseUrl}#${selectedInput.name}=${encodeURIComponent(filter)}`;
    }

    searchBox.setAttribute("redirection-url", redirectionUrl);
    console.log("Redirection URL set to:", redirectionUrl);
  }

  radioInputs.forEach((input) => {
    updateRadioButtonState(input, input.checked);
    const pagePathName = window.location.pathname;
    if (input.id == "handbooksRadio" && (pagePathName.startsWith("/handbooks") || pagePathName.startsWith("/content/handbooks"))) {
      updateRedirectionUrl(input);
    } else if (input.id == "studentsRadio" && (pagePathName.startsWith("/students") || pagePathName.startsWith("/content/students"))) {
      updateRedirectionUrl(input);
    } else if (input.checked) {
      updateRedirectionUrl(input);
    }
  });

  searchBox.addEventListener("input", function() {
    const selectedInput = document.querySelector('input[type="radio"][name="f-commoncontenttype"]:checked') || radioInputs[0];
    latestKeyword = getCurrentSearchValue();
    updateRedirectionUrl(selectedInput);
  });

  radioInputs.forEach((input) => {
    input.addEventListener("change", function() {
      radioInputs.forEach((otherInput) => {
        updateRadioButtonState(otherInput, otherInput === input);
      });
      updateRedirectionUrl(input);
    });
  });

}

function coveoLegacySearchBoxInitialize() {
  console.log("Coveo legacy search initialization called");
  initializeLegacySearchControls();
}
console.log("[Coveo] Loading script version: coveo-unisyd-aem-ver-0045-prod");
var initialSearch = true;
var SEARCH_HUBS = {
  "library-search": {
    apiKey: "xx644e23b8-0baa-49aa-a70a-bea7ce90440b",
    translations: {
      "search": "Search the Library website",
      "sort-and-filter": "Filters",
      "no-results-for": "There are no results matching your search {{query}}"
      // Add library-specific translations if needed
    },
    showTrending: true
    // Flag to show trending searches
  },
  "courses-search": {
    apiKey: "xx3124d44f-146e-43cd-a3d5-af6a42a52f55",
    translations: {
      "search": "Search for a course or degree",
      "showing-results-of": "Showing {{first}} of {{total}} results",
      "showing-results-of_other": "Showing {{first}}-{{last}} of {{total}} results",
      "showing-results-of-with-query": "Showing {{first}} of {{total}} result for {{query}}",
      "showing-results-of-with-query_other": "Showing {{first}}-{{last}} of {{total}} results for {{query}}",
      "no-results-for": "There are no results for {{query}}",
      "clear": "Clear"
    },
    showTrending: true
    // Flag to show trending searches
  },
  "corporate-search": {
    apiKey: "xx8b233a7f-74ba-47eb-94f3-a8183a83af6b",
    translations: {
      "search": "What are you interested in?",
      "sort-and-filter": "Sort & Filter",
      "no-results-for": "We couldn't find {{query}}"
    }
  },
  "intranet-search": {
    apiKey: "xxcd30237d-bcc8-40eb-b62b-b795a9341e77",
    translations: {
      "sort-by": "Order results by",
      "showing-results-of": "{{total}} results found",
      "showing-results-of_other": "{{total}} results found",
      "showing-results-of-with-query": "{{total}} result for {{query}}",
      "showing-results-of-with-query_other": "{{total}} results found for {{query}}",
      "no-results-for": "We couldn't find any results for {{query}}. You can try changing the wording of your search terms or adding some more terms."
    }
  },
  "uos-search": {
    apiKey: "xxf8204f8d-c2dc-4c5e-befb-83168d339bfd",
    translations: {
      "search": "Search unit name, unit code or keywords",
      "sort-by": "Order results by",
      "showing-results-of": "There are {{total}} results",
      "showing-results-of_other": "There are {{total}} results",
      "showing-results-of-with-query": "There are {{total}} result for {{query}}",
      "showing-results-of-with-query_other": "There are {{total}} results for {{query}}",
      "load-more-results": "Show more",
      "results-per-page": "Results per page:"
      // Add intranet-specific translations if needed
    }
  },
  "searchbox": {
    apiKey: "xx8b233a7f-74ba-47eb-94f3-a8183a83af6b",
    translations: {
      "search": ""
      // Add intranet-specific translations if needed
    }
  },
  "legacy-searchbox": {
    apiKey: "xx8b233a7f-74ba-47eb-94f3-a8183a83af6b",
    translations: {
      "search": ""
      // Add intranet-specific translations if needed
    }
  },
  "default": {
    apiKey: "xx8b233a7f-74ba-47eb-94f3-a8183a83af6b",
    translations: {
      "search": ""
      // Add intranet-specific translations if needed
    }
  }
};
function updateAdobeEvent(eventName, newSearchResults) {
  if (!window.adobeDataLayer || !Array.isArray(window.adobeDataLayer)) {
    console.error("adobeDataLayer is not available or not an array.");
    return;
  }
  const lastEvent = window.adobeDataLayer[window.adobeDataLayer.length - 1];
  if (lastEvent?.event !== eventName) {
    return;
  }
  if (lastEvent?.digitalData?.search) {
    lastEvent.digitalData.search.searchResults = newSearchResults;
  } else {
    console.warn(`Last event "${eventName}" does not contain a digitalData.search object.`);
  }
}
var inCooldown = {};
function handleAdobeEvent(eventName, payload) {
  if (inCooldown && inCooldown[eventName])
    return;
  setTimeout(() => {
    inCooldown[eventName] = false;
  }, 250);
  inCooldown[eventName] = true;
  console.log("[Atomic \u2192 Adobe Data Layer]", {
    event: payload.actionCause,
    payload
  });
  const data = {
    event: payload.actionCause,
    payload
  };
  if (window.pushToAdobe) {
    window.pushToAdobe(data);
  } else if (window.adobeDataLayer) {
    window.adobeDataLayer.push(data);
  } else {
    console.warn("Adobe Data Layer not found");
  }
}
function applyPromiseFix() {
  try {
    const properAllSettled = function(promises) {
      return Promise.all(promises.map((promise) => Promise.resolve(promise).then((value) => ({ status: "fulfilled", value }), (reason) => ({ status: "rejected", reason }))));
    };
    Promise.allSettled = properAllSettled;
    const verificationPromise = Promise.allSettled([Promise.resolve("test")]);
    return verificationPromise.then((results) => {
      if (results[0] && results[0].status === "fulfilled") {
        return true;
      } else {
        console.warn("[AEM-Coveo Fix] Promise.allSettled fix did not work as expected");
        return false;
      }
    }).catch((err3) => {
      console.error("[AEM-Coveo Fix] Verification error:", err3);
      return false;
    });
  } catch (e7) {
    console.error("[AEM-Coveo Fix] Error applying Promise fix:", e7);
    return Promise.resolve(false);
  }
}
async function initSearchInterface(searchInterface) {
  try {
    if (!searchInterface) {
      throw new Error("Search interface not found");
    }
    const searchHubValue = searchInterface.getAttribute("id") || "default";
    const currentHub = SEARCH_HUBS[searchHubValue] || SEARCH_HUBS["default"];
    const accessToken = currentHub.apiKey;
    if (!accessToken) {
      throw new Error("API Key not found for search interface");
    }
    const organizationId = "universityofsydneyproduction10somjans";
    const initOptions = {
      accessToken,
      organizationId,
      analytics: {
        analyticsMode: "legacy"
      }
    };
    const analyticsClientMiddleware = (eventName, payload) => {
      if (searchHubValue === "corporate-search" || searchHubValue === "intranet-search" || searchHubValue === "courses-search") {
        window.adobeDataLayer = window.adobeDataLayer || [];
        handleAdobeEvent(eventName, payload);
      }
      return payload;
    };

    let isYearSelected = false;
    function deepQueryAll(root, selector) {
      const results = [];
      function traverse(node) {
        if (node.shadowRoot) traverse(node.shadowRoot);
        node.querySelectorAll("*").forEach(child => {
          if (child.matches?.(selector)) results.push(child);
          if (child.shadowRoot) traverse(child.shadowRoot);
        });
      }
      traverse(root);
      return results;
    }

    initOptions.analytics.analyticsClientMiddleware = analyticsClientMiddleware;
    initOptions.search = {
      searchHub: searchHubValue,
      preprocessSearchResponseMiddleware: async (response) => {
        try {
          updateAdobeEvent("searchKeyword", response.body.totalCountFiltered);
          updateAdobeEvent("facetFilterClick", response.body.totalCountFiltered);
          return response;
        } catch (err3) {
          console.error(err3);
          return response;
        }
      }
    };
    initOptions.preprocessRequest = (request, clientOrigin, metadata) => {
      if (metadata?.method === "search" && clientOrigin === "searchApiFetch") {
        if (!request.body || typeof request.body !== "string")
          return request;
        const body = JSON.parse(request.body);
        body.facetOptions = {
          "enableIndexFacetOrdering": false,
          "freezeFacetOrder": true
        };
        if (body.searchHub == "courses-search") {
          if (body.facets && Array.isArray(body.facets)) {
            body.facets.forEach((facet) => {
              const hasSelectedValues = facet.currentValues && facet.currentValues.some((value) => value.state === "selected");
              if (facet.customSort && Array.isArray(facet.customSort)) {
                const currentValueMap = new Map((facet.currentValues || []).map((cv) => [cv.value, cv]));
                const missingValues = facet.customSort.filter((sortValue) => !currentValueMap.has(sortValue));
                if (missingValues.length > 0) {
                  facet.currentValues = facet.currentValues || [];
                  missingValues.forEach((missingValue) => {
                    facet.currentValues.push({
                      value: missingValue,
                      state: "idle"
                    });
                  });
                }
              }
              if (initialSearch && facet.customSort && Array.isArray(facet.customSort)) {
                facet.freezeCurrentValues = true;
                const selectedValues = new Set((facet.currentValues || []).filter((v) => v.state === "selected").map((v) => v.value));
                facet.currentValues = facet.customSort.map((value) => ({
                  value,
                  state: selectedValues.has(value) ? "selected" : "idle"
                }));
              } else if (hasSelectedValues && !initialSearch) {
                facet.freezeCurrentValues = true;
              }
            });
          }
          if (initialSearch) {
            initialSearch = false;
          }
          const qualificationData = localStorage.getItem("courseQualifications") ? localStorage.getItem("courseQualifications") : "";
          let dictionaryFieldData = "";
          let dictionaryContextDomesticInternational = "domestic";
          let dictionaryContextYear = "";
          searchInterface.querySelector(".subject-area-facet-notice").hidden = true;
          searchInterface.querySelector("#qual-facet").hidden = false;
          const contentTypeFacet = body.facets.find((o) => o.field === "commoncontenttype").currentValues;
          let facetSelectedCount = 0;
          contentTypeFacet.forEach((facet) => {
            if (facet["state"] == "selected") {
              facetSelectedCount++;
            }
            if (facet["value"] == "Subject Areas" && facet["state"] == "selected") {
              searchInterface.querySelector(".subject-area-facet-notice").hidden = false;
              searchInterface.querySelector("#qual-facet").hidden = true;
            }
          });
          if (facetSelectedCount === 0) {
            console.log("no facet selected");
            contentTypeFacet.forEach((facet) => {
              if (facet["value"] == "Courses") {
                facet["state"] = "selected";
              }
            });
            const currentHash = window.location.hash;
            if (!currentHash.includes("f-courses_search_type=")) {
              const separator = currentHash && currentHash !== "#" ? "&" : "";
              const newHash = currentHash === "" ? "#" : currentHash;
              window.location.hash = newHash + separator + "f-courses_search_type=Courses";
            }
          }
          const startYearFacet = body.facets.find((o) => o.field === "usyd_courses_startyear")?.currentValues;
          const domesticInternationalFacet = body.facets.find((o) => o.field === "usyd_courses_citizenship")?.currentValues;
          if (domesticInternationalFacet && domesticInternationalFacet.length) {
            domesticInternationalFacet.forEach((facet) => {
              if (facet["state"] == "selected") {
                dictionaryContextDomesticInternational = facet["value"];
              }
            });
          }
          if (startYearFacet && startYearFacet.length) {
            startYearFacet.forEach((facet) => {
              if (facet["state"] == "selected") {
                dictionaryContextYear = facet["value"];
              }
            });
          }

          isYearSelected = startYearFacet &&
          startYearFacet.some((facet) => facet["state"] === "selected");

          if(isYearSelected){
            dictionaryFieldData += dictionaryContextDomesticInternational + "_";
            dictionaryFieldData += qualificationData.replace(/-/g, "_").toLowerCase();
            dictionaryFieldData += "_" + dictionaryContextYear;
            body.dictionaryFieldContext = { "usyd_courses_entryscore": dictionaryFieldData };
            // to change the color of error message to grey
            let retries = 0;
            const maxRetries = 5;
            const tryApplyStyle = () => {
                const elements = deepQueryAll(document, "atomic-result-html[field='usyd_courses_entryscore']");
                if (elements.length > 0) {
                    elements.forEach(el => {
                        const span = el.querySelector("atomic-html")?.shadowRoot?.querySelector("span");
                        const spanText = span?.textContent?.trim();
                        if (!span) return;
                        if (spanText?.toLowerCase().includes("not available")) {
                            span.style.color = "#B0B0B0";
                        } else {
                            span.style.color = "";
                        }
                    });
                } else if (retries < maxRetries) {
                    retries++;
                    setTimeout(tryApplyStyle, 300);
                }
            };

			      setTimeout(tryApplyStyle, 300);
          }
          else{
              body.dictionaryFieldContext = {"usyd_courses_entryscore": " "};
          }

          }
        if (body.searchHub == "uos-search") {
          const noResultsElement = searchInterface.querySelector("atomic-no-results");
          const validationElement = searchInterface.querySelector(".validation-message");
          if (body.q == "") {
            body.numberOfResults = 0;
            noResultsElement.classList.add("hidden");
            if (initialSearch) {
              validationElement.classList.add("hidden");
            } else {
              validationElement.classList.remove("hidden");
            }
            initialSearch = false;
            searchInterface.classList.add("hide-no-results");
          } else {
            noResultsElement.classList.remove("hidden");
            validationElement.classList.add("hidden");
            searchInterface.classList.remove("hide-no-results");
          }
        }
        if (body.searchHub == "corporate-search") {
          const noResultsElement = searchInterface.querySelector("atomic-no-results");
          const validationElement = searchInterface.querySelector(".validation-message");
          if (body.q == "") {
            body.numberOfResults = 0;
            noResultsElement.classList.add("hidden");
            if (initialSearch) {
              validationElement.classList.add("hidden");
            } else {
              validationElement.classList.remove("hidden");
            }
            initialSearch = false;
            searchInterface.classList.add("hide-no-results");
          } else {
            noResultsElement.classList.remove("hidden");
            validationElement.classList.add("hidden");
            searchInterface.classList.remove("hide-no-results");
          }
        }
        request.body = JSON.stringify(body);
      }
      return request;
    };
    initOptions.search = {
      preprocessSearchResponseMiddleware: (response) => {
        if (response.body.pipeline == "Intranet Search") {
          for (let i = 0; i < response.body.facets.length; i++) {
            const facetData = response.body.facets[i].values;
            let selectedFacetValues = [];
            let deselectedFacetValues = [];
            facetData.forEach((facetValue) => {
              if (facetValue.state == "selected") {
                selectedFacetValues.push(facetValue);
              } else {
                deselectedFacetValues.push(facetValue);
              }
            });
            response.body.facets[i].values = selectedFacetValues.concat(deselectedFacetValues);
          }
        }
        if (response.body.pipeline == "Courses Search") {
          for (let i = 0; i < response.body.facets.length; i++) {
            const facetData = response.body.facets[i].values;
            let staticFacetValues = [];
            let selectedValues = [];
            switch (response.body.facets[i].field) {
              case "commoncontenttype":
                facetData.forEach((facetValue) => {
                  if (facetValue.state == "selected") {
                    selectedValues[facetValue.value] = facetValue.numberOfResults;
                  }
                });
                staticFacetValues = [
                  {
                    "value": "Courses",
                    "state": "idle",
                    "numberOfResults": 0,
                    "order": 0
                  },
                  {
                    "value": "Subject Areas",
                    "state": "idle",
                    "numberOfResults": 0,
                    "order": 1
                  }
                ];
                staticFacetValues.forEach((facetValue) => {
                  if (selectedValues[facetValue.value]) {
                    facetValue.state = "selected";
                    facetValue.numberOfResults = selectedValues[facetValue.value];
                  }
                });
                response.body.facets[i].values = staticFacetValues;
                break;
              default:
                response.body.facets[i].values = facetData.filter((facetValue) => {
                  return facetValue.numberOfResults > 0;
                });
                break;
            }
          }
        }
        response.body.results.forEach((result) => {
          return result;
        });
        return response;
      },
      preprocessFacetSearchResponseMiddleware: (response) => response,
      preprocessQuerySuggestResponseMiddleware: (response) => response
    };
    await searchInterface.initialize(initOptions);
    const headlessEngine = searchInterface.engine;
    window.coveoHeadlessEngine = headlessEngine;
    if (currentHub.translations && Object.keys(currentHub.translations).length > 0) {
      searchInterface.i18n.addResourceBundle("en", "translation", currentHub.translations, true, true);
    }
    return currentHub;
  } catch (error) {
    console.error("Failed to initialize search interface:", error);
    throw error;
  }
}
async function initSearchBox(legacy = false) {
  try {
    const selector = legacy ? "atomic-search-interface#legacy-searchbox" : "atomic-search-interface#searchbox";
    const searchInterface = document.querySelector(selector);
    await initSearchInterface(searchInterface);
  } catch (error) {
    console.error(`Failed to initialize ${legacy ? "legacy " : ""}searchbox:`, error);
  }
}
async function initMainSearch() {
  try {
    const searchInterface = document.querySelector("atomic-search-interface:not(#legacy-searchbox):not(#searchbox)");
    const currentHub = await initSearchInterface(searchInterface);
    searchInterface.i18n.addResourceBundle("en", "caption-usyd_courses_studylevel", {
      pc: "Postgraduate",
      uc: "Undergraduate",
      pr: "Research"
    });
    searchInterface.i18n.addResourceBundle("en", "caption-usyd_courses_pathwaytype", {
      major: "Major",
      minor: "Minor",
      progrm: "Program",
      hons: "Honours",
      spec: "Specialisation",
      advncd: "Advanced coursework"
    });
    searchInterface.i18n.addResourceBundle("en", "caption-usyd_courses_fieldofstudy", {
      "architecture-design-and-planning": "Architecture, Design and Planning",
      "arts-and-social-sciences": "Arts and Social Sciences",
      "business": "Business",
      "education-and-social-work": "Education and Social Work",
      "law": "Law",
      "music": "Music",
      "medicine-and-health": "Medicine and Health",
      "science": "Science",
      "economics": "Economics",
      "engineering-and-information-technology": "Engineering and Computer Science"
    });
    searchInterface.i18n.addResourceBundle("en", "caption-usyd_courses_availability", {
      "full time": "Full-time",
      "full-time": "Full-time",
      "part-time": "Part-time"
    });
    searchInterface.i18n.addResourceBundle("en", "caption-usyd_courses_citizenship", {
      "Domestic": "Domestic",
      "INT": "International"
    });
    searchInterface.executeFirstSearch();
    setupTrendingSearches(currentHub);
    if (searchInterface.getAttribute("id") === "courses-search") {
      modifyRefineModal();
    }
  } catch (error) {
    console.error("Error in main function:", error);
  }
}
function setupTrendingSearches(currentHub) {
  const searchBox = document.querySelector("atomic-search-box");
  if (!searchBox)
    return;
  const config = { attributes: true, childList: true, subtree: true };
  const callback = (mutationList, _observer) => {
    for (const mutation of mutationList) {
      if (mutation.type === "childList" || mutation.type === "attributes") {
        updateTrendingLabel(searchBox, currentHub);
      }
    }
  };
  searchBoxObserver = new MutationObserver(callback);
  searchBoxObserver.observe(searchBox, config);
}
function updateTrendingLabel(searchBox, currentHub) {
  const wrapper = searchBox.shadowRoot?.querySelector('[part="wrapper"]');
  if (!wrapper)
    return;
  const existingLabel = wrapper.querySelector('[part="trending-label"]');
  const recentItems = wrapper.querySelectorAll('button[part*="recent-query-item"]');
  const querySuggestions = wrapper.querySelectorAll('button[part*="query-suggestion-item"]');
  const suggestionWrapper = wrapper.querySelector('[part="suggestions suggestions-left"]');
  let buttonTabIndex = 0;
  let trendingOrder = "0";
  recentItems.forEach((element) => {
    buttonTabIndex++;
    element.style.order = buttonTabIndex.toString();
  });
  buttonTabIndex++;
  trendingOrder = buttonTabIndex.toString();
  querySuggestions.forEach((element) => {
    buttonTabIndex++;
    element.style.order = buttonTabIndex.toString();
  });
  if (querySuggestions.length && currentHub.showTrending && !existingLabel) {
    const trending = createTrendingLabel();
    trending.style.order = trendingOrder;
    suggestionWrapper?.appendChild(trending);
  } else if (querySuggestions.length && currentHub.showTrending && existingLabel) {
    existingLabel.style.order = trendingOrder;
  } else if (!querySuggestions.length && currentHub.showTrending && existingLabel) {
    existingLabel.remove();
  }
}
function createTrendingLabel() {
  const trending = document.createElement("div");
  trending.setAttribute("part", "trending-label");
  trending.setAttribute("aria-hidden", "true");
  trending.className = "flex px-4 min-h-[40px] items-center text-left text-neutral-dark bg-transparent cursor-default";
  trending.style.pointerEvents = "none";
  trending.tabIndex = -1;
  const container = document.createElement("div");
  container.className = "flex items-center break-all text-left";
  const label = document.createElement("span");
  label.className = "line-clamp-2 break-all";
  label.textContent = "Suggested searches";
  container.appendChild(label);
  trending.appendChild(container);
  return trending;
}
async function waitForChildElement(parentNode, childSelector, timeout = 5e3) {
  const existing = parentNode.querySelector(childSelector);
  if (existing) {
    return existing;
  }
  return await new Promise((resolve) => {
    const observer = new MutationObserver(() => {
      const child = parentNode.querySelector(childSelector);
      if (child) {
        observer.disconnect();
        resolve(child);
      }
    });
    observer.observe(parentNode, {
      childList: true,
      subtree: true
    });
    if (timeout > 0) {
      setTimeout(() => {
        observer.disconnect();
        resolve(null);
      }, timeout);
    }
  });
}
async function modifyRefineModal() {
  const mainSection = document.querySelector("atomic-layout-section[section='main']");
  if (!mainSection)
    return;
  const refineModal = await waitForChildElement(mainSection, "atomic-refine-modal");
  if (!refineModal || !refineModal.shadowRoot)
    return;
  const refineModalShadowRoot = refineModal.shadowRoot;
  const clearFiltersSection = await waitForChildElement(refineModalShadowRoot, "div[part='filter-section']");
  const footerContentContainer = await waitForChildElement(refineModalShadowRoot, "div[part='footer-content']");
  const viewResultsButton = await waitForChildElement(refineModalShadowRoot, "button[part='footer-button']");
  if (!clearFiltersSection || !footerContentContainer || !viewResultsButton)
    return;
  clearFiltersSection.setAttribute("class", "flex");
  const footerContentButtonsContainer = document.createElement("div");
  footerContentButtonsContainer.setAttribute("part", "footer-content-split");
  footerContentContainer.prepend(footerContentButtonsContainer);
  footerContentButtonsContainer.prepend(viewResultsButton);
  footerContentButtonsContainer.prepend(clearFiltersSection);
}
var searchBoxObserver = null;
var bannerInitializedFlag = false;
function cleanup() {
  if (searchBoxObserver) {
    searchBoxObserver.disconnect();
    searchBoxObserver = null;
  }
  document.removeEventListener("DOMContentLoaded", coveoSearchInitialize);
}
async function coveoSearchInitialize() {
  try {
    cleanup();
    const isLegacySearchBoxPage = document.querySelector("atomic-search-interface#legacy-searchbox") !== null;
    const isSearchBoxPage = document.querySelector("atomic-search-interface#searchbox") !== null;
    const isSearchInterface = document.querySelector("atomic-search-interface:not(#legacy-searchbox):not(#searchbox)");
    await applyPromiseFix();
    await waitForAtomic();
    if (isLegacySearchBoxPage || isSearchBoxPage) {
      await initSearchBox(isLegacySearchBoxPage);
    }
    if (isSearchInterface) {
      await initMainSearch();
      const coursesSearch = document.querySelector("atomic-search-interface#courses-search");
      if (coursesSearch) {
        const targ = document.getElementById("qual-facet");
        if (document.location.hash && document.location.hash.includes("subjectareas")) {
          if (targ) {
            targ.classList.add("hide");
          }
        }
        document.querySelectorAll("[tab-id]").forEach((elem) => {
          elem.addEventListener("click", () => {
            if (elem.getAttribute("tab-id") == "courses") {
              if (targ) {
                targ.classList.remove("hide");
              }
            } else if (elem.getAttribute("tab-id") == "subjectareas") {
              if (targ) {
                targ.classList.add("hide");
              }
            }
          });
        });
      }
    }
  } catch (err3) {
    console.error("Error during initialization:", err3);
  }
}
document.addEventListener("CoveoSearchBannerLoaded", async () => {
  const searchbox = document.querySelector("atomic-search-interface#searchbox");
  if (!searchbox) {
    bannerInitializedFlag = false;
  }
  if (bannerInitializedFlag) {
    return;
  }
  try {
    bannerInitializedFlag = true;
    const waitForSearchboxAndInitialize = async (attempts = 3) => {
      for (let attempt = 1; attempt <= attempts; attempt++) {
        const delay = 100 * Math.pow(2, attempt - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
        const searchbox2 = document.querySelector("atomic-search-interface#searchbox");
        if (searchbox2) {
          try {
            await coveoSearchInitialize();
            coveoSearchBoxInitialize();
            return true;
          } catch (error) {
            console.error("Error during Coveo search initialization:", error);
            return false;
          }
        }
        if (attempt < attempts) {
          console.warn(`CoveoSearchBannerLoaded: search box not found on attempt ${attempt}, retrying...`);
        } else {
          console.error("Coveo search box not found after all retry attempts");
        }
      }
      return false;
    };
    try {
      const initialized = await waitForSearchboxAndInitialize();
      if (!initialized) {
        console.warn("Failed to initialize banner search box");
        bannerInitializedFlag = false;
      }
    } catch (innerErr) {
      console.error("Error in waitForSearchboxAndInitialize:", innerErr);
    }
  } catch (err3) {
    console.error("Error during Coveo banner search initialization:", err3);
    bannerInitializedFlag = false;
  }
});
function resetCoveoSearchBanner() {
  bannerInitializedFlag = false;
  cleanup();
}
document.addEventListener("CoveoSearchBannerReset", () => {
  resetCoveoSearchBanner();
});
document.addEventListener("DOMContentLoaded", () => {
  const legacySearchBox = document.querySelector("atomic-search-interface#legacy-searchbox");
  const searchInterface = document.querySelector("atomic-search-interface:not(#legacy-searchbox):not(#searchbox)");
  if (searchInterface || legacySearchBox) {
    coveoSearchInitialize();
    if (legacySearchBox) {
      coveoLegacySearchBoxInitialize();
    }
  }
  const coursesSearch = document.querySelector("atomic-search-interface#courses-search");
  if (coursesSearch) {
    const targ = document.getElementById("qual-facet");
    if (document.location.hash && document.location.hash.includes("subjectareas")) {
      if (targ) {
        targ.classList.add("hide");
      }
    }
    document.querySelectorAll("[tab-id]").forEach((elem) => {
      elem.addEventListener("click", () => {
        if (elem.getAttribute("tab-id") == "courses") {
          if (targ) {
            targ.classList.remove("hide");
          }
        } else if (elem.getAttribute("tab-id") == "subjectareas") {
          if (targ) {
            targ.classList.add("hide");
          }
        }
      });
    });
  }
});
var defineCustomElements = (opts) => {
  if (typeof customElements !== "undefined") {
    [
      ContenttypeBadge,
      DirectionsLink2,
      FacetButtonsController2,
      QualificationsLink2,
      ResultFieldLink2,
      ResultUrl2,
      UnisydMap2,
      UnisydPager2,
      UnisydTab2
    ].forEach((cmp) => {
      if (!customElements.get(cmp.is)) {
        customElements.define(cmp.is, cmp, opts);
      }
    });
  }
};
defineCustomElements();
export {
  coveoSearchInitialize,
  defineCustomElements,
  getAssetPath,
  render,
  resetCoveoSearchBanner,
  setAssetPath,
  setNonce,
  setPlatformOptions
};
/*! @license DOMPurify 3.2.4 | (c) Cure53 and other contributors | Released under the Apache license 2.0 and Mozilla Public License 2.0 | github.com/cure53/DOMPurify/blob/3.2.4/LICENSE */
/**
 * @license
 *
 * Copyright 2025 Coveo Solutions Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

