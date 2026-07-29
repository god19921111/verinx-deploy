# VerinX

## 后端部署
- 平台：Hugging Face Spaces（不要卡号，16GB内存）
- Space name: verinx-api
- SDK: Docker
- Visibility: Public

环境变量（在 Space Settings → Repository secrets）：
- ZHIPU_API_KEY = b9d4a116e2f54a3b88d68d2750408821.KSzPr0DkEWY3VwfB
- JWT_SECRET_KEY = verinx-secret-2026-xyz-very-strong
- CORS_ALLOW_ORIGINS = https://verinx.vercel.app

## 前端部署
- 平台：Vercel
- 链接：https://vercel.com/new/clone?repository-url=https://github.com/god19921111/verinx-deploy&root-directory=frontend&env=VITE_API_BASE_URL
- 环境变量 VITE_API_BASE_URL 填后端地址 + /api
