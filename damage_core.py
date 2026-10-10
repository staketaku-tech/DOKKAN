"""DEF uses the original simulator; received damage applies type/guard before DEF."""
import math
from fractions import Fraction

FIELDS = ("memory", "add", "field", "mult", "active", "link", "sa")
LABELS = {"足し算パッシブ": "add", "掛け算パッシブ": "mult", "必殺技効果・味方の必殺支援": "sa", "メモリー": "memory", "フィールド": "field", "アクティブ": "active", "リンク": "link"}

def ratio_def(screen_def, current, target):
    """Recompute each checkpoint from the original snapshot, not rounded prior rows."""
    value = int(screen_def)
    for field in FIELDS:
        old, new = Fraction(str(current.get(field, 0))), Fraction(str(target.get(field, 0)))
        if old <= -100 or new <= -100:
            raise ValueError("DEF補正の合計は-100%より大きい値にしてください。")
        if old != new:
            value = math.floor(Fraction(value) * (100 + new) / (100 + old))
    return value

def basis_def(base, leader, modifiers):
    return calculate_dokkan_def(base, leader, modifiers.get("memory", 0), modifiers.get("add", 0), modifiers.get("field", 0), modifiers.get("active", 0), modifiers.get("mult", 0), modifiers.get("link", 0), modifiers.get("sa", 0))

def damage_details(defense, enemy_atk, reduction, type_multi=1.0, guard=False, advantageous=False, crit=False, crit_atk=50, crit_def=50):
    if not 0 <= reduction <= 100:
        raise ValueError("軽減率は0〜100%にしてください。")
    if min(defense, enemy_atk) < 0 or not 0 <= crit_def <= 100 or crit_atk < 0:
        raise ValueError("DEF・敵ATK・会心補正の値を確認してください。")
    effective_atk = math.floor(Fraction(enemy_atk) * (100 + Fraction(str(crit_atk))) / 100) if crit else enemy_atk
    effective_def = math.floor(Fraction(defense) * (100 - Fraction(str(crit_def))) / 100) if crit else defense
    before_type = Fraction(4, 5) if guard else Fraction(str(type_multi))
    after_def = Fraction(1, 2) if guard or advantageous else Fraction(1)
    attacking = math.floor(Fraction(effective_atk) * before_type * (100 - Fraction(str(reduction))) / 100)
    damage = math.floor(max(0, attacking - effective_def) * after_def)
    return {"damage": damage, "effective_def": effective_def, "attack_before_def": attacking}

def calculate_damage(defense, enemy_atk, reduction, **kwargs):
    return damage_details(defense, enemy_atk, reduction, **kwargs)["damage"]

def max_enemy_atk(defense, reduction, limit, **kwargs):
    """Find the actual integer boundary, including the floors in the forward calculation."""
    if reduction >= 100:
        return "∞"
    low, high = 0, 1
    while calculate_damage(defense, high, reduction, **kwargs) <= limit:
        high *= 2
    while low + 1 < high:
        middle = (low + high) // 2
        if calculate_damage(defense, middle, reduction, **kwargs) <= limit:
            low = middle
        else:
            high = middle
    return low

def reverse_enemy_atk(observed, defense, reduction, **kwargs):
    if observed <= 0 or reduction >= 100:
        raise ValueError("完封・100%軽減のとき敵ATKを一意に逆算できません。")
    lower = max_enemy_atk(defense, reduction, observed - 1, **kwargs) + 1
    upper = max_enemy_atk(defense, reduction, observed, **kwargs)
    if lower > upper:
        raise ValueError("この条件では入力したダメージに一致する敵ATKがありません。")
    return lower, upper

def timeline(screen_def, current, events, enemy_atk, reduction, *, basis=None, receiving=0, **damage_options):
    """Events are cumulative; rows with the same order activate together."""
    totals = {field: current.get(field, 0) for field in FIELDS}
    results = []
    def append(label, dr):
        target = dict(totals)
        target["mult"] += receiving
        if basis is None:
            defense = ratio_def(screen_def, current, target)
        else:
            defense = basis_def(*basis, target)
        detail = damage_details(defense, enemy_atk, dr, **damage_options)
        results.append({"タイミング": label, "被弾時DEF": defense, "被ダメージ": detail["damage"], "DEFを引く直前の敵ATK": detail["attack_before_def"], "足し算合計(%)": target["add"], "掛け算合計(%)": target["mult"], "必殺効果合計(%)": target["sa"], "軽減率(%)": dr})
    append("確認直後に被弾", reduction)
    valid = []
    for row in events:
        if not row.get("有効", True):
            continue
        if not row.get("タイミング") or not row.get("補正先"):
            raise ValueError("効果を追加した行は、タイミング・補正先・変化量を入力してください。")
        if row["補正先"] not in LABELS and row["補正先"] != "軽減率":
            raise ValueError("補正先を選択してください。")
        try:
            order = int(row["順番"])
            delta = int(row["変化量(%)"])
            if order != row["順番"] or delta != row["変化量(%)"]:
                raise ValueError()
        except (TypeError, ValueError, OverflowError):
            raise ValueError("順番と変化量は整数で入力してください。") from None
        valid.append((order, row, delta))
    valid.sort(key=lambda item: item[0])
    index = 0
    dr = reduction
    while index < len(valid):
        order = valid[index][0]
        labels = []
        while index < len(valid) and valid[index][0] == order:
            _, row, delta = valid[index]
            labels.append(str(row["タイミング"]))
            if row["補正先"] == "軽減率":
                dr += delta
            else:
                totals[LABELS[row["補正先"]]] += delta
            index += 1
        if any(value <= -100 for value in totals.values()):
            raise ValueError("DEF補正の合計は-100%より大きい値にしてください。")
        append(" / ".join(dict.fromkeys(labels)), dr)
    return results

def calculate_dokkan_def(base, ls, supp_mem, add_p, field, active, mult_p, link, sa_effect):
    val = math.floor(base * (1 + ls / 100))
    val = math.floor(val * (1 + supp_mem / 100))
    val = math.floor(val * (1 + add_p / 100))
    val = math.floor(val * (1 + field / 100))
    val = math.floor(val * (1 + mult_p / 100))
    val = math.floor(val * (1 + active / 100))
    val = math.floor(val * (1 + link / 100))
    val = math.floor(val * (1 + sa_effect / 100))
    return val
