# destinations/views.py
import uuid
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from .models import Destination, Log
from accounts.models import Account
from .serializers import DestinationSerializer, LogSerializer
from users.permissions import IsAccountMember, IsAdminUser
from .tasks import send_to_destination
from drf_spectacular.utils import extend_schema
from django.core.cache import cache
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

class DataHandlerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request={'type': 'object'},
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    def post(self, request):
        app_secret_token = request.headers.get('CL-X-TOKEN')
        event_id = request.headers.get('CL-X-EVENT-ID', str(uuid.uuid4()))
        
        if not app_secret_token:
            return Response({"error": "CL-X-TOKEN header is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not request.data or not isinstance(request.data, dict):
            return Response({"error": "Invalid Data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uuid.UUID(app_secret_token)
            account = Account.objects.get(members__user=request.user, app_secret_token=app_secret_token)
        except ValueError:
            logger.warning(f"Invalid CL-X-TOKEN format received: {app_secret_token}")
            return Response({"error": "Invalid CL-X-TOKEN format; must be a UUID"}, status=status.HTTP_400_BAD_REQUEST)
        except Account.DoesNotExist:
            logger.warning(f"Invalid CL-X-TOKEN used: {app_secret_token}")
            return Response({"error": "Invalid CL-X-TOKEN or no matching account"}, status=status.HTTP_403_FORBIDDEN)
        except Account.MultipleObjectsReturned:
            logger.error(f"Multiple accounts matched for CL-X-TOKEN: {app_secret_token}")
            return Response({"error": "Multiple accounts matched; specify a unique CL-X-TOKEN"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Unexpected error while verifying CL-X-TOKEN: {str(e)}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        destinations = Destination.objects.filter(account=account)
        if not destinations.exists():
            return Response({"error": "No destinations for this account"}, status=status.HTTP_400_BAD_REQUEST)

        for destination in destinations:
            try:
                log = Log.objects.create(
                    event_id=f"{event_id}-{destination.id}",
                    account=account,
                    destination=destination,
                    received_data=request.data,
                    status='pending'
                )
                send_to_destination.delay(log.id)
                # Invalidate log cache for this account
                cache.delete(f"logs_{account.id}")
            except Exception as e:
                logger.error(f"Failed to create log: {str(e)}")
                return Response({"error": f"Failed to create log: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Invalidate destination cache for this account
        cache.delete(f"destinations_{account.id}")
        return Response({"message": "Data Received"}, status=status.HTTP_200_OK)

class DestinationListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = DestinationSerializer

    def get_queryset(self):
        account_id = self.kwargs['account_id']
        url = self.request.query_params.get('url', '')
        cache_key = f"destinations_{account_id}_{url}"  # Dynamic key with filter
        queryset = cache.get(cache_key)
        if not queryset:
            queryset = Destination.objects.filter(account_id=account_id).select_related('account', 'created_by', 'updated_by')
            if url:
                queryset = queryset.filter(url__icontains=url)
            cache.set(cache_key, queryset, timeout=300)  # 5 minutes
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.memberships.filter(account_id=self.kwargs['account_id'], role__role_name='Admin').exists():
            raise serializers.ValidationError("Only admins can create destinations.")
        account_id = self.kwargs['account_id']
        serializer.save(account_id=account_id, created_by=self.request.user, updated_by=self.request.user)
        # Invalidate cache on create
        cache.delete(f"destinations_{account_id}")

class DestinationUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = DestinationSerializer
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.memberships.filter(account__destinations__id=self.kwargs['id'], role__role_name='Admin').exists():
            return Destination.objects.all().select_related('account', 'created_by', 'updated_by')
        return Destination.objects.filter(account__members__user=self.request.user).select_related('account', 'created_by', 'updated_by')

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        # Invalidate cache on update
        cache.delete(f"destinations_{serializer.instance.account_id}")

    def perform_destroy(self, instance):
        if not self.request.user.memberships.filter(account=instance.account, role__role_name='Admin').exists():
            raise serializers.ValidationError("Only admins can delete destinations.")
        account_id = instance.account_id
        instance.delete()
        # Invalidate cache on delete
        cache.delete(f"destinations_{account_id}")

class LogListView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAccountMember]
    serializer_class = LogSerializer

    def get_queryset(self):
        account_id = self.kwargs['account_id']
        status = self.request.query_params.get('status', '')
        event_id = self.request.query_params.get('event_id', '')
        destination_id = self.request.query_params.get('destination_id', '')
        received_timestamp_gte = self.request.query_params.get('received_timestamp__gte', '')
        received_timestamp_lte = self.request.query_params.get('received_timestamp__lte', '')
        
        # Dynamic cache key based on all filters
        cache_key = f"logs_{account_id}_{status}_{event_id}_{destination_id}_{received_timestamp_gte}_{received_timestamp_lte}"
        queryset = cache.get(cache_key)
        if not queryset:
            queryset = Log.objects.filter(account_id=account_id).select_related('account', 'destination')
            if status:
                queryset = queryset.filter(status=status)
            if event_id:
                queryset = queryset.filter(event_id__icontains=event_id)
            if destination_id:
                try:
                    queryset = queryset.filter(destination_id=int(destination_id))
                except ValueError:
                    logger.warning(f"Invalid destination_id: {destination_id}")
            if received_timestamp_gte:
                parsed_gte = parse_datetime(received_timestamp_gte)
                if parsed_gte:
                    queryset = queryset.filter(received_timestamp__gte=parsed_gte)
                else:
                    logger.warning(f"Invalid received_timestamp__gte: {received_timestamp_gte}")
            if received_timestamp_lte:
                parsed_lte = parse_datetime(received_timestamp_lte)
                if parsed_lte:
                    queryset = queryset.filter(received_timestamp__lte=parsed_lte)
                else:
                    logger.warning(f"Invalid received_timestamp__lte: {received_timestamp_lte}")
            cache.set(cache_key, queryset, timeout=300)  # 5 minutes
        return queryset