# GEE 认证与 key 管理

## 认证方式(已验证可用)

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

## 内置 key(2 个, 用户 intake 选)

| key | project | 适用 |
|---|---|---|
| feisty-gateway-498706-m2-1b9cc04e520c.json | feisty-gateway-498706 | 默认 |
| zeta-turbine-498806-j3-e99120f8bd27.json | zeta-turbine-498806 | 备用/轮换 |

默认路径 `C:/Users/19161/Desktop/长征/`。两个都失效则需自注册。

## key 失效/配额耗尽 → 自注册步骤

1. **注册 Earth Engine**: 浏览器开 https://code.earthengine.google.com/ , 用 Google 账号登录,
   按提示选/注册一个 Cloud Project(免费), 等待"Earth Engine 已启用"(通常秒开)。
2. **创建 service account**: 进 https://console.cloud.google.com/ → 选刚注册的 project →
   IAM 与管理 → Service Accounts → 创建服务账号 → 角色 `Earth Engine Resource Viewer`(或 Editor)。
3. **下载 JSON key**: 服务账号详情 → 密钥 → 添加密钥 → JSON → 下载 `.json` 文件, 存到本地
   (如 `Desktop/长征/your-project-xxxx.json`)。
4. **填到 config**: `gee.key_file: "C:/path/to/your-key.json"`。
5. **测连通**: `python -m src.gee_auth` 应显示 `GEE 已连接: account=...`。

## 代理(国内必须)

GEE 是 Google 服务, 国内直连 `oauth2.googleapis.com` 会超时。需开代理:
- **Cloudflare WARP**: `warp-cli connect` (不用向日葵远程时可一直开)
- **Clash/v2ray**: 规则模式, google 走代理
- 用向日葵远程时: 用 `run_with_warp.py` 跑 GEE 前自动开 WARP、跑完关(保向日葵)

## 安全

key 的 private_key 是账号钥匙, **绝不进 git/截图/发群**。`.gitignore` 已排除 `*.json`/`*credentials*`。
内置 key 公开在 skill 是用户授权选择, 他人复用请自注册。
