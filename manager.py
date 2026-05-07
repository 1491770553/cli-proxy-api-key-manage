#!/usr/bin/env python3
import os, sys, json, yaml, secrets, threading, time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, session

CONFIG = "/data/CLIProxyAPI_6.9.38_linux_amd64/config.yaml"
RECYCLE_FILE = "/data/CLIProxyAPI_6.9.38_linux_amd64/recycle.json"
PASSWORD = "wlie0726"
PORT = 18317

# Copy templates configuration (use {apikey} as placeholder)
COPY_TEMPLATES = [
    {
        "name": "样式1：简洁分享",
        "content": "key：{apikey}\n\nBase：http://your-api-server:port"
    },
    {
        "name": "样式2：完整说明",
        "content": "key：{apikey}\n\nBase：http://your-api-server:port\n\n使用apikey和地址可接入到cc，cx，oc，claw等agent工具中，不懂或者不会使用可咨询我，带协助（同时我还接安装龙虾，25一次，后期续费模型一直持续客户维护龙虾）。\n\n模型列表：\nkimi-k2\nkimi-k2-thinking\nkimi-k2.5\nkimi-k2.6\n\n商品卖出后并且发货，如果使用不允退款。\n未使用退款退款一半（商品首页有说明）"
    }
]

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
lock = threading.Lock()

def load():
    with open(CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)

def save(cfg):
    with open(CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)

