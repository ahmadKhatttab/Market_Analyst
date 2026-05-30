# هنا نقوم بإنشاء الـ schema لأضافة الداتا لها 
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base 
from datetime import datetime


class CarAd(Base):
    __tablename__ = 'car_ads'
    
    #قمنا بتعيينه كمفتاح رئيسي لكي يقوم النظام بالتأكد من عدم التكرار
    id = Column(Integer, primary_key=True)
    
    
    title = Column(String)

    
    brand = Column(String)
    model = Column(String)

    
    year = Column(Integer)

    
    price = Column(Float)

    
    mileage = Column(Integer)

    
    fuel_type = Column(String)

    
    city = Column(String)

    
    image_url = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)