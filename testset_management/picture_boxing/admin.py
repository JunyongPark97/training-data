import codecs
import csv
import json

import requests
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django import forms
from munch import munchify

from .models import Source, Box


class SourceForm(forms.ModelForm):
    grade = forms.ChoiceField(choices=((i, i) for i in range(1,7)))


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={'accept': ".csv"}))


class BoxInline(admin.TabularInline):
    model = Box
    fields = ['get_image', 'label', 'left', 'right', 'top', 'bottom']
    readonly_fields = ['get_image','label']

    def get_image(self, box):
        return mark_safe('<img src="%s" style="max-width:200px;" />' % box.image.url)


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


class SourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_image_url', 'grade', 'grade_category',
                    ]
    list_editable = ['grade', 'grade_category']
    list_filter = [IsBoxNullFilter]
    change_list_template = 'source/admin/source_change_list.html'
    change_form_template = 'picture_boxing/admin/source_change_form.html'
    inlines = [BoxInline, ]
    actions = (
        'get_word_boxes',
    )

    def get_word_boxes(self, request, queryset):
        boxes = []
        for source in queryset:
            resp = requests.post('http://222.110.255.105:7722/api/detect/', data={'image_url': source.image_url})
            box_info = munchify(json.loads(resp.text)['boxes'])
            for box in box_info:
                boxes.append(Box(source=source, top=box.top, bottom=box.bottom, right=box.right, left=box.left))
        Box.objects.bulk_create(boxes)

    def get_urls(self):
        urls = [path('import_csv/', self.import_csv, name='source_import_csv'),]
        urls += super().get_urls()
        return urls

    def get_changelist_form(self, request, **kwargs):
        return SourceForm

    def get_image_url(self, testset):
        return mark_safe('<img src="%s" width=200px "/>' % testset.image_url)
    get_image_url.short_description = 'image'

    def import_csv(self, request):
        if request.method == 'POST':
            csv_file = request.FILES['csv_file']
            csv_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(csv_file)
            header = next(reader)
            grade = {'초': 1, '중': 2, '고': 3}
            index = dict()
            index["search_request_id"] = header.index('id')
            index['image_url'] = header.index('image_key')
            index['user_id'] = header.index('user_id')
            index['grade'] = header.index('grade')
            new_testsets = []
            for line in reader:
                new_testset = Source(
                    search_request_id=line[index["search_request_id"]],
                    image_key=line[index['image_url']],
                    user_id=line[index['user_id']],
                    grade=grade.get(line[index['grade']]),
                )
                new_testsets.append(new_testset)
            Source.objects.bulk_create(new_testsets)

            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        ctx = {'form': CsvImportForm()}
        return render(request, 'testset/admin/csv_form.html', ctx)

    def expressions(self, testset):
        return mark_safe('<br>'.join(list(map(lambda x:x.latex, testset.boxes.all()))))

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(SourceAdmin, self).get_readonly_fields(request, obj)
        readonly_fields += ('get_image_url', )
        return readonly_fields

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        print(extra_context)
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


class IsLatexNullFilter(admin.SimpleListFilter):
    title = 'is_latex_null'
    parameter_name = 'is_latex_null'

    def lookups(self, request, model_admin):
        return [
            (None, '전체'),
            ('true', '수식 없음'),
            ('false', '수식 있음'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'true':
            # queryset = queryset.filter(latex__isnull=True)
            queryset = queryset.filter(latex='')
        elif self.value() == 'false':
            queryset = queryset.exclude(latex='')
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


class BoxAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'get_image_url', 'label', 'left','right','top','bottom', 'valid']
    list_filter = [IsLatexNullFilter, IsValidFilter, IsCopiedFilter]
    actions = ['process_mathpix', 'mark_as_valid', 'copy_to_testset']

    def process_mathpix(self, request, queryset):
        valid_queryset = queryset.filter(latex='')
        if valid_queryset.count() > 100:
            self.message_user(request, "ERROR: Cannot Finish Requests (Requests Count: {})".format(valid_queryset.count()), level=messages.ERROR)
        else:
            for box in valid_queryset:
                box._save_mathpix_latex()
            self.message_user(request, "Finish {} Requests Successfully".format(valid_queryset.count()))
    process_mathpix.short_description = "Request Mathpix Latex Result to Drip Server"

    def mark_as_valid(self, request, queryset):
        length = queryset.count()
        queryset.update(valid=True)
        self.message_user(request, "Finish {} Requests Successfully".format(length))
    mark_as_valid.short_description = "Mark Selected Boxes Valid"

    def copy_to_testset(self, request, queryset):
        valid_queryset = queryset.filter(valid=True)
        length = valid_queryset.count()
        if length > 100:
            self.message_user(request, "ERROR: Cannot Finish Requests (Requests Count: {})".format(length), level=messages.ERROR)
        else:
            for box in valid_queryset:
                box._clone_to_testset()
            self.message_user(request, "Finish {} Requests Successfully".format(length))
    copy_to_testset.short_description = "Selected Valid OCRSearchRequest Boxes to Testset"

    def get_image_url(self, box):
        try:
            return mark_safe('<img src="%s" width=200px "/>' % box.image.url)
        except:
            return ''
    get_image_url.short_description = 'image'


admin.site.register(Source, SourceAdmin)
admin.site.register(Box, BoxAdmin)