def load_recycle():
    if os.path.exists(RECYCLE_FILE):
        with open(RECYCLE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_recycle(data):
    with open(RECYCLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def gen_key():
    return "sk-" + secrets.token_urlsafe(24)

def auth(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get("auth"): return redirect("/login")
        return f(*a, **kw)
    return dec

def cleanup():
    with lock:
        cfg = load()
        keys = cfg.get("api-keys", [])
        meta = cfg.get("api-key-metadata", {})
        valid, rem = [], 0
        recycle = load_recycle()
        for k in keys:
            m = meta.get(k, {})
            exp = m.get("expires_at")
            starts_at = m.get("starts_at")
            if exp:
                try:
                    now = datetime.now()
                    if starts_at:
                        try:
                            start_time = datetime.fromisoformat(starts_at)
                            if now < start_time:
                                pass
                            elif now >= datetime.fromisoformat(exp):
                                recycle.append({"key": k, "deleted_at": now.isoformat(), "created_at": m.get("created_at"), "starts_at": starts_at, "expires_at": exp, "note": m.get("note", ""), "deleted_by": "expired"})
                                rem += 1
                                continue
                        except:
                            if now >= datetime.fromisoformat(exp):
                                recycle.append({"key": k, "deleted_at": now.isoformat(), "created_at": m.get("created_at"), "starts_at": starts_at, "expires_at": exp, "note": m.get("note", ""), "deleted_by": "expired"})
                                rem += 1
                                continue
                    else:
                        if now >= datetime.fromisoformat(exp):
                            recycle.append({"key": k, "deleted_at": now.isoformat(), "created_at": m.get("created_at"), "starts_at": starts_at, "expires_at": exp, "note": m.get("note", ""), "deleted_by": "expired"})
                            rem += 1
                            continue
                except:
                    pass
            valid.append(k)
        if rem:
            cfg["api-keys"] = valid
            cfg["api-key-metadata"] = meta
            save(cfg)
            save_recycle(recycle)
        return rem

def cleanup_loop():
    while True:
        time.sleep(300)
        cleanup()

LOGIN = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>API Key 管理 - 登录</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,#0c0c1e 0%,#1a1a3e 50%,#2d1b4e 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative;}
#particles-canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;}
.login-box{background:rgba(255,255,255,0.1);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);padding:50px;border-radius:24px;box-shadow:0 25px 70px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.1);width:420px;max-width:90vw;animation:slideUp 0.6s cubic-bezier(0.16,1,0.3,1);border:1px solid rgba(255,255,255,0.15);position:relative;z-index:1;}
@keyframes slideUp{from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)}}
.login-box h1{text-align:center;color:#fff;margin-bottom:10px;font-size:32px;font-weight:700;text-shadow:0 2px 20px rgba(0,0,0,0.3);}
.login-box p{text-align:center;color:rgba(255,255,255,0.6);margin-bottom:35px;font-size:14px;letter-spacing:2px;}
.login-box input{width:100%;padding:16px 20px;margin:12px 0;border:2px solid rgba(255,255,255,0.15);border-radius:12px;font-size:16px;transition:all 0.3s ease;outline:none;background:rgba(255,255,255,0.08);color:#fff;}
.login-box input::placeholder{color:rgba(255,255,255,0.4);}
.login-box input:focus{border-color:#7c3aed;box-shadow:0 0 0 4px rgba(124,58,237,0.2);background:rgba(255,255,255,0.12);}
.login-box button{width:100%;padding:16px;background:linear-gradient(135deg,#7c3aed,#5b21b6);color:#fff;border:none;border-radius:12px;font-size:18px;font-weight:600;cursor:pointer;margin-top:20px;transition:all 0.3s cubic-bezier(0.16,1,0.3,1);box-shadow:0 4px 20px rgba(124,58,237,0.4);}
.login-box button:hover{transform:translateY(-3px);box-shadow:0 8px 30px rgba(124,58,237,0.6);}
.login-box .remember-row{display:flex;align-items:center;margin-top:15px;}
.login-box .remember-row label{display:flex;align-items:center;gap:8px;color:rgba(255,255,255,0.6);font-size:14px;cursor:pointer;}
.login-box .remember-row input[type="checkbox"]{width:18px;height:18px;cursor:pointer;accent-color:#7c3aed;}
.login-box .error{color:#ef4444;text-align:center;margin-top:15px;font-size:14px;animation:shake 0.5s ease;}
@keyframes shake{0%,100%{transform:translateX(0)} 25%{transform:translateX(-10px)} 75%{transform:translateX(10px)}}
</style>
</head>
<body>
<canvas id="particles-canvas"></canvas>
<div class="login-box">
<h1>API Key 管理</h1>
<p>CLI PROXY API MANAGEMENT</p>
<form method="POST" id="loginForm">
<input type="password" name="password" id="passwordInput" placeholder="Enter password" required>
<div class="remember-row">
<label><input type="checkbox" id="rememberMe"> Remember password</label>
</div>
<button type="submit">Sign In</button>
</form>
{% if e %}<p class="error">Invalid password, please try again</p>{% endif %}
</div>
<script>
!function(){const c=document.getElementById("particles-canvas");const ctx=c.getContext("2d");let w=window.innerWidth,h=window.innerHeight;c.width=w;c.height=h;const ps=[];for(let i=0;i<80;i++)ps.push({x:Math.random()*w,y:Math.random()*h,r:Math.random()*2+1,spd:Math.random()*0.5+0.2,s:Math.random()*9999});function an(){ctx.clearRect(0,0,w,h);ps.forEach(p=>{p.y+=p.spd;p.x+=Math.sin(p.s)*0.3;if(p.y>h)p.y=0;if(p.x>w)p.x=0;if(p.x<0)p.x=w;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,2*Math.PI);ctx.fillStyle="rgba(124,58,237,0.5)";ctx.fill();});requestAnimationFrame(an);}window.addEventListener("resize",()=>{w=window.innerWidth;h=window.innerHeight;c.width=w;c.height=h;});an();}();
if(localStorage.getItem("apikey_manager_pwd")){document.getElementById("passwordInput").value=localStorage.getItem("apikey_manager_pwd");if(localStorage.getItem("apikey_manager_remember")==="1"){document.getElementById("rememberMe").checked=true;document.getElementById("loginForm").submit();}}
document.getElementById("loginForm").onsubmit=function(){if(document.getElementById("rememberMe").checked){localStorage.setItem("apikey_manager_pwd",document.getElementById("passwordInput").value);localStorage.setItem("apikey_manager_remember","1");}else{localStorage.removeItem("apikey_manager_pwd");localStorage.removeItem("apikey_manager_remember");}};
</script>
</body>
</html>"""

DASH = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>API Key 管理</title>
<style>
:root{--primary:#7c3aed;--primary-dark:#5b21b6;--success:#10b981;--danger:#ef4444;--bg:linear-gradient(135deg,#0c0c1e 0%,#1a1a3e 50%,#2d1b4e 100%);--card-bg:rgba(255,255,255,0.08);--text:#fff;--text-light:rgba(255,255,255,0.6);--border:rgba(255,255,255,0.1);}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);background-attachment:fixed;color:var(--text);min-height:100vh;position:relative;}
#dash-particles{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;}
.header{background:rgba(0,0,0,0.3);backdrop-filter:blur(20px);padding:20px 30px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;}
.header h1{font-size:24px;font-weight:700;background:linear-gradient(135deg,#7c3aed,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.user{display:flex;align-items:center;gap:15px;}
.user span{color:var(--text-light);font-size:14px;}
.logout{background:rgba(255,255,255,0.1);color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px;transition:all 0.2s;}
.logout:hover{background:rgba(255,255,255,0.2);}
.container{max-width:1200px;margin:0 auto;padding:30px;position:relative;z-index:1;}
.stats{display:flex;gap:20px;margin-bottom:30px;}
.stat-box{flex:1;background:var(--card-bg);backdrop-filter:blur(20px);border-radius:16px;padding:24px;text-align:center;border:1px solid var(--border);}
.stat-box.red{background:linear-gradient(135deg,rgba(239,68,68,0.2),rgba(220,38,38,0.2));}
.stat-box .num{font-size:42px;font-weight:700;background:linear-gradient(135deg,#fff,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.stat-box.red .num{background:linear-gradient(135deg,#fca5a5,#ef4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.stat-box .label{font-size:14px;color:var(--text-light);margin-top:8px;}
.card{background:var(--card-bg);backdrop-filter:blur(20px);border-radius:16px;padding:25px;margin-bottom:20px;border:1px solid var(--border);overflow-x:auto;}
.card h2{font-size:18px;font-weight:600;margin-bottom:20px;padding-bottom:15px;border-bottom:1px solid var(--border);}
.quick-btns{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;}
.quick-btn{padding:10px 20px;background:rgba(255,255,255,0.1);border:1px solid var(--border);border-radius:10px;color:#fff;cursor:pointer;font-size:14px;transition:all 0.2s;}
.quick-btn:hover,.quick-btn.active{background:var(--primary);border-color:var(--primary);}
.btn{padding:10px 20px;background:var(--primary);color:#fff;border:none;border-radius:10px;cursor:pointer;font-size:14px;transition:all 0.2s;}
.btn:hover{background:var(--primary-dark);}
.btn-sm{padding:6px 12px;font-size:12px;}
.btn-danger{background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.3);}
.btn-danger:hover{background:rgba(239,68,68,0.3);}
.btn-group{display:flex;gap:10px;flex-wrap:wrap;}
.card-table{width:100%;border-collapse:collapse;table-layout:fixed;}
.card-table th{background:rgba(0,0,0,0.2);padding:14px 16px;text-align:left;font-weight:600;font-size:13px;color:var(--text-light);border-bottom:2px solid var(--border);}
.card-table td{padding:14px 16px;border-bottom:1px solid var(--border);font-size:14px;}
.card-table tr:hover{background:rgba(124,58,237,0.1);}
.key-cell{font-family:monospace;background:rgba(0,0,0,0.3);padding:6px 12px;border-radius:6px;word-break:break-all;font-size:13px;}
.note-cell{max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.time-cell{font-size:13px;color:var(--text-light);white-space:nowrap;}
.actions{display:flex;gap:8px;}
.btn-copy{padding:6px 12px;background:linear-gradient(135deg,#7c3aed,#5b21b6);color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px;position:relative;}
.btn-copy:hover{transform:translateY(-1px);}
.empty-state{text-align:center;padding:60px;color:var(--text-light);}
.keys-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px;}
.key-card{background:rgba(0,0,0,0.2);border-radius:12px;padding:20px;border:1px solid var(--border);transition:transform 0.2s,box-shadow 0.2s;}
.key-card:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,0,0,0.3);}
.key-card-header{margin-bottom:15px;padding-bottom:12px;border-bottom:1px solid var(--border);}
.key-card-note{font-size:15px;font-weight:600;color:#fff;}
.key-card-body{margin-bottom:15px;}
.key-card-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;}
.key-card-label{font-size:13px;color:var(--text-light);}
.key-card-value{font-size:13px;color:#fff;font-family:monospace;}
.key-card-actions{display:flex;gap:8px;flex-wrap:wrap;}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:none;align-items:center;justify-content:center;z-index:1000;}
.modal.show{display:flex;}
.modal-content{background:linear-gradient(135deg,rgba(30,30,60,0.95),rgba(20,20,40,0.95));backdrop-filter:blur(20px);border-radius:20px;padding:30px;width:500px;max-width:90vw;border:1px solid var(--border);max-height:90vh;overflow-y:auto;}
.modal h3{font-size:20px;margin-bottom:20px;padding-bottom:15px;border-bottom:1px solid var(--border);}
.form-group{margin-bottom:15px;}
.form-group label{display:block;margin-bottom:8px;color:var(--text-light);font-size:14px;}
.form-group input,.form-group select{width:100%;padding:12px 16px;background:rgba(0,0,0,0.3);border:1px solid var(--border);border-radius:10px;color:#fff;font-size:14px;outline:none;}
.form-group input:focus{border-color:var(--primary);}
.form-group input::placeholder{color:rgba(255,255,255,0.4);}
.form-row{display:flex;gap:15px;}
.form-row .form-group{flex:1;}
.modal-btns{display:flex;gap:10px;margin-top:25px;}
.modal-close{background:rgba(255,255,255,0.1);color:#fff;border:none;padding:12px 24px;border-radius:10px;cursor:pointer;font-size:14px;}
.modal-close:hover{background:rgba(255,255,255,0.2);}
.toast{position:fixed;top:20px;right:20px;padding:15px 25px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,0.3);z-index:2000;display:none;animation:slideIn 0.3s ease;}
.toast.error{background:linear-gradient(135deg,#ef4444,#dc2626);}
@keyframes slideIn{from{transform:translateX(100px);opacity:0;}to{transform:translateX(0);opacity:1;}}
.recycle-table{width:100%;border-collapse:collapse;}
.recycle-table th,.recycle-table td{padding:12px;text-align:left;border-bottom:1px solid var(--border);font-size:13px;}
.recycle-table th{background:rgba(0,0,0,0.2);color:var(--text-light);}
.btn-success{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;}
.btn-success:hover{opacity:0.9;}
.copy-style-option{padding:16px;background:rgba(0,0,0,0.2);border:1px solid var(--border);border-radius:10px;margin-bottom:12px;cursor:pointer;transition:all 0.2s;}
.copy-style-option:hover{border-color:var(--primary);background:rgba(124,58,237,0.1);}
.copy-style-title{font-size:15px;font-weight:600;color:#fff;margin-bottom:8px;}
.copy-style-preview{font-size:12px;color:var(--text-light);font-family:monospace;white-space:pre-wrap;word-break:break-all;}
@media(max-width:768px){
  .stats{flex-direction:column;}
  .keys-list{grid-template-columns:1fr;gap:15px;}
  .key-card{padding:15px;}
  .key-card-header{margin-bottom:12px;padding-bottom:10px;}
  .key-card-note{font-size:14px;}
  .key-card-row{padding:6px 0;}
  .key-card-label{font-size:12px;}
  .key-card-value{font-size:12px;word-break:break-all;}
  .key-cell{font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis;display:inline-block;}
  .form-row{flex-direction:column;gap:0;}
  .quick-btns{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;}
  .quick-btn{padding:10px 8px;font-size:12px;text-align:center;}
  .container{padding:15px;}
  .card{padding:15px;}
  .header{padding:15px;}
}
</style>
</head>
<body>
<canvas id="dash-particles"></canvas>
<div class="header">
<h1>API Key 管理</h1>
<div class="user"><span>Admin</span><button onclick="logout()" class="logout">退出</button></div>
</div>
<div class="container">
<div class="stats">
<div class="stat-box"><div class="num">{{keys|length}}</div><div class="label">总数</div></div>
<div class="stat-box red"><div class="num">{{expired_count}}</div><div class="label">已过期</div></div>
</div>
<div class="card">
<h2>创建新的 API Key</h2>
<div class="quick-btns">
<button class="quick-btn" onclick="quickSelect(1,'h')">1小时</button>
<button class="quick-btn" onclick="quickSelect(6,'h')">6小时</button>
<button class="quick-btn" onclick="quickSelect(12,'h')">12小时</button>
<button class="quick-btn active" onclick="quickSelect(1,'d')">1天</button>
<button class="quick-btn" onclick="quickSelect(7,'d')">7天</button>
<button class="quick-btn" onclick="quickSelect(30,'d')">30天</button>
<button class="quick-btn" onclick="quickSelect(90,'d')">90天</button>
<button class="quick-btn" onclick="quickSelect(365,'d')">1年</button>
<button class="quick-btn" onclick="quickSelect(0,'n')">永不过期</button>
</div>
<form id="createForm">
<div class="form-row">
<div class="form-group"><label>开始时间（可选）</label><input type="datetime-local" id="startTime"></div>
<div class="form-group"><label>结束时间</label><input type="datetime-local" id="endTime"></div>
</div>
<div class="form-group"><label>备注</label><input type="text" id="noteInput" placeholder="输入备注信息"></div>
<div class="btn-group">
<button type="submit" class="btn">生成 API Key</button>
<button type="button" class="btn" onclick="openRecycle()">回收站</button>
</div>
</form>
</div>
<div class="card">
<h2>API Keys ({{keys|length}})</h2>
<div id="keysList" class="keys-list">
{% for k in keys %}
<div class="key-card" data-key="{{k.key}}">
<div class="key-card-header">
<span class="key-card-note">{{k.note}}</span>
</div>
<div class="key-card-body">
<div class="key-card-row">
<span class="key-card-label">API Key</span>
<span class="key-card-value key-cell">{{k.key}}</span>
</div>
<div class="key-card-row">
<span class="key-card-label">开始时间</span>
<span class="key-card-value">{{k.s}}{% if not k.s %}-{% endif %}</span>
</div>
<div class="key-card-row">
<span class="key-card-label">结束时间</span>
<span class="key-card-value">{{k.e}}</span>
</div>
</div>
<div class="key-card-actions">
<button onclick="openCopyModal('{{k.key}}')" class="btn-copy">复制</button>
<button onclick="editKey('{{k.key}}')" class="btn btn-sm">编辑</button>
<button onclick="deleteKey('{{k.key}}')" class="btn btn-danger btn-sm">删除</button>
</div>
</div>
{% endfor %}
{% if keys|length == 0 %}
<div class="empty-state">暂无 API Keys</div>
{% endif %}
</div>
</div>
</div>
<div id="editModal" class="modal">
<div class="modal-content">
<h3>编辑 API Key</h3>
<form id="editForm">
<input type="hidden" id="editKeyInput">
<div class="form-group"><label>备注</label><input type="text" id="editNote"></div>
<div class="form-row">
<div class="form-group"><label>开始时间</label><input type="datetime-local" id="editStartTime"></div>
<div class="form-group"><label>结束时间</label><input type="datetime-local" id="editEndTime"></div>
</div>
<div class="modal-btns"><button type="submit" class="btn">保存</button><button type="button" class="modal-close" onclick="closeModal()">取消</button></div>
</form>
</div>
</div>
<div id="recycleModal" class="modal">
<div class="modal-content" style="width:800px;">
<h3>回收站</h3>
<div id="recycleList"></div>
<div class="modal-btns"><button type="button" class="modal-close" onclick="closeRecycle()">关闭</button></div>
</div>
</div>
<div id="restoreModal" class="modal">
<div class="modal-content">
<h3>恢复 API Key</h3>
<form id="restoreForm">
<input type="hidden" id="restoreKey">
<div class="form-group"><label>备注</label><input type="text" id="restoreNote"></div>
<div class="form-row">
<div class="form-group"><label>开始时间</label><input type="datetime-local" id="restoreStart"></div>
<div class="form-group"><label>结束时间</label><input type="datetime-local" id="restoreEnd"></div>
</div>
<div class="modal-btns"><button type="submit" class="btn btn-success">恢复</button><button type="button" class="modal-close" onclick="closeRestore()">取消</button></div>
</form>
</div>
</div>
<div id="copyModal" class="modal">
<div class="modal-content" style="width:600px;">
<h3>选择复制样式</h3>
<div id="copyTemplateList"></div>
<div class="modal-btns"><button type="button" class="modal-close" onclick="closeCopyModal()">取消</button></div>
</div>
</div>
<div id="toast" class="toast"></div>
<script>
var COPY_TEMPLATES = {{ copy_templates | tojson }};
renderCopyTemplates();
// Particles animation
(function(){
  var canvas = document.getElementById("dash-particles");
  if(!canvas) return;
  var ctx = canvas.getContext("2d");
  var w = window.innerWidth;
  var h = window.innerHeight;
  canvas.width = w;
  canvas.height = h;
  var particles = [];
  for(var i=0; i<50; i++){
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 2 + 1,
      speed: Math.random() * 0.3 + 0.1,
      seed: Math.random() * 9999,
      opacity: Math.random() * 0.3 + 0.2
    });
  }
  function animate(){
    ctx.clearRect(0, 0, w, h);
    particles.forEach(function(p){
      p.y += p.speed;
      p.x += Math.sin(p.seed) * 0.2;
      if(p.y > h) p.y = 0;
      if(p.x > w) p.x = 0;
      if(p.x < 0) p.x = w;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, 2 * Math.PI);
      ctx.fillStyle = "rgba(79, 70, 229, " + p.opacity + ")";
      ctx.fill();
    });
    requestAnimationFrame(animate);
  }
  animate();
  window.addEventListener("resize", function(){
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = w;
    canvas.height = h;
  });
})();

function showToast(text, isError) {
  var toast = document.getElementById("toast");
  toast.textContent = text;
  toast.className = isError ? "toast error" : "toast";
  toast.style.display = "block";
  setTimeout(function(){ toast.style.display = "none"; }, 3000);
}

function logout() {
  localStorage.removeItem("apikey_manager_pwd");
  localStorage.removeItem("apikey_manager_remember");
  window.location.href = "/logout";
}

var currentCopyKey = "";

function openCopyModal(key) {
  currentCopyKey = key;
  document.getElementById("copyModal").classList.add("show");
}

function closeCopyModal() {
  document.getElementById("copyModal").classList.remove("show");
  currentCopyKey = "";
}

function renderCopyTemplates() {
  var list = document.getElementById("copyTemplateList");
  var html = "";
  COPY_TEMPLATES.forEach(function(tpl, idx) {
    var preview = tpl.content.replace(/{apikey}/g, "xxx").substring(0, 100) + "...";
    html += '<div class="copy-style-option" onclick="doCopyStyle(' + idx + ')">';
    html += '<div class="copy-style-title">' + tpl.name + '</div>';
    html += '<div class="copy-style-preview">' + preview + '</div>';
    html += '</div>';
  });
  list.innerHTML = html;
}

function doCopyStyle(styleIdx) {
  var tpl = COPY_TEMPLATES[styleIdx];
  if(!tpl) return;
  var text = tpl.content.replace(/{apikey}/g, currentCopyKey);
  doCopy(text);
  closeCopyModal();
}

function copyKey(key) {
  doCopy(key);
}

function doCopy(text) {
  if(navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function(){
      showToast("已复制到剪贴板");
    }).catch(function(){
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  var textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
  showToast("已复制到剪贴板");
}

function quickSelect(value, unit) {
  var now = new Date();
  var end;
  if(unit === "n") {
    document.getElementById("endTime").value = "";
    return;
  } else if(unit === "h") {
    end = new Date(now.getTime() + value * 3600000);
  } else if(unit === "d") {
    end = new Date(now.getTime() + value * 86400000);
  }
  function toLocalDateTimeStr(date) {
    var y = date.getFullYear();
    var mo = (date.getMonth() + 1).toString().padStart(2, '0');
    var d = date.getDate().toString().padStart(2, '0');
    var hh = date.getHours().toString().padStart(2, '0');
    var mm = date.getMinutes().toString().padStart(2, '0');
    return y + '-' + mo + '-' + d + 'T' + hh + ':' + mm;
  }
  var endStr = toLocalDateTimeStr(end);
  var nowStr = toLocalDateTimeStr(now);
  document.getElementById("startTime").value = nowStr;
  document.getElementById("endTime").value = endStr;
}

function editKey(key) {
  var card = document.querySelector('.key-card[data-key="' + key + '"]');
  var noteEl = card.querySelector('.key-card-note');
  var rows = card.querySelectorAll('.key-card-row');
  document.getElementById("editKeyInput").value = key;
  document.getElementById("editNote").value = noteEl ? noteEl.textContent.trim() : "";
  var startEl = rows[1] ? rows[1].querySelector('.key-card-value') : null;
  var endEl = rows[2] ? rows[2].querySelector('.key-card-value') : null;
  var startCell = startEl ? startEl.textContent.trim() : "";
  var endCell = endEl ? endEl.textContent.trim() : "";
  document.getElementById("editStartTime").value = startCell === "-" ? "" : startCell;
  document.getElementById("editEndTime").value = endCell === "永不过期" ? "" : endCell;
  document.getElementById("editModal").classList.add("show");
}

function closeModal() {
  document.getElementById("editModal").classList.remove("show");
}

function deleteKey(key) {
  if(!confirm("确定要删除此 API Key?")) return;
  fetch("/api/keys", {
    method: "DELETE",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({key: key})
  }).then(function(r){ return r.json(); }).then(function(j){
    if(j.success) {
      showToast("已删除");
      setTimeout(function(){ location.reload(); }, 1000);
    } else {
      showToast(j.error || "错误", true);
    }
  }).catch(function(){ showToast("错误", true); });
}

function openRecycle() {
  fetch("/api/recycle").then(function(r){ return r.json(); }).then(function(j){
    var list = document.getElementById("recycleList");
    if(j.items.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">回收站为空</div>';
    } else {
      var html = '<table class="recycle-table"><thead><tr><th>Key</th><th>备注</th><th>过期时间</th><th>删除方式</th><th>删除时间</th><th>操作</th></tr></thead><tbody>';
      j.items.forEach(function(item){
        var note = item.note || "-";
        var expiredTime = item.expires_at ? item.expires_at.replace("T", " ").substring(0, 19) : "永不过期";
        var deletedBy = item.deleted_by === "expired" ? "过期清理" : "手动删除";
        var deletedTime = item.deleted_at ? item.deleted_at.replace("T", " ").substring(0, 19) : "-";
        var encodedNote = btoa(unescape(encodeURIComponent(note)));
        html += '<tr data-key="' + item.key + '" data-note="' + encodedNote + '">';
        html += '<td style="word-break:break-all;font-size:12px;">' + item.key + '</td>';
        html += '<td>' + note + '</td>';
        html += '<td>' + expiredTime + '</td>';
        html += '<td>' + deletedBy + '</td>';
        html += '<td>' + deletedTime + '</td>';
        html += '<td><button onclick="restoreFromRow(this)" class="btn-success btn-sm">恢复</button> <button onclick="permanentDelete(this)" class="btn btn-danger btn-sm" data-key="' + item.key + '">彻底删除</button></td>';
        html += '</tr>';
      });
      html += '</tbody></table>';
      list.innerHTML = html;
    }
    document.getElementById("recycleModal").classList.add("show");
  }).catch(function(){ showToast("加载失败", true); });
}

function closeRecycle() {
  document.getElementById("recycleModal").classList.remove("show");
}

function restoreFromRow(btn) {
  var row = btn.closest("tr");
  var key = row.getAttribute("data-key");
  var note = decodeURIComponent(escape(atob(row.getAttribute("data-note") || "")));
  document.getElementById("restoreKey").value = key;
  document.getElementById("restoreNote").value = note;
  document.getElementById("restoreStart").value = "";
  document.getElementById("restoreEnd").value = "";
  document.getElementById("restoreModal").classList.add("show");
}

function permanentDelete(btn) {
  if(!confirm("彻底删除后无法恢复，确定?")) return;
  var key = btn.getAttribute("data-key");
  fetch("/api/recycle/permanent", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({key: key})
  }).then(function(r){ return r.json(); }).then(function(j){
    if(j.success) {
      showToast("已彻底删除");
      setTimeout(function(){ location.reload(); }, 1000);
    } else {
      showToast(j.error || "错误", true);
    }
  }).catch(function(){ showToast("错误", true); });
}

function closeRestore() {
  document.getElementById("restoreModal").classList.remove("show");
}

// Form submissions
document.getElementById("createForm").onsubmit = function(e) {
  e.preventDefault();
  var s = document.getElementById("startTime").value;
  var t = document.getElementById("endTime").value;
  var n = document.getElementById("noteInput").value;
  fetch("/api/keys", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({starts_at: s || null, expires_at: t, note: n})
  }).then(function(r){ return r.json(); }).then(function(j){
    if(j.success) {
      showToast("API Key 已生成");
      setTimeout(function(){ location.reload(); }, 1500);
    } else {
      showToast(j.error || "错误", true);
    }
  }).catch(function(){ showToast("错误", true); });
};

document.getElementById("editForm").onsubmit = function(e) {
  e.preventDefault();
  var k = document.getElementById("editKeyInput").value;
  var n = document.getElementById("editNote").value;
  var s = document.getElementById("editStartTime").value;
  var t = document.getElementById("editEndTime").value;
  fetch("/api/keys/update", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({key: k, starts_at: s || null, expires_at: t, note: n})
  }).then(function(r){ return r.json(); }).then(function(j){
    if(j.success) {
      showToast("已保存");
      setTimeout(function(){ location.reload(); }, 1000);
    } else {
      showToast(j.error || "错误", true);
    }
  }).catch(function(){ showToast("错误", true); });
};

document.getElementById("restoreForm").onsubmit = function(e) {
  e.preventDefault();
  var k = document.getElementById("restoreKey").value;
  var n = document.getElementById("restoreNote").value;
  var s = document.getElementById("restoreStart").value;
  var t = document.getElementById("restoreEnd").value;
  fetch("/api/recycle/restore", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({key: k, starts_at: s || null, expires_at: t, note: n})
  }).then(function(r){ return r.json(); }).then(function(j){
    if(j.success) {
      showToast("已恢复");
      setTimeout(function(){ location.reload(); }, 1000);
    } else {
      showToast(j.error || "错误", true);
    }
  }).catch(function(){ showToast("错误", true); });
};

// Modal close on background click
document.getElementById("editModal").onclick = function(e) { if(e.target === this) closeModal(); };
document.getElementById("recycleModal").onclick = function(e) { if(e.target === this) closeRecycle(); };
document.getElementById("restoreModal").onclick = function(e) { if(e.target === this) closeRestore(); };
document.getElementById("copyModal").onclick = function(e) { if(e.target === this) closeCopyModal(); };
</script>
</body>
</html>"""

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET": return render_template_string(LOGIN) if not session.get("auth") else redirect("/")
    if request.form.get("password") == PASSWORD:
        session["auth"] = True
        return redirect("/")
    return render_template_string(LOGIN, e=1)

@app.route("/logout")
def logout():
    session.pop("auth", None)
    return redirect("/login")

@app.route("/")
@auth
def dashboard():
    cfg = load()
    keys = cfg.get("api-keys", [])
    meta = cfg.get("api-key-metadata", {})
    info = []
    for k in keys:
        m = meta.get(k, {})
        starts_at = m.get("starts_at")
        expires_at = m.get("expires_at")
        starts_disp = "-"
        exp_disp = "永不过期"
        status = "active"
        if starts_at:
            try:
                start_time = datetime.fromisoformat(starts_at)
                if datetime.now() < start_time:
                    status = "pending"
                    starts_disp = starts_at[:16]
                    exp_disp = expires_at[:16] if expires_at else "永不过期"
                else:
                    starts_disp = starts_at[:16]
            except:
                starts_disp = starts_at[:16] if starts_at else "-"
        if expires_at:
            try:
                exp_time = datetime.fromisoformat(expires_at)
                if datetime.now() >= exp_time:
                    status = "expired"
                exp_disp = expires_at[:16]
            except:
                exp_disp = expires_at[:16] if expires_at else "永不过期"
        note = m.get("note", "")
        info.append({"key": k, "s": starts_disp, "e": exp_disp, "status": status, "note": note})
    info.sort(key=lambda x: (x["status"] == "active", x["status"] == "pending", x["s"]), reverse=True)
    recycle = load_recycle()
    expired_count = len(recycle)
    return render_template_string(DASH, keys=info, expired_count=expired_count, copy_templates=COPY_TEMPLATES)

@app.route("/api/keys", methods=["GET"])
@auth
def get_keys():
    cfg = load()
    keys = cfg.get("api-keys", [])
    meta = cfg.get("api-key-metadata", {})
    return jsonify({"keys": [{"key": k, "starts_at": meta.get(k, {}).get("starts_at"), "expires_at": meta.get(k, {}).get("expires_at"), "note": meta.get(k, {}).get("note", "")} for k in keys]})

@app.route("/api/keys", methods=["POST"])
@auth
def create_key():
    data = request.get_json()
    starts_at = data.get("starts_at")
    expires_at = data.get("expires_at")
    note = data.get("note", "")
    new_key = gen_key()
    with lock:
        cfg = load()
        if "api-keys" not in cfg: cfg["api-keys"] = []
        if "api-key-metadata" not in cfg: cfg["api-key-metadata"] = {}
        cfg["api-keys"].append(new_key)
        cfg["api-key-metadata"][new_key] = {"created_at": datetime.now().isoformat(), "starts_at": starts_at, "expires_at": expires_at, "note": note}
        save(cfg)
    return jsonify({"success": True, "key": new_key})

@app.route("/api/keys/update", methods=["POST"])
@auth
def update_key():
    data = request.get_json()
    k = data.get("key")
    starts_at = data.get("starts_at")
    expires_at = data.get("expires_at")
    note = data.get("note", "")
    with lock:
        cfg = load()
        if k not in cfg.get("api-keys", []):
            return jsonify({"error": "Key not found"}), 404
        if "api-key-metadata" not in cfg: cfg["api-key-metadata"] = {}
        meta = cfg["api-key-metadata"].get(k, {})
        meta["starts_at"] = starts_at
        meta["expires_at"] = expires_at
        meta["note"] = note
        cfg["api-key-metadata"][k] = meta
        save(cfg)
    return jsonify({"success": True})

@app.route("/api/keys", methods=["DELETE"])
@auth
def delete_key():
    data = request.get_json()
    k = data.get("key")
    with lock:
        cfg = load()
        if k in cfg.get("api-keys", []):
            meta = cfg.get("api-key-metadata", {}).get(k, {})
            recycle = load_recycle()
            recycle.append({"key": k, "deleted_at": datetime.now().isoformat(), "created_at": meta.get("created_at"), "starts_at": meta.get("starts_at"), "expires_at": meta.get("expires_at"), "note": meta.get("note", ""), "deleted_by": "manual"})
            save_recycle(recycle)
            cfg["api-keys"].remove(k)
            if k in cfg.get("api-key-metadata", {}): del cfg["api-key-metadata"][k]
            save(cfg)
            return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/recycle", methods=["GET"])
@auth
def get_recycle():
    return jsonify({"items": load_recycle()})

@app.route("/api/recycle/restore", methods=["POST"])
@auth
def restore_recycle():
    data = request.get_json()
    k = data.get("key")
    starts_at = data.get("starts_at")
    expires_at = data.get("expires_at")
    note = data.get("note", "")
    recycle = load_recycle()
    item = None
    for i, r in enumerate(recycle):
        if r["key"] == k:
            item = recycle.pop(i)
            break
    if not item:
        return jsonify({"error": "Not found"}), 404
    save_recycle(recycle)
    with lock:
        cfg = load()
        if "api-keys" not in cfg: cfg["api-keys"] = []
        if "api-key-metadata" not in cfg: cfg["api-key-metadata"] = {}
        cfg["api-keys"].append(k)
        cfg["api-key-metadata"][k] = {"created_at": item.get("created_at"), "starts_at": starts_at, "expires_at": expires_at, "note": note}
        save(cfg)
    return jsonify({"success": True})

@app.route("/api/recycle/permanent", methods=["POST"])
@auth
def permanent_delete():
    data = request.get_json()
    k = data.get("key")
    recycle = load_recycle()
    for i, r in enumerate(recycle):
        if r["key"] == k:
            recycle.pop(i)
            save_recycle(recycle)
            return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/cleanup", methods=["POST"])
@auth
def cleanup_api():
    return jsonify({"success": True, "count": cleanup()})

if __name__ == "__main__":
    cleanup()
    threading.Thread(target=cleanup_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)