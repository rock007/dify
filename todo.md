## 20250624 理解框架、组件



### api service

### web  front
+ doccker 方式运行
  docker run -id -p 3000:3000 --name=dify-web  -e CONSOLE_API_URL=http://192.168.1.3:5001 -e APP_API_URL=http://192.168.1.3:5001 docker.m.daocloud.io/langgenius/dify-web:1.4.3

### 中间件 docker-compose.middleware.yaml
+ pg 
docker run -id --privileged=true  --name postgres15 -p 5432:5432 -v /data/postgresql_data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=fuckthis321 -d docker.m.daocloud.io/postgres:15-alpine
==> 已存在 用 postgres  版本17
+ redis
 docker run  -v /data/redis/data:/data --name redis  -p 6379:6379  -d docker.m.daocloud.io/redis:6 --requirepass fuckthis321

+ 支持minio
docker run \
--name minio \
-p 9000:9000 \
-p 9090:9090 \
-d \
-e "MINIO_ROOT_USER=minio" \
-e "MINIO_ROOT_PASSWORD=fuckthis321" \
-v /data/minio-data:/data \
-v /data/minio-config:/root/.minio \
docker.m.daocloud.io/minio/minio server /data --console-address ":9090" --address ":9000"

== quay.io/minio/minio:RELEASE.2023-04-28T18-11-17Z 用旧版本吧，cpu不支持

+ 向量数据库 如qdrant weaviate
sudo docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v /data/qdrant_data:/qdrant/storage \
  docker.m.daocloud.io/qdrant/qdrant

+ sandbox 是一个轻量、快速、安全的代码运行环境，支持多种编程语言   ==>不能共享，放到docker-compose中
langgenius/dify-sandbox:0.2.12

SANDBOX_API_KEY=dify-sandbox
SANDBOX_GIN_MODE=release
SANDBOX_WORKER_TIMEOUT=15
SANDBOX_ENABLE_NETWORK=true
SANDBOX_HTTP_PROXY=http://ssrf_proxy:3128
SANDBOX_HTTPS_PROXY=http://ssrf_proxy:3128
SANDBOX_PORT=8194



