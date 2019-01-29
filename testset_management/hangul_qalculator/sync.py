from source.models import *
from testset.models import *
from hangul_qalculator.models import *
from munch import Munch, munchify


def get_ltrb_from_box(box):
    return box.left, box.top, box.right, box.bottom


def find_all_boxes(testset, left, top, right, bottom):
    lst = []
    if not testset:
        return lst
    width = right - left
    height = bottom - top
    for box in testset.boxes.all():
        l, t, r, b = get_ltrb_from_box(box)
        input_text = box.input_text
        final_l = left + l * width
        final_r = left + r * width
        final_t = top + t * height
        final_b = top + b * height
        tmp = Munch()
        tmp.left = final_l
        tmp.right = final_r
        tmp.top = final_t
        tmp.bottom = final_b
        tmp.input_text = input_text
        lst.append(tmp)
    return lst


queryset = OCRSearchRequestSource.objects.filter(boxes__testsets__valid=True).distinct()

ocrsr_source_ids = queryset.values_list('id', flat=True)

existing_ids = QalculatorSource.objects.values_list('ocrsr_source__id', flat=True).distinct()


target_ocrsr_source_ids = list(set(ocrsr_source_ids) - set(existing_ids))

print(target_ocrsr_source_ids[:5])
print(len(target_ocrsr_source_ids))

queryset = queryset.filter(id__in=target_ocrsr_source_ids)

for source in queryset[:5]:
    ocrsr_box = source.boxes.all()
    lst = []
    for box in ocrsr_box:
        testset = box.testsets.filter(valid=True).first()
        l, t, r, b = get_ltrb_from_box(box)
        if testset:
            tmp_lst = find_all_boxes(testset, l, t, r, b)
            lst += tmp_lst
    if lst:
        image_key = source.image_key
        user_id = source.user_id
        search_request_id = source.search_request_id

        qalculator_source = QalculatorSource.objects.create(
                search_request_id = search_request_id,
                image_key = image_key,
                user_id = user_id,
                ocrsr_source = source)
        
        qalculator_box_lst = []
        for tmpbox in lst:
            qalc_box = QalculatorBox(
                    source = qalculator_source,
                    left = tmpbox.left,
                    right = tmpbox.right,
                    bottom = tmpbox.bottom,
                    top = tmpbox.top,
                    input_text = tmpbox.input_text)
            qalculator_box_lst.append(qalc_box)
        QalculatorBox.objects.bulk_create(qalculator_box_lst)
    


