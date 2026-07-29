"""LLM四维评分服务"""

import json
import re
from typing import Optional

from app.config import settings


CATEGORY_PROMPTS = {
    "综合分析": """你是一位资深公考面试考官。请认真阅读题目和考生回答，进行专业的四维评分。

【面试题目】
{question_content}

【考生回答】
{answer_text}

请从以下四个维度评分（0-100分）：

1. **综合分析能力**（权重30%）：对问题的分析深度、逻辑性、多角度思考、观点新颖性
2. **言语表达能力**（权重25%）：表达流畅度、条理清晰度、用词准确性、说服力
3. **应变能力**（权重25%）：思维灵活性、临场反应、对突发情况的处理思路
4. **计划组织协调能力**（权重20%）：方案系统性、可操作性、资源调配、步骤完整性

评分要求：
- 每个维度都必须结合题目要求和考生回答的具体内容进行分析
- 综合评价要指出回答的亮点和不足，引用具体例子说明
- 扣分项要具体指出哪些内容导致扣分，不要泛泛而谈
- 优化建议要实用、可操作，针对回答中的具体问题给出改进方向
- 语言风格要像资深考官的个性化点评，不要使用模板化套话
- 避免使用"考生在XX方面表现出色/不足"这类笼统表述，要具体说明

请严格按以下JSON格式返回，不要包含其他内容：
{{
    "score_analysis": <0-100整数>,
    "score_expression": <0-100整数>,
    "score_adaptability": <0-100整数>,
    "score_organization": <0-100整数>,
    "report_content": "<综合评价：结合题目和回答具体分析，指出亮点和不足>",
    "dimension_analysis": {{
        "analysis": "<针对综合分析维度的具体点评，引用回答中的具体内容>",
        "expression": "<针对言语表达维度的具体点评，分析表达特点>",
        "adaptability": "<针对应变能力维度的具体点评，分析思维灵活性>",
        "organization": "<针对计划组织协调维度的具体点评，分析方案完整性>"
    }},
    "deduction_points": "<具体扣分项，分点列出，每项说明具体扣分原因>",
    "optimization_suggestions": "<具体优化建议，分点列出，每项说明如何改进>"
}}""",

    "人际沟通": """你是一位资深公考面试考官。请认真阅读题目和考生回答，进行专业的四维评分。

【面试题目】
{question_content}

【考生回答】
{answer_text}

请从以下四个维度评分（0-100分）：

1. **综合分析能力**（权重30%）：对人际关系问题的理解深度、矛盾根源分析、各方利益考量
2. **言语表达能力**（权重25%）：沟通方式恰当性、措辞得体性、表达技巧运用
3. **应变能力**（权重25%）：面对人际冲突时的灵活应对、情绪管理能力
4. **计划组织协调能力**（权重20%）：沟通方案可操作性、多方协调策略、步骤合理性

评分要求：
- 每个维度都必须结合题目情境和考生回答的具体内容进行分析
- 综合评价要指出回答的亮点和不足，引用具体例子说明
- 扣分项要具体指出哪些内容导致扣分，不要泛泛而谈
- 优化建议要实用、可操作，针对回答中的具体问题给出改进方向
- 语言风格要像资深考官的个性化点评，不要使用模板化套话

请严格按以下JSON格式返回，不要包含其他内容：
{{
    "score_analysis": <0-100整数>,
    "score_expression": <0-100整数>,
    "score_adaptability": <0-100整数>,
    "score_organization": <0-100整数>,
    "report_content": "<综合评价：结合题目情境和回答具体分析，指出亮点和不足>",
    "dimension_analysis": {{
        "analysis": "<针对综合分析维度的具体点评，分析矛盾根源把握>",
        "expression": "<针对言语表达维度的具体点评，分析沟通方式>",
        "adaptability": "<针对应变能力维度的具体点评，分析冲突应对>",
        "organization": "<针对计划组织协调维度的具体点评，分析协调策略>"
    }},
    "deduction_points": "<具体扣分项，分点列出>",
    "optimization_suggestions": "<具体优化建议，分点列出>"
}}""",

    "应急应变": """你是一位资深公考面试考官。请认真阅读题目和考生回答，进行专业的四维评分。

【面试题目】
{question_content}

【考生回答】
{answer_text}

请从以下四个维度评分（0-100分）：

1. **综合分析能力**（权重30%）：对突发事件的分析判断、轻重缓急把握、问题本质理解
2. **言语表达能力**（权重25%）：应急情况下表达清晰度、条理性、关键信息传递
3. **应变能力**（权重25%）：应对策略灵活性、多方案准备、风险预判能力
4. **计划组织协调能力**（权重20%）：应急方案系统性、可执行性、资源调配效率

评分要求：
- 每个维度都必须结合题目情境和考生回答的具体内容进行分析
- 综合评价要指出回答的亮点和不足，引用具体例子说明
- 扣分项要具体指出哪些内容导致扣分，不要泛泛而谈
- 优化建议要实用、可操作，针对回答中的具体问题给出改进方向
- 语言风格要像资深考官的个性化点评，不要使用模板化套话

请严格按以下JSON格式返回，不要包含其他内容：
{{
    "score_analysis": <0-100整数>,
    "score_expression": <0-100整数>,
    "score_adaptability": <0-100整数>,
    "score_organization": <0-100整数>,
    "report_content": "<综合评价：结合题目情境和回答具体分析，指出亮点和不足>",
    "dimension_analysis": {{
        "analysis": "<针对综合分析维度的具体点评，分析问题判断>",
        "expression": "<针对言语表达维度的具体点评，分析应急表达>",
        "adaptability": "<针对应变能力维度的具体点评，分析方案灵活性>",
        "organization": "<针对计划组织协调维度的具体点评，分析方案执行>"
    }},
    "deduction_points": "<具体扣分项，分点列出>",
    "optimization_suggestions": "<具体优化建议，分点列出>"
}}""",

    "组织管理": """你是一位资深公考面试考官。请认真阅读题目和考生回答，进行专业的四维评分。

【面试题目】
{question_content}

【考生回答】
{answer_text}

请从以下四个维度评分（0-100分）：

1. **综合分析能力**（权重30%）：对活动目标的理解、需求分析深度、可行性评估
2. **言语表达能力**（权重25%）：方案描述条理性、重点突出程度、表达感染力
3. **应变能力**（权重25%）：预案设计、突发情况考虑、风险应对措施
4. **计划组织协调能力**（权重20%）：方案完整性、流程合理性、资源配置、时间管理

评分要求：
- 每个维度都必须结合题目要求和考生回答的具体内容进行分析
- 综合评价要指出回答的亮点和不足，引用具体例子说明
- 扣分项要具体指出哪些内容导致扣分，不要泛泛而谈
- 优化建议要实用、可操作，针对回答中的具体问题给出改进方向
- 语言风格要像资深考官的个性化点评，不要使用模板化套话

请严格按以下JSON格式返回，不要包含其他内容：
{{
    "score_analysis": <0-100整数>,
    "score_expression": <0-100整数>,
    "score_adaptability": <0-100整数>,
    "score_organization": <0-100整数>,
    "report_content": "<综合评价：结合题目要求和回答具体分析，指出亮点和不足>",
    "dimension_analysis": {{
        "analysis": "<针对综合分析维度的具体点评，分析目标理解>",
        "expression": "<针对言语表达维度的具体点评，分析方案描述>",
        "adaptability": "<针对应变能力维度的具体点评，分析预案设计>",
        "organization": "<针对计划组织协调维度的具体点评，分析方案完整性>"
    }},
    "deduction_points": "<具体扣分项，分点列出>",
    "optimization_suggestions": "<具体优化建议，分点列出>"
}}""",

    "自我认知": """你是一位资深公考面试考官。请认真阅读题目和考生回答，进行专业的四维评分。

【面试题目】
{question_content}

【考生回答】
{answer_text}

请从以下四个维度评分（0-100分）：

1. **综合分析能力**（权重30%）：自我认知深度、与岗位匹配度分析、职业规划合理性
2. **言语表达能力**（权重25%）：表达真诚度、流畅度、说服力、个人特色展现
3. **应变能力**（权重25%）：面对追问时的灵活应对、压力下的表达稳定性
4. **计划组织协调能力**（权重20%）：职业规划系统性、阶段性目标明确、执行路径清晰

评分要求：
- 每个维度都必须结合题目要求和考生回答的具体内容进行分析
- 综合评价要指出回答的亮点和不足，引用具体例子说明
- 扣分项要具体指出哪些内容导致扣分，不要泛泛而谈
- 优化建议要实用、可操作，针对回答中的具体问题给出改进方向
- 语言风格要像资深考官的个性化点评，不要使用模板化套话

请严格按以下JSON格式返回，不要包含其他内容：
{{
    "score_analysis": <0-100整数>,
    "score_expression": <0-100整数>,
    "score_adaptability": <0-100整数>,
    "score_organization": <0-100整数>,
    "report_content": "<综合评价：结合题目要求和回答具体分析，指出亮点和不足>",
    "dimension_analysis": {{
        "analysis": "<针对综合分析维度的具体点评，分析自我认知>",
        "expression": "<针对言语表达维度的具体点评，分析表达真诚度>",
        "adaptability": "<针对应变能力维度的具体点评，分析灵活应对>",
        "organization": "<针对计划组织协调维度的具体点评，分析职业规划>"
    }},
    "deduction_points": "<具体扣分项，分点列出>",
    "optimization_suggestions": "<具体优化建议，分点列出>"
}}""",
}

