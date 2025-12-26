from sqlalchemy import create_engine, select, func, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from .config import settings
from .models import Base, MessageDB

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def insert_message(db, msg_data):
    """
    Returns True if inserted, False if duplicate (idempotent)
    """
    db_msg = MessageDB(
        message_id=msg_data.message_id,
        from_msisdn=msg_data.from_,
        to_msisdn=msg_data.to,
        ts=msg_data.ts,
        text=msg_data.text
    )
    try:
        db.add(db_msg)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False

def get_messages(db, limit=50, offset=0, from_msisdn=None, since=None, q=None):
    query = select(MessageDB)

    if from_msisdn:
        query = query.where(MessageDB.from_msisdn == from_msisdn)
    if since:
        query = query.where(MessageDB.ts >= since)
    if q:
        query = query.where(MessageDB.text.icontains(q))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    query = query.order_by(MessageDB.ts.asc(), MessageDB.message_id.asc())
    query = query.offset(offset).limit(limit)
    
    result = db.execute(query).scalars().all()
    return result, total

def get_stats_data(db):
    total = db.query(func.count(MessageDB.message_id)).scalar()
    
    sender_stats = db.query(
        MessageDB.from_msisdn, 
        func.count(MessageDB.message_id).label('count')
    ).group_by(MessageDB.from_msisdn).order_by(desc('count')).limit(10).all()
    
    senders_count = db.query(func.count(func.distinct(MessageDB.from_msisdn))).scalar()
    
    min_ts = db.query(func.min(MessageDB.ts)).scalar()
    max_ts = db.query(func.max(MessageDB.ts)).scalar()

    return {
        "total_messages": total,
        "senders_count": senders_count,
        "messages_per_sender": [{"from": r[0], "count": r[1]} for r in sender_stats],
        "first_message_ts": min_ts,
        "last_message_ts": max_ts
    }