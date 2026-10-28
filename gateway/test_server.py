import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from server import normalize, handler, report_time
from datetime import datetime, timezone

class Tests(unittest.TestCase):
    def test_source_age_china_time(self):
        display, status = report_time('2026-10-28 09:11:46.109', datetime(2026,10,28,2,11,46,tzinfo=timezone.utc))
        self.assertEqual(display, '10-28 09:11')
        self.assertEqual(status, '车辆数据 59 分钟前')
        self.assertEqual(report_time('bad')[1], '车辆时间待核对')

    def test_unknown_is_not_zero_or_off(self):
        result = normalize({'fuel_percent':{'state':'unknown'}, 'engine_running':{'state':'unavailable'}})
        self.assertEqual(result['values']['fuel_percent'], '—')
        self.assertEqual(result['values']['engine_running'], '—')
        self.assertIsNone(result['vehicle_reported_at'])

    def test_real_zero_and_units(self):
        result = normalize({'fuel_percent':{'state':'0'}, 'engine_running':{'state':'off'}, 'tire_pressure_fl':{'state':'2.5', 'attributes':{'unit_of_measurement':'bar'}}})
        self.assertEqual(result['values']['fuel_percent'], '0 %')
        self.assertEqual(result['values']['engine_running'], '停止')
        self.assertEqual(result['values']['tire_pressure_fl'], '2.50 bar')

    def test_auth_and_source_time(self):
        result = normalize({'authentication_required':{'state':'on'}, 'vehicle_reported_at':{'state':'2026-10-27 12:00:00'}})
        self.assertIn('登录已失效', result['warning'])
        self.assertEqual(result['vehicle_reported_at'], '2026-10-27 12:00:00')

    def test_nonfinite(self):
        self.assertEqual(normalize({'fuel_percent':{'state':'NaN'}})['values']['fuel_percent'], '—')

    def test_http_auth_and_allowlist(self):
        class FakeGateway:
            config = {'watch_key':'test-only-' + 'x' * 24}
            calls = 0
            def status(self):
                self.calls += 1
                return normalize({})
        gateway = FakeGateway()
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler(gateway))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = 'http://127.0.0.1:' + str(server.server_port)
        try:
            for path, code in [('/v1/status', 401), ('/api/services/light/turn_on', 404)]:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(url + path)
                self.assertEqual(error.exception.code, code)
            self.assertEqual(gateway.calls, 0)
            request = urllib.request.Request(url + '/v1/status', headers={'Authorization':'Bearer ' + gateway.config['watch_key']})
            self.assertEqual(json.load(urllib.request.urlopen(request))['schema'], 1)
            self.assertEqual(gateway.calls, 1)
        finally:
            server.shutdown()
            server.server_close()

if __name__ == '__main__':
    unittest.main()
