# Railway 部署指南

本仓库已经包含 Railway 部署所需的全部配置:

- `Dockerfile` — 用 uv 安装依赖,以 streamable-http 模式启动,监听 Railway 的 `$PORT`
- `railway.json` — 告诉 Railway 用 Dockerfile 构建,失败自动重启

## 一次性部署步骤(约 10 分钟)

### 1. 登录 Railway

访问 https://railway.com,用 GitHub 登录(首次需手机验证,送 $5/月免费额度)。

### 2. 创建项目

- 点击 **+ New Project** → **Deploy from GitHub repo**
- 选择本仓库 `excel-mcp-server`
- 点 **Deploy** — Railway 会自动用 Dockerfile 构建

### 3. 添加 Volume(必做!否则文件丢)

项目页面 → **Settings** → **Volumes** → **+ New Volume**

- Mount Path: `/data`
- Size: `1 GB`

### 4. 暴露公网域名

**Settings** → **Networking** → **Generate Domain**

得到形如 `https://excel-mcp-server-production-xxxx.up.railway.app` 的 URL。

### 5. 验证

查看 **Deployments → Logs**,看到类似 `Uvicorn running on http://0.0.0.0:XXXX` 即成功。

MCP 端点路径:`https://your-domain.up.railway.app/mcp`

## 可选环境变量(Variables 标签)

| Variable | 默认值 | 说明 |
|---|---|---|
| `EXCEL_FILES_PATH` | `/data` | Excel 文件目录(对应 Volume Mount Path) |
| `FASTMCP_HOST` | `0.0.0.0` | 监听地址(Dockerfile 已写死) |

> `FASTMCP_PORT` 由 Dockerfile 在启动时从 Railway 注入的 `$PORT` 自动设置,不需要手动配。

## 上传 Excel 到 /data

本 MCP server 没有内置上传 API。三种方式:

### 方式 A · 仓库携带(最简)

在仓库根目录建 `excel_files/`,把 .xlsx 放进去,改 Dockerfile CMD:

```dockerfile
CMD sh -c "cp -rn /app/excel_files/* /data/ 2>/dev/null; FASTMCP_PORT=${PORT:-8000} uv run excel-mcp-server streamable-http"
```

每次更新 Excel → push → Railway 自动重新部署 → 文件同步到 /data。

### 方式 B · Railway CLI 直传

```bash
npm i -g @railway/cli
railway login
railway link    # 选择项目
railway shell   # 进入容器查看 /data
```

## 接入 Notion

1. Notion **Settings → Connections → Add connection → Add custom MCP server**
2. 填写:
   - Name: `Excel MCP`
   - URL: `https://your-domain.up.railway.app/mcp`
   - Auth: None(本服务暂未启用鉴权)
3. 完成后告诉你的 Notion AI agent,把这个 MCP 加到 integrations。

## 安全提醒

本 MCP server **没有内置鉴权**。任何拿到 URL 的人都能访问。生产环境建议:
- 不公开 URL
- 在 Railway 前面套 Cloudflare 反代加 Bearer Token 校验
