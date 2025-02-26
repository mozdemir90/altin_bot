import requests
import xml.etree.ElementTree as ET
import asyncio
import signal
from telegram import Bot

# Telegram bot ayarları
TELEGRAM_TOKEN = "7599491092:AAFJz1K9GPGwY_DugwDNtRIzaEe6E6vZzD0"
TELEGRAM_CHAT_ID = "1660853466"

# Fiyat eşikleri (TL)
upper_threshold = 3484.0  # Üst eşik
lower_threshold = 3477.0  # Alt eşik

# Son durum değişkeni (fiyat hangi seviyede olduğunu tutar)
last_status = None  # "high" veya "low" olacak

# Çalışan döngüyü kontrol etmek için değişken
running = True

async def send_telegram(message):
    """Telegram'a mesaj gönder."""
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def get_gold_rates():
    """Altın kuru bilgisini al ve eşik değerleri kontrol et."""
    global last_status

    url = "http://data.altinkaynak.com/DataService.asmx"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://data.altinkaynak.com/GetGold"
    }
    body = """<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Header>
            <AuthHeader xmlns="http://data.altinkaynak.com/">
                <Username>AltinkaynakWebServis</Username>
                <Password>AltinkaynakWebServis</Password>
            </AuthHeader>
        </soap12:Header>
        <soap12:Body>
            <GetGold xmlns="http://data.altinkaynak.com/" />
        </soap12:Body>
    </soap12:Envelope>"""

    response = requests.post(url, data=body, headers=headers)

    if response.status_code == 200:
        root = ET.fromstring(response.text)

        gold_data = root.find(".//{http://data.altinkaynak.com/}GetGoldResult")

        has_altin_info = None
        satis_fiyati = None

        if gold_data is not None:
            gold_xml = ET.fromstring(gold_data.text)

            for kur in gold_xml.findall("Kur"):
                kod = kur.find("Kod").text
                if kod == "HH_T":
                    aciklama = kur.find("Aciklama").text
                    alis = float(kur.find("Alis").text)
                    satis = float(kur.find("Satis").text)
                    guncellenme_zamani = kur.find("GuncellenmeZamani").text

                    alis_fiyati = alis

                    has_altin_info = (
                        f"📌 {aciklama} ({kod})\n"
                        f"💰 Alış: {alis} TL\n"
                        f"💰 Satış: {satis} TL\n"
                        f"⏳ Güncelleme: {guncellenme_zamani}"
                    )
                    break

        if alis_fiyati:
            if alis_fiyati >= upper_threshold and last_status != "high":
                await send_telegram(f"🚀 Altın fiyatı yükseldi: {alis_fiyati} TL\n(Üst eşik: {upper_threshold} TL)")
                last_status = "high"

            elif alis_fiyati <= lower_threshold and last_status != "low":
                await send_telegram(f"📉 Altın fiyatı düştü: {alis_fiyati} TL\n(Alt eşik: {lower_threshold} TL)")
                last_status = "low"

async def main():
    """Ana döngü: Sürekli olarak fiyatları kontrol eder."""
    global running
    while running:
        await get_gold_rates()
        await asyncio.sleep(20)  # 10 dakika

def stop_loop():
    """Ctrl+C veya başka bir sinyal ile döngüyü durdur."""
    global running
    running = False
    print("Döngü durduruldu. Telegram mesajları artık gelmeyecek.")

# Ctrl+C veya process kapatıldığında programı düzgün sonlandır
signal.signal(signal.SIGINT, lambda s, f: stop_loop())
signal.signal(signal.SIGTERM, lambda s, f: stop_loop())

loop = asyncio.get_event_loop()

if loop.is_running():
    asyncio.ensure_future(main())
else:
    loop.run_until_complete(main())