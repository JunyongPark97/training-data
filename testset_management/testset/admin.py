import codecs
import csv
import json

from django.contrib import admin
from django.db.models import Count
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django import forms

from .models import TestSet, TestSetTag, Box
# from .utils import get_pred_result, read_image_from_url, \
        # get_merge_result, latex_to_length, change_boxes_to_unicode_boxes, \
        # rescale_boxes, get_latex_from_merge_result, \
        # convert_latex_to_mlatex

from .utils import *


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}))


class TestSetBoxInline(admin.TabularInline):
    model = Box
    fields = ['image_preview', 'input_text', 'left', 'right', 'top', 'bottom']
    readonly_fields = ['image_preview', 'input_text', 'left', 'right', 'top', 'bottom']

    def image_preview(self, box):
        return mark_safe('<img src="%s" style="max-width:200px;" />' % box.image.url)


class TestSetTagInline(admin.TabularInline):
    model = TestSetTag
    fields = ['key', 'value']


class IsBoxNullFilter(admin.SimpleListFilter):
    title = 'is_box_null'
    parameter_name = 'is_box_null'

    def lookups(self, request, model_admin):
        return [
            (None, '전체'),
            ('true', '박스가 없음'),
            ('false', '박스가 있음'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            queryset = queryset.filter(boxes__isnull=True)
        elif self.value() == 'false':
            queryset = queryset.filter(boxes__isnull=False)
        return queryset


class IsValidFilter(admin.SimpleListFilter):
    title = 'is_valid'
    parameter_name = 'is_valid'

    def lookups(self, request, model_admin):
        return [
            (None, '전체'),
            ('true', 'Valid'),
            ('false', 'Not Valid'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            queryset = queryset.filter(valid=True)
        elif self.value() == 'false':
            queryset = queryset.exclude(valid=True)
        return queryset


class IsPredictValidFilter(admin.SimpleListFilter):
    title = 'predict_valid'
    parameter_name = 'predict_valid'

    def lookups(self, request, model_admin):
        return [
            (None, '전체'),
            ('true', 'Valid'),
            ('false', 'Not Valid'),
            ('notyet', 'Not Yet'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            queryset = queryset.filter(tags__key='pred_valid', tags__value=True)
        elif self.value() == 'false':
            queryset = queryset.filter(tags__key='pred_valid', tags__value=False)
        elif self.value() == 'notyet':
            queryset = queryset.exclude(tags__key='pred_valid')
        return queryset


class IsPredictValid2Filter(admin.SimpleListFilter):
    title = 'predict_valid2'
    parameter_name = 'predict_valid2'

    def lookups(self, request, model_admin):
        return [
            (None, '전체'),
            ('true', 'Valid'),
            ('false', 'Not Valid'),
            ('notyet', 'Not Yet'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            queryset = queryset.filter(tags__key='pred_valid2', tags__value=True)
        elif self.value() == 'false':
            queryset = queryset.filter(tags__key='pred_valid2', tags__value=False)
        elif self.value() == 'notyet':
            queryset = queryset.exclude(tags__key='pred_valid2')
        return queryset


class TestSetAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_preview',
            # 'grade_category',
                    # 'mathpix_latex',
                    # 'pred_latex',
                    'pred_latex2',
                    'boxes_count', 'gt_length',
                    'latex',
                    'pred_valid',
                    'pred_valid2',
                    'valid']
    # list_editable = ['grade_category']
    list_filter = [
            # 'grade_category',
            IsBoxNullFilter, IsValidFilter, IsPredictValidFilter,
            IsPredictValid2Filter]
    actions = [
            'create_pred_boxes',
            'create_pred_latex',
            'create_valid_tag',
            'create_valid_tag_v2',
            # 'run_mathpix',
            ]
    change_list_template = 'testset/admin/testset_change_list.html'
    change_form_template = 'testset/admin/testset_change_form.html'
    inlines = [TestSetBoxInline, TestSetTagInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).annotate(boxes_count=Count('boxes', distinct=True))
        return queryset

    def get_urls(self):
        urls = [path('import_csv/', self.import_csv, name='testset_import_csv'),]
        urls += super().get_urls()
        return urls

    def image_preview(self, testset):
        return mark_safe('<img src="%s" width=300px "/>' % testset.image_url)

    def boxes_count(self, testset):
        return testset.boxes_count

    def import_csv(self, request):
        if request.method == 'POST':
            csv_file = request.FILES['csv_file']
            csv_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(csv_file)
            header = next(reader)
            index = dict()
            index['mathpix_latex'] = header.index('search_request_id')
            index['image_url'] = header.index('image_url')
            index['grade_category'] = header.index('grade_category')
            new_testsets = []
            for line in reader:
                # print(line[index['raw_concept']])
                # print(type(line[index['raw_concept']]))
                new_testset = TestSet(
                    image_url=line[index['image_url']],
                    grade_category=line[index['grade_category']],
                    mathpix_latex=line[index['mathpix_latex']],
                )
                new_testsets.append(new_testset)
            TestSet.objects.bulk_create(new_testsets)

            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        ctx = {
            'form': CsvImportForm(),
            'description': 'Please upload csv. (allowed headers: image_url, grade_category)'
        }
        return render(request, 'testset/admin/csv_form.html', ctx)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        print(extra_context)
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    
    def get_predict_latex(self, testset):
        image = read_image_from_url(testset.image_url)
        h, w = image.shape[:2]

        boxes = testset.boxes.all()
        unicode_boxes = change_boxes_to_unicode_boxes(boxes)
        rescale_boxes(unicode_boxes, w, h)
        try:
            print([chr(box.candidates[0].unicode) for box in unicode_boxes])
        except:
            print(testset.id)
        text_lst = get_merge_result(unicode_boxes)
        result = get_latex_from_merge_result(text_lst)
        print(result)
        defaults={
            'value': json.dumps(result),
        }
        testsettag, _ = TestSetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)


    def get_predict_latex_v2(self, testset):
        image = read_image_from_url(testset.image_url)
        h, w = image.shape[:2]

        boxes = testset.boxes.all()
        unicode_boxes = change_boxes_to_unicode_boxes(boxes)
        rescale_boxes(unicode_boxes, w, h)
        text_lst = get_merge_result_v2(unicode_boxes)
        result = get_latex_from_merge_result(text_lst)
        defaults={
            'value': json.dumps(result),
        }
        testsettag, _ = TestSetTag.objects.update_or_create(testset=testset, key="pred_latex2", defaults=defaults)


    def create_pred_boxes(self, request, queryset):
        valid_queryset = queryset.filter(boxes__isnull=True)
        for testset in valid_queryset:
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

            if not testset.tags.filter(key="pred_latex"):
                self.get_predict_latex(testset)


    def create_pred_latex(self, request, queryset):
        for testset in queryset:
            self.get_predict_latex(testset)


    def create_pred_latex_v2(self, request, queryset):
        for testset in queryset:
            self.get_predict_latex_v2(testset)


    def create_valid_tag(self, request, queryset):
        valid_queryset = queryset
        for testset in valid_queryset:
            if not testset.tags.filter(key="pred_latex"):
                self.get_predict_latex(testset)

            length = testset.boxes.count()
            gt_length = testset.gt_length
            flag = False
            length_flag = length == gt_length
                
            image = read_image_from_url(testset.image_url)
            h, w = image.shape[:2]

            boxes = testset.boxes.all()
            unicode_boxes = change_boxes_to_unicode_boxes(boxes)
            rescale_boxes(unicode_boxes, w, h)
            text_lst = get_merge_result(unicode_boxes)
            result = get_latex_from_merge_result(text_lst)

            defaults={
                'value': json.dumps(result),
            }
            testsettag, _ = TestSetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)

            if not result:
                continue
            gt_latex = testset.latex
            gt_text = convert_latex_to_mlatex(gt_latex)
            for pred_text in result:
                if gt_text == pred_text.replace(' ', ''):
                    flag = True

            defaults = {
                'value': flag and length_flag
            }

            TestSetTag.objects.update_or_create(testset=testset, key="pred_valid", defaults=defaults)


    def create_valid_tag_v2(self, request, queryset):
        valid_queryset = queryset
        total_length = queryset.count()
        for i, testset in enumerate(valid_queryset):
            if i%50 == 0:
                print('{}/{}'.format(i, total_length))
            try:
                # if not testset.tags.filter(key="pred_latex2"):
                image = read_image_from_url(testset.image_url)
                h, w = image.shape[:2]

                boxes = testset.boxes.all()
                unicode_boxes = change_boxes_to_unicode_boxes(boxes)
                rescale_boxes(unicode_boxes, w, h)
                text_lst = get_merge_result_v2(unicode_boxes)
                result = get_latex_from_merge_result(text_lst)
                defaults={
                    'value': json.dumps(result),
                }
                testsettag, _ = TestSetTag.objects.update_or_create(testset=testset, key="pred_latex2", defaults=defaults)

                result = json.loads(testset.tags.filter(key="pred_latex2").first().value)

                # print(result)

                length = testset.boxes.count()
                gt_length = testset.gt_length
                flag = False
                length_flag = length == gt_length
                    
                if not result:
                    continue
                gt_latex = testset.latex
                gt_text = convert_latex_to_mlatex(gt_latex)
                for pred_text in result:
                    # print(pred_text, gt_text)
                    if gt_text == pred_text.replace(' ', ''):
                        flag = True

                defaults = {
                    'value': flag and length_flag
                }

                TestSetTag.objects.update_or_create(testset=testset, key="pred_valid2", defaults=defaults)
            except:
                print(testset.id)



    def pred_latex(self, testset):
        pred_latex = testset.tags.filter(key="pred_latex")
        if pred_latex:
            try:
                text = json.loads(pred_latex.first().value)
            except:
                print(testset.id)
                text = ''

            return ['${}$'.format(i) for i in text]
        else:
            return '$$'


    def pred_valid(self, testset):
        pred_valid = testset.tags.filter(key="pred_valid")
        if pred_valid:
            return pred_valid.first().value
        else:
            return "Not Yet"


    def pred_latex2(self, testset):
        pred_latex = testset.tags.filter(key="pred_latex2")
        if pred_latex:
            try:
                text = json.loads(pred_latex.first().value)
            except:
                print(testset.id)
                text = ''

            return ['${}$'.format(i) for i in text]
        else:
            return '$$'


    def pred_valid2(self, testset):
        pred_valid = testset.tags.filter(key="pred_valid2")
        if pred_valid:
            return pred_valid.first().value
        else:
            return "Not Yet"



    def run_mathpix(self, request, queryset):
        for testset in queryset:
            testset.run_and_save_mathpix()


admin.site.register(TestSet, TestSetAdmin)
admin.site.register(Box)
