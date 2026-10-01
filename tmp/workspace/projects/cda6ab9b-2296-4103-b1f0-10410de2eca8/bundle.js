const ve = globalThis, pt = ve.ShadowRoot && (ve.ShadyCSS === void 0 || ve.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Tt = /* @__PURE__ */ Symbol(), Ot = /* @__PURE__ */ new WeakMap();
let ds = class {
  constructor(e, s, r) {
    if (this._$cssResult$ = !0, r !== Tt) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = e, this.t = s;
  }
  get styleSheet() {
    let e = this.o;
    const s = this.t;
    if (pt && e === void 0) {
      const r = s !== void 0 && s.length === 1;
      r && (e = Ot.get(s)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), r && Ot.set(s, e));
    }
    return e;
  }
  toString() {
    return this.cssText;
  }
};
const ti = (t) => new ds(typeof t == "string" ? t : t + "", void 0, Tt), us = (t, ...e) => {
  const s = t.length === 1 ? t[0] : e.reduce((r, a, n) => r + ((c) => {
    if (c._$cssResult$ === !0) return c.cssText;
    if (typeof c == "number") return c;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + c + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(a) + t[n + 1], t[0]);
  return new ds(s, t, Tt);
}, si = (t, e) => {
  if (pt) t.adoptedStyleSheets = e.map((s) => s instanceof CSSStyleSheet ? s : s.styleSheet);
  else for (const s of e) {
    const r = document.createElement("style"), a = ve.litNonce;
    a !== void 0 && r.setAttribute("nonce", a), r.textContent = s.cssText, t.appendChild(r);
  }
}, Lt = pt ? (t) => t : (t) => t instanceof CSSStyleSheet ? ((e) => {
  let s = "";
  for (const r of e.cssRules) s += r.cssText;
  return ti(s);
})(t) : t;
const { is: ii, defineProperty: ri, getOwnPropertyDescriptor: ai, getOwnPropertyNames: ni, getOwnPropertySymbols: oi, getPrototypeOf: Ai } = Object, $e = globalThis, wt = $e.trustedTypes, ci = wt ? wt.emptyScript : "", li = $e.reactiveElementPolyfillSupport, de = (t, e) => t, dt = { toAttribute(t, e) {
  switch (e) {
    case Boolean:
      t = t ? ci : null;
      break;
    case Object:
    case Array:
      t = t == null ? t : JSON.stringify(t);
  }
  return t;
}, fromAttribute(t, e) {
  let s = t;
  switch (e) {
    case Boolean:
      s = t !== null;
      break;
    case Number:
      s = t === null ? null : Number(t);
      break;
    case Object:
    case Array:
      try {
        s = JSON.parse(t);
      } catch {
        s = null;
      }
  }
  return s;
} }, Es = (t, e) => !ii(t, e), kt = { attribute: !0, type: String, converter: dt, reflect: !1, useDefault: !1, hasChanged: Es };
Symbol.metadata ??= /* @__PURE__ */ Symbol("metadata"), $e.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let z = class extends HTMLElement {
  static addInitializer(e) {
    this._$Ei(), (this.l ??= []).push(e);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(e, s = kt) {
    if (s.state && (s.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((s = Object.create(s)).wrapped = !0), this.elementProperties.set(e, s), !s.noAccessor) {
      const r = /* @__PURE__ */ Symbol(), a = this.getPropertyDescriptor(e, r, s);
      a !== void 0 && ri(this.prototype, e, a);
    }
  }
  static getPropertyDescriptor(e, s, r) {
    const { get: a, set: n } = ai(this.prototype, e) ?? { get() {
      return this[s];
    }, set(c) {
      this[s] = c;
    } };
    return { get: a, set(c) {
      const h = a?.call(this);
      n?.call(this, c), this.requestUpdate(e, h, r);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(e) {
    return this.elementProperties.get(e) ?? kt;
  }
  static _$Ei() {
    if (this.hasOwnProperty(de("elementProperties"))) return;
    const e = Ai(this);
    e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(de("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(de("properties"))) {
      const s = this.properties, r = [...ni(s), ...oi(s)];
      for (const a of r) this.createProperty(a, s[a]);
    }
    const e = this[Symbol.metadata];
    if (e !== null) {
      const s = litPropertyMetadata.get(e);
      if (s !== void 0) for (const [r, a] of s) this.elementProperties.set(r, a);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [s, r] of this.elementProperties) {
      const a = this._$Eu(s, r);
      a !== void 0 && this._$Eh.set(a, s);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(e) {
    const s = [];
    if (Array.isArray(e)) {
      const r = new Set(e.flat(1 / 0).reverse());
      for (const a of r) s.unshift(Lt(a));
    } else e !== void 0 && s.push(Lt(e));
    return s;
  }
  static _$Eu(e, s) {
    const r = s.attribute;
    return r === !1 ? void 0 : typeof r == "string" ? r : typeof e == "string" ? e.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
  }
  addController(e) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
  }
  removeController(e) {
    this._$EO?.delete(e);
  }
  _$E_() {
    const e = /* @__PURE__ */ new Map(), s = this.constructor.elementProperties;
    for (const r of s.keys()) this.hasOwnProperty(r) && (e.set(r, this[r]), delete this[r]);
    e.size > 0 && (this._$Ep = e);
  }
  createRenderRoot() {
    const e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return si(e, this.constructor.elementStyles), e;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
  }
  enableUpdating(e) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((e) => e.hostDisconnected?.());
  }
  attributeChangedCallback(e, s, r) {
    this._$AK(e, r);
  }
  _$ET(e, s) {
    const r = this.constructor.elementProperties.get(e), a = this.constructor._$Eu(e, r);
    if (a !== void 0 && r.reflect === !0) {
      const n = (r.converter?.toAttribute !== void 0 ? r.converter : dt).toAttribute(s, r.type);
      this._$Em = e, n == null ? this.removeAttribute(a) : this.setAttribute(a, n), this._$Em = null;
    }
  }
  _$AK(e, s) {
    const r = this.constructor, a = r._$Eh.get(e);
    if (a !== void 0 && this._$Em !== a) {
      const n = r.getPropertyOptions(a), c = typeof n.converter == "function" ? { fromAttribute: n.converter } : n.converter?.fromAttribute !== void 0 ? n.converter : dt;
      this._$Em = a;
      const h = c.fromAttribute(s, n.type);
      this[a] = h ?? this._$Ej?.get(a) ?? h, this._$Em = null;
    }
  }
  requestUpdate(e, s, r, a = !1, n) {
    if (e !== void 0) {
      const c = this.constructor;
      if (a === !1 && (n = this[e]), r ??= c.getPropertyOptions(e), !((r.hasChanged ?? Es)(n, s) || r.useDefault && r.reflect && n === this._$Ej?.get(e) && !this.hasAttribute(c._$Eu(e, r)))) return;
      this.C(e, s, r);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(e, s, { useDefault: r, reflect: a, wrapped: n }, c) {
    r && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, c ?? s ?? this[e]), n !== !0 || c !== void 0) || (this._$AL.has(e) || (this.hasUpdated || r || (s = void 0), this._$AL.set(e, s)), a === !0 && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (s) {
      Promise.reject(s);
    }
    const e = this.scheduleUpdate();
    return e != null && await e, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [a, n] of this._$Ep) this[a] = n;
        this._$Ep = void 0;
      }
      const r = this.constructor.elementProperties;
      if (r.size > 0) for (const [a, n] of r) {
        const { wrapped: c } = n, h = this[a];
        c !== !0 || this._$AL.has(a) || h === void 0 || this.C(a, void 0, n, h);
      }
    }
    let e = !1;
    const s = this._$AL;
    try {
      e = this.shouldUpdate(s), e ? (this.willUpdate(s), this._$EO?.forEach((r) => r.hostUpdate?.()), this.update(s)) : this._$EM();
    } catch (r) {
      throw e = !1, this._$EM(), r;
    }
    e && this._$AE(s);
  }
  willUpdate(e) {
  }
  _$AE(e) {
    this._$EO?.forEach((s) => s.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(e) {
    return !0;
  }
  update(e) {
    this._$Eq &&= this._$Eq.forEach((s) => this._$ET(s, this[s])), this._$EM();
  }
  updated(e) {
  }
  firstUpdated(e) {
  }
};
z.elementStyles = [], z.shadowRootOptions = { mode: "open" }, z[de("elementProperties")] = /* @__PURE__ */ new Map(), z[de("finalized")] = /* @__PURE__ */ new Map(), li?.({ ReactiveElement: z }), ($e.reactiveElementVersions ??= []).push("2.1.2");
const ft = globalThis, Ft = (t) => t, Pe = ft.trustedTypes, vt = Pe ? Pe.createPolicy("lit-html", { createHTML: (t) => t }) : void 0, gs = "$lit$", W = `lit$${Math.random().toFixed(9).slice(2)}$`, _s = "?" + W, hi = `<${_s}>`, X = document, Te = () => X.createComment(""), fe = (t) => t === null || typeof t != "object" && typeof t != "function", It = Array.isArray, di = (t) => It(t) || typeof t?.[Symbol.iterator] == "function", it = `[ 	
\f\r]`, ne = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, Mt = /-->/g, xt = />/g, $ = RegExp(`>|${it}(?:([^\\s"'>=/]+)(${it}*=${it}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), Pt = /'/g, Ht = /"/g, ms = /^(?:script|style|textarea|title)$/i, ui = (t) => (e, ...s) => ({ _$litType$: t, strings: e, values: s }), m = ui(1), ee = /* @__PURE__ */ Symbol.for("lit-noChange"), R = /* @__PURE__ */ Symbol.for("lit-nothing"), Ut = /* @__PURE__ */ new WeakMap(), J = X.createTreeWalker(X, 129);
function ps(t, e) {
  if (!It(t) || !t.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return vt !== void 0 ? vt.createHTML(e) : e;
}
const Ei = (t, e) => {
  const s = t.length - 1, r = [];
  let a, n = e === 2 ? "<svg>" : e === 3 ? "<math>" : "", c = ne;
  for (let h = 0; h < s; h++) {
    const E = t[h];
    let u, _, f = -1, I = 0;
    for (; I < E.length && (c.lastIndex = I, _ = c.exec(E), _ !== null); ) I = c.lastIndex, c === ne ? _[1] === "!--" ? c = Mt : _[1] !== void 0 ? c = xt : _[2] !== void 0 ? (ms.test(_[2]) && (a = RegExp("</" + _[2], "g")), c = $) : _[3] !== void 0 && (c = $) : c === $ ? _[0] === ">" ? (c = a ?? ne, f = -1) : _[1] === void 0 ? f = -2 : (f = c.lastIndex - _[2].length, u = _[1], c = _[3] === void 0 ? $ : _[3] === '"' ? Ht : Pt) : c === Ht || c === Pt ? c = $ : c === Mt || c === xt ? c = ne : (c = $, a = void 0);
    const D = c === $ && t[h + 1].startsWith("/>") ? " " : "";
    n += c === ne ? E + hi : f >= 0 ? (r.push(u), E.slice(0, f) + gs + E.slice(f) + W + D) : E + W + (f === -2 ? h : D);
  }
  return [ps(t, n + (t[s] || "<?>") + (e === 2 ? "</svg>" : e === 3 ? "</math>" : "")), r];
};
class Ie {
  constructor({ strings: e, _$litType$: s }, r) {
    let a;
    this.parts = [];
    let n = 0, c = 0;
    const h = e.length - 1, E = this.parts, [u, _] = Ei(e, s);
    if (this.el = Ie.createElement(u, r), J.currentNode = this.el.content, s === 2 || s === 3) {
      const f = this.el.content.firstChild;
      f.replaceWith(...f.childNodes);
    }
    for (; (a = J.nextNode()) !== null && E.length < h; ) {
      if (a.nodeType === 1) {
        if (a.hasAttributes()) for (const f of a.getAttributeNames()) if (f.endsWith(gs)) {
          const I = _[c++], D = a.getAttribute(f).split(W), N = /([.?@])?(.*)/.exec(I);
          E.push({ type: 1, index: n, name: N[2], strings: D, ctor: N[1] === "." ? _i : N[1] === "?" ? mi : N[1] === "@" ? pi : Je }), a.removeAttribute(f);
        } else f.startsWith(W) && (E.push({ type: 6, index: n }), a.removeAttribute(f));
        if (ms.test(a.tagName)) {
          const f = a.textContent.split(W), I = f.length - 1;
          if (I > 0) {
            a.textContent = Pe ? Pe.emptyScript : "";
            for (let D = 0; D < I; D++) a.append(f[D], Te()), J.nextNode(), E.push({ type: 2, index: ++n });
            a.append(f[I], Te());
          }
        }
      } else if (a.nodeType === 8) if (a.data === _s) E.push({ type: 2, index: n });
      else {
        let f = -1;
        for (; (f = a.data.indexOf(W, f + 1)) !== -1; ) E.push({ type: 7, index: n }), f += W.length - 1;
      }
      n++;
    }
  }
  static createElement(e, s) {
    const r = X.createElement("template");
    return r.innerHTML = e, r;
  }
}
function te(t, e, s = t, r) {
  if (e === ee) return e;
  let a = r !== void 0 ? s._$Co?.[r] : s._$Cl;
  const n = fe(e) ? void 0 : e._$litDirective$;
  return a?.constructor !== n && (a?._$AO?.(!1), n === void 0 ? a = void 0 : (a = new n(t), a._$AT(t, s, r)), r !== void 0 ? (s._$Co ??= [])[r] = a : s._$Cl = a), a !== void 0 && (e = te(t, a._$AS(t, e.values), a, r)), e;
}
class gi {
  constructor(e, s) {
    this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = s;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(e) {
    const { el: { content: s }, parts: r } = this._$AD, a = (e?.creationScope ?? X).importNode(s, !0);
    J.currentNode = a;
    let n = J.nextNode(), c = 0, h = 0, E = r[0];
    for (; E !== void 0; ) {
      if (c === E.index) {
        let u;
        E.type === 2 ? u = new Se(n, n.nextSibling, this, e) : E.type === 1 ? u = new E.ctor(n, E.name, E.strings, this, e) : E.type === 6 && (u = new Ti(n, this, e)), this._$AV.push(u), E = r[++h];
      }
      c !== E?.index && (n = J.nextNode(), c++);
    }
    return J.currentNode = X, a;
  }
  p(e) {
    let s = 0;
    for (const r of this._$AV) r !== void 0 && (r.strings !== void 0 ? (r._$AI(e, r, s), s += r.strings.length - 2) : r._$AI(e[s])), s++;
  }
}
class Se {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(e, s, r, a) {
    this.type = 2, this._$AH = R, this._$AN = void 0, this._$AA = e, this._$AB = s, this._$AM = r, this.options = a, this._$Cv = a?.isConnected ?? !0;
  }
  get parentNode() {
    let e = this._$AA.parentNode;
    const s = this._$AM;
    return s !== void 0 && e?.nodeType === 11 && (e = s.parentNode), e;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(e, s = this) {
    e = te(this, e, s), fe(e) ? e === R || e == null || e === "" ? (this._$AH !== R && this._$AR(), this._$AH = R) : e !== this._$AH && e !== ee && this._(e) : e._$litType$ !== void 0 ? this.$(e) : e.nodeType !== void 0 ? this.T(e) : di(e) ? this.k(e) : this._(e);
  }
  O(e) {
    return this._$AA.parentNode.insertBefore(e, this._$AB);
  }
  T(e) {
    this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
  }
  _(e) {
    this._$AH !== R && fe(this._$AH) ? this._$AA.nextSibling.data = e : this.T(X.createTextNode(e)), this._$AH = e;
  }
  $(e) {
    const { values: s, _$litType$: r } = e, a = typeof r == "number" ? this._$AC(e) : (r.el === void 0 && (r.el = Ie.createElement(ps(r.h, r.h[0]), this.options)), r);
    if (this._$AH?._$AD === a) this._$AH.p(s);
    else {
      const n = new gi(a, this), c = n.u(this.options);
      n.p(s), this.T(c), this._$AH = n;
    }
  }
  _$AC(e) {
    let s = Ut.get(e.strings);
    return s === void 0 && Ut.set(e.strings, s = new Ie(e)), s;
  }
  k(e) {
    It(this._$AH) || (this._$AH = [], this._$AR());
    const s = this._$AH;
    let r, a = 0;
    for (const n of e) a === s.length ? s.push(r = new Se(this.O(Te()), this.O(Te()), this, this.options)) : r = s[a], r._$AI(n), a++;
    a < s.length && (this._$AR(r && r._$AB.nextSibling, a), s.length = a);
  }
  _$AR(e = this._$AA.nextSibling, s) {
    for (this._$AP?.(!1, !0, s); e !== this._$AB; ) {
      const r = Ft(e).nextSibling;
      Ft(e).remove(), e = r;
    }
  }
  setConnected(e) {
    this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
  }
}
class Je {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(e, s, r, a, n) {
    this.type = 1, this._$AH = R, this._$AN = void 0, this.element = e, this.name = s, this._$AM = a, this.options = n, r.length > 2 || r[0] !== "" || r[1] !== "" ? (this._$AH = Array(r.length - 1).fill(new String()), this.strings = r) : this._$AH = R;
  }
  _$AI(e, s = this, r, a) {
    const n = this.strings;
    let c = !1;
    if (n === void 0) e = te(this, e, s, 0), c = !fe(e) || e !== this._$AH && e !== ee, c && (this._$AH = e);
    else {
      const h = e;
      let E, u;
      for (e = n[0], E = 0; E < n.length - 1; E++) u = te(this, h[r + E], s, E), u === ee && (u = this._$AH[E]), c ||= !fe(u) || u !== this._$AH[E], u === R ? e = R : e !== R && (e += (u ?? "") + n[E + 1]), this._$AH[E] = u;
    }
    c && !a && this.j(e);
  }
  j(e) {
    e === R ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
  }
}
class _i extends Je {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(e) {
    this.element[this.name] = e === R ? void 0 : e;
  }
}
class mi extends Je {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(e) {
    this.element.toggleAttribute(this.name, !!e && e !== R);
  }
}
class pi extends Je {
  constructor(e, s, r, a, n) {
    super(e, s, r, a, n), this.type = 5;
  }
  _$AI(e, s = this) {
    if ((e = te(this, e, s, 0) ?? R) === ee) return;
    const r = this._$AH, a = e === R && r !== R || e.capture !== r.capture || e.once !== r.once || e.passive !== r.passive, n = e !== R && (r === R || a);
    a && this.element.removeEventListener(this.name, this, r), n && this.element.addEventListener(this.name, this, e), this._$AH = e;
  }
  handleEvent(e) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
  }
}
class Ti {
  constructor(e, s, r) {
    this.element = e, this.type = 6, this._$AN = void 0, this._$AM = s, this.options = r;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(e) {
    te(this, e);
  }
}
const fi = ft.litHtmlPolyfillSupport;
fi?.(Ie, Se), (ft.litHtmlVersions ??= []).push("3.3.2");
const Ii = (t, e, s) => {
  const r = s?.renderBefore ?? e;
  let a = r._$litPart$;
  if (a === void 0) {
    const n = s?.renderBefore ?? null;
    r._$litPart$ = a = new Se(e.insertBefore(Te(), n), n, void 0, s ?? {});
  }
  return a._$AI(t), a;
};
const Ct = globalThis;
class G extends z {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const e = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= e.firstChild, e;
  }
  update(e) {
    const s = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Ii(s, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return ee;
  }
}
G._$litElement$ = !0, G.finalized = !0, Ct.litElementHydrateSupport?.({ LitElement: G });
const Ci = Ct.litElementPolyfillSupport;
Ci?.({ LitElement: G });
(Ct.litElementVersions ??= []).push("4.2.2");
const bt = us`
  :host {
    /* brand tokens → semantic layer */
    --ink: #1B2D58;            /* color.primary — app bar, headings */
    --ink-soft: #24386B;       /* primary hover */
    --ink-press: #16244A;      /* primary active */
    --accent: #5DC5C4;         /* color.accent — focus / selection ONLY */
    --text: #3C4453;           /* body — a touch darker than #4C5364 for clarity (~8:1) */
    --text-muted: #5C6575;     /* secondary text (~5.4:1 AA) */
    --bg: #F2F2F2;             /* color.bg — page */
    --surface: #FFFFFF;        /* cards, table */
    --surface-2: #F4F6FA;      /* table head, row hover (cool 2nd layer) */
    --line: #E4E8EF;           /* hairlines */
    --line-strong: #D3D9E3;
    --danger: #D4494F;         /* color.error */
    --danger-soft: #FBEBEC;
    --danger-press: #BB3940;
    --success: #168967;        /* color.success */
    --radius: 14px;
    --radius-sm: 9px;
    --shadow-1: 0 1px 2px rgba(16,28,54,.05), 0 1px 3px rgba(16,28,54,.07);
    --shadow-2: 0 6px 22px rgba(16,28,54,.10), 0 2px 6px rgba(16,28,54,.06);
    --ring: 0 0 0 3px rgba(93,197,196,.50);
    --bar-h: 60px;
    --ease: cubic-bezier(.22,.61,.36,1);

    display: block;
    font-family: 'Noto Sans TC', sans-serif;
    color: var(--text);
    font-size: 16px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  *, *::before, *::after { box-sizing: border-box; }

  /* ── Top app bar (fixed, full-bleed via viewport-relative fixed) ───────── */
  .topbar {
    position: fixed; inset: 0 0 auto 0; height: var(--bar-h); z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    gap: 16px; padding: 0 clamp(16px, 4vw, 32px);
    background: var(--ink); color: #fff;
    box-shadow: 0 1px 0 rgba(255,255,255,.06), 0 2px 12px rgba(16,28,54,.18);
  }
  .topbar__back {
    display: inline-flex; align-items: center; gap: 9px;
    color: #fff; text-decoration: none; font-weight: 700; font-size: 17px;
    padding: 8px 12px 8px 10px; margin-left: -10px; border-radius: 10px;
    min-height: 44px; transition: background .15s var(--ease);
  }
  .topbar__back svg { width: 18px; height: 18px; opacity: .9; }
  .topbar__back:hover { background: rgba(255,255,255,.12); }
  .topbar__back:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(255,255,255,.55); }
  .topbar__logout {
    appearance: none; cursor: pointer; font-family: inherit; font-size: 15px; font-weight: 600;
    color: #EAF6F6; background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.22); border-radius: 10px;
    min-height: 40px; padding: 0 16px; transition: background .15s var(--ease), border-color .15s var(--ease);
  }
  .topbar__logout:hover { background: rgba(255,255,255,.20); }
  .topbar__logout:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(255,255,255,.55); }

  /* ── Content column ───────────────────────────────────────────────────── */
  .wrap {
    /* no max-width: the Banner/hero preview must render at full width to show
       its real desktop format (and scale a device frame to fit). */
    margin: 0 auto;
    padding: calc(var(--bar-h) + 28px) clamp(16px, 4vw, 32px) 96px;
  }

  .head {
    display: flex; align-items: flex-end; justify-content: space-between;
    gap: 16px; flex-wrap: wrap; margin-bottom: 22px;
  }
  .head__titles h1 {
    margin: 0; color: var(--ink); font-size: 28px; font-weight: 700;
    letter-spacing: -.01em; text-wrap: balance;
  }
  .head__sub { margin: 6px 0 0; color: var(--text-muted); font-size: 15px; }

  /* ── Buttons (full state vocabulary, ≥44px) ───────────────────────────── */
  .btn {
    appearance: none; cursor: pointer; font-family: inherit; text-decoration: none;
    font-size: 16px; font-weight: 700; line-height: 1;
    min-height: 46px; padding: 0 20px; border-radius: 11px; border: 1px solid transparent;
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    transition: background .16s var(--ease), border-color .16s var(--ease), box-shadow .16s var(--ease), transform .08s var(--ease);
  }
  .btn:active { transform: translateY(1px); }
  .btn:focus-visible { outline: none; box-shadow: var(--ring); }
  .btn:disabled { opacity: .5; cursor: not-allowed; transform: none; }

  .btn--primary { background: var(--ink); color: #fff; }
  .btn--primary:hover:not(:disabled) { background: var(--ink-soft); }
  .btn--primary:active { background: var(--ink-press); }

  .btn--ghost { background: var(--surface); color: var(--ink); border-color: var(--line-strong); }
  .btn--ghost:hover:not(:disabled) { border-color: var(--ink); background: #fff; }

  .btn--danger { background: var(--surface); color: var(--danger); border-color: #EAC2C4; }
  .btn--danger:hover:not(:disabled) { background: var(--danger); color: #fff; border-color: var(--danger); }

  .btn--sm { min-height: 38px; font-size: 14px; padding: 0 14px; border-radius: 9px; }

  /* ── Cards / panels ───────────────────────────────────────────────────── */
  .card {
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
    box-shadow: var(--shadow-2); overflow: hidden;
  }
  .card + .card { margin-top: 18px; }
  .card__head {
    display: flex; align-items: center; gap: 10px;
    padding: 18px 22px; border-bottom: 1px solid var(--line);
  }
  .card__head h2 { margin: 0; font-size: 19px; font-weight: 700; color: var(--ink); }
  .card__head .spacer { flex: 1; }
  .card__body { padding: 22px; }

  /* ── Table (report-grade) ─────────────────────────────────────────────── */
  .table-card {
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
    box-shadow: var(--shadow-1); overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; font-size: 16px; }
  thead th {
    background: var(--surface-2); color: var(--ink);
    text-align: left; font-weight: 700; font-size: 14px;
    padding: 13px 18px; border-bottom: 1px solid var(--line-strong); white-space: nowrap;
  }
  thead th:last-child { text-align: right; }
  tbody td {
    padding: 15px 18px; border-bottom: 1px solid var(--line);
    color: var(--text); vertical-align: middle;
    max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr { transition: background .12s var(--ease); }
  tbody tr:hover td { background: var(--surface-2); }
  th.col-actions, td.actions { width: 1%; text-align: right; white-space: nowrap; }
  .row-actions { display: inline-flex; gap: 8px; justify-content: flex-end; }
  .cell-strong { color: var(--ink); font-weight: 600; }

  /* list search (searchable collections) */
  .search-bar { margin: 0 0 14px; }
  .search-bar input[type=search] {
    width: 100%; max-width: 440px; font-family: inherit; font-size: 16px; color: var(--text);
    background: var(--surface); border: 1.5px solid var(--line-strong); border-radius: 10px;
    padding: 11px 14px; min-height: 46px; line-height: 1.5;
    transition: border-color .15s var(--ease), box-shadow .15s var(--ease);
  }
  .search-bar input[type=search]::placeholder { color: #9099A8; }
  .search-bar input[type=search]:hover { border-color: #B7C0CF; }
  .search-bar input[type=search]:focus { outline: none; border-color: var(--accent); box-shadow: var(--ring); }

  /* drag-to-reorder */
  .list-hint { font-size: 13px; color: var(--text-muted); margin: 0 0 10px; }
  th.col-drag, td.drag { width: 1%; white-space: nowrap; padding-right: 4px; }
  td.drag { color: var(--text-muted); }
  .drag-grip {
    cursor: grab; font-size: 17px; line-height: 1; color: #AAB2C0; padding: 0 2px;
    user-select: none; -webkit-user-select: none;
  }
  .drag-grip:active { cursor: grabbing; }
  .reorder { display: inline-flex; flex-direction: column; gap: 2px; vertical-align: middle; margin-left: 2px; }
  .reorder button {
    width: 28px; height: 20px; padding: 0; cursor: pointer; color: var(--ink);
    border: 1px solid var(--line-strong); background: var(--surface); border-radius: 6px;
    font-size: 10px; line-height: 1; transition: background .12s var(--ease);
  }
  .reorder button:hover:not(:disabled) { background: var(--surface-2); }
  .reorder button:disabled { opacity: .35; cursor: not-allowed; }
  tr[draggable] td:not(.drag):not(.actions) { cursor: default; }
  tr.dragging { opacity: .4; }
  tr.drag-over td { box-shadow: inset 0 2px 0 0 var(--accent); }

  /* transient save confirmation */
  .toast {
    position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); z-index: 200;
    background: var(--ink); color: #fff; padding: 11px 18px; border-radius: 12px;
    font-size: 15px; font-weight: 600; box-shadow: 0 8px 24px rgba(16,28,54,.28);
    display: inline-flex; align-items: center; gap: 8px;
  }

  /* ── Forms ────────────────────────────────────────────────────────────── */
  .field { display: flex; flex-direction: column; gap: 7px; margin-bottom: 20px; }
  .field:last-child { margin-bottom: 0; }
  .field > label { font-size: 15px; font-weight: 700; color: var(--ink); }
  .field--check > label { flex-direction: row; align-items: center; gap: 10px; font-weight: 600; cursor: pointer; }
  .req {
    display: inline-block; margin-left: 7px; color: var(--danger);
    font-size: 12px; font-weight: 700; vertical-align: 1px;
  }
  .hint { font-size: 13px; color: var(--text-muted); margin-top: 1px; }
  .group {
    border: 1px solid var(--line); border-radius: 12px; padding: 16px; background: #FBFCFE; margin-bottom: 20px;
  }
  .group > .group__title { font-size: 15px; font-weight: 700; color: var(--ink); margin: 0 0 14px; }
  .group .field:last-child { margin-bottom: 0; }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0 18px; }

  input[type=text], input[type=url], input[type=number], input[type=date], textarea, select {
    width: 100%; font-family: inherit; font-size: 16px; color: var(--text);
    background: var(--surface); border: 1.5px solid var(--line-strong); border-radius: 10px;
    padding: 11px 14px; min-height: 46px; line-height: 1.5;
    transition: border-color .15s var(--ease), box-shadow .15s var(--ease);
  }
  /* 原生日期欄：套上與其他輸入框一致的外框，並讓日曆鈕看起來可點。 */
  input[type=date] { appearance: none; -webkit-appearance: none; }
  input[type=date]::-webkit-datetime-edit { padding: 0; color: var(--text); }
  input[type=date]::-webkit-calendar-picker-indicator {
    cursor: pointer; opacity: .5; padding-left: 6px; transition: opacity .15s var(--ease);
  }
  input[type=date]:hover::-webkit-calendar-picker-indicator,
  input[type=date]:focus::-webkit-calendar-picker-indicator { opacity: .85; }
  textarea { min-height: 96px; resize: vertical; }
  input::placeholder, textarea::placeholder { color: #9099A8; }
  input:hover, textarea:hover, select:hover { border-color: #B7C0CF; }
  input:focus, textarea:focus, select:focus {
    outline: none; border-color: var(--accent); box-shadow: var(--ring);
  }
  input[type=checkbox] {
    width: 24px; height: 24px; min-height: 0; accent-color: var(--ink); cursor: pointer; flex: none;
  }
  input[type=file] { font-size: 14px; color: var(--text-muted); }
  input[type=file]::file-selector-button {
    font-family: inherit; font-size: 14px; font-weight: 700; cursor: pointer;
    color: var(--ink); background: var(--surface-2); border: 1px solid var(--line-strong);
    border-radius: 9px; padding: 9px 14px; margin-right: 12px; min-height: 40px;
    transition: background .15s var(--ease);
  }
  input[type=file]::file-selector-button:hover { background: #E9EEF6; }

  /* repeatable sub-editors (buttons / string list / stats / links) */
  .sub {
    border: 1px dashed var(--line-strong); border-radius: 11px;
    padding: 14px; background: #FBFCFE; display: flex; flex-direction: column; gap: 10px;
  }
  .sub .row { display: flex; gap: 10px; align-items: center; }
  .sub .row input { flex: 1; }
  .sub__empty { color: var(--text-muted); font-size: 14px; padding: 2px 0; }

  .img-preview {
    display: block; max-width: 200px; max-height: 116px; object-fit: cover;
    border-radius: 10px; border: 1px solid var(--line); margin-bottom: 10px; background: var(--surface-2);
  }

  /* sticky form action bar */
  .form-actions {
    display: flex; gap: 12px; margin-top: 4px; padding-top: 18px;
    border-top: 1px solid var(--line);
    position: sticky; bottom: 0;
    background: linear-gradient(to top, var(--surface) 70%, rgba(255,255,255,0));
  }

  /* editor + live preview (two-pane) */
  .editor-2col { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 22px; align-items: start; }
  /* stacked (singleton / Banner): live preview on top as the primary element, form below */
  .editor-stacked { display: flex; flex-direction: column; gap: 22px; }
  .editor-stacked .preview-col { position: static; }
  .preview-col { position: sticky; top: calc(var(--bar-h) + 18px); }
  .preview-head {
    display: flex; align-items: center; gap: 8px; margin: 0 0 9px;
    font-size: 13px; font-weight: 700; color: var(--text-muted);
  }
  .preview-head::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); }
  .preview-frame {
    width: 100%; height: 460px; display: block; background: #fff;
    border: 1px solid var(--line); border-radius: 14px; box-shadow: var(--shadow-1);
  }
  .preview-frame--wide { height: 380px; }
  .section-preview { margin-bottom: 24px; }
  .back-link {
    display: inline-block; color: #30559F; text-decoration: none;
    font-size: 15px; font-weight: 600; margin-bottom: 14px;
  }
  .back-link:hover { text-decoration: underline; }
  @media (max-width: 980px) {
    .editor-2col { grid-template-columns: 1fr; }
    .preview-col { position: static; }
  }

  /* ── States ───────────────────────────────────────────────────────────── */
  .info-hint {
    margin: 0 0 18px; padding: 12px 16px; border-radius: 11px;
    font-size: 14.5px; line-height: 1.6; font-weight: 600;
    color: #185E5C; background: #EAF7F6; border: 1px solid #BFE6E4;
  }
  .alert { border-radius: 11px; padding: 13px 16px; font-size: 15px; margin-bottom: 18px; font-weight: 600; }
  .alert--error { background: var(--danger-soft); color: var(--danger-press); border: 1px solid #F0C9CB; }

  .empty {
    text-align: center; padding: 56px 24px; color: var(--text-muted);
    background: var(--surface); border: 1px dashed var(--line-strong); border-radius: var(--radius);
  }
  .empty__title { font-size: 18px; font-weight: 700; color: var(--ink); margin: 0 0 6px; }
  .empty__hint { font-size: 15px; margin: 0; }

  /* skeleton loading (no center spinner) */
  .skeleton { display: flex; flex-direction: column; gap: 1px; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--line); }
  .skeleton__row { height: 56px; background: var(--surface); position: relative; overflow: hidden; }
  .skeleton__row::after {
    content: ""; position: absolute; inset: 0;
    background: linear-gradient(90deg, transparent, rgba(27,45,88,.06), transparent);
    transform: translateX(-100%); animation: shimmer 1.3s infinite;
  }
  @keyframes shimmer { to { transform: translateX(100%); } }

  .busy-dot {
    display: inline-block; width: 9px; height: 9px; border-radius: 50%;
    background: var(--accent); margin-right: 8px; animation: pulse 1s var(--ease) infinite;
  }
  @keyframes pulse { 50% { opacity: .35; } }

  /* ── Responsive ───────────────────────────────────────────────────────── */
  @media (max-width: 720px) {
    .head__titles h1 { font-size: 24px; }
    thead { display: none; }
    .table-card, table, tbody, tr, td { display: block; width: 100%; }
    tbody tr { border-bottom: 1px solid var(--line); padding: 6px 0; }
    tbody td { max-width: none; white-space: normal; border: none; padding: 8px 16px; }
    tbody td.actions { text-align: left; }
    .row-actions { justify-content: flex-start; }
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
    .skeleton__row::after { display: none; }
  }
`, bi = "https://tool.tzuchi-org.tw/public/d26a0119-5633-41d0-8ea8-388f12105f26";
function U(t) {
  if (t && t.default !== void 0) return t.default;
  switch (t.type) {
    case "number":
      return 0;
    case "checkbox":
      return 0;
    case "buttons":
    case "stringlist":
      return [];
    case "sroi":
    case "data_panel":
      return {};
    default:
      return "";
  }
}
function rt(t, e, s, r) {
  const a = Array.isArray(t) ? t : [], n = (c, h, E) => {
    const u = a.map((_) => ({ ..._ }));
    u[c] = { ...u[c], [h]: E }, s(u);
  };
  return m`<div class="sub">
    ${a.length ? "" : m`<div class="sub__empty">尚無項目,點下方新增</div>`}
    ${a.map((c, h) => m`<div class="row">
      ${e.map((E) => m`<input type="text" placeholder=${E.label}
        .value=${c[E.name] || ""} @input=${(u) => n(h, E.name, u.target.value)}>`)}
      <button type="button" class="btn btn--danger btn--sm"
        @click=${() => s(a.filter((E, u) => u !== h))}>刪除</button>
    </div>`)}
    <button type="button" class="btn btn--ghost btn--sm"
      @click=${() => s([...a, Object.fromEntries(e.map((c) => [c.name, ""]))])}>＋ ${r}</button>
  </div>`;
}
function Qt(t, e, s) {
  const r = Array.isArray(t) ? t : [];
  return m`<div class="sub">
    ${r.length ? "" : m`<div class="sub__empty">尚無內容,點下方新增</div>`}
    ${r.map((a, n) => m`<div class="row">
      <input type="text" .value=${a} @input=${(c) => {
    const h = r.slice();
    h[n] = c.target.value, e(h);
  }}>
      <button type="button" class="btn btn--danger btn--sm"
        @click=${() => e(r.filter((c, h) => h !== n))}>刪除</button>
    </div>`)}
    <button type="button" class="btn btn--ghost btn--sm"
      @click=${() => e([...r, ""])}>＋ ${s}</button>
  </div>`;
}
function He(t, e, s) {
  const r = (n) => s.onChange(t.name, n), a = m`<label>${t.label}${t.required ? m`<span class="req">必填</span>` : ""}</label>`;
  if (t.readonly)
    return m`<div class="field field--ro">${a}
      <div class="ro-value">${e == null || e === "" ? "—" : e}</div></div>`;
  switch (t.type) {
    case "textarea":
      return m`<div class="field">${a}
        <textarea .value=${e || ""} placeholder=${t.placeholder || ""}
          @input=${(n) => r(n.target.value)}></textarea></div>`;
    case "number":
      return m`<div class="field">${a}
        <input type="number" .value=${e === "" || e == null ? "" : String(e)}
          @input=${(n) => r(n.target.value === "" ? "" : Number(n.target.value))}></div>`;
    case "url":
      return m`<div class="field">${a}
        <input type="url" .value=${e || ""} placeholder=${t.placeholder || "https://"}
          @input=${(n) => r(n.target.value)}></div>`;
    case "checkbox":
      return m`<div class="field field--check"><label>
        <input type="checkbox" .checked=${!!e} @change=${(n) => r(n.target.checked ? 1 : 0)}>
        ${t.label}</label></div>`;
    case "select":
      return m`<div class="field">${a}
        <select @change=${(n) => r(n.target.value)}>
          ${(t.options || []).map((n) => {
        const c = n && typeof n == "object" ? n.value : n, h = n && typeof n == "object" ? n.label : n;
        return m`<option value=${c} ?selected=${c === e}>${h}</option>`;
      })}
        </select></div>`;
    case "image": {
      const n = t.storeAs === "drust_id", c = e ? n && !/^https?:/i.test(e) ? `${bi}/${e}` : e : "";
      return m`<div class="field">${a}
        ${c ? m`<img class="img-preview" src=${c} alt="">` : ""}
        <input type="text" .value=${e || ""}
          placeholder=${n ? "drust 檔案 id,或用下方按鈕上傳" : "圖片網址,或用下方按鈕上傳"}
          @input=${(h) => r(h.target.value)}>
        <input type="file" accept="image/*" @change=${async (h) => {
        const E = h.target.files[0];
        if (E)
          try {
            const u = await s.upload(E);
            r(n ? u.split("/").pop() : u);
          } catch (u) {
            alert(u.message);
          }
      }}>
        <div class="hint">建議橫式圖片;上傳後會自動填入網址。</div></div>`;
    }
    case "richtext":
      return m`<div class="field">${a}
        <tc-richtext-editor .value=${e || ""}
          @change=${(n) => r(n.detail)}></tc-richtext-editor></div>`;
    case "stringlist":
      return m`<div class="field">${a}
        ${Qt(e, (n) => r(n), "新增一行")}</div>`;
    case "buttons": {
      const n = t.subFields || [{ name: "text", label: "文字" }, { name: "href", label: "連結" }];
      return m`<div class="field">${a}
        ${rt(e, n, (c) => r(c), "新增按鈕")}</div>`;
    }
    // ── 首頁設定的結構化欄位（不顯示原始 JSON） ──────────────────────────
    case "sroi": {
      const n = e && typeof e == "object" && !Array.isArray(e) ? e : {}, c = (h, E) => r({ ...n, [h]: E });
      return m`<div class="field"><label>${t.label}</label>
        <div class="group">
          <div class="grid-2">
            <div class="field"><label>影響力數值</label>
              <input type="number" .value=${n.value ?? ""}
                @input=${(h) => c("value", h.target.value === "" ? "" : Number(h.target.value))}></div>
            <div class="field"><label>幣別</label>
              <input type="text" .value=${n.currency || ""} placeholder="NT$"
                @input=${(h) => c("currency", h.target.value)}></div>
          </div>
          <div class="field"><label>說明文字（每行一句）</label>
            ${Qt(n.descriptions, (h) => c("descriptions", h), "新增一行")}</div>
          <div class="grid-2">
            <div class="field"><label>按鈕文字</label>
              <input type="text" .value=${n.buttonText || ""}
                @input=${(h) => c("buttonText", h.target.value)}></div>
            <div class="field"><label>按鈕連結</label>
              <input type="url" .value=${n.buttonHref || ""} placeholder="https://"
                @input=${(h) => c("buttonHref", h.target.value)}></div>
          </div>
        </div></div>`;
    }
    case "data_panel": {
      const n = e && typeof e == "object" && !Array.isArray(e) ? e : {}, c = (_, f) => r({ ...n, [_]: f }), h = (_) => n[_] && typeof n[_] == "object" ? n[_] : {}, E = (_, f, I) => c(_, { ...h(_), [f]: I }), u = (_, f) => {
        const I = h(_);
        return m`<div class="group"><p class="group__title">${f}</p>
          <div class="field"><label>數據（標籤 + 數值）</label>
            ${rt(
          I.stats,
          [{ name: "label", label: "標籤" }, { name: "value", label: "數值" }],
          (D) => E(_, "stats", D),
          "新增數據"
        )}</div>
          <div class="field"><label>連結（文字 + 網址）</label>
            ${rt(
          I.links,
          [{ name: "text", label: "文字" }, { name: "href", label: "網址" }],
          (D) => E(_, "links", D),
          "新增連結"
        )}</div>
        </div>`;
      };
      return m`<div class="field"><label>${t.label}</label>
        <div class="field"><label>年度</label>
          <input type="number" .value=${n.year ?? ""}
            @input=${(_) => c("year", _.target.value === "" ? "" : Number(_.target.value))}></div>
        ${u("row1", "第一列")}
        ${u("row2", "第二列")}
      </div>`;
    }
    case "date":
      return m`<div class="field">${a}
        <input type="date" .value=${e || ""}
          @input=${(n) => r(n.target.value)}></div>`;
    // 附件 PDF：直接上傳（→ drust 公開檔）、上傳後可「開啟檢視」，並存公開 URL 當前端連結。
    case "filelist": {
      const n = Array.isArray(e) ? e : [], c = (E, u) => {
        const _ = n.map((f) => ({ ...f }));
        _[E] = { ..._[E], ...u }, r(_);
      }, h = async (E, u) => {
        const _ = u.target.files[0];
        if (_) {
          try {
            const f = await (s.uploadFile ? s.uploadFile(_) : s.upload(_));
            c(E, { href: f, label: n[E] && n[E].label ? n[E].label : _.name });
          } catch (f) {
            alert(f.message);
          }
          u.target.value = "";
        }
      };
      return m`<div class="field">${a}
        <div class="sub">
          ${n.length ? "" : m`<div class="sub__empty">尚無附件，點下方「上傳 PDF」</div>`}
          ${n.map((E, u) => m`<div class="row filerow">
            <input type="text" placeholder="顯示標籤（例：114年下半年報告 PDF）"
              .value=${E.label || ""} @input=${(_) => c(u, { label: _.target.value })}>
            ${E.href ? m`<a class="file-open btn btn--ghost btn--sm" href=${E.href} target="_blank" rel="noopener">開啟檢視</a>
                     <label class="btn btn--ghost btn--sm file-pick">重新上傳
                       <input type="file" accept="application/pdf,.pdf" hidden @change=${(_) => h(u, _)}></label>` : m`<label class="btn btn--primary btn--sm file-pick">上傳 PDF
                       <input type="file" accept="application/pdf,.pdf" hidden @change=${(_) => h(u, _)}></label>`}
            <button type="button" class="btn btn--danger btn--sm"
              @click=${() => r(n.filter((_, f) => f !== u))}>刪除</button>
          </div>`)}
          <button type="button" class="btn btn--ghost btn--sm"
            @click=${() => r([...n, { label: "", href: "" }])}>＋ 新增附件</button>
        </div></div>`;
    }
    case "datalist": {
      const n = `dl-${t.name}`;
      return m`<div class="field">${a}
        <input type="text" list=${n} .value=${e || ""}
          placeholder=${t.placeholder || "可自由輸入或從建議選"}
          @input=${(c) => r(c.target.value)}>
        <datalist id=${n}>
          ${(t.options || []).map((c) => m`<option value=${c}></option>`)}
        </datalist></div>`;
    }
    default:
      return m`<div class="field">${a}
        <input type="text" .value=${e || ""} placeholder=${t.placeholder || ""}
          @input=${(n) => r(n.target.value)}></div>`;
  }
}
const Yt = {
  marquee_bar: [
    { name: "title", label: "標題", type: "text", required: !0 },
    { name: "content", label: "內容", type: "textarea", required: !0 },
    { name: "href", label: "連結", type: "url" },
    { name: "display_order", label: "排序", type: "number" }
  ],
  site_alert: [
    { name: "enabled", label: "啟用（顯示於首頁）", type: "checkbox" },
    { name: "message", label: "公告內容", type: "richtext", required: !0 }
  ],
  hero_quicklinks: [
    { name: "title", label: "標題", type: "text", required: !0 },
    { name: "subtitle", label: "副標", type: "text" },
    { name: "href", label: "連結", type: "url", required: !0 },
    { name: "display_order", label: "排序", type: "number" }
  ],
  hero_cards: [
    // 首頁只顯示 2 張 published：slot=feature→主特色卡（左）、slot=data→數據卡（右）。
    // 可建多張 draft；把某卡發佈到某版位時，該版位原 published 卡由 tc-dash-crud 自動降級 draft（見 COLLECTION_CONFIG）。
    { name: "title", label: "標題", type: "text", required: !0 },
    {
      name: "status",
      label: "狀態",
      type: "select",
      default: "draft",
      options: [{ value: "draft", label: "草稿（不顯示）" }, { value: "published", label: "已發佈（上首頁）" }]
    },
    {
      name: "slot",
      label: "版位",
      type: "select",
      default: "feature",
      options: [{ value: "feature", label: "版位1・主特色卡（左）" }, { value: "data", label: "版位2・數據卡（右）" }]
    },
    { name: "subtitle", label: "副標", type: "text" },
    { name: "image_url", label: "圖片", type: "image" },
    { name: "content", label: "內文", type: "textarea" },
    {
      name: "buttons",
      label: "按鈕",
      type: "buttons",
      subFields: [{ name: "text", label: "文字" }, { name: "href", label: "連結" }]
    },
    { name: "badge", label: "徽章（如 NEW，留空不顯示）", type: "text" },
    { name: "display_order", label: "排序", type: "number" }
  ],
  projects: [
    { name: "title", label: "標題", type: "text", required: !0 },
    {
      name: "status",
      label: "狀態",
      type: "select",
      default: "draft",
      options: [{ value: "draft", label: "草稿（不顯示）" }, { value: "published", label: "已發佈（上首頁）" }]
    },
    { name: "image_url", label: "圖片", type: "image" },
    {
      name: "buttons",
      label: "按鈕",
      type: "buttons",
      subFields: [{ name: "text", label: "文字" }, { name: "href", label: "連結" }]
    },
    { name: "display_order", label: "排序", type: "number" }
  ],
  site_settings: [
    // hero_bg / hero_bg_mobile 已停用：首頁背景改為頁內動畫 SVG bubble，不再讀這兩欄。
    { name: "slogan", label: "標語（每行一句）", type: "stringlist" },
    { name: "slogan_en", label: "英文標語", type: "text" },
    { name: "sroi", label: "SROI 社會影響力", type: "sroi" },
    { name: "data_panel", label: "數據面板", type: "data_panel" }
  ],
  knowledge_packages: [
    { name: "title", label: "標題", type: "text", required: !0 },
    { name: "subtitle", label: "副標", type: "text" },
    { name: "href", label: "連結", type: "url", required: !0 },
    { name: "show_on_homepage", label: "顯示於首頁", type: "checkbox" },
    { name: "cover_image_drust_id", label: "封面圖", type: "image", storeAs: "drust_id" },
    { name: "display_order", label: "排序", type: "number" }
  ],
  knowledge_slides: [
    { name: "alt", label: "替代文字", type: "text" },
    { name: "image_drust_id", label: "圖片", type: "image", storeAs: "drust_id" },
    { name: "display_order", label: "排序", type: "number" }
  ],
  map_locations: [
    // 全球據點（Leaflet 地圖）。經緯度為正確語意（匯入時已修正來源 JSON 的欄名對調）。
    { name: "title", label: "據點名稱", type: "text", required: !0 },
    { name: "address_zh", label: "地址", type: "text" },
    { name: "tel", label: "電話", type: "text" },
    { name: "website", label: "網站", type: "url" },
    { name: "country", label: "國家/地區", type: "text" },
    { name: "latitude", label: "緯度（-90～90，臺灣約 22～25）", type: "number", required: !0 },
    { name: "longitude", label: "經度（-180～180，臺灣約 120～122）", type: "number", required: !0 }
  ]
}, Kt = {
  hero_cards: {
    exclusiveSlot: { statusField: "status", slotField: "slot", published: "published", draft: "draft" }
  }
}, Ni = "published";
function Ts(t) {
  return !t || typeof t != "object" ? !1 : t.status === void 0 ? !0 : t.status === Ni;
}
function Di(t) {
  const e = [], s = [];
  for (const r of Array.isArray(t) ? t : [])
    r && (Ts(r) ? e : s).push(r);
  return { published: e, drafts: s };
}
function Si(t) {
  return Ts(t) ? "已發佈（上首頁）" : "草稿（首頁不顯示）";
}
function Bi(t, e) {
  if (e == null) return "";
  const r = (t && Array.isArray(t.options) ? t.options : []).find((a) => a && String(a.value) === String(e));
  return r && r.label != null ? String(r.label) : String(e);
}
function yi(t, e) {
  return e == null ? "" : t && t.type === "select" ? Bi(t, e) : String(e);
}
const fs = "https://tool.tzuchi-org.tw/drust/t/d26a0119-5633-41d0-8ea8-388f12105f26", Ue = "tc_dash_auth", Is = "/dashboard/login";
function Ri() {
  return `${location.origin}/dashboard/`;
}
function co() {
  const t = `${fs}/oauth/google/start?redirect_uri=${encodeURIComponent(Ri())}`;
  location.href = t;
}
function lo() {
  if (!location.hash || location.hash.length < 2) return !1;
  const t = new URLSearchParams(location.hash.slice(1)), e = t.get("access_token");
  if (!e) return !1;
  const s = parseInt(t.get("expires_in") || "0", 10), r = Date.now() + (s > 0 ? s : 2592e3) * 1e3;
  return sessionStorage.setItem(Ue, JSON.stringify({ token: e, expiresAt: r })), history.replaceState(null, "", location.pathname + location.search), !0;
}
function Oi() {
  try {
    const t = sessionStorage.getItem(Ue);
    if (!t) return null;
    const e = JSON.parse(t);
    return !e || !e.token || e.expiresAt && Date.now() > e.expiresAt ? (sessionStorage.removeItem(Ue), null) : e;
  } catch {
    return null;
  }
}
function Cs() {
  const t = Oi();
  return t ? t.token : null;
}
function Li() {
  return !!Cs();
}
function Nt() {
  return Li() ? !0 : (location.href = Is, !1);
}
function Ce() {
  sessionStorage.removeItem(Ue), location.href = Is;
}
async function re(t, e = {}) {
  const s = Cs();
  if (!s)
    throw Ce(), new Error("未登入或登入逾時");
  const r = await fetch(`${fs}${t}`, {
    ...e,
    headers: { Authorization: `Bearer ${s}`, ...e.headers || {} }
  });
  if (r.status === 401)
    throw Ce(), new Error("登入逾時，請重新登入");
  if (!r.ok) {
    let a = "";
    try {
      a = JSON.stringify(await r.json());
    } catch {
      a = await r.text().catch(() => "");
    }
    throw new Error(`drust ${r.status}: ${a}`);
  }
  return r.status === 204 ? null : r.json();
}
async function q(t, { sort: e } = {}) {
  const s = { sort: e || { field: "display_order", dir: "asc" }, per_page: 500 }, r = await re(`/collections/${t}/list`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(s)
  });
  return r && r.records || [];
}
async function Wt(t, { sort: e, page: s = 1, perPage: r = 20, filter: a, select: n } = {}) {
  const c = { sort: e || { field: "display_order", dir: "asc" }, page: s, per_page: r };
  a && (c.filter = a), n && (c.select = n);
  const h = await re(`/collections/${t}/list`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(c)
  }), E = h && h.records || [];
  return {
    records: E,
    total: h && typeof h.total == "number" ? h.total : E.length,
    page: h && h.page || s,
    perPage: h && (h.perPage || h.per_page) || r
  };
}
async function be(t, e) {
  const s = await re(`/records/${t}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data: e })
  });
  return s && s.record || s;
}
async function Q(t, e, s) {
  const r = await re(`/records/${t}/${e}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data: s })
  });
  return r && r.record || r;
}
async function Qe(t, e) {
  return re(`/records/${t}/${e}`, { method: "DELETE" });
}
async function Ye(t) {
  return bs(t, "圖片");
}
async function wi(t) {
  return bs(t, "檔案");
}
async function bs(t, e) {
  if (t.size > 25 * 1024 * 1024) throw new Error(`${e}過大（上限 25MB）`);
  const s = new FormData();
  s.append("file", t), s.append("visibility", "public");
  try {
    return (await re("/files", { method: "POST", body: s })).url;
  } catch (r) {
    throw new Error(`${e}上傳失敗：${r.message}`);
  }
}
function Ne(t, e) {
  if (t == null || t === "") return e;
  if (typeof t != "string") return t;
  try {
    return JSON.parse(t);
  } catch {
    return e;
  }
}
function Gt(t) {
  return JSON.stringify(t);
}
const ki = /^(https?:|mailto:)/i;
function Me(t, e) {
  t.childNodes.forEach((s) => {
    if (s.nodeType === Node.TEXT_NODE) {
      e.appendChild(document.createTextNode(s.nodeValue));
      return;
    }
    if (s.nodeType !== Node.ELEMENT_NODE) return;
    const r = s.tagName.toLowerCase();
    if (r === "br") {
      e.appendChild(document.createElement("br"));
      return;
    }
    if (r === "a") {
      const a = (s.getAttribute("href") || "").trim();
      if (ki.test(a)) {
        const n = document.createElement("a");
        n.setAttribute("href", a), n.setAttribute("target", "_blank"), n.setAttribute("rel", "noopener noreferrer"), Me(s, n), e.appendChild(n);
        return;
      }
      Me(s, e);
      return;
    }
    Me(s, e);
  });
}
function Ns(t) {
  if (!t || typeof t != "string") return "";
  const e = new DOMParser().parseFromString(t, "text/html"), s = document.createElement("div");
  return Me(e.body, s), s.innerHTML;
}
let at = null;
function Fi() {
  return at || (at = fetch("/").then((t) => t.text()).then((t) => {
    const e = new DOMParser().parseFromString(t, "text/html");
    return Array.from(e.querySelectorAll("style")).map((s) => s.textContent).join(`
`);
  }).catch(() => "")), at;
}
const vi = "https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=Roboto:wght@400;700;900&display=swap";
let nt = null;
function Mi() {
  return nt || (nt = fetch("/data/projects.json").then((t) => t.json()).catch(() => ({ title: "近期專案與活動", moreText: "更多", moreHref: "#" }))), nt;
}
let ot = null;
function xi() {
  return ot || (ot = q("site_settings", { sort: { field: "id", dir: "asc" } }).then((t) => {
    const e = t && t[0] || {};
    return { sroi: Ne(e.sroi, {}), data_panel: Ne(e.data_panel, {}) };
  }).catch(() => ({ sroi: {}, data_panel: {} }))), ot;
}
const b = (t) => String(t ?? "").replace(
  /[&<>"]/g,
  (e) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[e]
), Ze = (t) => {
  if (Array.isArray(t)) return t;
  if (typeof t == "string" && t)
    try {
      const e = JSON.parse(t);
      return Array.isArray(e) ? e : [];
    } catch {
      return [];
    }
  return [];
}, ut = (t) => /^https?:\/\//.test(t || ""), $t = (t) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="${t === "left" ? "15 18 9 12 15 6" : "9 18 15 12 9 6"}"/></svg>`;
function At(t) {
  const e = b(t.image_url != null ? t.image_url : t.image || ""), s = b(t.title || "（未命名專案）"), r = Ze(t.buttons), a = `<img class="card__img card__img--bg" src="${e}" alt="" aria-hidden="true" loading="lazy"><img class="card__img" src="${e}" alt="${s}" loading="lazy">`;
  if (r.length > 1) {
    const c = r.map((h) => `<a class="btn-primary" href="${b(h.href || "#")}"${ut(h.href) ? ' target="_blank" rel="noopener noreferrer"' : ""}>${b(h.text || "按鈕")}</a>`).join("");
    return `<div class="card card--with-buttons"><div class="card__img-wrap">${a}<div class="card__overlay">${c}</div></div><div class="card__title">${s}</div></div>`;
  }
  const n = r[0] && r[0].href || "#";
  return `<a class="card" href="${b(n)}"${ut(n) ? ' target="_blank" rel="noopener noreferrer"' : ""}><div class="card__img-wrap">${a}</div><div class="card__title">${s}</div></a>`;
}
function Le(t) {
  return {
    image: t.image_url != null ? t.image_url : t.image || "",
    title: t.title || "",
    subtitle: t.subtitle || "",
    body: t.content || "",
    buttons: Ze(t.buttons).slice(0, 4),
    badge: t.badge || ""
  };
}
function we(t) {
  const e = b(t.image);
  return `
    <div class="hero__feature-card">
      ${t.image ? `<div class="hero__feature-img"><img class="hero__feature-img__bg" src="${e}" alt="" aria-hidden="true"><img src="${e}" alt="${b(t.title)}">${t.badge ? `<span class="hero__feature-badge">${b(t.badge)}</span>` : ""}</div>` : ""}
      <div class="hero__feature-text">
        <div class="hero__feature-title">${b(t.title) || "（未命名）"}</div>
        ${t.subtitle ? `<div class="hero__feature-subtitle">${b(t.subtitle)}</div>` : ""}
        ${t.body ? `<div class="hero__feature-body">${b(t.body)}</div>` : ""}
      </div>
      <div class="hero__feature-buttons">
        ${t.buttons.map((s) => `<a class="btn-primary" href="${b(s.href || "#")}"${ut(s.href) ? ' target="_blank" rel="noopener noreferrer"' : ""}>${b(s.text || "按鈕")}</a>`).join("")}
      </div>
    </div>`;
}
function Pi(t) {
  return `<a class="hero__quick-link" href="${b(t.href || "#")}">
    <div class="hero__quick-link-title">${b(t.title || "")}</div>
    <div class="hero__quick-link-sub">${b(t.subtitle || "")}</div></a>`;
}
const Hi = '<svg viewBox="0 0 28 28" fill="currentColor"><rect x="4" y="14" width="5" height="10" rx="1"/><rect x="11.5" y="8" width="5" height="16" rx="1"/><rect x="19" y="4" width="5" height="20" rx="1"/></svg>', Ui = '<svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 20 11 13 16 18 24 8"/><polyline points="18 8 24 8 24 14"/></svg>';
function Jt(t, e, s) {
  const r = t && Array.isArray(t.stats) ? t.stats : [], a = t && Array.isArray(t.links) ? t.links : [];
  return `<div class="hero__data-row">
    <div class="hero__data-icon">${e}</div>
    <div class="hero__data-stats" style="width:${s}">
      ${r.map((n) => `<div class="hero__data-stat"><span>${b(n.label)}</span><span>${b(n.value)}</span></div>`).join("")}
    </div>
    <div class="hero__data-links">
      ${a.map((n) => `<a class="btn-primary btn-primary--full" href="${b(n.href || "#")}" target="_blank">${b(n.text || "")}</a>`).join("")}
    </div>
  </div>`;
}
function Zt(t) {
  const e = t.sroi || {}, s = t.data_panel || {}, r = Ze(e.descriptions);
  return `<div class="hero__data-col">
    <div class="hero__sroi">
      <div class="hero__sroi-title">SROI 社會影響力評估</div>
      <div class="hero__sroi-center">
        <div class="hero__sroi-value"><span class="hero__sroi-currency">${b(e.currency)}</span><span class="hero__sroi-number">${b(e.value)}</span></div>
        <div class="hero__sroi-desc">${r.map(b).join("<br>")}</div>
      </div>
      <a class="btn-primary btn-primary--full" href="${b(e.buttonHref || "#")}" target="_blank">${b(e.buttonText || "")}</a>
    </div>
    <div class="hero__data-panel">
      ${Jt(s.row1, Hi, "103px")}
      ${Jt(s.row2, Ui, "112px")}
    </div>
  </div>`;
}
function Qi() {
  return `<svg class="hero__bg-svg hero__bg-svg--d" viewBox="442.2 251.5 1768.7 604.3" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs><radialGradient id="pv-orange-grad" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffc577"/><stop offset=".8" stop-color="#f3931b"/><stop offset="1" stop-color="#f08319"/></radialGradient></defs>
    <circle class="b1" cx="2009.2" cy="857.3" r="674.5" fill="url(#pv-orange-grad)"/>
    <circle class="b2" cx="629.5" cy="340.4" r="168" fill="url(#pv-orange-grad)"/>
    <circle class="b3" cx="1308.6" cy="933.8" r="177.5" fill="#47aeb9" fill-opacity=".8"/>
    <circle class="b4" cx="812.2" cy="199.7" r="125" fill="#47aeb9" fill-opacity=".8"/>
  </svg>`;
}
const Yi = `
  :host { display:block; background:#F2F2F2; font-family:'Noto Sans TC',sans-serif;
    border:1px solid #E4E8EF; border-radius:14px; overflow:hidden; }
  .pv-root { padding:22px 0; }
  .pv-single .card-grid-3 { max-width:380px; margin:0 auto; }
  .pv-single .container { padding:0 22px; }
  .pv-empty { color:#888; padding:12px 22px; }

  /* projects — 草稿分流：預覽只畫 published（與首頁一致），草稿只留一行提示 */
  .pv-role { text-align:center; padding:0 22px 12px; }
  .pv-draft-note { font-size:12.5px; color:#9AA3B2; text-align:center; margin:14px 0 0; padding:0 22px; }
  .pv-note { color:#9AA3B2; font-size:12.5px; padding:0 22px 10px; }

  /* hero (Banner) device preview: toolbar + a fixed-width stage scaled to fit */
  .pv-toolbar { display:flex; gap:8px; justify-content:center; padding:6px 0 16px; }
  .pv-dev { font:inherit; font-size:13px; font-weight:700; cursor:pointer; color:#3C4453;
    background:#fff; border:1px solid #CBD5E6; border-radius:9px; min-height:36px; padding:0 18px;
    display:inline-flex; align-items:center; gap:6px; transition:background .15s, color .15s, border-color .15s; }
  .pv-dev:hover { border-color:#9FB2CE; }
  .pv-dev.is-on { background:#1B2D58; color:#fff; border-color:#1B2D58; }
  .pv-stage-wrap { overflow:hidden; display:flex; justify-content:center; }
  /* flex-shrink:0 — keep the inline device width; transform:scale() does the fitting,
     otherwise the flex parent would shrink the box before _fitHeroStage measures it. */
  .pv-stage { transform-origin:top center; flex-shrink:0; }

  /* desktop device — assert the wide hero row layout (beats homepage @media) */
  .pv-stage--desktop .hero { min-height:auto; }
  .pv-stage--desktop .hero__content { flex-direction:row; align-items:flex-end; }
  .pv-stage--desktop .hero__left { width:435px; align-items:flex-start; }
  .pv-stage--desktop .hero__slogan { text-align:left; font-size:60px; }
  .pv-stage--desktop .hero__right { flex-direction:row; align-items:flex-start; }
  .pv-stage--desktop .hero__data-col { width:300px; max-width:none; }

  /* mobile device — assert the stacked layout (≈ homepage ≤480) */
  .pv-stage--mobile .hero { min-height:auto; padding:28px 22px; }
  .pv-stage--mobile .hero__content { flex-direction:column; align-items:center; gap:28px; max-width:none; padding-bottom:0; }
  .pv-stage--mobile .hero__left { width:100%; min-height:auto; align-items:center; gap:24px; }
  .pv-stage--mobile .hero__slogan { text-align:center; font-size:40px; }
  .pv-stage--mobile .hero__right { width:100%; justify-content:center; flex-wrap:wrap; }

  /* hero_cards — Hero right-side arrangement (主特色卡 + 數據卡 / SROI fallback) */
  .pv-hc { display:flex; flex-wrap:wrap; gap:14px 28px; justify-content:center; align-items:flex-start; padding:24px 22px; }
  .pv-hc__slot { display:flex; flex-direction:column; gap:10px; align-items:center; }
  /* pin production desktop widths — beats the homepage's viewport @media (≤1200/≤800),
     which would otherwise balloon these cards based on the dashboard's browser width. */
  .pv-hc .hero__feature-card { width:324px; max-width:none; }
  .pv-hc .hero__data-col { width:300px; max-width:none; }
  .pv-hc__label .tag, .pv-role .tag { display:inline-block; font-size:12.5px; font-weight:700; color:#1B2D58;
    background:#E8EEFE; border-radius:999px; padding:3px 12px; white-space:nowrap; }
  .pv-hc__ph, .pv-hc__loading { width:300px; min-height:300px; display:flex; align-items:center;
    justify-content:center; text-align:center; color:#9AA3B2; font-size:13px; }
  .pv-hc__ph { border:1.5px dashed #CBD5E6; border-radius:8px; padding:16px; }
  .pv-hc__extra { width:100%; padding:4px 22px 0; }
  .pv-hc__extra-head { font-size:12.5px; font-weight:700; color:#9AA3B2; text-align:center; margin:6px 0 12px; }
  .pv-hc__extra-row { display:flex; flex-wrap:wrap; gap:18px; justify-content:center; opacity:.55; }

  /* quicklinks list — center + wrap */
  .pv-quicklinks { display:flex; flex-wrap:wrap; gap:16px; justify-content:center; padding:28px 22px; }
`;
class Ki extends HTMLElement {
  constructor() {
    super(), this.attachShadow({ mode: "open" }), this._rows = [], this._form = {}, this._rowsLoaded = !0, this._ready = !1, this._autoTimer = null, this._cp = 0, this._tp = 1, this._track = null, this._hoverPaused = !1, this._device = "desktop", this._ro = null, this._lastFitW = -1, this._onClick = this._onClick.bind(this);
  }
  set rows(e) {
    this._rows = Array.isArray(e) ? e : [], this._ready && this._render();
  }
  get rows() {
    return this._rows;
  }
  // 載入中／載入失敗時 rows 同樣是空陣列，光看 rows 分不出「真的零筆」與「還沒拿到」，
  // 所以由呼叫端明講；false 時預覽不會斷言「目前沒有已發佈的項目」（見 _buildCarousel）。
  set rowsLoaded(e) {
    const s = !!e;
    s !== this._rowsLoaded && (this._rowsLoaded = s, this._ready && this._render());
  }
  get rowsLoaded() {
    return this._rowsLoaded;
  }
  set form(e) {
    this._form = e || {}, this._ready && this._render();
  }
  get form() {
    return this._form;
  }
  get _kind() {
    return this.getAttribute("kind");
  }
  get _single() {
    return this.hasAttribute("single");
  }
  async connectedCallback() {
    if (this._ready) return;
    if (!document.getElementById("tc-preview-fonts")) {
      const s = document.createElement("link");
      s.id = "tc-preview-fonts", s.rel = "stylesheet", s.href = vi, document.head.appendChild(s);
    }
    const e = await Fi();
    this._kind === "projects" && (this._meta = await Mi()), this.shadowRoot.innerHTML = `<style>${e}</style><style>${Yi}</style><div class="pv-root"></div>`, this._root = this.shadowRoot.querySelector(".pv-root"), this._root.addEventListener("click", this._onClick), this._root.addEventListener("mouseenter", () => {
      this._hoverPaused = !0;
    }), this._root.addEventListener("mouseleave", () => {
      this._hoverPaused = !1;
    }), this._mql = window.matchMedia("(min-width: 768px)"), this._motionMql = window.matchMedia("(prefers-reduced-motion: reduce)"), this._mql.addEventListener("change", () => {
      this._kind === "projects" && !this._single && (this._buildCarousel(), this._startAuto());
    }), "ResizeObserver" in window && (this._ro = new ResizeObserver((s) => {
      if (this._kind !== "hero") return;
      const r = Math.round(s[0].contentRect.width);
      r !== this._lastFitW && (this._lastFitW = r, this._fitHeroStage());
    }), this._ro.observe(this)), this._ready = !0, this._render();
  }
  disconnectedCallback() {
    clearInterval(this._autoTimer), this._ro && this._ro.disconnect();
  }
  _render() {
    if (this._root)
      switch (clearInterval(this._autoTimer), this._kind) {
        case "projects":
          return this._renderProjects();
        case "marquee":
          return this._renderMarquee();
        case "hero-cards":
          return this._renderHeroCards();
        case "hero":
          return this._renderHero();
        case "quicklinks":
          return this._renderQuicklinks();
        default:
          this._root.innerHTML = '<p class="pv-empty">（此區塊的即時預覽即將支援）</p>';
      }
  }
  // ── projects (carousel / single card) ──
  // 首頁只顯示 status='published'（get_homepage RPC 就是這樣撈的），所以預覽也照分：
  // published 進輪播、draft 另列於下方並標明首頁不顯示（同 _renderHeroCards 的作法）。
  _renderProjects() {
    if (this._single) {
      const e = this._form || {}, s = e.status !== void 0, r = Si(s ? e : { status: null });
      this._root.innerHTML = `<div id="projects-section" class="pv-single"><div class="pv-role"><span class="tag">${b(r)}</span></div><div class="container"><div class="card-grid-3">${At(e)}</div></div></div>`;
      return;
    }
    this._buildCarousel(), this._startAuto();
  }
  _perPage() {
    return this._mql && this._mql.matches ? 6 : 2;
  }
  _buildCarousel() {
    const { published: e, drafts: s } = Di(this._rows), a = this._rowsLoaded && !e.length && this._meta && Array.isArray(this._meta.items) ? this._meta.items : [], n = a.length > 0, c = n ? a.map((N) => At({ title: N.title, image: N.image, buttons: [{ text: "", href: N.href }] })) : e.map(At), h = this._perPage();
    this._tp = Math.max(1, Math.ceil(c.length / h)), this._cp = Math.min(this._cp, this._tp - 1);
    const E = Array.from({ length: this._tp }, (N, O) => `<div class="carousel-slide"><div class="card-grid-3">${c.slice(O * h, (O + 1) * h).join("")}</div></div>`).join(""), u = this._tp > 1 ? `<div class="pager"><div class="line"></div><div class="pager-controls"><button class="pager-btn" data-action="prev" aria-label="上一頁">${$t("left")}</button><div class="pager-dots">${Array.from({ length: this._tp }, (N, O) => `<button class="pager-dot" data-page="${O}" aria-label="第 ${O + 1} 頁"></button>`).join("")}</div><button class="pager-btn" data-action="next" aria-label="下一頁">${$t("right")}</button></div><div class="line"></div></div>` : "", _ = c.length ? "" : '<p class="pv-empty">尚無項目</p>', f = n ? '<p class="pv-note">目前沒有已發佈的項目，首頁會顯示預設清單（data/projects.json）：</p>' : "", I = this._meta && this._meta.moreHref ? `<a class="more-link" href="${b(this._meta.moreHref)}">${b(this._meta.moreText || "更多")} <img class="link-chevron" src="/images/icons/chevron-right.svg" alt=""></a>` : "", D = s.length ? `<p class="pv-draft-note">另有 ${s.length} 筆草稿（首頁不顯示，預覽亦不列出）</p>` : "";
    this._root.innerHTML = `<div id="projects-section"><div class="container"><div class="section-header"><h2>${b(this._meta && this._meta.title || "近期專案與活動")}</h2><div class="line"></div>${I}</div>${f}<div class="carousel-viewport"><div class="carousel-track">${E}</div></div>${u}${_}</div>${D}</div>`, this._track = this._root.querySelector(".carousel-track"), this._goTo(this._cp, !1);
  }
  _goTo(e, s = !0) {
    if (!this._track) return;
    e = (e % this._tp + this._tp) % this._tp, this._cp = e;
    const r = this._track.querySelectorAll(".carousel-slide");
    s ? r.forEach((a, n) => a.classList.toggle("is-active", n === e)) : (r.forEach((a) => {
      a.style.transition = "none";
    }), r.forEach((a, n) => a.classList.toggle("is-active", n === e)), this._track.offsetHeight, r.forEach((a) => {
      a.style.transition = "";
    })), this._root.querySelectorAll(".pager-dot").forEach((a, n) => a.classList.toggle("active", n === e));
  }
  _startAuto() {
    clearInterval(this._autoTimer), !(this._tp <= 1 || this._motionMql && this._motionMql.matches) && (this._autoTimer = setInterval(() => {
      this._hoverPaused || this._goTo(this._cp + 1);
    }, 1e4));
  }
  // ── marquee (reuse the real <tc-marquee> component, fed edited rows) ──
  _renderMarquee() {
    const e = (this._single ? [this._form] : this._rows).filter((s) => s && (s.title || s.content));
    if (!e.length) {
      this._root.innerHTML = '<p class="pv-empty">尚無項目</p>';
      return;
    }
    import("./tc-marquee-K4VvbqnC.js").then(() => {
      if (this._kind !== "marquee") return;
      let s = this._root.querySelector("tc-marquee");
      s || (this._root.innerHTML = "", s = document.createElement("tc-marquee"), this._root.appendChild(s)), s.items = e;
    });
  }
  // ── hero_cards — reproduce the homepage Hero right-side arrangement（新版：published + slot）：
  //    slot='feature' published → 主特色卡（左）；slot='data' published → 數據卡（右）；
  //    無 data 卡 → Banner SROI/data-panel 回退；draft 卡首頁不顯示（另列標示）。──
  _renderHeroCards() {
    const e = (u, _) => `<div class="pv-hc__slot"><div class="pv-hc__label"><span class="tag">${b(u)}</span></div>${_}</div>`;
    if (this._single) {
      const u = this._form, _ = u.status !== "published" ? "草稿（首頁不顯示）" : u.slot === "data" ? "版位2・數據卡（右）" : "版位1・主特色卡（左）";
      this._root.innerHTML = `<div class="pv-hc">${e(_, we(Le(u)))}</div>`;
      return;
    }
    const s = (this._rows || []).filter(Boolean), r = s.filter((u) => u.status === "published"), a = r.find((u) => u.slot === "feature") || null, n = r.find((u) => u.slot === "data") || null, c = s.filter((u) => u.status !== "published"), h = a ? e("版位1・主特色卡（左）", we(Le(a))) : '<div class="pv-hc__slot"><div class="pv-hc__label"><span class="tag">版位1・主特色卡（左）</span></div><div class="pv-hc__ph">尚無 published 卡片</div></div>', E = c.length ? `<div class="pv-hc__extra"><div class="pv-hc__extra-head">↓ 草稿（首頁不顯示）</div><div class="pv-hc__extra-row">${c.map((u) => we(Le(u))).join("")}</div></div>` : "";
    if (n) {
      this._root.innerHTML = `<div class="pv-hc">${h}${e("版位2・數據卡（右）", we(Le(n)))}</div>${E}`;
      return;
    }
    this._root.innerHTML = `<div class="pv-hc">${h}${e("版位2・數據卡（右）· 預設 SROI／數據面板", '<div class="pv-hc__loading">載入 Banner 設定…</div>')}</div>${E}`, xi().then((u) => {
      if (this._kind !== "hero-cards" || this._single) return;
      const _ = this._root.querySelector(".pv-hc__loading");
      _ && (_.outerHTML = Zt(u));
    }).catch(() => {
    });
  }
  // ── hero (Banner singleton: slogan + sroi + data-panel) ──
  // Renders the hero at a fixed device width (desktop/mobile) and scales it to
  // fit the panel, with a toggle button. Real wide format, not force-stacked.
  _renderHero() {
    const e = this._single ? this._form : this._rows[0] || {}, s = this._device === "mobile" ? "mobile" : "desktop", r = s === "mobile" ? 390 : 1280, a = Ze(e.slogan), n = e.slogan_en || "", c = (h, E) => `<button type="button" class="pv-dev ${s === h ? "is-on" : ""}" data-device="${h}">${E}</button>`;
    this._root.innerHTML = `
      <div class="pv-toolbar">${c("desktop", "🖥 桌機")}${c("mobile", "📱 手機")}</div>
      <div class="pv-stage-wrap">
        <div class="pv-stage pv-stage--${s}" style="width:${r}px">
          <section class="hero">
            ${Qi()}
            <div class="hero__content">
              <div class="hero__left">
                <h1 class="hero__slogan">${a.map(b).join("<br>")}${n ? `<br><span class="hero__slogan-en">${b(n)}</span>` : ""}</h1>
              </div>
              <div class="hero__right">${Zt(e)}</div>
            </div>
          </section>
        </div>
      </div>`, this._fitHeroStage();
  }
  // Scale the fixed-width device stage down to fit the available panel width,
  // then collapse the wrapper to the scaled height (no transform whitespace).
  _fitHeroStage() {
    const e = this._root && this._root.querySelector(".pv-stage-wrap"), s = e && e.querySelector(".pv-stage");
    if (!s) return;
    s.style.transform = "none";
    const r = e.clientWidth;
    if (r <= 0) {
      e.style.height = "";
      return;
    }
    const a = s.offsetWidth || 1, n = a > r ? r / a : 1;
    s.style.transform = `scale(${n})`, e.style.height = s.offsetHeight * n + "px";
  }
  // ── quicklinks (hero__quick-link pills) ──
  _renderQuicklinks() {
    const s = (this._single ? [this._form] : this._rows).filter(Boolean).map(Pi).join("");
    this._root.innerHTML = `<div class="pv-quicklinks">${s || '<p class="pv-empty">尚無項目</p>'}</div>`;
  }
  _onClick(e) {
    const s = e.target.closest(".pv-dev");
    if (s) {
      this._device = s.dataset.device, this._lastFitW = -1, this._renderHero();
      return;
    }
    const r = e.target.closest(".pager-btn"), a = e.target.closest(".pager-dot");
    if (r || a) {
      r && r.dataset.action === "prev" ? this._goTo(this._cp - 1) : r && r.dataset.action === "next" ? this._goTo(this._cp + 1) : a && this._goTo(Number(a.dataset.page)), this._startAuto();
      return;
    }
    if (e.target.closest(".btn-primary")) return;
    const n = e.target.closest(".card--with-buttons");
    this._root.querySelectorAll(".card--with-buttons.is-active").forEach((c) => {
      c !== n && c.classList.remove("is-active");
    }), n && n.classList.toggle("is-active");
  }
}
customElements.define("tc-section-preview", Ki);
const Xt = /* @__PURE__ */ new Set(["buttons", "stringlist", "sroi", "data_panel"]), Wi = m`<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
class Gi extends G {
  static styles = bt;
  static properties = {
    collection: { type: String },
    fields: { attribute: !1 },
    titleText: { type: String, attribute: "title-text" },
    singleton: { type: Boolean },
    searchable: { type: Boolean },
    previewKind: { type: String, attribute: "preview-kind" },
    hintText: { type: String, attribute: "hint-text" },
    _rows: { state: !0 },
    _q: { state: !0 },
    _form: { state: !0 },
    _busy: { state: !0 },
    _error: { state: !0 },
    _flash: { state: !0 }
  };
  constructor() {
    super(), this.collection = "", this.fields = [], this.titleText = "", this.singleton = !1, this.searchable = !1, this.previewKind = "", this.hintText = "", this._rows = [], this._q = "", this._form = {}, this._busy = !1, this._error = "", this._flash = "", this._nav = { mode: "list", slug: "" }, this.__editRow = null, this.__init = !1, this.__dragFrom = null, this.__flashT = null, this.__previewReady = !1, this.__rowsLoaded = !1;
  }
  connectedCallback() {
    if (super.connectedCallback(), !Nt()) return;
    const e = location.pathname.split("/").filter(Boolean), s = e[1] || this.collection;
    this.singleton ? this._nav = { mode: "edit", slug: s, recordId: null, isNew: !1 } : e[2] === "new" ? this._nav = { mode: "edit", slug: s, recordId: null, isNew: !0 } : e[2] === "edit" ? this._nav = { mode: "edit", slug: s, recordId: Number(e[3]), isNew: !1 } : this._nav = { mode: "list", slug: s };
  }
  get _hasOrder() {
    return this.fields.some((e) => e.name === "display_order");
  }
  // 表單不顯示 display_order（拖曳排序）與 hidden 欄（如 slot：NOT NULL 但版位由順序決定、
  // 承辦不需填）；hidden 欄仍會經 _blankForm/_toPayload 隨表單流轉並於存檔自動補值。
  get _formFields() {
    return this.fields.filter((e) => e.name !== "display_order" && !e.hidden);
  }
  get _listPath() {
    return "/dashboard/" + this._nav.slug;
  }
  // 搜尋過濾後的列表（比對 schema 所有欄位的字串值）。
  get _visibleRows() {
    const e = this._q.trim().toLowerCase();
    return e ? this._rows.filter((s) => this.fields.some((r) => String(s[r.name] ?? "").toLowerCase().includes(e))) : this._rows;
  }
  // ── data loading (lazy: waits until the page JS has set `fields`) ──
  async _loadList() {
    this._busy = !0, this._error = "";
    try {
      const e = await q(this.collection, { sort: { field: this._hasOrder ? "display_order" : "id", dir: "asc" } });
      this.__rowsLoaded = !0, this._rows = e;
    } catch (e) {
      this._error = e.message;
    } finally {
      this._busy = !1;
    }
  }
  async _loadEditRow() {
    this._busy = !0, this._error = "";
    try {
      const e = await q(this.collection, { sort: { field: this._hasOrder ? "display_order" : "id", dir: "asc" } });
      if (this._rows = e, this.singleton)
        this.__editRow = e[0] || null, this._form = this.__editRow ? this._toForm(this.__editRow) : this._blankForm();
      else if (this._nav.isNew)
        this.__editRow = null, this._form = this._blankForm(), this._hasOrder && (this._form.display_order = e.length);
      else {
        const s = e.find((r) => r.id === this._nav.recordId);
        s ? (this.__editRow = s, this._form = this._toForm(s)) : (this._error = "找不到這筆資料（可能已被刪除）。", this._form = this._blankForm());
      }
    } catch (e) {
      this._error = e.message;
    } finally {
      this._busy = !1;
    }
  }
  _toForm(e) {
    const s = {};
    for (const r of this.fields) {
      const a = e[r.name];
      Xt.has(r.type) ? s[r.name] = Ne(a, U(r)) : s[r.name] = a ?? U(r);
    }
    return s;
  }
  _blankForm() {
    const e = {};
    for (const s of this.fields) e[s.name] = U(s);
    return e;
  }
  _toPayload() {
    const e = {};
    for (const s of this.fields) {
      const r = this._form[s.name];
      Xt.has(s.type) ? e[s.name] = JSON.stringify(r ?? U(s)) : s.type === "number" ? e[s.name] = r === "" || r == null ? 0 : Number(r) : s.type === "richtext" ? e[s.name] = Ns(r || "") : e[s.name] = r;
    }
    return e;
  }
  _onChange = (e, s) => {
    this._form = { ...this._form, [e]: s };
  };
  _upload = (e) => Ye(e);
  _flashMsg(e) {
    this._flash = e, clearTimeout(this.__flashT), this.__flashT = setTimeout(() => {
      this._flash = "";
    }, 1800);
  }
  _gotoList() {
    location.href = this._listPath;
  }
  _validate() {
    for (const e of this.fields)
      if (e.required) {
        const s = this._form[e.name];
        if (s === "" || s == null) return `「${e.label}」為必填`;
      }
    return "";
  }
  async _save() {
    const e = this._validate();
    if (e) {
      this._error = e;
      return;
    }
    this._busy = !0, this._error = "";
    try {
      const s = this._toPayload();
      if (this.singleton)
        this.__editRow ? await Q(this.collection, this.__editRow.id, s) : await be(this.collection, s), await this._loadEditRow(), this._busy = !1, this._flashMsg("已儲存");
      else if (this._nav.isNew) {
        const r = await be(this.collection, s);
        await this._applyExclusiveSlot(r && r.id, s), this._gotoList();
      } else
        await Q(this.collection, this._nav.recordId, s), await this._applyExclusiveSlot(this._nav.recordId, s), this._gotoList();
    } catch (s) {
      this._error = s.message, this._busy = !1;
    }
  }
  // exclusiveSlot（如 hero_cards）：存為 published 時，把「同 slot 的其他 published 列」降級 draft，
  // 使每版位至多一張 published（＝把新卡發佈到某版位時原佔位卡自動退為草稿）。
  async _applyExclusiveSlot(e, s) {
    const r = Kt[this.collection] && Kt[this.collection].exclusiveSlot;
    if (!r || s[r.statusField] !== r.published) return;
    const a = s[r.slotField], n = await q(this.collection);
    for (const c of n)
      c.id !== e && c[r.statusField] === r.published && c[r.slotField] === a && await Q(this.collection, c.id, { [r.statusField]: r.draft });
  }
  async _delete(e) {
    if (confirm(`確定刪除這筆？
（${e[this._formFields[0].name] || e.id}）`)) {
      this._busy = !0, this._error = "";
      try {
        await Qe(this.collection, e.id), await this._loadList(), this._flashMsg("已刪除");
      } catch (s) {
        this._error = s.message;
      } finally {
        this._busy = !1;
      }
    }
  }
  // ── reordering (drag + ▲▼) ──
  async _reorder(e, s) {
    if (e == null || e === s) return;
    const r = this._rows.slice(), [a] = r.splice(e, 1);
    r.splice(s, 0, a), this._rows = r, this._busy = !0, this._error = "";
    try {
      await Promise.all(r.map((n, c) => n.display_order === c ? null : Q(this.collection, n.id, { display_order: c })).filter(Boolean)), await this._loadList(), this._flashMsg("順序已更新");
    } catch (n) {
      this._error = n.message, await this._loadList();
    } finally {
      this._busy = !1;
    }
  }
  _move(e, s) {
    const r = e + s;
    r < 0 || r >= this._rows.length || this._reorder(e, r);
  }
  _onDragStart(e, s) {
    if (this.__dragFrom = s, e.dataTransfer) {
      e.dataTransfer.effectAllowed = "move";
      try {
        e.dataTransfer.setData("text/plain", String(s));
      } catch {
      }
    }
    e.currentTarget.classList.add("dragging");
  }
  _onDragOver(e) {
    e.preventDefault(), e.dataTransfer && (e.dataTransfer.dropEffect = "move");
  }
  _onDrop(e, s) {
    e.preventDefault();
    const r = this.__dragFrom;
    this.__dragFrom = null, this._clearDrag(), this._reorder(r, s);
  }
  _onDragEnd() {
    this.__dragFrom = null, this._clearDrag();
  }
  _clearDrag() {
    this.renderRoot.querySelectorAll("tr.dragging").forEach((e) => e.classList.remove("dragging"));
  }
  // ── lifecycle: lazy init + live preview wiring ──
  // Lazy init: load data once the page JS has set `fields`. The live preview
  // updates itself via property binding on <tc-section-preview> (.rows / .form).
  updated() {
    !this.__init && this.collection && this.fields && this.fields.length && (this.__init = !0, this._nav.mode === "list" ? this._loadList() : this._loadEditRow());
  }
  render() {
    const e = this._nav.mode === "edit";
    return m`
      <header class="topbar">
        <a class="topbar__back" href="/dashboard/">${Wi} 首頁後台</a>
        <button class="topbar__logout" @click=${() => Ce()}>登出</button>
      </header>
      <div class="wrap">
        ${e && !this.singleton ? m`<a class="back-link" href=${this._listPath}>← 返回${this.titleText}列表</a>` : ""}
        <div class="head">
          <div class="head__titles">
            <h1>${this.titleText}</h1>
            <p class="head__sub">${this._subtitle()}</p>
          </div>
          ${e ? "" : m`<a class="btn btn--primary" href=${this._listPath + "/new"}>＋ 新增</a>`}
        </div>
        ${this.hintText ? m`<p class="info-hint">ℹ️ ${this.hintText}</p>` : ""}
        ${this._error ? m`<div class="alert alert--error">${this._error}</div>` : ""}
        ${e ? this._renderEditArea() : this._renderListBody()}
      </div>
      ${this._flash ? m`<div class="toast">✓ ${this._flash}</div>` : ""}
    `;
  }
  _subtitle() {
    return this.singleton ? "修改後立即反映於首頁" : this._nav.mode === "edit" ? this._nav.isNew ? "新增一筆內容" : "編輯內容" : this._busy ? m`<span class="busy-dot"></span>載入中…` : this._q.trim() ? `符合 ${this._visibleRows.length} 筆（共 ${this._rows.length} 筆）` : `目前共 ${this._rows.length} 筆`;
  }
  // ── list view ──
  _renderListBody() {
    return m`
      ${this.previewKind ? m`
        <div class="section-preview">
          <div class="preview-head">區塊預覽（首頁實際樣子）</div>
          <tc-section-preview kind=${this.previewKind} .rowsLoaded=${this.__rowsLoaded} .rows=${this._rows}></tc-section-preview>
        </div>` : ""}
      ${this.searchable ? m`
        <div class="search-bar">
          <input type="search" placeholder="搜尋（名稱、地址、電話…）" aria-label="搜尋列表"
            .value=${this._q} @input=${(e) => {
      this._q = e.target.value;
    }}>
        </div>` : ""}
      ${this._busy && !this._rows.length ? this._renderSkeleton() : this._rows.length ? this._renderTable() : this._renderEmpty()}
    `;
  }
  _listColumns() {
    return this.fields.filter((e) => !e.hidden && ["text", "textarea", "url", "select"].includes(e.type)).slice(0, 2);
  }
  _renderTable() {
    const e = this._listColumns(), s = this._visibleRows, r = this._hasOrder && !this._q.trim();
    if (!s.length)
      return m`<div class="empty">
        <p class="empty__title">找不到符合「${this._q.trim()}」的資料</p>
        <p class="empty__hint">換個關鍵字試試。</p>
      </div>`;
    const a = s.length - 1;
    return m`
      ${r ? m`<p class="list-hint">拖曳左側 ⋮⋮ 可調整順序（或用 ▲▼）；變更即時儲存。</p>` : ""}
      <div class="table-card">
        <table>
          <thead><tr>
            ${r ? m`<th class="col-drag"></th>` : ""}
            ${e.map((n) => m`<th>${n.label}</th>`)}
            <th class="col-actions">操作</th>
          </tr></thead>
          <tbody>
            ${s.map((n, c) => m`<tr
              draggable=${r ? "true" : "false"}
              @dragstart=${(h) => this._onDragStart(h, c)} @dragover=${this._onDragOver}
              @drop=${(h) => this._onDrop(h, c)} @dragend=${() => this._onDragEnd()}>
              ${r ? m`<td class="drag">
                <span class="drag-grip" title="拖曳排序">⋮⋮</span>
                <span class="reorder">
                  <button title="上移" ?disabled=${c === 0 || this._busy} @click=${() => this._move(c, -1)}>▲</button>
                  <button title="下移" ?disabled=${c === a || this._busy} @click=${() => this._move(c, 1)}>▼</button>
                </span></td>` : ""}
              ${e.map((h, E) => {
      const u = yi(h, n[h.name]);
      return m`<td class=${E === 0 ? "cell-strong" : ""} title=${u}>${u || "—"}</td>`;
    })}
              <td class="actions"><div class="row-actions">
                <a class="btn btn--ghost btn--sm" href=${this._listPath + "/edit/" + n.id}>編輯</a>
                <button class="btn btn--danger btn--sm" @click=${() => this._delete(n)}>刪除</button>
              </div></td>
            </tr>`)}
          </tbody>
        </table>
      </div>`;
  }
  _renderSkeleton() {
    return m`<div class="skeleton">${[0, 1, 2, 3, 4].map(() => m`<div class="skeleton__row"></div>`)}</div>`;
  }
  _renderEmpty() {
    return m`<div class="empty">
      <p class="empty__title">尚無資料</p>
      <p class="empty__hint">點右上角「＋ 新增」建立第一筆。</p>
    </div>`;
  }
  // ── edit view (form + optional live preview) ──
  _renderEditArea() {
    const e = { onChange: this._onChange, upload: this._upload }, s = this.singleton ? this.titleText : `${this._nav.isNew ? "新增" : "編輯"} ${this.titleText}`, r = m`
      <div class="card">
        <div class="card__head"><h2>${s}</h2></div>
        <div class="card__body">
          ${this._formFields.map((n) => He(n, this._form[n.name], e))}
          <div class="form-actions">
            <button class="btn btn--primary" ?disabled=${this._busy} @click=${() => this._save()}>
              ${this._busy ? m`<span class="busy-dot"></span>儲存中…` : "儲存"}
            </button>
            ${this.singleton ? "" : m`<button class="btn btn--ghost" ?disabled=${this._busy}
              @click=${() => this._gotoList()}>取消</button>`}
          </div>
        </div>
      </div>`;
    if (!this.previewKind) return r;
    const a = m`
      <div class="preview-col">
        <div class="preview-head">即時預覽</div>
        <tc-section-preview kind=${this.previewKind} .form=${this._form} single></tc-section-preview>
      </div>`;
    return this.singleton ? m`<div class="editor-stacked">${a}<div>${r}</div></div>` : m`
      <div class="editor-2col">
        <div>${r}</div>
        ${a}
      </div>`;
  }
}
customElements.define("tc-dash-crud", Gi);
const $i = m`<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
class Ji extends G {
  static styles = bt;
  static properties = {
    _pkgs: { state: !0 },
    _editingPkg: { state: !0 },
    // null | 'new' | pkg row
    _pkgForm: { state: !0 },
    _slides: { state: !0 },
    _editingSlide: { state: !0 },
    // null | 'new' | slide row
    _slideForm: { state: !0 },
    _busy: { state: !0 },
    _error: { state: !0 },
    _flash: { state: !0 }
  };
  constructor() {
    super(), this._pkgs = [], this._editingPkg = null, this._pkgForm = {}, this._slides = [], this._editingSlide = null, this._slideForm = {}, this._busy = !1, this._error = "", this._flash = "", this.__dragFrom = null, this.__dragKind = null, this.__flashT = null;
  }
  connectedCallback() {
    super.connectedCallback(), Nt() && this._loadPkgs();
  }
  get _pkgFields() {
    return Yt.knowledge_packages;
  }
  get _slideFields() {
    return Yt.knowledge_slides;
  }
  get _pkgFormFields() {
    return this._pkgFields.filter((e) => e.name !== "display_order");
  }
  get _slideFormFields() {
    return this._slideFields.filter((e) => e.name !== "display_order");
  }
  _ctx = { onChange: (e, s) => {
    this._pkgForm = { ...this._pkgForm, [e]: s };
  }, upload: (e) => Ye(e) };
  _slideCtx = { onChange: (e, s) => {
    this._slideForm = { ...this._slideForm, [e]: s };
  }, upload: (e) => Ye(e) };
  _flashMsg(e) {
    this._flash = e, clearTimeout(this.__flashT), this.__flashT = setTimeout(() => {
      this._flash = "";
    }, 1800);
  }
  _blank(e) {
    const s = {};
    for (const r of e) s[r.name] = U(r);
    return s;
  }
  _toForm(e, s) {
    const r = {};
    for (const a of e) r[a.name] = s[a.name] == null ? U(a) : s[a.name];
    return r;
  }
  _payload(e, s) {
    const r = {};
    for (const a of e) r[a.name] = a.type === "number" ? Number(s[a.name] || 0) : s[a.name];
    return r;
  }
  async _loadPkgs() {
    this._busy = !0, this._error = "";
    try {
      this._pkgs = await q("knowledge_packages");
    } catch (e) {
      this._error = e.message;
    } finally {
      this._busy = !1;
    }
  }
  async _loadSlides(e) {
    this._busy = !0;
    try {
      const s = await q("knowledge_slides");
      this._slides = s.filter((r) => r.package_id === e);
    } catch (s) {
      this._error = s.message;
    } finally {
      this._busy = !1;
    }
  }
  // ── packages ──
  _newPkg() {
    this._editingPkg = "new", this._pkgForm = this._blank(this._pkgFields), this._pkgForm.display_order = this._pkgs.length, this._slides = [], this._error = "";
  }
  async _editPkg(e) {
    this._editingPkg = e, this._pkgForm = this._toForm(this._pkgFields, e), this._error = "", await this._loadSlides(e.id);
  }
  _closePkg() {
    this._editingPkg = null, this._slides = [], this._editingSlide = null, this._error = "";
  }
  async _savePkg() {
    for (const e of this._pkgFields) if (e.required && !this._pkgForm[e.name]) {
      this._error = `「${e.label}」為必填`;
      return;
    }
    this._busy = !0, this._error = "";
    try {
      const e = this._payload(this._pkgFields, this._pkgForm);
      if (this._editingPkg === "new") {
        const s = await be("knowledge_packages", e);
        this._editingPkg = s;
      } else await Q("knowledge_packages", this._editingPkg.id, e);
      await this._loadPkgs(), this._flashMsg("已儲存知識包");
    } catch (e) {
      this._error = e.message;
    } finally {
      this._busy = !1;
    }
  }
  async _deletePkg(e) {
    if (confirm(`刪除知識包「${e.title}」？
其投影片需先刪除。`)) {
      this._busy = !0, this._error = "";
      try {
        await Qe("knowledge_packages", e.id), await this._loadPkgs(), this._closePkg(), this._flashMsg("已刪除");
      } catch (s) {
        this._error = s.message;
      } finally {
        this._busy = !1;
      }
    }
  }
  // ── slides ──
  _newSlide() {
    this._editingSlide = "new", this._slideForm = this._blank(this._slideFields), this._slideForm.display_order = this._slides.length;
  }
  _editSlide(e) {
    this._editingSlide = e, this._slideForm = this._toForm(this._slideFields, e);
  }
  _closeSlide() {
    this._editingSlide = null;
  }
  async _saveSlide() {
    const e = this._editingPkg && this._editingPkg.id;
    if (!e) {
      this._error = "請先儲存知識包再新增投影片";
      return;
    }
    this._busy = !0, this._error = "";
    try {
      const s = { ...this._payload(this._slideFields, this._slideForm), package_id: e };
      this._editingSlide === "new" ? await be("knowledge_slides", s) : await Q("knowledge_slides", this._editingSlide.id, s), await this._loadSlides(e), this._editingSlide = null, this._flashMsg("已儲存投影片");
    } catch (s) {
      this._error = s.message;
    } finally {
      this._busy = !1;
    }
  }
  async _deleteSlide(e) {
    if (confirm("刪除這張投影片？")) {
      this._busy = !0;
      try {
        await Qe("knowledge_slides", e.id), await this._loadSlides(this._editingPkg.id), this._flashMsg("已刪除");
      } catch (s) {
        this._error = s.message;
      } finally {
        this._busy = !1;
      }
    }
  }
  // ── reordering (persists display_order = position) ──
  async _reorderPkg(e, s) {
    if (e == null || e === s) return;
    const r = this._pkgs.slice(), [a] = r.splice(e, 1);
    r.splice(s, 0, a), this._pkgs = r, this._busy = !0, this._error = "";
    try {
      await Promise.all(r.map((n, c) => n.display_order === c ? null : Q("knowledge_packages", n.id, { display_order: c })).filter(Boolean)), await this._loadPkgs(), this._flashMsg("順序已更新");
    } catch (n) {
      this._error = n.message, await this._loadPkgs();
    } finally {
      this._busy = !1;
    }
  }
  async _reorderSlide(e, s) {
    if (e == null || e === s) return;
    const r = this._slides.slice(), [a] = r.splice(e, 1);
    r.splice(s, 0, a), this._slides = r, this._busy = !0, this._error = "";
    try {
      await Promise.all(r.map((n, c) => n.display_order === c ? null : Q("knowledge_slides", n.id, { display_order: c })).filter(Boolean)), await this._loadSlides(this._editingPkg.id), this._flashMsg("順序已更新");
    } catch (n) {
      this._error = n.message, await this._loadSlides(this._editingPkg.id);
    } finally {
      this._busy = !1;
    }
  }
  _move(e, s, r) {
    const a = e === "slide" ? this._slides : this._pkgs, n = s + r;
    n < 0 || n >= a.length || (e === "slide" ? this._reorderSlide(s, n) : this._reorderPkg(s, n));
  }
  // Drag handlers — no reactive state writes during the drag.
  _onDragStart(e, s, r) {
    if (this.__dragFrom = s, this.__dragKind = r, e.dataTransfer) {
      e.dataTransfer.effectAllowed = "move";
      try {
        e.dataTransfer.setData("text/plain", String(s));
      } catch {
      }
    }
    e.currentTarget.classList.add("dragging");
  }
  _onDragOver(e) {
    e.preventDefault(), e.dataTransfer && (e.dataTransfer.dropEffect = "move");
  }
  _onDrop(e, s) {
    e.preventDefault();
    const r = this.__dragFrom, a = this.__dragKind;
    this.__dragFrom = null, this._clearDrag(), a === "slide" ? this._reorderSlide(r, s) : this._reorderPkg(r, s);
  }
  _onDragEnd() {
    this.__dragFrom = null, this._clearDrag();
  }
  _clearDrag() {
    this.renderRoot.querySelectorAll("tr.dragging").forEach((e) => e.classList.remove("dragging"));
  }
  render() {
    const e = this._editingPkg != null;
    return m`
      <header class="topbar">
        <a class="topbar__back" href="/dashboard/">${$i} 首頁後台</a>
        <button class="topbar__logout" @click=${() => Ce()}>登出</button>
      </header>
      <div class="wrap">
        <div class="head">
          <div class="head__titles">
            <h1>圖解知識包</h1>
            <p class="head__sub">${this._subtitle()}</p>
          </div>
          ${e ? m`<button class="btn btn--ghost" @click=${() => this._closePkg()}>返回列表</button>` : m`<button class="btn btn--primary" ?disabled=${this._busy} @click=${() => this._newPkg()}>＋ 新增知識包</button>`}
        </div>
        ${this._error ? m`<div class="alert alert--error">${this._error}</div>` : ""}
        ${e ? this._renderEditor() : this._renderList()}
      </div>
      ${this._flash ? m`<div class="toast">✓ ${this._flash}</div>` : ""}
    `;
  }
  _subtitle() {
    return this._editingPkg != null ? this._editingPkg === "new" ? "新增知識包" : "編輯知識包與其投影片" : this._busy ? m`<span class="busy-dot"></span>載入中…` : `目前共 ${this._pkgs.length} 個知識包`;
  }
  _dragRow(e, s, r, a) {
    return m`<tr draggable="true"
      @dragstart=${(n) => this._onDragStart(n, s, e)} @dragover=${this._onDragOver}
      @drop=${(n) => this._onDrop(n, s)} @dragend=${() => this._onDragEnd()}>
      <td class="drag">
        <span class="drag-grip" title="拖曳排序">⋮⋮</span>
        <span class="reorder">
          <button title="上移" ?disabled=${s === 0 || this._busy} @click=${() => this._move(e, s, -1)}>▲</button>
          <button title="下移" ?disabled=${s === r || this._busy} @click=${() => this._move(e, s, 1)}>▼</button>
        </span></td>
      ${a}
    </tr>`;
  }
  _renderList() {
    if (this._busy && !this._pkgs.length) return m`<div class="skeleton">${[0, 1, 2, 3].map(() => m`<div class="skeleton__row"></div>`)}</div>`;
    if (!this._pkgs.length) return m`<div class="empty">
      <p class="empty__title">尚無知識包</p><p class="empty__hint">點右上角「＋ 新增知識包」建立第一個。</p></div>`;
    const e = this._pkgs.length - 1;
    return m`
      <p class="list-hint">拖曳左側 ⋮⋮ 可調整順序（或用 ▲▼）；變更即時儲存。</p>
      <div class="table-card">
        <table>
          <thead><tr><th class="col-drag"></th><th>標題</th><th>顯示首頁</th><th class="col-actions">操作</th></tr></thead>
          <tbody>${this._pkgs.map((s, r) => this._dragRow("pkg", r, e, m`
            <td class="cell-strong" title=${s.title}>${s.title || "—"}</td>
            <td>${s.show_on_homepage ? "是" : "否"}</td>
            <td class="actions"><div class="row-actions">
              <button class="btn btn--ghost btn--sm" @click=${() => this._editPkg(s)}>編輯</button>
              <button class="btn btn--danger btn--sm" @click=${() => this._deletePkg(s)}>刪除</button>
            </div></td>`))}</tbody>
        </table>
      </div>`;
  }
  _renderEditor() {
    const e = this._editingPkg !== "new", s = this._slides.length - 1;
    return m`
      <div class="card">
        <div class="card__head"><h2>${e ? "編輯" : "新增"}知識包</h2></div>
        <div class="card__body">
          ${this._pkgFormFields.map((r) => He(r, this._pkgForm[r.name], this._ctx))}
          <div class="form-actions">
            <button class="btn btn--primary" ?disabled=${this._busy} @click=${() => this._savePkg()}>
              ${this._busy ? m`<span class="busy-dot"></span>儲存中…` : "儲存知識包"}</button>
            <button class="btn btn--ghost" @click=${() => this._closePkg()}>返回列表</button>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card__head">
          <h2>投影片</h2><span class="spacer"></span>
          ${e ? m`<button class="btn btn--primary btn--sm" @click=${() => this._newSlide()}>＋ 新增投影片</button>` : m`<span class="head__sub">請先儲存知識包</span>`}
        </div>
        <div class="card__body">
          ${this._editingSlide != null ? m`
            <div class="group">
              ${this._slideFormFields.map((r) => He(r, this._slideForm[r.name], this._slideCtx))}
              <div class="form-actions">
                <button class="btn btn--primary" ?disabled=${this._busy} @click=${() => this._saveSlide()}>
                  ${this._busy ? m`<span class="busy-dot"></span>儲存中…` : "儲存投影片"}</button>
                <button class="btn btn--ghost" @click=${() => this._closeSlide()}>取消</button>
              </div>
            </div>` : ""}
          ${e ? this._slides.length ? m`
            <p class="list-hint">拖曳 ⋮⋮ 調整投影片順序（或用 ▲▼）。</p>
            <table>
              <thead><tr><th class="col-drag"></th><th>替代文字</th><th class="col-actions">操作</th></tr></thead>
              <tbody>${this._slides.map((r, a) => this._dragRow("slide", a, s, m`
                <td class="cell-strong">${r.alt || "—"}</td>
                <td class="actions"><div class="row-actions">
                  <button class="btn btn--ghost btn--sm" @click=${() => this._editSlide(r)}>編輯</button>
                  <button class="btn btn--danger btn--sm" @click=${() => this._deleteSlide(r)}>刪除</button>
                </div></td>`))}</tbody>
            </table>` : m`<p class="sub__empty">尚無投影片,點上方「＋ 新增投影片」加入第一張。</p>` : ""}
        </div>
      </div>
    `;
  }
}
customElements.define("tc-dash-knowledge", Ji);
class Zi extends G {
  static styles = us`
    :host { display: block; }
    .toolbar { display: flex; gap: 6px; margin-bottom: 6px; }
    .toolbar button {
      font-family: inherit; font-size: 13px; padding: 4px 10px; cursor: pointer;
      border: 1px solid #CBD5E6; border-radius: 6px; background: #fff; color: #1B2D58;
    }
    .toolbar button:hover { background: #F1FAF9; }
    .editor {
      min-height: 96px; padding: 10px 12px; border: 1px solid #CBD5E6; border-radius: 8px;
      background: #fff; font-family: inherit; font-size: 15px; line-height: 1.6; color: #3C4453;
      outline: none;
    }
    .editor:focus { border-color: #5DC5C4; box-shadow: 0 0 0 3px rgba(93,197,196,.25); }
    .editor a { color: #30559F; text-decoration: underline; }
  `;
  static properties = { value: { type: String } };
  constructor() {
    super(), this.value = "", this._last = "", this._focused = !1;
  }
  get _ed() {
    return this.renderRoot.querySelector(".editor");
  }
  updated() {
    const e = this._ed;
    e && !this._focused && this.value !== this._last && (e.innerHTML = this.value || "", this._last = this.value);
  }
  _emit() {
    const e = this._ed;
    this._last = e.innerHTML, this.dispatchEvent(new CustomEvent("change", { detail: e.innerHTML, bubbles: !0, composed: !0 }));
  }
  _onInput() {
    this._emit();
  }
  _onFocus() {
    this._focused = !0;
  }
  _onBlur() {
    this._focused = !1;
    const e = this._ed, s = Ns(e.innerHTML);
    s !== e.innerHTML && (e.innerHTML = s), this._emit();
  }
  _createLink(e) {
    e.preventDefault();
    const s = (prompt("連結網址（http / https / mailto）：") || "").trim();
    s && (document.execCommand("createLink", !1, s), this._emit());
  }
  _removeLink(e) {
    e.preventDefault(), document.execCommand("unlink"), this._emit();
  }
  _onPaste(e) {
    e.preventDefault();
    const s = e.clipboardData ? e.clipboardData.getData("text/plain") : "";
    s && document.execCommand("insertText", !1, s);
  }
  render() {
    return m`
      <div class="toolbar">
        <button type="button" @mousedown=${this._createLink}>🔗 插入連結</button>
        <button type="button" @mousedown=${this._removeLink}>✕ 移除連結</button>
      </div>
      <div class="editor" contenteditable="true"
        @input=${this._onInput} @focus=${this._onFocus} @blur=${this._onBlur} @paste=${this._onPaste}></div>
    `;
  }
}
customElements.define("tc-richtext-editor", Zi);
const Xi = new RegExp("[\\u0000-\\u001F\\u007F]", "g");
function ct(t) {
  return String(t || "").trim().replace(/\s+/g, "").replace(/[/\\]/g, "-").replace(Xi, "").replace(/\.{2,}/g, ".").replace(/^\.+/, "");
}
const Vi = /* @__PURE__ */ new Set([
  65534,
  65535,
  131070,
  131071,
  196606,
  196607,
  262142,
  262143,
  327678,
  327679,
  393214,
  393215,
  458750,
  458751,
  524286,
  524287,
  589822,
  589823,
  655358,
  655359,
  720894,
  720895,
  786430,
  786431,
  851966,
  851967,
  917502,
  917503,
  983038,
  983039,
  1048574,
  1048575,
  1114110,
  1114111
]), S = "�";
var o;
(function(t) {
  t[t.EOF = -1] = "EOF", t[t.NULL = 0] = "NULL", t[t.TABULATION = 9] = "TABULATION", t[t.CARRIAGE_RETURN = 13] = "CARRIAGE_RETURN", t[t.LINE_FEED = 10] = "LINE_FEED", t[t.FORM_FEED = 12] = "FORM_FEED", t[t.SPACE = 32] = "SPACE", t[t.EXCLAMATION_MARK = 33] = "EXCLAMATION_MARK", t[t.QUOTATION_MARK = 34] = "QUOTATION_MARK", t[t.AMPERSAND = 38] = "AMPERSAND", t[t.APOSTROPHE = 39] = "APOSTROPHE", t[t.HYPHEN_MINUS = 45] = "HYPHEN_MINUS", t[t.SOLIDUS = 47] = "SOLIDUS", t[t.DIGIT_0 = 48] = "DIGIT_0", t[t.DIGIT_9 = 57] = "DIGIT_9", t[t.SEMICOLON = 59] = "SEMICOLON", t[t.LESS_THAN_SIGN = 60] = "LESS_THAN_SIGN", t[t.EQUALS_SIGN = 61] = "EQUALS_SIGN", t[t.GREATER_THAN_SIGN = 62] = "GREATER_THAN_SIGN", t[t.QUESTION_MARK = 63] = "QUESTION_MARK", t[t.LATIN_CAPITAL_A = 65] = "LATIN_CAPITAL_A", t[t.LATIN_CAPITAL_Z = 90] = "LATIN_CAPITAL_Z", t[t.RIGHT_SQUARE_BRACKET = 93] = "RIGHT_SQUARE_BRACKET", t[t.GRAVE_ACCENT = 96] = "GRAVE_ACCENT", t[t.LATIN_SMALL_A = 97] = "LATIN_SMALL_A", t[t.LATIN_SMALL_Z = 122] = "LATIN_SMALL_Z";
})(o || (o = {}));
const k = {
  DASH_DASH: "--",
  CDATA_START: "[CDATA[",
  DOCTYPE: "doctype",
  SCRIPT: "script",
  PUBLIC: "public",
  SYSTEM: "system"
};
function Ds(t) {
  return t >= 55296 && t <= 57343;
}
function ji(t) {
  return t >= 56320 && t <= 57343;
}
function zi(t, e) {
  return (t - 55296) * 1024 + 9216 + e;
}
function Ss(t) {
  return t !== 32 && t !== 10 && t !== 13 && t !== 9 && t !== 12 && t >= 1 && t <= 31 || t >= 127 && t <= 159;
}
function Bs(t) {
  return t >= 64976 && t <= 65007 || Vi.has(t);
}
var g;
(function(t) {
  t.controlCharacterInInputStream = "control-character-in-input-stream", t.noncharacterInInputStream = "noncharacter-in-input-stream", t.surrogateInInputStream = "surrogate-in-input-stream", t.nonVoidHtmlElementStartTagWithTrailingSolidus = "non-void-html-element-start-tag-with-trailing-solidus", t.endTagWithAttributes = "end-tag-with-attributes", t.endTagWithTrailingSolidus = "end-tag-with-trailing-solidus", t.unexpectedSolidusInTag = "unexpected-solidus-in-tag", t.unexpectedNullCharacter = "unexpected-null-character", t.unexpectedQuestionMarkInsteadOfTagName = "unexpected-question-mark-instead-of-tag-name", t.invalidFirstCharacterOfTagName = "invalid-first-character-of-tag-name", t.unexpectedEqualsSignBeforeAttributeName = "unexpected-equals-sign-before-attribute-name", t.missingEndTagName = "missing-end-tag-name", t.unexpectedCharacterInAttributeName = "unexpected-character-in-attribute-name", t.unknownNamedCharacterReference = "unknown-named-character-reference", t.missingSemicolonAfterCharacterReference = "missing-semicolon-after-character-reference", t.unexpectedCharacterAfterDoctypeSystemIdentifier = "unexpected-character-after-doctype-system-identifier", t.unexpectedCharacterInUnquotedAttributeValue = "unexpected-character-in-unquoted-attribute-value", t.eofBeforeTagName = "eof-before-tag-name", t.eofInTag = "eof-in-tag", t.missingAttributeValue = "missing-attribute-value", t.missingWhitespaceBetweenAttributes = "missing-whitespace-between-attributes", t.missingWhitespaceAfterDoctypePublicKeyword = "missing-whitespace-after-doctype-public-keyword", t.missingWhitespaceBetweenDoctypePublicAndSystemIdentifiers = "missing-whitespace-between-doctype-public-and-system-identifiers", t.missingWhitespaceAfterDoctypeSystemKeyword = "missing-whitespace-after-doctype-system-keyword", t.missingQuoteBeforeDoctypePublicIdentifier = "missing-quote-before-doctype-public-identifier", t.missingQuoteBeforeDoctypeSystemIdentifier = "missing-quote-before-doctype-system-identifier", t.missingDoctypePublicIdentifier = "missing-doctype-public-identifier", t.missingDoctypeSystemIdentifier = "missing-doctype-system-identifier", t.abruptDoctypePublicIdentifier = "abrupt-doctype-public-identifier", t.abruptDoctypeSystemIdentifier = "abrupt-doctype-system-identifier", t.cdataInHtmlContent = "cdata-in-html-content", t.incorrectlyOpenedComment = "incorrectly-opened-comment", t.eofInScriptHtmlCommentLikeText = "eof-in-script-html-comment-like-text", t.eofInDoctype = "eof-in-doctype", t.nestedComment = "nested-comment", t.abruptClosingOfEmptyComment = "abrupt-closing-of-empty-comment", t.eofInComment = "eof-in-comment", t.incorrectlyClosedComment = "incorrectly-closed-comment", t.eofInCdata = "eof-in-cdata", t.absenceOfDigitsInNumericCharacterReference = "absence-of-digits-in-numeric-character-reference", t.nullCharacterReference = "null-character-reference", t.surrogateCharacterReference = "surrogate-character-reference", t.characterReferenceOutsideUnicodeRange = "character-reference-outside-unicode-range", t.controlCharacterReference = "control-character-reference", t.noncharacterCharacterReference = "noncharacter-character-reference", t.missingWhitespaceBeforeDoctypeName = "missing-whitespace-before-doctype-name", t.missingDoctypeName = "missing-doctype-name", t.invalidCharacterSequenceAfterDoctypeName = "invalid-character-sequence-after-doctype-name", t.duplicateAttribute = "duplicate-attribute", t.nonConformingDoctype = "non-conforming-doctype", t.missingDoctype = "missing-doctype", t.misplacedDoctype = "misplaced-doctype", t.endTagWithoutMatchingOpenElement = "end-tag-without-matching-open-element", t.closingOfElementWithOpenChildElements = "closing-of-element-with-open-child-elements", t.disallowedContentInNoscriptInHead = "disallowed-content-in-noscript-in-head", t.openElementsLeftAfterEof = "open-elements-left-after-eof", t.abandonedHeadElementChild = "abandoned-head-element-child", t.misplacedStartTagForHeadElement = "misplaced-start-tag-for-head-element", t.nestedNoscriptInHead = "nested-noscript-in-head", t.eofInElementThatCanContainOnlyText = "eof-in-element-that-can-contain-only-text";
})(g || (g = {}));
const qi = 65536;
class er {
  constructor(e) {
    this.handler = e, this.html = "", this.pos = -1, this.lastGapPos = -2, this.gapStack = [], this.skipNextNewLine = !1, this.lastChunkWritten = !1, this.endOfChunkHit = !1, this.bufferWaterline = qi, this.isEol = !1, this.lineStartPos = 0, this.droppedBufferSize = 0, this.line = 1, this.lastErrOffset = -1;
  }
  /** The column on the current line. If we just saw a gap (eg. a surrogate pair), return the index before. */
  get col() {
    return this.pos - this.lineStartPos + +(this.lastGapPos !== this.pos);
  }
  get offset() {
    return this.droppedBufferSize + this.pos;
  }
  getError(e, s) {
    const { line: r, col: a, offset: n } = this, c = a + s, h = n + s;
    return {
      code: e,
      startLine: r,
      endLine: r,
      startCol: c,
      endCol: c,
      startOffset: h,
      endOffset: h
    };
  }
  _err(e) {
    this.handler.onParseError && this.lastErrOffset !== this.offset && (this.lastErrOffset = this.offset, this.handler.onParseError(this.getError(e, 0)));
  }
  _addGap() {
    this.gapStack.push(this.lastGapPos), this.lastGapPos = this.pos;
  }
  _processSurrogate(e) {
    if (this.pos !== this.html.length - 1) {
      const s = this.html.charCodeAt(this.pos + 1);
      if (ji(s))
        return this.pos++, this._addGap(), zi(e, s);
    } else if (!this.lastChunkWritten)
      return this.endOfChunkHit = !0, o.EOF;
    return this._err(g.surrogateInInputStream), e;
  }
  willDropParsedChunk() {
    return this.pos > this.bufferWaterline;
  }
  dropParsedChunk() {
    this.willDropParsedChunk() && (this.html = this.html.substring(this.pos), this.lineStartPos -= this.pos, this.droppedBufferSize += this.pos, this.pos = 0, this.lastGapPos = -2, this.gapStack.length = 0);
  }
  write(e, s) {
    this.html.length > 0 ? this.html += e : this.html = e, this.endOfChunkHit = !1, this.lastChunkWritten = s;
  }
  insertHtmlAtCurrentPos(e) {
    this.html = this.html.substring(0, this.pos + 1) + e + this.html.substring(this.pos + 1), this.endOfChunkHit = !1;
  }
  startsWith(e, s) {
    if (this.pos + e.length > this.html.length)
      return this.endOfChunkHit = !this.lastChunkWritten, !1;
    if (s)
      return this.html.startsWith(e, this.pos);
    for (let r = 0; r < e.length; r++)
      if ((this.html.charCodeAt(this.pos + r) | 32) !== e.charCodeAt(r))
        return !1;
    return !0;
  }
  peek(e) {
    const s = this.pos + e;
    if (s >= this.html.length)
      return this.endOfChunkHit = !this.lastChunkWritten, o.EOF;
    const r = this.html.charCodeAt(s);
    return r === o.CARRIAGE_RETURN ? o.LINE_FEED : r;
  }
  advance() {
    if (this.pos++, this.isEol && (this.isEol = !1, this.line++, this.lineStartPos = this.pos), this.pos >= this.html.length)
      return this.endOfChunkHit = !this.lastChunkWritten, o.EOF;
    let e = this.html.charCodeAt(this.pos);
    return e === o.CARRIAGE_RETURN ? (this.isEol = !0, this.skipNextNewLine = !0, o.LINE_FEED) : e === o.LINE_FEED && (this.isEol = !0, this.skipNextNewLine) ? (this.line--, this.skipNextNewLine = !1, this._addGap(), this.advance()) : (this.skipNextNewLine = !1, Ds(e) && (e = this._processSurrogate(e)), this.handler.onParseError === null || e > 31 && e < 127 || e === o.LINE_FEED || e === o.CARRIAGE_RETURN || e > 159 && e < 64976 || this._checkForProblematicCharacters(e), e);
  }
  _checkForProblematicCharacters(e) {
    Ss(e) ? this._err(g.controlCharacterInInputStream) : Bs(e) && this._err(g.noncharacterInInputStream);
  }
  retreat(e) {
    for (this.pos -= e; this.pos < this.lastGapPos; )
      this.lastGapPos = this.gapStack.pop(), this.pos--;
    this.isEol = !1;
  }
}
var C;
(function(t) {
  t[t.CHARACTER = 0] = "CHARACTER", t[t.NULL_CHARACTER = 1] = "NULL_CHARACTER", t[t.WHITESPACE_CHARACTER = 2] = "WHITESPACE_CHARACTER", t[t.START_TAG = 3] = "START_TAG", t[t.END_TAG = 4] = "END_TAG", t[t.COMMENT = 5] = "COMMENT", t[t.DOCTYPE = 6] = "DOCTYPE", t[t.EOF = 7] = "EOF", t[t.HIBERNATION = 8] = "HIBERNATION";
})(C || (C = {}));
function ys(t, e) {
  for (let s = t.attrs.length - 1; s >= 0; s--)
    if (t.attrs[s].name === e)
      return t.attrs[s].value;
  return null;
}
const tr = /* @__PURE__ */ new Map([
  [0, 65533],
  // C1 Unicode control character reference replacements
  [128, 8364],
  [130, 8218],
  [131, 402],
  [132, 8222],
  [133, 8230],
  [134, 8224],
  [135, 8225],
  [136, 710],
  [137, 8240],
  [138, 352],
  [139, 8249],
  [140, 338],
  [142, 381],
  [145, 8216],
  [146, 8217],
  [147, 8220],
  [148, 8221],
  [149, 8226],
  [150, 8211],
  [151, 8212],
  [152, 732],
  [153, 8482],
  [154, 353],
  [155, 8250],
  [156, 339],
  [158, 382],
  [159, 376]
]);
function sr(t) {
  return t >= 55296 && t <= 57343 || t > 1114111 ? 65533 : tr.get(t) ?? t;
}
function ir(t) {
  const e = atob(t), s = e.length & -2, r = new Uint16Array(s / 2);
  for (let a = 0, n = 0; a < s; a += 2) {
    const c = e.charCodeAt(a), h = e.charCodeAt(a + 1);
    r[n++] = c | h << 8;
  }
  return r;
}
const rr = /* @__PURE__ */ ir("QR08ALkAAgH6AYsDNQR2BO0EPgXZBQEGLAbdBxMISQrvCmQLfQurDKQNLw4fD4YPpA+6D/IPAAAAAAAAAAAAAAAAKhBMEY8TmxUWF2EYLBkxGuAa3RsJHDscWR8YIC8jSCSIJcMl6ie3Ku8rEC0CLjoupS7kLgAIRU1hYmNmZ2xtbm9wcnN0dVQAWgBeAGUAaQBzAHcAfgCBAIQAhwCSAJoAoACsALMAbABpAGcAO4DGAMZAUAA7gCYAJkBjAHUAdABlADuAwQDBQHIiZXZlAAJhAAFpeW0AcgByAGMAO4DCAMJAEGRyAADgNdgE3XIAYQB2AGUAO4DAAMBA8CFoYZFj4SFjcgBhZAAAoFMqAAFncIsAjgBvAG4ABGFmAADgNdg43fAlbHlGdW5jdGlvbgCgYSBpAG4AZwA7gMUAxUAAAWNzpACoAHIAAOA12Jzc6SFnbgCgVCJpAGwAZABlADuAwwDDQG0AbAA7gMQAxEAABGFjZWZvcnN1xQDYANoA7QDxAPYA+QD8AAABY3LJAM8AayNzbGFzaAAAoBYidgHTANUAAKDnKmUAZAAAoAYjeQARZIABY3J0AOAA5QDrAGEidXNlAACgNSLuI291bGxpcwCgLCFhAJJjcgAA4DXYBd1wAGYAAOA12Dnd5SF2ZdhiYwDyAOoAbSJwZXEAAKBOIgAHSE9hY2RlZmhpbG9yc3UXARoBHwE6AVIBVQFiAWQBZgGCAakB6QHtAfIBYwB5ACdkUABZADuAqQCpQIABY3B5ACUBKAE1AfUhdGUGYWmg0iJ0KGFsRGlmZmVyZW50aWFsRAAAoEUhbCJleXMAAKAtIQACYWVpb0EBRAFKAU0B8iFvbgxhZABpAGwAO4DHAMdAcgBjAAhhbiJpbnQAAKAwIm8AdAAKYQABZG5ZAV0BaSJsbGEAuGB0I2VyRG90ALdg8gA5AWkAp2NyImNsZQAAAkRNUFRwAXQBeQF9AW8AdAAAoJkiaSJudXMAAKCWIuwhdXMAoJUiaSJtZXMAAKCXIm8AAAFjc4cBlAFrKndpc2VDb250b3VySW50ZWdyYWwAAKAyImUjQ3VybHkAAAFEUZwBpAFvJXVibGVRdW90ZQAAoB0gdSJvdGUAAKAZIAACbG5wdbABtgHNAdgBbwBuAGWgNyIAoHQqgAFnaXQAvAHBAcUB8iJ1ZW50AKBhIm4AdAAAoC8i7yV1ckludGVncmFsAKAuIgABZnLRAdMBAKACIe8iZHVjdACgECJuLnRlckNsb2Nrd2lzZUNvbnRvdXJJbnRlZ3JhbAAAoDMi7yFzcwCgLypjAHIAAOA12J7ccABDoNMiYQBwAACgTSKABURKU1phY2VmaW9zAAsCEgIVAhgCGwIsAjQCOQI9AnMCfwNvoEUh9CJyYWhkAKARKWMAeQACZGMAeQAFZGMAeQAPZIABZ3JzACECJQIoAuchZXIAoCEgcgAAoKEhaAB2AACg5CoAAWF5MAIzAvIhb24OYRRkbAB0oAciYQCUY3IAAOA12AfdAAFhZkECawIAAWNtRQJnAvIjaXRpY2FsAAJBREdUUAJUAl8CYwJjInV0ZQC0YG8AdAFZAloC2WJiJGxlQWN1dGUA3WJyImF2ZQBgYGkibGRlANxi7yFuZACgxCJmJWVyZW50aWFsRAAAoEYhcAR9AgAAAAAAAIECjgIAABoDZgAA4DXYO91EoagAhQKJAm8AdAAAoNwgcSJ1YWwAAKBQIuIhbGUAA0NETFJVVpkCqAK1Au8C/wIRA28AbgB0AG8AdQByAEkAbgB0AGUAZwByAGEA7ADEAW8AdAKvAgAAAACwAqhgbiNBcnJvdwAAoNMhAAFlb7kC0AJmAHQAgAFBUlQAwQLGAs0CciJyb3cAAKDQIekkZ2h0QXJyb3cAoNQhZQDlACsCbgBnAAABTFLWAugC5SFmdAABQVLcAuECciJyb3cAAKD4J+kkZ2h0QXJyb3cAoPon6SRnaHRBcnJvdwCg+SdpImdodAAAAUFU9gL7AnIicm93AACg0iFlAGUAAKCoInAAQQIGAwAAAAALA3Iicm93AACg0SFvJHduQXJyb3cAAKDVIWUlcnRpY2FsQmFyAACgJSJuAAADQUJMUlRhJAM2AzoDWgNxA3oDciJyb3cAAKGTIUJVLAMwA2EAcgAAoBMpcCNBcnJvdwAAoPUhciJldmUAEWPlIWZ00gJDAwAASwMAAFIDaSVnaHRWZWN0b3IAAKBQKWUkZVZlY3RvcgAAoF4p5SJjdG9yQqC9IWEAcgAAoFYpaSJnaHQA1AFiAwAAaQNlJGVWZWN0b3IAAKBfKeUiY3RvckKgwSFhAHIAAKBXKWUAZQBBoKQiciJyb3cAAKCnIXIAcgBvAPcAtAIAAWN0gwOHA3IA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YwAAoN8i4SFycnCgtiEAoD0pgKIqImJjZG9zACsVMBU6FT4VQRVyImNhcAAAoEgqAAFhdTQVNxVwAACgRipwAACgSipvAHQAAKCNInIAAKBFKgDgKiIA/gACYWxydksVURVuFXMVcgByAG2gtyEAoDwpeQCAAWV2dwBYFWUVaRVxAHACXxUAAAAAYxVyAGUA4wAXFXUA4wAZFWUAZQAAoM4iZSJkZ2UAAKDPImUAbgA7gKQApEBlI2Fycm93AAABbHJ7FX8V5SFmdACgtiFpImdodAAAoLchZQDkAG0VAAFjaYsVkRVvAG4AaQBuAPQAkwFuAHQAAKAxImwiY3R5AACgLSOACUFIYWJjZGVmaGlqbG9yc3R1d3oAuBW7Fb8V1RXgFegV+RUKFhUWHxZUFlcWZRbFFtsW7xb7FgUXChdyAPIAtAJhAHIAAKBlKQACZ2xyc8YVyhXOFdAV5yFlcgCgICDlIXRoAKA4IfIA9QxoAHagECAAoKMiawHZFd4VYSJyb3cAAKAPKWEA4wBfAgABYXnkFecV8iFvbg9hNGQAoUYhYW/tFfQVAAFnciEC8RVyAACgyiF0InNlcQAAoHcqgAFnbG0A/xUCFgUWO4CwALBAdABhALRjcCJ0eXYAAKCxKQABaXIOFhIW8yFodACgfykA4DXYId1hAHIAAAFschsWHRYAoMMhAKDCIYACYWVnc3YAKBauAjYWOhY+Fm0AAKHEIm9zLhY0Fm4AZABzoMQi9SFpdACgZiZhIm1tYQDdY2kAbgAAoPIiAKH3AGlvQxZRFmQAZQAAgfcAO29KFksW90BuI3RpbWVzAACgxyJuAPgAUBZjAHkAUmRjAG8CXhYAAAAAYhZyAG4AAKAeI28AcAAAoA0jgAJscHR1dwBuFnEWdRaSFp4W7CFhciRgZgAA4DXYVd0AotkCZW1wc30WhBaJFo0WcQBkoFAibwB0AACgUSJpIm51cwAAoDgi7CF1cwCgFCLxInVhcmUAoKEiYgBsAGUAYgBhAHIAdwBlAGQAZwDlANcAbgCAAWFkaAClFqoWtBZyAHIAbwD3APUMbwB3AG4AYQByAHIAbwB3APMA8xVhI3Jwb29uAAABbHK8FsAWZQBmAPQAHBZpAGcAaAD0AB4WYgHJFs8WawBhAHIAbwD3AJILbwLUFgAAAADYFnIAbgAAoB8jbwBwAACgDCOAAWNvdADhFukW7BYAAXJ55RboFgDgNdi53FVkbAAAoPYp8iFvaxFhAAFkcvMW9xZvAHQAAKDxImkA5qC/JVsSAAFhaP8WAhdyAPIANQNhAPIA1wvhIm5nbGUAoKYpAAFjaQ4XEBd5AF9k5yJyYXJyAKD/JwAJRGFjZGVmZ2xtbm9wcXJzdHV4MRc4F0YXWxcyBF4XaRd5F40XrBe0F78X2RcVGCEYLRg1GEAYAAFEbzUXgRZvAPQA+BUAAWNzPBdCF3UAdABlADuA6QDpQPQhZXIAoG4qAAJhaW95TRdQF1YXWhfyIW9uG2FyAGOgViI7gOoA6kDsIW9uAKBVIk1kbwB0ABdhAAFEcmIXZhdvAHQAAKBSIgDgNdgi3XKhmipuF3QXYQB2AGUAO4DoAOhAZKCWKm8AdAAAoJgqgKGZKmlscwCAF4UXhxfuInRlcnMAoOcjAKATIWSglSpvAHQAAKCXKoABYXBzAJMXlheiF2MAcgATYXQAeQBzogUinxcAAAAAoRdlAHQAAKAFInAAMaADIDMBqRerFwCgBCAAoAUgAAFnc7AXsRdLYXAAAKACIAABZ3C4F7sXbwBuABlhZgAA4DXYVt2AAWFscwDFF8sXzxdyAHOg1SJsAACg4yl1AHMAAKBxKmkAAKG1A2x21RfYF28AbgC1Y/VjAAJjc3V24BfoF/0XEBgAAWlv5BdWF3IAYwAAoFYiaQLuFwAAAADwF+0ADQThIW50AAFnbPUX+Rd0AHIAAKCWKuUhc3MAoJUqgAFhZWkAAxgGGAoYbABzAD1gcwB0AACgXyJ2AESgYSJEAACgeCrwImFyc2wAoOUpAAFEYRkYHRhvAHQAAKBTInIAcgAAoHEpgAFjZGkAJxgqGO0XcgAAoC8hbwD0AIwCAAFhaDEYMhi3YzuA8ADwQAABbXI5GD0YbAA7gOsA60BvAACgrCCAAWNpcABGGEgYSxhsACFgcwD0ACwEAAFlb08YVxhjAHQAYQB0AGkAbwDuABoEbgBlAG4AdABpAGEAbADlADME4Ql1GAAAgRgAAIMYiBgAAAAAoRilGAAAqhgAALsYvhjRGAAA1xgnGWwAbABpAG4AZwBkAG8AdABzAGUA8QBlF3kARGRtImFsZQAAoEAmgAFpbHIAjRiRGJ0Y7CFpZwCgA/tpApcYAAAAAJoYZwAAoAD7aQBnAACgBPsA4DXYI93sIWlnAKAB++whaWcA4GYAagCAAWFsdACvGLIYthh0AACgbSZpAGcAAKAC+24AcwAAoLElbwBmAJJh8AHCGAAAxhhmAADgNdhX3QABYWvJGMwYbADsAGsEdqDUIgCg2SphI3J0aW50AACgDSoAAWFv2hgiGQABY3PeGB8ZsQPnGP0YBRkSGRUZAAAdGbID7xjyGPQY9xj5GAAA+xg7gL0AvUAAoFMhO4C8ALxAAKBVIQCgWSEAoFshswEBGQAAAxkAoFQhAKBWIbQCCxkOGQAAAAAQGTuAvgC+QACgVyEAoFwhNQAAoFghtgEZGQAAGxkAoFohAKBdITgAAKBeIWwAAKBEIHcAbgAAoCIjYwByAADgNdi73IAIRWFiY2RlZmdpamxub3JzdHYARhlKGVoZXhlmGWkZkhmWGZkZnRmgGa0ZxhnLGc8Z4BkjGmygZyIAoIwqgAFjbXAAUBlTGVgZ9SF0ZfVhbQBhAOSgswM6FgCghipyImV2ZQAfYQABaXliGWUZcgBjAB1hM2RvAHQAIWGAoWUibHFzAMYEcBl6GfGhZSLOBAAAdhlsAGEAbgD0AN8EgKF+KmNkbACBGYQZjBljAACgqSpvAHQAb6CAKmyggioAoIQqZeDbIgD+cwAAoJQqcgAA4DXYJN3noGsirATtIWVsAKA3IWMAeQBTZIChdyJFYWoApxmpGasZAKCSKgCgpSoAoKQqAAJFYWVztBm2Gb0ZwhkAoGkicABwoIoq8iFveACgiipxoIgq8aCIKrUZaQBtAACg5yJwAGYAAOA12FjdYQB2AOUAYwIAAWNp0xnWGXIAAKAKIW0AAKFzImVs3BneGQCgjioAoJAqAIM+ADtjZGxxco0E6xn0GfgZ/BkBGgABY2nvGfEZAKCnKnIAAKB6Km8AdAAAoNci0CFhcgCglSl1ImVzdAAAoHwqgAJhZGVscwAKGvQZFhrVBCAa8AEPGgAAFBpwAHIAbwD4AFkZcgAAoHgpcQAAAWxxxAQbGmwAZQBzAPMASRlpAO0A5AQAAWVuJxouGnIjdG5lcXEAAOBpIgD+xQAsGgAFQWFiY2Vma29zeUAaQxpmGmoabRqDGocalhrCGtMacgDyAMwCAAJpbG1yShpOGlAaVBpyAHMA8ABxD2YAvWBpAGwA9AASBQABZHJYGlsaYwB5AEpkAKGUIWN3YBpkGmkAcgAAoEgpAKCtIWEAcgAAoA8h6SFyYyVhgAFhbHIAcxp7Gn8a8iF0c3WgZSZpAHQAAKBlJuwhaXAAoCYg4yFvbgCguSJyAADgNdgl3XMAAAFld4wakRphInJvdwAAoCUpYSJyb3cAAKAmKYACYW1vcHIAnxqjGqcauhq+GnIAcgAAoP8h9CFodACgOyJrAAABbHKsGrMaZSRmdGFycm93AACgqSHpJGdodGFycm93AKCqIWYAAOA12Fnd4iFhcgCgFSCAAWNsdADIGswa0BpyAADgNdi93GEAcwDoAGka8iFvaydhAAFicNca2xr1IWxsAKBDIOghZW4AoBAg4Qr2GgAA/RoAAAgbExsaGwAAIRs7GwAAAAA+G2IbmRuVG6sbAACyG80b0htjAHUAdABlADuA7QDtQAChYyBpeQEbBhtyAGMAO4DuAO5AOGQAAWN4CxsNG3kANWRjAGwAO4ChAKFAAAFmcssCFhsA4DXYJt1yAGEAdgBlADuA7ADsQIChSCFpbm8AJxsyGzYbAAFpbisbLxtuAHQAAKAMKnQAAKAtIuYhaW4AoNwpdABhAACgKSHsIWlnM2GAAWFvcABDG1sbXhuAAWNndABJG0sbWRtyACthgAFlbHAAcQVRG1UbaQBuAOUAyAVhAHIA9AByBWgAMWFmAACgtyJlAGQAtWEAoggiY2ZvdGkbbRt1G3kb4SFyZQCgBSFpAG4AdKAeImkAZQAAoN0pZABvAPQAWxsAoisiY2VscIEbhRuPG5QbYQBsAACguiIAAWdyiRuNG2UAcgDzACMQ4wCCG2EicmhrAACgFyryIW9kAKA8KgACY2dwdJ8boRukG6gbeQBRZG8AbgAvYWYAAOA12FrdYQC5Y3UAZQBzAHQAO4C/AL9AAAFjabUbuRtyAADgNdi+3G4AAKIIIkVkc3bCG8QbyBvQAwCg+SJvAHQAAKD1Inag9CIAoPMiaaBiIOwhZGUpYesB1hsAANkbYwB5AFZkbAA7gO8A70AAA2NmbW9zdeYb7hvyG/Ub+hsFHAABaXnqG+0bcgBjADVhOWRyAADgNdgn3eEhdGg3YnAAZgAA4DXYW93jAf8bAAADHHIAAOA12L/c8iFjeVhk6yFjeVRkAARhY2ZnaGpvcxUcGhwiHCYcKhwtHDAcNRzwIXBhdqC6A/BjAAFleR4cIRzkIWls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ZmdobG1vcHJzdHV3CiwNLBEsHSwnLDEsQCxLLFIsYix6LIQsjyzLLOgs7Sz/LAotcgDyAAkDYQByAACgYykAAWNyFSwbLHUAdABlADuA+gD6QPIACQ1yAOMBIywAACUseQBeZHYAZQBtYQABaXkrLDAscgBjADuA+wD7QENkgAFhYmgANyw6LD0scgDyANEO7CFhY3FhYQDyAOAOAAFpckQsSCzzIWh0AKB+KQDgNdgy3XIAYQB2AGUAO4D5APlAYQFWLF8scgAAAWxyWixcLACgvyEAoL4hbABrAACggCUAAWN0Zix2LG8CbCwAAAAAcyxyAG4AZaAcI3IAAKAcI28AcAAAoA8jcgBpAACg+CUAAWFsfiyBLGMAcgBrYTuAqACoQAABZ3CILIssbwBuAHNhZgAA4DXYZt0AA2FkaGxzdZksniynLLgsuyzFLHIAcgBvAPcACQ1vAHcAbgBhAHIAcgBvAPcA2A5hI3Jwb29uAAABbHKvLLMsZQBmAPQAWyxpAGcAaAD0AF0sdQDzAKYOaQAAocUDaGzBLMIs0mNvAG4AxWPwI2Fycm93cwCgyCGAAWNpdADRLOEs5CxvAtcsAAAAAN4scgBuAGWgHSNyAACgHSNvAHAAAKAOI24AZwBvYXIAaQAAoPklYwByAADgNdjK3IABZGlyAPMs9yz6LG8AdAAAoPAi7CFkZWlhaQBmoLUlAKC0JQABYW0DLQYtcgDyAMosbAA7gPwA/EDhIm5nbGUAoKcpgAdBQkRhY2RlZmxub3Byc3oAJy0qLTAtNC2bLZ0toS2/LcMtxy3TLdgt3C3gLfwtcgDyABADYQByAHag6CoAoOkqYQBzAOgA/gIAAW5yOC08LechcnQAoJwpgANla25wcnN0AJkpSC1NLVQtXi1iLYItYQBwAHAA4QAaHG8AdABoAGkAbgDnAKEXgAFoaXIAoSmzJFotbwBwAPQAdCVooJUh7wD4JgABaXVmLWotZwBtAOEAuygAAWJwbi14LXMjZXRuZXEAceCKIgD+AODLKgD+cyNldG5lcQBx4IsiAP4A4MwqAP4AAWhyhi2KLWUAdADhABIraSNhbmdsZQAAAWxyki2WLeUhZnQAoLIiaSJnaHQAAKCzInkAMmThIXNoAKCiIoABZWxyAKcttC24LWKiKCKuLQAAAACyLWEAcgAAoLsicQAAoFoi7CFpcACg7iIAAWJ0vC1eD2EA8gBfD3IAAOA12DPddAByAOkAlS1zAHUAAAFicM0t0C0A4IIi0iAA4IMi0iBwAGYAAOA12GfdcgBvAPAAWQt0AHIA6QCaLQABY3XkLegtcgAA4DXYy9wAAWJw7C30LW4AAAFFZXUt8S0A4IoiAP5uAAABRWV/LfktAOCLIgD+6SJnemFnAKCaKYADY2Vmb3BycwANLhAuJS4pLiMuLi40LukhcmN1YQABZGkULiEuAAFiZxguHC5hAHIAAKBfKmUAcaAnIgCgWSLlIXJwAKAYIXIAAOA12DTdcABmAADgNdho3WWgQCJhAHQA6ABqD2MAcgAA4DXYzNzjCuQRUC4AAFQuAABYLmIuAAAAAGMubS5wLnQuAAAAAIguki4AAJouJxIqEnQAcgDpAB0ScgAA4DXYNd0AAUFhWy5eLnIA8gDnAnIA8gCTB75jAAFBYWYuaS5yAPIA4AJyAPIAjAdhAPAAeh5pAHMAAKD7IoABZHB0APgReS6DLgABZmx9LoAuAOA12GnddQDzAP8RaQBtAOUABBIAAUFhiy6OLnIA8gDuAnIA8gCaBwABY3GVLgoScgAA4DXYzdwAAXB0nS6hLmwAdQDzACUScgDpACASAARhY2VmaW9zdbEuvC7ELsguzC7PLtQu2S5jAAABdXm2LrsudABlADuA/QD9QE9kAAFpecAuwy5yAGMAd2FLZG4AO4ClAKVAcgAA4DXYNt1jAHkAV2RwAGYAAOA12GrdYwByAADgNdjO3AABY23dLt8ueQBOZGwAO4D/AP9AAAVhY2RlZmhpb3N38y73Lv8uAi8MLxAvEy8YLx0vIi9jInV0ZQB6YQABYXn7Lv4u8iFvbn5hN2RvAHQAfGEAAWV0Bi8KL3QAcgDmAB8QYQC2Y3IAAOA12DfdYwB5ADZk5yJyYXJyAKDdIXAAZgAA4DXYa91jAHIAAOA12M/cAAFqbiYvKC8AoA0gagAAoAwg");
var w;
(function(t) {
  t[t.VALUE_LENGTH = 49152] = "VALUE_LENGTH", t[t.FLAG13 = 8192] = "FLAG13", t[t.BRANCH_LENGTH = 8064] = "BRANCH_LENGTH", t[t.JUMP_TABLE = 127] = "JUMP_TABLE";
})(w || (w = {}));
var B;
(function(t) {
  t[t.NUM = 35] = "NUM", t[t.SEMI = 59] = "SEMI", t[t.EQUALS = 61] = "EQUALS", t[t.ZERO = 48] = "ZERO", t[t.NINE = 57] = "NINE", t[t.LOWER_A = 97] = "LOWER_A", t[t.LOWER_F = 102] = "LOWER_F", t[t.LOWER_X = 120] = "LOWER_X", t[t.LOWER_Z = 122] = "LOWER_Z", t[t.UPPER_A = 65] = "UPPER_A", t[t.UPPER_F = 70] = "UPPER_F", t[t.UPPER_Z = 90] = "UPPER_Z";
})(B || (B = {}));
const Vt = 32;
function Et(t) {
  return t >= B.ZERO && t <= B.NINE;
}
function ar(t) {
  return t >= B.UPPER_A && t <= B.UPPER_F || t >= B.LOWER_A && t <= B.LOWER_F;
}
function nr(t) {
  return t >= B.UPPER_A && t <= B.UPPER_Z || t >= B.LOWER_A && t <= B.LOWER_Z || Et(t);
}
function or(t) {
  return t === B.EQUALS || nr(t);
}
var y;
(function(t) {
  t[t.EntityStart = 0] = "EntityStart", t[t.NumericStart = 1] = "NumericStart", t[t.NumericDecimal = 2] = "NumericDecimal", t[t.NumericHex = 3] = "NumericHex", t[t.NamedEntity = 4] = "NamedEntity";
})(y || (y = {}));
var H;
(function(t) {
  t[t.Legacy = 0] = "Legacy", t[t.Strict = 1] = "Strict", t[t.Attribute = 2] = "Attribute";
})(H || (H = {}));
class Ar {
  decodeTree;
  emitCodePoint;
  errors;
  constructor(e, s, r) {
    this.decodeTree = e, this.emitCodePoint = s, this.errors = r;
  }
  /** The current state of the decoder. */
  state = y.EntityStart;
  /** Characters that were consumed while parsing an entity. */
  consumed = 1;
  /**
   * The result of the entity.
   *
   * Either the result index of a numeric entity, or the codepoint of a
   * numeric entity.
   */
  result = 0;
  /** The current index in the decode tree. */
  treeIndex = 0;
  /** The number of characters that were consumed in excess. */
  excess = 1;
  /** The mode in which the decoder is operating. */
  decodeMode = H.Strict;
  /** The number of characters that have been consumed in the current run. */
  runConsumed = 0;
  /**
   * Resets the instance to make it reusable.
   * @param decodeMode Entity decoding mode to use.
   */
  startEntity(e) {
    this.decodeMode = e, this.state = y.EntityStart, this.result = 0, this.treeIndex = 0, this.excess = 1, this.consumed = 1, this.runConsumed = 0;
  }
  /**
   * Write an entity to the decoder. This can be called multiple times with partial entities.
   * If the entity is incomplete, the decoder will return -1.
   *
   * Mirrors the implementation of `getDecoder`, but with the ability to stop decoding if the
   * entity is incomplete, and resume when the next string is written.
   * @param input The string containing the entity (or a continuation of the entity).
   * @param offset The offset at which the entity begins. Should be 0 if this is not the first call.
   * @returns The number of characters that were consumed, or -1 if the entity is incomplete.
   */
  write(e, s) {
    switch (this.state) {
      case y.EntityStart:
        return e.charCodeAt(s) === B.NUM ? (this.state = y.NumericStart, this.consumed += 1, this.stateNumericStart(e, s + 1)) : (this.state = y.NamedEntity, this.stateNamedEntity(e, s));
      case y.NumericStart:
        return this.stateNumericStart(e, s);
      case y.NumericDecimal:
        return this.stateNumericDecimal(e, s);
      case y.NumericHex:
        return this.stateNumericHex(e, s);
      case y.NamedEntity:
        return this.stateNamedEntity(e, s);
    }
  }
  /**
   * Switches between the numeric decimal and hexadecimal states.
   *
   * Equivalent to the `Numeric character reference state` in the HTML spec.
   * @param input The string containing the entity (or a continuation of the entity).
   * @param offset The current offset.
   * @returns The number of characters that were consumed, or -1 if the entity is incomplete.
   */
  stateNumericStart(e, s) {
    return s >= e.length ? -1 : (e.charCodeAt(s) | Vt) === B.LOWER_X ? (this.state = y.NumericHex, this.consumed += 1, this.stateNumericHex(e, s + 1)) : (this.state = y.NumericDecimal, this.stateNumericDecimal(e, s));
  }
  /**
   * Parses a hexadecimal numeric entity.
   *
   * Equivalent to the `Hexademical character reference state` in the HTML spec.
   * @param input The string containing the entity (or a continuation of the entity).
   * @param offset The current offset.
   * @returns The number of characters that were consumed, or -1 if the entity is incomplete.
   */
  stateNumericHex(e, s) {
    for (; s < e.length; ) {
      const r = e.charCodeAt(s);
      if (Et(r) || ar(r)) {
        const a = r <= B.NINE ? r - B.ZERO : (r | Vt) - B.LOWER_A + 10;
        this.result = this.result * 16 + a, this.consumed++, s++;
      } else
        return this.emitNumericEntity(r, 3);
    }
    return -1;
  }
  /**
   * Parses a decimal numeric entity.
   *
   * Equivalent to the `Decimal character reference state` in the HTML spec.
   * @param input The string containing the entity (or a continuation of the entity).
   * @param offset The current offset.
   * @returns The number of characters that were consumed, or -1 if the entity is incomplete.
   */
  stateNumericDecimal(e, s) {
    for (; s < e.length; ) {
      const r = e.charCodeAt(s);
      if (Et(r))
        this.result = this.result * 10 + (r - B.ZERO), this.consumed++, s++;
      else
        return this.emitNumericEntity(r, 2);
    }
    return -1;
  }
  /**
   * Validate and emit a numeric entity.
   *
   * Implements the logic from the `Hexademical character reference start
   * state` and `Numeric character reference end state` in the HTML spec.
   * @param lastCp The last code point of the entity. Used to see if the
   *               entity was terminated with a semicolon.
   * @param expectedLength The minimum number of characters that should be
   *                       consumed. Used to validate that at least one digit
   *                       was consumed.
   * @returns The number of characters that were consumed.
   */
  emitNumericEntity(e, s) {
    if (this.consumed <= s)
      return this.errors?.absenceOfDigitsInNumericCharacterReference(this.consumed), 0;
    if (e === B.SEMI)
      this.consumed += 1;
    else if (this.decodeMode === H.Strict)
      return 0;
    return this.emitCodePoint(sr(this.result), this.consumed), this.errors && (e !== B.SEMI && this.errors.missingSemicolonAfterCharacterReference(), this.errors.validateNumericCharacterReference(this.result)), this.consumed;
  }
  /**
   * Parses a named entity.
   *
   * Equivalent to the `Named character reference state` in the HTML spec.
   * @param input The string containing the entity (or a continuation of the entity).
   * @param offset The current offset.
   * @returns The number of characters that were consumed, or -1 if the entity is incomplete.
   */
  stateNamedEntity(e, s) {
    const { decodeTree: r } = this;
    let a = r[this.treeIndex], n = (a & w.VALUE_LENGTH) >> 14;
    for (; s < e.length; ) {
      if (n === 0 && (a & w.FLAG13) !== 0) {
        const h = (a & w.BRANCH_LENGTH) >> 7;
        if (this.runConsumed === 0) {
          const E = a & w.JUMP_TABLE;
          if (e.charCodeAt(s) !== E)
            return this.result === 0 ? 0 : this.emitNotTerminatedNamedEntity();
          s++, this.excess++, this.runConsumed++;
        }
        for (; this.runConsumed < h; ) {
          if (s >= e.length)
            return -1;
          const E = this.runConsumed - 1, u = r[this.treeIndex + 1 + (E >> 1)], _ = E % 2 === 0 ? u & 255 : u >> 8 & 255;
          if (e.charCodeAt(s) !== _)
            return this.runConsumed = 0, this.result === 0 ? 0 : this.emitNotTerminatedNamedEntity();
          s++, this.excess++, this.runConsumed++;
        }
        this.runConsumed = 0, this.treeIndex += 1 + (h >> 1), a = r[this.treeIndex], n = (a & w.VALUE_LENGTH) >> 14;
      }
      if (s >= e.length)
        break;
      const c = e.charCodeAt(s);
      if (c === B.SEMI && n !== 0 && (a & w.FLAG13) !== 0)
        return this.emitNamedEntityData(this.treeIndex, n, this.consumed + this.excess);
      if (this.treeIndex = cr(r, a, this.treeIndex + Math.max(1, n), c), this.treeIndex < 0)
        return this.result === 0 || // If we are parsing an attribute
        this.decodeMode === H.Attribute && // We shouldn't have consumed any characters after the entity,
        (n === 0 || // And there should be no invalid characters.
        or(c)) ? 0 : this.emitNotTerminatedNamedEntity();
      if (a = r[this.treeIndex], n = (a & w.VALUE_LENGTH) >> 14, n !== 0) {
        if (c === B.SEMI)
          return this.emitNamedEntityData(this.treeIndex, n, this.consumed + this.excess);
        this.decodeMode !== H.Strict && (a & w.FLAG13) === 0 && (this.result = this.treeIndex, this.consumed += this.excess, this.excess = 0);
      }
      s++, this.excess++;
    }
    return -1;
  }
  /**
   * Emit a named entity that was not terminated with a semicolon.
   * @returns The number of characters consumed.
   */
  emitNotTerminatedNamedEntity() {
    const { result: e, decodeTree: s } = this, r = (s[e] & w.VALUE_LENGTH) >> 14;
    return this.emitNamedEntityData(e, r, this.consumed), this.errors?.missingSemicolonAfterCharacterReference(), this.consumed;
  }
  /**
   * Emit a named entity.
   * @param result The index of the entity in the decode tree.
   * @param valueLength The number of bytes in the entity.
   * @param consumed The number of characters consumed.
   * @returns The number of characters consumed.
   */
  emitNamedEntityData(e, s, r) {
    const { decodeTree: a } = this;
    return this.emitCodePoint(s === 1 ? a[e] & ~(w.VALUE_LENGTH | w.FLAG13) : a[e + 1], r), s === 3 && this.emitCodePoint(a[e + 2], r), r;
  }
  /**
   * Signal to the parser that the end of the input was reached.
   *
   * Remaining data will be emitted and relevant errors will be produced.
   * @returns The number of characters consumed.
   */
  end() {
    switch (this.state) {
      case y.NamedEntity:
        return this.result !== 0 && (this.decodeMode !== H.Attribute || this.result === this.treeIndex) ? this.emitNotTerminatedNamedEntity() : 0;
      // Otherwise, emit a numeric entity if we have one.
      case y.NumericDecimal:
        return this.emitNumericEntity(0, 2);
      case y.NumericHex:
        return this.emitNumericEntity(0, 3);
      case y.NumericStart:
        return this.errors?.absenceOfDigitsInNumericCharacterReference(this.consumed), 0;
      case y.EntityStart:
        return 0;
    }
  }
}
function cr(t, e, s, r) {
  const a = (e & w.BRANCH_LENGTH) >> 7, n = e & w.JUMP_TABLE;
  if (a === 0)
    return n !== 0 && r === n ? s : -1;
  if (n) {
    const u = r - n;
    return u < 0 || u >= a ? -1 : t[s + u] - 1;
  }
  const c = a + 1 >> 1;
  let h = 0, E = a - 1;
  for (; h <= E; ) {
    const u = h + E >>> 1, _ = u >> 1, I = t[s + _] >> (u & 1) * 8 & 255;
    if (I < r)
      h = u + 1;
    else if (I > r)
      E = u - 1;
    else
      return t[s + c + u];
  }
  return -1;
}
var p;
(function(t) {
  t.HTML = "http://www.w3.org/1999/xhtml", t.MATHML = "http://www.w3.org/1998/Math/MathML", t.SVG = "http://www.w3.org/2000/svg", t.XLINK = "http://www.w3.org/1999/xlink", t.XML = "http://www.w3.org/XML/1998/namespace", t.XMLNS = "http://www.w3.org/2000/xmlns/";
})(p || (p = {}));
var Z;
(function(t) {
  t.TYPE = "type", t.ACTION = "action", t.ENCODING = "encoding", t.PROMPT = "prompt", t.NAME = "name", t.COLOR = "color", t.FACE = "face", t.SIZE = "size";
})(Z || (Z = {}));
var v;
(function(t) {
  t.NO_QUIRKS = "no-quirks", t.QUIRKS = "quirks", t.LIMITED_QUIRKS = "limited-quirks";
})(v || (v = {}));
var d;
(function(t) {
  t.A = "a", t.ADDRESS = "address", t.ANNOTATION_XML = "annotation-xml", t.APPLET = "applet", t.AREA = "area", t.ARTICLE = "article", t.ASIDE = "aside", t.B = "b", t.BASE = "base", t.BASEFONT = "basefont", t.BGSOUND = "bgsound", t.BIG = "big", t.BLOCKQUOTE = "blockquote", t.BODY = "body", t.BR = "br", t.BUTTON = "button", t.CAPTION = "caption", t.CENTER = "center", t.CODE = "code", t.COL = "col", t.COLGROUP = "colgroup", t.DD = "dd", t.DESC = "desc", t.DETAILS = "details", t.DIALOG = "dialog", t.DIR = "dir", t.DIV = "div", t.DL = "dl", t.DT = "dt", t.EM = "em", t.EMBED = "embed", t.FIELDSET = "fieldset", t.FIGCAPTION = "figcaption", t.FIGURE = "figure", t.FONT = "font", t.FOOTER = "footer", t.FOREIGN_OBJECT = "foreignObject", t.FORM = "form", t.FRAME = "frame", t.FRAMESET = "frameset", t.H1 = "h1", t.H2 = "h2", t.H3 = "h3", t.H4 = "h4", t.H5 = "h5", t.H6 = "h6", t.HEAD = "head", t.HEADER = "header", t.HGROUP = "hgroup", t.HR = "hr", t.HTML = "html", t.I = "i", t.IMG = "img", t.IMAGE = "image", t.INPUT = "input", t.IFRAME = "iframe", t.KEYGEN = "keygen", t.LABEL = "label", t.LI = "li", t.LINK = "link", t.LISTING = "listing", t.MAIN = "main", t.MALIGNMARK = "malignmark", t.MARQUEE = "marquee", t.MATH = "math", t.MENU = "menu", t.META = "meta", t.MGLYPH = "mglyph", t.MI = "mi", t.MO = "mo", t.MN = "mn", t.MS = "ms", t.MTEXT = "mtext", t.NAV = "nav", t.NOBR = "nobr", t.NOFRAMES = "noframes", t.NOEMBED = "noembed", t.NOSCRIPT = "noscript", t.OBJECT = "object", t.OL = "ol", t.OPTGROUP = "optgroup", t.OPTION = "option", t.P = "p", t.PARAM = "param", t.PLAINTEXT = "plaintext", t.PRE = "pre", t.RB = "rb", t.RP = "rp", t.RT = "rt", t.RTC = "rtc", t.RUBY = "ruby", t.S = "s", t.SCRIPT = "script", t.SEARCH = "search", t.SECTION = "section", t.SELECT = "select", t.SOURCE = "source", t.SMALL = "small", t.SPAN = "span", t.STRIKE = "strike", t.STRONG = "strong", t.STYLE = "style", t.SUB = "sub", t.SUMMARY = "summary", t.SUP = "sup", t.TABLE = "table", t.TBODY = "tbody", t.TEMPLATE = "template", t.TEXTAREA = "textarea", t.TFOOT = "tfoot", t.TD = "td", t.TH = "th", t.THEAD = "thead", t.TITLE = "title", t.TR = "tr", t.TRACK = "track", t.TT = "tt", t.U = "u", t.UL = "ul", t.SVG = "svg", t.VAR = "var", t.WBR = "wbr", t.XMP = "xmp";
})(d || (d = {}));
var i;
(function(t) {
  t[t.UNKNOWN = 0] = "UNKNOWN", t[t.A = 1] = "A", t[t.ADDRESS = 2] = "ADDRESS", t[t.ANNOTATION_XML = 3] = "ANNOTATION_XML", t[t.APPLET = 4] = "APPLET", t[t.AREA = 5] = "AREA", t[t.ARTICLE = 6] = "ARTICLE", t[t.ASIDE = 7] = "ASIDE", t[t.B = 8] = "B", t[t.BASE = 9] = "BASE", t[t.BASEFONT = 10] = "BASEFONT", t[t.BGSOUND = 11] = "BGSOUND", t[t.BIG = 12] = "BIG", t[t.BLOCKQUOTE = 13] = "BLOCKQUOTE", t[t.BODY = 14] = "BODY", t[t.BR = 15] = "BR", t[t.BUTTON = 16] = "BUTTON", t[t.CAPTION = 17] = "CAPTION", t[t.CENTER = 18] = "CENTER", t[t.CODE = 19] = "CODE", t[t.COL = 20] = "COL", t[t.COLGROUP = 21] = "COLGROUP", t[t.DD = 22] = "DD", t[t.DESC = 23] = "DESC", t[t.DETAILS = 24] = "DETAILS", t[t.DIALOG = 25] = "DIALOG", t[t.DIR = 26] = "DIR", t[t.DIV = 27] = "DIV", t[t.DL = 28] = "DL", t[t.DT = 29] = "DT", t[t.EM = 30] = "EM", t[t.EMBED = 31] = "EMBED", t[t.FIELDSET = 32] = "FIELDSET", t[t.FIGCAPTION = 33] = "FIGCAPTION", t[t.FIGURE = 34] = "FIGURE", t[t.FONT = 35] = "FONT", t[t.FOOTER = 36] = "FOOTER", t[t.FOREIGN_OBJECT = 37] = "FOREIGN_OBJECT", t[t.FORM = 38] = "FORM", t[t.FRAME = 39] = "FRAME", t[t.FRAMESET = 40] = "FRAMESET", t[t.H1 = 41] = "H1", t[t.H2 = 42] = "H2", t[t.H3 = 43] = "H3", t[t.H4 = 44] = "H4", t[t.H5 = 45] = "H5", t[t.H6 = 46] = "H6", t[t.HEAD = 47] = "HEAD", t[t.HEADER = 48] = "HEADER", t[t.HGROUP = 49] = "HGROUP", t[t.HR = 50] = "HR", t[t.HTML = 51] = "HTML", t[t.I = 52] = "I", t[t.IMG = 53] = "IMG", t[t.IMAGE = 54] = "IMAGE", t[t.INPUT = 55] = "INPUT", t[t.IFRAME = 56] = "IFRAME", t[t.KEYGEN = 57] = "KEYGEN", t[t.LABEL = 58] = "LABEL", t[t.LI = 59] = "LI", t[t.LINK = 60] = "LINK", t[t.LISTING = 61] = "LISTING", t[t.MAIN = 62] = "MAIN", t[t.MALIGNMARK = 63] = "MALIGNMARK", t[t.MARQUEE = 64] = "MARQUEE", t[t.MATH = 65] = "MATH", t[t.MENU = 66] = "MENU", t[t.META = 67] = "META", t[t.MGLYPH = 68] = "MGLYPH", t[t.MI = 69] = "MI", t[t.MO = 70] = "MO", t[t.MN = 71] = "MN", t[t.MS = 72] = "MS", t[t.MTEXT = 73] = "MTEXT", t[t.NAV = 74] = "NAV", t[t.NOBR = 75] = "NOBR", t[t.NOFRAMES = 76] = "NOFRAMES", t[t.NOEMBED = 77] = "NOEMBED", t[t.NOSCRIPT = 78] = "NOSCRIPT", t[t.OBJECT = 79] = "OBJECT", t[t.OL = 80] = "OL", t[t.OPTGROUP = 81] = "OPTGROUP", t[t.OPTION = 82] = "OPTION", t[t.P = 83] = "P", t[t.PARAM = 84] = "PARAM", t[t.PLAINTEXT = 85] = "PLAINTEXT", t[t.PRE = 86] = "PRE", t[t.RB = 87] = "RB", t[t.RP = 88] = "RP", t[t.RT = 89] = "RT", t[t.RTC = 90] = "RTC", t[t.RUBY = 91] = "RUBY", t[t.S = 92] = "S", t[t.SCRIPT = 93] = "SCRIPT", t[t.SEARCH = 94] = "SEARCH", t[t.SECTION = 95] = "SECTION", t[t.SELECT = 96] = "SELECT", t[t.SOURCE = 97] = "SOURCE", t[t.SMALL = 98] = "SMALL", t[t.SPAN = 99] = "SPAN", t[t.STRIKE = 100] = "STRIKE", t[t.STRONG = 101] = "STRONG", t[t.STYLE = 102] = "STYLE", t[t.SUB = 103] = "SUB", t[t.SUMMARY = 104] = "SUMMARY", t[t.SUP = 105] = "SUP", t[t.TABLE = 106] = "TABLE", t[t.TBODY = 107] = "TBODY", t[t.TEMPLATE = 108] = "TEMPLATE", t[t.TEXTAREA = 109] = "TEXTAREA", t[t.TFOOT = 110] = "TFOOT", t[t.TD = 111] = "TD", t[t.TH = 112] = "TH", t[t.THEAD = 113] = "THEAD", t[t.TITLE = 114] = "TITLE", t[t.TR = 115] = "TR", t[t.TRACK = 116] = "TRACK", t[t.TT = 117] = "TT", t[t.U = 118] = "U", t[t.UL = 119] = "UL", t[t.SVG = 120] = "SVG", t[t.VAR = 121] = "VAR", t[t.WBR = 122] = "WBR", t[t.XMP = 123] = "XMP";
})(i || (i = {}));
const lr = /* @__PURE__ */ new Map([
  [d.A, i.A],
  [d.ADDRESS, i.ADDRESS],
  [d.ANNOTATION_XML, i.ANNOTATION_XML],
  [d.APPLET, i.APPLET],
  [d.AREA, i.AREA],
  [d.ARTICLE, i.ARTICLE],
  [d.ASIDE, i.ASIDE],
  [d.B, i.B],
  [d.BASE, i.BASE],
  [d.BASEFONT, i.BASEFONT],
  [d.BGSOUND, i.BGSOUND],
  [d.BIG, i.BIG],
  [d.BLOCKQUOTE, i.BLOCKQUOTE],
  [d.BODY, i.BODY],
  [d.BR, i.BR],
  [d.BUTTON, i.BUTTON],
  [d.CAPTION, i.CAPTION],
  [d.CENTER, i.CENTER],
  [d.CODE, i.CODE],
  [d.COL, i.COL],
  [d.COLGROUP, i.COLGROUP],
  [d.DD, i.DD],
  [d.DESC, i.DESC],
  [d.DETAILS, i.DETAILS],
  [d.DIALOG, i.DIALOG],
  [d.DIR, i.DIR],
  [d.DIV, i.DIV],
  [d.DL, i.DL],
  [d.DT, i.DT],
  [d.EM, i.EM],
  [d.EMBED, i.EMBED],
  [d.FIELDSET, i.FIELDSET],
  [d.FIGCAPTION, i.FIGCAPTION],
  [d.FIGURE, i.FIGURE],
  [d.FONT, i.FONT],
  [d.FOOTER, i.FOOTER],
  [d.FOREIGN_OBJECT, i.FOREIGN_OBJECT],
  [d.FORM, i.FORM],
  [d.FRAME, i.FRAME],
  [d.FRAMESET, i.FRAMESET],
  [d.H1, i.H1],
  [d.H2, i.H2],
  [d.H3, i.H3],
  [d.H4, i.H4],
  [d.H5, i.H5],
  [d.H6, i.H6],
  [d.HEAD, i.HEAD],
  [d.HEADER, i.HEADER],
  [d.HGROUP, i.HGROUP],
  [d.HR, i.HR],
  [d.HTML, i.HTML],
  [d.I, i.I],
  [d.IMG, i.IMG],
  [d.IMAGE, i.IMAGE],
  [d.INPUT, i.INPUT],
  [d.IFRAME, i.IFRAME],
  [d.KEYGEN, i.KEYGEN],
  [d.LABEL, i.LABEL],
  [d.LI, i.LI],
  [d.LINK, i.LINK],
  [d.LISTING, i.LISTING],
  [d.MAIN, i.MAIN],
  [d.MALIGNMARK, i.MALIGNMARK],
  [d.MARQUEE, i.MARQUEE],
  [d.MATH, i.MATH],
  [d.MENU, i.MENU],
  [d.META, i.META],
  [d.MGLYPH, i.MGLYPH],
  [d.MI, i.MI],
  [d.MO, i.MO],
  [d.MN, i.MN],
  [d.MS, i.MS],
  [d.MTEXT, i.MTEXT],
  [d.NAV, i.NAV],
  [d.NOBR, i.NOBR],
  [d.NOFRAMES, i.NOFRAMES],
  [d.NOEMBED, i.NOEMBED],
  [d.NOSCRIPT, i.NOSCRIPT],
  [d.OBJECT, i.OBJECT],
  [d.OL, i.OL],
  [d.OPTGROUP, i.OPTGROUP],
  [d.OPTION, i.OPTION],
  [d.P, i.P],
  [d.PARAM, i.PARAM],
  [d.PLAINTEXT, i.PLAINTEXT],
  [d.PRE, i.PRE],
  [d.RB, i.RB],
  [d.RP, i.RP],
  [d.RT, i.RT],
  [d.RTC, i.RTC],
  [d.RUBY, i.RUBY],
  [d.S, i.S],
  [d.SCRIPT, i.SCRIPT],
  [d.SEARCH, i.SEARCH],
  [d.SECTION, i.SECTION],
  [d.SELECT, i.SELECT],
  [d.SOURCE, i.SOURCE],
  [d.SMALL, i.SMALL],
  [d.SPAN, i.SPAN],
  [d.STRIKE, i.STRIKE],
  [d.STRONG, i.STRONG],
  [d.STYLE, i.STYLE],
  [d.SUB, i.SUB],
  [d.SUMMARY, i.SUMMARY],
  [d.SUP, i.SUP],
  [d.TABLE, i.TABLE],
  [d.TBODY, i.TBODY],
  [d.TEMPLATE, i.TEMPLATE],
  [d.TEXTAREA, i.TEXTAREA],
  [d.TFOOT, i.TFOOT],
  [d.TD, i.TD],
  [d.TH, i.TH],
  [d.THEAD, i.THEAD],
  [d.TITLE, i.TITLE],
  [d.TR, i.TR],
  [d.TRACK, i.TRACK],
  [d.TT, i.TT],
  [d.U, i.U],
  [d.UL, i.UL],
  [d.SVG, i.SVG],
  [d.VAR, i.VAR],
  [d.WBR, i.WBR],
  [d.XMP, i.XMP]
]);
function Xe(t) {
  var e;
  return (e = lr.get(t)) !== null && e !== void 0 ? e : i.UNKNOWN;
}
const T = i, hr = {
  [p.HTML]: /* @__PURE__ */ new Set([
    T.ADDRESS,
    T.APPLET,
    T.AREA,
    T.ARTICLE,
    T.ASIDE,
    T.BASE,
    T.BASEFONT,
    T.BGSOUND,
    T.BLOCKQUOTE,
    T.BODY,
    T.BR,
    T.BUTTON,
    T.CAPTION,
    T.CENTER,
    T.COL,
    T.COLGROUP,
    T.DD,
    T.DETAILS,
    T.DIR,
    T.DIV,
    T.DL,
    T.DT,
    T.EMBED,
    T.FIELDSET,
    T.FIGCAPTION,
    T.FIGURE,
    T.FOOTER,
    T.FORM,
    T.FRAME,
    T.FRAMESET,
    T.H1,
    T.H2,
    T.H3,
    T.H4,
    T.H5,
    T.H6,
    T.HEAD,
    T.HEADER,
    T.HGROUP,
    T.HR,
    T.HTML,
    T.IFRAME,
    T.IMG,
    T.INPUT,
    T.LI,
    T.LINK,
    T.LISTING,
    T.MAIN,
    T.MARQUEE,
    T.MENU,
    T.META,
    T.NAV,
    T.NOEMBED,
    T.NOFRAMES,
    T.NOSCRIPT,
    T.OBJECT,
    T.OL,
    T.P,
    T.PARAM,
    T.PLAINTEXT,
    T.PRE,
    T.SCRIPT,
    T.SECTION,
    T.SELECT,
    T.SOURCE,
    T.STYLE,
    T.SUMMARY,
    T.TABLE,
    T.TBODY,
    T.TD,
    T.TEMPLATE,
    T.TEXTAREA,
    T.TFOOT,
    T.TH,
    T.THEAD,
    T.TITLE,
    T.TR,
    T.TRACK,
    T.UL,
    T.WBR,
    T.XMP
  ]),
  [p.MATHML]: /* @__PURE__ */ new Set([T.MI, T.MO, T.MN, T.MS, T.MTEXT, T.ANNOTATION_XML]),
  [p.SVG]: /* @__PURE__ */ new Set([T.TITLE, T.FOREIGN_OBJECT, T.DESC]),
  [p.XLINK]: /* @__PURE__ */ new Set(),
  [p.XML]: /* @__PURE__ */ new Set(),
  [p.XMLNS]: /* @__PURE__ */ new Set()
}, gt = /* @__PURE__ */ new Set([T.H1, T.H2, T.H3, T.H4, T.H5, T.H6]);
d.STYLE, d.SCRIPT, d.XMP, d.IFRAME, d.NOEMBED, d.NOFRAMES, d.PLAINTEXT;
var A;
(function(t) {
  t[t.DATA = 0] = "DATA", t[t.RCDATA = 1] = "RCDATA", t[t.RAWTEXT = 2] = "RAWTEXT", t[t.SCRIPT_DATA = 3] = "SCRIPT_DATA", t[t.PLAINTEXT = 4] = "PLAINTEXT", t[t.TAG_OPEN = 5] = "TAG_OPEN", t[t.END_TAG_OPEN = 6] = "END_TAG_OPEN", t[t.TAG_NAME = 7] = "TAG_NAME", t[t.RCDATA_LESS_THAN_SIGN = 8] = "RCDATA_LESS_THAN_SIGN", t[t.RCDATA_END_TAG_OPEN = 9] = "RCDATA_END_TAG_OPEN", t[t.RCDATA_END_TAG_NAME = 10] = "RCDATA_END_TAG_NAME", t[t.RAWTEXT_LESS_THAN_SIGN = 11] = "RAWTEXT_LESS_THAN_SIGN", t[t.RAWTEXT_END_TAG_OPEN = 12] = "RAWTEXT_END_TAG_OPEN", t[t.RAWTEXT_END_TAG_NAME = 13] = "RAWTEXT_END_TAG_NAME", t[t.SCRIPT_DATA_LESS_THAN_SIGN = 14] = "SCRIPT_DATA_LESS_THAN_SIGN", t[t.SCRIPT_DATA_END_TAG_OPEN = 15] = "SCRIPT_DATA_END_TAG_OPEN", t[t.SCRIPT_DATA_END_TAG_NAME = 16] = "SCRIPT_DATA_END_TAG_NAME", t[t.SCRIPT_DATA_ESCAPE_START = 17] = "SCRIPT_DATA_ESCAPE_START", t[t.SCRIPT_DATA_ESCAPE_START_DASH = 18] = "SCRIPT_DATA_ESCAPE_START_DASH", t[t.SCRIPT_DATA_ESCAPED = 19] = "SCRIPT_DATA_ESCAPED", t[t.SCRIPT_DATA_ESCAPED_DASH = 20] = "SCRIPT_DATA_ESCAPED_DASH", t[t.SCRIPT_DATA_ESCAPED_DASH_DASH = 21] = "SCRIPT_DATA_ESCAPED_DASH_DASH", t[t.SCRIPT_DATA_ESCAPED_LESS_THAN_SIGN = 22] = "SCRIPT_DATA_ESCAPED_LESS_THAN_SIGN", t[t.SCRIPT_DATA_ESCAPED_END_TAG_OPEN = 23] = "SCRIPT_DATA_ESCAPED_END_TAG_OPEN", t[t.SCRIPT_DATA_ESCAPED_END_TAG_NAME = 24] = "SCRIPT_DATA_ESCAPED_END_TAG_NAME", t[t.SCRIPT_DATA_DOUBLE_ESCAPE_START = 25] = "SCRIPT_DATA_DOUBLE_ESCAPE_START", t[t.SCRIPT_DATA_DOUBLE_ESCAPED = 26] = "SCRIPT_DATA_DOUBLE_ESCAPED", t[t.SCRIPT_DATA_DOUBLE_ESCAPED_DASH = 27] = "SCRIPT_DATA_DOUBLE_ESCAPED_DASH", t[t.SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH = 28] = "SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH", t[t.SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN = 29] = "SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN", t[t.SCRIPT_DATA_DOUBLE_ESCAPE_END = 30] = "SCRIPT_DATA_DOUBLE_ESCAPE_END", t[t.BEFORE_ATTRIBUTE_NAME = 31] = "BEFORE_ATTRIBUTE_NAME", t[t.ATTRIBUTE_NAME = 32] = "ATTRIBUTE_NAME", t[t.AFTER_ATTRIBUTE_NAME = 33] = "AFTER_ATTRIBUTE_NAME", t[t.BEFORE_ATTRIBUTE_VALUE = 34] = "BEFORE_ATTRIBUTE_VALUE", t[t.ATTRIBUTE_VALUE_DOUBLE_QUOTED = 35] = "ATTRIBUTE_VALUE_DOUBLE_QUOTED", t[t.ATTRIBUTE_VALUE_SINGLE_QUOTED = 36] = "ATTRIBUTE_VALUE_SINGLE_QUOTED", t[t.ATTRIBUTE_VALUE_UNQUOTED = 37] = "ATTRIBUTE_VALUE_UNQUOTED", t[t.AFTER_ATTRIBUTE_VALUE_QUOTED = 38] = "AFTER_ATTRIBUTE_VALUE_QUOTED", t[t.SELF_CLOSING_START_TAG = 39] = "SELF_CLOSING_START_TAG", t[t.BOGUS_COMMENT = 40] = "BOGUS_COMMENT", t[t.MARKUP_DECLARATION_OPEN = 41] = "MARKUP_DECLARATION_OPEN", t[t.COMMENT_START = 42] = "COMMENT_START", t[t.COMMENT_START_DASH = 43] = "COMMENT_START_DASH", t[t.COMMENT = 44] = "COMMENT", t[t.COMMENT_LESS_THAN_SIGN = 45] = "COMMENT_LESS_THAN_SIGN", t[t.COMMENT_LESS_THAN_SIGN_BANG = 46] = "COMMENT_LESS_THAN_SIGN_BANG", t[t.COMMENT_LESS_THAN_SIGN_BANG_DASH = 47] = "COMMENT_LESS_THAN_SIGN_BANG_DASH", t[t.COMMENT_LESS_THAN_SIGN_BANG_DASH_DASH = 48] = "COMMENT_LESS_THAN_SIGN_BANG_DASH_DASH", t[t.COMMENT_END_DASH = 49] = "COMMENT_END_DASH", t[t.COMMENT_END = 50] = "COMMENT_END", t[t.COMMENT_END_BANG = 51] = "COMMENT_END_BANG", t[t.DOCTYPE = 52] = "DOCTYPE", t[t.BEFORE_DOCTYPE_NAME = 53] = "BEFORE_DOCTYPE_NAME", t[t.DOCTYPE_NAME = 54] = "DOCTYPE_NAME", t[t.AFTER_DOCTYPE_NAME = 55] = "AFTER_DOCTYPE_NAME", t[t.AFTER_DOCTYPE_PUBLIC_KEYWORD = 56] = "AFTER_DOCTYPE_PUBLIC_KEYWORD", t[t.BEFORE_DOCTYPE_PUBLIC_IDENTIFIER = 57] = "BEFORE_DOCTYPE_PUBLIC_IDENTIFIER", t[t.DOCTYPE_PUBLIC_IDENTIFIER_DOUBLE_QUOTED = 58] = "DOCTYPE_PUBLIC_IDENTIFIER_DOUBLE_QUOTED", t[t.DOCTYPE_PUBLIC_IDENTIFIER_SINGLE_QUOTED = 59] = "DOCTYPE_PUBLIC_IDENTIFIER_SINGLE_QUOTED", t[t.AFTER_DOCTYPE_PUBLIC_IDENTIFIER = 60] = "AFTER_DOCTYPE_PUBLIC_IDENTIFIER", t[t.BETWEEN_DOCTYPE_PUBLIC_AND_SYSTEM_IDENTIFIERS = 61] = "BETWEEN_DOCTYPE_PUBLIC_AND_SYSTEM_IDENTIFIERS", t[t.AFTER_DOCTYPE_SYSTEM_KEYWORD = 62] = "AFTER_DOCTYPE_SYSTEM_KEYWORD", t[t.BEFORE_DOCTYPE_SYSTEM_IDENTIFIER = 63] = "BEFORE_DOCTYPE_SYSTEM_IDENTIFIER", t[t.DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED = 64] = "DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED", t[t.DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED = 65] = "DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED", t[t.AFTER_DOCTYPE_SYSTEM_IDENTIFIER = 66] = "AFTER_DOCTYPE_SYSTEM_IDENTIFIER", t[t.BOGUS_DOCTYPE = 67] = "BOGUS_DOCTYPE", t[t.CDATA_SECTION = 68] = "CDATA_SECTION", t[t.CDATA_SECTION_BRACKET = 69] = "CDATA_SECTION_BRACKET", t[t.CDATA_SECTION_END = 70] = "CDATA_SECTION_END", t[t.CHARACTER_REFERENCE = 71] = "CHARACTER_REFERENCE", t[t.AMBIGUOUS_AMPERSAND = 72] = "AMBIGUOUS_AMPERSAND";
})(A || (A = {}));
const F = {
  DATA: A.DATA,
  RCDATA: A.RCDATA,
  RAWTEXT: A.RAWTEXT,
  SCRIPT_DATA: A.SCRIPT_DATA,
  PLAINTEXT: A.PLAINTEXT,
  CDATA_SECTION: A.CDATA_SECTION
};
function dr(t) {
  return t >= o.DIGIT_0 && t <= o.DIGIT_9;
}
function le(t) {
  return t >= o.LATIN_CAPITAL_A && t <= o.LATIN_CAPITAL_Z;
}
function ur(t) {
  return t >= o.LATIN_SMALL_A && t <= o.LATIN_SMALL_Z;
}
function Y(t) {
  return ur(t) || le(t);
}
function jt(t) {
  return Y(t) || dr(t);
}
function ke(t) {
  return t + 32;
}
function Rs(t) {
  return t === o.SPACE || t === o.LINE_FEED || t === o.TABULATION || t === o.FORM_FEED;
}
function zt(t) {
  return Rs(t) || t === o.SOLIDUS || t === o.GREATER_THAN_SIGN;
}
function Er(t) {
  return t === o.NULL ? g.nullCharacterReference : t > 1114111 ? g.characterReferenceOutsideUnicodeRange : Ds(t) ? g.surrogateCharacterReference : Bs(t) ? g.noncharacterCharacterReference : Ss(t) || t === o.CARRIAGE_RETURN ? g.controlCharacterReference : null;
}
class gr {
  constructor(e, s) {
    this.options = e, this.handler = s, this.paused = !1, this.inLoop = !1, this.inForeignNode = !1, this.lastStartTagName = "", this.active = !1, this.state = A.DATA, this.returnState = A.DATA, this.entityStartPos = 0, this.consumedAfterSnapshot = -1, this.currentCharacterToken = null, this.currentToken = null, this.currentAttr = { name: "", value: "" }, this.preprocessor = new er(s), this.currentLocation = this.getCurrentLocation(-1), this.entityDecoder = new Ar(rr, (r, a) => {
      this.preprocessor.pos = this.entityStartPos + a - 1, this._flushCodePointConsumedAsCharacterReference(r);
    }, s.onParseError ? {
      missingSemicolonAfterCharacterReference: () => {
        this._err(g.missingSemicolonAfterCharacterReference, 1);
      },
      absenceOfDigitsInNumericCharacterReference: (r) => {
        this._err(g.absenceOfDigitsInNumericCharacterReference, this.entityStartPos - this.preprocessor.pos + r);
      },
      validateNumericCharacterReference: (r) => {
        const a = Er(r);
        a && this._err(a, 1);
      }
    } : void 0);
  }
  //Errors
  _err(e, s = 0) {
    var r, a;
    (a = (r = this.handler).onParseError) === null || a === void 0 || a.call(r, this.preprocessor.getError(e, s));
  }
  // NOTE: `offset` may never run across line boundaries.
  getCurrentLocation(e) {
    return this.options.sourceCodeLocationInfo ? {
      startLine: this.preprocessor.line,
      startCol: this.preprocessor.col - e,
      startOffset: this.preprocessor.offset - e,
      endLine: -1,
      endCol: -1,
      endOffset: -1
    } : null;
  }
  _runParsingLoop() {
    if (!this.inLoop) {
      for (this.inLoop = !0; this.active && !this.paused; ) {
        this.consumedAfterSnapshot = 0;
        const e = this._consume();
        this._ensureHibernation() || this._callState(e);
      }
      this.inLoop = !1;
    }
  }
  //API
  pause() {
    this.paused = !0;
  }
  resume(e) {
    if (!this.paused)
      throw new Error("Parser was already resumed");
    this.paused = !1, !this.inLoop && (this._runParsingLoop(), this.paused || e?.());
  }
  write(e, s, r) {
    this.active = !0, this.preprocessor.write(e, s), this._runParsingLoop(), this.paused || r?.();
  }
  insertHtmlAtCurrentPos(e) {
    this.active = !0, this.preprocessor.insertHtmlAtCurrentPos(e), this._runParsingLoop();
  }
  //Hibernation
  _ensureHibernation() {
    return this.preprocessor.endOfChunkHit ? (this.preprocessor.retreat(this.consumedAfterSnapshot), this.consumedAfterSnapshot = 0, this.active = !1, !0) : !1;
  }
  //Consumption
  _consume() {
    return this.consumedAfterSnapshot++, this.preprocessor.advance();
  }
  _advanceBy(e) {
    this.consumedAfterSnapshot += e;
    for (let s = 0; s < e; s++)
      this.preprocessor.advance();
  }
  _consumeSequenceIfMatch(e, s) {
    return this.preprocessor.startsWith(e, s) ? (this._advanceBy(e.length - 1), !0) : !1;
  }
  //Token creation
  _createStartTagToken() {
    this.currentToken = {
      type: C.START_TAG,
      tagName: "",
      tagID: i.UNKNOWN,
      selfClosing: !1,
      ackSelfClosing: !1,
      attrs: [],
      location: this.getCurrentLocation(1)
    };
  }
  _createEndTagToken() {
    this.currentToken = {
      type: C.END_TAG,
      tagName: "",
      tagID: i.UNKNOWN,
      selfClosing: !1,
      ackSelfClosing: !1,
      attrs: [],
      location: this.getCurrentLocation(2)
    };
  }
  _createCommentToken(e) {
    this.currentToken = {
      type: C.COMMENT,
      data: "",
      location: this.getCurrentLocation(e)
    };
  }
  _createDoctypeToken(e) {
    this.currentToken = {
      type: C.DOCTYPE,
      name: e,
      forceQuirks: !1,
      publicId: null,
      systemId: null,
      location: this.currentLocation
    };
  }
  _createCharacterToken(e, s) {
    this.currentCharacterToken = {
      type: e,
      chars: s,
      location: this.currentLocation
    };
  }
  //Tag attributes
  _createAttr(e) {
    this.currentAttr = {
      name: e,
      value: ""
    }, this.currentLocation = this.getCurrentLocation(0);
  }
  _leaveAttrName() {
    var e, s;
    const r = this.currentToken;
    if (ys(r, this.currentAttr.name) === null) {
      if (r.attrs.push(this.currentAttr), r.location && this.currentLocation) {
        const a = (e = (s = r.location).attrs) !== null && e !== void 0 ? e : s.attrs = /* @__PURE__ */ Object.create(null);
        a[this.currentAttr.name] = this.currentLocation, this._leaveAttrValue();
      }
    } else
      this._err(g.duplicateAttribute);
  }
  _leaveAttrValue() {
    this.currentLocation && (this.currentLocation.endLine = this.preprocessor.line, this.currentLocation.endCol = this.preprocessor.col, this.currentLocation.endOffset = this.preprocessor.offset);
  }
  //Token emission
  prepareToken(e) {
    this._emitCurrentCharacterToken(e.location), this.currentToken = null, e.location && (e.location.endLine = this.preprocessor.line, e.location.endCol = this.preprocessor.col + 1, e.location.endOffset = this.preprocessor.offset + 1), this.currentLocation = this.getCurrentLocation(-1);
  }
  emitCurrentTagToken() {
    const e = this.currentToken;
    this.prepareToken(e), e.tagID = Xe(e.tagName), e.type === C.START_TAG ? (this.lastStartTagName = e.tagName, this.handler.onStartTag(e)) : (e.attrs.length > 0 && this._err(g.endTagWithAttributes), e.selfClosing && this._err(g.endTagWithTrailingSolidus), this.handler.onEndTag(e)), this.preprocessor.dropParsedChunk();
  }
  emitCurrentComment(e) {
    this.prepareToken(e), this.handler.onComment(e), this.preprocessor.dropParsedChunk();
  }
  emitCurrentDoctype(e) {
    this.prepareToken(e), this.handler.onDoctype(e), this.preprocessor.dropParsedChunk();
  }
  _emitCurrentCharacterToken(e) {
    if (this.currentCharacterToken) {
      switch (e && this.currentCharacterToken.location && (this.currentCharacterToken.location.endLine = e.startLine, this.currentCharacterToken.location.endCol = e.startCol, this.currentCharacterToken.location.endOffset = e.startOffset), this.currentCharacterToken.type) {
        case C.CHARACTER: {
          this.handler.onCharacter(this.currentCharacterToken);
          break;
        }
        case C.NULL_CHARACTER: {
          this.handler.onNullCharacter(this.currentCharacterToken);
          break;
        }
        case C.WHITESPACE_CHARACTER: {
          this.handler.onWhitespaceCharacter(this.currentCharacterToken);
          break;
        }
      }
      this.currentCharacterToken = null;
    }
  }
  _emitEOFToken() {
    const e = this.getCurrentLocation(0);
    e && (e.endLine = e.startLine, e.endCol = e.startCol, e.endOffset = e.startOffset), this._emitCurrentCharacterToken(e), this.handler.onEof({ type: C.EOF, location: e }), this.active = !1;
  }
  //Characters emission
  //OPTIMIZATION: The specification uses only one type of character token (one token per character).
  //This causes a huge memory overhead and a lot of unnecessary parser loops. parse5 uses 3 groups of characters.
  //If we have a sequence of characters that belong to the same group, the parser can process it
  //as a single solid character token.
  //So, there are 3 types of character tokens in parse5:
  //1)TokenType.NULL_CHARACTER - \u0000-character sequences (e.g. '\u0000\u0000\u0000')
  //2)TokenType.WHITESPACE_CHARACTER - any whitespace/new-line character sequences (e.g. '\n  \r\t   \f')
  //3)TokenType.CHARACTER - any character sequence which don't belong to groups 1 and 2 (e.g. 'abcdef1234@@#$%^')
  _appendCharToCurrentCharacterToken(e, s) {
    if (this.currentCharacterToken)
      if (this.currentCharacterToken.type === e) {
        this.currentCharacterToken.chars += s;
        return;
      } else
        this.currentLocation = this.getCurrentLocation(0), this._emitCurrentCharacterToken(this.currentLocation), this.preprocessor.dropParsedChunk();
    this._createCharacterToken(e, s);
  }
  _emitCodePoint(e) {
    const s = Rs(e) ? C.WHITESPACE_CHARACTER : e === o.NULL ? C.NULL_CHARACTER : C.CHARACTER;
    this._appendCharToCurrentCharacterToken(s, e < 65536 ? String.fromCharCode(e) : String.fromCodePoint(e));
  }
  //NOTE: used when we emit characters explicitly.
  //This is always for non-whitespace and non-null characters, which allows us to avoid additional checks.
  _emitChars(e) {
    this._appendCharToCurrentCharacterToken(C.CHARACTER, e);
  }
  // Character reference helpers
  _startCharacterReference() {
    this.returnState = this.state, this.state = A.CHARACTER_REFERENCE, this.entityStartPos = this.preprocessor.pos, this.entityDecoder.startEntity(this._isCharacterReferenceInAttribute() ? H.Attribute : H.Legacy);
  }
  _isCharacterReferenceInAttribute() {
    return this.returnState === A.ATTRIBUTE_VALUE_DOUBLE_QUOTED || this.returnState === A.ATTRIBUTE_VALUE_SINGLE_QUOTED || this.returnState === A.ATTRIBUTE_VALUE_UNQUOTED;
  }
  _flushCodePointConsumedAsCharacterReference(e) {
    this._isCharacterReferenceInAttribute() ? this.currentAttr.value += String.fromCodePoint(e) : this._emitCodePoint(e);
  }
  // Calling states this way turns out to be much faster than any other approach.
  _callState(e) {
    switch (this.state) {
      case A.DATA: {
        this._stateData(e);
        break;
      }
      case A.RCDATA: {
        this._stateRcdata(e);
        break;
      }
      case A.RAWTEXT: {
        this._stateRawtext(e);
        break;
      }
      case A.SCRIPT_DATA: {
        this._stateScriptData(e);
        break;
      }
      case A.PLAINTEXT: {
        this._statePlaintext(e);
        break;
      }
      case A.TAG_OPEN: {
        this._stateTagOpen(e);
        break;
      }
      case A.END_TAG_OPEN: {
        this._stateEndTagOpen(e);
        break;
      }
      case A.TAG_NAME: {
        this._stateTagName(e);
        break;
      }
      case A.RCDATA_LESS_THAN_SIGN: {
        this._stateRcdataLessThanSign(e);
        break;
      }
      case A.RCDATA_END_TAG_OPEN: {
        this._stateRcdataEndTagOpen(e);
        break;
      }
      case A.RCDATA_END_TAG_NAME: {
        this._stateRcdataEndTagName(e);
        break;
      }
      case A.RAWTEXT_LESS_THAN_SIGN: {
        this._stateRawtextLessThanSign(e);
        break;
      }
      case A.RAWTEXT_END_TAG_OPEN: {
        this._stateRawtextEndTagOpen(e);
        break;
      }
      case A.RAWTEXT_END_TAG_NAME: {
        this._stateRawtextEndTagName(e);
        break;
      }
      case A.SCRIPT_DATA_LESS_THAN_SIGN: {
        this._stateScriptDataLessThanSign(e);
        break;
      }
      case A.SCRIPT_DATA_END_TAG_OPEN: {
        this._stateScriptDataEndTagOpen(e);
        break;
      }
      case A.SCRIPT_DATA_END_TAG_NAME: {
        this._stateScriptDataEndTagName(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPE_START: {
        this._stateScriptDataEscapeStart(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPE_START_DASH: {
        this._stateScriptDataEscapeStartDash(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPED: {
        this._stateScriptDataEscaped(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPED_DASH: {
        this._stateScriptDataEscapedDash(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPED_DASH_DASH: {
        this._stateScriptDataEscapedDashDash(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPED_LESS_THAN_SIGN: {
        this._stateScriptDataEscapedLessThanSign(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPED_END_TAG_OPEN: {
        this._stateScriptDataEscapedEndTagOpen(e);
        break;
      }
      case A.SCRIPT_DATA_ESCAPED_END_TAG_NAME: {
        this._stateScriptDataEscapedEndTagName(e);
        break;
      }
      case A.SCRIPT_DATA_DOUBLE_ESCAPE_START: {
        this._stateScriptDataDoubleEscapeStart(e);
        break;
      }
      case A.SCRIPT_DATA_DOUBLE_ESCAPED: {
        this._stateScriptDataDoubleEscaped(e);
        break;
      }
      case A.SCRIPT_DATA_DOUBLE_ESCAPED_DASH: {
        this._stateScriptDataDoubleEscapedDash(e);
        break;
      }
      case A.SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH: {
        this._stateScriptDataDoubleEscapedDashDash(e);
        break;
      }
      case A.SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN: {
        this._stateScriptDataDoubleEscapedLessThanSign(e);
        break;
      }
      case A.SCRIPT_DATA_DOUBLE_ESCAPE_END: {
        this._stateScriptDataDoubleEscapeEnd(e);
        break;
      }
      case A.BEFORE_ATTRIBUTE_NAME: {
        this._stateBeforeAttributeName(e);
        break;
      }
      case A.ATTRIBUTE_NAME: {
        this._stateAttributeName(e);
        break;
      }
      case A.AFTER_ATTRIBUTE_NAME: {
        this._stateAfterAttributeName(e);
        break;
      }
      case A.BEFORE_ATTRIBUTE_VALUE: {
        this._stateBeforeAttributeValue(e);
        break;
      }
      case A.ATTRIBUTE_VALUE_DOUBLE_QUOTED: {
        this._stateAttributeValueDoubleQuoted(e);
        break;
      }
      case A.ATTRIBUTE_VALUE_SINGLE_QUOTED: {
        this._stateAttributeValueSingleQuoted(e);
        break;
      }
      case A.ATTRIBUTE_VALUE_UNQUOTED: {
        this._stateAttributeValueUnquoted(e);
        break;
      }
      case A.AFTER_ATTRIBUTE_VALUE_QUOTED: {
        this._stateAfterAttributeValueQuoted(e);
        break;
      }
      case A.SELF_CLOSING_START_TAG: {
        this._stateSelfClosingStartTag(e);
        break;
      }
      case A.BOGUS_COMMENT: {
        this._stateBogusComment(e);
        break;
      }
      case A.MARKUP_DECLARATION_OPEN: {
        this._stateMarkupDeclarationOpen(e);
        break;
      }
      case A.COMMENT_START: {
        this._stateCommentStart(e);
        break;
      }
      case A.COMMENT_START_DASH: {
        this._stateCommentStartDash(e);
        break;
      }
      case A.COMMENT: {
        this._stateComment(e);
        break;
      }
      case A.COMMENT_LESS_THAN_SIGN: {
        this._stateCommentLessThanSign(e);
        break;
      }
      case A.COMMENT_LESS_THAN_SIGN_BANG: {
        this._stateCommentLessThanSignBang(e);
        break;
      }
      case A.COMMENT_LESS_THAN_SIGN_BANG_DASH: {
        this._stateCommentLessThanSignBangDash(e);
        break;
      }
      case A.COMMENT_LESS_THAN_SIGN_BANG_DASH_DASH: {
        this._stateCommentLessThanSignBangDashDash(e);
        break;
      }
      case A.COMMENT_END_DASH: {
        this._stateCommentEndDash(e);
        break;
      }
      case A.COMMENT_END: {
        this._stateCommentEnd(e);
        break;
      }
      case A.COMMENT_END_BANG: {
        this._stateCommentEndBang(e);
        break;
      }
      case A.DOCTYPE: {
        this._stateDoctype(e);
        break;
      }
      case A.BEFORE_DOCTYPE_NAME: {
        this._stateBeforeDoctypeName(e);
        break;
      }
      case A.DOCTYPE_NAME: {
        this._stateDoctypeName(e);
        break;
      }
      case A.AFTER_DOCTYPE_NAME: {
        this._stateAfterDoctypeName(e);
        break;
      }
      case A.AFTER_DOCTYPE_PUBLIC_KEYWORD: {
        this._stateAfterDoctypePublicKeyword(e);
        break;
      }
      case A.BEFORE_DOCTYPE_PUBLIC_IDENTIFIER: {
        this._stateBeforeDoctypePublicIdentifier(e);
        break;
      }
      case A.DOCTYPE_PUBLIC_IDENTIFIER_DOUBLE_QUOTED: {
        this._stateDoctypePublicIdentifierDoubleQuoted(e);
        break;
      }
      case A.DOCTYPE_PUBLIC_IDENTIFIER_SINGLE_QUOTED: {
        this._stateDoctypePublicIdentifierSingleQuoted(e);
        break;
      }
      case A.AFTER_DOCTYPE_PUBLIC_IDENTIFIER: {
        this._stateAfterDoctypePublicIdentifier(e);
        break;
      }
      case A.BETWEEN_DOCTYPE_PUBLIC_AND_SYSTEM_IDENTIFIERS: {
        this._stateBetweenDoctypePublicAndSystemIdentifiers(e);
        break;
      }
      case A.AFTER_DOCTYPE_SYSTEM_KEYWORD: {
        this._stateAfterDoctypeSystemKeyword(e);
        break;
      }
      case A.BEFORE_DOCTYPE_SYSTEM_IDENTIFIER: {
        this._stateBeforeDoctypeSystemIdentifier(e);
        break;
      }
      case A.DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED: {
        this._stateDoctypeSystemIdentifierDoubleQuoted(e);
        break;
      }
      case A.DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED: {
        this._stateDoctypeSystemIdentifierSingleQuoted(e);
        break;
      }
      case A.AFTER_DOCTYPE_SYSTEM_IDENTIFIER: {
        this._stateAfterDoctypeSystemIdentifier(e);
        break;
      }
      case A.BOGUS_DOCTYPE: {
        this._stateBogusDoctype(e);
        break;
      }
      case A.CDATA_SECTION: {
        this._stateCdataSection(e);
        break;
      }
      case A.CDATA_SECTION_BRACKET: {
        this._stateCdataSectionBracket(e);
        break;
      }
      case A.CDATA_SECTION_END: {
        this._stateCdataSectionEnd(e);
        break;
      }
      case A.CHARACTER_REFERENCE: {
        this._stateCharacterReference();
        break;
      }
      case A.AMBIGUOUS_AMPERSAND: {
        this._stateAmbiguousAmpersand(e);
        break;
      }
      default:
        throw new Error("Unknown state");
    }
  }
  // State machine
  // Data state
  //------------------------------------------------------------------
  _stateData(e) {
    switch (e) {
      case o.LESS_THAN_SIGN: {
        this.state = A.TAG_OPEN;
        break;
      }
      case o.AMPERSAND: {
        this._startCharacterReference();
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitCodePoint(e);
        break;
      }
      case o.EOF: {
        this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  //  RCDATA state
  //------------------------------------------------------------------
  _stateRcdata(e) {
    switch (e) {
      case o.AMPERSAND: {
        this._startCharacterReference();
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.RCDATA_LESS_THAN_SIGN;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // RAWTEXT state
  //------------------------------------------------------------------
  _stateRawtext(e) {
    switch (e) {
      case o.LESS_THAN_SIGN: {
        this.state = A.RAWTEXT_LESS_THAN_SIGN;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // Script data state
  //------------------------------------------------------------------
  _stateScriptData(e) {
    switch (e) {
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_LESS_THAN_SIGN;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // PLAINTEXT state
  //------------------------------------------------------------------
  _statePlaintext(e) {
    switch (e) {
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // Tag open state
  //------------------------------------------------------------------
  _stateTagOpen(e) {
    if (Y(e))
      this._createStartTagToken(), this.state = A.TAG_NAME, this._stateTagName(e);
    else
      switch (e) {
        case o.EXCLAMATION_MARK: {
          this.state = A.MARKUP_DECLARATION_OPEN;
          break;
        }
        case o.SOLIDUS: {
          this.state = A.END_TAG_OPEN;
          break;
        }
        case o.QUESTION_MARK: {
          this._err(g.unexpectedQuestionMarkInsteadOfTagName), this._createCommentToken(1), this.state = A.BOGUS_COMMENT, this._stateBogusComment(e);
          break;
        }
        case o.EOF: {
          this._err(g.eofBeforeTagName), this._emitChars("<"), this._emitEOFToken();
          break;
        }
        default:
          this._err(g.invalidFirstCharacterOfTagName), this._emitChars("<"), this.state = A.DATA, this._stateData(e);
      }
  }
  // End tag open state
  //------------------------------------------------------------------
  _stateEndTagOpen(e) {
    if (Y(e))
      this._createEndTagToken(), this.state = A.TAG_NAME, this._stateTagName(e);
    else
      switch (e) {
        case o.GREATER_THAN_SIGN: {
          this._err(g.missingEndTagName), this.state = A.DATA;
          break;
        }
        case o.EOF: {
          this._err(g.eofBeforeTagName), this._emitChars("</"), this._emitEOFToken();
          break;
        }
        default:
          this._err(g.invalidFirstCharacterOfTagName), this._createCommentToken(2), this.state = A.BOGUS_COMMENT, this._stateBogusComment(e);
      }
  }
  // Tag name state
  //------------------------------------------------------------------
  _stateTagName(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this.state = A.BEFORE_ATTRIBUTE_NAME;
        break;
      }
      case o.SOLIDUS: {
        this.state = A.SELF_CLOSING_START_TAG;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentTagToken();
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.tagName += S;
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        s.tagName += String.fromCodePoint(le(e) ? ke(e) : e);
    }
  }
  // RCDATA less-than sign state
  //------------------------------------------------------------------
  _stateRcdataLessThanSign(e) {
    e === o.SOLIDUS ? this.state = A.RCDATA_END_TAG_OPEN : (this._emitChars("<"), this.state = A.RCDATA, this._stateRcdata(e));
  }
  // RCDATA end tag open state
  //------------------------------------------------------------------
  _stateRcdataEndTagOpen(e) {
    Y(e) ? (this.state = A.RCDATA_END_TAG_NAME, this._stateRcdataEndTagName(e)) : (this._emitChars("</"), this.state = A.RCDATA, this._stateRcdata(e));
  }
  handleSpecialEndTag(e) {
    if (!this.preprocessor.startsWith(this.lastStartTagName, !1))
      return !this._ensureHibernation();
    this._createEndTagToken();
    const s = this.currentToken;
    switch (s.tagName = this.lastStartTagName, this.preprocessor.peek(this.lastStartTagName.length)) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        return this._advanceBy(this.lastStartTagName.length), this.state = A.BEFORE_ATTRIBUTE_NAME, !1;
      case o.SOLIDUS:
        return this._advanceBy(this.lastStartTagName.length), this.state = A.SELF_CLOSING_START_TAG, !1;
      case o.GREATER_THAN_SIGN:
        return this._advanceBy(this.lastStartTagName.length), this.emitCurrentTagToken(), this.state = A.DATA, !1;
      default:
        return !this._ensureHibernation();
    }
  }
  // RCDATA end tag name state
  //------------------------------------------------------------------
  _stateRcdataEndTagName(e) {
    this.handleSpecialEndTag(e) && (this._emitChars("</"), this.state = A.RCDATA, this._stateRcdata(e));
  }
  // RAWTEXT less-than sign state
  //------------------------------------------------------------------
  _stateRawtextLessThanSign(e) {
    e === o.SOLIDUS ? this.state = A.RAWTEXT_END_TAG_OPEN : (this._emitChars("<"), this.state = A.RAWTEXT, this._stateRawtext(e));
  }
  // RAWTEXT end tag open state
  //------------------------------------------------------------------
  _stateRawtextEndTagOpen(e) {
    Y(e) ? (this.state = A.RAWTEXT_END_TAG_NAME, this._stateRawtextEndTagName(e)) : (this._emitChars("</"), this.state = A.RAWTEXT, this._stateRawtext(e));
  }
  // RAWTEXT end tag name state
  //------------------------------------------------------------------
  _stateRawtextEndTagName(e) {
    this.handleSpecialEndTag(e) && (this._emitChars("</"), this.state = A.RAWTEXT, this._stateRawtext(e));
  }
  // Script data less-than sign state
  //------------------------------------------------------------------
  _stateScriptDataLessThanSign(e) {
    switch (e) {
      case o.SOLIDUS: {
        this.state = A.SCRIPT_DATA_END_TAG_OPEN;
        break;
      }
      case o.EXCLAMATION_MARK: {
        this.state = A.SCRIPT_DATA_ESCAPE_START, this._emitChars("<!");
        break;
      }
      default:
        this._emitChars("<"), this.state = A.SCRIPT_DATA, this._stateScriptData(e);
    }
  }
  // Script data end tag open state
  //------------------------------------------------------------------
  _stateScriptDataEndTagOpen(e) {
    Y(e) ? (this.state = A.SCRIPT_DATA_END_TAG_NAME, this._stateScriptDataEndTagName(e)) : (this._emitChars("</"), this.state = A.SCRIPT_DATA, this._stateScriptData(e));
  }
  // Script data end tag name state
  //------------------------------------------------------------------
  _stateScriptDataEndTagName(e) {
    this.handleSpecialEndTag(e) && (this._emitChars("</"), this.state = A.SCRIPT_DATA, this._stateScriptData(e));
  }
  // Script data escape start state
  //------------------------------------------------------------------
  _stateScriptDataEscapeStart(e) {
    e === o.HYPHEN_MINUS ? (this.state = A.SCRIPT_DATA_ESCAPE_START_DASH, this._emitChars("-")) : (this.state = A.SCRIPT_DATA, this._stateScriptData(e));
  }
  // Script data escape start dash state
  //------------------------------------------------------------------
  _stateScriptDataEscapeStartDash(e) {
    e === o.HYPHEN_MINUS ? (this.state = A.SCRIPT_DATA_ESCAPED_DASH_DASH, this._emitChars("-")) : (this.state = A.SCRIPT_DATA, this._stateScriptData(e));
  }
  // Script data escaped state
  //------------------------------------------------------------------
  _stateScriptDataEscaped(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.SCRIPT_DATA_ESCAPED_DASH, this._emitChars("-");
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_ESCAPED_LESS_THAN_SIGN;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._err(g.eofInScriptHtmlCommentLikeText), this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // Script data escaped dash state
  //------------------------------------------------------------------
  _stateScriptDataEscapedDash(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.SCRIPT_DATA_ESCAPED_DASH_DASH, this._emitChars("-");
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_ESCAPED_LESS_THAN_SIGN;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.state = A.SCRIPT_DATA_ESCAPED, this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._err(g.eofInScriptHtmlCommentLikeText), this._emitEOFToken();
        break;
      }
      default:
        this.state = A.SCRIPT_DATA_ESCAPED, this._emitCodePoint(e);
    }
  }
  // Script data escaped dash dash state
  //------------------------------------------------------------------
  _stateScriptDataEscapedDashDash(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this._emitChars("-");
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_ESCAPED_LESS_THAN_SIGN;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.SCRIPT_DATA, this._emitChars(">");
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.state = A.SCRIPT_DATA_ESCAPED, this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._err(g.eofInScriptHtmlCommentLikeText), this._emitEOFToken();
        break;
      }
      default:
        this.state = A.SCRIPT_DATA_ESCAPED, this._emitCodePoint(e);
    }
  }
  // Script data escaped less-than sign state
  //------------------------------------------------------------------
  _stateScriptDataEscapedLessThanSign(e) {
    e === o.SOLIDUS ? this.state = A.SCRIPT_DATA_ESCAPED_END_TAG_OPEN : Y(e) ? (this._emitChars("<"), this.state = A.SCRIPT_DATA_DOUBLE_ESCAPE_START, this._stateScriptDataDoubleEscapeStart(e)) : (this._emitChars("<"), this.state = A.SCRIPT_DATA_ESCAPED, this._stateScriptDataEscaped(e));
  }
  // Script data escaped end tag open state
  //------------------------------------------------------------------
  _stateScriptDataEscapedEndTagOpen(e) {
    Y(e) ? (this.state = A.SCRIPT_DATA_ESCAPED_END_TAG_NAME, this._stateScriptDataEscapedEndTagName(e)) : (this._emitChars("</"), this.state = A.SCRIPT_DATA_ESCAPED, this._stateScriptDataEscaped(e));
  }
  // Script data escaped end tag name state
  //------------------------------------------------------------------
  _stateScriptDataEscapedEndTagName(e) {
    this.handleSpecialEndTag(e) && (this._emitChars("</"), this.state = A.SCRIPT_DATA_ESCAPED, this._stateScriptDataEscaped(e));
  }
  // Script data double escape start state
  //------------------------------------------------------------------
  _stateScriptDataDoubleEscapeStart(e) {
    if (this.preprocessor.startsWith(k.SCRIPT, !1) && zt(this.preprocessor.peek(k.SCRIPT.length))) {
      this._emitCodePoint(e);
      for (let s = 0; s < k.SCRIPT.length; s++)
        this._emitCodePoint(this._consume());
      this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED;
    } else this._ensureHibernation() || (this.state = A.SCRIPT_DATA_ESCAPED, this._stateScriptDataEscaped(e));
  }
  // Script data double escaped state
  //------------------------------------------------------------------
  _stateScriptDataDoubleEscaped(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED_DASH, this._emitChars("-");
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN, this._emitChars("<");
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._err(g.eofInScriptHtmlCommentLikeText), this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // Script data double escaped dash state
  //------------------------------------------------------------------
  _stateScriptDataDoubleEscapedDash(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH, this._emitChars("-");
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN, this._emitChars("<");
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED, this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._err(g.eofInScriptHtmlCommentLikeText), this._emitEOFToken();
        break;
      }
      default:
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED, this._emitCodePoint(e);
    }
  }
  // Script data double escaped dash dash state
  //------------------------------------------------------------------
  _stateScriptDataDoubleEscapedDashDash(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this._emitChars("-");
        break;
      }
      case o.LESS_THAN_SIGN: {
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN, this._emitChars("<");
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.SCRIPT_DATA, this._emitChars(">");
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED, this._emitChars(S);
        break;
      }
      case o.EOF: {
        this._err(g.eofInScriptHtmlCommentLikeText), this._emitEOFToken();
        break;
      }
      default:
        this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED, this._emitCodePoint(e);
    }
  }
  // Script data double escaped less-than sign state
  //------------------------------------------------------------------
  _stateScriptDataDoubleEscapedLessThanSign(e) {
    e === o.SOLIDUS ? (this.state = A.SCRIPT_DATA_DOUBLE_ESCAPE_END, this._emitChars("/")) : (this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED, this._stateScriptDataDoubleEscaped(e));
  }
  // Script data double escape end state
  //------------------------------------------------------------------
  _stateScriptDataDoubleEscapeEnd(e) {
    if (this.preprocessor.startsWith(k.SCRIPT, !1) && zt(this.preprocessor.peek(k.SCRIPT.length))) {
      this._emitCodePoint(e);
      for (let s = 0; s < k.SCRIPT.length; s++)
        this._emitCodePoint(this._consume());
      this.state = A.SCRIPT_DATA_ESCAPED;
    } else this._ensureHibernation() || (this.state = A.SCRIPT_DATA_DOUBLE_ESCAPED, this._stateScriptDataDoubleEscaped(e));
  }
  // Before attribute name state
  //------------------------------------------------------------------
  _stateBeforeAttributeName(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.SOLIDUS:
      case o.GREATER_THAN_SIGN:
      case o.EOF: {
        this.state = A.AFTER_ATTRIBUTE_NAME, this._stateAfterAttributeName(e);
        break;
      }
      case o.EQUALS_SIGN: {
        this._err(g.unexpectedEqualsSignBeforeAttributeName), this._createAttr("="), this.state = A.ATTRIBUTE_NAME;
        break;
      }
      default:
        this._createAttr(""), this.state = A.ATTRIBUTE_NAME, this._stateAttributeName(e);
    }
  }
  // Attribute name state
  //------------------------------------------------------------------
  _stateAttributeName(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
      case o.SOLIDUS:
      case o.GREATER_THAN_SIGN:
      case o.EOF: {
        this._leaveAttrName(), this.state = A.AFTER_ATTRIBUTE_NAME, this._stateAfterAttributeName(e);
        break;
      }
      case o.EQUALS_SIGN: {
        this._leaveAttrName(), this.state = A.BEFORE_ATTRIBUTE_VALUE;
        break;
      }
      case o.QUOTATION_MARK:
      case o.APOSTROPHE:
      case o.LESS_THAN_SIGN: {
        this._err(g.unexpectedCharacterInAttributeName), this.currentAttr.name += String.fromCodePoint(e);
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.currentAttr.name += S;
        break;
      }
      default:
        this.currentAttr.name += String.fromCodePoint(le(e) ? ke(e) : e);
    }
  }
  // After attribute name state
  //------------------------------------------------------------------
  _stateAfterAttributeName(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.SOLIDUS: {
        this.state = A.SELF_CLOSING_START_TAG;
        break;
      }
      case o.EQUALS_SIGN: {
        this.state = A.BEFORE_ATTRIBUTE_VALUE;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentTagToken();
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        this._createAttr(""), this.state = A.ATTRIBUTE_NAME, this._stateAttributeName(e);
    }
  }
  // Before attribute value state
  //------------------------------------------------------------------
  _stateBeforeAttributeValue(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.QUOTATION_MARK: {
        this.state = A.ATTRIBUTE_VALUE_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        this.state = A.ATTRIBUTE_VALUE_SINGLE_QUOTED;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.missingAttributeValue), this.state = A.DATA, this.emitCurrentTagToken();
        break;
      }
      default:
        this.state = A.ATTRIBUTE_VALUE_UNQUOTED, this._stateAttributeValueUnquoted(e);
    }
  }
  // Attribute value (double-quoted) state
  //------------------------------------------------------------------
  _stateAttributeValueDoubleQuoted(e) {
    switch (e) {
      case o.QUOTATION_MARK: {
        this.state = A.AFTER_ATTRIBUTE_VALUE_QUOTED;
        break;
      }
      case o.AMPERSAND: {
        this._startCharacterReference();
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.currentAttr.value += S;
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        this.currentAttr.value += String.fromCodePoint(e);
    }
  }
  // Attribute value (single-quoted) state
  //------------------------------------------------------------------
  _stateAttributeValueSingleQuoted(e) {
    switch (e) {
      case o.APOSTROPHE: {
        this.state = A.AFTER_ATTRIBUTE_VALUE_QUOTED;
        break;
      }
      case o.AMPERSAND: {
        this._startCharacterReference();
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.currentAttr.value += S;
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        this.currentAttr.value += String.fromCodePoint(e);
    }
  }
  // Attribute value (unquoted) state
  //------------------------------------------------------------------
  _stateAttributeValueUnquoted(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this._leaveAttrValue(), this.state = A.BEFORE_ATTRIBUTE_NAME;
        break;
      }
      case o.AMPERSAND: {
        this._startCharacterReference();
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._leaveAttrValue(), this.state = A.DATA, this.emitCurrentTagToken();
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), this.currentAttr.value += S;
        break;
      }
      case o.QUOTATION_MARK:
      case o.APOSTROPHE:
      case o.LESS_THAN_SIGN:
      case o.EQUALS_SIGN:
      case o.GRAVE_ACCENT: {
        this._err(g.unexpectedCharacterInUnquotedAttributeValue), this.currentAttr.value += String.fromCodePoint(e);
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        this.currentAttr.value += String.fromCodePoint(e);
    }
  }
  // After attribute value (quoted) state
  //------------------------------------------------------------------
  _stateAfterAttributeValueQuoted(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this._leaveAttrValue(), this.state = A.BEFORE_ATTRIBUTE_NAME;
        break;
      }
      case o.SOLIDUS: {
        this._leaveAttrValue(), this.state = A.SELF_CLOSING_START_TAG;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._leaveAttrValue(), this.state = A.DATA, this.emitCurrentTagToken();
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingWhitespaceBetweenAttributes), this.state = A.BEFORE_ATTRIBUTE_NAME, this._stateBeforeAttributeName(e);
    }
  }
  // Self-closing start tag state
  //------------------------------------------------------------------
  _stateSelfClosingStartTag(e) {
    switch (e) {
      case o.GREATER_THAN_SIGN: {
        const s = this.currentToken;
        s.selfClosing = !0, this.state = A.DATA, this.emitCurrentTagToken();
        break;
      }
      case o.EOF: {
        this._err(g.eofInTag), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.unexpectedSolidusInTag), this.state = A.BEFORE_ATTRIBUTE_NAME, this._stateBeforeAttributeName(e);
    }
  }
  // Bogus comment state
  //------------------------------------------------------------------
  _stateBogusComment(e) {
    const s = this.currentToken;
    switch (e) {
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentComment(s);
        break;
      }
      case o.EOF: {
        this.emitCurrentComment(s), this._emitEOFToken();
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.data += S;
        break;
      }
      default:
        s.data += String.fromCodePoint(e);
    }
  }
  // Markup declaration open state
  //------------------------------------------------------------------
  _stateMarkupDeclarationOpen(e) {
    this._consumeSequenceIfMatch(k.DASH_DASH, !0) ? (this._createCommentToken(k.DASH_DASH.length + 1), this.state = A.COMMENT_START) : this._consumeSequenceIfMatch(k.DOCTYPE, !1) ? (this.currentLocation = this.getCurrentLocation(k.DOCTYPE.length + 1), this.state = A.DOCTYPE) : this._consumeSequenceIfMatch(k.CDATA_START, !0) ? this.inForeignNode ? this.state = A.CDATA_SECTION : (this._err(g.cdataInHtmlContent), this._createCommentToken(k.CDATA_START.length + 1), this.currentToken.data = "[CDATA[", this.state = A.BOGUS_COMMENT) : this._ensureHibernation() || (this._err(g.incorrectlyOpenedComment), this._createCommentToken(2), this.state = A.BOGUS_COMMENT, this._stateBogusComment(e));
  }
  // Comment start state
  //------------------------------------------------------------------
  _stateCommentStart(e) {
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.COMMENT_START_DASH;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.abruptClosingOfEmptyComment), this.state = A.DATA;
        const s = this.currentToken;
        this.emitCurrentComment(s);
        break;
      }
      default:
        this.state = A.COMMENT, this._stateComment(e);
    }
  }
  // Comment start dash state
  //------------------------------------------------------------------
  _stateCommentStartDash(e) {
    const s = this.currentToken;
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.COMMENT_END;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.abruptClosingOfEmptyComment), this.state = A.DATA, this.emitCurrentComment(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInComment), this.emitCurrentComment(s), this._emitEOFToken();
        break;
      }
      default:
        s.data += "-", this.state = A.COMMENT, this._stateComment(e);
    }
  }
  // Comment state
  //------------------------------------------------------------------
  _stateComment(e) {
    const s = this.currentToken;
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.COMMENT_END_DASH;
        break;
      }
      case o.LESS_THAN_SIGN: {
        s.data += "<", this.state = A.COMMENT_LESS_THAN_SIGN;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.data += S;
        break;
      }
      case o.EOF: {
        this._err(g.eofInComment), this.emitCurrentComment(s), this._emitEOFToken();
        break;
      }
      default:
        s.data += String.fromCodePoint(e);
    }
  }
  // Comment less-than sign state
  //------------------------------------------------------------------
  _stateCommentLessThanSign(e) {
    const s = this.currentToken;
    switch (e) {
      case o.EXCLAMATION_MARK: {
        s.data += "!", this.state = A.COMMENT_LESS_THAN_SIGN_BANG;
        break;
      }
      case o.LESS_THAN_SIGN: {
        s.data += "<";
        break;
      }
      default:
        this.state = A.COMMENT, this._stateComment(e);
    }
  }
  // Comment less-than sign bang state
  //------------------------------------------------------------------
  _stateCommentLessThanSignBang(e) {
    e === o.HYPHEN_MINUS ? this.state = A.COMMENT_LESS_THAN_SIGN_BANG_DASH : (this.state = A.COMMENT, this._stateComment(e));
  }
  // Comment less-than sign bang dash state
  //------------------------------------------------------------------
  _stateCommentLessThanSignBangDash(e) {
    e === o.HYPHEN_MINUS ? this.state = A.COMMENT_LESS_THAN_SIGN_BANG_DASH_DASH : (this.state = A.COMMENT_END_DASH, this._stateCommentEndDash(e));
  }
  // Comment less-than sign bang dash dash state
  //------------------------------------------------------------------
  _stateCommentLessThanSignBangDashDash(e) {
    e !== o.GREATER_THAN_SIGN && e !== o.EOF && this._err(g.nestedComment), this.state = A.COMMENT_END, this._stateCommentEnd(e);
  }
  // Comment end dash state
  //------------------------------------------------------------------
  _stateCommentEndDash(e) {
    const s = this.currentToken;
    switch (e) {
      case o.HYPHEN_MINUS: {
        this.state = A.COMMENT_END;
        break;
      }
      case o.EOF: {
        this._err(g.eofInComment), this.emitCurrentComment(s), this._emitEOFToken();
        break;
      }
      default:
        s.data += "-", this.state = A.COMMENT, this._stateComment(e);
    }
  }
  // Comment end state
  //------------------------------------------------------------------
  _stateCommentEnd(e) {
    const s = this.currentToken;
    switch (e) {
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentComment(s);
        break;
      }
      case o.EXCLAMATION_MARK: {
        this.state = A.COMMENT_END_BANG;
        break;
      }
      case o.HYPHEN_MINUS: {
        s.data += "-";
        break;
      }
      case o.EOF: {
        this._err(g.eofInComment), this.emitCurrentComment(s), this._emitEOFToken();
        break;
      }
      default:
        s.data += "--", this.state = A.COMMENT, this._stateComment(e);
    }
  }
  // Comment end bang state
  //------------------------------------------------------------------
  _stateCommentEndBang(e) {
    const s = this.currentToken;
    switch (e) {
      case o.HYPHEN_MINUS: {
        s.data += "--!", this.state = A.COMMENT_END_DASH;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.incorrectlyClosedComment), this.state = A.DATA, this.emitCurrentComment(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInComment), this.emitCurrentComment(s), this._emitEOFToken();
        break;
      }
      default:
        s.data += "--!", this.state = A.COMMENT, this._stateComment(e);
    }
  }
  // DOCTYPE state
  //------------------------------------------------------------------
  _stateDoctype(e) {
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this.state = A.BEFORE_DOCTYPE_NAME;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.BEFORE_DOCTYPE_NAME, this._stateBeforeDoctypeName(e);
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), this._createDoctypeToken(null);
        const s = this.currentToken;
        s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingWhitespaceBeforeDoctypeName), this.state = A.BEFORE_DOCTYPE_NAME, this._stateBeforeDoctypeName(e);
    }
  }
  // Before DOCTYPE name state
  //------------------------------------------------------------------
  _stateBeforeDoctypeName(e) {
    if (le(e))
      this._createDoctypeToken(String.fromCharCode(ke(e))), this.state = A.DOCTYPE_NAME;
    else
      switch (e) {
        case o.SPACE:
        case o.LINE_FEED:
        case o.TABULATION:
        case o.FORM_FEED:
          break;
        case o.NULL: {
          this._err(g.unexpectedNullCharacter), this._createDoctypeToken(S), this.state = A.DOCTYPE_NAME;
          break;
        }
        case o.GREATER_THAN_SIGN: {
          this._err(g.missingDoctypeName), this._createDoctypeToken(null);
          const s = this.currentToken;
          s.forceQuirks = !0, this.emitCurrentDoctype(s), this.state = A.DATA;
          break;
        }
        case o.EOF: {
          this._err(g.eofInDoctype), this._createDoctypeToken(null);
          const s = this.currentToken;
          s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
          break;
        }
        default:
          this._createDoctypeToken(String.fromCodePoint(e)), this.state = A.DOCTYPE_NAME;
      }
  }
  // DOCTYPE name state
  //------------------------------------------------------------------
  _stateDoctypeName(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this.state = A.AFTER_DOCTYPE_NAME;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.name += S;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        s.name += String.fromCodePoint(le(e) ? ke(e) : e);
    }
  }
  // After DOCTYPE name state
  //------------------------------------------------------------------
  _stateAfterDoctypeName(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._consumeSequenceIfMatch(k.PUBLIC, !1) ? this.state = A.AFTER_DOCTYPE_PUBLIC_KEYWORD : this._consumeSequenceIfMatch(k.SYSTEM, !1) ? this.state = A.AFTER_DOCTYPE_SYSTEM_KEYWORD : this._ensureHibernation() || (this._err(g.invalidCharacterSequenceAfterDoctypeName), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e));
    }
  }
  // After DOCTYPE public keyword state
  //------------------------------------------------------------------
  _stateAfterDoctypePublicKeyword(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this.state = A.BEFORE_DOCTYPE_PUBLIC_IDENTIFIER;
        break;
      }
      case o.QUOTATION_MARK: {
        this._err(g.missingWhitespaceAfterDoctypePublicKeyword), s.publicId = "", this.state = A.DOCTYPE_PUBLIC_IDENTIFIER_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        this._err(g.missingWhitespaceAfterDoctypePublicKeyword), s.publicId = "", this.state = A.DOCTYPE_PUBLIC_IDENTIFIER_SINGLE_QUOTED;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.missingDoctypePublicIdentifier), s.forceQuirks = !0, this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingQuoteBeforeDoctypePublicIdentifier), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // Before DOCTYPE public identifier state
  //------------------------------------------------------------------
  _stateBeforeDoctypePublicIdentifier(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.QUOTATION_MARK: {
        s.publicId = "", this.state = A.DOCTYPE_PUBLIC_IDENTIFIER_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        s.publicId = "", this.state = A.DOCTYPE_PUBLIC_IDENTIFIER_SINGLE_QUOTED;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.missingDoctypePublicIdentifier), s.forceQuirks = !0, this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingQuoteBeforeDoctypePublicIdentifier), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // DOCTYPE public identifier (double-quoted) state
  //------------------------------------------------------------------
  _stateDoctypePublicIdentifierDoubleQuoted(e) {
    const s = this.currentToken;
    switch (e) {
      case o.QUOTATION_MARK: {
        this.state = A.AFTER_DOCTYPE_PUBLIC_IDENTIFIER;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.publicId += S;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.abruptDoctypePublicIdentifier), s.forceQuirks = !0, this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        s.publicId += String.fromCodePoint(e);
    }
  }
  // DOCTYPE public identifier (single-quoted) state
  //------------------------------------------------------------------
  _stateDoctypePublicIdentifierSingleQuoted(e) {
    const s = this.currentToken;
    switch (e) {
      case o.APOSTROPHE: {
        this.state = A.AFTER_DOCTYPE_PUBLIC_IDENTIFIER;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.publicId += S;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.abruptDoctypePublicIdentifier), s.forceQuirks = !0, this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        s.publicId += String.fromCodePoint(e);
    }
  }
  // After DOCTYPE public identifier state
  //------------------------------------------------------------------
  _stateAfterDoctypePublicIdentifier(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this.state = A.BETWEEN_DOCTYPE_PUBLIC_AND_SYSTEM_IDENTIFIERS;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.QUOTATION_MARK: {
        this._err(g.missingWhitespaceBetweenDoctypePublicAndSystemIdentifiers), s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        this._err(g.missingWhitespaceBetweenDoctypePublicAndSystemIdentifiers), s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingQuoteBeforeDoctypeSystemIdentifier), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // Between DOCTYPE public and system identifiers state
  //------------------------------------------------------------------
  _stateBetweenDoctypePublicAndSystemIdentifiers(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.GREATER_THAN_SIGN: {
        this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.QUOTATION_MARK: {
        s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingQuoteBeforeDoctypeSystemIdentifier), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // After DOCTYPE system keyword state
  //------------------------------------------------------------------
  _stateAfterDoctypeSystemKeyword(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED: {
        this.state = A.BEFORE_DOCTYPE_SYSTEM_IDENTIFIER;
        break;
      }
      case o.QUOTATION_MARK: {
        this._err(g.missingWhitespaceAfterDoctypeSystemKeyword), s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        this._err(g.missingWhitespaceAfterDoctypeSystemKeyword), s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.missingDoctypeSystemIdentifier), s.forceQuirks = !0, this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingQuoteBeforeDoctypeSystemIdentifier), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // Before DOCTYPE system identifier state
  //------------------------------------------------------------------
  _stateBeforeDoctypeSystemIdentifier(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.QUOTATION_MARK: {
        s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_DOUBLE_QUOTED;
        break;
      }
      case o.APOSTROPHE: {
        s.systemId = "", this.state = A.DOCTYPE_SYSTEM_IDENTIFIER_SINGLE_QUOTED;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.missingDoctypeSystemIdentifier), s.forceQuirks = !0, this.state = A.DATA, this.emitCurrentDoctype(s);
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.missingQuoteBeforeDoctypeSystemIdentifier), s.forceQuirks = !0, this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // DOCTYPE system identifier (double-quoted) state
  //------------------------------------------------------------------
  _stateDoctypeSystemIdentifierDoubleQuoted(e) {
    const s = this.currentToken;
    switch (e) {
      case o.QUOTATION_MARK: {
        this.state = A.AFTER_DOCTYPE_SYSTEM_IDENTIFIER;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.systemId += S;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.abruptDoctypeSystemIdentifier), s.forceQuirks = !0, this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        s.systemId += String.fromCodePoint(e);
    }
  }
  // DOCTYPE system identifier (single-quoted) state
  //------------------------------------------------------------------
  _stateDoctypeSystemIdentifierSingleQuoted(e) {
    const s = this.currentToken;
    switch (e) {
      case o.APOSTROPHE: {
        this.state = A.AFTER_DOCTYPE_SYSTEM_IDENTIFIER;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter), s.systemId += S;
        break;
      }
      case o.GREATER_THAN_SIGN: {
        this._err(g.abruptDoctypeSystemIdentifier), s.forceQuirks = !0, this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        s.systemId += String.fromCodePoint(e);
    }
  }
  // After DOCTYPE system identifier state
  //------------------------------------------------------------------
  _stateAfterDoctypeSystemIdentifier(e) {
    const s = this.currentToken;
    switch (e) {
      case o.SPACE:
      case o.LINE_FEED:
      case o.TABULATION:
      case o.FORM_FEED:
        break;
      case o.GREATER_THAN_SIGN: {
        this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.EOF: {
        this._err(g.eofInDoctype), s.forceQuirks = !0, this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
      default:
        this._err(g.unexpectedCharacterAfterDoctypeSystemIdentifier), this.state = A.BOGUS_DOCTYPE, this._stateBogusDoctype(e);
    }
  }
  // Bogus DOCTYPE state
  //------------------------------------------------------------------
  _stateBogusDoctype(e) {
    const s = this.currentToken;
    switch (e) {
      case o.GREATER_THAN_SIGN: {
        this.emitCurrentDoctype(s), this.state = A.DATA;
        break;
      }
      case o.NULL: {
        this._err(g.unexpectedNullCharacter);
        break;
      }
      case o.EOF: {
        this.emitCurrentDoctype(s), this._emitEOFToken();
        break;
      }
    }
  }
  // CDATA section state
  //------------------------------------------------------------------
  _stateCdataSection(e) {
    switch (e) {
      case o.RIGHT_SQUARE_BRACKET: {
        this.state = A.CDATA_SECTION_BRACKET;
        break;
      }
      case o.EOF: {
        this._err(g.eofInCdata), this._emitEOFToken();
        break;
      }
      default:
        this._emitCodePoint(e);
    }
  }
  // CDATA section bracket state
  //------------------------------------------------------------------
  _stateCdataSectionBracket(e) {
    e === o.RIGHT_SQUARE_BRACKET ? this.state = A.CDATA_SECTION_END : (this._emitChars("]"), this.state = A.CDATA_SECTION, this._stateCdataSection(e));
  }
  // CDATA section end state
  //------------------------------------------------------------------
  _stateCdataSectionEnd(e) {
    switch (e) {
      case o.GREATER_THAN_SIGN: {
        this.state = A.DATA;
        break;
      }
      case o.RIGHT_SQUARE_BRACKET: {
        this._emitChars("]");
        break;
      }
      default:
        this._emitChars("]]"), this.state = A.CDATA_SECTION, this._stateCdataSection(e);
    }
  }
  // Character reference state
  //------------------------------------------------------------------
  _stateCharacterReference() {
    let e = this.entityDecoder.write(this.preprocessor.html, this.preprocessor.pos);
    if (e < 0)
      if (this.preprocessor.lastChunkWritten)
        e = this.entityDecoder.end();
      else {
        this.active = !1, this.preprocessor.pos = this.preprocessor.html.length - 1, this.consumedAfterSnapshot = 0, this.preprocessor.endOfChunkHit = !0;
        return;
      }
    e === 0 ? (this.preprocessor.pos = this.entityStartPos, this._flushCodePointConsumedAsCharacterReference(o.AMPERSAND), this.state = !this._isCharacterReferenceInAttribute() && jt(this.preprocessor.peek(1)) ? A.AMBIGUOUS_AMPERSAND : this.returnState) : this.state = this.returnState;
  }
  // Ambiguos ampersand state
  //------------------------------------------------------------------
  _stateAmbiguousAmpersand(e) {
    jt(e) ? this._flushCodePointConsumedAsCharacterReference(e) : (e === o.SEMICOLON && this._err(g.unknownNamedCharacterReference), this.state = this.returnState, this._callState(e));
  }
}
const Os = /* @__PURE__ */ new Set([i.DD, i.DT, i.LI, i.OPTGROUP, i.OPTION, i.P, i.RB, i.RP, i.RT, i.RTC]), qt = /* @__PURE__ */ new Set([
  ...Os,
  i.CAPTION,
  i.COLGROUP,
  i.TBODY,
  i.TD,
  i.TFOOT,
  i.TH,
  i.THEAD,
  i.TR
]), Ke = /* @__PURE__ */ new Set([
  i.APPLET,
  i.CAPTION,
  i.HTML,
  i.MARQUEE,
  i.OBJECT,
  i.TABLE,
  i.TD,
  i.TEMPLATE,
  i.TH
]), _r = /* @__PURE__ */ new Set([...Ke, i.OL, i.UL]), mr = /* @__PURE__ */ new Set([...Ke, i.BUTTON]), es = /* @__PURE__ */ new Set([i.ANNOTATION_XML, i.MI, i.MN, i.MO, i.MS, i.MTEXT]), ts = /* @__PURE__ */ new Set([i.DESC, i.FOREIGN_OBJECT, i.TITLE]), pr = /* @__PURE__ */ new Set([i.TR, i.TEMPLATE, i.HTML]), Tr = /* @__PURE__ */ new Set([i.TBODY, i.TFOOT, i.THEAD, i.TEMPLATE, i.HTML]), fr = /* @__PURE__ */ new Set([i.TABLE, i.TEMPLATE, i.HTML]), Ir = /* @__PURE__ */ new Set([i.TD, i.TH]);
class Cr {
  get currentTmplContentOrNode() {
    return this._isInTemplate() ? this.treeAdapter.getTemplateContent(this.current) : this.current;
  }
  constructor(e, s, r) {
    this.treeAdapter = s, this.handler = r, this.items = [], this.tagIDs = [], this.stackTop = -1, this.tmplCount = 0, this.currentTagId = i.UNKNOWN, this.current = e;
  }
  //Index of element
  _indexOf(e) {
    return this.items.lastIndexOf(e, this.stackTop);
  }
  //Update current element
  _isInTemplate() {
    return this.currentTagId === i.TEMPLATE && this.treeAdapter.getNamespaceURI(this.current) === p.HTML;
  }
  _updateCurrentElement() {
    this.current = this.items[this.stackTop], this.currentTagId = this.tagIDs[this.stackTop];
  }
  //Mutations
  push(e, s) {
    this.stackTop++, this.items[this.stackTop] = e, this.current = e, this.tagIDs[this.stackTop] = s, this.currentTagId = s, this._isInTemplate() && this.tmplCount++, this.handler.onItemPush(e, s, !0);
  }
  pop() {
    const e = this.current;
    this.tmplCount > 0 && this._isInTemplate() && this.tmplCount--, this.stackTop--, this._updateCurrentElement(), this.handler.onItemPop(e, !0);
  }
  replace(e, s) {
    const r = this._indexOf(e);
    this.items[r] = s, r === this.stackTop && (this.current = s);
  }
  insertAfter(e, s, r) {
    const a = this._indexOf(e) + 1;
    this.items.splice(a, 0, s), this.tagIDs.splice(a, 0, r), this.stackTop++, a === this.stackTop && this._updateCurrentElement(), this.current && this.currentTagId !== void 0 && this.handler.onItemPush(this.current, this.currentTagId, a === this.stackTop);
  }
  popUntilTagNamePopped(e) {
    let s = this.stackTop + 1;
    do
      s = this.tagIDs.lastIndexOf(e, s - 1);
    while (s > 0 && this.treeAdapter.getNamespaceURI(this.items[s]) !== p.HTML);
    this.shortenToLength(Math.max(s, 0));
  }
  shortenToLength(e) {
    for (; this.stackTop >= e; ) {
      const s = this.current;
      this.tmplCount > 0 && this._isInTemplate() && (this.tmplCount -= 1), this.stackTop--, this._updateCurrentElement(), this.handler.onItemPop(s, this.stackTop < e);
    }
  }
  popUntilElementPopped(e) {
    const s = this._indexOf(e);
    this.shortenToLength(Math.max(s, 0));
  }
  popUntilPopped(e, s) {
    const r = this._indexOfTagNames(e, s);
    this.shortenToLength(Math.max(r, 0));
  }
  popUntilNumberedHeaderPopped() {
    this.popUntilPopped(gt, p.HTML);
  }
  popUntilTableCellPopped() {
    this.popUntilPopped(Ir, p.HTML);
  }
  popAllUpToHtmlElement() {
    this.tmplCount = 0, this.shortenToLength(1);
  }
  _indexOfTagNames(e, s) {
    for (let r = this.stackTop; r >= 0; r--)
      if (e.has(this.tagIDs[r]) && this.treeAdapter.getNamespaceURI(this.items[r]) === s)
        return r;
    return -1;
  }
  clearBackTo(e, s) {
    const r = this._indexOfTagNames(e, s);
    this.shortenToLength(r + 1);
  }
  clearBackToTableContext() {
    this.clearBackTo(fr, p.HTML);
  }
  clearBackToTableBodyContext() {
    this.clearBackTo(Tr, p.HTML);
  }
  clearBackToTableRowContext() {
    this.clearBackTo(pr, p.HTML);
  }
  remove(e) {
    const s = this._indexOf(e);
    s >= 0 && (s === this.stackTop ? this.pop() : (this.items.splice(s, 1), this.tagIDs.splice(s, 1), this.stackTop--, this._updateCurrentElement(), this.handler.onItemPop(e, !1)));
  }
  //Search
  tryPeekProperlyNestedBodyElement() {
    return this.stackTop >= 1 && this.tagIDs[1] === i.BODY ? this.items[1] : null;
  }
  contains(e) {
    return this._indexOf(e) > -1;
  }
  getCommonAncestor(e) {
    const s = this._indexOf(e) - 1;
    return s >= 0 ? this.items[s] : null;
  }
  isRootHtmlElementCurrent() {
    return this.stackTop === 0 && this.tagIDs[0] === i.HTML;
  }
  //Element in scope
  hasInDynamicScope(e, s) {
    for (let r = this.stackTop; r >= 0; r--) {
      const a = this.tagIDs[r];
      switch (this.treeAdapter.getNamespaceURI(this.items[r])) {
        case p.HTML: {
          if (a === e)
            return !0;
          if (s.has(a))
            return !1;
          break;
        }
        case p.SVG: {
          if (ts.has(a))
            return !1;
          break;
        }
        case p.MATHML: {
          if (es.has(a))
            return !1;
          break;
        }
      }
    }
    return !0;
  }
  hasInScope(e) {
    return this.hasInDynamicScope(e, Ke);
  }
  hasInListItemScope(e) {
    return this.hasInDynamicScope(e, _r);
  }
  hasInButtonScope(e) {
    return this.hasInDynamicScope(e, mr);
  }
  hasNumberedHeaderInScope() {
    for (let e = this.stackTop; e >= 0; e--) {
      const s = this.tagIDs[e];
      switch (this.treeAdapter.getNamespaceURI(this.items[e])) {
        case p.HTML: {
          if (gt.has(s))
            return !0;
          if (Ke.has(s))
            return !1;
          break;
        }
        case p.SVG: {
          if (ts.has(s))
            return !1;
          break;
        }
        case p.MATHML: {
          if (es.has(s))
            return !1;
          break;
        }
      }
    }
    return !0;
  }
  hasInTableScope(e) {
    for (let s = this.stackTop; s >= 0; s--)
      if (this.treeAdapter.getNamespaceURI(this.items[s]) === p.HTML)
        switch (this.tagIDs[s]) {
          case e:
            return !0;
          case i.TABLE:
          case i.HTML:
            return !1;
        }
    return !0;
  }
  hasTableBodyContextInTableScope() {
    for (let e = this.stackTop; e >= 0; e--)
      if (this.treeAdapter.getNamespaceURI(this.items[e]) === p.HTML)
        switch (this.tagIDs[e]) {
          case i.TBODY:
          case i.THEAD:
          case i.TFOOT:
            return !0;
          case i.TABLE:
          case i.HTML:
            return !1;
        }
    return !0;
  }
  hasInSelectScope(e) {
    for (let s = this.stackTop; s >= 0; s--)
      if (this.treeAdapter.getNamespaceURI(this.items[s]) === p.HTML)
        switch (this.tagIDs[s]) {
          case e:
            return !0;
          case i.OPTION:
          case i.OPTGROUP:
            break;
          default:
            return !1;
        }
    return !0;
  }
  //Implied end tags
  generateImpliedEndTags() {
    for (; this.currentTagId !== void 0 && Os.has(this.currentTagId); )
      this.pop();
  }
  generateImpliedEndTagsThoroughly() {
    for (; this.currentTagId !== void 0 && qt.has(this.currentTagId); )
      this.pop();
  }
  generateImpliedEndTagsWithExclusion(e) {
    for (; this.currentTagId !== void 0 && this.currentTagId !== e && qt.has(this.currentTagId); )
      this.pop();
  }
}
const lt = 3;
var P;
(function(t) {
  t[t.Marker = 0] = "Marker", t[t.Element = 1] = "Element";
})(P || (P = {}));
const ss = { type: P.Marker };
class br {
  constructor(e) {
    this.treeAdapter = e, this.entries = [], this.bookmark = null;
  }
  //Noah Ark's condition
  //OPTIMIZATION: at first we try to find possible candidates for exclusion using
  //lightweight heuristics without thorough attributes check.
  _getNoahArkConditionCandidates(e, s) {
    const r = [], a = s.length, n = this.treeAdapter.getTagName(e), c = this.treeAdapter.getNamespaceURI(e);
    for (let h = 0; h < this.entries.length; h++) {
      const E = this.entries[h];
      if (E.type === P.Marker)
        break;
      const { element: u } = E;
      if (this.treeAdapter.getTagName(u) === n && this.treeAdapter.getNamespaceURI(u) === c) {
        const _ = this.treeAdapter.getAttrList(u);
        _.length === a && r.push({ idx: h, attrs: _ });
      }
    }
    return r;
  }
  _ensureNoahArkCondition(e) {
    if (this.entries.length < lt)
      return;
    const s = this.treeAdapter.getAttrList(e), r = this._getNoahArkConditionCandidates(e, s);
    if (r.length < lt)
      return;
    const a = new Map(s.map((c) => [c.name, c.value]));
    let n = 0;
    for (let c = 0; c < r.length; c++) {
      const h = r[c];
      h.attrs.every((E) => a.get(E.name) === E.value) && (n += 1, n >= lt && this.entries.splice(h.idx, 1));
    }
  }
  //Mutations
  insertMarker() {
    this.entries.unshift(ss);
  }
  pushElement(e, s) {
    this._ensureNoahArkCondition(e), this.entries.unshift({
      type: P.Element,
      element: e,
      token: s
    });
  }
  insertElementAfterBookmark(e, s) {
    const r = this.entries.indexOf(this.bookmark);
    this.entries.splice(r, 0, {
      type: P.Element,
      element: e,
      token: s
    });
  }
  removeEntry(e) {
    const s = this.entries.indexOf(e);
    s !== -1 && this.entries.splice(s, 1);
  }
  /**
   * Clears the list of formatting elements up to the last marker.
   *
   * @see https://html.spec.whatwg.org/multipage/parsing.html#clear-the-list-of-active-formatting-elements-up-to-the-last-marker
   */
  clearToLastMarker() {
    const e = this.entries.indexOf(ss);
    e === -1 ? this.entries.length = 0 : this.entries.splice(0, e + 1);
  }
  //Search
  getElementEntryInScopeWithTagName(e) {
    const s = this.entries.find((r) => r.type === P.Marker || this.treeAdapter.getTagName(r.element) === e);
    return s && s.type === P.Element ? s : null;
  }
  getElementEntry(e) {
    return this.entries.find((s) => s.type === P.Element && s.element === e);
  }
}
const K = {
  //Node construction
  createDocument() {
    return {
      nodeName: "#document",
      mode: v.NO_QUIRKS,
      childNodes: []
    };
  },
  createDocumentFragment() {
    return {
      nodeName: "#document-fragment",
      childNodes: []
    };
  },
  createElement(t, e, s) {
    return {
      nodeName: t,
      tagName: t,
      attrs: s,
      namespaceURI: e,
      childNodes: [],
      parentNode: null
    };
  },
  createCommentNode(t) {
    return {
      nodeName: "#comment",
      data: t,
      parentNode: null
    };
  },
  createTextNode(t) {
    return {
      nodeName: "#text",
      value: t,
      parentNode: null
    };
  },
  //Tree mutation
  appendChild(t, e) {
    t.childNodes.push(e), e.parentNode = t;
  },
  insertBefore(t, e, s) {
    const r = t.childNodes.indexOf(s);
    t.childNodes.splice(r, 0, e), e.parentNode = t;
  },
  setTemplateContent(t, e) {
    t.content = e;
  },
  getTemplateContent(t) {
    return t.content;
  },
  setDocumentType(t, e, s, r) {
    const a = t.childNodes.find((n) => n.nodeName === "#documentType");
    if (a)
      a.name = e, a.publicId = s, a.systemId = r;
    else {
      const n = {
        nodeName: "#documentType",
        name: e,
        publicId: s,
        systemId: r,
        parentNode: null
      };
      K.appendChild(t, n);
    }
  },
  setDocumentMode(t, e) {
    t.mode = e;
  },
  getDocumentMode(t) {
    return t.mode;
  },
  detachNode(t) {
    if (t.parentNode) {
      const e = t.parentNode.childNodes.indexOf(t);
      t.parentNode.childNodes.splice(e, 1), t.parentNode = null;
    }
  },
  insertText(t, e) {
    if (t.childNodes.length > 0) {
      const s = t.childNodes[t.childNodes.length - 1];
      if (K.isTextNode(s)) {
        s.value += e;
        return;
      }
    }
    K.appendChild(t, K.createTextNode(e));
  },
  insertTextBefore(t, e, s) {
    const r = t.childNodes[t.childNodes.indexOf(s) - 1];
    r && K.isTextNode(r) ? r.value += e : K.insertBefore(t, K.createTextNode(e), s);
  },
  adoptAttributes(t, e) {
    const s = new Set(t.attrs.map((r) => r.name));
    for (let r = 0; r < e.length; r++)
      s.has(e[r].name) || t.attrs.push(e[r]);
  },
  //Tree traversing
  getFirstChild(t) {
    return t.childNodes[0];
  },
  getChildNodes(t) {
    return t.childNodes;
  },
  getParentNode(t) {
    return t.parentNode;
  },
  getAttrList(t) {
    return t.attrs;
  },
  //Node data
  getTagName(t) {
    return t.tagName;
  },
  getNamespaceURI(t) {
    return t.namespaceURI;
  },
  getTextNodeContent(t) {
    return t.value;
  },
  getCommentNodeContent(t) {
    return t.data;
  },
  getDocumentTypeNodeName(t) {
    return t.name;
  },
  getDocumentTypeNodePublicId(t) {
    return t.publicId;
  },
  getDocumentTypeNodeSystemId(t) {
    return t.systemId;
  },
  //Node types
  isTextNode(t) {
    return t.nodeName === "#text";
  },
  isCommentNode(t) {
    return t.nodeName === "#comment";
  },
  isDocumentTypeNode(t) {
    return t.nodeName === "#documentType";
  },
  isElementNode(t) {
    return Object.prototype.hasOwnProperty.call(t, "tagName");
  },
  // Source code location
  setNodeSourceCodeLocation(t, e) {
    t.sourceCodeLocation = e;
  },
  getNodeSourceCodeLocation(t) {
    return t.sourceCodeLocation;
  },
  updateNodeSourceCodeLocation(t, e) {
    t.sourceCodeLocation = { ...t.sourceCodeLocation, ...e };
  }
}, Ls = "html", Nr = "about:legacy-compat", Dr = "http://www.ibm.com/data/dtd/v11/ibmxhtml1-transitional.dtd", ws = [
  "+//silmaril//dtd html pro v0r11 19970101//",
  "-//as//dtd html 3.0 aswedit + extensions//",
  "-//advasoft ltd//dtd html 3.0 aswedit + extensions//",
  "-//ietf//dtd html 2.0 level 1//",
  "-//ietf//dtd html 2.0 level 2//",
  "-//ietf//dtd html 2.0 strict level 1//",
  "-//ietf//dtd html 2.0 strict level 2//",
  "-//ietf//dtd html 2.0 strict//",
  "-//ietf//dtd html 2.0//",
  "-//ietf//dtd html 2.1e//",
  "-//ietf//dtd html 3.0//",
  "-//ietf//dtd html 3.2 final//",
  "-//ietf//dtd html 3.2//",
  "-//ietf//dtd html 3//",
  "-//ietf//dtd html level 0//",
  "-//ietf//dtd html level 1//",
  "-//ietf//dtd html level 2//",
  "-//ietf//dtd html level 3//",
  "-//ietf//dtd html strict level 0//",
  "-//ietf//dtd html strict level 1//",
  "-//ietf//dtd html strict level 2//",
  "-//ietf//dtd html strict level 3//",
  "-//ietf//dtd html strict//",
  "-//ietf//dtd html//",
  "-//metrius//dtd metrius presentational//",
  "-//microsoft//dtd internet explorer 2.0 html strict//",
  "-//microsoft//dtd internet explorer 2.0 html//",
  "-//microsoft//dtd internet explorer 2.0 tables//",
  "-//microsoft//dtd internet explorer 3.0 html strict//",
  "-//microsoft//dtd internet explorer 3.0 html//",
  "-//microsoft//dtd internet explorer 3.0 tables//",
  "-//netscape comm. corp.//dtd html//",
  "-//netscape comm. corp.//dtd strict html//",
  "-//o'reilly and associates//dtd html 2.0//",
  "-//o'reilly and associates//dtd html extended 1.0//",
  "-//o'reilly and associates//dtd html extended relaxed 1.0//",
  "-//sq//dtd html 2.0 hotmetal + extensions//",
  "-//softquad software//dtd hotmetal pro 6.0::19990601::extensions to html 4.0//",
  "-//softquad//dtd hotmetal pro 4.0::19971010::extensions to html 4.0//",
  "-//spyglass//dtd html 2.0 extended//",
  "-//sun microsystems corp.//dtd hotjava html//",
  "-//sun microsystems corp.//dtd hotjava strict html//",
  "-//w3c//dtd html 3 1995-03-24//",
  "-//w3c//dtd html 3.2 draft//",
  "-//w3c//dtd html 3.2 final//",
  "-//w3c//dtd html 3.2//",
  "-//w3c//dtd html 3.2s draft//",
  "-//w3c//dtd html 4.0 frameset//",
  "-//w3c//dtd html 4.0 transitional//",
  "-//w3c//dtd html experimental 19960712//",
  "-//w3c//dtd html experimental 970421//",
  "-//w3c//dtd w3 html//",
  "-//w3o//dtd w3 html 3.0//",
  "-//webtechs//dtd mozilla html 2.0//",
  "-//webtechs//dtd mozilla html//"
], Sr = [
  ...ws,
  "-//w3c//dtd html 4.01 frameset//",
  "-//w3c//dtd html 4.01 transitional//"
], Br = /* @__PURE__ */ new Set([
  "-//w3o//dtd w3 html strict 3.0//en//",
  "-/w3c/dtd html 4.0 transitional/en",
  "html"
]), ks = ["-//w3c//dtd xhtml 1.0 frameset//", "-//w3c//dtd xhtml 1.0 transitional//"], yr = [
  ...ks,
  "-//w3c//dtd html 4.01 frameset//",
  "-//w3c//dtd html 4.01 transitional//"
];
function is(t, e) {
  return e.some((s) => t.startsWith(s));
}
function Rr(t) {
  return t.name === Ls && t.publicId === null && (t.systemId === null || t.systemId === Nr);
}
function Or(t) {
  if (t.name !== Ls)
    return v.QUIRKS;
  const { systemId: e } = t;
  if (e && e.toLowerCase() === Dr)
    return v.QUIRKS;
  let { publicId: s } = t;
  if (s !== null) {
    if (s = s.toLowerCase(), Br.has(s))
      return v.QUIRKS;
    let r = e === null ? Sr : ws;
    if (is(s, r))
      return v.QUIRKS;
    if (r = e === null ? ks : yr, is(s, r))
      return v.LIMITED_QUIRKS;
  }
  return v.NO_QUIRKS;
}
const rs = {
  TEXT_HTML: "text/html",
  APPLICATION_XML: "application/xhtml+xml"
}, Lr = "definitionurl", wr = "definitionURL", kr = new Map([
  "attributeName",
  "attributeType",
  "baseFrequency",
  "baseProfile",
  "calcMode",
  "clipPathUnits",
  "diffuseConstant",
  "edgeMode",
  "filterUnits",
  "glyphRef",
  "gradientTransform",
  "gradientUnits",
  "kernelMatrix",
  "kernelUnitLength",
  "keyPoints",
  "keySplines",
  "keyTimes",
  "lengthAdjust",
  "limitingConeAngle",
  "markerHeight",
  "markerUnits",
  "markerWidth",
  "maskContentUnits",
  "maskUnits",
  "numOctaves",
  "pathLength",
  "patternContentUnits",
  "patternTransform",
  "patternUnits",
  "pointsAtX",
  "pointsAtY",
  "pointsAtZ",
  "preserveAlpha",
  "preserveAspectRatio",
  "primitiveUnits",
  "refX",
  "refY",
  "repeatCount",
  "repeatDur",
  "requiredExtensions",
  "requiredFeatures",
  "specularConstant",
  "specularExponent",
  "spreadMethod",
  "startOffset",
  "stdDeviation",
  "stitchTiles",
  "surfaceScale",
  "systemLanguage",
  "tableValues",
  "targetX",
  "targetY",
  "textLength",
  "viewBox",
  "viewTarget",
  "xChannelSelector",
  "yChannelSelector",
  "zoomAndPan"
].map((t) => [t.toLowerCase(), t])), Fr = /* @__PURE__ */ new Map([
  ["xlink:actuate", { prefix: "xlink", name: "actuate", namespace: p.XLINK }],
  ["xlink:arcrole", { prefix: "xlink", name: "arcrole", namespace: p.XLINK }],
  ["xlink:href", { prefix: "xlink", name: "href", namespace: p.XLINK }],
  ["xlink:role", { prefix: "xlink", name: "role", namespace: p.XLINK }],
  ["xlink:show", { prefix: "xlink", name: "show", namespace: p.XLINK }],
  ["xlink:title", { prefix: "xlink", name: "title", namespace: p.XLINK }],
  ["xlink:type", { prefix: "xlink", name: "type", namespace: p.XLINK }],
  ["xml:lang", { prefix: "xml", name: "lang", namespace: p.XML }],
  ["xml:space", { prefix: "xml", name: "space", namespace: p.XML }],
  ["xmlns", { prefix: "", name: "xmlns", namespace: p.XMLNS }],
  ["xmlns:xlink", { prefix: "xmlns", name: "xlink", namespace: p.XMLNS }]
]), vr = new Map([
  "altGlyph",
  "altGlyphDef",
  "altGlyphItem",
  "animateColor",
  "animateMotion",
  "animateTransform",
  "clipPath",
  "feBlend",
  "feColorMatrix",
  "feComponentTransfer",
  "feComposite",
  "feConvolveMatrix",
  "feDiffuseLighting",
  "feDisplacementMap",
  "feDistantLight",
  "feFlood",
  "feFuncA",
  "feFuncB",
  "feFuncG",
  "feFuncR",
  "feGaussianBlur",
  "feImage",
  "feMerge",
  "feMergeNode",
  "feMorphology",
  "feOffset",
  "fePointLight",
  "feSpecularLighting",
  "feSpotLight",
  "feTile",
  "feTurbulence",
  "foreignObject",
  "glyphRef",
  "linearGradient",
  "radialGradient",
  "textPath"
].map((t) => [t.toLowerCase(), t])), Mr = /* @__PURE__ */ new Set([
  i.B,
  i.BIG,
  i.BLOCKQUOTE,
  i.BODY,
  i.BR,
  i.CENTER,
  i.CODE,
  i.DD,
  i.DIV,
  i.DL,
  i.DT,
  i.EM,
  i.EMBED,
  i.H1,
  i.H2,
  i.H3,
  i.H4,
  i.H5,
  i.H6,
  i.HEAD,
  i.HR,
  i.I,
  i.IMG,
  i.LI,
  i.LISTING,
  i.MENU,
  i.META,
  i.NOBR,
  i.OL,
  i.P,
  i.PRE,
  i.RUBY,
  i.S,
  i.SMALL,
  i.SPAN,
  i.STRONG,
  i.STRIKE,
  i.SUB,
  i.SUP,
  i.TABLE,
  i.TT,
  i.U,
  i.UL,
  i.VAR
]);
function xr(t) {
  const e = t.tagID;
  return e === i.FONT && t.attrs.some(({ name: r }) => r === Z.COLOR || r === Z.SIZE || r === Z.FACE) || Mr.has(e);
}
function Fs(t) {
  for (let e = 0; e < t.attrs.length; e++)
    if (t.attrs[e].name === Lr) {
      t.attrs[e].name = wr;
      break;
    }
}
function vs(t) {
  for (let e = 0; e < t.attrs.length; e++) {
    const s = kr.get(t.attrs[e].name);
    s != null && (t.attrs[e].name = s);
  }
}
function Dt(t) {
  for (let e = 0; e < t.attrs.length; e++) {
    const s = Fr.get(t.attrs[e].name);
    s && (t.attrs[e].prefix = s.prefix, t.attrs[e].name = s.name, t.attrs[e].namespace = s.namespace);
  }
}
function Pr(t) {
  const e = vr.get(t.tagName);
  e != null && (t.tagName = e, t.tagID = Xe(t.tagName));
}
function Hr(t, e) {
  return e === p.MATHML && (t === i.MI || t === i.MO || t === i.MN || t === i.MS || t === i.MTEXT);
}
function Ur(t, e, s) {
  if (e === p.MATHML && t === i.ANNOTATION_XML) {
    for (let r = 0; r < s.length; r++)
      if (s[r].name === Z.ENCODING) {
        const a = s[r].value.toLowerCase();
        return a === rs.TEXT_HTML || a === rs.APPLICATION_XML;
      }
  }
  return e === p.SVG && (t === i.FOREIGN_OBJECT || t === i.DESC || t === i.TITLE);
}
function Qr(t, e, s, r) {
  return (!r || r === p.HTML) && Ur(t, e, s) || (!r || r === p.MATHML) && Hr(t, e);
}
const Yr = "hidden", Kr = 8, Wr = 3;
var l;
(function(t) {
  t[t.INITIAL = 0] = "INITIAL", t[t.BEFORE_HTML = 1] = "BEFORE_HTML", t[t.BEFORE_HEAD = 2] = "BEFORE_HEAD", t[t.IN_HEAD = 3] = "IN_HEAD", t[t.IN_HEAD_NO_SCRIPT = 4] = "IN_HEAD_NO_SCRIPT", t[t.AFTER_HEAD = 5] = "AFTER_HEAD", t[t.IN_BODY = 6] = "IN_BODY", t[t.TEXT = 7] = "TEXT", t[t.IN_TABLE = 8] = "IN_TABLE", t[t.IN_TABLE_TEXT = 9] = "IN_TABLE_TEXT", t[t.IN_CAPTION = 10] = "IN_CAPTION", t[t.IN_COLUMN_GROUP = 11] = "IN_COLUMN_GROUP", t[t.IN_TABLE_BODY = 12] = "IN_TABLE_BODY", t[t.IN_ROW = 13] = "IN_ROW", t[t.IN_CELL = 14] = "IN_CELL", t[t.IN_SELECT = 15] = "IN_SELECT", t[t.IN_SELECT_IN_TABLE = 16] = "IN_SELECT_IN_TABLE", t[t.IN_TEMPLATE = 17] = "IN_TEMPLATE", t[t.AFTER_BODY = 18] = "AFTER_BODY", t[t.IN_FRAMESET = 19] = "IN_FRAMESET", t[t.AFTER_FRAMESET = 20] = "AFTER_FRAMESET", t[t.AFTER_AFTER_BODY = 21] = "AFTER_AFTER_BODY", t[t.AFTER_AFTER_FRAMESET = 22] = "AFTER_AFTER_FRAMESET";
})(l || (l = {}));
const Gr = {
  startLine: -1,
  startCol: -1,
  startOffset: -1,
  endLine: -1,
  endCol: -1,
  endOffset: -1
}, Ms = /* @__PURE__ */ new Set([i.TABLE, i.TBODY, i.TFOOT, i.THEAD, i.TR]), as = {
  scriptingEnabled: !0,
  sourceCodeLocationInfo: !1,
  treeAdapter: K,
  onParseError: null
};
class $r {
  constructor(e, s, r = null, a = null) {
    this.fragmentContext = r, this.scriptHandler = a, this.currentToken = null, this.stopped = !1, this.insertionMode = l.INITIAL, this.originalInsertionMode = l.INITIAL, this.headElement = null, this.formElement = null, this.currentNotInHTML = !1, this.tmplInsertionModeStack = [], this.pendingCharacterTokens = [], this.hasNonWhitespacePendingCharacterToken = !1, this.framesetOk = !0, this.skipNextNewLine = !1, this.fosterParentingEnabled = !1, this.options = {
      ...as,
      ...e
    }, this.treeAdapter = this.options.treeAdapter, this.onParseError = this.options.onParseError, this.onParseError && (this.options.sourceCodeLocationInfo = !0), this.document = s ?? this.treeAdapter.createDocument(), this.tokenizer = new gr(this.options, this), this.activeFormattingElements = new br(this.treeAdapter), this.fragmentContextID = r ? Xe(this.treeAdapter.getTagName(r)) : i.UNKNOWN, this._setContextModes(r ?? this.document, this.fragmentContextID), this.openElements = new Cr(this.document, this.treeAdapter, this);
  }
  // API
  static parse(e, s) {
    const r = new this(s);
    return r.tokenizer.write(e, !0), r.document;
  }
  static getFragmentParser(e, s) {
    const r = {
      ...as,
      ...s
    };
    e ?? (e = r.treeAdapter.createElement(d.TEMPLATE, p.HTML, []));
    const a = r.treeAdapter.createElement("documentmock", p.HTML, []), n = new this(r, a, e);
    return n.fragmentContextID === i.TEMPLATE && n.tmplInsertionModeStack.unshift(l.IN_TEMPLATE), n._initTokenizerForFragmentParsing(), n._insertFakeRootElement(), n._resetInsertionMode(), n._findFormInFragmentContext(), n;
  }
  getFragment() {
    const e = this.treeAdapter.getFirstChild(this.document), s = this.treeAdapter.createDocumentFragment();
    return this._adoptNodes(e, s), s;
  }
  //Errors
  /** @internal */
  _err(e, s, r) {
    var a;
    if (!this.onParseError)
      return;
    const n = (a = e.location) !== null && a !== void 0 ? a : Gr, c = {
      code: s,
      startLine: n.startLine,
      startCol: n.startCol,
      startOffset: n.startOffset,
      endLine: r ? n.startLine : n.endLine,
      endCol: r ? n.startCol : n.endCol,
      endOffset: r ? n.startOffset : n.endOffset
    };
    this.onParseError(c);
  }
  //Stack events
  /** @internal */
  onItemPush(e, s, r) {
    var a, n;
    (n = (a = this.treeAdapter).onItemPush) === null || n === void 0 || n.call(a, e), r && this.openElements.stackTop > 0 && this._setContextModes(e, s);
  }
  /** @internal */
  onItemPop(e, s) {
    var r, a;
    if (this.options.sourceCodeLocationInfo && this._setEndLocation(e, this.currentToken), (a = (r = this.treeAdapter).onItemPop) === null || a === void 0 || a.call(r, e, this.openElements.current), s) {
      let n, c;
      this.openElements.stackTop === 0 && this.fragmentContext ? (n = this.fragmentContext, c = this.fragmentContextID) : { current: n, currentTagId: c } = this.openElements, this._setContextModes(n, c);
    }
  }
  _setContextModes(e, s) {
    const r = e === this.document || e && this.treeAdapter.getNamespaceURI(e) === p.HTML;
    this.currentNotInHTML = !r, this.tokenizer.inForeignNode = !r && e !== void 0 && s !== void 0 && !this._isIntegrationPoint(s, e);
  }
  /** @protected */
  _switchToTextParsing(e, s) {
    this._insertElement(e, p.HTML), this.tokenizer.state = s, this.originalInsertionMode = this.insertionMode, this.insertionMode = l.TEXT;
  }
  switchToPlaintextParsing() {
    this.insertionMode = l.TEXT, this.originalInsertionMode = l.IN_BODY, this.tokenizer.state = F.PLAINTEXT;
  }
  //Fragment parsing
  /** @protected */
  _getAdjustedCurrentElement() {
    return this.openElements.stackTop === 0 && this.fragmentContext ? this.fragmentContext : this.openElements.current;
  }
  /** @protected */
  _findFormInFragmentContext() {
    let e = this.fragmentContext;
    for (; e; ) {
      if (this.treeAdapter.getTagName(e) === d.FORM) {
        this.formElement = e;
        break;
      }
      e = this.treeAdapter.getParentNode(e);
    }
  }
  _initTokenizerForFragmentParsing() {
    if (!(!this.fragmentContext || this.treeAdapter.getNamespaceURI(this.fragmentContext) !== p.HTML))
      switch (this.fragmentContextID) {
        case i.TITLE:
        case i.TEXTAREA: {
          this.tokenizer.state = F.RCDATA;
          break;
        }
        case i.STYLE:
        case i.XMP:
        case i.IFRAME:
        case i.NOEMBED:
        case i.NOFRAMES:
        case i.NOSCRIPT: {
          this.tokenizer.state = F.RAWTEXT;
          break;
        }
        case i.SCRIPT: {
          this.tokenizer.state = F.SCRIPT_DATA;
          break;
        }
        case i.PLAINTEXT: {
          this.tokenizer.state = F.PLAINTEXT;
          break;
        }
      }
  }
  //Tree mutation
  /** @protected */
  _setDocumentType(e) {
    const s = e.name || "", r = e.publicId || "", a = e.systemId || "";
    if (this.treeAdapter.setDocumentType(this.document, s, r, a), e.location) {
      const c = this.treeAdapter.getChildNodes(this.document).find((h) => this.treeAdapter.isDocumentTypeNode(h));
      c && this.treeAdapter.setNodeSourceCodeLocation(c, e.location);
    }
  }
  /** @protected */
  _attachElementToTree(e, s) {
    if (this.options.sourceCodeLocationInfo) {
      const r = s && {
        ...s,
        startTag: s
      };
      this.treeAdapter.setNodeSourceCodeLocation(e, r);
    }
    if (this._shouldFosterParentOnInsertion())
      this._fosterParentElement(e);
    else {
      const r = this.openElements.currentTmplContentOrNode;
      this.treeAdapter.appendChild(r ?? this.document, e);
    }
  }
  /**
   * For self-closing tags. Add an element to the tree, but skip adding it
   * to the stack.
   */
  /** @protected */
  _appendElement(e, s) {
    const r = this.treeAdapter.createElement(e.tagName, s, e.attrs);
    this._attachElementToTree(r, e.location);
  }
  /** @protected */
  _insertElement(e, s) {
    const r = this.treeAdapter.createElement(e.tagName, s, e.attrs);
    this._attachElementToTree(r, e.location), this.openElements.push(r, e.tagID);
  }
  /** @protected */
  _insertFakeElement(e, s) {
    const r = this.treeAdapter.createElement(e, p.HTML, []);
    this._attachElementToTree(r, null), this.openElements.push(r, s);
  }
  /** @protected */
  _insertTemplate(e) {
    const s = this.treeAdapter.createElement(e.tagName, p.HTML, e.attrs), r = this.treeAdapter.createDocumentFragment();
    this.treeAdapter.setTemplateContent(s, r), this._attachElementToTree(s, e.location), this.openElements.push(s, e.tagID), this.options.sourceCodeLocationInfo && this.treeAdapter.setNodeSourceCodeLocation(r, null);
  }
  /** @protected */
  _insertFakeRootElement() {
    const e = this.treeAdapter.createElement(d.HTML, p.HTML, []);
    this.options.sourceCodeLocationInfo && this.treeAdapter.setNodeSourceCodeLocation(e, null), this.treeAdapter.appendChild(this.openElements.current, e), this.openElements.push(e, i.HTML);
  }
  /** @protected */
  _appendCommentNode(e, s) {
    const r = this.treeAdapter.createCommentNode(e.data);
    this.treeAdapter.appendChild(s, r), this.options.sourceCodeLocationInfo && this.treeAdapter.setNodeSourceCodeLocation(r, e.location);
  }
  /** @protected */
  _insertCharacters(e) {
    let s, r;
    if (this._shouldFosterParentOnInsertion() ? ({ parent: s, beforeElement: r } = this._findFosterParentingLocation(), r ? this.treeAdapter.insertTextBefore(s, e.chars, r) : this.treeAdapter.insertText(s, e.chars)) : (s = this.openElements.currentTmplContentOrNode, this.treeAdapter.insertText(s, e.chars)), !e.location)
      return;
    const a = this.treeAdapter.getChildNodes(s), n = r ? a.lastIndexOf(r) : a.length, c = a[n - 1];
    if (this.treeAdapter.getNodeSourceCodeLocation(c)) {
      const { endLine: E, endCol: u, endOffset: _ } = e.location;
      this.treeAdapter.updateNodeSourceCodeLocation(c, { endLine: E, endCol: u, endOffset: _ });
    } else this.options.sourceCodeLocationInfo && this.treeAdapter.setNodeSourceCodeLocation(c, e.location);
  }
  /** @protected */
  _adoptNodes(e, s) {
    for (let r = this.treeAdapter.getFirstChild(e); r; r = this.treeAdapter.getFirstChild(e))
      this.treeAdapter.detachNode(r), this.treeAdapter.appendChild(s, r);
  }
  /** @protected */
  _setEndLocation(e, s) {
    if (this.treeAdapter.getNodeSourceCodeLocation(e) && s.location) {
      const r = s.location, a = this.treeAdapter.getTagName(e), n = (
        // NOTE: For cases like <p> <p> </p> - First 'p' closes without a closing
        // tag and for cases like <td> <p> </td> - 'p' closes without a closing tag.
        s.type === C.END_TAG && a === s.tagName ? {
          endTag: { ...r },
          endLine: r.endLine,
          endCol: r.endCol,
          endOffset: r.endOffset
        } : {
          endLine: r.startLine,
          endCol: r.startCol,
          endOffset: r.startOffset
        }
      );
      this.treeAdapter.updateNodeSourceCodeLocation(e, n);
    }
  }
  //Token processing
  shouldProcessStartTagTokenInForeignContent(e) {
    if (!this.currentNotInHTML)
      return !1;
    let s, r;
    return this.openElements.stackTop === 0 && this.fragmentContext ? (s = this.fragmentContext, r = this.fragmentContextID) : { current: s, currentTagId: r } = this.openElements, e.tagID === i.SVG && this.treeAdapter.getTagName(s) === d.ANNOTATION_XML && this.treeAdapter.getNamespaceURI(s) === p.MATHML ? !1 : (
      // Check that `current` is not an integration point for HTML or MathML elements.
      this.tokenizer.inForeignNode || // If it _is_ an integration point, then we might have to check that it is not an HTML
      // integration point.
      (e.tagID === i.MGLYPH || e.tagID === i.MALIGNMARK) && r !== void 0 && !this._isIntegrationPoint(r, s, p.HTML)
    );
  }
  /** @protected */
  _processToken(e) {
    switch (e.type) {
      case C.CHARACTER: {
        this.onCharacter(e);
        break;
      }
      case C.NULL_CHARACTER: {
        this.onNullCharacter(e);
        break;
      }
      case C.COMMENT: {
        this.onComment(e);
        break;
      }
      case C.DOCTYPE: {
        this.onDoctype(e);
        break;
      }
      case C.START_TAG: {
        this._processStartTag(e);
        break;
      }
      case C.END_TAG: {
        this.onEndTag(e);
        break;
      }
      case C.EOF: {
        this.onEof(e);
        break;
      }
      case C.WHITESPACE_CHARACTER: {
        this.onWhitespaceCharacter(e);
        break;
      }
    }
  }
  //Integration points
  /** @protected */
  _isIntegrationPoint(e, s, r) {
    const a = this.treeAdapter.getNamespaceURI(s), n = this.treeAdapter.getAttrList(s);
    return Qr(e, a, n, r);
  }
  //Active formatting elements reconstruction
  /** @protected */
  _reconstructActiveFormattingElements() {
    const e = this.activeFormattingElements.entries.length;
    if (e) {
      const s = this.activeFormattingElements.entries.findIndex((a) => a.type === P.Marker || this.openElements.contains(a.element)), r = s === -1 ? e - 1 : s - 1;
      for (let a = r; a >= 0; a--) {
        const n = this.activeFormattingElements.entries[a];
        this._insertElement(n.token, this.treeAdapter.getNamespaceURI(n.element)), n.element = this.openElements.current;
      }
    }
  }
  //Close elements
  /** @protected */
  _closeTableCell() {
    this.openElements.generateImpliedEndTags(), this.openElements.popUntilTableCellPopped(), this.activeFormattingElements.clearToLastMarker(), this.insertionMode = l.IN_ROW;
  }
  /** @protected */
  _closePElement() {
    this.openElements.generateImpliedEndTagsWithExclusion(i.P), this.openElements.popUntilTagNamePopped(i.P);
  }
  //Insertion modes
  /** @protected */
  _resetInsertionMode() {
    for (let e = this.openElements.stackTop; e >= 0; e--)
      switch (e === 0 && this.fragmentContext ? this.fragmentContextID : this.openElements.tagIDs[e]) {
        case i.TR: {
          this.insertionMode = l.IN_ROW;
          return;
        }
        case i.TBODY:
        case i.THEAD:
        case i.TFOOT: {
          this.insertionMode = l.IN_TABLE_BODY;
          return;
        }
        case i.CAPTION: {
          this.insertionMode = l.IN_CAPTION;
          return;
        }
        case i.COLGROUP: {
          this.insertionMode = l.IN_COLUMN_GROUP;
          return;
        }
        case i.TABLE: {
          this.insertionMode = l.IN_TABLE;
          return;
        }
        case i.BODY: {
          this.insertionMode = l.IN_BODY;
          return;
        }
        case i.FRAMESET: {
          this.insertionMode = l.IN_FRAMESET;
          return;
        }
        case i.SELECT: {
          this._resetInsertionModeForSelect(e);
          return;
        }
        case i.TEMPLATE: {
          this.insertionMode = this.tmplInsertionModeStack[0];
          return;
        }
        case i.HTML: {
          this.insertionMode = this.headElement ? l.AFTER_HEAD : l.BEFORE_HEAD;
          return;
        }
        case i.TD:
        case i.TH: {
          if (e > 0) {
            this.insertionMode = l.IN_CELL;
            return;
          }
          break;
        }
        case i.HEAD: {
          if (e > 0) {
            this.insertionMode = l.IN_HEAD;
            return;
          }
          break;
        }
      }
    this.insertionMode = l.IN_BODY;
  }
  /** @protected */
  _resetInsertionModeForSelect(e) {
    if (e > 0)
      for (let s = e - 1; s > 0; s--) {
        const r = this.openElements.tagIDs[s];
        if (r === i.TEMPLATE)
          break;
        if (r === i.TABLE) {
          this.insertionMode = l.IN_SELECT_IN_TABLE;
          return;
        }
      }
    this.insertionMode = l.IN_SELECT;
  }
  //Foster parenting
  /** @protected */
  _isElementCausesFosterParenting(e) {
    return Ms.has(e);
  }
  /** @protected */
  _shouldFosterParentOnInsertion() {
    return this.fosterParentingEnabled && this.openElements.currentTagId !== void 0 && this._isElementCausesFosterParenting(this.openElements.currentTagId);
  }
  /** @protected */
  _findFosterParentingLocation() {
    for (let e = this.openElements.stackTop; e >= 0; e--) {
      const s = this.openElements.items[e];
      switch (this.openElements.tagIDs[e]) {
        case i.TEMPLATE: {
          if (this.treeAdapter.getNamespaceURI(s) === p.HTML)
            return { parent: this.treeAdapter.getTemplateContent(s), beforeElement: null };
          break;
        }
        case i.TABLE: {
          const r = this.treeAdapter.getParentNode(s);
          return r ? { parent: r, beforeElement: s } : { parent: this.openElements.items[e - 1], beforeElement: null };
        }
      }
    }
    return { parent: this.openElements.items[0], beforeElement: null };
  }
  /** @protected */
  _fosterParentElement(e) {
    const s = this._findFosterParentingLocation();
    s.beforeElement ? this.treeAdapter.insertBefore(s.parent, e, s.beforeElement) : this.treeAdapter.appendChild(s.parent, e);
  }
  //Special elements
  /** @protected */
  _isSpecialElement(e, s) {
    const r = this.treeAdapter.getNamespaceURI(e);
    return hr[r].has(s);
  }
  /** @internal */
  onCharacter(e) {
    if (this.skipNextNewLine = !1, this.tokenizer.inForeignNode) {
      bn(this, e);
      return;
    }
    switch (this.insertionMode) {
      case l.INITIAL: {
        oe(this, e);
        break;
      }
      case l.BEFORE_HTML: {
        ue(this, e);
        break;
      }
      case l.BEFORE_HEAD: {
        Ee(this, e);
        break;
      }
      case l.IN_HEAD: {
        ge(this, e);
        break;
      }
      case l.IN_HEAD_NO_SCRIPT: {
        _e(this, e);
        break;
      }
      case l.AFTER_HEAD: {
        me(this, e);
        break;
      }
      case l.IN_BODY:
      case l.IN_CAPTION:
      case l.IN_CELL:
      case l.IN_TEMPLATE: {
        Ps(this, e);
        break;
      }
      case l.TEXT:
      case l.IN_SELECT:
      case l.IN_SELECT_IN_TABLE: {
        this._insertCharacters(e);
        break;
      }
      case l.IN_TABLE:
      case l.IN_TABLE_BODY:
      case l.IN_ROW: {
        ht(this, e);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ws(this, e);
        break;
      }
      case l.IN_COLUMN_GROUP: {
        We(this, e);
        break;
      }
      case l.AFTER_BODY: {
        Ge(this, e);
        break;
      }
      case l.AFTER_AFTER_BODY: {
        xe(this, e);
        break;
      }
    }
  }
  /** @internal */
  onNullCharacter(e) {
    if (this.skipNextNewLine = !1, this.tokenizer.inForeignNode) {
      Cn(this, e);
      return;
    }
    switch (this.insertionMode) {
      case l.INITIAL: {
        oe(this, e);
        break;
      }
      case l.BEFORE_HTML: {
        ue(this, e);
        break;
      }
      case l.BEFORE_HEAD: {
        Ee(this, e);
        break;
      }
      case l.IN_HEAD: {
        ge(this, e);
        break;
      }
      case l.IN_HEAD_NO_SCRIPT: {
        _e(this, e);
        break;
      }
      case l.AFTER_HEAD: {
        me(this, e);
        break;
      }
      case l.TEXT: {
        this._insertCharacters(e);
        break;
      }
      case l.IN_TABLE:
      case l.IN_TABLE_BODY:
      case l.IN_ROW: {
        ht(this, e);
        break;
      }
      case l.IN_COLUMN_GROUP: {
        We(this, e);
        break;
      }
      case l.AFTER_BODY: {
        Ge(this, e);
        break;
      }
      case l.AFTER_AFTER_BODY: {
        xe(this, e);
        break;
      }
    }
  }
  /** @internal */
  onComment(e) {
    if (this.skipNextNewLine = !1, this.currentNotInHTML) {
      _t(this, e);
      return;
    }
    switch (this.insertionMode) {
      case l.INITIAL:
      case l.BEFORE_HTML:
      case l.BEFORE_HEAD:
      case l.IN_HEAD:
      case l.IN_HEAD_NO_SCRIPT:
      case l.AFTER_HEAD:
      case l.IN_BODY:
      case l.IN_TABLE:
      case l.IN_CAPTION:
      case l.IN_COLUMN_GROUP:
      case l.IN_TABLE_BODY:
      case l.IN_ROW:
      case l.IN_CELL:
      case l.IN_SELECT:
      case l.IN_SELECT_IN_TABLE:
      case l.IN_TEMPLATE:
      case l.IN_FRAMESET:
      case l.AFTER_FRAMESET: {
        _t(this, e);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ae(this, e);
        break;
      }
      case l.AFTER_BODY: {
        qr(this, e);
        break;
      }
      case l.AFTER_AFTER_BODY:
      case l.AFTER_AFTER_FRAMESET: {
        ea(this, e);
        break;
      }
    }
  }
  /** @internal */
  onDoctype(e) {
    switch (this.skipNextNewLine = !1, this.insertionMode) {
      case l.INITIAL: {
        ta(this, e);
        break;
      }
      case l.BEFORE_HEAD:
      case l.IN_HEAD:
      case l.IN_HEAD_NO_SCRIPT:
      case l.AFTER_HEAD: {
        this._err(e, g.misplacedDoctype);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ae(this, e);
        break;
      }
    }
  }
  /** @internal */
  onStartTag(e) {
    this.skipNextNewLine = !1, this.currentToken = e, this._processStartTag(e), e.selfClosing && !e.ackSelfClosing && this._err(e, g.nonVoidHtmlElementStartTagWithTrailingSolidus);
  }
  /**
   * Processes a given start tag.
   *
   * `onStartTag` checks if a self-closing tag was recognized. When a token
   * is moved inbetween multiple insertion modes, this check for self-closing
   * could lead to false positives. To avoid this, `_processStartTag` is used
   * for nested calls.
   *
   * @param token The token to process.
   * @protected
   */
  _processStartTag(e) {
    this.shouldProcessStartTagTokenInForeignContent(e) ? Nn(this, e) : this._startTagOutsideForeignContent(e);
  }
  /** @protected */
  _startTagOutsideForeignContent(e) {
    switch (this.insertionMode) {
      case l.INITIAL: {
        oe(this, e);
        break;
      }
      case l.BEFORE_HTML: {
        sa(this, e);
        break;
      }
      case l.BEFORE_HEAD: {
        ra(this, e);
        break;
      }
      case l.IN_HEAD: {
        x(this, e);
        break;
      }
      case l.IN_HEAD_NO_SCRIPT: {
        oa(this, e);
        break;
      }
      case l.AFTER_HEAD: {
        ca(this, e);
        break;
      }
      case l.IN_BODY: {
        L(this, e);
        break;
      }
      case l.IN_TABLE: {
        se(this, e);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ae(this, e);
        break;
      }
      case l.IN_CAPTION: {
        nn(this, e);
        break;
      }
      case l.IN_COLUMN_GROUP: {
        yt(this, e);
        break;
      }
      case l.IN_TABLE_BODY: {
        ze(this, e);
        break;
      }
      case l.IN_ROW: {
        qe(this, e);
        break;
      }
      case l.IN_CELL: {
        cn(this, e);
        break;
      }
      case l.IN_SELECT: {
        Js(this, e);
        break;
      }
      case l.IN_SELECT_IN_TABLE: {
        hn(this, e);
        break;
      }
      case l.IN_TEMPLATE: {
        un(this, e);
        break;
      }
      case l.AFTER_BODY: {
        gn(this, e);
        break;
      }
      case l.IN_FRAMESET: {
        _n(this, e);
        break;
      }
      case l.AFTER_FRAMESET: {
        pn(this, e);
        break;
      }
      case l.AFTER_AFTER_BODY: {
        fn(this, e);
        break;
      }
      case l.AFTER_AFTER_FRAMESET: {
        In(this, e);
        break;
      }
    }
  }
  /** @internal */
  onEndTag(e) {
    this.skipNextNewLine = !1, this.currentToken = e, this.currentNotInHTML ? Dn(this, e) : this._endTagOutsideForeignContent(e);
  }
  /** @protected */
  _endTagOutsideForeignContent(e) {
    switch (this.insertionMode) {
      case l.INITIAL: {
        oe(this, e);
        break;
      }
      case l.BEFORE_HTML: {
        ia(this, e);
        break;
      }
      case l.BEFORE_HEAD: {
        aa(this, e);
        break;
      }
      case l.IN_HEAD: {
        na(this, e);
        break;
      }
      case l.IN_HEAD_NO_SCRIPT: {
        Aa(this, e);
        break;
      }
      case l.AFTER_HEAD: {
        la(this, e);
        break;
      }
      case l.IN_BODY: {
        je(this, e);
        break;
      }
      case l.TEXT: {
        Xa(this, e);
        break;
      }
      case l.IN_TABLE: {
        De(this, e);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ae(this, e);
        break;
      }
      case l.IN_CAPTION: {
        on(this, e);
        break;
      }
      case l.IN_COLUMN_GROUP: {
        An(this, e);
        break;
      }
      case l.IN_TABLE_BODY: {
        mt(this, e);
        break;
      }
      case l.IN_ROW: {
        $s(this, e);
        break;
      }
      case l.IN_CELL: {
        ln(this, e);
        break;
      }
      case l.IN_SELECT: {
        Zs(this, e);
        break;
      }
      case l.IN_SELECT_IN_TABLE: {
        dn(this, e);
        break;
      }
      case l.IN_TEMPLATE: {
        En(this, e);
        break;
      }
      case l.AFTER_BODY: {
        Vs(this, e);
        break;
      }
      case l.IN_FRAMESET: {
        mn(this, e);
        break;
      }
      case l.AFTER_FRAMESET: {
        Tn(this, e);
        break;
      }
      case l.AFTER_AFTER_BODY: {
        xe(this, e);
        break;
      }
    }
  }
  /** @internal */
  onEof(e) {
    switch (this.insertionMode) {
      case l.INITIAL: {
        oe(this, e);
        break;
      }
      case l.BEFORE_HTML: {
        ue(this, e);
        break;
      }
      case l.BEFORE_HEAD: {
        Ee(this, e);
        break;
      }
      case l.IN_HEAD: {
        ge(this, e);
        break;
      }
      case l.IN_HEAD_NO_SCRIPT: {
        _e(this, e);
        break;
      }
      case l.AFTER_HEAD: {
        me(this, e);
        break;
      }
      case l.IN_BODY:
      case l.IN_TABLE:
      case l.IN_CAPTION:
      case l.IN_COLUMN_GROUP:
      case l.IN_TABLE_BODY:
      case l.IN_ROW:
      case l.IN_CELL:
      case l.IN_SELECT:
      case l.IN_SELECT_IN_TABLE: {
        Ys(this, e);
        break;
      }
      case l.TEXT: {
        Va(this, e);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ae(this, e);
        break;
      }
      case l.IN_TEMPLATE: {
        Xs(this, e);
        break;
      }
      case l.AFTER_BODY:
      case l.IN_FRAMESET:
      case l.AFTER_FRAMESET:
      case l.AFTER_AFTER_BODY:
      case l.AFTER_AFTER_FRAMESET: {
        Bt(this, e);
        break;
      }
    }
  }
  /** @internal */
  onWhitespaceCharacter(e) {
    if (this.skipNextNewLine && (this.skipNextNewLine = !1, e.chars.charCodeAt(0) === o.LINE_FEED)) {
      if (e.chars.length === 1)
        return;
      e.chars = e.chars.substr(1);
    }
    if (this.tokenizer.inForeignNode) {
      this._insertCharacters(e);
      return;
    }
    switch (this.insertionMode) {
      case l.IN_HEAD:
      case l.IN_HEAD_NO_SCRIPT:
      case l.AFTER_HEAD:
      case l.TEXT:
      case l.IN_COLUMN_GROUP:
      case l.IN_SELECT:
      case l.IN_SELECT_IN_TABLE:
      case l.IN_FRAMESET:
      case l.AFTER_FRAMESET: {
        this._insertCharacters(e);
        break;
      }
      case l.IN_BODY:
      case l.IN_CAPTION:
      case l.IN_CELL:
      case l.IN_TEMPLATE:
      case l.AFTER_BODY:
      case l.AFTER_AFTER_BODY:
      case l.AFTER_AFTER_FRAMESET: {
        xs(this, e);
        break;
      }
      case l.IN_TABLE:
      case l.IN_TABLE_BODY:
      case l.IN_ROW: {
        ht(this, e);
        break;
      }
      case l.IN_TABLE_TEXT: {
        Ks(this, e);
        break;
      }
    }
  }
}
function Jr(t, e) {
  let s = t.activeFormattingElements.getElementEntryInScopeWithTagName(e.tagName);
  return s ? t.openElements.contains(s.element) ? t.openElements.hasInScope(e.tagID) || (s = null) : (t.activeFormattingElements.removeEntry(s), s = null) : Qs(t, e), s;
}
function Zr(t, e) {
  let s = null, r = t.openElements.stackTop;
  for (; r >= 0; r--) {
    const a = t.openElements.items[r];
    if (a === e.element)
      break;
    t._isSpecialElement(a, t.openElements.tagIDs[r]) && (s = a);
  }
  return s || (t.openElements.shortenToLength(Math.max(r, 0)), t.activeFormattingElements.removeEntry(e)), s;
}
function Xr(t, e, s) {
  let r = e, a = t.openElements.getCommonAncestor(e);
  for (let n = 0, c = a; c !== s; n++, c = a) {
    a = t.openElements.getCommonAncestor(c);
    const h = t.activeFormattingElements.getElementEntry(c), E = h && n >= Wr;
    !h || E ? (E && t.activeFormattingElements.removeEntry(h), t.openElements.remove(c)) : (c = Vr(t, h), r === e && (t.activeFormattingElements.bookmark = h), t.treeAdapter.detachNode(r), t.treeAdapter.appendChild(c, r), r = c);
  }
  return r;
}
function Vr(t, e) {
  const s = t.treeAdapter.getNamespaceURI(e.element), r = t.treeAdapter.createElement(e.token.tagName, s, e.token.attrs);
  return t.openElements.replace(e.element, r), e.element = r, r;
}
function jr(t, e, s) {
  const r = t.treeAdapter.getTagName(e), a = Xe(r);
  if (t._isElementCausesFosterParenting(a))
    t._fosterParentElement(s);
  else {
    const n = t.treeAdapter.getNamespaceURI(e);
    a === i.TEMPLATE && n === p.HTML && (e = t.treeAdapter.getTemplateContent(e)), t.treeAdapter.appendChild(e, s);
  }
}
function zr(t, e, s) {
  const r = t.treeAdapter.getNamespaceURI(s.element), { token: a } = s, n = t.treeAdapter.createElement(a.tagName, r, a.attrs);
  t._adoptNodes(e, n), t.treeAdapter.appendChild(e, n), t.activeFormattingElements.insertElementAfterBookmark(n, a), t.activeFormattingElements.removeEntry(s), t.openElements.remove(s.element), t.openElements.insertAfter(e, n, a.tagID);
}
function St(t, e) {
  for (let s = 0; s < Kr; s++) {
    const r = Jr(t, e);
    if (!r)
      break;
    const a = Zr(t, r);
    if (!a)
      break;
    t.activeFormattingElements.bookmark = r;
    const n = Xr(t, a, r.element), c = t.openElements.getCommonAncestor(r.element);
    t.treeAdapter.detachNode(n), c && jr(t, c, n), zr(t, a, r);
  }
}
function _t(t, e) {
  t._appendCommentNode(e, t.openElements.currentTmplContentOrNode);
}
function qr(t, e) {
  t._appendCommentNode(e, t.openElements.items[0]);
}
function ea(t, e) {
  t._appendCommentNode(e, t.document);
}
function Bt(t, e) {
  if (t.stopped = !0, e.location) {
    const s = t.fragmentContext ? 0 : 2;
    for (let r = t.openElements.stackTop; r >= s; r--)
      t._setEndLocation(t.openElements.items[r], e);
    if (!t.fragmentContext && t.openElements.stackTop >= 0) {
      const r = t.openElements.items[0], a = t.treeAdapter.getNodeSourceCodeLocation(r);
      if (a && !a.endTag && (t._setEndLocation(r, e), t.openElements.stackTop >= 1)) {
        const n = t.openElements.items[1], c = t.treeAdapter.getNodeSourceCodeLocation(n);
        c && !c.endTag && t._setEndLocation(n, e);
      }
    }
  }
}
function ta(t, e) {
  t._setDocumentType(e);
  const s = e.forceQuirks ? v.QUIRKS : Or(e);
  Rr(e) || t._err(e, g.nonConformingDoctype), t.treeAdapter.setDocumentMode(t.document, s), t.insertionMode = l.BEFORE_HTML;
}
function oe(t, e) {
  t._err(e, g.missingDoctype, !0), t.treeAdapter.setDocumentMode(t.document, v.QUIRKS), t.insertionMode = l.BEFORE_HTML, t._processToken(e);
}
function sa(t, e) {
  e.tagID === i.HTML ? (t._insertElement(e, p.HTML), t.insertionMode = l.BEFORE_HEAD) : ue(t, e);
}
function ia(t, e) {
  const s = e.tagID;
  (s === i.HTML || s === i.HEAD || s === i.BODY || s === i.BR) && ue(t, e);
}
function ue(t, e) {
  t._insertFakeRootElement(), t.insertionMode = l.BEFORE_HEAD, t._processToken(e);
}
function ra(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.HEAD: {
      t._insertElement(e, p.HTML), t.headElement = t.openElements.current, t.insertionMode = l.IN_HEAD;
      break;
    }
    default:
      Ee(t, e);
  }
}
function aa(t, e) {
  const s = e.tagID;
  s === i.HEAD || s === i.BODY || s === i.HTML || s === i.BR ? Ee(t, e) : t._err(e, g.endTagWithoutMatchingOpenElement);
}
function Ee(t, e) {
  t._insertFakeElement(d.HEAD, i.HEAD), t.headElement = t.openElements.current, t.insertionMode = l.IN_HEAD, t._processToken(e);
}
function x(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.BASE:
    case i.BASEFONT:
    case i.BGSOUND:
    case i.LINK:
    case i.META: {
      t._appendElement(e, p.HTML), e.ackSelfClosing = !0;
      break;
    }
    case i.TITLE: {
      t._switchToTextParsing(e, F.RCDATA);
      break;
    }
    case i.NOSCRIPT: {
      t.options.scriptingEnabled ? t._switchToTextParsing(e, F.RAWTEXT) : (t._insertElement(e, p.HTML), t.insertionMode = l.IN_HEAD_NO_SCRIPT);
      break;
    }
    case i.NOFRAMES:
    case i.STYLE: {
      t._switchToTextParsing(e, F.RAWTEXT);
      break;
    }
    case i.SCRIPT: {
      t._switchToTextParsing(e, F.SCRIPT_DATA);
      break;
    }
    case i.TEMPLATE: {
      t._insertTemplate(e), t.activeFormattingElements.insertMarker(), t.framesetOk = !1, t.insertionMode = l.IN_TEMPLATE, t.tmplInsertionModeStack.unshift(l.IN_TEMPLATE);
      break;
    }
    case i.HEAD: {
      t._err(e, g.misplacedStartTagForHeadElement);
      break;
    }
    default:
      ge(t, e);
  }
}
function na(t, e) {
  switch (e.tagID) {
    case i.HEAD: {
      t.openElements.pop(), t.insertionMode = l.AFTER_HEAD;
      break;
    }
    case i.BODY:
    case i.BR:
    case i.HTML: {
      ge(t, e);
      break;
    }
    case i.TEMPLATE: {
      V(t, e);
      break;
    }
    default:
      t._err(e, g.endTagWithoutMatchingOpenElement);
  }
}
function V(t, e) {
  t.openElements.tmplCount > 0 ? (t.openElements.generateImpliedEndTagsThoroughly(), t.openElements.currentTagId !== i.TEMPLATE && t._err(e, g.closingOfElementWithOpenChildElements), t.openElements.popUntilTagNamePopped(i.TEMPLATE), t.activeFormattingElements.clearToLastMarker(), t.tmplInsertionModeStack.shift(), t._resetInsertionMode()) : t._err(e, g.endTagWithoutMatchingOpenElement);
}
function ge(t, e) {
  t.openElements.pop(), t.insertionMode = l.AFTER_HEAD, t._processToken(e);
}
function oa(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.BASEFONT:
    case i.BGSOUND:
    case i.HEAD:
    case i.LINK:
    case i.META:
    case i.NOFRAMES:
    case i.STYLE: {
      x(t, e);
      break;
    }
    case i.NOSCRIPT: {
      t._err(e, g.nestedNoscriptInHead);
      break;
    }
    default:
      _e(t, e);
  }
}
function Aa(t, e) {
  switch (e.tagID) {
    case i.NOSCRIPT: {
      t.openElements.pop(), t.insertionMode = l.IN_HEAD;
      break;
    }
    case i.BR: {
      _e(t, e);
      break;
    }
    default:
      t._err(e, g.endTagWithoutMatchingOpenElement);
  }
}
function _e(t, e) {
  const s = e.type === C.EOF ? g.openElementsLeftAfterEof : g.disallowedContentInNoscriptInHead;
  t._err(e, s), t.openElements.pop(), t.insertionMode = l.IN_HEAD, t._processToken(e);
}
function ca(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.BODY: {
      t._insertElement(e, p.HTML), t.framesetOk = !1, t.insertionMode = l.IN_BODY;
      break;
    }
    case i.FRAMESET: {
      t._insertElement(e, p.HTML), t.insertionMode = l.IN_FRAMESET;
      break;
    }
    case i.BASE:
    case i.BASEFONT:
    case i.BGSOUND:
    case i.LINK:
    case i.META:
    case i.NOFRAMES:
    case i.SCRIPT:
    case i.STYLE:
    case i.TEMPLATE:
    case i.TITLE: {
      t._err(e, g.abandonedHeadElementChild), t.openElements.push(t.headElement, i.HEAD), x(t, e), t.openElements.remove(t.headElement);
      break;
    }
    case i.HEAD: {
      t._err(e, g.misplacedStartTagForHeadElement);
      break;
    }
    default:
      me(t, e);
  }
}
function la(t, e) {
  switch (e.tagID) {
    case i.BODY:
    case i.HTML:
    case i.BR: {
      me(t, e);
      break;
    }
    case i.TEMPLATE: {
      V(t, e);
      break;
    }
    default:
      t._err(e, g.endTagWithoutMatchingOpenElement);
  }
}
function me(t, e) {
  t._insertFakeElement(d.BODY, i.BODY), t.insertionMode = l.IN_BODY, Ve(t, e);
}
function Ve(t, e) {
  switch (e.type) {
    case C.CHARACTER: {
      Ps(t, e);
      break;
    }
    case C.WHITESPACE_CHARACTER: {
      xs(t, e);
      break;
    }
    case C.COMMENT: {
      _t(t, e);
      break;
    }
    case C.START_TAG: {
      L(t, e);
      break;
    }
    case C.END_TAG: {
      je(t, e);
      break;
    }
    case C.EOF: {
      Ys(t, e);
      break;
    }
  }
}
function xs(t, e) {
  t._reconstructActiveFormattingElements(), t._insertCharacters(e);
}
function Ps(t, e) {
  t._reconstructActiveFormattingElements(), t._insertCharacters(e), t.framesetOk = !1;
}
function ha(t, e) {
  t.openElements.tmplCount === 0 && t.treeAdapter.adoptAttributes(t.openElements.items[0], e.attrs);
}
function da(t, e) {
  const s = t.openElements.tryPeekProperlyNestedBodyElement();
  s && t.openElements.tmplCount === 0 && (t.framesetOk = !1, t.treeAdapter.adoptAttributes(s, e.attrs));
}
function ua(t, e) {
  const s = t.openElements.tryPeekProperlyNestedBodyElement();
  t.framesetOk && s && (t.treeAdapter.detachNode(s), t.openElements.popAllUpToHtmlElement(), t._insertElement(e, p.HTML), t.insertionMode = l.IN_FRAMESET);
}
function Ea(t, e) {
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._insertElement(e, p.HTML);
}
function ga(t, e) {
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t.openElements.currentTagId !== void 0 && gt.has(t.openElements.currentTagId) && t.openElements.pop(), t._insertElement(e, p.HTML);
}
function _a(t, e) {
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._insertElement(e, p.HTML), t.skipNextNewLine = !0, t.framesetOk = !1;
}
function ma(t, e) {
  const s = t.openElements.tmplCount > 0;
  (!t.formElement || s) && (t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._insertElement(e, p.HTML), s || (t.formElement = t.openElements.current));
}
function pa(t, e) {
  t.framesetOk = !1;
  const s = e.tagID;
  for (let r = t.openElements.stackTop; r >= 0; r--) {
    const a = t.openElements.tagIDs[r];
    if (s === i.LI && a === i.LI || (s === i.DD || s === i.DT) && (a === i.DD || a === i.DT)) {
      t.openElements.generateImpliedEndTagsWithExclusion(a), t.openElements.popUntilTagNamePopped(a);
      break;
    }
    if (a !== i.ADDRESS && a !== i.DIV && a !== i.P && t._isSpecialElement(t.openElements.items[r], a))
      break;
  }
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._insertElement(e, p.HTML);
}
function Ta(t, e) {
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._insertElement(e, p.HTML), t.tokenizer.state = F.PLAINTEXT;
}
function fa(t, e) {
  t.openElements.hasInScope(i.BUTTON) && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilTagNamePopped(i.BUTTON)), t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML), t.framesetOk = !1;
}
function Ia(t, e) {
  const s = t.activeFormattingElements.getElementEntryInScopeWithTagName(d.A);
  s && (St(t, e), t.openElements.remove(s.element), t.activeFormattingElements.removeEntry(s)), t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML), t.activeFormattingElements.pushElement(t.openElements.current, e);
}
function Ca(t, e) {
  t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML), t.activeFormattingElements.pushElement(t.openElements.current, e);
}
function ba(t, e) {
  t._reconstructActiveFormattingElements(), t.openElements.hasInScope(i.NOBR) && (St(t, e), t._reconstructActiveFormattingElements()), t._insertElement(e, p.HTML), t.activeFormattingElements.pushElement(t.openElements.current, e);
}
function Na(t, e) {
  t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML), t.activeFormattingElements.insertMarker(), t.framesetOk = !1;
}
function Da(t, e) {
  t.treeAdapter.getDocumentMode(t.document) !== v.QUIRKS && t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._insertElement(e, p.HTML), t.framesetOk = !1, t.insertionMode = l.IN_TABLE;
}
function Hs(t, e) {
  t._reconstructActiveFormattingElements(), t._appendElement(e, p.HTML), t.framesetOk = !1, e.ackSelfClosing = !0;
}
function Us(t) {
  const e = ys(t, Z.TYPE);
  return e != null && e.toLowerCase() === Yr;
}
function Sa(t, e) {
  t._reconstructActiveFormattingElements(), t._appendElement(e, p.HTML), Us(e) || (t.framesetOk = !1), e.ackSelfClosing = !0;
}
function Ba(t, e) {
  t._appendElement(e, p.HTML), e.ackSelfClosing = !0;
}
function ya(t, e) {
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._appendElement(e, p.HTML), t.framesetOk = !1, e.ackSelfClosing = !0;
}
function Ra(t, e) {
  e.tagName = d.IMG, e.tagID = i.IMG, Hs(t, e);
}
function Oa(t, e) {
  t._insertElement(e, p.HTML), t.skipNextNewLine = !0, t.tokenizer.state = F.RCDATA, t.originalInsertionMode = t.insertionMode, t.framesetOk = !1, t.insertionMode = l.TEXT;
}
function La(t, e) {
  t.openElements.hasInButtonScope(i.P) && t._closePElement(), t._reconstructActiveFormattingElements(), t.framesetOk = !1, t._switchToTextParsing(e, F.RAWTEXT);
}
function wa(t, e) {
  t.framesetOk = !1, t._switchToTextParsing(e, F.RAWTEXT);
}
function ns(t, e) {
  t._switchToTextParsing(e, F.RAWTEXT);
}
function ka(t, e) {
  t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML), t.framesetOk = !1, t.insertionMode = t.insertionMode === l.IN_TABLE || t.insertionMode === l.IN_CAPTION || t.insertionMode === l.IN_TABLE_BODY || t.insertionMode === l.IN_ROW || t.insertionMode === l.IN_CELL ? l.IN_SELECT_IN_TABLE : l.IN_SELECT;
}
function Fa(t, e) {
  t.openElements.currentTagId === i.OPTION && t.openElements.pop(), t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML);
}
function va(t, e) {
  t.openElements.hasInScope(i.RUBY) && t.openElements.generateImpliedEndTags(), t._insertElement(e, p.HTML);
}
function Ma(t, e) {
  t.openElements.hasInScope(i.RUBY) && t.openElements.generateImpliedEndTagsWithExclusion(i.RTC), t._insertElement(e, p.HTML);
}
function xa(t, e) {
  t._reconstructActiveFormattingElements(), Fs(e), Dt(e), e.selfClosing ? t._appendElement(e, p.MATHML) : t._insertElement(e, p.MATHML), e.ackSelfClosing = !0;
}
function Pa(t, e) {
  t._reconstructActiveFormattingElements(), vs(e), Dt(e), e.selfClosing ? t._appendElement(e, p.SVG) : t._insertElement(e, p.SVG), e.ackSelfClosing = !0;
}
function os(t, e) {
  t._reconstructActiveFormattingElements(), t._insertElement(e, p.HTML);
}
function L(t, e) {
  switch (e.tagID) {
    case i.I:
    case i.S:
    case i.B:
    case i.U:
    case i.EM:
    case i.TT:
    case i.BIG:
    case i.CODE:
    case i.FONT:
    case i.SMALL:
    case i.STRIKE:
    case i.STRONG: {
      Ca(t, e);
      break;
    }
    case i.A: {
      Ia(t, e);
      break;
    }
    case i.H1:
    case i.H2:
    case i.H3:
    case i.H4:
    case i.H5:
    case i.H6: {
      ga(t, e);
      break;
    }
    case i.P:
    case i.DL:
    case i.OL:
    case i.UL:
    case i.DIV:
    case i.DIR:
    case i.NAV:
    case i.MAIN:
    case i.MENU:
    case i.ASIDE:
    case i.CENTER:
    case i.FIGURE:
    case i.FOOTER:
    case i.HEADER:
    case i.HGROUP:
    case i.DIALOG:
    case i.DETAILS:
    case i.ADDRESS:
    case i.ARTICLE:
    case i.SEARCH:
    case i.SECTION:
    case i.SUMMARY:
    case i.FIELDSET:
    case i.BLOCKQUOTE:
    case i.FIGCAPTION: {
      Ea(t, e);
      break;
    }
    case i.LI:
    case i.DD:
    case i.DT: {
      pa(t, e);
      break;
    }
    case i.BR:
    case i.IMG:
    case i.WBR:
    case i.AREA:
    case i.EMBED:
    case i.KEYGEN: {
      Hs(t, e);
      break;
    }
    case i.HR: {
      ya(t, e);
      break;
    }
    case i.RB:
    case i.RTC: {
      va(t, e);
      break;
    }
    case i.RT:
    case i.RP: {
      Ma(t, e);
      break;
    }
    case i.PRE:
    case i.LISTING: {
      _a(t, e);
      break;
    }
    case i.XMP: {
      La(t, e);
      break;
    }
    case i.SVG: {
      Pa(t, e);
      break;
    }
    case i.HTML: {
      ha(t, e);
      break;
    }
    case i.BASE:
    case i.LINK:
    case i.META:
    case i.STYLE:
    case i.TITLE:
    case i.SCRIPT:
    case i.BGSOUND:
    case i.BASEFONT:
    case i.TEMPLATE: {
      x(t, e);
      break;
    }
    case i.BODY: {
      da(t, e);
      break;
    }
    case i.FORM: {
      ma(t, e);
      break;
    }
    case i.NOBR: {
      ba(t, e);
      break;
    }
    case i.MATH: {
      xa(t, e);
      break;
    }
    case i.TABLE: {
      Da(t, e);
      break;
    }
    case i.INPUT: {
      Sa(t, e);
      break;
    }
    case i.PARAM:
    case i.TRACK:
    case i.SOURCE: {
      Ba(t, e);
      break;
    }
    case i.IMAGE: {
      Ra(t, e);
      break;
    }
    case i.BUTTON: {
      fa(t, e);
      break;
    }
    case i.APPLET:
    case i.OBJECT:
    case i.MARQUEE: {
      Na(t, e);
      break;
    }
    case i.IFRAME: {
      wa(t, e);
      break;
    }
    case i.SELECT: {
      ka(t, e);
      break;
    }
    case i.OPTION:
    case i.OPTGROUP: {
      Fa(t, e);
      break;
    }
    case i.NOEMBED:
    case i.NOFRAMES: {
      ns(t, e);
      break;
    }
    case i.FRAMESET: {
      ua(t, e);
      break;
    }
    case i.TEXTAREA: {
      Oa(t, e);
      break;
    }
    case i.NOSCRIPT: {
      t.options.scriptingEnabled ? ns(t, e) : os(t, e);
      break;
    }
    case i.PLAINTEXT: {
      Ta(t, e);
      break;
    }
    case i.COL:
    case i.TH:
    case i.TD:
    case i.TR:
    case i.HEAD:
    case i.FRAME:
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD:
    case i.CAPTION:
    case i.COLGROUP:
      break;
    default:
      os(t, e);
  }
}
function Ha(t, e) {
  if (t.openElements.hasInScope(i.BODY) && (t.insertionMode = l.AFTER_BODY, t.options.sourceCodeLocationInfo)) {
    const s = t.openElements.tryPeekProperlyNestedBodyElement();
    s && t._setEndLocation(s, e);
  }
}
function Ua(t, e) {
  t.openElements.hasInScope(i.BODY) && (t.insertionMode = l.AFTER_BODY, Vs(t, e));
}
function Qa(t, e) {
  const s = e.tagID;
  t.openElements.hasInScope(s) && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilTagNamePopped(s));
}
function Ya(t) {
  const e = t.openElements.tmplCount > 0, { formElement: s } = t;
  e || (t.formElement = null), (s || e) && t.openElements.hasInScope(i.FORM) && (t.openElements.generateImpliedEndTags(), e ? t.openElements.popUntilTagNamePopped(i.FORM) : s && t.openElements.remove(s));
}
function Ka(t) {
  t.openElements.hasInButtonScope(i.P) || t._insertFakeElement(d.P, i.P), t._closePElement();
}
function Wa(t) {
  t.openElements.hasInListItemScope(i.LI) && (t.openElements.generateImpliedEndTagsWithExclusion(i.LI), t.openElements.popUntilTagNamePopped(i.LI));
}
function Ga(t, e) {
  const s = e.tagID;
  t.openElements.hasInScope(s) && (t.openElements.generateImpliedEndTagsWithExclusion(s), t.openElements.popUntilTagNamePopped(s));
}
function $a(t) {
  t.openElements.hasNumberedHeaderInScope() && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilNumberedHeaderPopped());
}
function Ja(t, e) {
  const s = e.tagID;
  t.openElements.hasInScope(s) && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilTagNamePopped(s), t.activeFormattingElements.clearToLastMarker());
}
function Za(t) {
  t._reconstructActiveFormattingElements(), t._insertFakeElement(d.BR, i.BR), t.openElements.pop(), t.framesetOk = !1;
}
function Qs(t, e) {
  const s = e.tagName, r = e.tagID;
  for (let a = t.openElements.stackTop; a > 0; a--) {
    const n = t.openElements.items[a], c = t.openElements.tagIDs[a];
    if (r === c && (r !== i.UNKNOWN || t.treeAdapter.getTagName(n) === s)) {
      t.openElements.generateImpliedEndTagsWithExclusion(r), t.openElements.stackTop >= a && t.openElements.shortenToLength(a);
      break;
    }
    if (t._isSpecialElement(n, c))
      break;
  }
}
function je(t, e) {
  switch (e.tagID) {
    case i.A:
    case i.B:
    case i.I:
    case i.S:
    case i.U:
    case i.EM:
    case i.TT:
    case i.BIG:
    case i.CODE:
    case i.FONT:
    case i.NOBR:
    case i.SMALL:
    case i.STRIKE:
    case i.STRONG: {
      St(t, e);
      break;
    }
    case i.P: {
      Ka(t);
      break;
    }
    case i.DL:
    case i.UL:
    case i.OL:
    case i.DIR:
    case i.DIV:
    case i.NAV:
    case i.PRE:
    case i.MAIN:
    case i.MENU:
    case i.ASIDE:
    case i.BUTTON:
    case i.CENTER:
    case i.FIGURE:
    case i.FOOTER:
    case i.HEADER:
    case i.HGROUP:
    case i.DIALOG:
    case i.ADDRESS:
    case i.ARTICLE:
    case i.DETAILS:
    case i.SEARCH:
    case i.SECTION:
    case i.SUMMARY:
    case i.LISTING:
    case i.FIELDSET:
    case i.BLOCKQUOTE:
    case i.FIGCAPTION: {
      Qa(t, e);
      break;
    }
    case i.LI: {
      Wa(t);
      break;
    }
    case i.DD:
    case i.DT: {
      Ga(t, e);
      break;
    }
    case i.H1:
    case i.H2:
    case i.H3:
    case i.H4:
    case i.H5:
    case i.H6: {
      $a(t);
      break;
    }
    case i.BR: {
      Za(t);
      break;
    }
    case i.BODY: {
      Ha(t, e);
      break;
    }
    case i.HTML: {
      Ua(t, e);
      break;
    }
    case i.FORM: {
      Ya(t);
      break;
    }
    case i.APPLET:
    case i.OBJECT:
    case i.MARQUEE: {
      Ja(t, e);
      break;
    }
    case i.TEMPLATE: {
      V(t, e);
      break;
    }
    default:
      Qs(t, e);
  }
}
function Ys(t, e) {
  t.tmplInsertionModeStack.length > 0 ? Xs(t, e) : Bt(t, e);
}
function Xa(t, e) {
  var s;
  e.tagID === i.SCRIPT && ((s = t.scriptHandler) === null || s === void 0 || s.call(t, t.openElements.current)), t.openElements.pop(), t.insertionMode = t.originalInsertionMode;
}
function Va(t, e) {
  t._err(e, g.eofInElementThatCanContainOnlyText), t.openElements.pop(), t.insertionMode = t.originalInsertionMode, t.onEof(e);
}
function ht(t, e) {
  if (t.openElements.currentTagId !== void 0 && Ms.has(t.openElements.currentTagId))
    switch (t.pendingCharacterTokens.length = 0, t.hasNonWhitespacePendingCharacterToken = !1, t.originalInsertionMode = t.insertionMode, t.insertionMode = l.IN_TABLE_TEXT, e.type) {
      case C.CHARACTER: {
        Ws(t, e);
        break;
      }
      case C.WHITESPACE_CHARACTER: {
        Ks(t, e);
        break;
      }
    }
  else
    Be(t, e);
}
function ja(t, e) {
  t.openElements.clearBackToTableContext(), t.activeFormattingElements.insertMarker(), t._insertElement(e, p.HTML), t.insertionMode = l.IN_CAPTION;
}
function za(t, e) {
  t.openElements.clearBackToTableContext(), t._insertElement(e, p.HTML), t.insertionMode = l.IN_COLUMN_GROUP;
}
function qa(t, e) {
  t.openElements.clearBackToTableContext(), t._insertFakeElement(d.COLGROUP, i.COLGROUP), t.insertionMode = l.IN_COLUMN_GROUP, yt(t, e);
}
function en(t, e) {
  t.openElements.clearBackToTableContext(), t._insertElement(e, p.HTML), t.insertionMode = l.IN_TABLE_BODY;
}
function tn(t, e) {
  t.openElements.clearBackToTableContext(), t._insertFakeElement(d.TBODY, i.TBODY), t.insertionMode = l.IN_TABLE_BODY, ze(t, e);
}
function sn(t, e) {
  t.openElements.hasInTableScope(i.TABLE) && (t.openElements.popUntilTagNamePopped(i.TABLE), t._resetInsertionMode(), t._processStartTag(e));
}
function rn(t, e) {
  Us(e) ? t._appendElement(e, p.HTML) : Be(t, e), e.ackSelfClosing = !0;
}
function an(t, e) {
  !t.formElement && t.openElements.tmplCount === 0 && (t._insertElement(e, p.HTML), t.formElement = t.openElements.current, t.openElements.pop());
}
function se(t, e) {
  switch (e.tagID) {
    case i.TD:
    case i.TH:
    case i.TR: {
      tn(t, e);
      break;
    }
    case i.STYLE:
    case i.SCRIPT:
    case i.TEMPLATE: {
      x(t, e);
      break;
    }
    case i.COL: {
      qa(t, e);
      break;
    }
    case i.FORM: {
      an(t, e);
      break;
    }
    case i.TABLE: {
      sn(t, e);
      break;
    }
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD: {
      en(t, e);
      break;
    }
    case i.INPUT: {
      rn(t, e);
      break;
    }
    case i.CAPTION: {
      ja(t, e);
      break;
    }
    case i.COLGROUP: {
      za(t, e);
      break;
    }
    default:
      Be(t, e);
  }
}
function De(t, e) {
  switch (e.tagID) {
    case i.TABLE: {
      t.openElements.hasInTableScope(i.TABLE) && (t.openElements.popUntilTagNamePopped(i.TABLE), t._resetInsertionMode());
      break;
    }
    case i.TEMPLATE: {
      V(t, e);
      break;
    }
    case i.BODY:
    case i.CAPTION:
    case i.COL:
    case i.COLGROUP:
    case i.HTML:
    case i.TBODY:
    case i.TD:
    case i.TFOOT:
    case i.TH:
    case i.THEAD:
    case i.TR:
      break;
    default:
      Be(t, e);
  }
}
function Be(t, e) {
  const s = t.fosterParentingEnabled;
  t.fosterParentingEnabled = !0, Ve(t, e), t.fosterParentingEnabled = s;
}
function Ks(t, e) {
  t.pendingCharacterTokens.push(e);
}
function Ws(t, e) {
  t.pendingCharacterTokens.push(e), t.hasNonWhitespacePendingCharacterToken = !0;
}
function Ae(t, e) {
  let s = 0;
  if (t.hasNonWhitespacePendingCharacterToken)
    for (; s < t.pendingCharacterTokens.length; s++)
      Be(t, t.pendingCharacterTokens[s]);
  else
    for (; s < t.pendingCharacterTokens.length; s++)
      t._insertCharacters(t.pendingCharacterTokens[s]);
  t.insertionMode = t.originalInsertionMode, t._processToken(e);
}
const Gs = /* @__PURE__ */ new Set([i.CAPTION, i.COL, i.COLGROUP, i.TBODY, i.TD, i.TFOOT, i.TH, i.THEAD, i.TR]);
function nn(t, e) {
  const s = e.tagID;
  Gs.has(s) ? t.openElements.hasInTableScope(i.CAPTION) && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilTagNamePopped(i.CAPTION), t.activeFormattingElements.clearToLastMarker(), t.insertionMode = l.IN_TABLE, se(t, e)) : L(t, e);
}
function on(t, e) {
  const s = e.tagID;
  switch (s) {
    case i.CAPTION:
    case i.TABLE: {
      t.openElements.hasInTableScope(i.CAPTION) && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilTagNamePopped(i.CAPTION), t.activeFormattingElements.clearToLastMarker(), t.insertionMode = l.IN_TABLE, s === i.TABLE && De(t, e));
      break;
    }
    case i.BODY:
    case i.COL:
    case i.COLGROUP:
    case i.HTML:
    case i.TBODY:
    case i.TD:
    case i.TFOOT:
    case i.TH:
    case i.THEAD:
    case i.TR:
      break;
    default:
      je(t, e);
  }
}
function yt(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.COL: {
      t._appendElement(e, p.HTML), e.ackSelfClosing = !0;
      break;
    }
    case i.TEMPLATE: {
      x(t, e);
      break;
    }
    default:
      We(t, e);
  }
}
function An(t, e) {
  switch (e.tagID) {
    case i.COLGROUP: {
      t.openElements.currentTagId === i.COLGROUP && (t.openElements.pop(), t.insertionMode = l.IN_TABLE);
      break;
    }
    case i.TEMPLATE: {
      V(t, e);
      break;
    }
    case i.COL:
      break;
    default:
      We(t, e);
  }
}
function We(t, e) {
  t.openElements.currentTagId === i.COLGROUP && (t.openElements.pop(), t.insertionMode = l.IN_TABLE, t._processToken(e));
}
function ze(t, e) {
  switch (e.tagID) {
    case i.TR: {
      t.openElements.clearBackToTableBodyContext(), t._insertElement(e, p.HTML), t.insertionMode = l.IN_ROW;
      break;
    }
    case i.TH:
    case i.TD: {
      t.openElements.clearBackToTableBodyContext(), t._insertFakeElement(d.TR, i.TR), t.insertionMode = l.IN_ROW, qe(t, e);
      break;
    }
    case i.CAPTION:
    case i.COL:
    case i.COLGROUP:
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD: {
      t.openElements.hasTableBodyContextInTableScope() && (t.openElements.clearBackToTableBodyContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE, se(t, e));
      break;
    }
    default:
      se(t, e);
  }
}
function mt(t, e) {
  const s = e.tagID;
  switch (e.tagID) {
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD: {
      t.openElements.hasInTableScope(s) && (t.openElements.clearBackToTableBodyContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE);
      break;
    }
    case i.TABLE: {
      t.openElements.hasTableBodyContextInTableScope() && (t.openElements.clearBackToTableBodyContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE, De(t, e));
      break;
    }
    case i.BODY:
    case i.CAPTION:
    case i.COL:
    case i.COLGROUP:
    case i.HTML:
    case i.TD:
    case i.TH:
    case i.TR:
      break;
    default:
      De(t, e);
  }
}
function qe(t, e) {
  switch (e.tagID) {
    case i.TH:
    case i.TD: {
      t.openElements.clearBackToTableRowContext(), t._insertElement(e, p.HTML), t.insertionMode = l.IN_CELL, t.activeFormattingElements.insertMarker();
      break;
    }
    case i.CAPTION:
    case i.COL:
    case i.COLGROUP:
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD:
    case i.TR: {
      t.openElements.hasInTableScope(i.TR) && (t.openElements.clearBackToTableRowContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE_BODY, ze(t, e));
      break;
    }
    default:
      se(t, e);
  }
}
function $s(t, e) {
  switch (e.tagID) {
    case i.TR: {
      t.openElements.hasInTableScope(i.TR) && (t.openElements.clearBackToTableRowContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE_BODY);
      break;
    }
    case i.TABLE: {
      t.openElements.hasInTableScope(i.TR) && (t.openElements.clearBackToTableRowContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE_BODY, mt(t, e));
      break;
    }
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD: {
      (t.openElements.hasInTableScope(e.tagID) || t.openElements.hasInTableScope(i.TR)) && (t.openElements.clearBackToTableRowContext(), t.openElements.pop(), t.insertionMode = l.IN_TABLE_BODY, mt(t, e));
      break;
    }
    case i.BODY:
    case i.CAPTION:
    case i.COL:
    case i.COLGROUP:
    case i.HTML:
    case i.TD:
    case i.TH:
      break;
    default:
      De(t, e);
  }
}
function cn(t, e) {
  const s = e.tagID;
  Gs.has(s) ? (t.openElements.hasInTableScope(i.TD) || t.openElements.hasInTableScope(i.TH)) && (t._closeTableCell(), qe(t, e)) : L(t, e);
}
function ln(t, e) {
  const s = e.tagID;
  switch (s) {
    case i.TD:
    case i.TH: {
      t.openElements.hasInTableScope(s) && (t.openElements.generateImpliedEndTags(), t.openElements.popUntilTagNamePopped(s), t.activeFormattingElements.clearToLastMarker(), t.insertionMode = l.IN_ROW);
      break;
    }
    case i.TABLE:
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD:
    case i.TR: {
      t.openElements.hasInTableScope(s) && (t._closeTableCell(), $s(t, e));
      break;
    }
    case i.BODY:
    case i.CAPTION:
    case i.COL:
    case i.COLGROUP:
    case i.HTML:
      break;
    default:
      je(t, e);
  }
}
function Js(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.OPTION: {
      t.openElements.currentTagId === i.OPTION && t.openElements.pop(), t._insertElement(e, p.HTML);
      break;
    }
    case i.OPTGROUP: {
      t.openElements.currentTagId === i.OPTION && t.openElements.pop(), t.openElements.currentTagId === i.OPTGROUP && t.openElements.pop(), t._insertElement(e, p.HTML);
      break;
    }
    case i.HR: {
      t.openElements.currentTagId === i.OPTION && t.openElements.pop(), t.openElements.currentTagId === i.OPTGROUP && t.openElements.pop(), t._appendElement(e, p.HTML), e.ackSelfClosing = !0;
      break;
    }
    case i.INPUT:
    case i.KEYGEN:
    case i.TEXTAREA:
    case i.SELECT: {
      t.openElements.hasInSelectScope(i.SELECT) && (t.openElements.popUntilTagNamePopped(i.SELECT), t._resetInsertionMode(), e.tagID !== i.SELECT && t._processStartTag(e));
      break;
    }
    case i.SCRIPT:
    case i.TEMPLATE: {
      x(t, e);
      break;
    }
  }
}
function Zs(t, e) {
  switch (e.tagID) {
    case i.OPTGROUP: {
      t.openElements.stackTop > 0 && t.openElements.currentTagId === i.OPTION && t.openElements.tagIDs[t.openElements.stackTop - 1] === i.OPTGROUP && t.openElements.pop(), t.openElements.currentTagId === i.OPTGROUP && t.openElements.pop();
      break;
    }
    case i.OPTION: {
      t.openElements.currentTagId === i.OPTION && t.openElements.pop();
      break;
    }
    case i.SELECT: {
      t.openElements.hasInSelectScope(i.SELECT) && (t.openElements.popUntilTagNamePopped(i.SELECT), t._resetInsertionMode());
      break;
    }
    case i.TEMPLATE: {
      V(t, e);
      break;
    }
  }
}
function hn(t, e) {
  const s = e.tagID;
  s === i.CAPTION || s === i.TABLE || s === i.TBODY || s === i.TFOOT || s === i.THEAD || s === i.TR || s === i.TD || s === i.TH ? (t.openElements.popUntilTagNamePopped(i.SELECT), t._resetInsertionMode(), t._processStartTag(e)) : Js(t, e);
}
function dn(t, e) {
  const s = e.tagID;
  s === i.CAPTION || s === i.TABLE || s === i.TBODY || s === i.TFOOT || s === i.THEAD || s === i.TR || s === i.TD || s === i.TH ? t.openElements.hasInTableScope(s) && (t.openElements.popUntilTagNamePopped(i.SELECT), t._resetInsertionMode(), t.onEndTag(e)) : Zs(t, e);
}
function un(t, e) {
  switch (e.tagID) {
    // First, handle tags that can start without a mode change
    case i.BASE:
    case i.BASEFONT:
    case i.BGSOUND:
    case i.LINK:
    case i.META:
    case i.NOFRAMES:
    case i.SCRIPT:
    case i.STYLE:
    case i.TEMPLATE:
    case i.TITLE: {
      x(t, e);
      break;
    }
    // Re-process the token in the appropriate mode
    case i.CAPTION:
    case i.COLGROUP:
    case i.TBODY:
    case i.TFOOT:
    case i.THEAD: {
      t.tmplInsertionModeStack[0] = l.IN_TABLE, t.insertionMode = l.IN_TABLE, se(t, e);
      break;
    }
    case i.COL: {
      t.tmplInsertionModeStack[0] = l.IN_COLUMN_GROUP, t.insertionMode = l.IN_COLUMN_GROUP, yt(t, e);
      break;
    }
    case i.TR: {
      t.tmplInsertionModeStack[0] = l.IN_TABLE_BODY, t.insertionMode = l.IN_TABLE_BODY, ze(t, e);
      break;
    }
    case i.TD:
    case i.TH: {
      t.tmplInsertionModeStack[0] = l.IN_ROW, t.insertionMode = l.IN_ROW, qe(t, e);
      break;
    }
    default:
      t.tmplInsertionModeStack[0] = l.IN_BODY, t.insertionMode = l.IN_BODY, L(t, e);
  }
}
function En(t, e) {
  e.tagID === i.TEMPLATE && V(t, e);
}
function Xs(t, e) {
  t.openElements.tmplCount > 0 ? (t.openElements.popUntilTagNamePopped(i.TEMPLATE), t.activeFormattingElements.clearToLastMarker(), t.tmplInsertionModeStack.shift(), t._resetInsertionMode(), t.onEof(e)) : Bt(t, e);
}
function gn(t, e) {
  e.tagID === i.HTML ? L(t, e) : Ge(t, e);
}
function Vs(t, e) {
  var s;
  if (e.tagID === i.HTML) {
    if (t.fragmentContext || (t.insertionMode = l.AFTER_AFTER_BODY), t.options.sourceCodeLocationInfo && t.openElements.tagIDs[0] === i.HTML) {
      t._setEndLocation(t.openElements.items[0], e);
      const r = t.openElements.items[1];
      r && !(!((s = t.treeAdapter.getNodeSourceCodeLocation(r)) === null || s === void 0) && s.endTag) && t._setEndLocation(r, e);
    }
  } else
    Ge(t, e);
}
function Ge(t, e) {
  t.insertionMode = l.IN_BODY, Ve(t, e);
}
function _n(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.FRAMESET: {
      t._insertElement(e, p.HTML);
      break;
    }
    case i.FRAME: {
      t._appendElement(e, p.HTML), e.ackSelfClosing = !0;
      break;
    }
    case i.NOFRAMES: {
      x(t, e);
      break;
    }
  }
}
function mn(t, e) {
  e.tagID === i.FRAMESET && !t.openElements.isRootHtmlElementCurrent() && (t.openElements.pop(), !t.fragmentContext && t.openElements.currentTagId !== i.FRAMESET && (t.insertionMode = l.AFTER_FRAMESET));
}
function pn(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.NOFRAMES: {
      x(t, e);
      break;
    }
  }
}
function Tn(t, e) {
  e.tagID === i.HTML && (t.insertionMode = l.AFTER_AFTER_FRAMESET);
}
function fn(t, e) {
  e.tagID === i.HTML ? L(t, e) : xe(t, e);
}
function xe(t, e) {
  t.insertionMode = l.IN_BODY, Ve(t, e);
}
function In(t, e) {
  switch (e.tagID) {
    case i.HTML: {
      L(t, e);
      break;
    }
    case i.NOFRAMES: {
      x(t, e);
      break;
    }
  }
}
function Cn(t, e) {
  e.chars = S, t._insertCharacters(e);
}
function bn(t, e) {
  t._insertCharacters(e), t.framesetOk = !1;
}
function js(t) {
  for (; t.treeAdapter.getNamespaceURI(t.openElements.current) !== p.HTML && t.openElements.currentTagId !== void 0 && !t._isIntegrationPoint(t.openElements.currentTagId, t.openElements.current); )
    t.openElements.pop();
}
function Nn(t, e) {
  if (xr(e))
    js(t), t._startTagOutsideForeignContent(e);
  else {
    const s = t._getAdjustedCurrentElement(), r = t.treeAdapter.getNamespaceURI(s);
    r === p.MATHML ? Fs(e) : r === p.SVG && (Pr(e), vs(e)), Dt(e), e.selfClosing ? t._appendElement(e, r) : t._insertElement(e, r), e.ackSelfClosing = !0;
  }
}
function Dn(t, e) {
  if (e.tagID === i.P || e.tagID === i.BR) {
    js(t), t._endTagOutsideForeignContent(e);
    return;
  }
  for (let s = t.openElements.stackTop; s > 0; s--) {
    const r = t.openElements.items[s];
    if (t.treeAdapter.getNamespaceURI(r) === p.HTML) {
      t._endTagOutsideForeignContent(e);
      break;
    }
    const a = t.treeAdapter.getTagName(r);
    if (a.toLowerCase() === e.tagName) {
      e.tagName = a, t.openElements.shortenToLength(s);
      break;
    }
  }
}
d.AREA, d.BASE, d.BASEFONT, d.BGSOUND, d.BR, d.COL, d.EMBED, d.FRAME, d.HR, d.IMG, d.INPUT, d.KEYGEN, d.LINK, d.META, d.PARAM, d.SOURCE, d.TRACK, d.WBR;
function Sn(t, e, s) {
  typeof t == "string" && (s = e, e = t, t = null);
  const r = $r.getFragmentParser(t, s);
  return r.tokenizer.write(e, !0), r.getFragment();
}
function M(t) {
  return String(t ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function ie(t) {
  const e = String(t ?? "").trim();
  if (!e) return "";
  const r = e.replace(/\s+/g, "").toLowerCase().match(/^([a-z][a-z0-9+.-]*):/);
  return r && !["http", "https", "mailto", "tel"].includes(r[1]) ? "#" : M(e);
}
const Bn = /* @__PURE__ */ new Set(["strong", "b", "em", "u", "br", "p", "ul", "ol", "li", "a"]), yn = /* @__PURE__ */ new Set(["script", "style", "noscript", "template", "textarea", "title", "iframe", "head"]), Rn = new RegExp("[\\u0000-\\u0020\\u007F]+", "g");
function On(t) {
  const e = String(t ?? "").trim();
  if (!e) return null;
  const s = e.replace(Rn, "").toLowerCase();
  if (s.startsWith("//")) return null;
  if (s.startsWith("/")) return { href: e, external: !1 };
  const r = s.match(/^([a-z][a-z0-9+.-]*):/);
  if (!r) return null;
  const a = r[1];
  return a === "http" || a === "https" ? { href: e, external: !0 } : a === "mailto" ? { href: e, external: !1 } : null;
}
function he(t) {
  let e = "";
  const s = t.childNodes || [];
  for (const r of s) e += Ln(r);
  return e;
}
function Ln(t) {
  if (t.nodeName === "#text") return M(t.value);
  if (!t.tagName) return "";
  const e = t.tagName.toLowerCase();
  if (yn.has(e)) return "";
  if (e === "br") return "<br>";
  if (e === "a") {
    const s = (t.attrs || []).find((n) => n.name === "href"), r = s ? On(s.value) : null;
    if (!r) return he(t);
    const a = r.external ? ' target="_blank" rel="noopener"' : "";
    return `<a href="${M(r.href)}"${a}>${he(t)}</a>`;
  }
  if (Bn.has(e)) {
    const s = e === "b" ? "strong" : e;
    return `<${s}>${he(t)}</${s}>`;
  }
  return he(t);
}
function pe(t) {
  if (t == null) return "";
  const e = typeof t == "string" ? t : String(t), s = Sn(e);
  return he(s);
}
function wn(t) {
  if (!t || typeof t != "object") return "";
  const e = t.data || {};
  switch (t.type) {
    case "header": {
      const s = Number(e.level), r = s >= 1 && s <= 6 ? s : 2;
      return `<h${r}>${pe(String(e.text == null ? "" : e.text))}</h${r}>`;
    }
    case "paragraph":
      return `<p>${pe(String(e.text == null ? "" : e.text))}</p>`;
    case "list": {
      const s = e.style === "ordered" ? "ol" : "ul", a = (Array.isArray(e.items) ? e.items : []).map((n) => `<li>${pe(String(n ?? ""))}</li>`).join("");
      return `<${s}>${a}</${s}>`;
    }
    case "reportTable":
      return Un(e);
    case "image": {
      const s = ie(e.src);
      if (!s) return "";
      const r = M(e.caption == null ? "" : e.caption), a = `<div class="img_caption"><img src="${s}" alt="${r}" /></div>`;
      return e.href ? `<a href="${ie(e.href)}" target="_blank" rel="noopener">${a}</a>` : a;
    }
    default:
      return "";
  }
}
const kn = {
  section: "report-section",
  subtotal: "report-subtotal",
  total: "report-total"
};
function Fn(t) {
  const e = t.length;
  return e === 3 ? ["20%", "15%", "65%"] : e === 2 ? ["50%", "50%"] : t.map(() => `${+(100 / e).toFixed(4)}%`);
}
function vn(t, e, s) {
  if (t.align) return t.align;
  const r = e[s];
  return r && r.align || "left";
}
function Mn(t, e, s) {
  if (typeof t.rich == "boolean") return t.rich;
  const r = e[s];
  return !!(r && r.rich);
}
function xn(t, e, s, r) {
  if (s) {
    const E = pe(String(t.v == null ? "" : t.v));
    return E.trim() === "" ? "<p>&nbsp;</p>" : E;
  }
  const a = M(t.v == null ? "" : t.v), c = e === "center" || e === "right" || r && e === "left" ? ` style="text-align: ${e};"` : "", h = a === "" ? "&nbsp;" : `${a}&nbsp;`;
  return `<p${c}>${h}</p>`;
}
function Pn(t) {
  const e = String(t && t.v != null ? t.v : "").replace(/<[^>]+>/g, "").replace(/&nbsp;/g, "").trim();
  return /[0-9]/.test(e) ? (e.match(/[一-鿿]/g) || []).length <= 2 : !1;
}
function Hn(t, { colSpan: e, rowSpan: s, role: r, cls: a, nowrap: n }) {
  let c = "";
  return e > 1 && (c += ` colspan="${e}"`), s > 1 && (c += ` rowspan="${s}"`), r && (c += ` role="${r}"`), a && (c += ` class="${a}"`), n && (c += ' style="white-space: nowrap;"'), `<td${c}>${t}</td>`;
}
function Un(t) {
  const e = t && t.columns || [], s = t && t.rows || [], r = e.length, n = `<colgroup>${Fn(e).map((u) => `<col style="width: ${u};" />`).join("")}</colgroup>`, c = `<tr role="row">${e.map((u, _) => {
    const f = M(u.label == null ? "" : u.label);
    return `<td role="${_ === 0 ? "rowheader" : "columnheader"}"><p style="text-align: center;">${f}&nbsp;</p></td>`;
  }).join("")}</tr>`, h = [], E = [];
  for (let u = 0; u < s.length; u++) {
    h[u] = h[u] || [];
    const _ = s[u] && s[u].cells || [];
    let f = 0, I = 0, D = "";
    for (; I < r; ) {
      if (h[u][I]) {
        I++;
        continue;
      }
      const N = _[f++];
      if (!N) break;
      const O = N.colSpan > 1 ? N.colSpan : 1, Re = N.rowSpan > 1 ? N.rowSpan : 1, et = vn(N, e, I), tt = Mn(N, e, I), Rt = xn(N, et, tt, O > 1), zs = I === 0 ? "rowheader" : null, qs = kn[N.kind] || null, ei = Pn(N);
      D += Hn(Rt, { colSpan: O, rowSpan: Re, role: zs, cls: qs, nowrap: ei });
      for (let Oe = 0; Oe < Re; Oe++)
        for (let st = 0; st < O; st++)
          (h[u + Oe] = h[u + Oe] || [])[I + st] = !0;
      I += O;
    }
    E.push(`<tr role="row">${D}</tr>`);
  }
  return [
    '<table border="1" dir="ltr">',
    n,
    "<tbody>",
    c,
    ...E,
    "</tbody>",
    "</table>"
  ].join(`
`);
}
function Qn(t) {
  let e = t;
  if (typeof e == "string")
    try {
      e = JSON.parse(e);
    } catch {
      return "";
    }
  if (!Array.isArray(e) || e.length === 0) return "";
  const s = e.filter((r) => r && r.href).map((r) => `<p><a href="${ie(r.href)}" target="_blank" rel="noopener">${M(r.label == null || r.label === "" ? r.href : r.label)}</a></p>`).join(`
`);
  return s ? `<div class="report-attachments">
${s}
</div>` : "";
}
function Yn(t) {
  const e = t || {};
  let s = e.body;
  if (typeof s == "string")
    try {
      s = JSON.parse(s);
    } catch {
      s = null;
    }
  const a = (s && Array.isArray(s.blocks) ? s.blocks : []).map(wn).filter(Boolean).join(`
`), n = Qn(e.attachments);
  return n ? `${a}
${n}` : a;
}
const Kn = "https://www.tzuchi.org.tw/images/1003--web--w1920xh573px.jpg", As = 80;
function Wn(t) {
  const e = String(t ?? "").trim();
  return e.length <= As ? e : `${e.slice(0, As)}…`;
}
function Gn(t, e, s = {}) {
  const r = t || {}, a = s.chrome !== !1, n = String(r.title == null ? "" : r.title), c = String(r.slug == null ? "" : r.slug), h = Number(r.item_no), E = Number.isFinite(h) ? Math.trunc(h) : 0, u = M(n), _ = `${u} - 慈濟入口網站`, f = r.og_image ? ie(r.og_image) : Kn, I = r.description == null ? "" : String(r.description).trim(), D = I ? `
  <meta name="description" content="${M(I)}" />` : "", N = I ? `
  <meta property="og:description" content="${M(Wn(I))}" />` : "", O = M(`/公益勸募/公益勸募事項/item/${E}-${c}#startOfPageId${E}`), Re = M(JSON.stringify([
    { name: "首頁", href: "/" },
    { name: "公益勸募", href: "/公益勸募" },
    { name: "公益勸募事項", href: "/公益勸募" },
    { name: n }
  ])), et = a ? `
  <script type="module" src="/src/components/index.js"><\/script>
  <script src="/src/page-utils.js" defer><\/script>` : "", tt = a ? `
  <tc-header></tc-header>
  <tc-nav></tc-nav>
  <div class="notice"></div>
  <div class="marquee"></div>
  <tc-breadcrumb items='${Re}'></tc-breadcrumb>` : "";
  return `<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${u} - 慈濟基金會</title>
  <meta property="og:type" content="article" />
  <meta property="og:title" content="${_}" />
  <meta property="og:image" content="${f}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="${_}" />${D}${N}
  <link rel="icon" href="/templates/tzuchi/favicon.ico" type="image/x-icon">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">${et}
  <link href="/templates/tzuchi/css/reset.css" rel="stylesheet" type="text/css" />
  <link href="/templates/tzuchi/css/template.css" rel="stylesheet" type="text/css" />
  <link href="/templates/tzuchi/css/k2style.css" rel="stylesheet" type="text/css" />
  <link href="/templates/tzuchi/css/pagas.css" rel="stylesheet" type="text/css" />
  <link href="/templates/tzuchi/css/item.css" rel="stylesheet" type="text/css" />
  <link href="/templates/tzuchi/css/article.css" rel="stylesheet" type="text/css" />
</head>
<body>${tt}
  <div class="main">
    <div class="container item-center">
      <span id="startOfPageId${E}"></span>
      <div id="k2Container" class="itemView">
        <div class="itemHeader">
          <h2 class="itemTitle">${u}</h2>
        </div>
        <div class="itemBody">
          <div class="itemContent">
${e}
          </div>
        </div>
        <div class="itemBackToTop" style="display:none;">
          <a class="k2Anchor" href="${O}">返回頂部</a>
        </div>
        <div class="clr"></div>
      </div>
    </div>
  </div>${a ? `
  <tc-footer></tc-footer>` : ""}
</body>
</html>
`;
}
function j(t) {
  const e = t.columns.length, s = t.rows.length, r = Array.from({ length: s }, () => new Array(e).fill(null));
  for (let a = 0; a < s; a++) {
    let n = 0;
    for (const c of t.rows[a].cells || []) {
      for (; n < e && r[a][n]; ) n++;
      if (n >= e) break;
      const h = Math.min(c.colSpan || 1, e - n), E = Math.min(c.rowSpan || 1, s - a), u = { v: c.v ?? "", colSpan: h, rowSpan: E, _r: a, _c: n };
      c.align && (u.align = c.align), c.rich && (u.rich = c.rich), c.kind && c.kind !== "normal" && (u.kind = c.kind);
      for (let _ = 0; _ < E; _++)
        for (let f = 0; f < h; f++)
          r[a + _][n + f] = _ || f ? { _cover: u } : u;
      n += h;
    }
  }
  return r;
}
function ae(t, e) {
  const s = t.length, r = e.length, a = Array.from({ length: s }, () => new Array(r).fill(!1)), n = [];
  for (let c = 0; c < s; c++) {
    const h = [];
    for (let E = 0; E < r; E++) {
      if (a[c][E]) continue;
      const u = t[c][E], _ = u && !u._cover ? u : null, f = Math.min(_ && _.rowSpan || 1, s - c), I = Math.min(_ && _.colSpan || 1, r - E);
      for (let N = 0; N < f; N++) for (let O = 0; O < I; O++) a[c + N][E + O] = !0;
      const D = { v: _ ? _.v ?? "" : "" };
      I > 1 && (D.colSpan = I), f > 1 && (D.rowSpan = f), _ && (_.align && (D.align = _.align), _.rich && (D.rich = _.rich), _.kind && _.kind !== "normal" && (D.kind = _.kind)), h.push(D);
    }
    n.push({ cells: h });
  }
  return n;
}
function ye(t) {
  return t.map((e) => ({ ...e }));
}
function $n(t, e, s, r, a) {
  const n = Math.min(e, r), c = Math.max(e, r), h = Math.min(s, a), E = Math.max(s, a), u = j(t), _ = u[n] && u[n][h], f = _ && !_._cover ? _ : null;
  return f ? (f.rowSpan = c - n + 1, f.colSpan = E - h + 1, { columns: ye(t.columns), rows: ae(u, t.columns) }) : t;
}
function Jn(t, e, s) {
  const r = j(t), a = r[e] && r[e][s], n = a && !a._cover ? a : null;
  return n ? (n.rowSpan = 1, n.colSpan = 1, { columns: ye(t.columns), rows: ae(r, t.columns) }) : t;
}
function Zn(t) {
  const e = t.columns.map(() => ({ v: "" }));
  return {
    columns: ye(t.columns),
    rows: [...t.rows.map((s) => ({ cells: s.cells.map((r) => ({ ...r })) })), { cells: e }]
  };
}
function Xn(t, e) {
  const s = zn(t), r = [...ye(t.columns), { key: s, label: "", align: "left" }], a = j(t).map((n) => [...n, { v: "", colSpan: 1, rowSpan: 1, _r: 0, _c: 0 }]);
  return { columns: r, rows: ae(a, r) };
}
function Vn(t, e) {
  if (t.rows.length <= 1) return t;
  const s = j(t);
  for (const r of s[e]) {
    const a = r && (r._cover || r);
    if (a && (a.rowSpan || 1) > 1) return t;
  }
  return s.splice(e, 1), { columns: ye(t.columns), rows: ae(s, t.columns) };
}
function jn(t, e) {
  if (t.columns.length <= 1) return t;
  const s = j(t);
  for (const n of s) {
    const c = n[e], h = c && (c._cover || c);
    if (h && (h.colSpan || 1) > 1) return t;
  }
  const r = t.columns.filter((n, c) => c !== e).map((n) => ({ ...n })), a = s.map((n) => n.filter((c, h) => h !== e));
  return { columns: r, rows: ae(a, r) };
}
function zn(t) {
  const e = new Set(t.columns.map((r) => r.key));
  let s = t.columns.length + 1;
  for (; e.has(`col${s}`); ) s++;
  return `col${s}`;
}
const qn = '<svg width="17" height="15" viewBox="0 0 17 15"><rect x="1" y="1" width="15" height="13" rx="1" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M1 5h15M1 10h15M6 1v13M11 1v13" stroke="currentColor" stroke-width="1"/></svg>', cs = {
  rowAdd: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3" width="15" height="5" rx="1"/><path d="M10 11.5v5M7.5 14h5"/></svg>',
  rowDel: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3" width="15" height="5" rx="1"/><path d="M7.5 14h5"/></svg>',
  colAdd: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="2.5" width="5" height="15" rx="1"/><path d="M13.5 7.5v5M11 10h5"/></svg>',
  colDel: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="2.5" width="5" height="15" rx="1"/><path d="M11 10h5"/></svg>',
  merge: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4.5" width="15" height="11" rx="1"/><path d="M10 4.5v2.5M10 13v2.5"/></svg>',
  split: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4.5" width="15" height="11" rx="1"/><path d="M10 4.5v11"/></svg>',
  bold: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 4h5a3 3 0 0 1 0 6h-5zM6.5 10h5.5a3 3 0 0 1 0 6h-5.5z"/></svg>',
  bullet: '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M7.5 5.5h9M7.5 10h9M7.5 14.5h9"/><circle cx="3.5" cy="5.5" r="1.15" fill="currentColor" stroke="none"/><circle cx="3.5" cy="10" r="1.15" fill="currentColor" stroke="none"/><circle cx="3.5" cy="14.5" r="1.15" fill="currentColor" stroke="none"/></svg>'
}, eo = () => ({
  columns: [
    { key: "item", label: "項目", align: "left" },
    { key: "amount", label: "金額", align: "right" },
    { key: "note", label: "說明", align: "left", rich: !0 }
  ],
  // 欄頭由 renderReportTable 從 columns[].label 合成；rows 只放內文，勿在此重複欄頭列。
  rows: [
    { cells: [{ v: "" }, { v: "" }, { v: "" }] },
    { cells: [{ v: "" }, { v: "" }, { v: "" }] }
  ]
});
class to {
  static get toolbox() {
    return { title: "收支表", icon: qn };
  }
  static get enableLineBreaks() {
    return !0;
  }
  constructor({ data: e }) {
    this.data = e && Array.isArray(e.columns) && e.columns.length ? so(e) : eo(), this.wrapper = null, this._sel = null, this._cur = null, this._dragging = !1, this.__mouseup = null;
  }
  render() {
    return this.wrapper = document.createElement("div"), this.wrapper.className = "tc-report-table", this.wrapper.appendChild(this._toolbar()), this.wrapper.appendChild(this._table()), this.wrapper;
  }
  // 純重繪。readback（擷取使用者打字）由各結構操作 handler 在套用 op 前自行呼叫，
  // 順序＝ readback → op → _rebuild（勿在此 readback，否則會用舊 DOM 覆寫剛套用的結構變更）。
  _rebuild() {
    this._sel = null, this._dragging = !1;
    const e = document.createElement("div");
    e.className = "tc-report-table", e.appendChild(this._toolbar()), e.appendChild(this._table()), this.wrapper.replaceWith(e), this.wrapper = e;
  }
  _toolbar() {
    const e = document.createElement("div");
    e.className = "tc-rt-toolbar", e.contentEditable = "false";
    const s = (c, h, E) => {
      const u = document.createElement("button");
      return u.type = "button", u.className = "tc-rt-icon", u.title = h, u.setAttribute("aria-label", h), u.innerHTML = cs[c] || "", u.addEventListener("click", (_) => {
        _.preventDefault(), E();
      }), e.appendChild(u), u;
    }, r = (c, h, E, u) => {
      const _ = document.createElement("button");
      return _.type = "button", _.className = "tc-rt-icon", _.title = h, _.setAttribute("aria-label", h), _.innerHTML = cs[c] || "", _.addEventListener("mousedown", (f) => {
        f.preventDefault();
        try {
          document.execCommand(E, !1, u);
        } catch {
        }
      }), e.appendChild(_), _;
    };
    s("rowAdd", "新增列", () => {
      this._readback(), this.data = Zn(this.data), this._rebuild();
    }), s("colAdd", "新增欄", () => {
      this._readback(), this.data = Xn(this.data), this._rebuild();
    }), s("rowDel", "刪除目前列", () => {
      this._readback();
      const c = this._activeRow();
      c != null && (this.data = Vn(this.data, c), this._rebuild());
    }), s("colDel", "刪除目前欄", () => {
      this._readback();
      const c = this._activeCol();
      c != null && (this.data = jn(this.data, c), this._rebuild());
    }), s("merge", "合併選取的格", () => {
      if (this._readback(), this._sel && this._sel.b) {
        const c = this._sel;
        this.data = $n(this.data, c.a.r, c.a.c, c.b.r, c.b.c), this._sel = null, this._rebuild();
      }
    }), s("split", "拆分合併格", () => {
      this._readback();
      const c = this._active();
      c && c.r >= 0 && (this.data = Jn(this.data, c.r, c.c), this._rebuild());
    });
    const a = document.createElement("span");
    a.className = "tc-rt-hint", a.textContent = "說明格式：", e.appendChild(a), r("bold", "粗體", "bold"), r("bullet", "項目符號", "insertUnorderedList");
    const n = document.createElement("span");
    return n.className = "tc-rt-hint", n.textContent = "選多格：拖曳，或按住 Shift 點選 → 再按合併", e.appendChild(n), e;
  }
  _table() {
    const e = document.createElement("table");
    e.className = "tc-rt-grid";
    const s = document.createElement("tr");
    s.dataset.header = "1";
    for (let a = 0; a < this.data.columns.length; a++) {
      const n = document.createElement("td");
      n.className = "tc-rt-th", n.dataset.header = "1", n.dataset.c = String(a), n.contentEditable = "true", n.textContent = this.data.columns[a].label || "", n.addEventListener("focus", () => {
        this._active(-1, a);
      }), s.appendChild(n);
    }
    e.appendChild(s);
    const r = j(this.data);
    for (let a = 0; a < r.length; a++) {
      const n = document.createElement("tr");
      for (let c = 0; c < this.data.columns.length; c++) {
        const h = r[a][c];
        if (!h || h._cover) continue;
        const E = document.createElement("td");
        E.dataset.r = String(h._r), E.dataset.c = String(h._c), h.colSpan > 1 && (E.colSpan = h.colSpan), h.rowSpan > 1 && (E.rowSpan = h.rowSpan), h.kind && (E.dataset.kind = h.kind);
        const u = !!(h.rich || this.data.columns[c].rich);
        u && (E.dataset.rich = "1");
        const _ = h.align || this.data.columns[c].align || "left";
        E.style.textAlign = _, E.contentEditable = "true", u ? E.innerHTML = pe(h.v || "") : E.textContent = h.v || "", E.addEventListener("focus", () => {
          if (this._active(h._r, h._c), u)
            try {
              document.execCommand("defaultParagraphSeparator", !1, "p");
            } catch {
            }
        }), E.addEventListener("mousedown", (f) => {
          f.shiftKey ? (f.preventDefault(), this._extendSel(h._r, h._c), this._paintSelection()) : this._startSel(h._r, h._c);
        }), E.addEventListener("mouseover", () => {
          if (!this._dragging || !this._cur || this._cur.r === h._r && this._cur.c === h._c) return;
          this._extendSel(h._r, h._c);
          const f = typeof window < "u" && window.getSelection ? window.getSelection() : null;
          f && f.removeAllRanges && f.removeAllRanges(), this._paintSelection();
        }), n.appendChild(E);
      }
      e.appendChild(n);
    }
    return e;
  }
  // selection / active-cell bookkeeping
  _active(e, s) {
    return e != null && (this._cur = { r: e, c: s }), this._cur || null;
  }
  // 表頭列 r=-1：不算「目前列」（刪除列不作用於表頭），但算「目前欄」（可刪整欄）。
  _activeRow() {
    return this._cur && this._cur.r >= 0 ? this._cur.r : null;
  }
  _activeCol() {
    return this._cur ? this._cur.c : null;
  }
  _startSel(e, s) {
    this._cur = { r: e, c: s }, this._sel = { a: { r: e, c: s }, b: null }, this._dragging = !0, this._armMouseup(), this._paintSelection();
  }
  _extendSel(e, s) {
    this._sel || (this._sel = { a: { r: e, c: s }, b: null }), this._sel.b = { r: e, c: s }, this._cur = { r: e, c: s };
  }
  // 拖曳結束（放開滑鼠，可能在表格外）→ 收起 dragging；自我移除、不留常駐監聽。
  _armMouseup() {
    this.__mouseup || typeof document > "u" || (this.__mouseup = () => {
      this._dragging = !1, document.removeEventListener("mouseup", this.__mouseup), this.__mouseup = null;
    }, document.addEventListener("mouseup", this.__mouseup));
  }
  // 有 range（b 已設）才塗選區底色；非選區格清空底色（讓 data-kind 的 CSS 底色回歸）。
  _paintSelection() {
    if (!this.wrapper || !this.wrapper.querySelectorAll) return;
    const e = this.wrapper.querySelectorAll("table.tc-rt-grid td");
    let s = null;
    if (this._sel && this._sel.b) {
      const r = this._sel.a, a = this._sel.b;
      s = { ra: Math.min(r.r, a.r), rb: Math.max(r.r, a.r), ca: Math.min(r.c, a.c), cb: Math.max(r.c, a.c) };
    }
    e.forEach((r) => {
      const a = Number(r.dataset.r), n = Number(r.dataset.c), c = s && a >= s.ra && a <= s.rb && n >= s.ca && n <= s.cb;
      r.style.backgroundColor = c ? "#cfe0ff" : "";
    });
  }
  // DOM → this.data (covered cells naturally absent; compact by construction).
  _readback() {
    if (!this.wrapper) return;
    const e = this.data.columns.map((r) => ({ ...r }));
    for (const r of this.wrapper.querySelectorAll("table.tc-rt-grid > tr > td[data-header]")) {
      const a = Number(r.dataset.c);
      e[a] && (e[a].label = r.textContent.trim());
    }
    const s = [];
    for (const r of this.wrapper.querySelectorAll("table.tc-rt-grid > tr")) {
      if (r.dataset.header === "1") continue;
      const a = [];
      for (const n of r.querySelectorAll(":scope > td")) {
        const c = n.dataset.rich === "1", h = { v: c ? n.innerHTML.trim() : n.textContent.trim() }, E = Number(n.getAttribute("colspan") || 1), u = Number(n.getAttribute("rowspan") || 1);
        E > 1 && (h.colSpan = E), u > 1 && (h.rowSpan = u), c && (h.rich = !0), n.dataset.kind && (h.kind = n.dataset.kind), a.push(h);
      }
      s.push({ cells: a });
    }
    this.data = { columns: e, rows: s.length ? s : this.data.rows };
  }
  save() {
    return this._readback(), this.data;
  }
}
function so(t) {
  return { columns: t.columns.map((e) => ({ ...e })), rows: ae(j(t), t.columns) };
}
class io {
  static get isReadOnlySupported() {
    return !0;
  }
  constructor({ data: e }) {
    this.data = {
      src: e && e.src || "",
      href: e && e.href || "",
      caption: e && e.caption || ""
    };
  }
  render() {
    const e = document.createElement("figure");
    e.className = "tc-report-image", e.contentEditable = "false";
    const s = document.createElement("img");
    s.src = ie(this.data.src), s.alt = this.data.caption || "", s.style.maxWidth = "100%";
    const r = ie(this.data.href);
    if (r) {
      const n = document.createElement("a");
      n.href = r, n.target = "_blank", n.rel = "noopener", n.appendChild(s), e.appendChild(n);
    } else
      e.appendChild(s);
    if (this.data.caption) {
      const n = document.createElement("figcaption");
      n.textContent = this.data.caption, e.appendChild(n);
    }
    const a = document.createElement("div");
    return a.className = "tc-ro-note", a.textContent = "（唯讀圖片區塊，僅供遷移內容顯示，不可於後台編輯）", e.appendChild(a), e;
  }
  save() {
    return { ...this.data };
  }
}
const ro = bt.cssText.replace(/:host/g, "tc-dash-gongyi"), ce = [
  { name: "title", label: "標題", type: "text", required: !0, w: "full" },
  { name: "slug", label: "網址代稱（slug）", type: "text", placeholder: "留空時由標題自動產生", w: "full" },
  { name: "publish_date", label: "公告日期", type: "date", required: !0, w: "half" },
  { name: "status", label: "狀態", type: "select", options: [{ value: "draft", label: "草稿" }, { value: "published", label: "已發布" }], required: !0, w: "half" },
  { name: "attachments", label: "附件 PDF（直接上傳，顯示於報告頁尾）", type: "filelist", w: "full" },
  // ── 隱藏、系統代管（存檔自動補：item_no 自動編號、minguo_year 由日期推導、其餘沿用既值）──
  { name: "item_no", type: "number", hidden: !0 },
  { name: "minguo_year", type: "number", hidden: !0 },
  { name: "report_type", type: "text", hidden: !0 },
  { name: "campaign", type: "text", hidden: !0 },
  { name: "description", type: "textarea", hidden: !0 }
], ls = /* @__PURE__ */ new Set(["attachments"]), Fe = () => ({ time: Date.now(), version: "2.31.6", blocks: [] }), ao = m`<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
  <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`, hs = 20;
class no extends G {
  static properties = {
    _rows: { state: !0 },
    _editing: { state: !0 },
    // null | 'new' | row
    _form: { state: !0 },
    _busy: { state: !0 },
    _error: { state: !0 },
    _flash: { state: !0 },
    _page: { state: !0 },
    // 目前頁（1-based）
    _pages: { state: !0 },
    // 總頁數
    _total: { state: !0 }
    // 全庫報告總數
  };
  // Light DOM (see LIGHT_STYLES note).
  createRenderRoot() {
    return this;
  }
  constructor() {
    super(), this._rows = [], this._editing = null, this._form = {}, this._busy = !1, this._error = "", this._flash = "", this._page = 1, this._pages = 1, this._total = 0, this._maxItemNo = 0, this.__editor = null, this.__flashT = null, this.__previewT = null;
  }
  connectedCallback() {
    super.connectedCallback(), Nt() && this._load();
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._destroyEditor();
  }
  async _load(e = this._page || 1) {
    this._busy = !0, this._error = "";
    try {
      const s = await Wt("gongyi_reports", {
        sort: { field: "publish_date", dir: "desc" },
        page: e,
        perPage: hs
      });
      if (!s.records.length && e > 1)
        return this._busy = !1, this._load(e - 1);
      this._rows = s.records, this._total = s.total, this._page = s.page, this._pages = Math.max(1, Math.ceil(s.total / hs));
      const r = await Wt("gongyi_reports", {
        sort: { field: "item_no", dir: "desc" },
        page: 1,
        perPage: 1,
        select: ["item_no"]
      });
      this._maxItemNo = r.records.length && Number(r.records[0].item_no) || 0;
    } catch (s) {
      this._error = s.message;
    } finally {
      this._busy = !1;
    }
  }
  _flashMsg(e) {
    this._flash = e, clearTimeout(this.__flashT), this.__flashT = setTimeout(() => {
      this._flash = "";
    }, 1800);
  }
  _blank() {
    const e = {};
    for (const s of ce) e[s.name] = U(s);
    return e.status = "draft", e.item_no = this._maxItemNo + 1, e.display_order = this._total, e.__body = Fe(), e;
  }
  _toForm(e) {
    const s = {};
    for (const r of ce) {
      const a = e[r.name];
      ls.has(r.name) ? s[r.name] = Ne(a, U(r)) : s[r.name] = a ?? U(r);
    }
    return s.display_order = e.display_order ?? 0, s.__body = Ne(e.body, Fe()), s;
  }
  _payload() {
    const e = {};
    for (const r of ce) {
      const a = this._form[r.name];
      ls.has(r.name) ? e[r.name] = Gt(a ?? []) : r.type === "number" ? e[r.name] = a === "" || a == null ? 0 : Number(a) : e[r.name] = a;
    }
    e.display_order = this._form.display_order ?? 0;
    const s = Number(String(this._form.publish_date || "").slice(0, 4));
    return Number.isFinite(s) && s > 1911 && (e.minguo_year = s - 1911), e;
  }
  // ctx for fields.js. Auto-fill slug from title while slug is untouched.
  _ctx = {
    onChange: (e, s) => {
      const r = { ...this._form, [e]: s };
      e === "title" && (!this._form.slug || this._form.slug === ct(this._form.title || "")) && (r.slug = ct(s)), this._form = r, this._schedulePreview();
    },
    upload: (e) => Ye(e),
    uploadFile: (e) => wi(e)
  };
  // ── navigation ──
  _new() {
    this._editing = "new", this._form = this._blank(), this._error = "", this._afterFormReady();
  }
  _edit(e) {
    this._editing = e, this._form = this._toForm(e), this._error = "", this._afterFormReady();
  }
  _close() {
    this._destroyEditor(), this._editing = null, this._error = "", this._load();
  }
  _afterFormReady() {
    this.updateComplete.then(() => this._mountEditor());
  }
  // body source. Prefers the live EditorJS content; falls back to the stored body.
  async _collectBody() {
    if (this.__editor && this.__editor.save)
      try {
        return await this.__editor.save();
      } catch {
      }
    return this._form.__body || Fe();
  }
  async _mountEditor() {
    this._destroyEditor();
    const e = this.querySelector("#gongyi-editor");
    if (!e) return;
    const [{ default: s }, { default: r }, { default: a }, { default: n }] = await Promise.all([
      import("./editorjs-DOT9nZW3.js"),
      import("./header-DsBPlGVr.js"),
      import("./editorjs-list-DOjtZ1eS.js"),
      import("./paragraph-CUYQrBuD.js")
    ]);
    this._editing == null || !this.isConnected || (this.__editor = new s({
      holder: e,
      data: this._form.__body || Fe(),
      tools: {
        header: { class: r, config: { levels: [2, 3, 4], defaultLevel: 2 } },
        paragraph: { class: n, inlineToolbar: !0 },
        list: { class: a, inlineToolbar: !0, config: { defaultStyle: "unordered" } },
        reportTable: { class: to },
        image: { class: io }
      },
      onChange: () => this._schedulePreview()
    }), this._schedulePreview());
  }
  _destroyEditor() {
    if (this.__editor && this.__editor.destroy)
      try {
        this.__editor.destroy();
      } catch {
      }
    this.__editor = null;
  }
  // ── live preview (D4): same renderReport/wrapReportPage the CI build uses ──
  async _previewRecord() {
    const e = await this._collectBody();
    return {
      ...this._payload(),
      // top-level fields (numbers coerced)
      attachments: this._form.attachments || [],
      // object form for render
      body: e
    };
  }
  _schedulePreview() {
    clearTimeout(this.__previewT), this.__previewT = setTimeout(() => this._renderPreview(), 300);
  }
  async _renderPreview() {
    const e = this.querySelector("#gongyi-preview");
    if (e)
      try {
        const s = await this._previewRecord();
        e.srcdoc = Gn(s, Yn(s), { chrome: !1 });
      } catch (s) {
        e.srcdoc = `<pre style="color:#b00;padding:16px;font-family:sans-serif">預覽產生失敗：${String(s && s.message || s)}</pre>`;
      }
  }
  async _save() {
    const e = ct(this._form.slug || this._form.title || "") || `report-${this._form.item_no || Date.now()}`;
    e !== this._form.slug && (this._form = { ...this._form, slug: e });
    for (const r of ce) if (r.required) {
      const a = this._form[r.name];
      if (a === "" || a == null) {
        this._error = `「${r.label}」為必填`;
        return;
      }
    }
    const s = this._editing && this._editing.id;
    this._busy = !0, this._error = "";
    try {
      const r = await this._collectBody(), a = { ...this._payload(), body: Gt(r) };
      this._editing === "new" ? (await be("gongyi_reports", a), this._page = 1) : await Q("gongyi_reports", s, a), this._flashMsg("已儲存"), this._close();
    } catch (r) {
      this._error = /unique|constraint|conflict|duplicate|已存在|409/i.test(r.message || "") ? `頁面編號 ${this._form.item_no} 已被使用，請重新開啟以取得新編號` : r.message;
    } finally {
      this._busy = !1;
    }
  }
  async _delete(e) {
    if (confirm(`刪除報告「${e.title}」？此動作無法復原。`)) {
      this._busy = !0, this._error = "";
      try {
        await Qe("gongyi_reports", e.id), await this._load(), this._flashMsg("已刪除");
      } catch (s) {
        this._error = s.message;
      } finally {
        this._busy = !1;
      }
    }
  }
  render() {
    const e = this._editing != null;
    return m`
      <style>${ro}</style>
      <style>
        tc-dash-gongyi .editor-2col { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 20px; align-items: start; }
        @media (max-width: 1024px) { tc-dash-gongyi .editor-2col { grid-template-columns: 1fr; } }
        tc-dash-gongyi .preview-col { position: sticky; top: calc(var(--bar-h) + 16px); }
        tc-dash-gongyi .preview-head { font-weight: 700; color: var(--ink); margin: 0 0 8px; }
        tc-dash-gongyi .gongyi-preview-frame { width: 100%; height: 78vh; border: 1px solid var(--line); border-radius: var(--radius); background: #fff; }
        tc-dash-gongyi .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 18px; }
        tc-dash-gongyi .fcell--full { grid-column: 1 / -1; }
        tc-dash-gongyi .fcell > .field { margin: 0 0 14px; }
        @media (max-width: 640px) { tc-dash-gongyi .form-grid { grid-template-columns: 1fr; } }
        tc-dash-gongyi .field--ro .ro-value { padding: 8px 10px; background: var(--surface-2); border: 1px dashed var(--line-strong); border-radius: 6px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
        tc-dash-gongyi input[type="date"] { max-width: 220px; }
        tc-dash-gongyi .filerow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
        tc-dash-gongyi .filerow input[type="text"] { flex: 1 1 240px; }
        tc-dash-gongyi .file-open { text-decoration: none; }
        tc-dash-gongyi .file-pick { cursor: pointer; display: inline-flex; align-items: center; }
        tc-dash-gongyi .gongyi-editor { border: 1px solid var(--line-strong); border-radius: var(--radius-sm); padding: 8px 12px; background: #fff; }
        tc-dash-gongyi .tc-rt-toolbar { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin:0 0 6px; padding:6px 4px; position:sticky; top:0; z-index:5; background:#fff; border-bottom:1px solid var(--line-strong); }
        tc-dash-gongyi .tc-rt-toolbar button { font:inherit; font-size:13px; padding:4px 9px; border:1px solid var(--line-strong); border-radius:6px; background:#fff; color:var(--ink); cursor:pointer; }
        tc-dash-gongyi .tc-rt-toolbar button:hover { background:var(--surface-2); }
        tc-dash-gongyi .tc-rt-toolbar button.tc-rt-icon { padding:5px 7px; line-height:0; display:inline-flex; align-items:center; }
        tc-dash-gongyi .tc-rt-toolbar button.tc-rt-icon svg { display:block; }
        tc-dash-gongyi .tc-rt-hint { font-size:12px; color:var(--text-muted); align-self:center; margin-left:2px; }
        tc-dash-gongyi table.tc-rt-grid { border-collapse:collapse; width:100%; }
        tc-dash-gongyi table.tc-rt-grid td { border:1px solid var(--line-strong); padding:6px 8px; min-width:60px; outline:none; }
        tc-dash-gongyi table.tc-rt-grid td.tc-rt-th { background:var(--surface-2); font-weight:700; text-align:center; }
        tc-dash-gongyi table.tc-rt-grid td:focus { box-shadow: inset 0 0 0 2px var(--accent); }
        tc-dash-gongyi table.tc-rt-grid td[data-kind="section"] { background:var(--surface-2); font-weight:700; }
        tc-dash-gongyi table.tc-rt-grid td[data-kind="total"] { font-weight:700; }
        tc-dash-gongyi figure.tc-report-image { margin:8px 0; padding:8px; border:1px dashed var(--line-strong); border-radius:var(--radius-sm); }
        tc-dash-gongyi figure.tc-report-image figcaption { color:var(--text-muted); font-size:14px; margin-top:4px; }
        tc-dash-gongyi figure.tc-report-image .tc-ro-note { color:var(--text-muted); font-size:12px; margin-top:6px; }
        tc-dash-gongyi .pager { display:flex; align-items:center; justify-content:center; gap:14px; margin-top:14px; }
        tc-dash-gongyi .pager__info { font-size:13px; color:var(--text-muted); }
      </style>
      <header class="topbar">
        <a class="topbar__back" href="/dashboard/">${ao} 首頁後台</a>
        <button class="topbar__logout" @click=${() => Ce()}>登出</button>
      </header>
      <div class="wrap">
        <div class="head">
          <div class="head__titles">
            <h1>公益勸募報告</h1>
            <p class="head__sub">${this._subtitle()}</p>
          </div>
          ${e ? m`<button class="btn btn--ghost" @click=${() => this._close()}>返回列表</button>` : m`<button class="btn btn--primary" ?disabled=${this._busy} @click=${() => this._new()}>＋ 新增報告</button>`}
        </div>
        ${this._error ? m`<div class="alert alert--error">${this._error}</div>` : ""}
        ${e ? this._renderEditor() : this._renderList()}
      </div>
      ${this._flash ? m`<div class="toast">✓ ${this._flash}</div>` : ""}
    `;
  }
  _subtitle() {
    return this._editing != null ? this._editing === "new" ? "新增報告" : "編輯報告" : this._busy ? m`<span class="busy-dot"></span>載入中…` : `目前共 ${this._total} 篇報告`;
  }
  _renderList() {
    return this._busy && !this._rows.length ? m`<div class="skeleton">${[0, 1, 2, 3].map(() => m`<div class="skeleton__row"></div>`)}</div>` : this._rows.length ? m`
      <div class="table-card">
        <table>
          <thead><tr><th>編號</th><th>標題</th><th>公告日期</th><th>狀態</th><th class="col-actions">操作</th></tr></thead>
          <tbody>${this._rows.map((e) => m`<tr>
            <td>${e.item_no}</td>
            <td class="cell-strong" title=${e.title}>${e.title || "—"}</td>
            <td>${e.publish_date || "—"}</td>
            <td>${e.status === "published" ? "已發布" : "草稿"}</td>
            <td class="actions"><div class="row-actions">
              <button class="btn btn--ghost btn--sm" @click=${() => this._edit(e)}>編輯</button>
              <button class="btn btn--danger btn--sm" @click=${() => this._delete(e)}>刪除</button>
            </div></td>
          </tr>`)}</tbody>
        </table>
      </div>
      ${this._pages > 1 ? m`<div class="pager">
        <button class="btn btn--ghost btn--sm" ?disabled=${this._busy || this._page <= 1}
          @click=${() => this._load(this._page - 1)}>← 上一頁</button>
        <span class="pager__info">第 ${this._page} / ${this._pages} 頁</span>
        <button class="btn btn--ghost btn--sm" ?disabled=${this._busy || this._page >= this._pages}
          @click=${() => this._load(this._page + 1)}>下一頁 →</button>
      </div>` : ""}` : m`<div class="empty">
      <p class="empty__title">尚無報告</p><p class="empty__hint">點右上角「＋ 新增報告」建立第一篇。</p></div>`;
  }
  _renderEditor() {
    const e = m`
      <div class="card">
        <div class="card__head"><h2>${this._editing === "new" ? "新增" : "編輯"}報告</h2></div>
        <div class="card__body">
          <div class="form-grid">
            ${ce.filter((r) => !r.hidden).map((r) => m`<div class="fcell ${r.w === "full" ? "fcell--full" : ""}">
              ${He(r, this._form[r.name], this._ctx)}</div>`)}
          </div>
          <div class="field">
            <label>報告內容（標題／段落／條列／收支表）</label>
            <div id="gongyi-editor" class="gongyi-editor"></div>
          </div>
          <div class="form-actions">
            <button class="btn btn--primary" ?disabled=${this._busy} @click=${() => this._save()}>
              ${this._busy ? m`<span class="busy-dot"></span>儲存中…` : "儲存報告"}</button>
            <button class="btn btn--ghost" @click=${() => this._close()}>返回列表</button>
          </div>
        </div>
      </div>`, s = m`
      <div class="preview-col">
        <div class="preview-head">即時預覽（正式頁樣式）</div>
        <iframe id="gongyi-preview" class="gongyi-preview-frame" title="報告預覽" sandbox=""></iframe>
      </div>`;
    return m`<div class="editor-2col"><div>${e}</div>${s}</div>`;
  }
}
customElements.define("tc-dash-gongyi", no);
export {
  Yt as S,
  us as a,
  m as b,
  lo as c,
  Li as d,
  Nt as e,
  Cs as g,
  G as i,
  Ce as l,
  ti as r,
  co as s
};
