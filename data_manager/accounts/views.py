from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import Account, AccountMember
from .serializers import AccountSerializer, AccountMemberSerializer
from users.permissions import IsAdminUser, IsAccountMember
from drf_spectacular.utils import extend_schema

class AccountListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AccountSerializer

    def get_queryset(self):
        queryset = Account.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

class AccountUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = AccountSerializer
    lookup_field = 'id'

    def get_queryset(self):
        is_admin = IsAdminUser().has_permission(self.request, self)
        if is_admin:
            return Account.objects.all()
        return Account.objects.filter(members__user=self.request.user)

class AccountMemberListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AccountMemberSerializer

    def get_queryset(self):
        account_id = self.kwargs['account_id']
        queryset = AccountMember.objects.filter(account_id=account_id)
        user_email = self.request.query_params.get('user_email')
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)
        return queryset

    def perform_create(self, serializer):
        serializer.save(account_id=self.kwargs['account_id'])