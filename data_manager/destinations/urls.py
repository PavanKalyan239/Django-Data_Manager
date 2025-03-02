from django.urls import path
from .views import DataHandlerView, DestinationListCreateView, DestinationUpdateDestroyView, LogListView

urlpatterns = [
    path('server/incoming_data/', DataHandlerView.as_view(), name='data-handler'),
    path('accounts/<int:account_id>/destinations/', DestinationListCreateView.as_view(), name='destination-list-create'),
    path('destinations/<int:id>/', DestinationUpdateDestroyView.as_view(), name='destination-update-destroy'),
    path('accounts/<int:account_id>/logs/', LogListView.as_view(), name='log-list'),
]