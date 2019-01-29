import random
import requests
import string
from io import BytesIO
import requests

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.safestring import mark_safe

# from core.task_utils import lambda_task

PRECISION = 4
THRESHOLD = 0.1 ** PRECISION


def get_box_filename():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)) + '.jpg'


def equals(f1, f2):
    return abs(f1 - f2) < THRESHOLD


class SmallOCRSearchRequestBoxException(Exception):
    pass


class OCRSearchRequestSource(models.Model):
    search_request_id = models.CharField(max_length=100)
    image_key = models.UUIDField()
    user_id = models.IntegerField()
    grade = models.IntegerField(blank=True, null=True)
    grade_category = models.IntegerField(blank=True,
                                         null=True,
                                         choices=((1, '1'),(2, '2'), (3,'3'),(4,'4')))

    def get_image_extension(self):
        return 'jpeg'

    @property
    def image_url(self):
        return 'https://qanda-storage.s3.amazonaws.com/{}.jpg'.format(self.image_key)

    @property
    def prev(self):
        return OCRSearchRequestSource.objects.filter(pk__lt=self.pk).order_by('pk').last()

    @property
    def next(self):
        return OCRSearchRequestSource.objects.filter(pk__gt=self.pk).order_by('pk').first()


class OCRSearchRequestBox(models.Model):
    source = models.ForeignKey(OCRSearchRequestSource, related_name='boxes', on_delete=models.CASCADE)
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
        # elif min(self.left, self.top, self.right, self.bottom) < 0:
            # raise Exception('invalid range (<0)')
        # elif max(self.left, self.top, self.right, self.bottom) > 1:
            # raise Exception('invalid range (>1)')

    def save(self, *args, **kwargs):
        self.validate_coordinates()
        super(OCRSearchRequestBox, self).save(*args, **kwargs)
        self._save_box_image()
        if not self.mathpix_latex and not self.latex:
            # self._save_mathpix_latex()
            self._do_everything()

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
        super(OCRSearchRequestBox, self).save()

    def _save_mathpix_latex(self):
        save_mathpix_latex_async(self.id, self.image.url)

    def __str__(self):
        if self.id:
            return 'B%d' % self.id
        return ''

    def _clone_to_testset(self):
        clone_to_testset(self.id)

    def _do_everything(self):
        do_everything(self.id, self.image.url)


class OCRSearchRequestBoxTag(models.Model):
    box = models.ForeignKey(OCRSearchRequestBox, related_name='tags', on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)


# @lambda_task
def save_mathpix_latex_async(box_id, image_url):
    url = 'http://drip-server-production.ap-northeast-2.elasticbeanstalk.com/api/image:processParallel'
    data = {
        "image_url": image_url,
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
            box = OCRSearchRequestBox.objects.get(id=box_id)
            box.mathpix_latex = '$' + resp.json()[0]["data"]["latex"] + '$'
            box.latex = box.mathpix_latex
            box.save()
        except:
            import traceback
            traceback.print_exc()


# @lambda_task
def clone_to_testset(box_id):
    from testset.models import TestSet
    try:
        box = OCRSearchRequestBox.objects.get(id=box_id)
        image_url = box.image.url
        grade_category = box.source.grade_category
        mathpix_latex = box.mathpix_latex
        latex = box.latex

        data = {
            'image_url': image_url, 
            'grade_category': grade_category,
            'mathpix_latex': mathpix_latex,
            'latex': latex,
        }

        testset, _ = TestSet.objects.get_or_create(ocrsr_box=box, defaults=data)
    except:
        import traceback
        traceback.print_exc()



# @lambda_task
def do_everything(box_id, image_url):
    url = 'http://drip-server-production.ap-northeast-2.elasticbeanstalk.com/api/image:processParallel'
    data = {
        "image_url": image_url,
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
            box = OCRSearchRequestBox.objects.get(id=box_id)
            box.mathpix_latex = '$' + resp.json()[0]["data"]["latex"] + '$'
            box.latex = box.mathpix_latex
            box.save()
        except:
            import traceback
            traceback.print_exc()

    from testset.models import TestSet
    try:
        box = OCRSearchRequestBox.objects.get(id=box_id)
        image_url = box.image.url
        grade_category = box.source.grade_category
        mathpix_latex = box.mathpix_latex
        latex = box.latex

        data = {
            'image_url': image_url, 
            'grade_category': grade_category,
            'mathpix_latex': mathpix_latex,
            'latex': latex,
        }

        testset, _ = TestSet.objects.get_or_create(ocrsr_box=box, defaults=data)
    except:
        import traceback
        traceback.print_exc()
