from rest_framework import serializers

from .models import Box, TestSet


class BoxWriteSerializer(serializers.ModelSerializer):
    left = serializers.FloatField()
    top = serializers.FloatField()
    right = serializers.FloatField()
    bottom = serializers.FloatField()
    input_text = serializers.CharField(allow_blank=True)

    class Meta:
        model = Box
        fields = ['id', 'testset', 'left', 'top', 'right', 'bottom', 'input_text']


class BoxReadSerializer(serializers.ModelSerializer):
    left = serializers.FloatField()
    top = serializers.FloatField()
    right = serializers.FloatField()
    bottom = serializers.FloatField()
    unicode = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Box
        fields = ['id', 'left', 'top', 'right', 'bottom', 'input_text', 'unicode', 'label']

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
        if box.input_text in defaults:
            return defaults[box.input_text]
        try:
            return ord(box.input_text)
        except:
            return None

    def get_label(self, box):
        if box.input_text in ('-', '='):
            return 'line'
        return 'char'


class TestSetSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    boxes = BoxReadSerializer(read_only=True, many=True)

    def get_tags(self, testset):
        result = {}
        for tag in testset.tags.all():
            result[tag.key] = tag.value
        return result

    class Meta:
        model = TestSet
        fields = (
            'id', 'image_url', 'grade_category',
            'mathpix_latex', 'latex',
            'tags', 'boxes', 'valid',
        )
