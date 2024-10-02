import os
from fastapi import FastAPI, UploadFile, File, Response, HTTPException, Depends
from typing import Union
from pydantic import BaseModel, ValidationError
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
    return {"message": "敏感词检测 API"}

# 函数用于验证输入的参数类型
async def get_text_or_file(
    payload: Union[TextPayload, None] = None,  # JSON 文本，默认为 None
    file: Union[UploadFile, None] = File(None)  # 文件上传，默认为 None
) -> str:
    """
    验证输入是文本还是文件，并返回文本内容。
    如果输入的 payload 是 JSON 请求体，则返回 payload.text；
    如果输入的是文件，则返回文件解码后的文本。
    """
    if payload:
        return payload.text  # 如果传递了 JSON 请求体，则使用该文本
    elif file:
        # 如果传递了文件，读取二进制文件并将其解码为 UTF-8 文本
        return (await file.read()).decode('utf-8')
    else:
        # 如果两者都没有提供，抛出 400 错误
        raise HTTPException(status_code=400, detail="必须提供文本或文件")


# 检测合规性接口，支持接收纯文本或文件
@app.post("/check_compliance")
async def check_compliance(
    text: str = Depends(get_text_or_file),  # 使用依赖注入，确保接收到的参数为文本字符串
):
    """
    接收纯文本或二进制数据，检测文本是否合规，返回敏感词列表。
    该接口支持同时接收 JSON 文本或文件上传，检查是否包含敏感词。
    """
    # 调用 collect_sensitive_words_and_filter 函数，检测敏感词
    sensitive_words, _ = collect_sensitive_words_and_filter(text)

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


# 敏感词替换接口，支持接收纯文本或文件
@app.post("/filter_sensitive_words")
async def filter_sensitive_words(
    text: str = Depends(get_text_or_file),  # 使用依赖注入，确保接收到的参数为文本字符串
):
    """
    接收纯文本或二进制数据，返回替换敏感词后的文本。
    该接口支持同时接收 JSON 文本或文件上传，将敏感词替换为指定符号。
    """
    # 调用 collect_sensitive_words_and_filter 函数，获取替换后的文本
    _, filtered_text = collect_sensitive_words_and_filter(text)

    # 将替换后的文本编码为 UTF-8 的二进制数据
    binary_data = filtered_text.encode('utf-8')

    # 返回二进制响应，设置 Content-Type 为 text/plain，表示返回的是文本数据
    return Response(content=binary_data, media_type="text/plain")


# 主函数，用于运行应用
if __name__ == "__main__":
    import uvicorn
    try:
        print("启动成功")
        # 启动 FastAPI 应用，监听 0.0.0.0 的 3005 端口
        uvicorn.run(app, host="0.0.0.0", port=3005)
    except Exception as e:
        # 如果启动失败，捕获异常并打印错误信息
        print(f"启动失败：{e}")
