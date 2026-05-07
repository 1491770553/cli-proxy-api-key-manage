# CLI Proxy API Key Manager

API Key 管理系统，用于管理 CLI Proxy API 的访问凭证。

## 功能特性

- 创建带过期时间的 API Key
- 快捷时间选择（1小时、6小时、12小时、1天、7天、30天、90天、1年、永不过期）
- 编辑和删除 API Key
- 回收站（恢复或永久删除）
- 复制功能（支持多种分享模板）
- 密码保护 + 记住密码
- 响应式设计（PC 和移动端适配）
- 粒子动画背景

## 项目结构

```
cli-proxy-api-key-manage/
├── manager.py          # 主程序（Flask 应用）
├── config.yaml         # 配置文件
├── recycle.json        # 回收站数据
├── templates/
│   ├── login.html      # 登录页面
│   └── index.html     # 主页面
└── README.md
```

## 底层架构

### 技术栈

- **后端**：Python Flask
- **前端**：原生 HTML/CSS/JavaScript（无框架依赖）
- **存储**：YAML 配置文件 + JSON 回收站
- **认证**：Session-based 会话管理

### 核心数据模型

```python
# API Key 数据结构
{
    "key": "sk-xxxxx",           # API Key 标识符
    "note": "备注信息",           # 用户备注
    "created_at": "2026-05-07T10:00:00",  # 创建时间
    "expires_at": "2026-06-07T10:00:00",  # 过期时间（None=永不过期）
    "starts_at": "2026-05-07T10:00:00"     # 生效时间（None=立即生效）
}

# 回收站数据结构
{
    "key": "sk-xxxxx",
    "note": "备注信息",
    "expires_at": "2026-06-07T10:00:00",
    "deleted_at": "2026-05-07T12:00:00",   # 删除时间
    "deleted_by": "expired" | "manual"      # 删除方式
}
```

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页面 |
| GET | `/login` | 登录页面 |
| POST | `/login` | 登录认证 |
| GET | `/logout` | 登出 |
| GET | `/api/keys` | 获取所有有效 Keys |
| POST | `/api/keys` | 创建新 Key |
| PUT | `/api/keys` | 更新 Key 信息 |
| DELETE | `/api/keys` | 删除 Key（移入回收站） |
| GET | `/api/recycle` | 获取回收站列表 |
| POST | `/api/recycle/restore` | 恢复 Key |
| POST | `/api/recycle/permanent` | 永久删除 |

### 请求/响应示例

**创建 API Key**
```json
// POST /api/keys
// Request:
{
    "note": "测试 Key",
    "starts_at": "2026-05-07T10:00:00",
    "expires_at": "2026-06-07T10:00:00"
}

// Response:
{
    "success": true,
    "key": "sk-xxxxx"
}
```

**删除 API Key（移入回收站）**
```json
// DELETE /api/keys
// Request:
{
    "key": "sk-xxxxx"
}

// Response:
{
    "success": true
}
```

## 工作流程

### 1. 认证流程

```
用户访问 → 检查 Session → 未登录重定向到 /login
                              ↓
                        输入密码提交
                              ↓
                        密码正确 → 设置 Session → 重定向到 /
                        密码错误 → 返回错误提示
```

**记住密码实现**：使用 localStorage 存储密码，登录时自动填充并提交。

### 2. Key 创建流程

```
填写表单（备注、开始时间、结束时间）
          ↓
    提交到 /api/keys
          ↓
    生成唯一 Key 标识符
          ↓
    保存到 config.yaml
          ↓
    返回成功响应 + 刷新页面
```

### 3. 自动清理机制

```
后台线程每 5 分钟执行一次
          ↓
    读取 config.yaml 中的所有 Keys
          ↓
    检查过期状态（expires_at < 当前时间）
          ↓
    将过期 Key 移入 recycle.json
          ↓
    更新 config.yaml（移除过期 Key）
```

### 4. 删除与恢复流程

```
删除 Key → 移入回收站（recycle.json）
          ↓
    恢复 → 从回收站取出 → 重新写入 config.yaml
          ↓
    永久删除 → 直接从回收站清除
```

## 页面渲染逻辑

### 登录页面（login.html）

- 背景：Canvas 粒子动画
- 表单：密码输入 + 记住密码复选框
- localStorage 存储密码实现自动填充

### 主页面（index.html）

**头部区域**
- 标题 + 退出按钮
- 统计数据（总数、已过期数）

**创建表单**
- 快捷时间按钮组（1h、1d、7d 等）
- 开始时间输入（可选，默认为当前时间）
- 结束时间输入（必填）
- 备注输入框
- 生成按钮

**Key 列表**
- 卡片式布局（响应式网格）
- 每张卡片显示：备注、Key 值、开始/结束时间
- 操作按钮：复制、编辑、删除

**复制功能**
- 样式1（简洁）：`key：xxx\n\nBase：http://...`
- 样式2（完整）：包含使用说明、模型列表、售后条款

**编辑弹窗**
- 填写新备注、开始/结束时间
- 保存后更新 config.yaml

**回收站弹窗**
- 表格显示所有已删除 Key
- 可恢复或永久删除

## 配置说明

```yaml
port: 18317                    # 服务端口
password: wlie0726            # 登录密码
cleanup_interval: 300         # 自动清理间隔（秒，默认5分钟）
keys:                         # API Keys 列表
  - key: sk-xxxxx
    note: 测试
    created_at: 2026-05-07T10:00:00
    expires_at: 2026-06-07T10:00:00
```

## 安装部署

### 环境要求

- Python 3.6+
- pip

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/1491770553/cli-proxy-api-key-manage.git
cd cli-proxy-api-key-manage

# 安装依赖
pip install flask flask-cors pyyaml

# 启动服务
python manager.py

# 或使用 systemd 服务（可选）
cp apikey-manager.service /etc/systemd/system/
systemctl enable apikey-manager
systemctl start apikey-manager
```

### 服务管理

```bash
# 启动
systemctl start apikey-manager

# 停止
systemctl stop apikey-manager

# 重启
systemctl restart apikey-manager

# 查看状态
systemctl status apikey-manager

# 查看日志
journalctl -u apikey-manager -f
```

## 访问地址

启动后访问：`http://服务器IP:18317`

默认密码：`wlie0726`
