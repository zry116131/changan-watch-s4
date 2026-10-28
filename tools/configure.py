"""Generate local configuration. Tokens entered with getpass never appear in output."""
import getpass
import json
import os
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
local = root / '.local'
local.mkdir(exist_ok=True, mode=0o700)
target = local / 'gateway.json'
if target.exists():
    raise SystemExit('配置已存在，请编辑 .local/gateway.json；不会覆盖已有凭据。')
ha_url = input('HA 地址: ').strip().rstrip('/')
ha_token = getpass.getpass('HA Token（不回显）: ').strip()
gateway_url = input('平板可访问的车况读取服务地址: ').strip().rstrip('/')
if not all(url.startswith(('http://', 'https://')) for url in [ha_url, gateway_url]) or not ha_token:
    raise SystemExit('地址或 Token 为空/格式错误')
key = secrets.token_urlsafe(32)
config = {'ha_url':ha_url, 'ha_token':ha_token, 'watch_key':key, 'entities':{}}
with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as file:
    json.dump(config, file, ensure_ascii=False, indent=2)
connection = root / 'watch/src/common/connection.js'
connection.write_text('export default ' + json.dumps({'baseUrl':gateway_url, 'key':key}) + '\n')
connection.chmod(0o600)
print('本地配置已生成。需在 gateway.json 的 entities 中填写该车辆的实际 HA 实体 ID，然后构建 RPK。')
