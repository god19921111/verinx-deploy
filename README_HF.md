---
title: VerinX API
emoji: 🚀
colorFrom: dark
colorTo: gray
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: mit
---

# VerinX · AI 全真面试模拟

后端 API 服务，基于 FastAPI + 智谱 GLM-4-Flash + FunASR。

## 环境变量

在 Space Settings → Repository secrets 中添加：
- `ZHIPU_API_KEY`：智谱 API Key
- `JWT_SECRET_KEY`：随机密钥
- `CORS_ALLOW_ORIGINS`：前端域名
