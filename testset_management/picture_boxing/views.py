from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView
from munch import munchify
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests
from rest_framework.utils import json

from .models import Source, Box
from .serializers import BoxWriteSerializer, SourceSerializer
from source.models import OCRSearchRequestBox


@method_decorator(login_required, name='dispatch')
class SourceDetailView(DetailView):
    model = Source


class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxWriteSerializer
    permission_classes = (IsAuthenticated, )

    @list_route()
    def word(self, request):
        queryset = self.get_queryset().filter(label=0)
        serializer=self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def picture(self, request):
        queryset = self.get_queryset().filter(label=1)
        serializer=self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def graph(self, request):
        queryset = self.get_queryset().filter(label=2)
        serializer=self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    # permission_classes = (IsAuthenticated, )
    pagination_class = LimitOffsetPagination
    # filter_backends = (TagValueFilterBackend, DjangoFilterBackend)
    # filterset_class = TestSetFilter


@csrf_protect
def call_word_box(request, pk):
    if request.method == "POST":
        source = Source.objects.get(id=pk)
        boxes = []
        resp = requests.post('http://222.110.255.105:7722/api/detect/', data={'image_url': source.image_url})
        box_info = munchify(json.loads(resp.text)['boxes'])
        for box in box_info:
            boxes.append(Box(source=source, top=box.top, bottom=box.bottom, right=box.right, left=box.left))
        return Box.objects.bulk_create(boxes)
    else:
        pass
    return redirect("boxing-detail" ,pk = pk)