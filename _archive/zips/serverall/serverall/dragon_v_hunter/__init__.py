"""
🐉 Dragon-V Logistics Hunter
专为越南物流/快递/订单系统设计的业务逻辑渗透框架
"""

__version__ = "1.0.0"
__author__ = "Dragon-V Research Team"
__description__ = "Business Logic Penetration Framework for Vietnamese Logistics Systems"

from .core.vietnamese_fingerprinter import VietnameseFingerprinter
from .core.attack_chainer import AttackChainer
from .database.deep_weaponization import DatabaseWeaponization
from .exfiltration.covert_exfil import CovertExfiltration
from .ai.chain_planner import ChainPlanner

__all__ = [
    "VietnameseFingerprinter",
    "AttackChainer",
    "DatabaseWeaponization",
    "CovertExfiltration",
    "ChainPlanner"
]