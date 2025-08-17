# airbnb_app/serializers.py

from decimal import Decimal
from rest_framework import serializers
from .models import Users, Listing, PropertyFeature, Booking, Review, Payment
from .enums import Roles, BookingStatus, AMENITIES, PaymentStatus


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom Users model.
    Handles user data representation, including custom properties.
    """
    full_name = serializers.ReadOnlyField()
    formatted_created_at = serializers.ReadOnlyField()

    class Meta:
        model = Users
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'created_at', 'full_name', 'formatted_created_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'full_name', 'formatted_created_at'] # Already covered by ReadOnlyField or model settings
        
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = Users.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class PropertyFeatureSerializer(serializers.ModelSerializer):
    """
    Serializer for the PropertyFeature model.
    Represents amenities associated with a listing.
    """
    formatted_created_at = serializers.ReadOnlyField()

    class Meta:
        model = PropertyFeature
        fields = [
            'amenity_id', 'listing', 'name', 'qty', 
            'created_at', 'formatted_created_at'
        ]
        read_only_fields = ['amenity_id', 'created_at', 'formatted_created_at']
        
        extra_kwargs = {
            'listing': {'write_only': True}
        }


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.
    Handles review data, including rating validation.
    """
    reviewer_full_name = serializers.ReadOnlyField(source='reviewer.full_name')
    listing_title = serializers.ReadOnlyField(source='listing.title')
    formatted_created_at = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = [
            'review_id', 'listing', 'reviewer', 'rating', 'comment',
            'created_at', 'reviewer_full_name', 'listing_title',
            'formatted_created_at'
        ]
        read_only_fields = [
            'review_id', 'created_at', 'reviewer_full_name',
            'listing_title', 'formatted_created_at'
        ]
        
        extra_kwargs = {
            'listing': {'write_only': True},
            'reviewer': {'write_only': True} 
        }

    def validate_rating(self, value):
        """
        Validates that the rating is between 1 and 5.
        """
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Listing model.
    Provides a comprehensive view of a listing, including nested related data
    and calculated properties.
    """
    host = UserSerializer(read_only=True)
    amenity = PropertyFeatureSerializer(many=True, read_only=True) 
    reviews = ReviewSerializer(many=True, read_only=True)
    watchlist = UserSerializer(many=True, read_only=True)

    formatted_created_at = serializers.ReadOnlyField() 
    features = serializers.SerializerMethodField()
    interested_clients = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'listing_id', 'host', 'title', 'description', 'location',
            'price_per_night', 'is_available', 'watchlist', 'created_at',
            'updated_at', 'amenity', 'reviews', 'bookings', # Fixed comma here
            'formatted_created_at', 'features', 'interested_clients', 'average_rating'
        ]
        read_only_fields = [
            'listing_id', 'host', 'created_at', 'updated_at', 
        ]
    

    def get_features(self, obj):
        """
        Returns a list of amenity names associated with the listing.
        """
        return [amenity.name for amenity in obj.amenity.all()]

    def get_interested_clients(self, obj):
        """
        Returns a list of full names of users who have added this listing to their watchlist.
        """
        return [user.full_name for user in obj.watchlist.all()]

    def get_average_rating(self, obj):
        """
        Calculates and returns the average rating for the listing, rounded to one decimal place.
        Returns "No Review" if there are no reviews.
        """
        reviews = obj.reviews.all()
        if not reviews:
            return "No Review"
        return round(sum([r.rating for r in reviews]) / len(reviews), 1)


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model with custom validation and creation logic.
    """
    class Meta:
        model = Payment
        fields = ['trnx_id', 'booking', 'amount', 'status', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at']

    def validate(self, data):
        """
        Validates the incoming data for creating a new Payment.
        Checks if the 'booking' exists and if the 'amount' is valid.
        """
        # Ensure the booking exists before trying to create a payment for it
        try:
            booking = Booking.objects.get(id=self.initial_data.get('booking'))
        except Booking.DoesNotExist:
            raise serializers.ValidationError("A payment must be associated with a valid booking.")

        # Ensure a payment amount is provided and is a positive value
        amount = data.get('amount')
        if amount is None or amount <= 0:
            raise serializers.ValidationError("The payment amount must be a positive value.")

        # Optional: Add a check to ensure the amount matches the total_price of the booking
        # if amount != booking.total_price:
        #     raise serializers.ValidationError("The payment amount must match the booking's total price.")
        
        # Add the booking instance to validated data for the create method
        data['booking'] = booking
        return data

    def create(self, validated_data):
        """
        Custom create method to handle payment creation and update the booking status.
        """
        booking = validated_data.pop('booking')
        amount = validated_data.pop('amount')
        
        # Create the Payment instance
        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            status=PaymentStatus.COMPLETED, # Assuming the payment is successful
            **validated_data
        )

        # Update the associated booking's status to confirmed
        if booking.status != BookingStatus.CONFIRMED:
            booking.status = BookingStatus.CONFIRMED
            booking.save()

        return payment


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    Handles booking data, including date validation and nested listing/guest info.
    """
    # Nested serializers for read-only representation of related objects
    listing_detail = serializers.ReadOnlyField() 
    guest_detail = serializers.ReadOnlyField() 

    # Nested serializer to display payments associated with this booking
    payments = PaymentSerializer(many=True, read_only=True)

    formatted_created_at = serializers.ReadOnlyField()
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'listing', 'guest', 'start_date', 'end_date',
            'total_price', 'status', 'created_at', 'formatted_created_at',
            'listing_detail', 'guest_detail', 'payments'
        ]
        read_only_fields = [
            'booking_id', 'created_at', 'formatted_created_at', 
            'total_price', 'status' 
        ]

    def validate(self, data):
        """
        Validates that the end_date is after the start_date.
        Also checks for existing bookings for the listing.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        listing = data.get('listing')

        if end_date <= start_date:
            raise serializers.ValidationError("End date must be after start date.")
        
        # Check for overlapping bookings
        if Booking.objects.filter(
            listing=listing,
            start_date__lt=end_date, 
            end_date__gt=start_date,
            status__in=['pending', 'confirmed']
        ).exists():
            raise serializers.ValidationError("This listing is already booked for part or all of the selected dates.")

        return data

    def create(self, validated_data):
        """
        Custom create method to calculate total_price and set initial status.
        """
        listing = validated_data['listing']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        duration_days = (end_date - start_date).days
        
        if duration_days <= 0: 
            raise serializers.ValidationError("Booking duration must be at least one day.")

        calculated_total_price = Decimal(duration_days) * listing.price_per_night
        validated_data['total_price'] = calculated_total_price
        
        if 'status' not in validated_data:
            validated_data['status'] = BookingStatus.PENDING # Ensure this is from your enums

        return super().create(validated_data)


