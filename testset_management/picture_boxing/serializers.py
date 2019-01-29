from rest_framework import serializers

from .models import Box, Source


class BoxWriteSerializer(serializers.ModelSerializer):
    left = serializers.DecimalField(max_digits=51, decimal_places=50)
    top = serializers.DecimalField(max_digits=51, decimal_places=50)
    right = serializers.DecimalField(max_digits=51, decimal_places=50)
    bottom = serializers.DecimalField(max_digits=51, decimal_places=50)
    # input_text = serializers.CharField(allow_blank=True)
    label = serializers.IntegerField()

    class Meta:
        model = Box
        fields = ['id', 'source', 'left', 'top', 'right', 'bottom', 'label']

class BoxReadSerializer(serializers.ModelSerializer):
    left = serializers.FloatField()
    top = serializers.FloatField()
    right = serializers.FloatField()
    bottom = serializers.FloatField()
    # unicode = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Box
        fields = ['id', 'left', 'top', 'right', 'bottom', 'label']

    def get_unicode(self, box):
        defaults = {
            '-': 0,
            '*': 215,  # times
            '/': 247,  # div
            '#': ord('{'),  # simeq curly brace
            '\\': 8730,  # sqrt
            'sum': 8721,  # sum
            'int': 8747,  # integral
        }
        if box.label in defaults:
            return defaults[box.label]
        try:
            return ord(box.label)
        except:
            return None

    def get_label(self, box):
        if box.label in ('-', '='):
            return 'line'
        return 'char'


class SourceSerializer(serializers.ModelSerializer):
    # tags = serializers.SerializerMethodField()
    boxes = BoxReadSerializer(read_only=True, many=True)
    #
    # def get_tags(self, qalculator):
    #     result = {}
    #     for tag in qalculator.tags.all():
    #         result[tag.key] = tag.value
    #     return result

    class Meta:
        model = Source
        fields = (
            'id', 'image_url', 'boxes', 'valid',
            # 'tags'
        )
