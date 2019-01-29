from rest_framework import serializers

from .models import OCRSearchRequestBox


class OCRSearchRequestBoxWriteSerializer(serializers.ModelSerializer):
    left = serializers.DecimalField(max_digits=51, decimal_places=50)
    top = serializers.DecimalField(max_digits=51, decimal_places=50)
    right = serializers.DecimalField(max_digits=51, decimal_places=50)
    bottom = serializers.DecimalField(max_digits=51, decimal_places=50)

    class Meta:
        model = OCRSearchRequestBox
        fields = ['left', 'top', 'right', 'bottom', 'source', 'mathpix_latex']

