#هذا الكود هو المحرك الاساسي الي رح يربط الداتابيس بالاكواد الي احنا عملناها
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

#هذا الرابط الي هون هو الي مخلي مشروعنا سكيل ابيليتي و قابل للتوسع عشان لما لقدام
DATABASE_URL = "sqlite:///opensooq_data.db"

#هون انشاء المحرك و الجلسة الي رح تكون توخذ و تعطي بين الكود و لداتابيس
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

#هون الأب او بنقدر نحكي الاساس الي عمل قاعدة البيانات 
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models 
    Base.metadata.create_all(bind=engine)