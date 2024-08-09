from app import db
from datetime import datetime

class Event(db.Model):
    SN=db.Column(db.Integer, primary_key=True)
    TITLE=db.Column(db.String(200), nullable=False)
    DESC=db.Column(db.String(500), nullable=False)
    StART_DATE=db.Column(db.Date, nullable=False)
    END_DATE=db.Column(db.Date, nullable=False)
    DATE_CREATED=db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sn} - {self.tile}"