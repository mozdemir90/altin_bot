import requests
import xml.etree.ElementTree as ET
import asyncio
from telegram import Bot
import os
from dotenv import load_dotenv

# Telegram bot ayarları
# .env dosyasından gerekli bilgileri yükle
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def get_gold_rates():
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
        
        # SOAP cevabı içinden altın kuru verisini çıkar
        gold_data = root.find(".//{http://data.altinkaynak.com/}GetGoldResult")
        
        has_altin_info = None  # Veriyi önce burada saklayacağız
        
        if gold_data is not None:
            gold_xml = ET.fromstring(gold_data.text)
            
            # "Has Toptan (HH_T)" altın verisini bul
            for kur in gold_xml.findall("Kur"):
                kod = kur.find("Kod").text
                if kod == "HH_T":  # "Has Toptan" kodunu kontrol et
                    aciklama = kur.find("Aciklama").text
                    alis = kur.find("Alis").text
                    satis = kur.find("Satis").text
                    guncellenme_zamani = kur.find("GuncellenmeZamani").text

                    has_altin_info = (
                        f"📌 {aciklama} ({kod})\n"
                        f"💰 Alış: {alis} TL\n"
                        f"💰 Satış: {satis} TL\n"
                        f"⏳ Güncelleme: {guncellenme_zamani}"
                    )
                    break  # "Has Toptan" bulunduğunda döngüden çık
        
        # Eğer "Has Altın" verisi bulunduysa, sadece onu gönder
        if has_altin_info:
            await send_telegram(has_altin_info)
        else:
            await send_telegram("⚠️ 'Has Toptan (HH_T)' verisi bulunamadı.")  # Bu mesajı sadece bir kere gönderiyoruz
    else:
        await send_telegram(f"❌ Hata: {response.status_code}, {response.text}")

async def main():
    while True:
        await get_gold_rates()
        await asyncio.sleep(120)  # 10 dakika

loop = asyncio.get_event_loop()

if loop.is_running():
    asyncio.ensure_future(main())
else:
    loop.run_until_complete(main())