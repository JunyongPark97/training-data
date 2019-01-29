from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from rest_framework import viewsets, mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from .filters import TagValueFilterBackend, TestSetFilter
from .serializers import BoxWriteSerializer, TestSetSerializer
from .models import Box, TestSet


def index(request):
    return render(request, 'index.html')


class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxWriteSerializer
    permission_classes = (IsAuthenticated, )


class TestSetViewSet(viewsets.ModelViewSet):
    queryset = TestSet.objects.all()
    serializer_class = TestSetSerializer
    # permission_classes = (IsAuthenticated, )
    pagination_class = LimitOffsetPagination
    filter_backends = (TagValueFilterBackend, DjangoFilterBackend)
    filterset_class = TestSetFilter


@method_decorator(login_required, name='dispatch')
class TestSetDetailView(DetailView):
    model = TestSet
