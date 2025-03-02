from django.urls import path
from .views import AccountListCreateView, AccountUpdateDestroyView, AccountMemberListCreateView, DestinationListCreateView, DestinationUpdateDestroyView

urlpatterns = [
    path('', AccountListCreateView.as_view(), name='account-list-create'),
    path('<int:id>/', AccountUpdateDestroyView.as_view(), name='account-update-destroy'),
    path('<int:account_id>/members/', AccountMemberListCreateView.as_view(), name='account-member-list-create'),
    path('<int:account_id>/destinations/', DestinationListCreateView.as_view(), name='destination-list-create'),
    path('destinations/<int:id>/', DestinationUpdateDestroyView.as_view(), name='destination-update-destroy'),
]