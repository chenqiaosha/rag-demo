# 基于 RAG 的 PDF 知识库问答系统

一个基于 RAG（Retrieval-Augmented Generation）的 PDF 知识库问答系统。上传 PDF 后，系统会自动解析、切分、向量化并存入向量数据库。用户可以用自然语言提问，系统从文档中检索相关内容，调用大语言模型生成答案，并显示来源。

## 功能特性

- **PDF 上传与索引**：上传 PDF，自动完成文本提取、切分、向量化并存入 ChromaDB。
- **智能问答**：基于 PDF 内容进行多轮问答，答案严格来源于文档。
- **来源引用**：每条回答均显示引用的 PDF 文件名，方便溯源。
- **对话历史**：所有问答自动保存到 MySQL，支持按会话 ID 查询。
- **文档删除**：按文件名删除已上传的 PDF 及其对应的向量数据。
- **可视化界面**：基于 Streamlit，支持上传、聊天、加载历史、删除文档。

## 技术栈

| 类别 | 技术 |
|---|---|
| 编程语言 | Python 3.11 |
| 后端框架 | FastAPI |
| RAG 框架 | LangChain |
| 向量数据库 | ChromaDB |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 |
| 大语言模型 | DeepSeek API（OpenAI 兼容接口） |
| 关系型数据库 | MySQL |
| 前端框架 | Streamlit |
| 部署工具 | Uvicorn |

## 项目结构

rag-demo/
├── .env                  # 环境变量（API 密钥、数据库密码）
├── .gitignore            # Git 忽略文件
├── requirements.txt      # 依赖清单
├── init_db.sql           # MySQL 建表语句
├── db.py                 # MySQL 连接与操作
├── rag_core.py           # RAG 核心逻辑
├── main.py               # FastAPI 后端接口
├── app.py                # Streamlit 前端界面
├── data/                 # 上传的 PDF 存放目录（不提交）
└── chroma_db/            # ChromaDB 向量持久化目录（不提交）

## 环境要求

- Python 3.11
- MySQL 5.7+（可使用 Docker）
- Git

## 安装与运行

### 1. 克隆项目

git clone https://github.com/chenqiaosha/rag-demo.git
cd rag-demo

### 2. 创建虚拟环境

conda create -n rag-demo python=3.11 -y
conda activate rag-demo

### 3. 安装依赖

pip install -r requirements.txt

### 4. 配置环境变量

在项目根目录创建 `.env` 文件，内容如下：

OPENAI_API_KEY=你的DeepSeek密钥
OPENAI_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=rag_demo

### 5. 初始化数据库

在 MySQL 中执行 `init_db.sql`：

mysql -u root -p < init_db.sql

### 6. 启动后端

uvicorn main:app --reload --port 8000

### 7. 启动前端

另开一个终端，激活环境后执行：

streamlit run app.py

浏览器会自动打开 http://localhost:8501

## 使用说明

1. 在左侧栏上传 PDF，点击“索引文档”。
2. 等待索引完成，底部输入框提问。
3. 答案会显示在右侧，并附上来源文件名。
4. 点击“从数据库加载历史记录”可查看当前会话的问答历史。
5. 在“删除文档”下拉框中选择文件，点击“删除文档”可移除对应 PDF 及向量。

## 常见问题

**Q：模型下载很慢或超时？**
A：在 `rag_core.py` 开头添加以下两行，使用国内镜像：
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_OFFLINE'] = '1'

**Q：报错 `ModuleNotFoundError: No module named 'dotenv'`？**
A：确认已激活 `rag-demo` 环境，并重新执行 `pip install -r requirements.txt`。

**Q：ChromaDB 报错 `Embedding dimension does not match`？**
A：嵌入模型改变后需删除 `chroma_db` 文件夹，重新上传 PDF。

**Q：MySQL 连接失败？**
A：检查 `.env` 中的数据库配置，确保 MySQL 已启动且 `rag_demo` 数据库已创建。

**Q：删除 PDF 时提示“文件被占用”？**
A：这是 Windows 文件句柄未释放所致，重启后端或稍后重试即可。接口已做容错处理，向量会被正常删除。

## 许可证

本项目仅用于学习与演示，代码开源，可自由使用。
