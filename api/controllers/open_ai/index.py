from flask_restful import Resource

from configs import dify_config
from controllers.open_ai import api
from pydantic import BaseModel, Field
import logging

import services
from controllers.service_api.wraps import FetchUserArg, WhereisUserArg, validate_app_token
from models.model import App, AppMode, EndUser
from controllers.service_api.app.error import (
    AppUnavailableError,
    CompletionRequestError,
    ConversationCompletedError,
    NotChatAppError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from flask_restful import Resource, reqparse,fields, marshal_with
from flask import Flask, request,current_app
from marshmallow import Schema, fields, ValidationError

from werkzeug.exceptions import InternalServerError, NotFound
from controllers.service_api.app.error import (
    AppUnavailableError,
    CompletionRequestError,
    ConversationCompletedError,
    NotChatAppError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from controllers.service_api.wraps import FetchUserArg, WhereisUserArg, validate_app_token
from controllers.web.error import InvokeRateLimitError as InvokeRateLimitHttpError
from core.app.apps.base_app_queue_manager import AppQueueManager
from core.app.entities.app_invoke_entities import InvokeFrom
from core.errors.error import (
    ModelCurrentlyNotSupportError,
    ProviderTokenNotInitError,
    QuotaExceededError,
)

from core.model_runtime.errors.invoke import InvokeError
from services.app_generate_service import AppGenerateService
from services.errors.llm import InvokeRateLimitError
from libs import helper
from libs.helper import uuid_value

import uuid
import json
import re
from typing import List, Optional, Dict, Any, Union

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

def message_list(value):
    if not isinstance(value, list):
        raise ValueError("必须是列表")
    return [Message(**item) for item in value]

## 方式二


class MessageSchema(Schema):
    role = fields.Str(required=True)
    content = fields.Str(required=True)

class MessageListSchema(Schema):
    messages = fields.List(fields.Nested(MessageSchema), required=False)



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

    site_fields = {
        "title": fields.String,
        "chat_color_theme": fields.String,
        "chat_color_theme_inverted": fields.Boolean,
        "icon_type": fields.String,
        "icon": fields.String,
        "icon_background": fields.String,
      #  "icon_url": AppIconUrlField,
        "description": fields.String,
        "copyright": fields.String,
        "privacy_policy": fields.String,
        "custom_disclaimer": fields.String,
        "default_language": fields.String,
        "prompt_public": fields.Boolean,
        "show_workflow_steps": fields.Boolean,
        "use_icon_as_answer_icon": fields.Boolean,
    }

    app_fields = {
        "app_id": fields.String,
        "end_user_id": fields.String,
        "enable_site": fields.Boolean,
        "site": fields.Nested(site_fields),
      #  "model_config": fields.Nested(model_config_fields, allow_null=True),
        "plan": fields.String,
        "can_replace_logo": fields.Boolean,
        "custom_config": fields.Raw(attribute="custom_config"),
    }

    @marshal_with(site_fields)
    #@validate_app_token(fetch_user_arg=FetchUserArg(fetch_from=WhereisUserArg.JSON, required=True))
    def post(self):
        try:

            # 方式一
            request = MessageListSchema().load(request.get_json())

            print(request)

            #request: ChatCompletionRequest

            # 方式一
            parser = reqparse.RequestParser()
            #parser.add_argument('role', type=str, help='角色')
            #parser.add_argument('content', type=str, help='聊天内容')
            parser.add_argument('model', type=str, help='模型名称')
            parser.add_argument('messages', type=message_list, help='消息列表', required=False, location="json")
            parser.add_argument('temperature', type=float, help='温度')
            parser.add_argument('top_p', type=float, help='')
            parser.add_argument('n', type=int, help='记录数')
            parser.add_argument('stream', type=bool, help='是否流式输出')
            #parser.add_argument('stop', type=Optional[Union[str, List[str]]], help='是否停止')

            parser.add_argument('max_tokens', type=int, help='最大消耗token数')
            parser.add_argument('presence_penalty', type=float, help='')
            parser.add_argument('frequency_penalty', type=float, help='')
            parser.add_argument('logit_bias', type=dict,required=False, location="json")
            parser.add_argument('user', type=str, help='用户')
            
            request = parser.parse_args()

    
            #request=ChatCompletionRequest()

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
                return response.dict()
            
        except Exception as e:
            current_app.logger.error(f"处理聊天完成时出错: {e}")
            #raise HTTPException(status_code=500, detail=str(e))
            raise InternalServerError()

class CompletionApi(Resource):
    @validate_app_token(fetch_user_arg=FetchUserArg(fetch_from=WhereisUserArg.JSON, required=True))
    def post(self, app_model: App, end_user: EndUser):
       # if app_model.mode != "completion":
       #     raise AppUnavailableError()

        #print(f"app_model:{json.dumps(app_model)}  ")
        #print(f"end_user:{json.dumps(end_user)}  ")

        parser = reqparse.RequestParser()
        parser.add_argument("inputs", type=dict, required=True, location="json")
        parser.add_argument("query", type=str, location="json", default="")
        parser.add_argument("files", type=list, required=False, location="json")
        parser.add_argument("response_mode", type=str, choices=["blocking", "streaming"], location="json")
        parser.add_argument("retriever_from", type=str, required=False, default="dev", location="json")

        args = parser.parse_args()

        logging.debug(f"args:{args}")
        streaming = args["response_mode"] == "streaming"

        args["auto_generate_name"] = False

        try:
            response = AppGenerateService.generate(
                app_model=app_model,
                user=end_user,
                args=args,
                invoke_from=InvokeFrom.SERVICE_API,
                streaming=streaming,
            )

            return helper.compact_generate_response(response)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except services.errors.conversation.ConversationCompletedError:
            raise ConversationCompletedError()
        except services.errors.app_model_config.AppModelConfigBrokenError:
            logging.exception("App model config broken.")
            raise AppUnavailableError()
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except ValueError as e:
            raise e
        except Exception:
            logging.exception("internal server error.")
            raise InternalServerError()


api.add_resource(IndexApi, "/")

api.add_resource(ModelsApi, "/models")
api.add_resource(ChatCompletionsApi, "/chat/completions2")
api.add_resource(CompletionApi, "/chat/completions")