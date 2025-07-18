# from django.core.management.base import BaseCommand
# from listings.models import Listing
# import random

# class Command(BaseCommand):
#     help = 'Seed the database with sample listing data'

#     def handle(self, *args, **kwargs):
#         titles = ['Beach House', 'City Apartment', 'Mountain Cabin', 'Lake Cottage']
#         locations = ['Mombasa', 'Nairobi', 'Naivasha', 'Eldoret']

#         for _ in range(10):
#             Listing.objects.create(
#                 title=random.choice(titles),
#                 description='A lovely place to stay!',
#                 location=random.choice(locations),
#                 price_per_night=random.uniform(50, 300),
#                 is_available=random.choice([True, False])
#             )
#         self.stdout.write(self.style.SUCCESS(' Successfully seeded listings!'))