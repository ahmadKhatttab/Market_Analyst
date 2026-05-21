import requests
from bs4 import BeautifulSoup
import json
import time
from database import db_session
from models import CarAd

def scrape_opensooq_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Connection Error: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')

    if not script_tags:
        print("No JSON-LD data was found")
        return []

    #  FIX 1: جمع كل الـ JSON في متغير data موحد بدل الكتابة فوق بعض
    all_data = []
    for tag in script_tags:
        try:
            parsed = json.loads(tag.string)
            all_data.append(parsed)
        except Exception as e:
            print(f"JSON parse error: {e}")
            continue

    items_list = []
    for data in all_data:
        for graph_item in data.get('@graph', []):
            if graph_item.get('@type') == 'ItemList':
                items_list = graph_item.get('itemListElement', [])
                break
        if items_list:
            break

    extracted_cars = []
    for element in items_list:
        item = element.get('item', {})
        if not item or item.get('@type') not in ['Vehicle', 'Product']:
            continue

        car_id_str = item.get('url', '').split('/')[-1]
        title = item.get('name')
        brand = item.get('brand', {}).get('name') if item.get('brand') else "Unknown"
        model = item.get('model')
        year = item.get('vehicleModelDate')
        price_raw = item.get('offers', {}).get('price')
        mileage_raw = item.get('mileageFromOdometer', {}).get('value')
        fuel_type = "gasoline"
        city = "Amman"
        image_url = item.get('image', {}).get('url') if item.get('image') else None

        try:
            mileage_clean = int(
                mileage_raw.split('-')[-1].replace(',', '').replace('+', '').strip()
            )
        except Exception:
            mileage_clean = 0

        try:
            car_id = int(car_id_str)
        except Exception:
            car_id = None

        car_data = {
            'id': car_id,
            'title': title,
            'brand': brand,
            'model': model,
            'year': int(''.join(filter(str.isdigit, str(year))))  if year else None,
            'price': float(price_raw) if price_raw else 0.0,
            'mileage': mileage_clean,
            'fuel_type': fuel_type,
            'city': city,
            'image_url': image_url,
        }
        extracted_cars.append(car_data)

    return extracted_cars  # FIX 2: رجّع النتائج بدل ما تحفظ مباشرة


# FIX 3: ميثود جديدة تتعامل مع كل الصفحات
def scrape_all_pages(base_url, max_pages=50, delay=2.0):
    """
    تسحب جميع صفحات السوق المفتوح وتحفظ النتائج في قاعدة البيانات.
    
    base_url  : الرابط الأساسي بدون page param
    max_pages : حد أقصى للصفحات (حماية من اللوب اللانهائي)
    delay     : ثواني الانتظار بين كل طلب (ضروري عشان ما يبان كـ bot)
    """
    total_saved = 0
    seen_ids = set()  # تتبع الـ IDs عشان نكتشف لو الموقع كرر نفس الصفحة

    for page_num in range(1, max_pages + 1):
        #  FIX 4: بناء رابط الـ pagination بشكل صحيح
        url = f"{base_url}?page={page_num}"
        print(f"Scraping page {page_num}: {url}")

        cars = scrape_opensooq_page(url)

        if not cars:
            print(f"No cars found on page {page_num}. Stopping.")
            break

        #  FIX 5: كشف الصفحات المكررة (الموقع رجّع نفس الداتا = وصلنا للنهاية)
        page_ids = {c['id'] for c in cars if c['id']}
        if page_ids and page_ids.issubset(seen_ids):
            print(f"Page {page_num} is a duplicate. End of listings.")
            break
        seen_ids.update(page_ids)

        # حفظناه في الdb   
        saved_this_page = 0
        for car in cars:
            if car['id'] is None:
                continue
            existing = db_session.query(CarAd).filter_by(id=car['id']).first()
            if not existing:
                new_ad = CarAd(
                    id=car['id'],
                    title=car['title'],
                    brand=car['brand'],
                    model=car['model'],
                    year=car['year'],
                    price=car['price'],
                    mileage=car['mileage'],
                    fuel_type=car['fuel_type'],
                    city=car['city'],
                    image_url=car['image_url'],
                )
                db_session.add(new_ad)
                saved_this_page += 1

        db_session.commit()
        total_saved += saved_this_page
        print(f"Saved {saved_this_page} new cars (total: {total_saved})")

        #  FIX 6: تأخير منطقي عشان ما يبلكنا 
        time.sleep(delay)

    print(f"\nDone! Total saved: {total_saved} cars.")


if __name__ == "__main__":
    target_url ="https://jo.opensooq.com/ar/%D8%B3%D9%8A%D8%A7%D8%B1%D8%A7%D8%AA-%D9%88%D9%85%D8%B1%D9%83%D8%A8%D8%A7%D8%AA/%D8%B3%D9%8A%D8%A7%D8%B1%D8%A7%D8%AA-%D9%84%D9%84%D8%A8%D9%8A%D8%B9"
    scrape_all_pages(target_url, max_pages=100, delay=2.0)