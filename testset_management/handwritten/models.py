import random
import string
from io import BytesIO

import requests
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from source.models import equals
from .utils import *
from core.task_utils import lambda_task

PRECISION = 4
THRESHOLD = 0.1 ** PRECISION

def get_box_filename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)) + '.jpg'

@lambda_task
def clone_to_testset(box_id):
    try:
        box = HandwrittenBox.objects.get(id=box_id)
        image_url = box.image.url
        mathpix_latex = box.mathpix_latex
        latex = box.latex

        data = {
            'image_url': image_url,
            'mathpix_latex': mathpix_latex,
            'latex': latex,
        }

        testset, _ = HandwrittenTestset.objects.get_or_create(handwritten_box=box, defaults=data)
    except:
        import traceback
        traceback.print_exc()

class HandwrittenSource(models.Model):
    answer_reply_id = models.CharField(max_length=100)
    image_key = models.UUIDField()
    user_id = models.IntegerField()
    valid = models.NullBooleanField()

    def get_image_extension(self):
        return 'jpeg'

    @property
    def image_url(self):
        return 'https://qanda-storage.s3.amazonaws.com/{}.jpg'.format(self.image_key)

    @property
    def prev(self):
        return HandwrittenSource.objects.filter(pk__lt=self.pk).order_by('pk').last()

    @property
    def next(self):
        return HandwrittenSource.objects.filter(pk__gt=self.pk).order_by('pk').first()


class HandwrittenBox(models.Model):
    source = models.ForeignKey(HandwrittenSource, related_name='boxes', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='box')
    left = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    top = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    right = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    bottom = models.DecimalField(max_digits=PRECISION+1, decimal_places=PRECISION)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mathpix_latex = models.CharField(blank=True, max_length=500)
    latex = models.CharField(blank=True, max_length=500)
    valid = models.NullBooleanField(default=None)

    def validate_coordinates(self):
        if self.left >= self.right:
            raise Exception('left >= right')
        elif self.top >= self.bottom:
            raise Exception('top >= bottom')
        self.left = 0 if self.left < 0 else self.left
        self.top = 0 if self.top < 0 else self.top
        self.right = 1 if self.right > 1 else self.right
        self.bottom = 1 if self.bottom > 1 else self.bottom

    def save(self, *args, **kwargs):
        self.validate_coordinates()
        super(HandwrittenBox, self).save(*args, **kwargs)
        self._save_box_image()
        self._clone_to_testset()

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
        super(HandwrittenBox, self).save()

    def __str__(self):
        if self.id:
            return 'B%d' % self.id
        return ''

    def _clone_to_testset(self):
        clone_to_testset(self.id)


class HandwrittenBoxTag(models.Model):
    box = models.ForeignKey(HandwrittenBox, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)


class HandwrittenTestset(models.Model):
    image_url = models.URLField()
    handwritten_box = models.ForeignKey(HandwrittenBox, related_name='testsets', blank=True, null=True,
                                  on_delete=models.CASCADE)
    mathpix_latex = models.CharField(max_length=500, blank=True)
    latex = models.CharField(max_length=500, blank=True)
    valid = models.NullBooleanField(default=None)

    @property
    def prev(self):
        return HandwrittenTestset.objects.filter(pk__lt=self.pk).order_by('pk').last()

    @property
    def next(self):
        return HandwrittenTestset.objects.filter(pk__gt=self.pk).order_by('pk').first()

    # @property
    # def prev_notvalid(self):
        # return HandwrittenTestset.objects.filter(pk__lt=self.pk).filter(valid=None).filter(tags__key='pred_valid', tags__value=False).order_by('pk').last()

    # @property
    # def next_notvalid(self):
        # return HandwrittenTestset.objects.filter(pk__gt=self.pk).filter(valid=None).filter(tags__key='pred_valid', tags__value=False).order_by('pk').first()

    # @property
    # def prev_valid(self):
        # return HandwrittenTestset.objects.filter(pk__lt=self.pk).filter(valid=False).order_by('pk').last()

    # @property
    # def next_valid(self):
        # return HandwrittenTestset.objects.filter(pk__gt=self.pk).filter(valid=False).order_by('pk').first()


    @property
    def gt_length(self):
        return latex_to_length(self.latex)

    def save(self, *args, **kwargs):
        super(HandwrittenTestset, self).save(*args, **kwargs)
        if not self.boxes.all().exists():
            self._do_everything()
        # else:
            # self._update_pred_latex()

    def get_image_extension(self):
        extension = self.image_url.split('.')[-1]
        if extension.lower() == 'jpg':
            extension = 'jpeg'
        return extension

    def _do_everything(self):
        do_everything(self.id)

    def _update_pred_latex(self):
        update_pred_latex(self.id)


class HandwrittenTestsetTag(models.Model):
    testset = models.ForeignKey(HandwrittenTestset, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=500)


class Box(models.Model):
    """
    Character 정보를 저장하는 box.
    """
    testset = models.ForeignKey(HandwrittenTestset, related_name='boxes', on_delete=models.CASCADE)
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


@lambda_task
def do_everything(testset_id):
    try:
        testset = HandwrittenTestset.objects.get(id=testset_id)
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
        testsettag, _ = HandwrittenTestsetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)

        # length = testset.boxes.count()
        # gt_length = testset.gt_length
        # flag = False
        # if length == gt_length:
            # pred_texts = testset.tags.filter(key="pred_latex").first()
            # if not pred_texts:
                # return
            # gt_latex = testset.latex
            # gt_text = convert_latex_to_mlatex(gt_latex)
            # for pred_text in json.loads(pred_texts.value):
                # if gt_text == pred_text.replace(' ', ''):
                    # flag = True

        # defaults = {
            # 'value': flag
        # }

        # HandwrittenTestsetTag.objects.update_or_create(testset=testset, key="pred_valid", defaults=defaults)

    except:
        import traceback
        traceback.print_exc()

# @lambda_task
def update_pred_latex(testset_id):
    try:
        testset = HandwrittenTestset.objects.get(id=testset_id)

        image = read_image_from_url(testset.image_url)
        h, w = image.shape[:2]

        boxes = testset.boxes.all()
        unicode_boxes = change_boxes_to_unicode_boxes(boxes)
        rescale_boxes(unicode_boxes, w, h)

        # print([chr(box.candidates[0].unicode) for box in unicode_boxes])

        text_lst = get_merge_result(unicode_boxes)
        result = get_latex_from_merge_result(text_lst)

        # print(result)

        defaults={
            'value': json.dumps(result),
        }
        testsettag, _ = HandwrittenTestsetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)
    except:
        pass
