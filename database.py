#هنا سوف نقوم بإنشاء المحرك الاساسي الذي يربط بين قاعدة البيانات و الاكواد التي كتبناها 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# هذا من الاهم الاسطر في مشروعنا و استخدامه مدروس لكي يجعله قابل للتوسع
DATABASE_URL = "sqlite:///opensooq_data.db"

#هنا انشاء المحرك و الجلسة التي سوف تنقل تعاملاتنا بين قاعدة البيانات و الكود
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# هنا الانشاء النهائي للقاعدة 
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models 
    Base.metadata.create_all(bind=engine)