DEFAULT_PROMPT = CATEGORY_PROMPTS["综合分析"]


class ScoreService:
    """四维评分服务"""

    def _build_prompt(
        self, question_content: str, answer_text: str, question_category: str
    ) -> str:
        template = CATEGORY_PROMPTS.get(question_category, DEFAULT_PROMPT)
        return template.format(
            question_content=question_content,
            answer_text=answer_text,
        )

    def _parse_llm_response(self, response_text: str) -> dict:
        if not response_text:
            return self._get_default_scores()

        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                text = json_match.group()
                text = text.replace("'", '"')
                text = re.sub(r'(\w+):', r'"\1":', text)
                text = re.sub(r':\s*(\d+\.?\d*)', r': \1', text)
                text = re.sub(r':\s*"([^"]*)"', r': "\1"', text)

                try:
                    result = json.loads(text)
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    pass

            try:
                result = json.loads(response_text)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        except Exception:
            pass

        return self._get_default_scores()

    def _get_default_scores(self) -> dict:
        return {
            "score_analysis": 60,
            "score_expression": 60,
            "score_adaptability": 60,
            "score_organization": 60,
            "report_content": "评分解析异常，请重新评分",
            "dimension_analysis": {
                "analysis": "无法解析",
                "expression": "无法解析",
                "adaptability": "无法解析",
                "organization": "无法解析",
            },
            "deduction_points": "无法解析",
            "optimization_suggestions": "无法解析",
        }

    def _calculate_overall_score(self, scores: dict) -> float:
        return round(
            scores.get("score_analysis", 0) * settings.SCORE_WEIGHT_ANALYSIS
            + scores.get("score_expression", 0) * settings.SCORE_WEIGHT_EXPRESSION
            + scores.get("score_adaptability", 0) * settings.SCORE_WEIGHT_ADAPTABILITY
            + scores.get("score_organization", 0) * settings.SCORE_WEIGHT_ORGANIZATION,
            1,
        )

    async def _call_llm(self, prompt: str) -> str:
        import httpx
        import time
        import jwt as jwt_lib

        if settings.ZHIPU_API_KEY:
            try:
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
                                {"role": "system", "content": "你是一位经验丰富的公考面试考官，擅长从多个维度对考生回答进行深入细致的个性化点评。你会认真阅读题目和考生回答，给出具体、针对性的分析，而不是使用模板化的套话。请严格按照JSON格式返回结果。"},
                                {"role": "user", "content": prompt},
                            ],
                            "temperature": 0.7,
                        },
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=90.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"[评分] 智谱GLM调用失败: {e}")

        if settings.DOUBAO_API_KEY:
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        settings.DOUBAO_API_URL,
                        json={
                            "model": settings.LLM_MODEL or "doubao-pro",
                            "messages": [
                                {"role": "system", "content": "你是一位经验丰富的公考面试考官，擅长从多个维度对考生回答进行深入细致的个性化点评。"},
                                {"role": "user", "content": prompt},
                            ],
                            "temperature": 0.7,
                        },
                        headers={"Authorization": f"Bearer {settings.DOUBAO_API_KEY}"},
                        timeout=90.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    if "choices" in data:
                        return data["choices"][0]["message"]["content"]
                    elif "output" in data:
                        return data["output"]
                    return str(data)
                except httpx.HTTPError as e:
                    print(f"[评分] 豆包调用失败: {e}")

        print("[评分] 警告：未配置可用的AI模型，使用Mock评分")
        return json.dumps({
            "score_analysis": 72,
            "score_expression": 68,
            "score_adaptability": 65,
            "score_organization": 70,
            "report_content": "考生的回答基本覆盖了题目要点，但分析深度有待加强。整体表达较为流畅，但可以更加条理化。",
            "dimension_analysis": {
                "analysis": "回答对题目有一定理解，但分析不够深入，建议从多个角度展开思考。",
                "expression": "表达较为流畅，但有些地方逻辑不够清晰，建议使用'第一、第二、第三'等结构。",
                "adaptability": "面对问题有基本的应对思路，但不够灵活，建议多准备几种应对方案。",
                "organization": "方案有一定完整性，但步骤不够细化，建议增加具体的时间节点和责任分工。",
            },
            "deduction_points": "1. 分析不够深入，仅停留在表面；2. 部分观点缺乏有效论证；3. 总结提升略显不足",
            "optimization_suggestions": "1. 建议采用'是什么-为什么-怎么办'的分析框架；2. 适当引用政策文件或社会现象作为论据；3. 结尾做好升华和展望",
        })

    async def score(
        self, question_content: str, answer_text: str, question_category: str
    ) -> dict:
        prompt = self._build_prompt(question_content, answer_text, question_category)

        llm_response = await self._call_llm(prompt)

        scores = self._parse_llm_response(llm_response)

        overall = self._calculate_overall_score(scores)

        deduction_points = scores.get("deduction_points", "")
        if isinstance(deduction_points, list):
            deduction_points = "；".join(deduction_points)

        optimization_suggestions = scores.get("optimization_suggestions", "")
        if isinstance(optimization_suggestions, list):
            optimization_suggestions = "；".join(optimization_suggestions)

        dimension_analysis = scores.get("dimension_analysis", {})
        if isinstance(dimension_analysis, str):
            try:
                dimension_analysis = json.loads(dimension_analysis)
            except:
                dimension_analysis = {}

        return {
            "score_overall": overall,
            "score_analysis": scores.get("score_analysis", 0),
            "score_expression": scores.get("score_expression", 0),
            "score_adaptability": scores.get("score_adaptability", 0),
            "score_organization": scores.get("score_organization", 0),
            "report_content": scores.get("report_content", ""),
            "dimension_analysis": dimension_analysis,
            "deduction_points": deduction_points,
            "optimization_suggestions": optimization_suggestions,
            "weights": {
                "analysis": settings.SCORE_WEIGHT_ANALYSIS,
                "expression": settings.SCORE_WEIGHT_EXPRESSION,
                "adaptability": settings.SCORE_WEIGHT_ADAPTABILITY,
                "organization": settings.SCORE_WEIGHT_ORGANIZATION,
            },
        }
