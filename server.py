import os
from fastapi import FastAPI, UploadFile, File, Response, HTTPException
from typing import List, Dict
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 导入敏感词过滤模块
from filter import collect_sensitive_words_and_filter

# 创建 FastAPI 应用
app = FastAPI()

# CORS 配置（跨域资源共享）
# CORS 是一种允许浏览器客户端与来自不同域的资源交互的安全机制。
# 这里的配置允许来自任意源的请求（allow_origins=["*"]）并允许跨域请求传递凭证。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求
    allow_credentials=True,  # 允许跨域请求传递凭证
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST, PUT, DELETE等）
    allow_headers=["*"],  # 允许所有类型的请求头
)


# 定义请求体的数据模型（用于接受 JSON 格式的文本）
class TextPayload(BaseModel):
    text: str  # 定义一个包含字符串的字段 "text"


@app.get("/")
async def root():
    """
    定义根路由处理函数，返回一个简单的欢迎消息。
    当客户端访问 "/" 路由时，会返回一个 "敏感词检测 API" 的消息。
    """
    return {"message": "敏感词检测 API"}


# 检测合规性接口
@app.post("/check_compliance")
def check_compliance(payload: TextPayload):
    """
    检测文本是否合规的 API。
    这个接口接收一个包含文本的请求体，检查文本中是否包含敏感词。

    参数:
    - payload: 请求体数据，包含要检测的文本。

    返回:
    - 如果有敏感词，返回 "compliant: False"，并列出敏感词列表。
    - 如果没有敏感词，返回 "compliant: True"，表示文本合规。
    """
    # 获取请求体中的文本
    text = payload.text

    # 调用 collect_sensitive_words_and_filter 函数，检测敏感词
    sensitive_words, _ = collect_sensitive_words_and_filter(text)

    # 如果敏感词列表不为空，则返回不合规的状态
    if sensitive_words:
        return {
            "compliant": False,  # 表示文本不合规
            "message": "文本包含敏感词",  # 返回的消息
            "sensitive_words": sensitive_words  # 返回的敏感词列表
        }
    else:
        # 如果没有敏感词，则返回合规的状态
        return {
            "compliant": True,  # 表示文本合规
            "message": "文本合规，不包含敏感词"  # 返回的消息
        }


# 敏感词替换接口
@app.post("/filter_sensitive_words")
def filter_sensitive_words(payload: TextPayload):
    """
    敏感词替换的 API。
    这个接口接收一个文本，将文本中的敏感词替换为指定符号，并返回处理后的文本。

    参数:
    - payload: 请求体数据，包含要处理的文本。

    返回:
    - 过滤后的文本，敏感词已经被替换。
    """
    # 获取请求体中的文本
    text = payload.text

    # 调用 collect_sensitive_words_and_filter 函数，获取替换后的文本
    _, filtered_text = collect_sensitive_words_and_filter(text)

    # 返回替换后的文本
    return {
        "filtered_text": filtered_text  # 处理后的文本，敏感词已被替换
    }


# 如果此模块作为主模块运行，则启动应用
if __name__ == "__main__":
    import uvicorn

    try:
        print("启动成功")  # 启动成功后打印的消息
        # 运行 FastAPI 应用，监听所有 IP 地址（0.0.0.0）和端口 3004
        uvicorn.run(app, host="0.0.0.0", port=3004)
    except Exception as e:
        # 如果应用启动失败，打印错误信息
        print(f"启动失败：{e}")
