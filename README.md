# RAG 知识库与智能客服学习项目

这是基于 Python、LangChain、Chroma、Streamlit 和通义千问接口整理的学习项目。项目包含知识库入库、命令行 RAG 问答，以及独立的网页客服与尺码推荐功能，用于练习从文档处理到模型回答的各个模块。

## 当前功能

| 模块 | 功能 |
| --- | --- |
| 知识库入库 | 读取上传的文本、计算 MD5 去重、文本切块、调用 Embedding、写入本地 Chroma |
| 命令行 RAG | 按问题检索文档片段，构建带参考资料和历史消息的提示词，调用模型回答 |
| 网页客服 | 普通问题通过 Qwen API 流式回答 |
| 本地尺码推荐 | 从问题与历史对话中提取身高、体重，按示例尺码表匹配并提示缺失或重叠区间 |
| 在线尺码分析 | 可在网页侧栏开启，将整份尺码表与会话历史交给 Qwen 分析 |
| 会话历史 | 将用户消息和模型回答保存到本地文件 |

**当前网页客服 `app_qa.py` 尚未调用 `RagService`。** 网页中的普通问答直接调用模型，在线尺码分析读取整份尺码表；向量检索问答通过 `rag.py` 单独运行。

## RAG 流程

知识库入库：

```text
UTF-8 TXT 文档 → MD5 去重 → 文本切块 → text-embedding-v4 → Chroma 持久化
```

命令行问答：

```text
用户问题 → Retriever 检索 → 文档片段格式化 → 参考资料 + 历史消息 + 问题
        → qwen3-max → 字符串回答 → 保存会话历史
```

默认切块长度为 1000 个字符，重叠为 100 个字符，检索返回 2 个片段。配置项 `similarity_threshold` 当前被用于检索的 `k`，表示返回数量，并非相似度分数阈值。具体配置见 `config_data.py`。

## 文件结构

```text
RAG项目实例/
├── app_file_uploader.py   # 知识库上传页面
├── app_qa.py              # 网页客服与尺码推荐
├── knowledge_base.py      # MD5 去重、切块、向量入库
├── vector_stores.py       # Chroma 与 Retriever
├── rag.py                 # 命令行 RAG 链
├── online_size_ai.py      # Qwen 流式调用
├── size_recommendation.py # 本地尺码表匹配
├── file_history_store.py  # 会话历史文件存储
├── config_data.py         # 模型与检索配置
├── data/
│   └── 尺码推荐.txt       # 示例资料
├── requirements.txt
├── README.md
└── .gitignore
```

`chroma_db/`、`chat_history/` 和 `md5.text` 在运行时生成，不需要作为示例代码上传。

## 安装与配置

依赖版本根据整理时使用的 Python 3.12 环境记录。先在终端进入本文件夹，再执行：

```powershell
python -m pip install -r requirements.txt
```

配置阿里云接口凭证：

```powershell
$env:DASHSCOPE_API_KEY = "替换为你自己的阿里云 API Key"
```

该设置只在当前 PowerShell 终端及其启动的程序中生效。使用 PyCharm 运行按钮时，需要在对应运行配置中设置 `DASHSCOPE_API_KEY`。

模型名称由 `config_data.py` 配置，默认聊天模型为 `qwen3-max`，Embedding 模型为 `text-embedding-v4`。账户需要具备相应模型的调用权限。

所有命令都从本文件夹执行。代码中的 `./chroma_db` 和 `./md5.text` 相对于当前工作目录解析；上传和检索应使用同一个工作目录。

## 运行方法

### 1. 启动知识库上传页面

```powershell
python -m streamlit run app_file_uploader.py --server.port 8501
```

按终端给出的地址打开网页，上传 `data/尺码推荐.txt` 或其他 UTF-8 编码的 TXT 文件。

虽然上传控件允许选择 PDF 和 DOCX，但当前代码统一使用 UTF-8 解码，并未实现这两类文件的解析。此版本请使用 TXT。

### 2. 运行命令行 RAG

文档入库后，在同一个文件夹下执行：

```powershell
python rag.py
```

程序启动时第一项输入用作会话 ID，当前提示文字写成了“今天是什么天气”；可以输入 `demo`。随后输入问题开始问答，输入 `exit` 结束。

例如：

```text
会话 ID：demo
问题：请根据参考资料列出 XL 对应的身高和体重范围。
```

终端会打印送给模型的提示词，可以检查其中是否包含检索到的资料。示例中的预期资料为身高 170—178 cm、体重 130—150 斤，实际回答取决于检索结果及模型输出。

### 3. 启动网页客服

```powershell
python -m streamlit run app_qa.py --server.port 8502
```

可以输入：

```text
身高 172cm，体重 140斤，推荐什么尺码？
```

默认本地尺码匹配不调用模型 API；普通问题和侧栏开启后的在线尺码分析会调用 Qwen。本地匹配遇到信息缺失会请求补充，符合多个区间时会列出多个尺码。

目前网页刷新后会创建新的会话 ID，文件历史不等同于已实现网页会话恢复。

## 当前限制与后续改进

- 网页客服尚未接入 `RagService`，后续可以将知识库问答接到网页。
- 上传模块尚未支持 PDF / DOCX 解析。
- `knowledge_base.py` 入库时使用了 `metadata=`，Chroma 对应参数是 `metadatas=`；需要修正后再验证来源信息是否保存完整。
- 当前只做向量 Top-K 检索，没有重排序、混合检索或相似度分数过滤。
- 提示词要求以参考资料为主，但尚未实现可靠的证据不足拒答与来源引用。
- 多轮历史会传入回答提示词；检索使用的是当前问题，尚未实现结合历史改写检索问题。
- 尚未建立固定问答集或完成检索、回答质量的量化评测。

此仓库用于课程学习与后续改进，README 描述按当前代码整理，不代表已完成全部流程的运行测试。

## 上传 GitHub

保留 Python 代码、示例 TXT、README、requirements 和 `.gitignore`。运行产生的向量库、聊天历史、MD5 记录，以及 IDE 配置、缓存和凭证文件无需上传。

`.gitignore` 在使用 Git 提交时生效；如果使用 GitHub 网页拖拽上传，需要手动排除这些文件。安装后应重新上传示例资料生成知识库。

## 学习收获

练习了文档去重与切块、Embedding、Chroma 检索、LangChain 链、提示词组装、流式响应、文件会话历史，以及网页展示与业务逻辑拆分。
