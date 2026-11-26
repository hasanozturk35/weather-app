import unittest
from unittest import mock

import requests

import weather

CURRENT = {
    "name": "Istanbul",
    "sys": {"country": "TR"},
    "main": {"temp": 14.23, "feels_like": 13.5, "humidity": 72},
    "wind": {"speed": 4.1},
    "weather": [{"description": "parçalı bulutlu"}],
}

# 2026-11-26 00:00 UTC'den başlayan 3 saatlik ölçümler (timezone=0)
BASE_TS = 1795651200
FORECAST = {
    "city": {"name": "Istanbul", "timezone": 0},
    "list": [
        {"dt": BASE_TS + i * 3 * 3600, "main": {"temp": 10 + i}, "weather": [{"description": f"d{i}"}]}
        for i in range(10)
    ],
}


def fake_response(status=200, payload=None):
    resp = mock.Mock(status_code=status)
    resp.json.return_value = payload if payload is not None else {}
    return resp


class FormatTests(unittest.TestCase):
    def test_format_current(self):
        out = weather.format_current(CURRENT)
        self.assertIn("Istanbul, TR", out)
        self.assertIn("14.2°C", out)
        self.assertIn("Parçalı bulutlu", out)
        self.assertIn("%72", out)

    def test_format_current_imperial(self):
        out = weather.format_current(CURRENT, "imperial")
        self.assertIn("°F", out)
        self.assertIn("mph", out)

    def test_summarize_forecast_groups_by_day(self):
        days = weather.summarize_forecast(FORECAST)
        self.assertEqual(len(days), 2)
        first = days[0]
        self.assertEqual(first["min"], 10)
        self.assertEqual(first["max"], 17)
        self.assertEqual(first["description"], "d4")  # saat 12:00
        self.assertEqual(days[1]["min"], 18)

    def test_format_forecast(self):
        out = weather.format_forecast(FORECAST)
        self.assertIn("5 Günlük Tahmin", out)
        self.assertIn("Perşembe 26.11", out)


class RequestTests(unittest.TestCase):
    @mock.patch("weather.requests.get")
    def test_success_sends_params(self, get):
        get.return_value = fake_response(200, CURRENT)
        data = weather.fetch_current("New York", "KEY")
        self.assertEqual(data, CURRENT)
        _, kwargs = get.call_args
        self.assertEqual(kwargs["params"]["q"], "New York")
        self.assertEqual(kwargs["timeout"], weather.TIMEOUT)

    @mock.patch("weather.requests.get")
    def test_city_not_found(self, get):
        get.return_value = fake_response(404, {"message": "city not found"})
        with self.assertRaisesRegex(weather.WeatherError, "Şehir bulunamadı"):
            weather.fetch_current("Yokşehir", "KEY")

    @mock.patch("weather.requests.get")
    def test_invalid_key(self, get):
        get.return_value = fake_response(401, {"message": "Invalid API key"})
        with self.assertRaisesRegex(weather.WeatherError, "API anahtarı"):
            weather.fetch_current("Istanbul", "BAD")

    @mock.patch(
        "weather.requests.get",
        side_effect=requests.ConnectionError("https://api.example/weather?appid=GIZLI_ANAHTAR"),
    )
    def test_connection_error_does_not_leak_key(self, _):
        with self.assertRaises(weather.WeatherError) as ctx:
            weather.fetch_current("Istanbul", "GIZLI_ANAHTAR")
        self.assertIn("Bağlantı", str(ctx.exception))
        self.assertNotIn("GIZLI_ANAHTAR", str(ctx.exception))
        self.assertIsNone(ctx.exception.__cause__)


class MainTests(unittest.TestCase):
    @mock.patch.dict("os.environ", {}, clear=True)
    @mock.patch("weather.load_dotenv")
    def test_missing_key(self, _):
        self.assertEqual(weather.main(["Istanbul"]), 1)

    @mock.patch.dict("os.environ", {"OPENWEATHER_API_KEY": "KEY"})
    @mock.patch("weather.requests.get")
    def test_main_success(self, get):
        get.return_value = fake_response(200, CURRENT)
        with mock.patch("builtins.print") as p:
            self.assertEqual(weather.main(["Istanbul"]), 0)
        self.assertIn("Istanbul, TR", p.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
