#!/usr/bin/env python3
"""冪等插入 5 條 AI 頻道到生產 config.yaml（Jy Gateway x4 + codex-pro）。

特點：
- 可重複執行：已存在的頻道自動跳過，不會重複插入。
- 寫檔前先做 YAML 解析驗證，驗證不過不落盤。
- 寫檔前自動備份（config.yaml.bak-<時間戳>）。
- 保留原檔註解與格式（純文字層插入，不整檔重寫語法）。

閘道金鑰不寫死在檔案裡，改由環境變數 JY_GATEWAY_API_KEY 提供。
這支腳本會進版控，寫死金鑰等於把它送進 git 歷史。

用法：
    JY_GATEWAY_API_KEY=sk-... sudo -E python3 scripts/insert_production_channels_20261003.py
    # 或指定其他設定檔先演練：
    JY_GATEWAY_API_KEY=sk-... python3 scripts/insert_production_channels_20261003.py \\
        --config /tmp/config.yaml --dry-run

跑完：sudo systemctl restart jysec-core
"""
import argparse
import os
import re
import shutil
import sys
import time

import yaml

# 這支腳本會用 sudo 執行，而 sudo 常常把 locale 降成 C/POSIX。
# 訊息是中文，沒先鎖定 UTF-8 會在印字時 UnicodeEncodeError 直接崩。
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PATH = '/var/lib/jysecai/core/config.yaml'

# 閘道金鑰一律從環境變數取得，不落檔。
GW_KEY_ENV = 'JY_GATEWAY_API_KEY'
GW_URL = 'https://ai5090.gasjy.com/api/v1'

# 不接受這些明顯是佔位符的值，避免把範例值寫進生產設定。
_PLACEHOLDER = re.compile(r'^sk-(x+|-?xxxx+)$', re.IGNORECASE)


def resolve_gateway_key():
    """從環境變數取得閘道金鑰，並擋掉佔位符。"""
    key = (os.environ.get(GW_KEY_ENV) or '').strip()
    if not key:
        raise SystemExit(
            '錯誤：缺少閘道金鑰。請設定環境變數後再執行：\n'
            '    export %s=sk-...\n'
            '  （注意 sudo 預設會清空環境變數，需一併使用 sudo -E）' % GW_KEY_ENV
        )
    if _PLACEHOLDER.match(key):
        raise SystemExit('錯誤：%s 看起來是佔位符，不是真的金鑰' % GW_KEY_ENV)
    return key


CHANNELS = [
    # (id, name, model, api_key, base_url)
    ('jy-gateway-jy53',       'Jy Gateway 5.3',                    'jy-5.3',        None,             GW_URL),
    ('jy-gateway-jy53-flash', 'Jy Gateway 5.3 Flash',              'jy-5.3-flash',  None,             GW_URL),
    ('jy-gateway-jy53-coder', 'Jy Gateway 5.3 Coder',              'jy-5.3-coder',  None,             GW_URL),
    ('jy-gateway-jy53-think', 'Jy Gateway 5.3 Think',              'jy-5.3-think',  None,             GW_URL),
    ('codex-pro',             'ChatGPT Pro (Codex 登入版)',        'codex-default', 'jysec-codex-bridge', 'http://127.0.0.1:18787/v1'),
]


def find_channels(node):
    """在 yaml 樹裡找 channels 映射（不假設層級位置）。"""
    if isinstance(node, dict):
        v = node.get('channels')
        if isinstance(v, dict) and v and all(isinstance(x, dict) for x in v.values()):
            return v
        for x in node.values():
            r = find_channels(x)
            if r is not None:
                return r
    elif isinstance(node, list):
        for x in node:
            r = find_channels(x)
            if r is not None:
                return r
    return None


def main():
    ap = argparse.ArgumentParser(description='冪等插入生產 AI 頻道到 config.yaml')
    ap.add_argument('--config', default=PATH,
                    help='要修改的設定檔（預設 %s）' % PATH)
    ap.add_argument('--dry-run', action='store_true',
                    help='只印出差異，不寫檔（不會產生備份）')
    args = ap.parse_args()

    # 就算全部頻道都已存在、根本不會用到金鑰，也先驗證環境變數設定正確，
    # 免得下次真的要插入時才發現 key 沒匯入。
    gw_key = resolve_gateway_key()
    channels = [c[:3] + (gw_key if c[3] is None else c[3],) + c[4:] for c in CHANNELS]

    data = open(args.config, 'rb').read()
    eol = b'\r\n' if b'\r\n' in data else b'\n'

    existing = find_channels(yaml.safe_load(data.decode('utf-8')))
    if existing is None:
        raise SystemExit('錯誤：config 裡找不到 channels 段')

    todo = [c for c in channels if c[0] not in existing]
    if not todo:
        print('5 條頻道都已存在，無需修改（頻道總數 %d）' % len(existing))
        return

    lines = data.decode('utf-8').split(eol.decode('ascii'))
    idx = [i for i, l in enumerate(lines) if re.fullmatch(r'  channels:\s*', l)]
    assert len(idx) == 1, 'channels 錨點數 = %d，需要 1' % len(idx)

    block = []
    for cid, name, model, key, url in todo:
        block += [
            '    %s:' % cid,
            '      name: %s' % name,
            '      provider: openai_compatible',
            '      api_key: %s' % key,
            '      base_url: %s' % url,
            '      model: %s' % model,
            '      max_total_tokens: 32768',
            '      max_completion_tokens: 8192',
            '      reasoning:',
            '        mode: off',
            '',
        ]
    lines[idx[0] + 1:idx[0] + 1] = block
    new_data = eol.join([l.encode('utf-8') for l in lines])

    parsed = yaml.safe_load(new_data.decode('utf-8'))
    after = find_channels(parsed)
    missing = [c[0] for c in todo if c[0] not in after]
    assert not missing, '寫前驗證失敗，缺少 %s（不落盤）' % missing

    if args.dry_run:
        print('[dry-run] 將插入 %d 條到 %s：%s'
              % (len(todo), args.config, ', '.join(c[0] for c in todo)))
        print('[dry-run] 插入後頻道總數 %d，未寫入任何檔案' % len(after))
        return

    backup = args.config + '.bak-' + time.strftime('%Y%m%d-%H%M%S')
    shutil.copy2(args.config, backup)
    with open(args.config, 'wb') as f:
        f.write(new_data)

    print('OK: 插入 %d 條 → %s' % (len(todo), ', '.join(c[0] for c in todo)))
    print('備份: %s' % backup)
    print('頻道總數: %d' % len(after))


if __name__ == '__main__':
    main()
