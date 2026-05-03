from config import MIN_ACTION_INTERVAL_DAYS, POSITION_MAX_RATIO

CB_INDEX_30D_CHANGE = 0.0


def run_router(snapshot):
    if snapshot["position_ratio"] > POSITION_MAX_RATIO:
        return {
            "branch": "Skip_S1",
            "action": "跳过",
            "suggest_ratio": 0,
            "skip": True,
            "skip_reason": "仓位占比超过上限",
        }

    if snapshot["days_since_last_action"] < MIN_ACTION_INTERVAL_DAYS:
        return {
            "branch": "Skip_S2",
            "action": "跳过",
            "suggest_ratio": 0,
            "skip": True,
            "skip_reason": "距离上次操作不足最小间隔",
        }

    if snapshot["fund_role"] == "底仓":
        if snapshot["profit_rate"] > 0.20 and CB_INDEX_30D_CHANGE > 0.15:
            return {
                "branch": "Branch_0",
                "action": "可考虑减仓10-20%",
                "suggest_ratio": 0.15,
                "skip": False,
                "skip_reason": None,
            }
        return {
            "branch": "Branch_0",
            "action": "持有",
            "suggest_ratio": 0,
            "skip": False,
            "skip_reason": None,
        }

    annualized_return = snapshot["annualized_return"]
    if annualized_return < 0:
        branch = "Branch_1"
        action = "亏损观察，评估是否补仓"
        suggest_ratio = 0
    elif annualized_return < 0.10:
        branch = "Branch_2"
        action = "年化偏低，评估是否加仓"
        suggest_ratio = 0
    elif annualized_return < 0.24:
        branch = "Branch_3"
        action = "持有观察"
        suggest_ratio = 0
    elif annualized_return < 0.36:
        branch = "Branch_4"
        action = "建议减仓20%"
        suggest_ratio = 0.20
    elif annualized_return < 0.48:
        branch = "Branch_5"
        action = "建议减仓30-40%"
        suggest_ratio = 0.35
    else:
        branch = "Branch_6"
        action = "强提示减仓50%"
        suggest_ratio = 0.50

    drawdown = snapshot["drawdown"]
    cash_pool_available = snapshot["cash_pool_available"]
    if drawdown > 0.15:
        branch = f"{branch}_R7+"
        action = f"{action}，回撤较深建议加大补仓"
    elif drawdown > 0.08 and cash_pool_available > 500:
        branch = f"{branch}_R7"
        action = f"{action}，同时建议补仓"

    return {
        "branch": branch,
        "action": action,
        "suggest_ratio": suggest_ratio,
        "skip": False,
        "skip_reason": None,
    }
