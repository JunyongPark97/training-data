from rest_framework import serializers

from .models import QalculatorBox, QalculatorSource


class QalculatorBoxWriteSerializer(serializers.ModelSerializer):
    left = serializers.DecimalField(max_digits=51, decimal_places=50)
    top = serializers.DecimalField(max_digits=51, decimal_places=50)
    right = serializers.DecimalField(max_digits=51, decimal_places=50)
    bottom = serializers.DecimalField(max_digits=51, decimal_places=50)
    input_text = serializers.CharField(allow_blank=True)

    class Meta:
        model = QalculatorBox
        fields = ['id', 'source', 'left', 'top', 'right', 'bottom', 'input_text']


class QalculatorBoxReadSerializer(serializers.ModelSerializer):
    left = serializers.FloatField()
    top = serializers.FloatField()
    right = serializers.FloatField()
    bottom = serializers.FloatField()
    unicode = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = QalculatorBox
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


class QalculatorSourceSerializer(serializers.ModelSerializer):
    # tags = serializers.SerializerMethodField()
    boxes = QalculatorBoxReadSerializer(read_only=True, many=True)

    def get_tags(self, qalculator):
        result = {}
        for tag in qalculator.tags.all():
            result[tag.key] = tag.value
        return result

    class Meta:
        model = QalculatorSource
        fields = (
            'id', 'image_url', 'boxes', 'valid',
            # 'tags'
        )
