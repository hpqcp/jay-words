# Jay Words

Jay Words 是一个面向英语学习的本地化背单词与文章背诵系统。项目包含词库管理、单词练习、错题复习、学习记录、词形变化练习、文章背诵和语音背诵等模块，适合个人或家庭自建使用。

## 功能特性

- 词库管理：按年级、课程、章节组织单词，支持新增、编辑、删除和导入导出。
- 多种单词练习：闪卡、拼写、选择题、配对、赛车练习等。
- 词形变化练习：支持比较级、最高级，以及原型到词形、词形到原型的筛选练习。
- 错题本：自动记录错误单词，支持集中复习和清理。
- 学习记录：统计练习结果，查看学习进度。
- 文章背诵：支持中英文文章管理、分段背诵、不同隐藏难度。
- 语音背诵：基于浏览器 Web Speech API 识别朗读内容，支持整段/逐句朗读、纠错后评分和进度记录。
- 本地部署：FastAPI 后端、Vue 3 前端、MySQL 数据库，可使用 Docker 一键构建运行。

## 技术栈

- 前端：Vue 3、Vue Router、Vite
- 后端：FastAPI、Uvicorn、PyMySQL、jieba
- 数据库：MySQL / MariaDB
- 部署：Docker、Docker Compose

## 目录结构

```text
.
├── backend/                 # FastAPI 后端
│   ├── routers/             # API 路由模块
│   ├── main.py              # 应用入口
│   ├── database.py          # 数据库初始化与连接
│   ├── vocab_data.py        # 内置词库数据
│   └── requirements.txt     # Python 依赖
├── frontend/                # Vue 前端
│   ├── src/api/             # 前端 API 封装
│   ├── src/router/          # 前端路由
│   ├── src/views/           # 页面模块
│   └── package.json
├── example_vocab.json       # 词库导入示例
├── Dockerfile
├── docker-compose.yml
├── start.ps1                # Windows 本地开发启动脚本
└── .env.example
```

## 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8+ 或 MariaDB
- Chrome / Edge 浏览器，语音背诵功能需要浏览器支持 `SpeechRecognition`

## 本地开发

1. 创建数据库用户和配置。

项目启动时会自动创建数据库和数据表，但数据库用户需要具备建库、建表和读写权限。

在项目根目录创建 `.env`，或在启动后端前设置环境变量：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=jay
DB_PASSWORD=your_password_here
DB_NAME=jay_words
```

2. 启动后端。

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 18001 --reload
```

后端地址：

```text
http://localhost:18001
```

接口文档：

```text
http://localhost:18001/docs
```

3. 启动前端。

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:3000
```

Vite 开发服务器会把 `/api` 代理到 `http://localhost:18001`。

### Windows 快速启动

安装好 Python、Node.js 和依赖后，也可以在项目根目录运行：

```powershell
.\start.ps1
```

脚本会同时启动后端和前端：

- 后端：`http://localhost:18001`
- 前端：`http://localhost:3000`

## Docker 部署

1. 准备环境变量。

```bash
cp .env.example .env
```

编辑 `.env`，填写 MySQL 连接信息。

2. 构建并启动。

```bash
docker compose up -d --build
```

3. 访问服务。

```text
http://localhost:18001
```

Docker 镜像会先构建前端静态文件，再由 FastAPI 统一提供后端 API 和前端页面。

## 词库导入格式

可参考 [example_vocab.json](./example_vocab.json)：

```json
[
  {
    "grade": "六年级上册",
    "lessons": [
      {
        "lesson": "Unit 1 - Hobby",
        "sections": [
          {
            "section": "Words",
            "words": [
              {
                "english": "swimming",
                "chinese": "游泳",
                "phonetic": "/ˈswɪmɪŋ/"
              }
            ]
          }
        ]
      }
    ]
  }
]
```

单词字段支持：

- `english`：英文单词或短语
- `chinese`：中文释义
- `phonetic`：音标，可为空
- `comparative`：比较级，可为空
- `superlative`：最高级，可为空

## 主要页面

- `/`：首页
- `/manage`：词库管理
- `/flashcard`：闪卡学习
- `/quiz`：单词测验
- `/completion`：拼写填空
- `/choice`：选择题
- `/match`：配对练习
- `/racing`：赛车练习
- `/word-forms`：词形变化练习
- `/wrong`：错题本
- `/records`：学习记录
- `/articles`：文章管理
- `/recite`：文章背诵
- `/voice-recite`：语音背诵

## 语音背诵说明

语音背诵使用浏览器内置 Web Speech API，不接入云端 ASR 服务。实际识别效果受浏览器、系统麦克风、网络和发音环境影响。

建议使用：

- Chrome 或 Edge
- HTTPS 或 `localhost` 环境
- 清晰稳定的麦克风输入

当前语音背诵流程为：开始朗读后手动点击“结束并纠错”，系统使用当前识别文本进行本地纠错、评分并保存练习记录。

## 数据库说明

后端启动时会自动初始化以下核心数据表：

- `grades`、`lessons`、`sections`、`words`
- `wrong_words`
- `learning_records`
- `articles`
- `article_practices`
- `voice_practices`

首次启动且词库为空时，会导入后端内置词库。

## 开发命令

前端：

```bash
cd frontend
npm run dev
npm run build
npm run preview
```

后端：

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 18001 --reload
```

基础健康检查：

```text
GET /api/health
GET /api/version
```

## 注意事项

- 不要把真实 `.env`、数据库文件、`node_modules/`、构建产物和缓存文件提交到 GitHub。
- Docker 部署时需要确保容器可以访问 `.env` 中配置的 MySQL 地址。
- 语音识别不是专业口语测评，仅用于辅助背诵和练习反馈。

## License

当前仓库未声明开源许可证。如需公开发布，建议补充明确的 `LICENSE` 文件。
