import codecs
import csv
import json

import requests
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django import forms
from munch import munchify

# from .models import HandwrittenSource, HandwrittenBox, HandwrittenTestset, Box
from .models import *


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}))


class HandwrittenBoxInline(admin.TabularInline):
    model = HandwrittenBox
    fields = ['get_image', 'left', 'right', 'top', 'bottom']
    readonly_fields = ['get_image']

    def get_image(self, box):
        return mark_safe('<img src="%s" style="max-width:200px;" />' % box.image.url)


class IsHandwrittenBoxNullFilter(admin.SimpleListFilter):
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
            queryset = queryset.filter(boxes__isnull=True).distinct()
        elif self.value() == 'false':
            queryset = queryset.filter(boxes__isnull=False).distinct()
        return queryset


class HandwrittenSourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_image_url', 'valid']
    # list_editable = ['grade', 'grade_category']
    list_filter = [IsHandwrittenBoxNullFilter]
    # change_list_template = 'source/admin/source_change_list.html'
    change_form_template = 'handwritten/admin/source_change_form.html'
    inlines = [HandwrittenBoxInline, ]

    # def get_urls(self):
        # urls = [path('import_csv/', self.import_csv, name='source_import_csv'),]
        # urls += super().get_urls()
        # return urls

    # def get_changelist_form(self, request, **kwargs):
        # return HandwrittenSourceForm

    def get_image_url(self, testset):
        return mark_safe('<img src="%s" width=200px "/>' % testset.image_url)
    get_image_url.short_description = 'image'

    # def import_csv(self, request):
        # if request.method == 'POST':
            # csv_file = request.FILES['csv_file']
            # csv_file = csv_file.read().decode('utf-8').splitlines()
            # reader = csv.reader(csv_file)
            # header = next(reader)
            # grade = {'초': 1, '중': 2, '고': 3}
            # index = dict()
            # index["search_request_id"] = header.index('id')
            # index['image_url'] = header.index('image_key')
            # index['user_id'] = header.index('user_id')
            # index['grade'] = header.index('grade')
            # new_testsets = []
            # for line in reader:
                # new_testset = HandwrittenSource(
                    # search_request_id=line[index["search_request_id"]],
                    # image_key=line[index['image_url']],
                    # user_id=line[index['user_id']],
                    # grade=grade.get(line[index['grade']]),
                # )
                # new_testsets.append(new_testset)
            # HandwrittenSource.objects.bulk_create(new_testsets)

            # self.message_user(request, "Your csv file has been imported")
            # return redirect("..")
        # ctx = {'form': CsvImportForm()}
        # return render(request, 'testset/admin/csv_form.html', ctx)

    def expressions(self, testset):
        return mark_safe('<br>'.join(list(map(lambda x:x.latex, testset.boxes.all()))))

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(HandwrittenSourceAdmin, self).get_readonly_fields(request, obj)
        readonly_fields += ('get_image_url', )
        return readonly_fields

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        print(extra_context)
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


# class IsLatexNullFilter(admin.SimpleListFilter):
    # title = 'is_latex_null'
    # parameter_name = 'is_latex_null'

    # def lookups(self, request, model_admin):
        # return [
            # (None, '전체'),
            # ('true', '수식 없음'),
            # ('false', '수식 있음'),
        # ]

    # def queryset(self, request, queryset):
        # if self.value() == 'true':
            # # queryset = queryset.filter(latex__isnull=True)
            # queryset = queryset.filter(latex='')
        # elif self.value() == 'false':
            # queryset = queryset.exclude(latex='')
        # return queryset


# class IsValidFilter(admin.SimpleListFilter):
    # title = 'is_valid'
    # parameter_name = 'is_valid'

    # def lookups(self, request, model_admin):
        # return [
            # (None, '전체'),
            # ('true', 'Valid'),
            # ('false', 'Not Valid'),
        # ]

    # def queryset(self, request, queryset):
        # if self.value() == 'true':
            # queryset = queryset.filter(valid=True)
        # elif self.value() == 'false':
            # queryset = queryset.exclude(valid=True)
        # return queryset


