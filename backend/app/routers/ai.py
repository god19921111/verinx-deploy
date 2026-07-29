"""AI服务路由"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    TTSRequest,
    ASRRequest,
    ScoreRequest,
    FollowUpQuestionRequest,
)
from app.services.scoring import ScoreService
from app.services.followup import FollowUpService
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("/tts")
async def text_to_speech(
    body: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """文字转语音"""
    if not settings.TTS_API_KEY or not settings.TTS_API_URL:
        return {
            "audio_url": f"/uploads/tts/mock_{hash(body.text) % 10000}.mp3",
            "duration": len(body.text) * 0.3 / body.speed,
            "status": "mock",
        }

    import httpx
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                settings.TTS_API_URL,
                json={"text": body.text, "speed": body.speed},
                headers={"Authorization": f"Bearer {settings.TTS_API_KEY}"},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"TTS服务调用失败: {str(e)}",
            )


@router.post("/asr")
async def speech_to_text(
    body: ASRRequest,
    current_user: User = Depends(get_current_user),
):
    """语音转文字（优先使用FunASR离线识别，fallback到Vosk）"""
    import httpx
    from pathlib import Path

    # 优先使用 FunASR 离线语音识别（完全免费、中文识别率高、支持多格式）
    if body.audio_url:
        try:
            text = await _funasr_asr(body.audio_url)
            if text:
                return {
                    "text": text,
                    "confidence": 0.95,
                    "duration": body.audio_duration or 60.0,
                    "audio_url": body.audio_url,
                    "status": "funasr",
                }
        except Exception as e:
            print(f"FunASR语音识别失败: {e}")

    # Fallback: Vosk 离线语音识别（免费、无需API Key，支持WAV格式）
    if body.audio_url:
        try:
            text = await _vosk_asr(body.audio_url)
            if text:
                return {
                    "text": text,
                    "confidence": 0.90,
                    "duration": body.audio_duration or 60.0,
                    "audio_url": body.audio_url,
                    "status": "vosk",
                }
        except Exception as e:
            print(f"Vosk语音识别失败: {e}")

    # 使用百度语音识别（国内速度快，每天5万次免费额度）
    if settings.BAIDU_API_KEY and settings.BAIDU_SECRET_KEY and body.audio_url:
        try:
            text = await _baidu_asr(body.audio_url)
            if text:
                return {
                    "text": text,
                    "confidence": 0.95,
                    "duration": body.audio_duration or 60.0,
                    "audio_url": body.audio_url,
                    "status": "baidu",
                }
        except Exception as e:
            print(f"百度语音识别失败: {e}")

    # 使用讯飞语音识别
    if settings.XFYUN_APP_ID and settings.XFYUN_API_KEY and settings.XFYUN_API_SECRET and body.audio_url:
        try:
            text = await _xfyun_asr(body.audio_url)
            if text:
                return {
                    "text": text,
                    "confidence": 0.95,
                    "duration": body.audio_duration or 60.0,
                    "audio_url": body.audio_url,
                    "status": "xfyun",
                }
        except Exception as e:
            print(f"讯飞语音识别失败: {e}")

    # 使用豆包ASR API
    if settings.DOUBAO_API_KEY and body.audio_url:
        async with httpx.AsyncClient() as client:
            try:
                audio_resp = await client.get(body.audio_url, timeout=30.0)
                audio_content = audio_resp.content

                import base64
                audio_b64 = base64.b64encode(audio_content).decode("utf-8")

                resp = await client.post(
                    "https://api.doubao.com/v1/audio/transcriptions",
                    json={
                        "model": "whisper-1",
                        "audio": audio_b64,
                        "language": "zh",
                        "response_format": "json",
                    },
                    headers={"Authorization": f"Bearer {settings.DOUBAO_API_KEY}"},
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                if "text" in data:
                    return {
                        "text": data["text"],
                        "confidence": data.get("confidence", 0.90),
                        "duration": body.audio_duration or 60.0,
                        "audio_url": body.audio_url,
                        "status": "doubao",
                    }
            except httpx.HTTPError as e:
                pass

    # 通用ASR API
    if settings.ASR_API_KEY and settings.ASR_API_URL:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    settings.ASR_API_URL,
                    json={"audio_url": body.audio_url, "audio_duration": body.audio_duration},
                    headers={"Authorization": f"Bearer {settings.ASR_API_KEY}"},
                    timeout=60.0,
                )
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ASR服务调用失败: {str(e)}",
                )

    # Mock 模式：返回提示用户配置API的信息
    return {
        "text": "（语音识别结果 - FunASR模型加载失败，请检查模型依赖或联系管理员）",
        "confidence": 0.95,
        "duration": body.audio_duration or 60.0,
        "audio_url": body.audio_url,
        "status": "mock",
    }


_vosk_model = None


def _get_vosk_model():
    """懒加载 Vosk 中文模型"""
    global _vosk_model
    if _vosk_model is None:
        import os
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models",
            "vosk-model-small-cn-0.22",
        )
        if not os.path.exists(model_path):
            return None
        from vosk import Model
        _vosk_model = Model(model_path)
    return _vosk_model


async def _vosk_asr(audio_url: str) -> str:
    """Vosk 离线语音识别（免费、无需API Key）"""
    import json
    import os
    import tempfile
    import wave

    import httpx

    model = _get_vosk_model()
    if model is None:
        return ""

    # 获取音频数据：支持本地路径和完整URL
    if audio_url.startswith("/uploads/"):
        # 本地文件，直接读取
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            audio_url.lstrip("/"),
        )
        with open(local_path, "rb") as f:
            audio_data = f.read()
    else:
        # 完整URL，用httpx下载
        async with httpx.AsyncClient() as client:
            resp = await client.get(audio_url, timeout=30.0)
            audio_data = resp.content

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        wf = wave.open(tmp_path, "rb")
        from vosk import KaldiRecognizer

        rec = KaldiRecognizer(model, wf.getframerate())
        text = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text += result.get("text", "")
        final = json.loads(rec.FinalResult())
        text += final.get("text", "")
        wf.close()
        return text
    finally:
        os.unlink(tmp_path)


_funasr_model = None


def _get_funasr_model():
    """懒加载 FunASR SenseVoice 轻量模型（完全离线，无需网络）"""
    global _funasr_model
    if _funasr_model is None:
        try:
            from funasr import AutoModel
            # 使用阿里 SenseVoiceSmall 轻量模型，参数量小，推理快
            _funasr_model = AutoModel(
                model="iic/SenseVoiceSmall",
                vad_model="fsmn-vad",
                punc_model="ct-punc-c",
                device="cpu",
                disable_pbar=True,
                disable_log=True,
            )
            print("[FunASR SenseVoice] 模型加载成功")
        except Exception as e:
            print(f"[FunASR SenseVoice] 模型加载失败: {e}")
            return None
    return _funasr_model


async def _funasr_asr(audio_url: str) -> str:
    """FunASR SenseVoice 离线语音识别（支持wav/webm/mp3等常见格式）"""
    import asyncio
    import os
    import tempfile

    import httpx

    model = _get_funasr_model()
    if model is None:
        return ""

    # 获取音频数据
    if audio_url.startswith("/uploads/"):
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            audio_url.lstrip("/"),
        )
        audio_path = local_path
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.get(audio_url, timeout=30.0)
            audio_data = resp.content
        ext = os.path.splitext(audio_url)[1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_data)
            audio_path = tmp.name

    try:
        # FunASR 是同步推理，放到线程池执行避免阻塞事件循环
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: model.generate(input=audio_path, batch_size_s=300))

        if result and len(result) > 0:
            text = result[0].get("text", "")
            return text.strip()
        return ""
    finally:
        # 只删除我们创建的临时文件
        if not audio_url.startswith("/uploads/") and os.path.exists(audio_path):
            os.unlink(audio_path)


_baidu_token = None
_baidu_token_expire = 0


async def _get_baidu_token() -> str:
    """获取百度语音识别 access_token（缓存30天）"""
    global _baidu_token, _baidu_token_expire
    import time

    if _baidu_token and _baidu_token_expire > time.time():
        return _baidu_token

    import httpx

    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": settings.BAIDU_API_KEY,
        "client_secret": settings.BAIDU_SECRET_KEY,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params, timeout=10.0)
        data = resp.json()
        _baidu_token = data.get("access_token", "")
        _baidu_token_expire = time.time() + data.get("expires_in", 2592000) - 300
        return _baidu_token


async def _baidu_asr(audio_url: str) -> str:
    """百度语音识别（支持wav/pcm/amr/m4a格式，采样率16000）"""
    import base64
    import json
    import os

    import httpx

    # 检查音频格式是否支持
    ext = os.path.splitext(audio_url)[1].lower().lstrip(".")
    # 百度支持的格式: wav, pcm, amr, m4a
    if ext not in ("wav", "pcm", "amr", "m4a"):
        print(f"百度语音识别: 不支持的格式 '{ext}', 跳过")
        return ""

    token = await _get_baidu_token()
    if not token:
        return ""

    # 读取音频数据
    if audio_url.startswith("/uploads/"):
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            audio_url.lstrip("/"),
        )
        with open(local_path, "rb") as f:
            audio_data = f.read()
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.get(audio_url, timeout=30.0)
            audio_data = resp.content

    audio_b64 = base64.b64encode(audio_data).decode("utf-8")

    url = f"https://vop.baidu.com/server_api?dev_pid=1537&cuid=gongkaoxing&token={token}"
    payload = {
        "format": ext,
        "rate": 16000,
        "channel": 1,
        "cuid": "gongkaoxing",
        "speech": audio_b64,
        "len": len(audio_data),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        result = resp.json()
        if result.get("err_no") == 0:
            return result.get("result", [""])[0]
        else:
            print(f"百度语音识别错误: {result}")
            return ""


async def _xfyun_asr(audio_url: str) -> str:
    """讯飞语音识别（一句话识别REST API）"""
    import base64
    import hashlib
    import hmac
    import json
    import time
    from datetime import datetime
    from urllib.parse import urlencode

    import httpx

    audio_resp = await httpx.AsyncClient().get(audio_url, timeout=30.0)
    audio_content = audio_resp.content

    audio_b64 = base64.b64encode(audio_content).decode("utf-8")

    # 讯飞一句话识别 API
    url = "https://api.xfyun.cn/v1/service/v1/iat"

    # 生成鉴权参数
    cur_time = str(int(time.time()))
    param = {
        "engine_type": "sms16k",
        "aue": "raw",
    }
    param_b64 = base64.b64encode(json.dumps(param).encode("utf-8")).decode("utf-8")

    check_sum_origin = settings.XFYUN_API_SECRET + cur_time + param_b64
    check_sum = hashlib.sha1(check_sum_origin.encode("utf-8")).hexdigest()

    headers = {
        "X-Appid": settings.XFYUN_APP_ID,
        "X-CurTime": cur_time,
        "X-Param": param_b64,
        "X-CheckSum": check_sum,
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }

    data = {
        "audio": audio_b64,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, data=data, timeout=30.0)
        result = resp.json()
        if result.get("code") == "0" and "data" in result:
            return result["data"]
        else:
            print(f"讯飞ASR返回错误: {result}")
            return ""


@router.post("/score")
async def score_answer(
    body: ScoreRequest,
    current_user: User = Depends(get_current_user),
):
    """AI五维评分"""
    service = ScoreService()
    result = await service.score(
        question_content=body.question_content,
        answer_text=body.answer_text,
        question_category=body.question_category,
    )
    return result


@router.post("/follow-up")
async def generate_follow_up(
    body: FollowUpQuestionRequest,
    current_user: User = Depends(get_current_user),
):
    """AI生成追问"""
    if body.round_number > settings.MAX_FOLLOW_UP_PER_SESSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"追问轮次不能超过{settings.MAX_FOLLOW_UP_PER_SESSION}轮",
        )

    service = FollowUpService()
    result = await service.generate(
        question_content=body.question_content,
        answer_text=body.answer_text,
        question_category=body.question_category,
        round_number=body.round_number,
    )
    return result


@router.post("/generate-question")
async def generate_question(
    category: str = "综合分析",
    exam_type: str = "国考",
    province: str = "",
    random_category: bool = False,
    use_search: bool = True,
    current_user: User = Depends(get_current_user),
):
    """使用AI生成面试题目（优先网络搜索最新真题，fallback智谱GLM，再fallback豆包）"""
    import json
    import random
    import re

    categories = ["综合分析", "人际沟通", "应急应变", "组织管理", "自我认知"]

    if random_category:
        category = random.choice(categories)

    # 优先从缓存池获取（毫秒级响应）
    from app.services.question_pool import get_question_pool
    pool = get_question_pool()

    cached = pool.get_question(category, exam_type, province)
    if cached:
        print(f"[出题] 缓存池命中: {category}, 剩余{pool.get_pool_status()[category]}道")
        return cached

    # 缓存池为空，尝试搜索生成
    if use_search:
        try:
            from app.services.search_service import SearchService
            search_service = SearchService()
            search_result = await search_service.generate_question_with_search(category, exam_type, province)
            if search_result:
                print(f"[出题] 网络搜索成功获取题目: {category}")
                return search_result
        except Exception as e:
            print(f"[出题] 网络搜索失败，回退到AI生成: {e}")

    hot_topics = [
        "高质量发展", "乡村振兴", "数字经济", "科技创新", "共同富裕",
        "碳中和", "教育改革", "医疗健康", "就业创业", "社会治理",
        "文化自信", "生态文明", "一带一路", "民生保障", "基层治理",
        "数据安全", "人工智能", "新能源", "老龄化", "青年发展",
    ]

    random_topics = random.sample(hot_topics, 3)

    topic_descriptions = {
        "高质量发展": "经济转型升级、产业升级、创新驱动",
        "乡村振兴": "农村发展、农业现代化、农民增收",
        "数字经济": "数字产业、数字化转型、数据要素",
        "科技创新": "关键核心技术攻关、科技自立自强",
        "共同富裕": "收入分配、公平正义、社会均衡",
        "碳中和": "绿色发展、节能减排、低碳生活",
        "教育改革": "双减政策、素质教育、教育公平",
        "医疗健康": "医药改革、公共卫生、健康中国",
        "就业创业": "就业优先、创业扶持、灵活就业",
        "社会治理": "基层治理、网格化管理、矛盾化解",
        "文化自信": "传统文化传承、文化创新、文化软实力",
        "生态文明": "生态保护、美丽中国、可持续发展",
        "一带一路": "对外开放、国际合作、互联互通",
        "民生保障": "社会保障、住房保障、公共服务",
        "基层治理": "社区治理、乡村治理、精细化管理",
        "数据安全": "网络安全、数据保护、个人隐私",
        "人工智能": "AI应用、智能化、人机协作",
        "新能源": "清洁能源、新能源汽车、储能技术",
        "老龄化": "养老服务、银发经济、健康养老",
        "青年发展": "青年就业、青年成长、人才培养",
    }

    category_templates = {
        "综合分析": [
            "请谈谈你对'{topic}'的理解，结合实际分析其重要意义和实现路径。",
            "{topic}已成为当前社会关注的热点，请你分析其面临的挑战及应对策略。",
            "如何看待'{topic}'在新时代背景下的发展趋势？请谈谈你的认识。",
            "请结合'{topic}'的发展现状，分析其对经济社会发展的影响。",
            "'{topic}'是当前工作的重点，请谈谈你对推进这项工作的思考。",
        ],
        "人际沟通": [
            "你在工作中与同事意见分歧较大，对方坚持自己的观点，你怎么办？",
            "领导安排你接手同事未完成的工作，但同事态度不配合，你如何处理？",
            "群众来办事时情绪激动，对办理结果不满意，你如何安抚并解决问题？",
            "你作为新人，老同事总是把琐碎工作推给你，你如何处理？",
            "跨部门协作中，其他部门不配合你的工作，你如何沟通协调？",
        ],
        "应急应变": [
            "你负责组织的重要活动突然遇到恶劣天气，活动无法按原计划进行，你怎么办？",
            "你正在处理群众投诉时，又有新的群众情绪激动地赶来，你如何应对？",
            "单位突发网络安全事件，数据面临泄露风险，你作为值班人员如何处理？",
            "你在会议上汇报工作时，发现PPT内容有误，你如何处理？",
            "领导交办的紧急任务与你手头的重要工作时间冲突，你怎么办？",
        ],
        "组织管理": [
            "单位让你组织一次'{topic}'主题宣传活动，你如何组织？",
            "领导要求你组织一次'{topic}'专题调研，你会如何开展？",
            "请你策划一场'{topic}'主题的青年论坛活动，谈谈你的方案。",
            "上级要来检查工作，领导让你负责接待和汇报，你如何准备？",
            "如何组织开展'{topic}'相关的培训活动？请谈谈你的思路。",
        ],
        "自我认知": [
            "请介绍一下你的经历，以及这些经历如何帮助你胜任这个岗位？",
            "你认为自己最大的优势是什么？这些优势如何在工作中发挥作用？",
            "如果工作中遇到挫折，你会如何调整心态？请结合实例说明。",
            "请谈谈你对'{topic}'的理解，以及你将如何在工作中践行？",
            "你为什么选择报考我们单位？你的职业规划是什么？",
        ],
    }

    topic = random.choice(random_topics)
    topic_desc = topic_descriptions.get(topic, "")
    
    templates = category_templates.get(category, category_templates["综合分析"])
    random_template = random.choice(templates)
    
    topic_context = f"\n【背景素材】{topic}：{topic_desc}"

    prompt = f"""你是一位资深公考面试出题专家，精通{exam_type}面试命题规律。请根据以下要求生成【仅一道】高质量面试题目：

