from django.db import models

class Roles(models.TextChoices):
    GUEST = 'GUEST', 'Guest'
    HOST = 'HOST', 'Host'
    ADMIN = 'ADMIN', 'Admin'

class BookingStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELED = 'CANCELED', 'Canceled'    
    
class AMENITIES(models.TextChoices):
    WI_FI = 'WI-FI', 'wi-fi'
    POOL = 'POOL', 'Pool'
    PETS = 'PETS', 'Pets' 
    GYM = "GYM", "Gym" 
    PARKING = 'PARKING', 'Parking'