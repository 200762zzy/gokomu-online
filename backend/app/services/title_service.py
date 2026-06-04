from ..models import TitleInfo

TIERS = [
    {"name": "初心者", "icon": "🥚", "tier": 1, "min_elo": 0},
    {"name": "青铜棋手", "icon": "🥉", "tier": 2, "min_elo": 900},
    {"name": "白银棋手", "icon": "🥈", "tier": 3, "min_elo": 1100},
    {"name": "黄金棋手", "icon": "🥇", "tier": 4, "min_elo": 1300},
    {"name": "铂金棋手", "icon": "💠", "tier": 5, "min_elo": 1500},
    {"name": "钻石棋手", "icon": "💎", "tier": 6, "min_elo": 1700},
    {"name": "大师", "icon": "🔥", "tier": 7, "min_elo": 1900},
    {"name": "宗师", "icon": "👑", "tier": 8, "min_elo": 2100},
    {"name": "棋圣", "icon": "🏆", "tier": 9, "min_elo": 2300},
    {"name": "传说", "icon": "✨", "tier": 10, "min_elo": 2500},
]


def get_title(elo: int | None) -> TitleInfo:
    if elo is None:
        elo = 1000
    for t in reversed(TIERS):
        if elo >= t["min_elo"]:
            return TitleInfo(
                name=t["name"],
                tier=t["tier"],
                icon=t["icon"],
                cssClass=f"tier-{t['tier']}",
            )
    return TitleInfo(
        name=TIERS[0]["name"],
        tier=TIERS[0]["tier"],
        icon=TIERS[0]["icon"],
        cssClass=f"tier-{TIERS[0]['tier']}",
    )
