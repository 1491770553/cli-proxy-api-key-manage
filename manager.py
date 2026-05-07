#!/usr/bin/env python3
import os, sys, json, yaml, secrets, threading, time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, session

CONFIG = "/data/CLIProxyAPI_6.9.38_linux_amd64/config.yaml"
RECYCLE_FILE = "/data/CLIProxyAPI_6.9.38_linux_amd64/recycle.json"
PASSWORD = "wlie0726"
PORT = 18317

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
        recycle=load_recycle()
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
                                recycle.append({
                                    "key":k,
                                    "deleted_at":now.isoformat(),
                                    "created_at":m.get("created_at"),
                                    "starts_at":starts_at,
                                    "expires_at":exp,
                                    "note":m.get("note",""),
                                    "deleted_by":"expired"
                                })
                                rem += 1
                                continue
                        except:
                            if now >= datetime.fromisoformat(exp):
                                recycle.append({
                                    "key":k,
                                    "deleted_at":now.isoformat(),
                                    "created_at":m.get("created_at"),
                                    "starts_at":starts_at,
                                    "expires_at":exp,
                                    "note":m.get("note",""),
                                    "deleted_by":"expired"
                                })
                                rem += 1
                                continue
                    else:
                        if now >= datetime.fromisoformat(exp):
                            recycle.append({
                                "key":k,
                                "deleted_at":now.isoformat(),
                                "created_at":m.get("created_at"),
                                "starts_at":starts_at,
                                "expires_at":exp,
                                "note":m.get("note",""),
                                "deleted_by":"expired"
                            })
                            rem += 1
                            continue
                except: pass
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
body{
  font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;
  background:linear-gradient(135deg,#0c0c1e 0%,#1a1a3e 50%,#2d1b4e 100%);
  overflow:hidden;
  position:relative;
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
}
.login-box{
  background:rgba(255,255,255,0.1);
  backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);
  padding:50px;
  border-radius:24px;
  box-shadow:0 25px 70px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.1);
  width:420px;
  max-width:90vw;
  animation:slideUp 0.6s cubic-bezier(0.16,1,0.3,1);
  border:1px solid rgba(255,255,255,0.15);
  position:relative;
  z-index:1;
}
@keyframes slideUp{
  from{opacity:0;transform:translateY(30px)}
  to{opacity:1;transform:translateY(0)}
}
.login-box h1{
  text-align:center;
  color:#ffffff;
  margin-bottom:10px;
  font-size:32px;
  font-weight:700;
  text-shadow:0 2px 20px rgba(0,0,0,0.3);
}
.login-box p{
  text-align:center;
  color:rgba(255,255,255,0.6);
  margin-bottom:35px;
  font-size:14px;
  letter-spacing:2px;
}
.login-box input{
  width:100%;
  padding:16px 20px;
  margin:12px 0;
  border:2px solid rgba(255,255,255,0.15);
  border-radius:12px;
  font-size:16px;
  transition:all 0.3s ease;
  outline:none;
  background:rgba(255,255,255,0.08);
  color:#fff;
}
.login-box input::placeholder{color:rgba(255,255,255,0.4);}
.login-box input:focus{
  border-color:#7c3aed;
  box-shadow:0 0 0 4px rgba(124,58,237,0.2);
  background:rgba(255,255,255,0.12);
}
.login-box button{
  width:100%;
  padding:16px;
  background:linear-gradient(135deg,#7c3aed,#5b21b6);
  color:white;
  border:none;
  border-radius:12px;
  font-size:18px;
  font-weight:600;
  cursor:pointer;
  margin-top:20px;
  transition:all 0.3s cubic-bezier(0.16,1,0.3,1);
  box-shadow:0 4px 20px rgba(124,58,237,0.4);
}
.login-box button:hover{
  transform:translateY(-3px);
  box-shadow:0 8px 30px rgba(124,58,237,0.6);
}
.login-box .remember-row{
  display:flex;
  align-items:center;
  margin-top:15px;
}
.login-box .remember-row label{
  display:flex;
  align-items:center;
  gap:8px;
  color:#666;
  font-size:14px;
  cursor:pointer;
}
.login-box .remember-row input[type="checkbox"]{
  width:18px;
  height:18px;
  cursor:pointer;
  accent-color:#7c3aed;
}
.login-box .error{
  color:#e74c3c;
  text-align:center;
  margin-top:15px;
  font-size:14px;
  animation:shake 0.5s ease;
}
@keyframes shake{
  0%,100%{transform:translateX(0)}
  25%{transform:translateX(-10px)}
  75%{transform:translateX(10px)}
}
</style>
</head>
<body>
<div class="login-box">
<h1>API Key 管理</h1>
<p>CLI Proxy API Management Panel</p>
<form method="POST" id="loginForm">
<input type="password" name="password" id="passwordInput" placeholder="Enter password" required>
<div class="remember-row">
<label><input type="checkbox" id="rememberMe"> Remember password</label>
</div>
<button type="submit">Sign In</button>
</form>
{% if e %}<p class="error">Invalid password, please try again</p>{% endif %}
<script>
if(localStorage.getItem("apikey_manager_pwd")){
  document.getElementById("passwordInput").value=localStorage.getItem("apikey_manager_pwd");
  if(localStorage.getItem("apikey_manager_remember")==="1"){
    document.getElementById("rememberMe").checked=true;
    document.getElementById("loginForm").submit();
  }
}
document.getElementById("loginForm").onsubmit=function(){
  if(document.getElementById("rememberMe").checked){
    localStorage.setItem("apikey_manager_pwd",document.getElementById("passwordInput").value);
    localStorage.setItem("apikey_manager_remember","1");
  } else {
    localStorage.removeItem("apikey_manager_pwd");
    localStorage.removeItem("apikey_manager_remember");
  }
};
</script>
<canvas id="particles-canvas"></canvas>
<script>
!function(){
  const canvas=document.getElementById("particles-canvas");
  const ctx=canvas.getContext("2d");
  let width=window.innerWidth,height=window.innerHeight;
  canvas.width=width;canvas.height=height;
  const particles=[];
  for(let i=0;i<80;i++){
    particles.push({
      x:Math.random()*width,
      y:Math.random()*height,
      r:Math.random()*2+1,
      speed:Math.random()*0.5+0.2,
      seed:Math.random()*9999
    });
  }
  function animate(){
    ctx.clearRect(0,0,width,height);
    particles.forEach(p=>{
      p.y+=p.speed;
      p.x+=Math.sin(p.seed)*0.3;
      if(p.y>height)p.y=0;
      if(p.x>width)p.x=0;
      if(p.x<0)p.x=width;
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,2*Math.PI);
      ctx.fillStyle="rgba(124,58,237,0.5)";
      ctx.fill();
    });
    requestAnimationFrame(animate);
  }
  window.addEventListener("resize",()=>{
    width=window.innerWidth;height=window.innerHeight;
    canvas.width=width;canvas.height=height;
  });
  animate();
}();
</script>

