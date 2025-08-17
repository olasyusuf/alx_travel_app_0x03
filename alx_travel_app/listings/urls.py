from rest_framework import routers

from .views import ListingViewSet, BookingViewSet, PaymentViewSet

router = routers.DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'payments', PaymentViewSet)


urlpatterns = router.urls