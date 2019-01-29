from munch import Munch


def rescale_boxes(boxes, width, height):
    '''
    ratio to pixel
    '''
    for box in boxes:
        box.l = box.left * width
        box.r = box.right * width
        box.t = box.top * height
        box.b = box.bottom * height

    return boxes


def change_seg_boxes_format_to_cls_boxes(boxes):
    for box in boxes:
        unicode_ = box.unicode
        confidence = box.confidence
        tmp = Munch()
        tmp.unicode = unicode_
        tmp.confidence = confidence
        box.candidates = [tmp]


LINES = ['1', 'line']

def change_seg_box_candidates_format_to_cls_boxes(box_candidates):
    ret_lst = []
    for box_candidate in box_candidates:
        ret = Munch()
        ret.confidence = 0
        for box in box_candidate.boxes:
            unicode_ = box.unicode
            confidence = box.confidence
            if box.label in LINES:
                confidence = 0.1
            if ret.confidence < confidence:
                ret.unicode = unicode_
                ret.confidence = confidence
        box_candidate.bounding_box.candidates = [ret]
        ret_lst.append(box_candidate.bounding_box)
    return ret_lst
