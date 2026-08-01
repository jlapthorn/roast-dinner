from roast_dinner import db


class Food(db.Model):
    __tablename__ = "foods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(32), nullable=False)  # meat, vegetable, other
    meat_type = db.Column(db.String(32))  # chicken, beef, pork, lamb
    temperature_c = db.Column(db.Integer)  # meats: fan oven °C; veg/other unused
    minutes_per_kg = db.Column(db.Float)  # meats: scale with weight
    base_minutes = db.Column(db.Float, default=0)  # meats: fixed add-on
    fixed_minutes = db.Column(db.Float)  # vegetables / other: fixed cook time
    rest_minutes = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, default="")
    is_favourite = db.Column(db.Boolean, nullable=False, default=False)

    def cook_minutes(self, weight_kg: float | None = None) -> float:
        if self.category == "meat":
            weight = float(weight_kg or 0)
            per_kg = float(self.minutes_per_kg or 0)
            base = float(self.base_minutes or 0)
            return per_kg * weight + base
        return float(self.fixed_minutes or 0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "meat_type": self.meat_type,
            "temperature_c": self.temperature_c,
            "minutes_per_kg": self.minutes_per_kg,
            "base_minutes": self.base_minutes,
            "fixed_minutes": self.fixed_minutes,
            "rest_minutes": self.rest_minutes,
            "notes": self.notes or "",
            "is_favourite": bool(self.is_favourite),
        }
