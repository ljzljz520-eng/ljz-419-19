# 企业级微服务应用系统

基于微服务架构的企业级应用系统，后端使用 FastAPI，前端使用 Vue3，数据库为 PostgreSQL，API 网关为 Kong。

## 🛠 技术栈

- **Frontend**: Vue3 + Element Plus + Vite
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **Service Layer**: Protocol 接口抽象 + 可替换实现
- **Database**: PostgreSQL 15 + Pgpool
- **API Gateway**: Kong 3.5（双实例直连对外暴露）
- **Service Discovery / Config**: Consul（服务注册 + KV 配置中心）
- **Monitoring**: Prometheus + Grafana + 健康检查 + Exporter
- **Logging**: Structlog JSON 结构化日志
- **Communication**: HTTP/REST + gRPC（支持 TLS/mTLS）
- **CI/CD**: GitHub Actions（CI + 镜像发布 + 远端部署）

## 🏗 架构与高可用

### 网关层

- `kong-1`：对外 `8000/8001`
- `kong-2`：对外 `8002/8003`
- 不再使用 Nginx 作为 Kong 前置入口，网关能力由 Kong 原生提供。

### 数据库层

- `postgres-primary` + `postgres-replica` 主从
- `postgres-pool-1`（`5432`）+ `postgres-pool-2`（`5433`）双 Pgpool 入口
- 应用内通过 `postgres` 别名访问双 Pgpool，降低单点风险。

### 服务治理

- Consul 负责服务注册与健康检查（`scripts/consul/config/services.json`）
- Consul KV 负责用户服务动态配置（`scripts/consul/bootstrap.sh`）
- 用户服务启动时会读取 Consul 配置覆盖环境变量。

### 监控

- Prometheus 抓取：
  - User Service `/metrics`
  - Kong Admin `/metrics`
  - Consul metrics
  - PostgreSQL exporter
- Grafana 预置 Prometheus 数据源。

## 🚀 启动

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

## 🔗 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| Frontend | http://localhost:3000 | 前端入口 |
| Kong Gateway #1 | http://localhost:8000 | 网关入口 1 |
| Kong Admin #1 | http://localhost:8001 | 管理口 1 |
| Kong Gateway #2 | http://localhost:8002 | 网关入口 2 |
| Kong Admin #2 | http://localhost:8003 | 管理口 2 |
| User Service #1 (HTTP) | http://localhost:8010/docs | Swagger |
| User Service #2 (HTTP) | http://localhost:8011/docs | 副本 |
| User Service #1 (gRPC TLS) | localhost:50051 | gRPC |
| User Service #2 (gRPC TLS) | localhost:50052 | gRPC 副本 |
| PostgreSQL Pgpool #1 | localhost:5432 | DB 入口 1 |
| PostgreSQL Pgpool #2 | localhost:5433 | DB 入口 2 |
| Consul UI | http://localhost:8500 | 服务发现/配置 |
| Prometheus | http://localhost:9090 | 指标采集 |
| Grafana | http://localhost:3001 | 可视化 |

## 🔐 安全与一致性

- gRPC 服务端默认支持 TLS，支持可选 mTLS。
- 用户服务数据库使用独立 schema：`user_service`。
- HTTP 异常（含 `HTTPException` 与 422 校验错误）统一输出：
  - `success`
  - `message`
  - `error_code`
  - `details`
  - `timestamp`

## 📁 关键目录

```text
.
├── docker-compose.yml
├── .github/workflows/ci-cd.yml
├── kong/kong.yml
├── scripts/
│   ├── init-db.sql
│   ├── consul/
│   │   ├── bootstrap.sh
│   │   └── config/services.json
│   ├── monitoring/
│   │   ├── prometheus.yml
│   │   └── grafana/provisioning/
│   └── postgres/
├── services/user-service/
│   ├── app/
│   └── certs/                 # 开发用 TLS/mTLS 证书（示例）
└── frontend/
```

## 🧪 测试

```bash
cd services/user-service
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing
```

## ⚙️ CI/CD

`/.github/workflows/ci-cd.yml` 当前流水线包含：

1. 代码质量检查
2. 后端/前端测试
3. Docker 构建
4. Compose 集成测试（含 HA 验证）
5. 主分支发布镜像到 GHCR
6. 通过 SSH 远程执行 Docker Compose 部署

部署阶段需配置以下 GitHub Secrets：

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PATH`
- `DEPLOY_REGISTRY_USERNAME`
- `DEPLOY_REGISTRY_TOKEN`

## ❓ 常见问题

**Q: Kong 路由不生效？**  
A: 检查 `http://localhost:8001/status` 与 `http://localhost:8003/status`。

**Q: 数据库连接异常？**  
A: 检查 `docker compose logs postgres-pool-1 postgres-pool-2`。

**Q: gRPC TLS 启动失败？**  
A: 检查证书是否存在于 `services/user-service/certs`，并确认 `.env` 中 TLS 开关配置。