【题目类型】{category}
【考试类型】{exam_type}
{province and f"【省份】{province}" or ""}
【参考话题】{topic}
{topic_desc and f"【话题背景】{topic_desc}" or ""}

命题要求（严格遵守）：
1. 题目必须紧扣{category}的考察要点，具有针对性
2. 结合{topic}相关的时政热点或社会现象，确保时效性和现实意义
3. 难度1-5星，根据题目复杂度合理设置
4. 参考答案思路要简明扼要，给出答题框架和关键点
5. 严禁生成多道题目，只生成一道题

参考题型示例（仅供参考，不要照搬）：
{random_template}

请严格按以下单个JSON对象格式返回（最外层只能有一对花括号，不要包含任何其他文本、代码块或解释）：
{{
    "content": "这道题的完整题目内容",
    "difficulty": 3,
    "answer_reference": "参考答案思路"
}}"""

    async def call_zhipu():
        """调用智谱GLM生成题目"""
        import time
        import jwt as jwt_lib
        import httpx

        api_key = settings.ZHIPU_API_KEY
        kid, secret = api_key.split(".")
        payload = {
            "api_key": kid,
            "exp": int(time.time()) + 3600,
            "timestamp": int(time.time()),
        }
        token = jwt_lib.encode(
            payload, secret, algorithm="HS256", headers={"alg": "HS256", "sign_type": "SIGN"}
        )

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                json={
                    "model": "glm-4-flash",
                    "messages": [
                        {"role": "system", "content": "你是一位资深公考面试出题专家，擅长生成高质量的公务员面试题目。请严格按照JSON格式返回结果。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def call_doubao():
        """调用豆包生成题目"""
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.DOUBAO_API_URL,
                json={
                    "model": settings.LLM_MODEL or "doubao-pro",
                    "messages": [
                        {"role": "system", "content": "你是一位资深公考面试出题专家，擅长生成高质量的公务员面试题目。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                },
                headers={"Authorization": f"Bearer {settings.DOUBAO_API_KEY}"},
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            elif "output" in data:
                return data["output"]
            return str(data)

    # 优先调用智谱GLM
    response_text = ""
    engine = "mock"
    if settings.ZHIPU_API_KEY:
        try:
            response_text = await call_zhipu()
            engine = "zhipu"
        except Exception as e:
            print(f"[出题] 智谱GLM调用失败: {e}")

    # fallback到豆包
    if not response_text and settings.DOUBAO_API_KEY:
        try:
            response_text = await call_doubao()
            engine = "doubao"
        except Exception as e:
            print(f"[出题] 豆包调用失败: {e}")

    # Mock兜底：增加丰富的题目库，避免重复
    if not response_text:
        mock_question_library = {
            "综合分析": [
                "请谈谈你对'高质量发展'的理解，结合实际分析其重要意义和实现路径。",
                "数字经济已成为当前社会关注的热点，请你分析其面临的挑战及应对策略。",
                "如何看待'乡村振兴'战略在新时代背景下的发展趋势？请谈谈你的认识。",
                "请结合'科技创新'的发展现状，分析其对经济社会发展的影响。",
                "'共同富裕'是当前工作的重点，请谈谈你对推进这项工作的思考。",
                "如何理解'碳中和'目标的重要性？结合实际谈谈如何实现这一目标。",
                "请分析'教育改革'面临的主要问题及解决思路。",
                "如何看待'人工智能'在政务服务中的应用前景？",
            ],
            "人际沟通": [
                "你在工作中与同事意见分歧较大，对方坚持自己的观点，你怎么办？",
                "领导安排你接手同事未完成的工作，但同事态度不配合，你如何处理？",
                "群众来办事时情绪激动，对办理结果不满意，你如何安抚并解决问题？",
                "你作为新人，老同事总是把琐碎工作推给你，你如何处理？",
                "跨部门协作中，其他部门不配合你的工作，你如何沟通协调？",
                "领导批评你的工作方案存在问题，但你认为自己的方案是正确的，你怎么办？",
                "同事在背后议论你的工作方式，你得知后如何处理？",
                "你负责的工作出现失误，导致其他同事的工作受到影响，你如何处理？",
            ],
            "应急应变": [
                "你负责组织的重要活动突然遇到恶劣天气，活动无法按原计划进行，你怎么办？",
                "你正在处理群众投诉时，又有新的群众情绪激动地赶来，你如何应对？",
                "单位突发网络安全事件，数据面临泄露风险，你作为值班人员如何处理？",
                "你在会议上汇报工作时，发现PPT内容有误，你如何处理？",
                "领导交办的紧急任务与你手头的重要工作时间冲突，你怎么办？",
                "你在基层工作时，遇到群体性事件苗头，你如何处理？",
                "单位重要文件丢失，领导让你负责调查处理，你怎么办？",
                "你陪同领导视察工作时，群众突然围上来反映问题，你如何应对？",
            ],
            "组织管理": [
                "单位让你组织一次'数字政府建设'主题宣传活动，你如何组织？",
                "领导要求你组织一次'营商环境优化'专题调研，你会如何开展？",
                "请你策划一场'青年干部成长'主题的论坛活动，谈谈你的方案。",
                "上级要来检查工作，领导让你负责接待和汇报，你如何准备？",
                "如何组织开展'安全生产'相关的培训活动？请谈谈你的思路。",
                "请你组织一次单位内部的'业务技能比武'活动，你如何安排？",
                "领导让你组织一次'我为群众办实事'实践活动，你如何策划？",
                "如何组织开展'党史学习教育'活动？请谈谈你的方案。",
            ],
            "自我认知": [
                "请介绍一下你的经历，以及这些经历如何帮助你胜任这个岗位？",
                "你认为自己最大的优势是什么？这些优势如何在工作中发挥作用？",
                "如果工作中遇到挫折，你会如何调整心态？请结合实例说明。",
                "请谈谈你对'为人民服务'的理解，以及你将如何在工作中践行？",
                "你为什么选择报考我们单位？你的职业规划是什么？",
                "请谈谈你的缺点，以及你如何改进？",
                "如果被录用，你如何快速适应新工作环境？",
                "请谈谈你在大学期间最有成就感的一件事。",
            ],
        }
        
        questions = mock_question_library.get(category, mock_question_library["综合分析"])
        random_question = random.choice(questions)
        
        return {
            "content": random_question,
            "difficulty": random.randint(2, 4),
            "answer_reference": "（请结合实际情况作答）",
            "category": category,
            "exam_type": exam_type,
            "province": province,
            "status": "mock",
        }

    # 解析返回结果：提取第一个平衡的JSON对象（避免贪婪匹配把多道题串在一起）
    def _extract_first_json(text: str):
        text = text.strip()
        # 去除可能的 ```json ... ``` 代码块包裹
        m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if m:
            text = m.group(1).strip()
        # 直接尝试解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 用括号平衡方式提取第一个完整JSON对象
        start = text.find('{')
        if start == -1:
            return None
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            return None
        return None

    parsed = _extract_first_json(response_text)
    if parsed and isinstance(parsed, dict) and parsed.get("content"):
        content = str(parsed["content"]).strip()
        
        if content.startswith("{"):
            try:
                inner_parsed = json.loads(content)
                if isinstance(inner_parsed, dict) and inner_parsed.get("content"):
                    content = str(inner_parsed["content"]).strip()
                    parsed["difficulty"] = inner_parsed.get("difficulty", parsed.get("difficulty", 3))
                    parsed["answer_reference"] = inner_parsed.get("answer_reference", parsed.get("answer_reference", ""))
            except json.JSONDecodeError:
                pass
        
        multi_match = re.split(r'(?:第[一二三四五六七八九十\d]+题|题目[一二三四五六七八九十\d]+[:：])', content)
        if len(multi_match) > 1:
            content = multi_match[1].strip() if multi_match[1].strip() else content
        return {
            "content": content,
            "difficulty": parsed.get("difficulty", 3),
            "answer_reference": parsed.get("answer_reference", ""),
            "category": category,
            "exam_type": exam_type,
            "province": province,
            "status": engine,
        }

    return {
        "content": response_text,
        "difficulty": 3,
        "answer_reference": "",
        "category": category,
        "exam_type": exam_type,
        "province": province,
        "status": engine,
    }
