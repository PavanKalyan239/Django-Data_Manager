# users/urls.py
from django.urls import path
from .views import RegisterView, LoginView, LogoutView, InviteUserView, UserListView, UserUpdateView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('invite/', InviteUserView.as_view(), name='invite-user'),
    path('', UserListView.as_view(), name='user-list'),
    path('<int:id>/', UserUpdateView.as_view(), name='user-update'),
]