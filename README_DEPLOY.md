# 部署到 Render / Railway / PythonAnywhere 的快速指南

下面给出把你的仓库自动部署到 Render、Railway、PythonAnywhere 的步骤（适合短期公开访问/多人查看）。这些平台都有免费层，适合中期公开展示。部署前请把仓库推到 GitHub。

公共前提
- 在仓库根目录有 `app.py`（Flask app），`requirements.txt`，以及 `Procfile`（针对 Render/Railway）。
- 确保 `requirements.txt` 列出 `Flask` 和 `gunicorn`（我已添加）。

Render（推荐）
1. 注册并登录 Render（https://render.com）。
2. 点击 New -> Web Service -> Connect a repository，选择你的 GitHub 仓库。
3. 在部署设置中：
   - Build Command: 留空或使用 `pip install -r requirements.txt`
   - Start Command: 使用 `gunicorn --bind 0.0.0.0:$PORT app:app`（Procfile 中已有）
   - 环境变量：无需特殊变量，除非你想设置 `FLASK_ENV`。
4. Deploy，Render 会自动构建并提供一个可访问的 URL。

Railway
1. 注册并登录 Railway（https://railway.app）。
2. New Project -> Deploy from GitHub，选择仓库。
3. Railway 会根据 `requirements.txt` 自动检测 Python，并使用 `Procfile` 的命令启动。
4. 部署完成后会给出一个公网 URL 分享给别人。

PythonAnywhere（适合小型或免费托管）
1. 注册并登录 PythonAnywhere（https://www.pythonanywhere.com）。
2. 创建一个新的 Web App，选择 Manual configuration -> Flask -> 指定 Python 版本。
3. 在 Web -> Source code 设置中，将代码从 GitHub clone 到你的 PythonAnywhere 家目录（或直接在 Bash 控制台用 `git clone`）。
4. 在 Web -> Virtualenv 创建并选择虚拟环境，然后用 `pip install -r requirements.txt` 安装依赖。
5. 编辑 WSGI 配置文件，指向你的 `app` 模块（例如 `from app import app as application`）。
6. Reload Web 应用，访问你的 PythonAnywhere 域名。

注意与建议
- 静态文件：Render/Railway 会自动托管静态资源（Flask 的 static 文件夹）。
- 数据更新：当前实现把 `data/raw/` 的内容加载到内存。如果你希望在部署后能通过 GitHub 推送自动更新网站内容，请确保每次内容变更后 push 到仓库并触发平台重新部署。
- 安全：开发模式（debug=True）不应在生产/公开部署环境中启用。部署前请在 `app.py` 中把 `debug=False` 或使用环境变量控制。

如果你希望我：
- 把 `requirements.txt` 补全（现在只有 Flask、gunicorn），我可以为你生成更完整的依赖列表并把 `debug` 设为根据环境变量控制；
- 创建一个简单的 GitHub Actions 工作流来在每次 push 时运行基本检查并自动推送到所选平台（例如通过 Render 的 Deploy 按钮挂钩或用 Railway 的 CLI），我也可以帮你完成这些。

Vercel（用于静态托管）

如果你想用 Vercel 来托管并分享网站（免费层支持），可以使用仓库中提供的静态构建脚本 `build_static.py`：

1. 在项目根目录下，脚本会读取 `data/raw/` 中的书籍/章节文本并渲染 `templates/` 生成静态文件到 `out/`。
2. 已在 `vercel.json` 中设置：
   - installCommand: pip install -r requirements.txt
   - buildCommand: python build_static.py
   - outputDirectory: out
3. 把项目 push 到 GitHub 后，登录 Vercel -> New Project -> Import Git Repository，选择仓库。Vercel 会按 `vercel.json` 执行 install/build 并把 `out/` 目录作为静态站点发布。
4. 注意事项：
   - 该静态生成器把章节页面输出为 `/book/<id>/chapter_<n>.html`（URL 与 Flask 运行时的动态路由略有不同）。
   - 若你想保持动态行为（例如“上一章/下一章”链接、搜索、按需加载），Vercel 静态部署会限制交互；可以考虑使用 Vercel Serverless Functions（需要改为 WSGI/ASGI 兼容的方式）或使用 Render/Railway 来运行完整 Flask 服务。

如果你同意，我可以：
- 调整静态页的章节链接以更接近原来的动态 URL 风格；
- 添加一个简单的 GitHub Actions 工作流以在 push 后自动在 `out/` 目录生成静态文件（便于在 push 时检测构建问题）。
