from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from .serializers import OCRSearchRequestBoxWriteSerializer
from .models import OCRSearchRequestSource, OCRSearchRequestBox


class OCRSearchRequestBoxViewSet(viewsets.ModelViewSet):
    queryset = OCRSearchRequestBox.objects.all()
    serializer_class = OCRSearchRequestBoxWriteSerializer
    permission_classes = (IsAuthenticated, )


@method_decorator(login_required, name='dispatch')
class OCRSearchRequestSourceDetailView(DetailView):
    model = OCRSearchRequestSource
