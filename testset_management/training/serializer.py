from rest_framework import serializers

from .models import Box, OCRSearchRequestSource


class CurrentSourceDefault(object):
    """
    현재의 Frame Default입니다.
    """
    def set_context(self, serializer_field):
        self.source = serializer_field.context['source']

    def __call__(self):
        return OCRSearchRequestSource.objects.get(pk=self.source)

class BoxWriteSerializer(serializers.ModelSerializer):
    left = serializers.DecimalField(max_digits=51, decimal_places=50)
    top = serializers.DecimalField(max_digits=51, decimal_places=50)
    right = serializers.DecimalField(max_digits=51, decimal_places=50)
    bottom = serializers.DecimalField(max_digits=51, decimal_places=50)
    # input_text = serializers.CharField(allow_blank=True)
    box_type = serializers.IntegerField()
    # input_text = serializers.CharField(allow_blank=True)
    source = serializers.HiddenField(default=CurrentSourceDefault())
    work_user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Box
        fields = ['id', 'box_type', 'source', 'left', 'top', 'right', 'bottom', 'work_user']

    def create(self, validated_data):
        source = validated_data['source']
        return Box.objects.create(
        left = validated_data['left'],
        top = validated_data['top'],
        right = validated_data['right'],
        bottom = validated_data['bottom'],
        frame_source = source,
        work_user = validated_data['work_user']
        )


class BoxReadSerializer(serializers.ModelSerializer):
    left = serializers.FloatField()
    top = serializers.FloatField()
    right = serializers.FloatField()
    bottom = serializers.FloatField()
    label = serializers.SerializerMethodField()
    unicode = serializers.SerializerMethodField()

    class Meta:
        model = Box
        fields = ['id', 'left', 'top', 'right', 'bottom', 'box_type', 'label', 'input_text','unicode','source','check_hangul_text']

    def get_label(self, box):
        if box.box_type ==0:
            return 'char'
        elif box.box_type ==1:
            return 'word'
        return 'line'

    def get_unicodess(self, box):
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

    def get_unicode(self, box):
        if len(box.input_text)==1:
            return ord(box.input_text)
        else:
            unicodes=[]
            for char in box.input_text:
                unicodes.append(ord(char))
            return unicodes


class BoxHangulSerializer(serializers.ModelSerializer):
    left = serializers.FloatField()
    top = serializers.FloatField()
    right = serializers.FloatField()
    bottom = serializers.FloatField()
    label = serializers.SerializerMethodField()
    # unicode = serializers.SerializerMethodField()

    class Meta:
        model = Box
        fields = ['id', 'left', 'top', 'right', 'bottom', 'box_type', 'label', 'input_text', 'unicode', 'source',
                  'check_hangul_text']

    def get_label(self, box):
        if box.box_type ==0:
            return 'char'
        elif box.box_type ==1:
            return 'word'
        return 'line'


class OCRSearchRequestSourceSerializer(serializers.ModelSerializer):
    # tags = serializers.SerializerMethodField()
    boxes = BoxReadSerializer(read_only=True, many=True)


    class Meta:
        model = OCRSearchRequestSource
        fields = (
            'id','valid','orig_image_url', 'boxes',
            # 'tags'
        )
