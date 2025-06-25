from flask_restful import Resource

from configs import dify_config
from controllers.open_ai import api
from pydantic import BaseModel, Field

import re
from typing import List, Optional, Dict, Any, Union
from flask import current_app
import time

## 集成ollama
# 数据模型
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def format_response(response):
    """
    格式化响应，添加适当的换行和段落分隔。
    """
    paragraphs = re.split(r'\n{2,}', response)

    formatted_paragraphs = []
    for para in paragraphs:
        if '```' in para:
            parts = para.split('```')
            for i, part in enumerate(parts):
                if i % 2 == 1:  # 这是代码块
                    parts[i] = f"\n```\n{part.strip()}\n```\n"
            para = ''.join(parts)
        else:
            para = para.replace('. ', '.\n')

        formatted_paragraphs.append(para.strip())

    current_app.logger.debug("完成返回结果格式化")

    return '\n\n'.join(formatted_paragraphs)

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Usage
    system_fingerprint: Optional[str] = None


class IndexApi(Resource):
    def get(self):
        return {
            "welcome": "Make fake OpenAI Api,support Open-webui",
            "api_version": "v1",
            "server_version": dify_config.CURRENT_VERSION,
        }

class ModelsApi(Resource):
    def get(self):
        """
        返回可用模型列表
        """
        current_app.logger.info("收到模型列表请求")
        current_time = int(time.time())
        models = [
             {"id": "本地检索", "object": "model", "created": current_time - 100000, "owned_by": "graphrag"},
             {"id": "全局检索", "object": "model", "created": current_time - 95000, "owned_by": "graphrag"},
             {"id": "tavily检索", "object": "model", "created": current_time - 85000, "owned_by": "tavily"},
        ]
        response = {
             "object": "list",
             "data": models
        }
        current_app.logger.info(f"发送模型列表: {response}")
        return response


class ChatCompletionsApi(Resource):
    #@validate_app_token(fetch_user_arg=FetchUserArg(fetch_from=WhereisUserArg.JSON, required=True))
    def post(self, request: ChatCompletionRequest):
        try:
            current_app.logger.info(f"收到聊天完成请求: {request}")
            prompt = request.messages[-1].content
            current_app.logger.info(f"处理提示: {prompt}")
    
            # 根据模型选择使用不同的搜索方法
            if request.model == "全局检索":
                response, context  = {"555555","11"}
                formatted_response = format_response(response)
            elif request.model == "tavily检索":
                response, context  = {"555555","11"}
                formatted_response = response
            elif request.model == "综合检索":
                formatted_response = {"555555","11"}
            else:  # 默认使用本地搜索
                #result = await local_search(prompt)
                current_app.logger.info(f"本地搜索")
                response, _context  = {"555555","11"}
                formatted_response = format_response(response)
    
            current_app.logger.info(f"格式化的搜索结果: {formatted_response}")
    
            # 流式响应和非流式响应的处理保持不变
            
            if request.stream:
                async def generate_stream():
                    chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
                    lines = formatted_response.split('\n')
                    for i, line in enumerate(lines):
                        chunk = {
                            "id": chunk_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": request.model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": line + '\n'}, # if i > 0 else {"role": "assistant", "content": ""},
                                    "finish_reason": None
                                }
                            ]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                        await asyncio.sleep(0.05)
    
                    final_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop"
                            }
                        ]
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
    
                return StreamingResponse(generate_stream(), media_type="text/event-stream")
            else:
                response = ChatCompletionResponse(
                    model=request.model,
                    choices=[
                        ChatCompletionResponseChoice(
                            index=0,
                            message=Message(role="assistant", content=formatted_response),
                            finish_reason="stop"
                        )
                    ],
                    usage=Usage(
                        prompt_tokens=len(prompt.split()),
                        completion_tokens=len(formatted_response.split()),
                        total_tokens=len(prompt.split()) + len(formatted_response.split())
                    )
                )
                current_app.logger.info(f"发送响应: {response}")
                return JSONResponse(content=response.dict())
            
        except Exception as e:
            current_app.logger.error(f"处理聊天完成时出错: {e}")
            raise HTTPException(status_code=500, detail=str(e))

api.add_resource(IndexApi, "/")

api.add_resource(ModelsApi, "/models")
api.add_resource(ChatCompletionsApi, "/chat/completions")