class IsCopiedFilter(admin.SimpleListFilter):
    title = 'is_copied'
    parameter_name = 'is_copied'

    def lookups(self, request, model_admin):
        return [
            (None, '전체'),
            ('true', 'Already Copied'),
            ('false', 'Not Copied Yet'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            queryset = queryset.filter(testsets__isnull=False).distinct()
        elif self.value() == 'false':
            queryset = queryset.filter(testsets__isnull=True)
        return queryset


class HandwrittenBoxAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'get_image_url', 'left','right','top','bottom', 'valid']
    # list_filter = [IsLatexNullFilter, IsValidFilter, IsCopiedFilter]
    list_filter = [IsCopiedFilter]
    # actions = ['process_mathpix', 'mark_as_valid', 'copy_to_testset']
    actions = ['copy_to_testset']

    # def process_mathpix(self, request, queryset):
        # valid_queryset = queryset.filter(latex='')
        # if valid_queryset.count() > 100:
            # self.message_user(request, "ERROR: Cannot Finish Requests (Requests Count: {})".format(valid_queryset.count()), level=messages.ERROR)
        # else:
            # for box in valid_queryset:
                # box._save_mathpix_latex()
            # self.message_user(request, "Finish {} Requests Successfully".format(valid_queryset.count()))
    # process_mathpix.short_description = "Request Mathpix Latex Result to Drip Server"

    # def mark_as_valid(self, request, queryset):
        # length = queryset.count()
        # queryset.update(valid=True)
        # self.message_user(request, "Finish {} Requests Successfully".format(length))
    # mark_as_valid.short_description = "Mark Selected Boxes Valid"

    def copy_to_testset(self, request, queryset):
        valid_queryset = queryset.filter(valid=True)
        length = valid_queryset.count()
        if length > 100:
            self.message_user(request, "ERROR: Cannot Finish Requests (Requests Count: {})".format(length), level=messages.ERROR)
        else:
            for box in valid_queryset:
                box._clone_to_testset()
            self.message_user(request, "Finish {} Requests Successfully".format(length))
    copy_to_testset.short_description = "Handwritten Box to Handwritten Testset"

    def get_image_url(self, box):
        try:
            return mark_safe('<img src="%s" width=200px "/>' % box.image.url)
        except:
            return ''
    get_image_url.short_description = 'image'


class HandwrittenTestsetBoxInline(admin.TabularInline):
    model = Box
    fields = ['image_preview', 'input_text', 'left', 'right', 'top', 'bottom']
    readonly_fields = ['image_preview', 'input_text', 'left', 'right', 'top', 'bottom']

    def image_preview(self, box):
        return mark_safe('<img src="%s" style="max-width:200px;" />' % box.image.url)


class HandwrittenTestsetTagInline(admin.TabularInline):
    model = HandwrittenTestsetTag
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


# class IsPredictValidFilter(admin.SimpleListFilter):
    # title = 'predict_valid'
    # parameter_name = 'predict_valid'

    # def lookups(self, request, model_admin):
        # return [
            # (None, '전체'),
            # ('true', 'Valid'),
            # ('false', 'Not Valid'),
            # ('notyet', 'Not Yet'),
        # ]

    # def queryset(self, request, queryset):
        # if self.value() == 'true':
            # queryset = queryset.filter(tags__key='pred_valid', tags__value=True)
        # elif self.value() == 'false':
            # queryset = queryset.filter(tags__key='pred_valid', tags__value=False)
        # elif self.value() == 'notyet':
            # queryset = queryset.exclude(tags__key='pred_valid')
        # return queryset


class HandwrittenTestsetAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_preview',
            # 'grade_category',
                    # 'mathpix_latex',
                    'pred_latex',
                    'boxes_count', 'gt_length',
                    'latex',
                    'pred_valid', 'valid']
    # list_editable = ['grade_category']
    list_filter = [
            # 'grade_category',
            IsBoxNullFilter, IsValidFilter,
            # IsPredictValidFilter,
            ]
    actions = [
            # 'create_pred_boxes',
            'create_pred_latex',
            # 'create_valid_tag',
            # # 'run_mathpix',
            ]
    # change_list_template = 'testset/admin/testset_change_list.html'
    change_form_template = 'handwritten/admin/testset_change_form.html'
    inlines = [HandwrittenTestsetBoxInline, HandwrittenTestsetTagInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).annotate(boxes_count=Count('boxes', distinct=True))
        return queryset

    # def get_urls(self):
        # urls = [path('import_csv/', self.import_csv, name='testset_import_csv'),]
        # urls += super().get_urls()
        # return urls

    def image_preview(self, testset):
        return mark_safe('<img src="%s" width=300px "/>' % testset.image_url)

    def boxes_count(self, testset):
        return testset.boxes_count

    # def import_csv(self, request):
        # if request.method == 'POST':
            # csv_file = request.FILES['csv_file']
            # csv_file = csv_file.read().decode('utf-8').splitlines()
            # reader = csv.reader(csv_file)
            # header = next(reader)
            # index = dict()
            # index['mathpix_latex'] = header.index('search_request_id')
            # index['image_url'] = header.index('image_url')
            # index['grade_category'] = header.index('grade_category')
            # new_testsets = []
            # for line in reader:
                # # print(line[index['raw_concept']])
                # # print(type(line[index['raw_concept']]))
                # new_testset = HandwrittenTestset(
                    # image_url=line[index['image_url']],
                    # grade_category=line[index['grade_category']],
                    # mathpix_latex=line[index['mathpix_latex']],
                # )
                # new_testsets.append(new_testset)
            # HandwrittenTestset.objects.bulk_create(new_testsets)

            # self.message_user(request, "Your csv file has been imported")
            # return redirect("..")
        # ctx = {
            # 'form': CsvImportForm(),
            # 'description': 'Please upload csv. (allowed headers: image_url, grade_category)'
        # }
        # return render(request, 'testset/admin/csv_form.html', ctx)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        print(extra_context)
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


    # def get_predict_latex(self, testset):
        # image = read_image_from_url(testset.image_url)
        # h, w = image.shape[:2]

        # boxes = testset.boxes.all()
        # unicode_boxes = change_boxes_to_unicode_boxes(boxes)
        # rescale_boxes(unicode_boxes, w, h)
        # try:
            # print([chr(box.candidates[0].unicode) for box in unicode_boxes])
        # except:
            # print(testset.id)
        # text_lst = get_merge_result(unicode_boxes)
        # result = get_latex_from_merge_result(text_lst)
        # print(result)
        # defaults={
            # 'value': json.dumps(result),
        # }
        # testsettag, _ = HandwrittenTestsetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)


    # def create_pred_boxes(self, request, queryset):
        # valid_queryset = queryset.filter(boxes__isnull=True)
        # for testset in valid_queryset:
            # unicode_boxes = get_pred_result(testset.image_url)
            # for box in unicode_boxes:
                # unicode_ = box.candidates[0].unicode
                # Box.objects.create(testset=testset,
                                   # left=box.left,
                                   # right=box.right,
                                   # top=box.top,
                                   # bottom=box.bottom,
                                   # input_text = chr(unicode_),
                                   # unicode_value = unicode_)

            # if not testset.tags.filter(key="pred_latex"):
                # self.get_predict_latex(testset)


    def create_pred_latex(self, request, queryset):
        for testset in queryset:
            update_pred_latex(testset.id)
            # self.get_predict_latex(testset)


    # def create_valid_tag(self, request, queryset):
        # valid_queryset = queryset
        # for testset in valid_queryset:
            # if not testset.tags.filter(key="pred_latex"):
                # self.get_predict_latex(testset)

            # length = testset.boxes.count()
            # gt_length = testset.gt_length
            # flag = False
            # length_flag = length == gt_length
                
            # image = read_image_from_url(testset.image_url)
            # h, w = image.shape[:2]

            # boxes = testset.boxes.all()
            # unicode_boxes = change_boxes_to_unicode_boxes(boxes)
            # rescale_boxes(unicode_boxes, w, h)
            # text_lst = get_merge_result(unicode_boxes)
            # result = get_latex_from_merge_result(text_lst)

            # defaults={
                # 'value': json.dumps(result),
            # }
            # testsettag, _ = HandwrittenTestsetTag.objects.update_or_create(testset=testset, key="pred_latex", defaults=defaults)

            # if not result:
                # continue
            # gt_latex = testset.latex
            # gt_text = convert_latex_to_mlatex(gt_latex)
            # for pred_text in result:
                # if gt_text == pred_text.replace(' ', ''):
                    # flag = True

            # defaults = {
                # 'value': flag and length_flag
            # }

            # HandwrittenTestsetTag.objects.update_or_create(testset=testset, key="pred_valid", defaults=defaults)


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


    # def run_mathpix(self, request, queryset):
        # for testset in queryset:
            # testset.run_and_save_mathpix()


admin.site.register(HandwrittenTestset, HandwrittenTestsetAdmin)
admin.site.register(Box)
admin.site.register(HandwrittenSource, HandwrittenSourceAdmin)
admin.site.register(HandwrittenBox, HandwrittenBoxAdmin)
