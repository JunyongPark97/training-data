import requests
import json
from munch import munchify, Munch
import numpy as np
import io, requests
from handwritten.ocr_utils import *

try:
    import cv2
except:
    pass


def download_to_buffer(url):
    resp = requests.get(url, stream=True)
    buffer = io.BytesIO()
    for chunk in resp.iter_content(chunk_size=1024):
        if chunk:
            buffer.write(chunk)
    buffer.seek(0)
    return buffer.read()


def read_image_from_url(url, channel=0):
    '''
        channel:
            - >0: 3-channel color image
            - =0: grayscale image
            - <0: loaded image as is
    '''
    image_data = np.fromstring(download_to_buffer(url), np.uint8)
    img = cv2.imdecode(image_data, channel)
    return img


def rescale_boxes(boxes, width, height):
    '''
    ratio to pixel
    '''
    for box in boxes:
        box.l = box.left * width
        box.r = box.right * width
        box.t = box.top * height
        box.b = box.bottom * height


def get_unicode(text):
    defaults = {
        '-': 8722,
        '*': 215,  # times
        '/': 247,  # div
        '#': ord('{'),  # simeq curly brace
        '\\': 8730,  # sqrt
        'sum': 8721,  # sum
        'int': 8747,  # integral
    }
    if text in defaults:
        return defaults[text]
    try:
        return ord(text)
    except:
        return None


def box_to_dict(box):
    ret_box = Munch()
    ret_box.left = box.left
    ret_box.right = box.right
    ret_box.top = box.top
    ret_box.bottom = box.bottom
    ret_box.confidence = 1.0
    return ret_box


def change_boxes_to_unicode_boxes(boxes):
    ret_boxes = []
    for box in boxes:
        ret_box = box_to_dict(box)
        unicode_ = get_unicode(box.input_text)
        confidence = 1.0
        tmp = Munch()
        tmp.unicode = unicode_
        tmp.confidence = confidence
        ret_box.candidates = [tmp]
        ret_boxes.append(ret_box)
    return ret_boxes


def get_pred_result(image_url):
    '''
    image_url을 받아서 Box Segmentation + Classification 결과를 돌려줍니다.
    '''
    segmentation_url = 'https://ocr-e3-segmentation-181219.mathpresso.net/api/recognize/'
    data = {
        'image_url': image_url,
    }
    resp = requests.post(segmentation_url, data=data)
    ret = resp.json()
    boxes = munchify(ret['boxes'])
    box_candidates = munchify(ret['box_candidates'])
    width = ret['width']
    height = ret['height']

    tmp_cand_boxes = change_seg_box_candidates_format_to_cls_boxes(box_candidates)
    all_seg_boxes = boxes + tmp_cand_boxes
    change_seg_boxes_format_to_cls_boxes(boxes)
    seg_pred_boxes_all = boxes + tmp_cand_boxes
    rescale_boxes(seg_pred_boxes_all, width, height)

    return seg_pred_boxes_all


def get_merge_result(unicode_boxes):
    merger_url = 'http://125.129.239.235:6020/api/merge/'
    merger_data = {
        'boxes': unicode_boxes,
    }

    resp = requests.post(merger_url, json=merger_data)
    ret = resp.json()
    text_lst = ret['result']
    return text_lst


def get_latex_from_merge_result(text_lst):
    ret_latex = []
    for expr_cand in text_lst:
        for expr in expr_cand:
            latex = expr['latex']
            ret_latex.append(latex)
    return ret_latex


def convert_latex_to_mlatex(latex):
    latex = latex.replace('$', '')

    latex = latex.replace('\\frac', '\\dfrac')

    # latex = latex.replace('\\times', '*')

    # latex = latex.replace('\\leq', '\\leqq')
    # latex = latex.replace('\\geq', '\\geqq')

    latex = latex.replace('(', '\\left(')
    latex = latex.replace(')', '\\right)')
    latex = latex.replace('\\{', '\\left(')
    latex = latex.replace('\\}', '\\right)')

    # 얜 못봄
    latex = latex.replace('[', '\\left(')
    latex = latex.replace(']', '\\right)')

    latex = latex.replace(' ', '')
    latex = latex.replace('\\left\\left(\\begin{array}{l}{', '\\begin{cases}')
    latex = latex.replace('}\\\\{', '\\\\')
    latex = latex.replace('}\\end{array}\\right.', '\\end{cases}')

    return latex


def latex_to_length(latex):
    latex = latex.replace('$', '')
    latex = latex.replace('\\leq', '\\leqq')
    latex = latex.replace('\\geq', '\\geqq')

    latex = latex.replace('\\leqq', '<')
    latex = latex.replace('\\geqq', '>')

    latex = latex.replace(' ', '')
    latex = latex.replace('^', '')
    latex = latex.replace('\\frac', '-')

    latex = latex.replace('\\left\\{\\begin{array}{l}{', '')
    latex = latex.replace('}\\\\{', '')
    latex = latex.replace('}\\end{array}\\right.', '#')

    latex = latex.replace('\\{', '(')
    latex = latex.replace('\\}', ')')
    latex = latex.replace('[', '(')
    latex = latex.replace(']', ')')
    latex = latex.replace('\\div', '÷')
    latex = latex.replace('\\sqrt', '√-')
    latex = latex.replace('operatorname', '')
    latex = latex.replace('\\times', '×')

    latex = latex.replace('{', '')
    latex = latex.replace('}', '')

    return len(latex)
