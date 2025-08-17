from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.conf import settings
import requests
import uuid

from .models import Listing, Booking, Payment, Review # Import Review for average rating calculation
from .serializers import (
    ListingSerializer,
    BookingSerializer,
    PaymentSerializer,
    ReviewSerializer # Potentially useful for nested writes, though not strictly required for these viewsets
)
from .enums import BookingStatus, PaymentStatus # Import BookingStatus for setting default status
from .tasks import send_booking_confirmation_email


class ListingViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing Listing instances.
    Provides CRUD operations for listings.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow authenticated users to write, others to read

    def perform_create(self, serializer):
        """
        Set the host of the listing to the authenticated user.
        """
        serializer.save(host=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_to_watchlist(self, request, pk=None):
        """
        Allows an authenticated user to add a listing to their watchlist.
        """
        listing = self.get_object()
        user = request.user
        
        if user in listing.watchlist.all():
            return Response({'detail': 'Listing already in watchlist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        listing.watchlist.add(user)
        return Response({'detail': 'Listing added to watchlist.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_from_watchlist(self, request, pk=None):
        """
        Allows an authenticated user to remove a listing from their watchlist.
        """
        listing = self.get_object()
        user = request.user

        if user not in listing.watchlist.all():
            return Response({'detail': 'Listing not in watchlist.'}, status=status.HTTP_400_BAD_REQUEST)
        
        listing.watchlist.remove(user)
        return Response({'detail': 'Listing removed from watchlist.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get all reviews for a specific listing.
        """
        listing = self.get_object()
        reviews = listing.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def book(self, request, pk=None):
        """
        Allows an authenticated user to book a specific listing.
        """
        listing = self.get_object()
        # You can get start_date and end_date from request.data
        data = request.data.copy()
        data['listing'] = listing.pk # Ensure listing ID is set
        data['guest'] = request.user.pk # Ensure guest ID is set to the current user

        serializer = BookingSerializer(data=data)
        if serializer.is_valid():
            serializer.save(listing=listing, guest=request.user, status=BookingStatus.PENDING)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing Booking instances.
    Provides CRUD operations for bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can manage bookings

    def get_queryset(self):
        """
        Optionally restrict bookings to those created by the requesting user
        or listings hosted by the requesting user.
        For hosts: see bookings for their listings.
        For guests: see their own bookings.
        """
        user = self.request.user
        if user.is_staff: # Admins can see all bookings
            return Booking.objects.all()
        # Guests can see their own bookings
        # Hosts can see bookings for their listings
        return Booking.objects.filter(guest=user) | Booking.objects.filter(listing__host=user)

    def perform_create(self, serializer):
        """
        Set the guest of the booking to the authenticated user and initial status.
        The `BookingSerializer`'s `create` method already handles total_price calculation.
        """
        # The serializer handles `guest` from validated_data already if passed.
        # Ensure it's explicitly set to the requesting user for security.
        serializer.save(guest=self.request.user, status=BookingStatus.PENDING)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Allows a host to approve a pending booking.
        """
        booking = self.get_object()
        user = request.user

        # Only the host of the listing associated with the booking can approve
        if booking.listing.host != user:
            return Response({'detail': 'You are not authorized to approve this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        if booking.status != BookingStatus.PENDING:
            return Response({'detail': 'Booking is not pending and cannot be approved.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = BookingStatus.CONFIRMED
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def decline(self, request, pk=None):
        """
        Allows a host to decline a pending booking.
        """
        booking = self.get_object()
        user = request.user

        # Only the host of the listing associated with the booking can decline
        if booking.listing.host != user:
            return Response({'detail': 'You are not authorized to decline this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return Response({'detail': 'Booking is already cancelled or completed.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = BookingStatus.DECLINED
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Allows the guest who made the booking, or the host, to cancel a booking.
        """
        booking = self.get_object()
        user = request.user

        # Check if the user is the guest or the host of the listing
        if booking.guest != user and booking.listing.host != user:
            return Response({'detail': 'You are not authorized to cancel this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        if booking.status in [BookingStatus.CANCELED, BookingStatus.CONFIRMED, BookingStatus.DECLINED]:
            return Response({'detail': 'Booking cannot be cancelled from its current status.'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = BookingStatus.CANCELED
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    
class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments to be viewed, and a new payment
    to be initiated with a custom 'initiate' action.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # This ensures that you can't create or update payments via standard CRUD
    http_method_names = ['post', 'get', 'head', 'options']

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Custom action to initiate a payment for a booking using the Chapa API.
        
        The endpoint will be accessible at: /api/payments/initiate/
        """
        # Retrieve request data
        booking_id = request.data.get('booking_id')
        
        if not booking_id:
            return Response(
                {"error": "booking_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Retrieve the booking and its related details
            booking = Booking.objects.get(booking_id=booking_id)
            email = request.data.get("email")
            listing = booking.listing
            guest = booking.guest

            # Check if the booking is in a state ready for payment
            if booking.status != BookingStatus.PENDING:
                return Response(
                    {"error": "This booking is not pending and cannot be paid for."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Use a database transaction to ensure atomicity
        with transaction.atomic():
            # Prepare the payload for the Chapa API
            # Generate transaction reference
            tx_ref = f"booking-payment-{booking.booking_id}-{uuid.uuid4().hex[:8]}"
        
            # Create a payment record in PENDING status
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                status=PaymentStatus.PENDING,
                trnx_id=tx_ref
            )

            # Chapa payload
            payload = {
                "amount": str(booking.total_price),
                "currency": "USD",  # Adjust currency as needed
                "email": email,
                "first_name": guest.first_name,
                "last_name": guest.last_name,
                "tx_ref": tx_ref,
                "callback_url": f"{request.build_absolute_uri('/api/payments/verify/')}{payment.trnx_id}/",
                "customization": {
                    "title": "Booking Payment",
                    "description": f"Payment for booking {booking.booking_id} on {listing.title}"
                }
            }

            # Make the POST request to the Chapa API
            url = "https://api.chapa.co/v1/transaction/initialize"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
            }

            try:
                # Make the request to Chapa
                chapa_response = requests.post(url, json=payload, headers=headers)
                chapa_response.raise_for_status()
                response_data = chapa_response.json()
                
                if response_data.get('status') == 'success':
                    return Response({
                        "message": "Payment initiated successfully.",
                        "payment_url": response_data.get('data').get('checkout_url')
                    }, status=status.HTTP_201_CREATED)
                else:
                    # Chapa returned a failure message, update payment status
                    payment.status = PaymentStatus.FAILED
                    payment.save()
                    raise Exception(f"Chapa initiation failed: {response_data.get('message')}")

            except requests.exceptions.RequestException as e:
                # Handle network errors, update payment status
                payment.status = PaymentStatus.FAILED
                payment.save()
                return Response(
                    {"error": f"Failed to connect to payment gateway: {str(e)}"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except Exception as e:
                # Handle any other errors during payment initiation
                return Response(
                    {"error": f"Payment initiation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
    
    # The new custom action to verify a payment
    @action(detail=False, methods=['get'])
    def verify(self, request, tx_ref):
        """
        Custom action to verify a payment with Chapa using the transaction reference.
        
        This endpoint is designed to be the callback URL for Chapa.
        The URL will be: /api/payments/verify/tx_ref=booking-payment-123-xyz
        """
        
        if not tx_ref:
            return Response(
                {"error": "Transaction reference (tx_ref) is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare the verification request to Chapa
        url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            # Handle network errors or non-2xx status codes
            return Response(
                {"error": f"Failed to verify with Chapa: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        # Check the verification status
        chapa_status = response_data.get('data', {}).get('status')
        chapa_message = response_data.get('message', 'Verification response received.')

        try:
            payment = Payment.objects.get(trnx_id=tx_ref)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment record not found for this transaction reference."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Use a database transaction to ensure atomicity
        with transaction.atomic():
            if chapa_status == "success":
                # If successful, update payment and booking statuses
                payment.status = PaymentStatus.COMPLETED
                payment.save()
                
                # Update the associated booking
                booking = payment.booking
                booking.status = BookingStatus.CONFIRMED
                booking.save()
                
                # Send confirmation email
                send_booking_confirmation_email.delay(booking.booking_id)
                
                return Response(
                    {"message": "Payment successfully verified and records updated."},
                    status=status.HTTP_200_OK
                )
            else:
                # If failed, update payment status and return error
                payment.status = PaymentStatus.FAILED
                payment.save()
                
                return Response(
                    {"error": f"Payment verification failed: {chapa_message}"},
                    status=status.HTTP_400_BAD_REQUEST
                )


    @action(detail=False, methods=['get'])
    def status(self, request, pk=None):
        """Get current payment status"""
        payment = self.get_object()
        serializer = self.get_serializer(payment)
        return Response({
            "status": "success",
            "data": serializer.data
        })