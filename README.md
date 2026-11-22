# 人寿海外智能知识库

面向人寿保险海外业务的智能知识库平台。项目提供文档上传、解析与结构化抽取、向量检索、知识问答、人工复核和多 Agent 风控能力，并配套 Vue 3 管理控制台。

## 功能

- 文档中心：上传、查看、删除文档，触发文档处理流水线
- 四阶段 Agent 抽取：解析文档内容，抽取结构化知识并生成可检索片段
- 双轨检索：结合结构化数据和向量相似度检索知识
- 知识问答：基于检索结果回答保险业务问题，并返回相关引用
- 人工复核：按 P0-P2 优先级处理复核任务，记录处理结果
- 风控中心：文本风险检查、风险概览和审计日志
- 运营总览：查看文档、处理、复核和问答相关统计
- 本地模式：未配置模型密钥时可使用本地规则完成演示流程

## 技术栈

- 前端：Vue 3、Vite、Vue Router、Axios
- 后端：FastAPI、Uvicorn、SQLAlchemy、Pydantic Settings
- 文档处理：pypdf、python-multipart
- AI 与检索：DeepSeek OpenAI 兼容接口、向量检索、结构化检索
- 数据库：SQLite，默认保存到 `fastapi/data/kb.db`

## 项目结构

```text
insurance-knowledge-base/
├── fastapi/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 配置与数据库
│   ├── models.py            # ORM 模型
│   ├── schemas.py           # 请求与响应模型
│   ├── routers/             # dashboard、document、review、qa、risk 等路由
│   ├── services/            # parser、pipeline、retrieval、risk、llm 等服务
│   ├── seed.py              # 演示数据初始化
│   ├── requirements.txt     # Python 依赖
│   └── .env.example         # 环境变量示例
├── vue/
│   ├── src/views/            # 总览、文档、详情、复核、问答、风控页面
│   ├── src/api/              # 后端 API 封装
│   ├── src/components/      # 通用组件
│   ├── vite.config.js        # Vite 与 API 代理配置
│   └── package.json          # 前端脚本与依赖
└── start.ps1                # Windows 一键启动脚本
```

## 环境要求

- Python 3.11+
- Node.js 18+
- npm
- 可选的 DeepSeek API Key

## 快速开始

### 1. 安装后端依赖

```powershell
cd fastapi
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### 2. 配置环境变量

编辑 `fastapi/.env`：

```dotenv
DEEPSEEK_API_KEY=请填写你的 API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LLM_MODE=auto
DATABASE_URL=sqlite:///./data/kb.db
```

`LLM_MODE=auto` 会优先调用真实模型，失败时回退到本地规则。使用 `mock` 可强制本地演示模式，使用 `llm` 可强制调用模型。

### 3. 安装前端依赖

```powershell
cd ..\vue
npm install
```

### 4. 启动服务

分别打开两个终端：

```powershell
# 终端一
cd fastapi
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

```powershell
# 终端二
cd vue
npm run dev
```

也可以在项目根目录执行：

```powershell
.\start.ps1
```

首次启动时后端会自动建表并写入演示数据。

## 常用地址

| 地址 | 用途 |
| --- | --- |
| http://127.0.0.1:5173 | Vue 管理控制台 |
| http://127.0.0.1:8000 | FastAPI 服务 |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/api/health | 健康检查 |

前端 Vite 将 `/api` 请求代理到 `http://localhost:8000`。

## 主要 API 模块

- `/api/system`：系统状态
- `/api/dashboard`：运营概览
- `/api/documents`：文档上传、处理和详情
- `/api/review`：复核任务与统计
- `/api/qa`：知识问答与推荐问题
- `/api/risk`：风险检查、风险概览和审计日志

## 开发命令

```powershell
# 前端
cd vue
npm run dev
npm run build
npm run preview

# 后端
cd fastapi
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 数据与安全

- SQLite 数据库默认位于 `fastapi/data/kb.db`。
- 上传文件默认保存到 `fastapi/data/uploads`。
- `.env`、数据库文件、上传文件和模型密钥不应提交到仓库。
- 生产环境请替换演示数据，限制 CORS 来源，并为上传、模型调用和审计日志增加访问控制。
- 保险知识问答结果应结合人工复核与业务规则使用，不能替代正式承保、理赔或合规审核。

## License

仓库当前未提供明确的开源许可证。若计划公开分发、商用或接受外部贡献，请先补充 `LICENSE` 并明确版权与使用范围。
