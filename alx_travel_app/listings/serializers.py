# airbnb_app/serializers.py

from decimal import Decimal
from rest_framework import serializers
from .models import Users, Listing, PropertyFeature, Booking, Review


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom Users model.
    Handles user data representation, including custom properties.
    """
    # Expose the full_name property from the model
    full_name = serializers.ReadOnlyField()
    # Expose the formatted_created_at property from the model
    formatted_created_at = serializers.ReadOnlyField()

    class Meta:
        model = Users
        # Explicitly list fields for clarity and security (excluding password on read)
        fields = [
            'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'created_at', 'full_name', 'formatted_created_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'full_name', 'formatted_created_at']
        # Make password write-only for creation/update, but not readable
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
        # 'listing' needs to be writable as a PrimaryKeyRelatedField for creation
        extra_kwargs = {
            'listing': {'write_only': True} # This assumes listing ID is provided on creation
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
        # 'listing' and 'reviewer' need to be writable as PrimaryKeyRelatedFields for creation
        extra_kwargs = {
            'listing': {'write_only': True},
            'reviewer': {'write_only': True} # This assumes reviewer ID is provided or set by view
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
    amenity = PropertyFeatureSerializer(many=True, read_only=True) # Corrected related_name to 'amenity'
    reviews = ReviewSerializer(many=True, read_only=True)
    watchlist = UserSerializer(many=True, read_only=True)

    # Custom calculated fields using SerializerMethodField
    formatted_created_at = serializers.ReadOnlyField() # Direct use of model property
    features = serializers.SerializerMethodField()
    interested_clients = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'listing_id', 'host', 'title', 'description', 'location',
            'price_per_night', 'is_available', 'watchlist', 'created_at',
            'updated_at', 'amenity', 'reviews', # 'amenity' is the correct related_name
            'formatted_created_at', 'features', 'interested_clients', 'average_rating'
        ]
        read_only_fields = [
            'listing_id', 'host', 'created_at', 'updated_at', 'amenity',
            'reviews', 'watchlist', 'formatted_created_at', 'features',
            'interested_clients', 'average_rating'
        ]
        # If 'host' needs to be set by ID on creation, you'd add:
        # extra_kwargs = {'host': {'write_only': True, 'required': True}}
        # But typically, host is set by request.user in the view, so read_only is fine.

    def get_features(self, obj):
        """
        Returns a list of amenity names associated with the listing.
        """
        # Ensure 'amenity' is the correct related_name on Listing model
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
    listing_detail = ListingSerializer(source='listing', read_only=True) # Use a different name to avoid conflict
    guest_detail = UserSerializer(source='guest', read_only=True) # Use a different name

    formatted_created_at = serializers.ReadOnlyField()

    # Writable fields for creating/updating a booking
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
    # 'guest' is typically set by the view to the authenticated user, so it can be read-only
    # or a PrimaryKeyRelatedField if manually provided. For this example, we'll assume
    # the view sets the guest.

    class Meta:
        model = Booking
        fields = [
            'booking_id', 'listing', 'guest', 'start_date', 'end_date',
            'total_price', 'status', 'created_at', 'formatted_created_at',
            'listing_detail', 'guest_detail' # Include nested details for read
        ]
        read_only_fields = ['booking_id', 'guest', 'created_at', 'formatted_created_at', 'total_price', 'status']
        # 'guest' is read-only here because it will be set by the view (request.user)
        # 'total_price' and 'status' might be calculated/set by logic, not direct input.

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
        # Example: Calculate total_price based on listing price and duration
        listing = validated_data['listing']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        duration_days = (end_date - start_date).days
        if duration_days <= 0: # Should be caught by validate, but good to double check
            raise serializers.ValidationError("Booking duration must be at least one day.")

        calculated_total_price = Decimal(duration_days) * listing.price_per_night
        validated_data['total_price'] = calculated_total_price
        # Status defaults to PENDING in the model, no need to set here unless overriding

        return super().create(validated_data)
