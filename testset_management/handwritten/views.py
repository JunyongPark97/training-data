from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from handwritten.models import HandwrittenBox, HandwrittenSource, HandwrittenTestset, Box
from handwritten.serializers import HandwrittenSourceSerializer, HandwrittenBoxWriteSerializer, HandwrittenTestsetSerializer, BoxWriteSerializer


@method_decorator(login_required, name='dispatch')
class HandwrittenSourceDetailView(DetailView):
    model = HandwrittenSource


class HandwrittenBoxViewSet(viewsets.ModelViewSet):
    queryset = HandwrittenBox.objects.all()
    serializer_class = HandwrittenBoxWriteSerializer
    permission_classes = (IsAuthenticated, )

class HandwrittenSourceViewSet(viewsets.ModelViewSet):
    queryset = HandwrittenSource.objects.all()
    serializer_class = HandwrittenSourceSerializer
    # permission_classes = (IsAuthenticated, )
    pagination_class = LimitOffsetPagination
    # filter_backends = (TagValueFilterBackend, DjangoFilterBackend)
    # filterset_class = TestSetFilter


@method_decorator(login_required, name='dispatch')
class HandwrittenTestsetDetailView(DetailView):
    model = HandwrittenTestset

class HandwrittenTestsetViewSet(viewsets.ModelViewSet):
    queryset = HandwrittenTestset.objects.all()
    serializer_class = HandwrittenTestsetSerializer
    pagination_class = LimitOffsetPagination


class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxWriteSerializer
    permission_classes = (IsAuthenticated, )
