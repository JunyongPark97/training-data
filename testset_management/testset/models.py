import json
import random
import string
from io import BytesIO
import requests

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.safestring import mark_safe

from source.models import OCRSearchRequestBox
from .utils import *
# from core.task_utils import lambda_task


PRECISION = 4
THRESHOLD = 0.1 ** PRECISION


def get_box_filename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)) + '.jpg'


def equals(f1, f2):
    return abs(f1 - f2) < THRESHOLD


class SmallBoxException(Exception):
    pass


class Image(models.Model):
    image = models.ImageField(upload_to='image')


class TestSet(models.Model):
    image_url = models.URLField()
    grade_category = models.IntegerField(blank=True,
                                         null=True,
                                         choices=((1, '1'),(2, '2'), (3,'3'), (4,'4')))
    ocrsr_box = models.ForeignKey(OCRSearchRequestBox, related_name='testsets', blank=True, null=True,
                                  on_delete=models.CASCADE)
    mathpix_latex = models.CharField(max_length=500, blank=True)
    latex = models.CharField(max_length=500, blank=True)
    valid = models.NullBooleanField(default=None)

    @property
    def prev(self):
        return TestSet.objects.filter(pk__lt=self.pk).order_by('pk').last()

    @property
    def next(self):
        return TestSet.objects.filter(pk__gt=self.pk).order_by('pk').first()

    @property
    def prev_notvalid(self):
        # print(TestSet.objects.filter(pk__lt=self.pk).filter(valid=None).filter(tags__key='pred_valid', tags__value=False).order_by('pk'))
        return TestSet.objects.filter(pk__lt=self.pk).filter(valid=None).filter(tags__key='pred_valid', tags__value=False).order_by('pk').last()

    @property
    def next_notvalid(self):
        # print(TestSet.objects.filter(pk__gt=self.pk).filter(valid=None).filter(tags__key='pred_valid', tags__value=False).order_by('pk'))
        return TestSet.objects.filter(pk__gt=self.pk).filter(valid=None).filter(tags__key='pred_valid', tags__value=False).order_by('pk').first()

    @property
    def prev_valid(self):
        return TestSet.objects.filter(pk__lt=self.pk).filter(valid=False).order_by('pk').last()

    @property
    def next_valid(self):
        return TestSet.objects.filter(pk__gt=self.pk).filter(valid=False).order_by('pk').first()


    @property
    def gt_length(self):
        return latex_to_length(self.latex)

    def save(self, *args, **kwargs):
        super(TestSet, self).save(*args, **kwargs)
        if not self.boxes.all().exists():
            self._do_everything()

    def run_and_save_mathpix(self):
        import requests
        url = 'http://drip-server-production.ap-northeast-2.elasticbeanstalk.com/api/image:processParallel'
        data = {
            "image_url": self.image_url,
            "requests": [
                {
                    "backend": "mathpix",
                    "version": 1,
                    "use_cache": True
                }
            ]
        }
        resp = requests.post(url, json=data)
        if resp.ok:
            try:
                self.mathpix_latex = '$' + resp.json()[0]["data"]["latex"] + '$'
                self.latex = self.mathpix_latex
                super().save()
            except:
                pass

    def get_image_extension(self):
        extension = self.image_url.split('.')[-1]
        if extension.lower() == 'jpg':
            extension = 'jpeg'
        return extension

    def _do_everything(self):
        do_everything(self.id)


class TestSetTag(models.Model):
    testset = models.ForeignKey(TestSet, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=500)


class Box(models.Model):
    """
    Character 정보를 저장하는 box.
    """
    testset = models.ForeignKey(TestSet, related_name='boxes', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='box')
    left = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    top = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    right = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    bottom = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    input_text = models.CharField(max_length=200, help_text='Boxing UI에서 입력한 값')
    unicode_value = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        super(Box, self).save(*args, **kwargs)
        # self._save_box_image()

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
        resp = requests.get(self.testset.image_url)
        image = Image.open(BytesIO(resp.content))
        width, height = image.size
        left = width * self.left
        top = height * self.top
        right = width * self.right
        bottom = height * self.bottom
        crop_data = image.crop((int(left), int(top), int(right), int(bottom)))
        # http://stackoverflow.com/questions/3723220/how-do-you-convert-a-pil-image-to-a-django-file
        crop_io = BytesIO()
        crop_data.save(crop_io, format=self.testset.get_image_extension())
        crop_file = InMemoryUploadedFile(crop_io, None, get_box_filename(), 'image/jpeg', len(crop_io.getvalue()), None)
        self.image.save(get_box_filename(), crop_file, save=False)
        # To avoid recursive save, call super.save
        super(Box, self).save()

    def __str__(self):
        if self.id:
            return 'B{}'.format(self.id)
        return 'Box'

    @property
    def escaped_input_text(self):
        # template에서 "\" 를 escape 해서 보여주기 위함
        return self.input_text.replace('\\', '\\\\')


class BoxTag(models.Model):
    box = models.ForeignKey(Box, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)


# @lambda_task
def do_everything(testset_id):
    try:
        testset = TestSet.objects.get(id=testset_id)
        unicode_boxes = get_pred_result(testset.image_url)
        for box in unicode_boxes:
            unicode_ = box.candidates[0].unicode
            Box.objects.create(testset=testset,
                               left=box.left,
                               right=box.right,
                               top=box.top,
                               bottom=box.bottom,
                               input_text = chr(unicode_),
                               unicode_value = unicode_)

        text_lst = get_merge_result(unicode_boxes)
        result = get_latex_from_merge_result(text_lst)
        defaults={
            'value': json.dumps(result),
        }
        testsettag, _ = TestSetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)

        length = testset.boxes.count()
        gt_length = testset.gt_length
        flag = False
        if length == gt_length:
            pred_texts = testset.tags.filter(key="pred_latex").first()
            if not pred_texts:
                return
            gt_latex = testset.latex
            gt_text = convert_latex_to_mlatex(gt_latex)
            for pred_text in json.loads(pred_texts.value):
                if gt_text == pred_text.replace(' ', ''):
                    flag = True

        defaults = {
            'value': flag
        }

        TestSetTag.objects.update_or_create(testset=testset, key="pred_valid", defaults=defaults)

    except:
        import traceback
        traceback.print_exc()
