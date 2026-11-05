import json
from sqlalchemy import create_engine, Integer, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

class Base(DeclarativeBase):
    pass

class Record(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(Text, index=True)
    event_json: Mapped[str] = mapped_column(Text)

class Store:
    """Append-only application event log. Snapshots support exact state replay."""
    def __init__(self, url):
        from sqlalchemy.pool import StaticPool
        options = {'connect_args': {'check_same_thread': False}}
        if ':memory:' in url:
            options['poolclass'] = StaticPool
        self.engine = create_engine(url, **options)
        Base.metadata.create_all(self.engine)

    def append(self, event):
        with Session(self.engine) as db:
            db.add(Record(session_id=event['sessionId'], event_json=json.dumps(event)))
            db.commit()

    def events(self, session_id):
        with Session(self.engine) as db:
            return [json.loads(r.event_json) for r in db.scalars(select(Record).where(Record.session_id == session_id).order_by(Record.id))]
