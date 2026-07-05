# AI 态势日报

一个批处理式 AI Landscape Daily 生成器：采集 RSS、GitHub Trending、arXiv 信号，写入 SQLite，生成 `态势总览`、`主题洞察`、`渠道热榜` 静态页面，并可选发送包含快照与链接的日报邮件。

## 本地运行

```bash
# conda 方式
conda create -n ai-landscape-daily python=3.11 -y
conda activate ai-landscape-daily
pip install -e . -r requirements-dev.txt
python -m playwright install chromium
cp .env.example .env
python -m ai_landscape_daily generate --date today --mock
```

或使用 venv：

```bash
python -m venv .venv
source .venv/bin/activate
python --version  # 建议 Python 3.9+
pip install -r requirements-dev.txt
python -m playwright install chromium
cp .env.example .env
python -m ai_landscape_daily generate --date today --mock
```

生成结果：

- SQLite：`data/ai_daily.sqlite3`
- 静态站点：`site/daily/<date>/index.html`
- 主题页：`site/daily/<date>/topics/*.html`
- 渠道页：`site/daily/<date>/channels/*.html`
- 快照：`site/daily/<date>/assets/snapshot.png`

如果只需要生成文件，不发送邮件，省略 `--send` 即可。`--mock` 使用确定性样例数据，适合本地验证和 CI 冒烟测试。

## 常用命令

```bash
python -m ai_landscape_daily generate --date 2026-06-28 --output-dir site
python -m ai_landscape_daily generate --date today --mock --db data/ai_daily.sqlite3
python -m ai_landscape_daily generate --date today --send
pytest
```

## 配置

- `config/sources.yaml`：RSS feed、arXiv 类别、GitHub Trending、渠道名称。
- `config/scoring.yaml`：热度公式权重、渠道权重、主题别名。
- `.env`：本地环境变量，参考 `.env.example`。

热度公式由以下可解释分数组成：

```text
source_weight * 0.25
+ cross_source_score * 0.20
+ frequency_score * 0.15
+ freshness_score * 0.15
+ momentum_score * 0.15
+ community_score * 0.10
```

## 邮件与密钥

使用 `--send` 时必须配置：

- `EMAIL_TO`
- `EMAIL_FROM`
- `RESEND_API_KEY`，或 SMTP 组合：`SMTP_HOST`、`SMTP_USERNAME`、`SMTP_PASSWORD`

可选：

- `REPORT_BASE_URL`：邮件中的 Web 报告链接基地址。
- `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`：可选 OpenAI-compatible 模型配置。任意实现 `/v1/chat/completions` 协议的模型服务都可以使用；三项必须一起配置。

缺少邮件密钥时，仅在使用 `--send` 时抛出清晰配置错误；不发送邮件的生成流程不依赖这些密钥。

163 邮箱 SMTP 示例：

```env
EMAIL_FROM=your_name@163.com
EMAIL_TO=yswu103@163.com,zhang_run_han@163.com
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=your_name@163.com
SMTP_PASSWORD=你的 163 SMTP 授权码
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

## GitHub Actions 和 Pages

工作流位于 `.github/workflows/daily.yml`，支持：

- 每日定时运行：北京时间 09:07，定时任务会默认发送邮件。
- `workflow_dispatch` 手动运行，可传入 `report_date` 和 `send_email`。
- 安装依赖和 Playwright Chromium。
- 运行日报生成命令。
- 推送 `site/` 内容到 `gh-pages` 分支作为 GitHub Pages 站点。
- 上传 SQLite 数据库为 workflow artifact。

仓库设置中建议配置：

- Repository variables：`REPORT_BASE_URL`
- Repository secrets：`EMAIL_TO`、`EMAIL_FROM`、`RESEND_API_KEY` 或 SMTP secrets、可选 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`

启用 GitHub Pages 时，选择 `gh-pages` 分支根目录作为 Pages 来源。

## 静态托管

`site/` 内所有页面使用相对链接，复制到 GitHub Pages、Cloudflare Pages、Netlify 或任意静态文件服务器后即可访问，不需要 Python 或 Node 后端。

## 验证

```bash
pytest
python -m ai_landscape_daily generate --date 2026-06-28 --mock
test -f site/daily/2026-06-28/index.html
test -f site/daily/2026-06-28/assets/snapshot.png
```

OpenSpec 覆盖关系：

- 数据采集与评分：collectors、normalize、storage、pipeline。
- 静态报告：report templates、CSS、相对链接和 `report-data.json`。
- 邮件快照与部署：snapshot、email delivery、GitHub Actions、README secrets 文档。