+ plugin daemon  ==>不能共享，放到docker-compose中
langgenius/dify-plugin-daemon:0.1.2-local

      DB_HOST: ${DB_HOST:-db}
      DB_PORT: ${DB_PORT:-5432}
      DB_USERNAME: ${DB_USER:-postgres}
      DB_PASSWORD: ${DB_PASSWORD:-difyai123456}
      DB_DATABASE: ${DB_PLUGIN_DATABASE:-dify_plugin}
      REDIS_HOST: ${REDIS_HOST:-redis}
      REDIS_PORT: ${REDIS_PORT:-6379}
      REDIS_PASSWORD: ${REDIS_PASSWORD:-difyai123456}
      SERVER_PORT: ${PLUGIN_DAEMON_PORT:-5002}
      SERVER_KEY: ${PLUGIN_DAEMON_KEY:-lYkiYYT6owG+71oLerGzA7GXCgOT++6ovaezWAjpCjf+Sjc3ZtU+qUEi}
      MAX_PLUGIN_PACKAGE_SIZE: ${PLUGIN_MAX_PACKAGE_SIZE:-52428800}
      PPROF_ENABLED: ${PLUGIN_PPROF_ENABLED:-false}
      DIFY_INNER_API_URL: ${PLUGIN_DIFY_INNER_API_URL:-http://host.docker.internal:5001}
      DIFY_INNER_API_KEY: ${PLUGIN_DIFY_INNER_API_KEY:-QaHbTe77CtuXmsfyhR7+vRjI/+XbV1AaFy691iy+kGDv2Jvy0/eAh8Y1}
      PLUGIN_REMOTE_INSTALLING_HOST: ${PLUGIN_DEBUGGING_HOST:-0.0.0.0}
      PLUGIN_REMOTE_INSTALLING_PORT: ${PLUGIN_DEBUGGING_PORT:-5003}
      PLUGIN_WORKING_PATH: ${PLUGIN_WORKING_PATH:-/app/storage/cwd}
      FORCE_VERIFYING_SIGNATURE: ${FORCE_VERIFYING_SIGNATURE:-true}
      PYTHON_ENV_INIT_TIMEOUT: ${PLUGIN_PYTHON_ENV_INIT_TIMEOUT:-120}
      PLUGIN_MAX_EXECUTION_TIMEOUT: ${PLUGIN_MAX_EXECUTION_TIMEOUT:-600}
      PIP_MIRROR_URL: ${PIP_MIRROR_URL:-}
      PLUGIN_STORAGE_TYPE: ${PLUGIN_STORAGE_TYPE:-local}
      PLUGIN_STORAGE_LOCAL_ROOT: ${PLUGIN_STORAGE_LOCAL_ROOT:-/app/storage}
      PLUGIN_INSTALLED_PATH: ${PLUGIN_INSTALLED_PATH:-plugin}
      PLUGIN_PACKAGE_CACHE_PATH: ${PLUGIN_PACKAGE_CACHE_PATH:-plugin_packages}
      PLUGIN_MEDIA_CACHE_PATH: ${PLUGIN_MEDIA_CACHE_PATH:-assets}
      PLUGIN_STORAGE_OSS_BUCKET: ${PLUGIN_STORAGE_OSS_BUCKET:-}
      S3_USE_AWS: ${PLUGIN_S3_USE_AWS:-false}
      S3_USE_AWS_MANAGED_IAM: ${PLUGIN_S3_USE_AWS_MANAGED_IAM:-false}
      S3_ENDPOINT: ${PLUGIN_S3_ENDPOINT:-}
      S3_USE_PATH_STYLE: ${PLUGIN_S3_USE_PATH_STYLE:-false}
      AWS_ACCESS_KEY: ${PLUGIN_AWS_ACCESS_KEY:-}
      AWS_SECRET_KEY: ${PLUGIN_AWS_SECRET_KEY:-}
      AWS_REGION: ${PLUGIN_AWS_REGION:-}
      AZURE_BLOB_STORAGE_CONNECTION_STRING: ${PLUGIN_AZURE_BLOB_STORAGE_CONNECTION_STRING:-}
      AZURE_BLOB_STORAGE_CONTAINER_NAME: ${PLUGIN_AZURE_BLOB_STORAGE_CONTAINER_NAME:-}
      TENCENT_COS_SECRET_KEY: ${PLUGIN_TENCENT_COS_SECRET_KEY:-}
      TENCENT_COS_SECRET_ID: ${PLUGIN_TENCENT_COS_SECRET_ID:-}
      TENCENT_COS_REGION: ${PLUGIN_TENCENT_COS_REGION:-}
      ALIYUN_OSS_REGION: ${PLUGIN_ALIYUN_OSS_REGION:-}
      ALIYUN_OSS_ENDPOINT: ${PLUGIN_ALIYUN_OSS_ENDPOINT:-}
      ALIYUN_OSS_ACCESS_KEY_ID: ${PLUGIN_ALIYUN_OSS_ACCESS_KEY_ID:-}
      ALIYUN_OSS_ACCESS_KEY_SECRET: ${PLUGIN_ALIYUN_OSS_ACCESS_KEY_SECRET:-}
      ALIYUN_OSS_AUTH_VERSION: ${PLUGIN_ALIYUN_OSS_AUTH_VERSION:-v4}
      ALIYUN_OSS_PATH: ${PLUGIN_ALIYUN_OSS_PATH:-}
      VOLCENGINE_TOS_ENDPOINT: ${PLUGIN_VOLCENGINE_TOS_ENDPOINT:-}
      VOLCENGINE_TOS_ACCESS_KEY: ${PLUGIN_VOLCENGINE_TOS_ACCESS_KEY:-}
      VOLCENGINE_TOS_SECRET_KEY: ${PLUGIN_VOLCENGINE_TOS_SECRET_KEY:-}
      VOLCENGINE_TOS_REGION: ${PLUGIN_VOLCENGINE_TOS_REGION:-}


+ ssrf_proxy  ==>不能共享，放到docker-compose中
ubuntu/squid:latest

SSRF_HTTP_PORT=3128
SSRF_COREDUMP_DIR=/var/spool/squid
SSRF_REVERSE_PROXY_PORT=8194
SSRF_SANDBOX_HOST=sandbox

#### 启动方式
+ sudo docker start redis postgres minio dify-web  qdrant

+ cd docker
  sudo docker-compose -f docker-compose.middleware_local.yaml up -d

+ cd api 
  + 变量   /home/eva/.local/bin/env
  + 启动backend 
  source venv/bin/activate
  uv run flask run --host 0.0.0.0 --port=5001 --debug
  
  + 启动task
  uv run celery -A app.celery worker -P gevent -c 1 --loglevel INFO -Q dataset,generation,mail,ops_trace

## 扩展dify，增加接口以支持openAi标准备接口，对接open-webui

+ dify 接口
curl -X POST 'http://192.168.1.3:5001/v1/chat-messages' \
--header 'Authorization: Bearer app-SS8K6ys44gFHwApHzKNXzMRS' \
--header 'Content-Type: application/json' \
--data-raw '{
    "inputs": {},
    "query": "What are the specs of the iPhone 13 Pro Max?",
    "response_mode": "streaming",
    "conversation_id": "",
    "user": "abc-123",
    "files": [
      {
        "type": "image",
        "transfer_method": "remote_url",
        "url": "https://cloud.dify.ai/logo/logo-site.png"
      }
    ]
}'

