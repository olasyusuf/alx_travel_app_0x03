# airbnb_app/serializers.py

from decimal import Decimal
from rest_framework import serializers
from .models import Users, Listing, PropertyFeature, Booking, Review


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
        read_only_fields = ['user_id', 'created_at', 'full_name', 'formatted_created_at']
        
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Custom create method to handle password hashing for new user creation.
        """
        user = Users.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        """
        Custom update method to handle password hashing if password is updated.
        """
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
            'amenity_id', 'listing', 'name', 'qty', 'created_at',
            'formatted_created_at'
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
    # Nested serializers for read-only representation
    host = UserSerializer(read_only=True)
    amenity = PropertyFeatureSerializer(many=True, read_only=True) 
    reviews = ReviewSerializer(many=True, read_only=True)
    watchlist = UserSerializer(many=True, read_only=True)

    # Custom calculated fields using SerializerMethodField
    formatted_created_at = serializers.ReadOnlyField() 
    features = serializers.SerializerMethodField()
    interested_clients = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'listing_id', 'host', 'title', 'description', 'location',
            'price_per_night', 'is_available', 'watchlist', 'created_at',
            'updated_at', 'amenity', 'reviews', 
            'formatted_created_at', 'features', 'interested_clients', 'average_rating'
        ]
        read_only_fields = [
            'listing_id', 'host', 'created_at', 'updated_at', 'amenity',
            'reviews', 'watchlist', 'formatted_created_at', 'features',
            'interested_clients', 'average_rating'
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


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    Handles booking data, including date validation and nested listing/guest info.
    """
    # Nested serializers for read-only representation
    listing_detail = ListingSerializer(source='listing', read_only=True) 
    guest_detail = UserSerializer(source='guest', read_only=True) 

    formatted_created_at = serializers.ReadOnlyField()
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'listing', 'guest', 'start_date', 'end_date',
            'total_price', 'status', 'created_at', 'formatted_created_at',
            'listing_detail', 'guest_detail' # Include nested details for read
        ]
        read_only_fields = [
            'booking_id', 'guest', 'created_at', 
            'formatted_created_at', 'total_price', 'status'
        ]

    def validate(self, data):
        """
        Validates that the end_date is after the start_date.
        """
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data

    def create(self, validated_data):
        """
        Custom create method to potentially calculate total_price or set initial status.
        """
        listing = validated_data['listing']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        duration_days = (end_date - start_date).days
        if duration_days <= 0: # Should be caught by validate, but good to double check
            raise serializers.ValidationError("Booking duration must be at least one day.")

        calculated_total_price = Decimal(duration_days) * listing.price_per_night
        validated_data['total_price'] = calculated_total_price
        
        return super().create(validated_data)
