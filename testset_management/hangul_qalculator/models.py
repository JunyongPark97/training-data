import random
import requests
import string
from io import BytesIO
import requests

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.safestring import mark_safe

from source.models import OCRSearchRequestSource, save_mathpix_latex_async, clone_to_testset
from testset.models import do_everything

PRECISION = 4
THRESHOLD = 0.1 ** PRECISION


def get_box_filename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)) + '.jpg'


def equals(f1, f2):
    return abs(f1 - f2) < THRESHOLD


class SmallQalculatorBoxException(Exception):
    pass


class QalculatorSource(models.Model):
    search_request_id = models.CharField(max_length=100)
    image_key = models.UUIDField()
    user_id = models.IntegerField()
    ocrsr_source = models.ForeignKey(OCRSearchRequestSource, related_name='qalculator', on_delete=models.SET_NULL, blank=True, null=True)
    valid = models.NullBooleanField()

    def get_image_extension(self):
        return 'jpeg'

    @property
    def image_url(self):
        return 'https://qanda-storage.s3.amazonaws.com/{}.jpg'.format(self.image_key)

    @property
    def prev(self):
        return QalculatorSource.objects.filter(pk__lt=self.pk).order_by('pk').last()

    @property
    def next(self):
        return QalculatorSource.objects.filter(pk__gt=self.pk).order_by('pk').first()


class QalculatorBox(models.Model):
    source = models.ForeignKey(QalculatorSource, related_name='boxes', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='box')
    left = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    top = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    right = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    bottom = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    input_text = models.CharField(max_length=200, help_text='Boxing UI에서 입력한 값')
    unicode_value = models.IntegerField(blank=True, null=True)


    def validate_coordinates(self):
        if self.left >= self.right:
            raise Exception('left >= right')
        elif self.top >= self.bottom:
            raise Exception('top >= bottom')
        self.left = 0 if self.left < 0 else self.left
        self.top = 0 if self.top < 0 else self.top
        self.right = 1 if self.right > 1 else self.right
        self.bottom = 1 if self.bottom > 1 else self.bottom
        # elif min(self.left, self.top, self.right, self.bottom) < 0:
            # raise Exception('invalid range (<0)')
        # elif max(self.left, self.top, self.right, self.bottom) > 1:
            # raise Exception('invalid range (>1)')

    def save(self, *args, **kwargs):
        self.validate_coordinates()
        super(QalculatorBox, self).save(*args, **kwargs)
        # self._save_box_image()
        # if not self.mathpix_latex and not self.latex:
            # # self._save_mathpix_latex()
            # self._do_everything()

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
        super(QalculatorBox, self).save()

    def _save_mathpix_latex(self):
        save_mathpix_latex_async(self.id, self.image.url)

    def __str__(self):
        if self.id:            return 'B%d' % self.id
        return ''

    def _clone_to_testset(self):
        clone_to_testset(self.id)

    def _do_everything(self):
        do_everything(self.id, self.image.url)


class QalculatorBoxTag(models.Model):
    box = models.ForeignKey(QalculatorBox, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
