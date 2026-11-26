# Hava Durumu Uygulaması

[OpenWeatherMap](https://openweathermap.org/) API'sini kullanan, komut satırından anlık hava durumu ve 5 günlük tahmin gösteren bir Python uygulaması.

## Özellikler

- Anlık hava durumu: sıcaklık, hissedilen sıcaklık, nem, rüzgâr
- 5 günlük tahmin: şehrin yerel saatine göre günlük en düşük/en yüksek sıcaklık
- Metrik (°C) veya imperial (°F) birimler
- Türkçe çıktı ve anlaşılır hata mesajları (geçersiz anahtar, şehir bulunamadı, bağlantı hatası)
- API anahtarı koda yazılmaz; ortam değişkeninden veya `.env` dosyasından okunur

## Kurulum

Python 3.10 veya üstü gerekir.

```bash
git clone https://github.com/hasanozturk35/weather-app.git
cd weather-app
pip install -r requirements.txt
```

[OpenWeatherMap](https://home.openweathermap.org/users/sign_up) üzerinden ücretsiz bir API anahtarı alın. Sonra `.env.example` dosyasını `.env` adıyla kopyalayıp anahtarınızı yazın:

```
OPENWEATHER_API_KEY=anahtariniz
```

> `.env` dosyası `.gitignore` içindedir, yani git'e eklenmez. API anahtarınızı koda ya da repoya asla yazmayın.

Anahtarı ortam değişkeni olarak da verebilirsiniz:

```powershell
$env:OPENWEATHER_API_KEY = "anahtariniz"   # Windows PowerShell
```
```bash
export OPENWEATHER_API_KEY="anahtariniz"   # Linux / macOS
```

## Kullanım

```bash
python weather.py Istanbul            # anlık hava durumu
python weather.py "New York"          # boşluklu şehir adları
python weather.py Ankara --forecast   # 5 günlük tahmin
python weather.py London -u imperial  # °F ve mph
python weather.py                     # şehri sorar
```

Örnek çıktı:

```
--- Istanbul, TR Hava Durumu ---
Durum    : Parçalı bulutlu
Sıcaklık : 14.2°C (hissedilen 13.5°C)
Nem      : %72
Rüzgâr   : 4.1 m/s
```

## Testler

Testler API'ye gerçekten bağlanmaz, yanıtları taklit eder. Bu yüzden anahtar gerektirmez.

```bash
python -m unittest discover -s tests -t . -v
```
## Lisans

[MIT](LICENSE)
