import django_filters
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from testset.models import TestSet


class TagValueFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for key, value in request.query_params.items():
            if key.startswith('tag_'):
                key = key[4:]
                splitted_key = key.split('__')
                if len(splitted_key) == 1:
                    key = key
                    lookup = ''
                elif len(splitted_key) == 2:
                    key = splitted_key[0]
                    lookup = '__' + splitted_key[1]
                else:
                    continue
                filter_data = {
                    'tags__key': key,
                    'tags__value' + lookup: value,
                }
                queryset = queryset.filter(Q(**filter_data))
        return queryset


class TestSetFilter(django_filters.FilterSet):
    boxes__isnull = django_filters.CharFilter(method='filter_boxes_isnull')

    class Meta:
        model = TestSet
        fields = ('boxes__isnull',)

    def filter_boxes_isnull(self, queryset, name, value):
        if value.lower() == 'true':
            queryset = queryset.filter(boxes__isnull=True)
        elif value.lower() == 'false':
            queryset = queryset.filter(boxes__isnull=False)
        return queryset.distinct()

