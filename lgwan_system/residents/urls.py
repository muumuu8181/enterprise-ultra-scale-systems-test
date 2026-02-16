from django.urls import path
from .views import MoveInView, MoveOutView, CertificateView

urlpatterns = [
    path('move-in/', MoveInView.as_view(), name='move_in'),
    path('move-out/', MoveOutView.as_view(), name='move_out'),
    path('certificate/<int:resident_id>/', CertificateView.as_view(), name='certificate'),
]
