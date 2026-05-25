#!/usr/bin/env python3
"""Fly GEO Agent — Vercel Serverless API."""

import os
import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Fly GEO Agent", version="1.0.0")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
PROVIDER_ADDRESS = "0x5460BeEd186E1b3786713AFf6eD71962C1CBE931"

GEO_PACKAGES = {
    "starter": {"name": "GEO诊断尝鲜", "price": 9.9, "currency": "USDT"},
    "basic": {"name": "基础GEO优化", "price": 59, "currency": "USDT"},
    "pro": {"name": "深度GEO代运营", "price": 299, "currency": "USDT"},
    "enterprise": {"name": "全托管代运营", "price": 999, "currency": "USDT"},
}

SYSTEM_PROMPT = """你是Fly GEO Agent，专业的本地商家AI搜索可见性诊断专家。
根据店铺信息生成GEO诊断报告。核心要求：
1. Markdown格式
2. 包含：店铺信息表、AI搜索可见性评分(1-10)、各平台覆盖诊断、优化建议
3. 针对该行业和地区给出精准建议
4. 每个建议具体到可执行步骤
5. 中文，专业易懂，不用技术术语
6. 不出现Web3/链上/合约/区块链等术语
7. 结尾加：*本报告由 Fly GEO Agent 生成 | fly-agent.xyz*
套餐区分：starter=5条建议, basic=10条+执行计划, pro=15条+月度计划+竞品分析, enterprise=20条+季度计划+专人方案"""

class GEODiagnosisRequest(BaseModel):
    store_name: str
    industry: str = ""
    address: str = ""
    contact: str = ""
    website: str = ""
    package_type: str = "starter"

@app.get("/")
async def root():
    return {
        "service": "Fly GEO Agent",
        "version": "1.0.0",
        "provider": PROVIDER_ADDRESS,
        "network": "BSC Mainnet",
        "deepseek_configured": bool(DEEPSEEK_API_KEY),
        "endpoints": {"/health": "健康检查", "/geo-diagnosis": "GEO诊断", "/packages": "套餐列表"}
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "fly-geo-agent", "version": "1.0.0",
            "provider": PROVIDER_ADDRESS, "deepseek_configured": bool(DEEPSEEK_API_KEY),
            "timestamp": datetime.now().isoformat()}

@app.get("/packages")
async def list_packages():
    return {"packages": GEO_PACKAGES, "default_currency": "USDT", "network": "BSC Mainnet"}

@app.post("/geo-diagnosis")
async def geo_diagnosis(request: GEODiagnosisRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="DeepSeek API not configured")
    now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    user_prompt = f"""请为以下店铺生成GEO诊断报告。
店铺：{request.store_name} | 行业：{request.industry} | 地址：{request.address}
联系：{request.contact} | 网站：{request.website} | 套餐：{request.package_type}
生成时间：{now}"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={"model": DEEPSEEK_MODEL, "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ], "max_tokens": 3000, "temperature": 0.7})
            resp.raise_for_status()
            report = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DeepSeek error: {e}")
    return {"success": True, "package_type": request.package_type,
            "store_name": request.store_name, "report": report,
            "metadata": {"agent": "fly-geo-agent", "generated_at": datetime.now().isoformat(),
                         "provider": PROVIDER_ADDRESS}}
