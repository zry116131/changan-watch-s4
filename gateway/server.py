"""Small read-only HA adapter. No vehicle commands or HA service calls."""
import argparse
import hmac
import json
import math
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone, timedelta

FIELDS = {
    'remaining_range': ('km', 0), 'fuel_percent': ('%', 0),
    'odometer': ('km', 1), 'fuel_consumption': ('L/100km', 1),
    'cabin_temperature': ('°C', 1), 'battery_voltage': ('V', 1),
    'tire_pressure_fl': ('kPa', 0), 'tire_pressure_fr': ('kPa', 0),
    'tire_pressure_rl': ('kPa', 0), 'tire_pressure_rr': ('kPa', 0),
    'engine_running': ('', 0), 'air_conditioner': ('', 0),
    'vehicle_reported_at': ('', 0), 'authentication_required': ('', 0),
}

def available(state):
    return state is not None and str(state).strip() not in ('', 'unknown', 'unavailable', 'None')

def format_value(key, entity):
    value = entity.get('state')
    if not available(value):
        return '—'
    if key in ('engine_running', 'air_conditioner'):
        return {'on':'运行中' if key == 'engine_running' else '开启', 'off':'停止' if key == 'engine_running' else '关闭'}.get(value, '—')
    unit, precision = FIELDS[key]
    try:
        number = float(value)
        if not math.isfinite(number):
            return '—'
    except (ValueError, TypeError):
        return '—'
    # Respect HA's actual unit; do not relabel a user-configured unit as kPa/km.
    actual_unit = entity.get('attributes', {}).get('unit_of_measurement', unit)
    if key.startswith('tire_pressure') and actual_unit != 'kPa':
        precision = 2
    return f'{number:.{precision}f} {actual_unit}'.strip()

def report_time(value, now=None):
    if not available(value):
        return None, '车辆上报时间未知'
    try:
        moment = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        # This integration exposes the Changan China local timestamp as text.
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone(timedelta(hours=8)))
        age = ((now or datetime.now(timezone.utc)) - moment).total_seconds()
        display = moment.astimezone(timezone(timedelta(hours=8))).strftime('%m-%d %H:%M')
        if age < -60:
            return display, '车辆时间异常'
        minutes = max(0, int(age // 60))
        return display, '车辆数据刚刚上报' if minutes == 0 else (f'车辆数据 {minutes} 分钟前' if minutes < 60 else f'车辆数据 {minutes // 60} 小时前')
    except (ValueError, TypeError, OverflowError):
        return str(value)[:32], '车辆时间待核对'

def normalize(entities):
    values = {key: format_value(key, entities.get(key, {})) for key in FIELDS
              if key not in ('vehicle_reported_at', 'authentication_required')}
    reported = entities.get('vehicle_reported_at', {}).get('state')
    auth = entities.get('authentication_required', {}).get('state')
    display, warning = report_time(reported)
    if any(v == '—' for v in values.values()):
        warning = '部分车况不可用'
    if auth == 'on':
        warning = '长安登录已失效 · 旧值'
    return {'schema':1, 'values':values,
            'vehicle_reported_at':str(reported)[:64] if available(reported) else None,
            'vehicle_reported_display':display,
            'ha_read_at':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'warning':warning}

class Gateway:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.cached = None
        self.cached_at = 0
        if len(config.get('watch_key', '')) < 24:
            raise ValueError('watch_key must contain at least 24 characters')
        if not config.get('ha_url', '').startswith(('http://', 'https://')):
            raise ValueError('configure ha_url')
        if not config.get('ha_token'):
            raise ValueError('configure ha_token')
        for key, entity in config.get('entities', {}).items():
            if key not in FIELDS or not isinstance(entity, str) or not entity.startswith(('sensor.', 'binary_sensor.')) or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_.' for c in entity):
                raise ValueError('invalid entity mapping')
        if not config.get('entities'):
            raise ValueError('configure exact HA entity IDs')

    def read_entity(self, item):
        key, entity = item
        request = urllib.request.Request(self.config['ha_url'].rstrip('/') + '/api/states/' + entity,
            headers={'Authorization':'Bearer ' + self.config['ha_token'], 'Accept':'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read(65536))
                if data.get('entity_id') != entity:
                    raise ValueError('entity mismatch')
                return key, data
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return key, {'state':'unavailable'}
            raise

    def status(self):
        with self.lock:
            if self.cached is not None and time.monotonic() - self.cached_at < 30:
                return self.cached
            with ThreadPoolExecutor(max_workers=14) as pool:
                data = dict(pool.map(self.read_entity, self.config['entities'].items()))
            result = normalize(data)
            self.cached = result
            self.cached_at = time.monotonic()
            return result

def handler(gateway):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log authorization headers or request URLs.

        def reply(self, code, data):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/health':
                return self.reply(200, {'service':'changan-s3', 'schema':1})
            if self.path != '/v1/status':
                return self.reply(404, {'error':'not_found'})
            supplied = self.headers.get('Authorization', '')
            expected = 'Bearer ' + gateway.config['watch_key']
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                return self.reply(401, {'error':'unauthorized'})
            try:
                result = gateway.status()
                self.reply(200, result)
                print(time.strftime('%Y-%m-%d %H:%M:%S'), 'Vehicle snapshot served', flush=True)
                return
            except Exception:
                return self.reply(502, {'error':'ha_unavailable'})
    return Handler

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    gateway = Gateway(json.loads(Path(args.config).read_text()))
    server = ThreadingHTTPServer((args.bind, args.port), handler(gateway))
    print('Changan read-only gateway started', flush=True)
    server.serve_forever()
