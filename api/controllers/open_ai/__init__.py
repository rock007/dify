from flask import Blueprint

from libs.external_api import ExternalApi

bp = Blueprint("open_ai", __name__, url_prefix="/open_ai/api")
api = ExternalApi(bp)


from .index import (
    IndexApi,
    ModelsApi,
    ChatCompletionsApi
)
