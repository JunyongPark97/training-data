from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from .serializers import QalculatorBoxWriteSerializer, QalculatorSourceSerializer
from .models import QalculatorSource, QalculatorBox
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend


class QalculatorBoxViewSet(viewsets.ModelViewSet):
    queryset = QalculatorBox.objects.all()
    serializer_class = QalculatorBoxWriteSerializer
    permission_classes = (IsAuthenticated, )


@method_decorator(login_required, name='dispatch')
class QalculatorSourceDetailView(DetailView):
    model = QalculatorSource


class QalculatorSourceViewSet(viewsets.ModelViewSet):
    queryset = QalculatorSource.objects.all()
    serializer_class = QalculatorSourceSerializer
    # permission_classes = (IsAuthenticated, )
    pagination_class = LimitOffsetPagination
    # filter_backends = (TagValueFilterBackend, DjangoFilterBackend)
    # filterset_class = TestSetFilter
