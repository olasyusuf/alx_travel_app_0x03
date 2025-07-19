from rest_framework import serializers
from .models import Users, Listing, PropertyFeature, Booking, Review


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='user_id', read_only=True)  # Expose user_id as id
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'role', 'created_at', 'formatted_created_at'
        ]
        
        read_only_fields = ['id', 'created_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at


# PropertyFeature Serializer
class PropertyFeatureSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='amenity_id', read_only=True)
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = PropertyFeature
        fields = [
            'id', 'listing', 'name', 
            'qty', 'created_at', 'formatted_created_at'
        ]
        
        read_only_fields = ['id', 'created_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='review_id', read_only=True)
    comment = serializers.CharField(max_length=500)
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'listing', 'reviewer', 
            'rating', 'comment', 'created_at', 'formatted_created_at'
        ]
        
        read_only_fields = ['id', 'created_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at
    
    def validate(self, data):
        if not (1 <= data['rating'] <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return data
    

# Listing Serializer
class ListingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='listing_id', read_only=True)
    host = UserSerializer(read_only=True)
    amenities = PropertyFeatureSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    watchlist = UserSerializer(many=True, read_only=True)
    formatted_created_at = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    interested_clients = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'host', 'name', 'description', 'location', 'price_per_night', 
            'watchlist', 'is_available', 'created_at', 'updated_at', 'formatted_created_at'
        ]
        
        read_only_fields = ['id', 'host', 'created_at', 'updated_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at
    
    def get_features(self, obj):
        return [amenity.name for amenity in obj.amenities.all()] 
    
    def get_interested_clients(self, obj):
        return [user.full_name for user in obj.watchlist.all()]    
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return "No Review"
        return round(sum([r.rating for r in reviews]) / len(reviews), 1)
        

# Booking Serializer
class BookingSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='booking_id', read_only=True)
    listing = ListingSerializer(read_only=True)
    guest = UserSerializer(read_only=True)
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'guest', 'start_date', 'end_date',
            'total_price', 'status', 'created_at', 'formatted_created_at'
        ]
        
        read_only_fields = ['id', 'guest', 'created_at']

    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at
    
    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data