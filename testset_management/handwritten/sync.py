from handwritten.models import *


def get_duplicate_ids(queryset):
    existing_answer_reply_ids = list(HandwrittenSource.objects.values_list('answer_reply_id', flat=True))
    answer_reply_ids = list(queryset.values_list('id', flat=True))
    duplicates = [i for i in answer_reply_ids if str(i) in existing_answer_reply_ids]
    return duplicates

def get_unique_ids(queryset):
    existing_answer_reply_ids = list(HandwrittenSource.objects.values_list('answer_reply_id', flat=True))
    answer_reply_ids = list(queryset.values_list('id', flat=True))
    uniques = [i for i in answer_reply_ids if str(i) not in existing_answer_reply_ids]
    return uniques


def copy_qanda_answer_reply_to_handwritten_source(queryset=None):
    '''
    queryset: QandaAnswerReply queryset

    queryset = QandaAnswerReply.objects.filter(~~)
    unique_ids = get_unique_ids(queryset)
    queryset = QandaAnswerReply.objects.filter(id__in=unique_ids)
    copy_qanda_answer_reply_to_handwritten_source(queryset)
    '''
    if not queryset:
        return

    if get_duplicate_ids(queryset):
        raise Exception('Duplicate Answer Reply Detected!')

    source_lst = []
    count = 0
    for ar in queryset:
        if not ar.image_key:
            continue
        try:
            ar.author.teacher_profile
        except:
            continue

        image_key = ar.image_key
        user_id = ar.author.id
        answer_reply_id = ar.id

        source = HandwrittenSource(answer_reply_id = answer_reply_id,
                                   image_key = image_key,
                                   user_id = user_id)

        source_lst.append(source)
        count += 1

    print("Total Count:", count)
    HandwrittenSource.objects.bulk_create(source_lst)


def copy_qanda_answer_reply_to_handwritten_source_limit(queryset=None, limit=50):
    '''
    queryset: QandaAnswerReply queryset

    queryset = QandaAnswerReply.objects.filter(~~)
    unique_ids = get_unique_ids(queryset)
    queryset = QandaAnswerReply.objects.filter(id__in=unique_ids)
    copy_qanda_answer_reply_to_handwritten_source(queryset)
    '''
    if not queryset:
        return

    source_lst = []
    count = 0
    for ar in queryset:
        if not ar.image_key:
            continue
        try:
            ar.author.teacher_profile
        except:
            continue

        image_key = ar.image_key
        user_id = ar.author.id
        answer_reply_id = ar.id

        source = HandwrittenSource(answer_reply_id = answer_reply_id,
                                   image_key = image_key,
                                   user_id = user_id)

        source_lst.append(source)
        count += 1

        if count == limit:
            break

    print("Total Count:", count)
    HandwrittenSource.objects.bulk_create(source_lst)
