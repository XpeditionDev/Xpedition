from app.extensions import db


from datetime import datetime





class Accommodation(db.Model):


    __tablename__ = 'accommodations'


    


    id = db.Column(db.Integer, primary_key=True)


    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)


    name = db.Column(db.String(255), nullable=False)


    address = db.Column(db.String(255))


    check_in_date = db.Column(db.DateTime, nullable=False)


    check_out_date = db.Column(db.DateTime, nullable=False)


    cost_per_night = db.Column(db.Float)


    type = db.Column(db.String(50), default='Hotel')  # Hotel, Airbnb, Hostel, etc.


    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    


    # Fix relationship with back_populates and overlaps


    itinerary = db.relationship('Itinerary', foreign_keys=[itinerary_id], back_populates='accommodations', overlaps="accommodations")


    


    def __repr__(self):


        return f'<Accommodation {self.name} for Itinerary {self.itinerary_id}>'


    


    @property


    def duration_nights(self):


        """Calculate the number of nights for this accommodation."""


        if not self.check_in_date or not self.check_out_date:


            return 0


        delta = self.check_out_date - self.check_in_date


        return delta.days


    


    @property


    def total_cost(self):


        """Calculate the total cost for this accommodation."""


        if not self.cost_per_night:


            return 0


        return self.cost_per_night * self.duration_nights 