#!/usr/bin/env python3

from rest_framework import serializers
from .models import Users, Listing, PropertyFeature, Booking, Review


# User Serializer
class UserSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = '__all__'
        extra_fields = ['formatted_created_at']
        
        read_only_fields = ['user_id', 'created_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at


# PropertyFeature Serializer
class PropertyFeatureSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = PropertyFeature
        fields = '__all__'
        extra_fields = ['formatted_created_at']
        
        read_only_fields = ['amenity_id', 'created_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    # comment = serializers.CharField(max_length=500)
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = '__all__'
        extra_fields = ['formatted_created_at']
        
        read_only_fields = ['review_id', 'created_at']
        
    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at
    
    def validate(self, data):
        if not (1 <= data['rating'] <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return data
    

# Listing Serializer
class ListingSerializer(serializers.ModelSerializer):
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
        fields = '__all__'
        
        read_only_fields = ['listing_id', 'host', 'created_at', 'updated_at']
        extra_fields = [
            'host', 'amenities', 'reviews', 'watchlist', 
            'formatted_created_at', 'features', 'interested_clients', 'average_rating'
            ]
        
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
    listing = ListingSerializer(read_only=True)
    guest = UserSerializer(read_only=True)
    formatted_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'
        extra_fields = ['listing', 'guest', 'formatted_created_at']
        
        read_only_fields = ['booking_id', 'guest', 'created_at']

    def get_formatted_created_at(self, obj):
        return obj.formatted_created_at
    
    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data