</div>
</body><canvas id="dash-particles" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;"></canvas>
<script>
!function(){
  const canvas=document.getElementById("dash-particles");
  if(!canvas)return;
  const ctx=canvas.getContext("2d");
  let w=window.innerWidth,h=window.innerHeight;
  canvas.width=w;canvas.height=h;
  const ps=[];
  for(let i=0;i<50;i++)ps.push({x:Math.random()*w,y:Math.random()*h,r:Math.random()*2+1,spd:Math.random()*0.3+0.1,s:Math.random()*9999,op:Math.random()*0.3+0.2});
  function an(){
    ctx.clearRect(0,0,w,h);
    ps.forEach(p=>{
      p.y+=p.spd;p.x+=Math.sin(p.s)*0.2;
      if(p.y>h)p.y=0;if(p.x>w)p.x=0;if(p.x<0)p.x=w;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,2*Math.PI);
      ctx.fillStyle="rgba(79,70,229,"+p.op+")";ctx.fill();
    });
    requestAnimationFrame(an);
  }
  window.addEventListener("resize",()=>{w=window.innerWidth;h=window.innerHeight;canvas.width=w;canvas.height=h;});
  an();
}();
</script>
<canvas id="particles-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;"></canvas>
<script>
!function(){
  const canvas=document.getElementById("particles-canvas");
  const ctx=canvas.getContext("2d");
  let w=window.innerWidth,h=window.innerHeight;
  canvas.width=w;canvas.height=h;
  const ps=[];
  for(let i=0;i<80;i++)ps.push({x:Math.random()*w,y:Math.random()*h,r:Math.random()*2+1,spd:Math.random()*0.5+0.2,s:Math.random()*9999});
  function an(){
    ctx.clearRect(0,0,w,h);
    ps.forEach(p=>{
      p.y+=p.spd;p.x+=Math.sin(p.s)*0.3;
      if(p.y>h)p.y=0;if(p.x>w)p.x=0;if(p.x<0)p.x=w;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,2*Math.PI);
      ctx.fillStyle="rgba(124,58,237,0.5)";ctx.fill();
    });
    requestAnimationFrame(an);
  }
  window.addEventListener("resize",()=>{w=window.innerWidth;h=window.innerHeight;canvas.width=w;canvas.height=h;});
  an();
}();
</script>
<canvas id="particles-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;"></canvas>
<script>
!function(){
  const canvas=document.getElementById("particles-canvas");
  const ctx=canvas.getContext("2d");
  let width=window.innerWidth,height=window.innerHeight;
  canvas.width=width;canvas.height=height;
  const particles=[];
  for(let i=0;i<60;i++){
    particles.push({
      x:Math.random()*width,
      y:Math.random()*height,
      r:Math.random()*2+1,
      speed:Math.random()*0.3+0.1,
      seed:Math.random()*9999,
      opacity:Math.random()*0.3+0.2
    });
  }
  function animate(){
    ctx.clearRect(0,0,width,height);
    particles.forEach(p=>{
      p.y+=p.speed;
      p.x+=Math.sin(p.seed)*0.2;
      if(p.y>height)p.y=0;
      if(p.x>width)p.x=0;
      if(p.x<0)p.x=width;
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r,0,2*Math.PI);
      ctx.fillStyle="rgba(79,70,229,"+p.opacity+")";
      ctx.fill();
    });
    requestAnimationFrame(animate);
  }
  window.addEventListener("resize",()=>{
    width=window.innerWidth;height=window.innerHeight;
    canvas.width=width;canvas.height=height;
  });
  animate();
}();
</script>

