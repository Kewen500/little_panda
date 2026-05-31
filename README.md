# API Balance Floating Widget

<p align="center">
  <img src="assets/api-balance-widget.png" alt="API Balance Floating Widget icon" width="128">
</p>

一个使用 PySide6 编写的 Windows 桌面悬浮挂件，用于查看 API 平台账户余额。
挂件内置 DeepSeek 和 Kimi / Moonshot，也支持添加其他返回 JSON 余额接口的平台。API Key 使用 Windows DPAPI 加密后保存在本机，不会上传到 Git。

## 功能

- 查询余额、币种、可用状态和更新时间
- 内置 DeepSeek 与 Kimi / Moonshot
- 支持添加其他返回 JSON 的余额接口
- 支持 `Authorization: Bearer <token>` 形式的鉴权
- 支持平台切换、手动刷新和定时刷新
- 支持切换深色背景
- 支持设置窗口是否置顶
- 使用熊猫动画提示余额状态
- 接口暂时不可用时回退显示最近一次本地缓存

## 安装

需要 Python 3.10 或更高版本。

```powershell
git clone <your-repository-url>
cd api-usage-floating-widget
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

## 内置平台

| 平台 | 默认 URL | 余额接口 |
| --- | --- | --- |
| DeepSeek | `https://api.deepseek.com` | `GET /user/balance` |
| Kimi / Moonshot | `https://api.moonshot.cn` | `GET /v1/users/me/balance` |

内置平台使用：

```text
Authorization: Bearer <API_KEY>
```

## 配置账户

展开挂件后点击顶部的 `账户`：

1. 选择内置平台，或点击 `新增`。
2. 填写平台名称、URL 和余额接口。
3. 填写 API Key，或从网页请求里复制出来的 Bearer token。
4. 填写余额 JSON 对应的字段路径。
5. 点击 `保存`。

API Key 加密保存在 `.cache/accounts.json`。`.cache/` 已加入 `.gitignore`。

## 自定义平台

如果接口返回：

```json
{
  "data": {
    "account": {
      "balance": 12.5,
      "currency": "CNY",
      "available": true
    }
  }
}
```

填写：

```text
余额字段路径: data.account.balance
币种字段路径: data.account.currency
默认币种: CNY
可用状态路径: data.account.available
```

字段路径使用英文句点分隔。不同平台的 JSON 结构不同，需要根据浏览器 Network 中的响应内容填写。

## 从网页请求里找配置

有些网站没有公开 API Key 页面，但网页本身会调用余额、钱包、额度或用户信息接口。这种情况下可以从浏览器开发者工具里找到 URL、余额接口和 Bearer token。

1. 在 Chrome 或 Edge 里登录目标网站。
2. 按 `F12` 打开开发者工具。
3. 进入 `Network / 网络`。
4. 点击 `Fetch/XHR`，然后刷新网页。
5. 找看起来像用户信息、余额、钱包、额度的请求，例如 `me`、`user`、`balance`、`wallet`、`quota`。
6. 点开请求，在 `Headers / 标头` 里查看 `Request URL`。
7. 把域名部分填到 `URL`，例如 `https://example.com`。
8. 把路径和查询参数填到 `余额接口`，例如 `api/v1/account/me`。
9. 在 `Request Headers / 请求标头` 里找到 `authorization`。
10. 如果值是 `Bearer <TOKEN>`，把 `Bearer ` 后面的整段内容填到 `API Key`，不要包含 `Bearer` 这个单词。
11. `鉴权请求头` 填 `Authorization`，`鉴权前缀` 填 `Bearer`。
12. 切到 `Response / 响应`，根据 JSON 结构填写余额字段路径、币种字段路径和可用状态路径。

注意：网页请求里的 `cookie` 不一定是登录凭据。有些网站真正的登录凭据在 `authorization: Bearer ...` 里。本工具已经取消 Cookie 登录方式，只支持 API Key / Bearer token。

### 通用示例

如果浏览器里看到：

```text
Request URL: https://example.com/api/v1/account/me
authorization: Bearer <TOKEN>
```

填写：

```text
平台名称: Example
URL: https://example.com
余额接口: api/v1/account/me
API Key: <TOKEN> 这一整段，不包含 Bearer
余额字段路径: data.account.balance
币种字段路径: data.account.currency
默认币种: CNY
可用状态路径: data.account.available
鉴权请求头: Authorization
鉴权前缀: Bearer
```

如果响应 JSON 结构不同，请以 `Response / 响应` 里的实际字段为准。

## 上传前检查

- 不要上传 `.cache/accounts.json`。
- 不要把 API Key、Bearer token、Cookie、真实网站接口或个人配置写入代码、README 或截图。
- `.env`、`.venv/`、`.cache/`、`config/providers.json` 和 Python 缓存目录已加入 `.gitignore`。

## 测试

测试不会调用在线接口：

```powershell
python -m unittest discover -v
```
