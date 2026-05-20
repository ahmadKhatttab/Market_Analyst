import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
from database import db_session
from models import CarAd

def scrape_opensooq_page(url):
    #هون عملنا السكراب و رتبنه شوي 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    


    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Connection Error : {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    



    script_tag = soup.find_all('script', type='application/ld+json')
    if not script_tag:
        print("No JSON-LD data was found")
        return
    
    for tag in script_tag:
        try:
            data = json.loads(tag.string)
        except Exception as e:
            print(e)
        

    items_list = []
    for graph_item in data.get('@graph', []):
        if graph_item.get('@type') == 'ItemList':
            items_list = graph_item.get('itemListElement', [])
            break
            
    extracted_cars = []
    
    for element in items_list:
        item = element.get('item', {})
        if not item or item.get('@type') not in ['Vehicle', 'Product']:
            continue 
            
        car_id = item.get('url', '').split('/')[-1] 
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
            mileage_clean = int(mileage_raw.split('-')[-1].replace(',', '').replace('+', '').strip())
        except:
            mileage_clean = 0
            
        car_data = {
            'id': int(car_id) if car_id else None,
            'title': title,
            'brand': brand,
            'model': model,
            'year': int(year) if year else None,
            'price': float(price_raw) if price_raw else 0.0,
            'mileage': mileage_clean,
            'fuel_type': fuel_type,
            'city': city,
            'image_url': image_url
        }
        extracted_cars.append(car_data)
        
    for car in extracted_cars:
        existing_car = db_session.query(CarAd).filter_by(id=car['id']).first()
        
        if not existing_car:
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
                image_url=car['image_url']
            )
            db_session.add(new_ad)
            
    db_session.commit()
    print(f"Done !! {len(extracted_cars)}")

if __name__ == "__main__":
    target_url = "https://jo.opensooq.com/ar/cars/cars-for-sale"
    scrape_opensooq_page(target_url)