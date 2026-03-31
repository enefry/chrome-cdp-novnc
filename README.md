# chrome-cdp-novnc

一个基于 Docker 的 Chrome 容器，内置：

- Chrome / Chromium
- Chrome DevTools Protocol（CDP）
- noVNC Web 访问
- Xvfb + fluxbox 桌面环境
- `linux/amd64` 和 `linux/arm64` 多架构镜像发布能力

这个项目的目标是提供一套可直接复用的“带界面的 Chrome + CDP”运行环境。

## 安全说明

这个镜像默认不提供安全防护，必须由外部环境自行做访问控制。

默认情况下，这个镜像不包含：

- 登录认证
- noVNC 访问密码
- CDP 接口鉴权
- HTTPS / TLS
- 细粒度权限控制

这意味着只要网络能访问到暴露端口，就可能直接控制浏览器和查看浏览器画面。

因此不建议直接暴露到公网。正确做法是由外部基础设施自行保护，例如：

- 反向代理鉴权
- VPN / 内网访问
- 防火墙白名单
- Zero Trust 访问控制
- HTTPS 终止和证书管理

如果你要在生产环境使用，必须把安全措施放在这个镜像外面做。

## 许可证说明

本仓库使用 `Apache-2.0`，见 [LICENSE](/media/data/service/chrome-cdp/LICENSE)。

补充说明见 [NOTICE](/media/data/service/chrome-cdp/NOTICE)。

需要特别说明的是：

- `Apache-2.0` 只覆盖本仓库中自有的代码、脚本、配置和文档
- 容器镜像中安装的第三方软件仍分别受其各自许可证约束
- 这些第三方组件不会因为本仓库使用 `Apache-2.0` 而自动变成 `Apache-2.0`

尤其在发布镜像时，应自行确认第三方组件的许可证、再分发条款和商标限制是否满足你的使用场景。

## 功能

- 通过 noVNC 在浏览器里直接查看和操作 Chrome
- 通过 CDP 从本地程序控制浏览器
- 访问 `http://<host>:<port>/` 时自动跳转到 noVNC 页面并自动连接
- 默认关闭 fluxbox 底部 toolbar，避免遮挡 Chrome 可视区域
- 支持本地测试脚本和 GitHub Actions 自动发布镜像

## 目录结构

```text
.
├── bin/                  # 容器内可执行包装脚本
├── config/               # supervisor 和 fluxbox 配置
├── scripts/              # 容器启动和运行时辅助脚本
├── test/                 # CDP / noVNC 测试与示例脚本
├── Dockerfile
├── docker-compose.yml
└── cdp_client.py         # 测试脚本共享的 CDP 客户端
```

## 本地运行

注意：以下运行方式默认只适合本地开发、受控内网或已经有外围安全措施的环境。

### 使用 docker compose

```bash
docker compose up -d --build
```

默认端口：

- noVNC: `http://127.0.0.1:9600`
- CDP Proxy: `http://127.0.0.1:9601`

这些端口本身默认没有认证。

默认卷：

- Chrome 用户数据目录挂载到 `./data/chrome`

### 访问 noVNC

直接打开：

```text
http://127.0.0.1:9600/
```

根路径会自动跳转到：

```text
/vnc.html?autoconnect=1&resize=remote&path=websockify
```

也就是开箱即用，不需要再手动点 `vnc.html` 或手动连接。

## CDP 连接方式

### Browser-level endpoint

```text
http://127.0.0.1:9601/json/version
```

返回结果里会包含：

- `webSocketDebuggerUrl`

例如：

```text
ws://127.0.0.1:9601/devtools/browser/<id>
```

### Page-level endpoint

先查询：

```text
http://127.0.0.1:9601/json/list
```

每个页面 target 都会返回：

- `id`
- `title`
- `url`
- `webSocketDebuggerUrl`

## 测试与示例脚本

### 1. 基础验证

