from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import hashlib
from decimal import Decimal

# Import your models 
from listings.enums import AMENITIES, Roles # Import AMENITIES and UserRole
from listings.models import Users, Listing, PropertyFeature

class Command(BaseCommand):
    """
    Django custom management command to populate the database with sample
    listing data, including associated property features.
    """
    help = 'Populates the database with sample Airbnb listings and their features.'

    def handle(self, *args, **options):
        """
        The main entry point for the command.
        It creates sample users, listings, and property features, Bookings, & Reviews.
        """
        self.stdout.write(self.style.SUCCESS('Starting database population for listings...'))

        try:
            with transaction.atomic():
                # 1. Create or get admin users
                admin, admin_created = Users.objects.get_or_create(
                    username='admin_airbnb_clone',
                    email='admin_airbnb_clone@gmail.com',
                    defaults={'first_name': 'Admin', 'last_name': 'Admin', 'role': Roles.ADMIN}
                )
                if admin_created:
                    admin.set_password("admin123") 
                    admin.is_staff = 1
                    admin.save()
                    self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin.username}'))
                    
                # 1. Create or get host users
                host1, host1_created = Users.objects.get_or_create(
                    username='lifeisshort',
                    email='lifeisshort@gmail.com',
                    defaults={
                        'first_name': 'Samuel', 'last_name': 'John', 
                        'role': Roles.HOST, 'phone_number': '2348216723456'
                    }
                )
                if host1_created:
                    host1.set_password("1mm@tu@l") 
                    host1.save()
                    self.stdout.write(self.style.SUCCESS(f'Created host 1 user: {host1.username}'))

                host2, host2_created = Users.objects.get_or_create(
                    username='sani_bil',
                    email='sani_bil@gmail.com',
                    defaults={
                        'first_name': 'Bilal', 'last_name': 'Sanni', 
                        'role': Roles.HOST, 'phone_number': '2348216723456'
                        }
                )
                if host2_created:
                    host2.set_password("n@g0d3")
                    host2.save()
                    self.stdout.write(self.style.SUCCESS(f'Created host 2 user: {host2.username}'))

                # 2. Create or get guest users
                guest1, guest1_created = Users.objects.get_or_create(
                    username='abu_yinuz',
                    email='abu_yinuz@gmail.com',
                    defaults={'first_name': 'Abubakar', 'last_name': 'Yinuz', 'role': Roles.GUEST}
                )
                if guest1_created:
                    guest1.set_password('t3lisc0pe')
                    guest1.save()
                    self.stdout.write(self.style.SUCCESS(f'Created guest 1 user: {guest1.username}'))

                guest2, guest2_created = Users.objects.get_or_create(
                    username='akpan_dan',
                    email='akpan_dan@gmail.com',
                    defaults={'first_name': 'Dan', 'last_name': 'Akpan', 'role': Roles.GUEST}
                )
                if guest2_created:
                    guest2.set_password('runn1ng_h0rse')
                    guest2.save()
                    self.stdout.write(self.style.SUCCESS(f'Created guest 2 user: {guest2.username}'))
                    
                guest3, guest3_created = Users.objects.get_or_create(
                    username='ken.willy',
                    email='ken.willy@gmail.com',
                    defaults={'first_name': 'Ken', 'last_name': 'Williams', 'role': Roles.GUEST}
                )
                if guest3_created:
                    guest3.set_password('Rumin@nt')
                    guest3.save()
                    self.stdout.write(self.style.SUCCESS(f'Created guest 3 user: {guest3.username}'))


                # 3. Create Sample Listings
                listings_data = [
                    {
                        'host': host1,
                        'title': 'Paradise is not Far',
                        'description': 'Tallest white building on the street.',
                        'location': 'block 2A, Dimple Close, Ikoyi - Lagos',
                        'price_per_night': Decimal('451.00'),
                        'amenities': [
                            (AMENITIES.WI_FI, 1), (AMENITIES.POOL, 1), (AMENITIES.PETS, 1)
                        ],
                        'watchlist': [guest1, guest2]
                    },
                    {
                        'host': host1,
                        'title': 'Spacious Family Home with Garden',
                        'description': 'Ideal for families, close to parks and amenities.',
                        'location': 'Victoria Island, Lagos',
                        'price_per_night': Decimal('150.00'),
                        'amenities': [
                            (AMENITIES.WI_FI, 1), (AMENITIES.PARKING, 2), (AMENITIES.POOL, 1)
                        ],
                        'watchlist': [guest2]
                    },
                    {
                        'host': host2,
                        'title': 'Luxury Villa with Ocean View',
                        'description': 'Experience ultimate luxury with breathtaking views.',
                        'location': 'Eko Atlantic, Lagos',
                        'price_per_night': Decimal('300.00'),
                        'amenities': [
                            (AMENITIES.WI_FI, 1), (AMENITIES.POOL, 1), (AMENITIES.GYM, 1)
                        ],
                        'watchlist': [guest3, guest2]
                    },
                    {
                        'host': host2,
                        'title': 'Auto Palace',
                        'description': 'Best Catfish in town.',
                        'location': '82, Opebi Ikeja, Lagos.',
                        'price_per_night': Decimal('551.00'),
                        'amenities': [
                            (AMENITIES.PARKING, 1), (AMENITIES.PETS, 1)
                        ],
                        'watchlist': []
                    }
                ]

                for data in listings_data:
                    listing, created = Listing.objects.get_or_create(
                        host=data['host'],
                        title=data['title'],
                        defaults={
                            'description': data['description'],
                            'location': data['location'],
                            'price_per_night': data['price_per_night'],
                            'is_available': True
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created listing: "{listing.title}"'))

                        # Add amenities
                        for amenity_name, qty in data['amenities']:
                            PropertyFeature.objects.get_or_create(
                                listing=listing,
                                name=amenity_name,
                                defaults={'qty': qty}
                            )
                            self.stdout.write(self.style.SUCCESS(f'  - Added amenity: {amenity_name}'))

                        # Add to watchlist
                        if data['watchlist']:
                            listing.watchlist.add(*data['watchlist'])
                            self.stdout.write(self.style.SUCCESS(f' - Added to watchlist for {len(data["watchlist"])} users.'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Listing "{listing.title}" already exists. Skipping.'))

            self.stdout.write(self.style.SUCCESS('Database population for listings completed successfully!'))

        except Exception as e:
            raise CommandError(f'Error populating listings: {e}')

