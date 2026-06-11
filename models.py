
from extensions import db
from datetime import date


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100) , nullable=False)
    email = db.Column(db.String(100), unique=True ,nullable=False)
    password = db.Column(db.String(100) ,nullable=False)
    role = db.Column(db.String(20))
    approved = db.Column(db.Boolean, default=False)
    blacklisted = db.Column(db.Boolean, default=False)
    # relationship
    # bookings = db.relationship(
    #     'Booking',
    #     backref='user',
    #     lazy=True
    # )
    bookings = db.relationship(
        'Booking',
        backref='user',
        lazy=True
    )


class Trek(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    assigned_staff_id=staff_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    available_slots=db.Column(db.Integer)
    difficulty = db.Column(db.String(50))
    duration = db.Column(db.Integer)
    status = db.Column(db.String(20),default='Open')
    start_date=db.Column(db.Date)
    end_date=db.Column(db.Date)
    image=db.Column(db.String(500))
    trek_details=db.Column(db.String(500))
    bookings = db.relationship(
        'Booking',
        backref='trek',
        lazy=True
    )
    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=True
    )
    


class Booking(db.Model):

    Booking_ID = db.Column(db.Integer, primary_key=True)
    User_ID=db.Column(db.Integer, db.ForeignKey('user.id'))
    Trek_ID=db.Column(db.Integer, db.ForeignKey('trek.id'))
    Booking_Date=db.Column(db.Date)
    Status=db.Column(db.String(100))
    # user_id = db.Column(
    #     db.Integer,
    #     db.ForeignKey('user.id')
    # )

    # trek_id = db.Column(
    #     db.Integer,
    #     db.ForeignKey('trek.id')
    # )

    # status = db.Column(db.String(50))