```bash
python3 test/verify_cdp.py
```

支持参数：

```bash
python3 test/verify_cdp.py --new-page --url https://example.com
python3 test/verify_cdp.py --eval 'document.title'
python3 test/verify_cdp.py --screenshot /tmp/page.png
python3 test/verify_cdp.py --eval 'location.href' --screenshot /tmp/page.png
```

### 2. 整体环境验证

```bash
python3 test/test_all.py
```

这个脚本会一次性检查：

- noVNC HTTP
- CDP `json/version`
- CDP browser websocket
- target 列表
- 打开页面
- 执行 JavaScript
- 截图保存

### 3. 单项示例

```bash
python3 test/new_page.py https://example.com
python3 test/eval_js.py 'document.title'
python3 test/screenshot.py https://example.com /tmp/example.png
```

## noVNC 根路径模板化参数

镜像默认在启动时生成 noVNC 根首页，因此在别的环境直接运行同一张 image 也会自动获得这个效果。

可通过环境变量覆盖：

- `NOVNC_START_PAGE`
- `NOVNC_AUTOCONNECT`
- `NOVNC_RESIZE`
- `NOVNC_PATH`

默认值：

```text
NOVNC_START_PAGE=vnc.html
NOVNC_AUTOCONNECT=1
NOVNC_RESIZE=remote
NOVNC_PATH=websockify
```

例如：

```bash
docker run -e NOVNC_START_PAGE=vnc_lite.html -e NOVNC_RESIZE=scale ...
```

## 常用环境变量

- `SCREEN_WIDTH`
- `SCREEN_HEIGHT`
- `CHROME_BIN`
- `XDG_RUNTIME_DIR`
- `NOVNC_START_PAGE`
- `NOVNC_AUTOCONNECT`
- `NOVNC_RESIZE`
- `NOVNC_PATH`

`docker-compose.yml` 默认配置：

```yaml
environment:
  - SCREEN_WIDTH=1280
  - SCREEN_HEIGHT=840
```

## 镜像发布

### GitHub Actions 自动发布

工作流文件：

[`/.github/workflows/publish-image.yml`](./.github/workflows/publish-image.yml)

默认发布到：

```text
ghcr.io/<github-owner>/chrome-cdp-novnc
```

触发条件：

- push 到 `main`
- 手动执行 `workflow_dispatch`

发布标签：

- UTC 时间戳，格式 `YYYYMMDD-HHMMSS`
- `latest`
- 短 SHA

发布平台：

- `linux/amd64`
- `linux/arm64`

### 本地手动发布

```bash
./scripts/push_multiarch.sh ghcr.io/<owner>/chrome-cdp-novnc
```

会推送：

- `ghcr.io/<owner>/chrome-cdp-novnc:<UTC timestamp>`
- `ghcr.io/<owner>/chrome-cdp-novnc:latest`

## 镜像构建

### 本地构建

```bash
docker build -t chrome-cdp-novnc .
```

### 本地多架构构建并推送

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/<owner>/chrome-cdp-novnc:latest \
  --push \
  .
```

## 故障排查

### noVNC 打开后只是目录列表

正常情况下不会出现。如果出现，通常说明运行的还是旧镜像或旧容器。重建并重启：

```bash
docker compose up -d --build
```

### Chrome 画面显示不全

本项目已经默认关闭 fluxbox toolbar，并对 Chromium / Chrome 设置无边框最大化。如果仍有异常，先强刷 noVNC 页面。

### CDP 能访问 `json/version`，但脚本偶发失败

优先使用 `webSocketDebuggerUrl` 直接建立 websocket 连接，不要只依赖 HTTP 探测结果。

## 生产使用提醒

这个镜像本身是浏览器运行环境，不是安全网关。

如果你要对外提供服务，建议至少在镜像外层补这些能力：

- 入口认证
- HTTPS
- 来源 IP 限制
- 日志审计
- 资源隔离
- 会话清理策略
