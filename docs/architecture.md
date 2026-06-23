# Claude Code DevOps 自动化实训 — 架构文档

## 1. 概述

本项目演示如何借助 **Claude Code MCP（Model Context Protocol）** 实现 AI 辅助的全流程 DevOps 自动化。通过将 Claude Code 与 Git、文件系统、Docker、GitHub Actions 集成，构建一条从需求到部署的闭环流水线。

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        DevOps 自动化流水线                        │
├───────────┬───────────┬───────────┬───────────┬─────────────────┤
│  需求分析  │  AI 编码   │  MCP 操作  │  CI/CD    │    部署上线      │
│  (人工)   │ (Claude)  │ (File/Git) │ (Actions) │   (Docker)      │
├───────────┼───────────┼───────────┼───────────┼─────────────────┤
│ 原型设计   │ 代码生成   │ 文件管理   │ 静态扫描   │ 容器打包         │
│ 需求拆分   │ 代码审查   │ Git 操作   │ 单元测试   │ 镜像推送         │
│ 任务规划   │ 文档生成   │ 分支管理   │ 构建验证   │ 自动部署         │
└───────────┴───────────┴───────────┴───────────┴─────────────────┘
```

## 3. 技术栈

| 层级       | 技术                        | 说明                  |
|----------|---------------------------|---------------------|
| AI 引擎   | Claude Code + MCP         | 代码生成、审查、文件/Git 自动化 |
| 版本控制   | Git + GitHub              | 源码管理、分支策略、PR 流程     |
| CI/CD    | GitHub Actions            | 自动化构建、测试、部署流水线     |
| 容器化    | Docker                    | 应用打包、环境一致性         |
| 运行时    | Linux / Windows (WSL2)    | 开发与生产运行环境          |

## 4. MCP 集成设计

```
┌──────────────┐     MCP Protocol     ┌──────────────────┐
│  Claude Code  │ ◄──────────────────► │  MCP Servers      │
│  (AI 客户端)   │                      │                   │
└──────────────┘                      ├──────────────────┤
                                      │  • File MCP       │
                                      │    - 文件 CRUD     │
                                      │    - 目录管理       │
                                      │                   │
                                      │  • Git MCP        │
                                      │    - 状态查询       │
                                      │    - 提交/分支      │
                                      │    - diff/log      │
                                      └──────────────────┘
```

### 4.1 File MCP
- **功能**：文件和目录的创建、读取、更新、删除
- **用途**：批量生成项目文件、生成文档、配置文件管理

### 4.2 Git MCP
- **功能**：仓库状态查询、变更追踪、提交管理
- **用途**：自动化 Git 工作流、代码变更审计、分支操作

## 5. CI/CD 流水线 (GitHub Actions)

```yaml
# 触发条件：推送到 main/master 分支 或 创建 PR

name: DevOps Pipeline
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  static-analysis:    # 阶段1：静态代码扫描
  unit-test:          # 阶段2：单元测试
  docker-build:       # 阶段3：Docker 镜像构建
  deploy:             # 阶段4：自动部署
```

### 流水线阶段

1. **Static Analysis** — ESLint / Pylint / ShellCheck 代码质量检查
2. **Unit Test** — pytest / jest 等框架执行单元测试
3. **Docker Build** — 构建 Docker 镜像并推送至镜像仓库
4. **Deploy** — 拉取最新镜像并重启容器服务

## 6. 目录结构

```
project-root/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions 流水线定义
├── docs/
│   └── architecture.md        # 项目架构文档（本文件）
├── src/                       # 源代码目录
├── tests/                     # 测试目录
├── Dockerfile                 # Docker 镜像定义
├── .gitignore                 # Git 忽略规则
├── README.md                  # 项目说明
└── requirements.txt / package.json
```

## 7. 开发工作流

```
Developer Prompt
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Claude Code  │───►│  File MCP    │───►│  文件生成     │
│  (AI 处理)    │    │  Git MCP     │    │  代码编写     │
└─────────────┘    └─────────────┘    └─────────────┘
      │                                      │
      ▼                                      ▼
  AI 决策 & 执行                        git add/commit
      │                                      │
      └──────────────────┬───────────────────┘
                         ▼
                  git push → GitHub
                         │
                         ▼
                 GitHub Actions
                 (CI/CD 流水线)
                         │
                         ▼
                  Docker Deploy
```

## 8. 后续扩展

- [ ] 接入更多 MCP Server（数据库、云服务 API）
- [ ] 增加自动化测试覆盖率
- [ ] 集成 Kubernetes 部署
- [ ] 添加监控与告警（Prometheus + Grafana）
- [ ] 实现蓝绿部署 / 金丝雀发布策略
