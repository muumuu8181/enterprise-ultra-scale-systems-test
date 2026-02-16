from django.urls import path
from .views import CaseListView, CaseCreateView, CaseDetailView

urlpatterns = [
    path('', CaseListView.as_view(), name='case_list'),
    path('new/', CaseCreateView.as_view(), name='case_create'),
    path('<str:case_number>/', CaseDetailView.as_view(), name='case_detail'),
]
