from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base 
from datetime import datetime

class CarAd(Base):
    __tablename__ = 'car_ads'
    
    #السيستم بشيك اذالاي دي موجود او لا عشان يمنع التكرار
    id = Column(Integer, primary_key=True)
    
    #رح نستخدمه لأمر البحث لما اليوزر يدخل شو يده بنبحث بهذا العمود
    title = Column(String)

    #هذول الثنين اساس الفلترة ف لو المستخدم اختار تويوتها رح يرجعله بس السطور الي فيها تويوتا 
    brand = Column(String)
    model = Column(String)

    #ممكن نستخدمه عشان نرتب السيارات من الاحدث للأقدم 
    year = Column(Integer)

    #نفس مبدأ السنة لما اليوزر يختار انه بده اقل سعر او اكثر سعر و هكذا
    price = Column(Float)

    #لو اليوزر اختار انه بده سيارة ماشية عدد معين 
    mileage = Column(Integer)

    #لو اليزر اختار نوع الوقيد نرجعله ياهم 
    fuel_type = Column(String)

    #المدينة الي البائع فيها في حال اليوزر بده من مدينة معينة 
    city = Column(String)

    #الصورة و التاريخ الي انسحبت فيه الداتا 
    image_url = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)