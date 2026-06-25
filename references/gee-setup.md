# GEE 认证与 key 管理

## 认证方式

service account key + `ee.Initialize(credentials)` **不传 project**(传 project 会触发
"project not found")。代码 `src/gee_auth.py` 已实现:

```python
import json, os, ee
info = json.load(open(key_file, encoding="utf-8"))
email = info["client_email"]
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
creds = ee.ServiceAccountCredentials(email, key_file)
ee.Initialize(creds)  # 不传 project, 用 SA 默认 project
```

只读 `client_email`(账号邮箱, 非密钥); private_key 永远留在文件里, 不读出、不打印、不进 git。

## key 来源

使用用户本机的 Google Cloud service-account JSON。不要在公开 skill、GitHub、报告或截图中写入真实 key 文件名、private_key 或固定本机路径。

config 中只保留本机路径:

```yaml
gee:
  key_file: "C:/path/to/your-service-account.json"
```

没有 key 时按下方步骤自注册。

## key 失效/配额耗尽 → 自注册步骤

1. **注册 Earth Engine**: 浏览器开 https://code.earthengine.google.com/ , 用 Google 账号登录,
   按提示选/注册一个 Cloud Project(免费), 等待"Earth Engine 已启用"(通常秒开)。
2. **创建 service account**: 进 https://console.cloud.google.com/ → 选刚注册的 project →
   IAM 与管理 → Service Accounts → 创建服务账号 → 角色 `Earth Engine Resource Viewer`(或 Editor)。
3. **下载 JSON key**: 服务账号详情 → 密钥 → 添加密钥 → JSON → 下载 `.json` 文件, 存到本地
   (如 `C:/path/to/your-project-xxxx.json`)。
4. **填到 config**: `gee.key_file: "C:/path/to/your-key.json"`。
5. **测连通**: `python -m src.gee_auth -c config.yaml` 应显示 `GEE 已连接: account=...`。

## 代理(国内必须)

GEE 是 Google 服务, 国内直连 `oauth2.googleapis.com` 会超时。需开代理:
- **Cloudflare WARP**: `warp-cli connect` (不用向日葵远程时可一直开)
- **Clash/v2ray**: 规则模式, google 走代理
- 用向日葵远程时: 用 `run_with_warp.py` 跑 GEE 前自动开 WARP、跑完关(保向日葵)

## 安全

key 的 private_key 是账号钥匙, **绝不进 git/截图/发群**。`.gitignore` 已排除 `*.json`/`*credentials*`。
多人复用本 skill 时, 每个人使用自己的 service account。
