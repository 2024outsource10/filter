import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Response, HTTPException, Body, Request
from typing import Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 导入敏感词过滤模块
from filter import collect_sensitive_words_and_filter

# 创建 FastAPI 应用实例
app = FastAPI()

# CORS 配置（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求
    allow_credentials=True,  # 允许跨域请求携带凭证（如 Cookies）
    allow_methods=["*"],  # 允许所有 HTTP 方法：GET, POST, PUT, DELETE 等
    allow_headers=["*"],  # 允许所有的请求头部
)

# 定义请求体模型，用于接收 JSON 格式的文本请求
class TextPayload(BaseModel):
    text: str  # 包含要处理的文本


@app.get("/")
async def root():
    """
    根路径 '/' 的 GET 请求处理器。
    返回一个简单的 JSON 消息，用于测试 API 是否正常工作。
    """
    return {"message": "Hello World"}


@app.post("/check")
async def check_compliance(
    request: Request,  # 用于处理原始请求体
    payload: Optional[TextPayload] = Body(None),  # JSON 请求体
    file: Optional[UploadFile] = File(None),  # 文件上传
):
    """
    接收 JSON、文件或纯文本，检测文本是否合规，返回敏感词列表。
    该接口支持接收 JSON、文件上传或纯文本，检查是否包含敏感词。
    """
    # 优先处理 JSON 请求体
    if payload and payload.text:
        text_to_check = payload.text
    # 如果有文件上传，读取文件内容
    elif file:
        try:
            text_to_check = (await file.read()).decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件无法解码为 UTF-8 文本")
    # 如果是纯文本（text/plain 请求体）
    else:
        # 尝试读取 request body 中的纯文本内容
        try:
            text_to_check = (await request.body()).decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="纯文本无法解码为 UTF-8")

    # 调用 collect_sensitive_words_and_filter 函数，检测敏感词
    sensitive_words, _ = collect_sensitive_words_and_filter(text_to_check)

    # 如果存在敏感词，返回不合规状态和敏感词列表
    if sensitive_words:
        return {
            "compliant": False,  # 表示文本不合规
            "message": "文本包含敏感词",  # 错误信息
            "sensitive_words": sensitive_words  # 返回的敏感词列表
        }
    else:
        # 如果没有敏感词，返回合规状态
        return {
            "compliant": True,  # 表示文本合规
            "message": "文本合规，不包含敏感词"
        }


@app.post("/filter")
async def filter_text(
    request: Request,  # 用于处理原始请求体
    payload: Optional[TextPayload] = Body(None),  # JSON 请求体
    file: Optional[UploadFile] = File(None),  # 文件上传
):
    """
    接收 JSON、文件或纯文本，过滤文本并替换敏感词，返回处理后的文本。
    该接口支持接收 JSON、文件上传或纯文本，替换敏感词并返回处理后的文本。
    """
    # 优先处理 JSON 请求体
    if payload and payload.text:
        text_to_check = payload.text
    # 如果有文件上传，读取文件内容
    elif file:
        try:
            text_to_check = (await file.read()).decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件无法解码为 UTF-8 文本")
    # 如果是纯文本（text/plain 请求体）
    else:
        # 尝试读取 request body 中的纯文本内容
        try:
            text_to_check = (await request.body()).decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="纯文本无法解码为 UTF-8")

    # 调用 collect_sensitive_words_and_filter 函数，进行敏感词过滤并替换
    _, filtered_text = collect_sensitive_words_and_filter(text_to_check)

    # 返回过滤后的文本
    return {
        "message": "文本已处理",
        "filtered_text": filtered_text  # 返回过滤后的文本
    }

if __name__ == "__main__":
    import uvicorn

    try:
        print("启动成功")
        uvicorn.run(app, host="0.0.0.0", port=3005)
    except Exception as e:
        print(f"启动失败：{e}")