+ ## 客服一 
  + token中包含app_id
  {
  "iss": "66bd460f-a38c-45d7-b53c-1c6114d2cbe1",
  "sub": "Web API Passport",
  "app_id": "66bd460f-a38c-45d7-b53c-1c6114d2cbe1",
  "app_code": "e6sE0RcNi77vVMgp",
  "end_user_id": "a8ce120b-9fbb-448d-b396-dc3bcc5ab7ac"
}
+ 请求
curl -X POST 'http://192.168.1.3:5001/api/chat-messages' --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2NmJkNDYwZi1hMzhjLTQ1ZDctYjUzYy0xYzYxMTRkMmNiZTEiLCJzdWIiOiJXZWIgQVBJIFBhc3Nwb3J0IiwiYXBwX2lkIjoiNjZiZDQ2MGYtYTM4Yy00NWQ3LWI1M2MtMWM2MTE0ZDJjYmUxIiwiYXBwX2NvZGUiOiJlNnNFMFJjTmk3N3ZWTWdwIiwiZW5kX3VzZXJfaWQiOiJhOGNlM            MTIwYi05ZmJiLTQ0OGQtYjM5Ni1kYzNiY2M1YWI3YWMifQ.0rhfdNOsyAz7QPVp7vj71l-v1LDQlRrT_2hhjYB5WVM' --header 'Content-Type: application/json' --data-raw '{

    "inputs": {},
    "parent_message_id":null,
    "query": "你是谁?",
    "response_mode": "streaming",
    "conversation_id": "",
    "user": "abc-123",
    "files": [
      {
        "type": "image",
        "transfer_method": "remote_url",
        "url": "https://cloud.dify.ai/logo/logo-site.png"
      }
    ]
}'


+ ## 分析接口 
+ api/controllers/console/feature.py 不需要登录
    http://192.168.1.3:5001/console/api/system-features

+ api/controllers/service_api/index.py
   http://192.168.1.3:5001/v1/
+ api/controllers/open_ai/index.py
试下 http://192.168.1.3:5001/api/v1/models
### 增加controller 
+ 修改 api/extensions/ext_blueprints.py 增加新增controller
 + + 获取所有模型 http://192.168.1.3:5001/open_ai/api/models 
 + + 消息 http://192.168.1.3:5001/open_ai/api/chat/completions 