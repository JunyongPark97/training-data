import django_filters
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, TemplateView
from rest_framework import viewsets, mixins, generics
from rest_framework.decorators import list_route, action, detail_route
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Box, OCRSearchRequestSource
from .serializer import BoxWriteSerializer, OCRSearchRequestSourceSerializer, BoxReadSerializer


@method_decorator(login_required, name='dispatch')
class OCRSearchRequestSourceDetailView(DetailView):
    model = OCRSearchRequestSource

#박싱하러 가기
class OCRSearchRequestSourceBoxingView(TemplateView):
    template_name = 'training/ocrsearchrequestsource_detail.html'

    def get_context_data(self, pk):
        context = super(OCRSearchRequestSourceBoxingView, self).get_context_data()
        source = OCRSearchRequestSource.objects.get(id=pk)

        context['source'] = source
        # context['char_source'] =
        return context

class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxWriteSerializer
    permission_classes = (IsAuthenticated, )

    @action(methods=['get'], detail=True)
    def char(self, request, pk=None):
        # source = request.data[]
        queryset = self.get_queryset().filter(box_type=0)[:2]
        print(self.get_queryset().filter(type=0)[:2])
        # print(queryset[1].boxes.all())
        serializer=self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
        if self.request:
            qdict = self.request.data
            try:
                qdict = qdict.dict()
                return {'request': self.request, 'source': qdict['source']}

            except:
                pass


class BoxTypeFilter(django_filters.FilterSet):
    class Meta:
        model = Box
        fields = {
            'source',
            'box_type',}

# class BoxReadViewSet(generics.ListAPIView):
class BoxReadViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxReadSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = BoxTypeFilter


    @classmethod
    def get_extra_actions(cls):
        return []


# class BoxHangulList(viewsets.ModelViewSet):
#     queryset = OCRSearchRequestSource.objects.all()
#     serializer_class = OCRSearchRequestSourceSerializer
#     pagination_class = LimitOffsetPagination

    # def get_queryset(self, queryset=None):
    #     if self.kwargs['hangul']:
    #         queryset for queryset in Box.objects.all() if queryset.check_hangul_text == True
    #         return queryset
    #         # queryset = Box.objects.filter(check_hangul_text=True)
    #     else:
    #         queryset = Box.objects.all()
    #     print(self.kwargs['hangul'])
    #     return queryset

class OCRSearchRequestSourceList(viewsets.ModelViewSet):
    queryset = OCRSearchRequestSource.objects.all()
    serializer_class = OCRSearchRequestSourceSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    # filter_fields = ('boxes__label',)



    # @action(methods=['get'],detail=True)
    # def char(self, request, pk=None):
    #     # source = request.data[]
    #     queryset = self.get_queryset().filter(boxes__box_type=0)[:2]
    #     print(self.get_queryset().filter(boxes__box_type=0)[:2])
    #     # print(queryset[1].boxes.all())
    #     serializer=self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)
    #
    # @action(methods=['get'],detail=True)
    # def word(self, request,pk=None):
    #     queryset = self.get_queryset().filter(boxes__box_type=1)[:2]
    #     serializer=self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)
    #
    # @list_route()
    # def line(self, request):
    #     queryset = self.get_queryset().filter(boxes__box_type=2)
    #     serializer=self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)

