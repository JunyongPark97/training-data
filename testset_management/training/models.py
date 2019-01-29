import random
import re
import string
from io import BytesIO

import requests
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models


PRECISION = 4
THRESHOLD = 0.1 ** PRECISION

def get_box_filename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)) + '.jpg'

def equals(f1, f2):
    return abs(f1 - f2) < THRESHOLD


class OCRSearchRequestSource(models.Model):
    search_request_id = models.CharField(max_length=100)
    orig_image_key = models.UUIDField()
    image_url = models.CharField(max_length=100)
    user_id = models.IntegerField()
    valid = models.NullBooleanField()

    def get_image_extension(self):
        return 'jpeg'

    @property
    def orig_image_url(self):
        return 'https://qanda-storage.s3.amazonaws.com/{}.jpg'.format(self.orig_image_key)

    @property
    def prev(self):
        return OCRSearchRequestSource.objects.filter(pk__lt=self.pk).order_by('pk').last()

    @property
    def next(self):
        return OCRSearchRequestSource.objects.filter(pk__gt=self.pk).order_by('pk').first()


class OCRSearchRequestSourceTag(models.Model):
    source = models.ForeignKey(OCRSearchRequestSource, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)


class Box(models.Model):
    source = models.ForeignKey(OCRSearchRequestSource, related_name='boxes', on_delete=models.CASCADE)
    box_type = models.IntegerField(choices=((0, 'char'), (1, 'word'), (2, 'line')))
    image = models.ImageField(upload_to='box')
    left = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    top = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    right = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    bottom = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    input_text = models.CharField(max_length=100)
    work_user = models.ForeignKey(User, null=True, blank=True,related_name='worked_box', on_delete=models.CASCADE)

    def validate_coordinates(self):
        if self.left >= self.right:
            raise Exception('left >= right')
        elif self.top >= self.bottom:
            raise Exception('top >= bottom')
        self.left = 0 if self.left < 0 else self.left
        self.top = 0 if self.top < 0 else self.top
        self.right = 1 if self.right > 1 else self.right
        self.bottom = 1 if self.bottom > 1 else self.bottom

    @property
    def check_hangul_text(self):
        if len(self.input_text) == 1:
            hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', self.input_text))
            print(hanCount)
        # else:

            # for char in self.input_text:

            return hanCount>0

    def save(self, *args, **kwargs):
        self.validate_coordinates()
        super(Box, self).save(*args, **kwargs)

    def update(self, left, top, right, bottom, **kwargs):
        if not equals(float(self.left), left) or \
                not equals(float(self.top), top) or \
                not equals(float(self.right), right) or \
                not equals(float(self.bottom), bottom):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.save()

    def _save_box_image(self):
        # appengine images api
        from PIL import Image
        resp = requests.get(self.source.image_url)
        image = Image.open(BytesIO(resp.content))
        width, height = image.size
        left = width * self.left
        top = height * self.top
        right = width * self.right
        bottom = height * self.bottom
        crop_data = image.crop((int(left), int(top), int(right), int(bottom)))
        # http://stackoverflow.com/questions/3723220/how-do-you-convert-a-pil-image-to-a-django-file
        crop_io = BytesIO()
        crop_data.save(crop_io, format=self.source.get_image_extension())
        crop_file = InMemoryUploadedFile(crop_io, None, get_box_filename(), 'image/jpeg', len(crop_io.getvalue()), None)
        self.image.save(get_box_filename(), crop_file, save=False)
        # To avoid recursive save, call super.save
        super(Box, self).save()

    def __str__(self):
        if self.id:
            return 'B%d' % self.id
        return ''

    @property
    def escaped_input_text(self):
        # template에서 "\" 를 escape 해서 보여주기 위함
        text = self.input_text
        text = text.replace('×', '*')
        text = text.replace('/', '÷')
        text = text.replace('\\', '√')
        return text
        # return self.input_text.replace('\\', '\\\\')



class BoxTag(models.Model):
    box = models.ForeignKey(Box, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