</html>"""

DASH = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>API Key 管理</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --primary:#7c3aed;
  --primary-dark:#5b21b6;
  --success:#10b981;
  --danger:#ef4444;
  --warning:#f59e0b;
  --bg:linear-gradient(135deg,#0c0c1e 0%,#1a1a3e 50%,#2d1b4e 100%);
  --card-bg:rgba(255,255,255,0.08);
  --text:#ffffff;
  --text-light:rgba(255,255,255,0.6);
  --border:rgba(255,255,255,0.1);
}
body{
  font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;
  background:var(--bg);
  background-attachment:fixed;
  color:var(--text);
  min-height:100vh;
  position:relative;
}
.header{
  background:linear-gradient(135deg,#4f46e5,#7c3aed);
  color:white;
  padding:24px 40px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  box-shadow:0 4px 20px rgba(79,70,229,0.3);
}
.header h1{font-size:24px;font-weight:600}
.header .user{
  display:flex;
  align-items:center;
  gap:15px;
}
.header .user span{
  background:rgba(255,255,255,0.2);
  padding:8px 16px;
  border-radius:20px;
  font-size:14px;
}
.logout{
  color:white;
  text-decoration:none;
  padding:10px 20px;
  background:rgba(255,255,255,0.15);
  border-radius:10px;
  transition:all 0.3s;
}
.logout:hover{background:rgba(255,255,255,0.25)}
.container{
  max-width:1400px;
  margin:0 auto;
  padding:30px 40px;
}
.card{
  background:var(--card-bg);
  border-radius:16px;
  padding:30px;
  margin-bottom:25px;
  box-shadow:0 1px 3px rgba(0,0,0,0.05),0 10px 40px rgba(0,0,0,0.03);
  border:1px solid var(--border);
}
.card-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:25px;
  padding-bottom:15px;
  border-bottom:2px solid var(--border);
}
.card-header h2{
  font-size:20px;
  font-weight:600;
  color:var(--text);
}
.stats{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:20px;
  margin-bottom:30px;
}
.stat-box{
  background:linear-gradient(135deg,#4f46e5,#7c3aed);
  color:white;
  padding:25px;
  border-radius:16px;
  text-align:center;
  box-shadow:0 10px 30px rgba(79,70,229,0.3);
}
.stat-box.green{background:linear-gradient(135deg,#10b981,#059669)}
.stat-box.red{background:linear-gradient(135deg,#ef4444,#dc2626)}
.stat-box .num{font-size:36px;font-weight:700}
.stat-box .label{font-size:14px;opacity:0.9;margin-top:5px}
.quick-btns{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-bottom:25px;
}
.quick-btn{
  padding:10px 20px;
  background:#f1f5f9;
  color:var(--text);
  border:2px solid var(--border);
  border-radius:10px;
  font-size:14px;
  font-weight:500;
  cursor:pointer;
  transition:all 0.2s;
}
.quick-btn:hover{
  border-color:var(--primary);
  background:#eef2ff;
  color:var(--primary);
}
.quick-btn.active{
  border-color:var(--primary);
  background:var(--primary);
  color:white;
}
.form-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:20px;
  margin-bottom:20px;
}
.form-group{margin-bottom:0}
.form-group label{
  display:block;
  margin-bottom:8px;
  font-weight:500;
  color:var(--text);
  font-size:14px;
}
.form-group input{
  width:100%;
  padding:14px 16px;
  border:2px solid var(--border);
  border-radius:10px;
  font-size:15px;
  transition:all 0.3s;
  outline:none;
}
.form-group input:focus{
  border-color:var(--primary);
  box-shadow:0 0 0 4px rgba(79,70,229,0.1);
}
.btn{
  padding:14px 28px;
  background:var(--primary);
  color:white;
  border:none;
  border-radius:10px;
  font-size:15px;
  font-weight:600;
  cursor:pointer;
  transition:all 0.3s;
}
.btn:hover{
  background:var(--primary-dark);
  transform:translateY(-2px);
  box-shadow:0 10px 20px rgba(79,70,229,0.3);
}
.btn-success{background:var(--success)}
.btn-success:hover{background:#059669}
.btn-danger{background:var(--danger)}
.btn-danger:hover{background:#dc2626}
.btn-warning{background:var(--warning)}
.btn-warning:hover{background:#d97706}
.btn-sm{padding:10px 16px;font-size:13px}
.btn-sm:hover{transform:none}
.btn-copy{
  padding:8px 14px;
  background:#10b981;
  color:white;
  border:none;
  border-radius:8px;
  font-size:13px;
  cursor:pointer;
  transition:all 0.2s;
}
.btn-copy:hover{background:#059669}
.btn-group{display:flex;gap:10px}
.search-box{
  margin-bottom:20px;
  position:relative;
}
.search-box input{
  width:100%;
  padding:14px 20px;
  padding-left:45px;
  border:2px solid var(--border);
  border-radius:12px;
  font-size:15px;
  outline:none;
  transition:all 0.3s;
}
.search-box input:focus{
  border-color:var(--primary);
  box-shadow:0 0 0 4px rgba(79,70,229,0.1);
}
.search-box::before{
  content:"🔍";
  position:absolute;
  left:16px;
  top:50%;
  transform:translateY(-50%);
  font-size:18px;
}
table{width:100%;border-collapse:collapse}
thead th{
  background:var(--bg);
  padding:14px 16px;
  text-align:left;
  font-weight:600;
  font-size:13px;
  color:var(--text-light);
  text-transform:uppercase;
  letter-spacing:0.5px;
}
tbody td{
  padding:18px 16px;
  border-bottom:1px solid var(--border);
  vertical-align:middle;
}
tbody tr:hover{background:rgba(79,70,229,0.02)}
tbody tr:last-child td{border-bottom:none}
.key-cell{
  font-family:'Consolas','Monaco',monospace;
  background:#f1f5f9;
  padding:8px 14px;
  border-radius:8px;
  font-size:13px;
  word-break:break-all;
  max-width:280px;
}
.note-cell{
  font-size:13px;
  color:#333;
  max-width:150px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.note-cell:hover{
  white-space:normal;
  word-break:break-all;
}
.status{
  display:inline-flex;
  align-items:center;
  gap:6px;
  padding:6px 14px;
  border-radius:20px;
  font-size:13px;
  font-weight:500;
}
.status.active{background:#dcfce7;color:#166534}
.status.expired{background:#fee2e2;color:#991b1b}
.status.pending{background:#fef3c7;color:#92400e}
.status::before{
  content:"";
  width:8px;
  height:8px;
  border-radius:50%;
}
.status.active::before{background:#22c55e}
.status.expired::before{background:#ef4444}
.status.pending::before{background:#f59e0b}
.time-cell{font-size:14px;color:var(--text)}
.time-cell small{display:block;font-size:12px;color:var(--text-light);margin-top:2px}
.actions{display:flex;gap:8px}
.toast{
  position:fixed;
  bottom:30px;
  right:30px;
  padding:18px 28px;
  background:var(--text);
  color:white;
  border-radius:12px;
  font-size:15px;
  box-shadow:0 10px 40px rgba(0,0,0,0.2);
  z-index:1000;
  animation:slideIn 0.3s ease;
  display:none;
}
.toast.success{background:var(--success)}
.toast.error{background:var(--danger)}
@keyframes slideIn{
  from{opacity:0;transform:translateY(20px)}
  to{opacity:1;transform:translateY(0)}
}
.modal{
  display:none;
  position:fixed;
  inset:0;
  background:rgba(0,0,0,0.5);
  z-index:100;
  align-items:center;
  justify-content:center;
  backdrop-filter:blur(4px);
}
.modal.show{display:flex}
.modal-content{
  background:white;
  border-radius:20px;
  padding:35px;
  width:600px;
  max-width:90vw;
  max-height:90vh;
  overflow-y:auto;
  animation:modalIn 0.3s ease;
}
@keyframes modalIn{
  from{opacity:0;transform:scale(0.95)}
  to{opacity:1;transform:scale(1)}
}
.modal-content h3{
  font-size:22px;
  margin-bottom:25px;
  color:var(--text);
}
.modal-content .btn-group{
  margin-top:25px;
  justify-content:flex-end;
}
.copy-option{
  border:2px solid var(--border);
  border-radius:12px;
  padding:20px;
  margin-bottom:15px;
  cursor:pointer;
  transition:all 0.2s;
}
.copy-option:hover{
  border-color:var(--primary);
  background:#f8faff;
}
.copy-option.selected{
  border-color:var(--primary);
  background:#eef2ff;
}
.copy-option h4{
  font-size:16px;
  margin-bottom:8px;
  color:var(--text);
}
.copy-option p{
  font-size:13px;
  color:var(--text-light);
  line-height:1.5;
}
.copy-preview{
  background:#f8fafc;
  border:1px solid var(--border);
  border-radius:8px;
  padding:15px;
  margin-top:15px;
  font-family:monospace;
  font-size:12px;
  white-space:pre-wrap;
  word-break:break-all;
  max-height:200px;
  overflow-y:auto;
}
.empty-state{
  text-align:center;
  padding:60px 20px;
  color:var(--text-light);
}
.empty-state .icon{font-size:48px;margin-bottom:15px}
.empty-state p{font-size:16px}
/* Mobile H5 Adaptation */
@media (max-width: 768px) {
  *{webkit-tap-highlight-color:transparent}
  body{font-size:14px}
  .header{
    padding:15px 12px;
    flex-direction:column;
    gap:12px;
    text-align:center;
  }
  .header h1{font-size:18px}
  .header .user{width:100%;justify-content:center}
  .logout{padding:8px 16px;font-size:13px}
  .container{padding:12px}
  .card{
    padding:16px;
    margin-bottom:16px;
    border-radius:12px;
  }
  .card-header{
    flex-direction:column;
    gap:12px;
    align-items:flex-start;
  }
  .card-header h2{font-size:16px}
  .stats{
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-bottom:16px;
  }
  .stat-box{
    padding:16px 12px;
    border-radius:12px;
  }
  .stat-box .num{font-size:24px}
  .stat-box .label{font-size:12px}
  .quick-btns{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin-bottom:16px;
  }
  .quick-btn{
    padding:10px 8px;
    font-size:12px;
    text-align:center;
    border-radius:8px;
  }
  .form-grid{
    grid-template-columns:1fr;
    gap:12px;
    margin-bottom:12px;
  }
  .form-group input{
    padding:12px;
    font-size:14px;
  }
  .btn{
    padding:12px 20px;
    font-size:14px;
    width:100%;
    border-radius:8px;
  }
  .btn-group{flex-direction:column}
  .search-box{margin-bottom:12px}
  .search-box input{
    padding:12px 14px 12px 40px;
    font-size:14px;
  }
  table{
    display:block;
    overflow-x:auto;
    -webkit-overflow-scrolling:touch;
  }
  thead th{
    padding:10px 8px;
    font-size:11px;
    white-space:nowrap;
  }
  tbody td{
    padding:12px 8px;
    font-size:13px;
  }
  .key-cell{
    padding:6px 10px;
    font-size:11px;
    max-width:180px;
  }
  .note-cell{
    font-size:11px;
    max-width:80px;
  }
  .status{
    padding:4px 10px;
    font-size:11px;
  }
  .actions{
    display:flex;
    flex-direction:column;
    gap:6px;
  }
  .actions .btn,.actions .btn-copy,.actions .btn-sm{
    width:100%;
    padding:8px 10px;
    font-size:12px;
    text-align:center;
  }
  .toast{
    left:16px;
    right:16px;
    bottom:20px;
    padding:14px 20px;
    font-size:14px;
  }
  .modal-content{
    width:calc(100% - 24px);
    max-width:none;
    margin:12px;
    padding:20px;
    border-radius:16px;
  }
  .modal-content h3{font-size:18px;margin-bottom:16px}
  .copy-option{
    padding:14px;
    margin-bottom:10px;
    border-radius:10px;
  }
  .copy-option h4{font-size:14px}
  .copy-option p{font-size:12px}
  .copy-preview{
    padding:10px;
    font-size:11px;
    margin-top:10px;
  }
  .empty-state{padding:40px 16px}
  .empty-state .icon{font-size:36px}
  .empty-state p{font-size:14px}
}
/* Very small screens */
@media (max-width: 375px) {
  .quick-btns{grid-template-columns:repeat(3,1fr)}
  .stats{grid-template-columns:1fr 1fr}
  .header h1{font-size:16px}
}
/* Landscape mode on mobile */
@media (max-height: 500px) and (orientation: landscape) {
  .header{padding:10px 15px}
  .container{padding:10px}
  .stats{grid-template-columns:repeat(3,1fr)}
  .card{padding:12px}
}
</style>
</head>
<body>
<div class="header">
<h1>API Key 管理</h1>
<div class="user">
<span>Admin</span>
<button onclick="logout()" class="logout">退出</button>
</div>
</div>
<div class="container">
<div class="stats">
<div class="stat-box">
<div class="num">{{keys|length}}</div>
<div class="label">总数</div>
</div>
<div class="stat-box red">
<div class="num">{{expired_count}}</div>
<div class="label">已过期</div>
</div>
</div>
<div class="card">
<div class="card-header">
<h2>创建新的 API Key</h2>
</div>
<div class="quick-btns">
<button class="quick-btn" onclick="quickSelect(1,'h')">1小时</button>
<button class="quick-btn" onclick="quickSelect(6,'h')">6小时</button>
<button class="quick-btn" onclick="quickSelect(12,'h')">12小时</button>
<button class="quick-btn active" onclick="quickSelect(1,'d')">1天</button>
<button class="quick-btn" onclick="quickSelect(7,'d')">7天</button>
<button class="quick-btn" onclick="quickSelect(30,'d')">30天</button>
<button class="quick-btn" onclick="quickSelect(90,'d')">90天</button>
<button class="quick-btn" onclick="quickSelect(365,'d')">1年</button>
</div>
<form id="createForm">
<div class="form-grid">
<div class="form-group">
<label>备注（可选）</label>
<input type="text" id="noteInput" placeholder="请输入备注">
</div>
<div class="form-group">
<label>开始时间</label>
<input type="datetime-local" id="startTime">
</div>
<div class="form-group">
<label>结束时间</label>
<input type="datetime-local" id="endTime" required>
</div>
</div>
<div class="btn-group">
<button type="submit" class="btn btn-success">生成 API Key</button>
</div>
</form>
</div>
<div class="card">
<div class="card-header">
<h2>API Keys 列表</h2>
<div class="btn-group">
<button onclick="openRecycle()" class="btn btn-sm">回收站</button>
</div>
</div>
<div class="search-box">
<input type="text" id="searchInput" placeholder="搜索..." onkeyup="filterTable()">
</div>
{% if keys %}
<table>
<thead>
<tr>
<th>API Key</th>
<th>备注</th>
<th>开始时间</th>
<th>结束时间</th>
<th>操作</th>
</tr>
</thead>
<tbody id="keysTable">
{% for k in keys %}
<tr data-key="{{k.key}}">
<td><span class="key-cell">{{k.key}}</span></td>
<td class="note-cell"><span class="note-text">{{k.note}}</span></td>
<td class="time-cell">{{k.s}}{% if not k.s %}<small>-</small>{% endif %}</td>
<td class="time-cell">{{k.e}}</td>
<td class="actions">
<button onclick="copyKey('{{k.key}}')" class="btn-copy">复制</button>
<button onclick="editKey('{{k.key}}')" class="btn btn-sm">编辑</button>
<button onclick="deleteKey('{{k.key}}')" class="btn btn-danger btn-sm">删除</button>
</td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty-state">
<div class="icon">🔑</div>
<p>No API keys found. Create one above!</p>
</div>
{% endif %}
</div>
</div>
<div id="toast" class="toast"></div>
<div id="editModal" class="modal">
<div class="modal-content">
<h3>编辑 API Key</h3>
<input type="hidden" id="editKeyInput">
<div class="form-group" style="margin-bottom:20px">
<label>备注</label>
<input type="text" id="editNote" placeholder="请输入备注">
</div>
<div class="form-group" style="margin-bottom:20px">
<label>开始时间</label>
<input type="datetime-local" id="editStartTime">
</div>
<div class="form-group" style="margin-bottom:20px">
<label>结束时间</label>
<input type="datetime-local" id="editEndTime">
</div>
<div class="btn-group">
<button onclick="closeModal()" class="btn btn-sm" style="background:#e2e8f0;color:#333">取消</button>
<button onclick="saveEdit()" class="btn">保存</button>
</div>
</div>
</div>
<div id="recycleModal" class="modal">
<div class="modal-content" style="max-width:700px">
<h3>回收站</h3>
<div id="recycleList" style="max-height:500px;overflow-y:auto;"></div>
<div class="btn-group" style="margin-top:20px;">
<button onclick="closeRecycle()" class="btn btn-sm" style="background:#e2e8f0;color:#333">关闭</button>
</div>
</div>
</div>
<div id="restoreModal" class="modal">
<div class="modal-content">
<h3>恢复 API Key</h3>
<input type="hidden" id="restoreKey">
<div class="form-group" style="margin-bottom:20px">
<label>备注</label>
<input type="text" id="restoreNote" readonly style="background:#f0f0f0">
</div>
<div class="form-group" style="margin-bottom:20px">
<label>开始时间</label>
<input type="datetime-local" id="restoreStart">
</div>
<div class="form-group" style="margin-bottom:20px">
<label>结束时间</label>
<input type="datetime-local" id="restoreEnd" required>
</div>
<div class="btn-group">
<button onclick="closeRestore()" class="btn btn-sm" style="background:#e2e8f0;color:#333">取消</button>
<button onclick="doRestore()" class="btn btn-success">恢复</button>
</div>
</div>
</div>
<div id="copyModal" class="modal">
<div class="modal-content">
<h3>复制 API Key</h3>
<input type="hidden" id="copyKeyInput">
<div class="copy-option" onclick="selectCopyOption(1)" id="copyOption1">
<h4>模板一：车队分享</h4>
<p>适用于车队分享，包含用量提醒说明</p>
<div class="copy-preview" id="copyPreview1"></div>
</div>
<div class="copy-option" onclick="selectCopyOption(2)" id="copyOption2">
<h4>模板二：通用</h4>
<p>适用于CC、CX、OC、Claw等agent工具</p>
<div class="copy-preview" id="copyPreview2"></div>
</div>
<div class="btn-group">
<button onclick="closeCopyModal()" class="btn btn-sm" style="background:#e2e8f0;color:#333">取消</button>
<button onclick="doCopy()" class="btn btn-success">复制到剪贴板</button>
</div>
</div>
</div>
<div style="display:none">
<div id="template1">key：__KEY__

Base：http://42.193.140.242:8317

发apikey和地址，可以直接使用，后台会记录每个人的apikey的tokens消耗，过量会进行提醒，多次提醒不改就踢出保证车队每个人用量均衡，其实用量应该都是足够的，加上我的话车队才4个人，我不咋使用，所以基本不太需要为用量担心。</div>
<div id="template2">key：__KEY__

Base：http://42.193.140.242:8317

使用apikey和地址可接入到cc，cx，oc，claw等agent工具中，不懂或者不会使用可咨询我，带协助（同时我还接安装龙虾，25一次，后期续费模型一直持续售后维护龙虾）。

模型列表：

kimi-k2
kimi-k2-thinking
kimi-k2.5
kimi-k2.6

商品售出后并且发货，如果有使用不允退款。
未使用退款退款一半（商品首页有说明）。</div>
</div>
<script>
var selectedCopyOption=1;
function show(m,type){
  var t=document.getElementById("toast");
  t.textContent=m;
  t.className="toast"+(type?" "+type:"");
  t.style.display="block";
  setTimeout(function(){t.style.display="none"},3500);
}
function quickSelect(val,unit){
  var btns=document.querySelectorAll('.quick-btn');
  btns.forEach(function(b){b.classList.remove('active')});
  event.target.classList.add('active');
  var now=new Date();
  var start=new Date(now);
  var end=new Date(now);
  if(unit==='h'){
    end.setHours(end.getHours()+parseInt(val));
  } else {
    end.setDate(end.getDate()+parseInt(val));
  }
  var fmt=function(d){
    return d.getFullYear()+'-'+
      String(d.getMonth()+1).padStart(2,'0')+'-'+
      String(d.getDate()).padStart(2,'0')+'T'+
      String(d.getHours()).padStart(2,'0')+':'+
      String(d.getMinutes()).padStart(2,'0');
  };
  document.getElementById('startTime').value=fmt(start);
  document.getElementById('endTime').value=fmt(end);
}
document.getElementById("createForm").onsubmit=function(e){
  e.preventDefault();
  var start=document.getElementById("startTime").value;
  var end=document.getElementById("endTime").value;
  var note=document.getElementById("noteInput").value;
  if(!end){show("请选择结束时间","error");return;}
  fetch("/api/keys",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({starts_at:start||null,expires_at:end,note:note})
  }).then(function(r){return r.json()}).then(function(j){
    if(j.success){
      show("API Key: "+j.key,"success");
      setTimeout(function(){location.reload()},2000);
    }else{show(j.error||"错误",true)}
  }).catch(function(err){show(err.message,true)});
};
function deleteKey(k){
  if(!confirm("确定删除此 API Key?"))return;
  fetch("/api/keys",{
    method:"DELETE",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key:k})
  }).then(function(r){return r.json()}).then(function(j){
    if(j.success){show("删除成功","success");setTimeout(function(){location.reload()},1000);}
    else{show(j.error||"错误",true)}
  }).catch(function(err){show(err.message,true)});
}
function editKey(k){
  var row=document.querySelector('tr[data-key="'+k+'"]');
  var cells=row.cells;
  document.getElementById("editKeyInput").value=k;
  document.getElementById("editNote").value=cells[1].textContent.trim()||"";
  document.getElementById("editStartTime").value=cells[2].textContent.split("\\n")[0].trim()||"";
  document.getElementById("editEndTime").value=cells[3].textContent.split("\\n")[0].trim()||"";
  document.getElementById("editModal").classList.add("show");
}
function closeModal(){
  document.getElementById("editModal").classList.remove("show");
}
function saveEdit(){
  var k=document.getElementById("editKeyInput").value;
  var note=document.getElementById("editNote").value;
  var start=document.getElementById("editStartTime").value;
  var end=document.getElementById("editEndTime").value;
  fetch("/api/keys/update",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key:k,starts_at:start||null,expires_at:end,note:note})
  }).then(function(r){return r.json()}).then(function(j){
    if(j.success){show("保存成功","success");closeModal();setTimeout(function(){location.reload()},1000);}
    else{show(j.error||"错误",true)}
  }).catch(function(err){show(err.message,true)});
}
function logout(){localStorage.removeItem("apikey_manager_pwd");localStorage.removeItem("apikey_manager_remember");window.location.href="/logout";}
function openRecycle(){
  fetch("/api/recycle").then(function(r){return r.json()}).then(function(j){
    var list=document.getElementById("recycleList");
    if(j.items.length===0){
      list.innerHTML='<div style="text-align:center;padding:40px;color:#999;">回收站为空</div>';
    } else {
      var html='<table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f5f6fa;"><th style="padding:10px;text-align:left;font-size:12px;">Key</th><th style="padding:10px;text-align:left;font-size:12px;">备注</th><th style="padding:10px;text-align:left;font-size:12px;">过期时间</th><th style="padding:10px;text-align:left;font-size:12px;">删除方式</th><th style="padding:10px;text-align:left;font-size:12px;">删除时间</th><th style="padding:10px;text-align:left;font-size:12px;">操作</th></tr></thead><tbody>';
      j.items.forEach(function(item,idx){
        var deletedBy=item.deleted_by==="expired"?"过期清理":"手动删除";
        var expiredTime=item.expires_at?item.expires_at.replace("T"," ").substring(0,19):"永不过期";
        var deletedTime=item.deleted_at?item.deleted_at.replace("T"," ").substring(0,19):"-";
        var note=item.note||"";
        var encodedNote=btoa(unescape(encodeURIComponent(note)));
        html+='<tr data-key="'+item.key+'" data-note="'+encodedNote+'"><td style="padding:10px;font-size:12px;word-break:break-all;max-width:150px;">'+item.key+'</td><td style="padding:10px;font-size:12px;">'+(note||'-')+'</td><td style="padding:10px;font-size:12px;">'+expiredTime+'</td><td style="padding:10px;font-size:12px;">'+deletedBy+'</td><td style="padding:10px;font-size:12px;">'+deletedTime+'</td><td style="padding:10px;"><button onclick="restoreFromRow(this)" class="btn btn-sm btn-success">恢复</button> <button onclick="permanentDeleteFromRow(this)" class="btn btn-sm btn-danger">彻底删除</button></td></tr>';
      });
      html+='</tbody></table>';
      list.innerHTML=html;
    }
    document.getElementById("recycleModal").classList.add("show");
  }).catch(function(err){show("加载失败","error")});
}
function closeRecycle(){
  document.getElementById("recycleModal").classList.remove("show");
}
function restoreFromRow(btn){
  var row=btn.closest("tr");
  var k=row.getAttribute("data-key");
  var note=decodeURIComponent(escape(atob(row.getAttribute("data-note")||"")));
  document.getElementById("restoreKey").value=k;
  document.getElementById("restoreNote").value=note;
  document.getElementById("restoreStart").value="";
  document.getElementById("restoreEnd").value="";
  document.getElementById("restoreModal").classList.add("show");
}
function permanentDeleteFromRow(btn){
  var row=btn.closest("tr");
  var k=row.getAttribute("data-key");
  if(!confirm("彻底删除后无法恢复，确定？"))return;
  fetch("/api/recycle/delete",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key:k})
  }).then(function(r){return r.json()}).then(function(j){
    if(j.success){show("已彻底删除","success");openRecycle();}
    else{show("删除失败",true)}
  }).catch(function(err){show(err.message,true)});
}
function closeRestore(){
  document.getElementById("restoreModal").classList.remove("show");
}
function doRestore(){
  var k=document.getElementById("restoreKey").value;
  var note=document.getElementById("restoreNote").value;
  var start=document.getElementById("restoreStart").value;
  var end=document.getElementById("restoreEnd").value;
  if(!end){show("请选择结束时间","error");return;}
  fetch("/api/recycle/restore",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key:k,starts_at:start||null,expires_at:end,note:note})
  }).then(function(r){return r.json()}).then(function(j){
    if(j.success){show("恢复成功","success");closeRestore();openRecycle();}
    else{show(j.error||"恢复失败",true)}
  }).catch(function(err){show(err.message,true)});
}
function permanentDelete(k){
  if(!confirm("彻底删除后无法恢复，确定？"))return;
  fetch("/api/recycle/delete",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({key:k})
  }).then(function(r){return r.json()}).then(function(j){
    if(j.success){show("已彻底删除","success");openRecycle();}
    else{show("删除失败",true)}
  }).catch(function(err){show(err.message,true)});
}
function filterTable(){
  var input=document.getElementById("searchInput").value.toLowerCase();
  var rows=document.getElementById("keysTable").rows;
  for(var i=0;i<rows.length;i++){
    var text=rows[i].textContent.toLowerCase();
    rows[i].style.display=text.indexOf(input)>-1?"":"none";
  }
}
document.getElementById("editModal").onclick=function(e){
  if(e.target===this)closeModal();
};
var currentKeyForCopy="";
function copyKey(k){
  currentKeyForCopy=k;
  selectedCopyOption=1;
  var opts=document.querySelectorAll('.copy-option');
  opts.forEach(function(o){o.classList.remove('selected')});
  document.getElementById('copyOption1').classList.add('selected');
  var t1=document.getElementById('template1').innerHTML.replace(/__KEY__/g,k);
  var t2=document.getElementById('template2').innerHTML.replace(/__KEY__/g,k);
  document.getElementById('copyPreview1').textContent=t1;
  document.getElementById('copyPreview2').textContent=t2;
  document.getElementById('copyModal').classList.add('show');
}
function selectCopyOption(opt){
  selectedCopyOption=opt;
  var opts=document.querySelectorAll('.copy-option');
  opts.forEach(function(o){o.classList.remove('selected')});
  document.getElementById('copyOption'+opt).classList.add('selected');
}
function doCopy(){
  var t=selectedCopyOption===1?document.getElementById('copyPreview1').textContent:document.getElementById('copyPreview2').textContent;
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(function(){
      show("已复制到剪贴板!","success");
      closeCopyModal();
    }).catch(function(err){
      fallbackCopy(t);
    });
  } else {
    fallbackCopy(t);
  }
}
function fallbackCopy(text){
  var textarea=document.createElement('textarea');
  textarea.value=text;
  textarea.style.position='fixed';
  textarea.style.left='-9999px';
  textarea.style.top='-9999px';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try{
    document.execCommand('copy');
    show("已复制到剪贴板!","success");
    closeCopyModal();
  } catch(err){
    show("复制失败，请手动复制","error");
  }
  document.body.removeChild(textarea);
}
function closeCopyModal(){
  document.getElementById("copyModal").classList.remove("show");
}
document.getElementById("copyModal").onclick=function(e){
  if(e.target===this)closeCopyModal();
};
document.getElementById("recycleModal").onclick=function(e){
  if(e.target===this)closeRecycle();
};
document.getElementById("restoreModal").onclick=function(e){
  if(e.target===this)closeRestore();
};
</script>
