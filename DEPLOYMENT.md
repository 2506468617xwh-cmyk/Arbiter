# RAbot 部署文档

## 部署架构

```
用户浏览器 → Vercel / Cloudflare Pages（前端 React）
                 ↓
          Render / Railway（后端 FastAPI）
                 ↓
          持久化存储（SQLite / 文件系统）
```

- 前端：Vercel 或 Cloudflare Pages，托管 React 构建产物
- 后端：Render 或 Railway，运行 FastAPI + Uvicorn
- 数据：SQLite 文件和报告存入 `RABOT_DATA_DIR` 目录

---

## 一、GitHub 准备

1. 确保 .env 不被上传到仓库。检查 .gitignore 包含：

```
.env
.env.*
!.env.example
frontend/.env
frontend/.env.*
!frontend/.env.example
```

2. 可以上传 .env.example，里面只有空值占位，没有真实 API key。
3. 确认没有真实 key 泄露到仓库历史。

---

## 二、Render 后端部署

### 步骤

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New +** → **Web Service**
3. 连接 GitHub 仓库，选择 rabot 项目
4. 填写配置：

| 配置项 | 值 |
|--------|-----|
| Name | rabot-api |
| Region | 选择离你最近 |
| Branch | main |
| Root Directory | （留空，项目根目录） |
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Plan | Free 或 Starter |
| Health Check Path | `/health` |

5. 添加环境变量（参考下方列表）
6. 点击 **Create Web Service**
7. 等待部署完成，记录服务域名 `https://rabot-api.onrender.com`

### 必填环境变量

```env
APP_ENV=production
FRONTEND_ORIGINS=https://你的前端域名
RABOT_DATA_DIR=data
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

### 可选环境变量

```env
TUSHARE_TOKEN=你的Tushare密钥
LONGBRIDGE_APP_KEY=你的Longbridge密钥
LONGBRIDGE_APP_SECRET=你的Longbridge密钥
LONGBRIDGE_ACCESS_TOKEN=你的Longbridge令牌
FINNHUB_API_KEY=你的Finnhub密钥
NEWSAPI_KEY=你的NewsAPI密钥
ALPHAVANTAGE_API_KEY=你的Alpha Vantage密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
RABOT_AUTO_UPDATE_ON_START=true
```

### 注意

- Render 免费实例在无流量时会休眠，首次请求可能延迟约 30 秒。
- SQLite 数据存在临时文件系统，重启后丢失。如需持久化，建议升级付费计划并挂载 **Persistent Disk**（Render 付费特性）。
- 如果部署 Railway，步骤类似：连接仓库 → 设置 Start Command → 添加环境变量。

---

## 三、Vercel 前端部署

### 步骤

1. 登录 [Vercel Dashboard](https://vercel.com)
2. 点击 **Add New** → **Project**
3. 导入 rabot GitHub 仓库
4. 填写配置：

| 配置项 | 值 |
|--------|-----|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

5. 添加环境变量：

```
VITE_API_BASE_URL=https://你的后端域名（如 https://rabot-api.onrender.com）
```

6. 点击 **Deploy**
7. 部署完成后，打开 Vercel 域名验证

### 如果使用 Cloudflare Pages

1. 登录 Cloudflare Dashboard → **Workers & Pages** → **Pages**
2. 连接 GitHub 仓库
3. 构建设置：
   - Framework: Vite
   - Build command: `npm run build`
   - Build output: `dist`
   - Root directory: `frontend`
4. 环境变量：
   - `VITE_API_BASE_URL=https://你的后端域名`
5. 点击部署

---

## 四、部署后检查清单

- [ ] 后端 Health Check：访问 `https://你的后端域名/health`
  ```json
  {
    "status": "ok",
    "app": "RAbot API",
    "version": "0.1.0",
    "environment": "production",
    "data_dir_exists": true,
    "reports_dir_exists": true
  }
  ```
- [ ] 前端页面：打开 Vercel 域名，确认页面正常加载
- [ ] API 通信：打开浏览器控制台，确认网络请求的目标是线上后端（不是 localhost）
- [ ] CORS：检查是否有跨域报错
- [ ] API key：确认 /health 响应中没有暴露任何密钥

---

## 五、本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 准备 .env（从 .env.example 复制）
cp .env.example .env
# 编辑 .env 填入真实 API key

# 3. 启动后端
cd frontend && npm install && npm run dev &
cd ..
PYTHONPATH=src uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

前端开发模式（Vite dev server）会自动代理 `/api` 到后端。

---

## 六、常见错误排查

| 问题 | 原因 | 解决 |
|------|------|------|
| CORS 报错 | FRONTEND_ORIGINS 未配置或配置错误 | 检查 Render 环境变量 `FRONTEND_ORIGINS` |
| API 请求仍是 localhost | VITE_API_BASE_URL 未设置或未生效 | 检查 Vercel 环境变量，重新部署 |
| 后端启动失败 | PYTHONPATH 未设置或依赖缺失 | 检查 Build/Start Command |
| 数据为空 | 免费平台临时文件系统重启后数据丢失 | 使用 Persistent Disk 或 PostgreSQL |
| API key 无效 | 环境变量名拼写错误或值不对 | 检查 Render 环境变量面板 |
| 前端白屏 | Build 失败或接口地址不对 | 查看 Vercel 部署日志和浏览器 Console |
| 报告无法保存 | 目录权限不足或 RABOT_DATA_DIR 配置不对 | 检查 RABOT_DATA_DIR 值 |

---

## 七、安全提醒

- 不要将 `.env` 文件提交到 GitHub
- 不要在代码或接口响应中暴露 API key
- `VITE_API_BASE_URL` 只写 URL 地址，不包含任何密钥
- 如果仓库是公开的，务必确认 `.gitignore` 正确配置，且 git 历史中没有 key
- 定期轮换 API key
