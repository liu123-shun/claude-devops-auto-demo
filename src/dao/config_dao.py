"""系统配置数据访问层 — 从数据库读取/写入配置"""
from typing import Optional
from sqlalchemy.orm import Session
from ..db.models import SystemConfig

DEFAULTS = {
    "overdue_days":    {"value": "30",  "type": "int",    "desc": "逾期天数阈值：借出超过此天数未归还视为逾期"},
    "max_borrow_count": {"value": "5",  "type": "int",    "desc": "每个学生最多同时借阅数量"},
    "renew_days":      {"value": "15",  "type": "int",    "desc": "续借延长天数"},
    "captcha_enabled":  {"value": "1",  "type": "bool",   "desc": "是否开启验证码：1=开启 0=关闭"},
}


def init_defaults(db: Session) -> None:
    """启动时初始化默认配置（不存在才插入）"""
    for key, info in DEFAULTS.items():
        existing = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if not existing:
            db.add(SystemConfig(
                config_key=key, config_value=info["value"],
                config_type=info["type"], description=info["desc"],
            ))
    db.commit()


def get_config(db: Session, key: str) -> Optional[str]:
    """读取单个配置值"""
    row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if row:
        return row.config_value
    return DEFAULTS.get(key, {}).get("value")


def get_config_int(db: Session, key: str) -> int:
    val = get_config(db, key)
    try: return int(val)
    except: return int(DEFAULTS.get(key, {}).get("value", "0"))


def get_config_float(db: Session, key: str) -> float:
    val = get_config(db, key)
    try: return float(val)
    except: return float(DEFAULTS.get(key, {}).get("value", "0"))


def get_config_bool(db: Session, key: str) -> bool:
    val = get_config(db, key)
    return val == "1" or (val or "").lower() == "true"


def get_all_config(db: Session) -> list:
    """获取全部配置项"""
    result = []
    for key, info in DEFAULTS.items():
        row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        result.append({
            "key": key,
            "value": row.config_value if row else info["value"],
            "type": row.config_type if row else info["type"],
            "description": row.description if row else info["desc"],
        })
    return result


def save_config(db: Session, key: str, value: str) -> None:
    """保存单个配置项"""
    row = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if row:
        row.config_value = value
    else:
        info = DEFAULTS.get(key, {})
        db.add(SystemConfig(
            config_key=key, config_value=value,
            config_type=info.get("type", "string"), description=info.get("desc", ""),
        ))
    db.commit()


def batch_save_config(db: Session, configs: dict) -> None:
    """批量保存配置"""
    for key, value in configs.items():
        save_config(db, key, str(value))
