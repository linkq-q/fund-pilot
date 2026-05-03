import json

import requests

from config import DEEPSEEK_API_KEY

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
BASE_SYSTEM_PROMPT = (
    "你是一个保守型基金定投顾问。用户是在校学生，可投资金有限，"
    "目标年化收益12%。你只分析传入的持仓数据，不预测市场走势，"
    "不推荐未持有的基金。核心任务是帮助用户及时止盈、控制情绪、执行纪律。"
    "只输出JSON，不输出任何其他内容。"
)
FORMAT_PROMPT = (
    "必须严格按以下JSON格式输出，不允许添加任何其他字段：\n"
    "{\n"
    '  "action": "持有 / 减仓X% / 补仓X元 / 暂停 / 观察",\n'
    '  "confidence": 0到1之间的小数保留两位,\n'
    '  "reason": "不超过30字，必须引用数据中的具体数字",\n'
    '  "risk_warning": "不超过20字或null",\n'
    '  "cash_pool_change": 正数表示减仓回款金额，负数表示补仓支出，0表示无变动\n'
    "}"
)


BRANCH_PROMPTS = {
    "Branch_0": "当前为底仓基金，评估是否处于高位可以小幅减仓。",
    "Branch_1": "当前基金亏损，评估亏损是否在正常波动范围，是否满足补仓条件，不要安慰用户。",
    "Branch_2": "当前年化收益偏低，判断是否值得继续定投，重点考虑资金池余量和仓位占比。",
    "Branch_3": "当前收益处于合理区间，默认持有，只有发现明显异常才输出非持有建议。",
    "Branch_4": "当前年化已达目标2倍以上，触发止盈，建议减仓20%，解释理由需引用具体数字。",
    "Branch_5": "当前年化已达目标3倍以上，触发止盈，建议减仓30-40%，解释理由需引用具体数字。",
    "Branch_6": "当前年化已达目标4倍以上，强烈止盈信号，建议减仓50%，解释理由需引用具体数字。",
}


def fallback_result():
    return {
        "action": "观察",
        "confidence": 0.0,
        "reason": "今日建议生成失败，维持观察",
        "risk_warning": "请手动检查持仓",
        "cash_pool_change": 0,
    }


def _build_system_prompt(branch):
    base_branch = branch.split("_")[0] + "_" + branch.split("_")[1] if "_" in branch else branch
    prompt = BASE_SYSTEM_PROMPT + BRANCH_PROMPTS.get(base_branch, "")
    if "R7+" in branch:
        prompt += "回撤超过15%属于深度回撤，补仓权重加大，建议动用资金池30%以内补仓。"
    elif "R7" in branch:
        prompt += "同时存在回撤超过8%，在止盈建议基础上额外评估补仓可行性。"
    prompt += FORMAT_PROMPT
    return prompt


def _parse_response(content):
    data = json.loads(content)
    required = ["action", "confidence", "reason", "risk_warning", "cash_pool_change"]
    if not all(k in data for k in required):
        raise ValueError("Missing required fields")
    data["confidence"] = float(data["confidence"])
    data["cash_pool_change"] = float(data["cash_pool_change"])
    return data


def generate_advice(snapshot, router_result):
    if not DEEPSEEK_API_KEY:
        return fallback_result()

    branch = router_result.get("branch", "")
    system_prompt = _build_system_prompt(branch)
    user_prompt = json.dumps(
        {
            "snapshot": snapshot,
            "router_action": router_result.get("action"),
            "suggest_ratio": router_result.get("suggest_ratio"),
        },
        ensure_ascii=False,
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _parse_response(content)
    except Exception:
        return fallback_result()


def generate_daily_card(branch, fund_name):
    if not DEEPSEEK_API_KEY:
        return None

    if branch.startswith("Branch_0"):
        term = "底仓策略"
    elif branch.startswith("Branch_1"):
        term = "回撤与补仓"
    elif branch.startswith("Branch_2"):
        term = "折算年化收益率"
    elif branch.startswith("Branch_3"):
        term = "定投纪律"
    elif branch.startswith("Branch_4") or branch.startswith("Branch_5") or branch.startswith("Branch_6"):
        term = "止盈策略"
    else:
        term = "可投资金池"

    system_prompt = (
        "你是基金知识讲解员。只输出JSON。"
        "格式：{\"term\":str,\"explanation\":str,\"example\":str}"
    )
    user_prompt = f"请围绕术语{term}，结合基金{fund_name}给出简明解释和例子。"

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        if all(k in data for k in ["term", "explanation", "example"]):
            return {"term": data["term"], "explanation": data["explanation"], "example": data["example"]}
        return None
    except Exception:
        return None
