"""OpenWeatherMap API'si ile komut satırından hava durumu sorgulama."""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE_URL = "https://api.openweathermap.org/data/2.5"
TIMEOUT = 10
ENV_VAR = "OPENWEATHER_API_KEY"

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


class WeatherError(Exception):
    """API'den anlamlı bir yanıt alınamadığında fırlatılır."""


def load_dotenv(path: Path = Path(".env")) -> None:
    """Basit .env okuyucu: KEY=VALUE satırlarını ortam değişkenlerine ekler."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _request(endpoint: str, city: str, api_key: str, units: str) -> dict:
    params = {"q": city, "appid": api_key, "units": units, "lang": "tr"}
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=TIMEOUT)
    except requests.Timeout:
        raise WeatherError("Bağlantı hatası: sunucu zamanında yanıt vermedi.") from None
    except requests.RequestException as e:
        # Hata metni API anahtarını içeren URL'yi barındırabilir; bu yüzden yalnızca türünü göster.
        raise WeatherError(f"Bağlantı hatası: {type(e).__name__}") from None

    try:
        data = response.json()
    except ValueError:
        raise WeatherError("Sunucudan geçersiz yanıt alındı.") from None
    if not isinstance(data, dict):
        raise WeatherError("Sunucudan beklenmeyen yanıt alındı.")

    if response.status_code == 401:
        raise WeatherError("API anahtarı geçersiz. (Yeni anahtarların aktifleşmesi birkaç saat sürebilir.)")
    if response.status_code == 404:
        raise WeatherError(f"Şehir bulunamadı: {city}")
    if response.status_code != 200:
        raise WeatherError(f"API hatası ({response.status_code}): {data.get('message', 'bilinmiyor')}")
    return data


def fetch_current(city: str, api_key: str, units: str = "metric") -> dict:
    return _request("weather", city, api_key, units)


def fetch_forecast(city: str, api_key: str, units: str = "metric") -> dict:
    return _request("forecast", city, api_key, units)


def _unit_symbols(units: str) -> tuple[str, str]:
    return ("°F", "mph") if units == "imperial" else ("°C", "m/s")


def format_current(data: dict, units: str = "metric") -> str:
    temp_u, wind_u = _unit_symbols(units)
    main = data["main"]
    name = data["name"]
    country = data.get("sys", {}).get("country")
    title = f"{name}, {country}" if country else name
    return "\n".join(
        [
            f"--- {title} Hava Durumu ---",
            f"Durum    : {data['weather'][0]['description'].capitalize()}",
            f"Sıcaklık : {main['temp']:.1f}{temp_u} (hissedilen {main['feels_like']:.1f}{temp_u})",
            f"Nem      : %{main['humidity']}",
            f"Rüzgâr   : {data['wind']['speed']} {wind_u}",
        ]
    )


def summarize_forecast(data: dict) -> list[dict]:
    """3 saatlik tahminleri şehrin yerel saatine göre günlük özetlere çevirir."""
    tz = timezone(timedelta(seconds=data.get("city", {}).get("timezone", 0)))
    days: dict = defaultdict(list)
    for item in data["list"]:
        local = datetime.fromtimestamp(item["dt"], tz)
        days[local.date()].append((local, item))

    summary = []
    for day in sorted(days):
        entries = days[day]
        temps = [item["main"]["temp"] for _, item in entries]
        # Günün durumunu öğlene en yakın ölçümden al
        _, midday = min(entries, key=lambda e: abs(e[0].hour - 12))
        summary.append(
            {
                "date": day,
                "min": min(temps),
                "max": max(temps),
                "description": midday["weather"][0]["description"],
            }
        )
    return summary


def format_forecast(data: dict, units: str = "metric") -> str:
    temp_u, _ = _unit_symbols(units)
    lines = [f"--- {data['city']['name']} 5 Günlük Tahmin ---"]
    for day in summarize_forecast(data):
        label = f"{GUNLER[day['date'].weekday()]} {day['date']:%d.%m}"
        lines.append(
            f"{label:<16} {day['min']:>5.1f} / {day['max']:>5.1f}{temp_u}  "
            f"{day['description'].capitalize()}"
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Komut satırından hava durumu sorgulayın.")
    parser.add_argument("city", nargs="*", help="Şehir adı (ör. Istanbul veya 'New York')")
    parser.add_argument("-f", "--forecast", action="store_true", help="5 günlük tahmini göster")
    parser.add_argument(
        "-u", "--units", choices=["metric", "imperial"], default="metric",
        help="Birim sistemi (varsayılan: metric)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv()

    api_key = os.environ.get(ENV_VAR)
    if not api_key:
        print(f"Hata: {ENV_VAR} tanımlı değil. Kurulum için README'ye bakın.", file=sys.stderr)
        return 1

    city = " ".join(args.city).strip() or input("Şehir adı: ").strip()
    if not city:
        print("Hata: Şehir adı boş olamaz.", file=sys.stderr)
        return 1

    try:
        if args.forecast:
            print(format_forecast(fetch_forecast(city, api_key, args.units), args.units))
        else:
            print(format_current(fetch_current(city, api_key, args.units), args.units))
    except WeatherError as e:
        print(f"Hata: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
