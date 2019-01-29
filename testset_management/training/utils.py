import requests
import json
from munch import munchify, Munch
import re
import io
import numpy as np
import urllib

from PIL import Image, ImageFont, ImageDraw
import PIL.Image
import cv2
import base64


def get_ocr_results(image_url):
    drip_endpoint = 'http://drip-server-production.ap-northeast-2.elasticbeanstalk.com/api/result:list?'
    data = 'image_url={}'
    
    resp = requests.get(drip_endpoint + data.format(image_url))
    if not resp.json():
        print('Process OCR...')
        drip_endpoint = 'http://drip-server-production.ap-northeast-2.elasticbeanstalk.com/api/image:processParallel'
        data = {
            "image_url": image_url,
            "requests": [
                {
                    "backend": "google_vision",
                    "version": 1,
                    "use_cache": True
                }
            ]
        }
        resp = requests.post('http://drip-server-production.ap-northeast-2.elasticbeanstalk.com/api/image:processParallel', json=data)
    if not resp.json():
        return []
    
    flag = False
    for ret in resp.json():
        if ret['backend_name'] == 'google_vision':
            flag = True
#         print(ret['backend_name'])
#     print()
    if not flag:
        return []
    return resp.json()

def get_rectangle(vertices):
    x0 = vertices[0]['x']
    y0 = vertices[0]['y']

    cx = 0
    cy = 0

    for vertex in vertices:
        cx += vertex['x']
        cy += vertex['y']

    cx/=4
    cy/=4

    if x0 < cx:
        if y0 < cy:
            return 0
        else:
            return 270
    else:
        if y0 < cy:
            return 90
        else:
            return 180

def get_angle(text_annotations):
    d = {0:0, 90:0, 180:0, 270:0}

    for result in text_annotations[1:]:
        try:
            vertices = result['boundingPoly']['vertices']
            d[get_rectangle(vertices)]+=1
        except:
            pass

    max_count = 0
    angle = 0
    for key, value in d.items():
        if value > max_count:
            angle = key
            max_count = value

    return angle

def get_ltrb_from_vertices(vertices):
    xs = []
    ys = []
    for vertice in vertices:
        xs.append(vertice.get('x', 0))
        ys.append(vertice.get('y', 0))
    return min(xs), min(ys), max(xs), max(ys)

def get_distance(target, last):
    tt = target.t
    tb = target.b
    tl = target.l
    ty = int((tb + tl) / 2)
    
    lr = last.r
    lt = last.t
    lb = last.b
    ly = int((lt + lb) / 2)
    
    if tt <= lb:
        if lt <= tb:
            dy = 0
        else:
            dy = tb - lt
    else:
        dy = tt - lb
            
    
    return tl - lr, dy, ty - ly

def get_avg_size(fulltextannotation):
    if not fulltextannotation:
        avg_height = 50
        avg_width = 50
        return avg_width, avg_height
    
    bounds = []   

    for page in fulltextannotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        bounds.append(symbol)

    hangul = re.compile('[^ㄱ-ㅣ가-힣]+')
    all_hanguls = [i for i in bounds if hangul.sub('', i.text)]

    avg_height = 0
    avg_width = 0
    
    if not all_hanguls:
        all_hanguls = bounds

    for box in all_hanguls:
        l, t, r, b = get_ltrb_from_vertices(box.boundingBox.vertices)
        avg_height += (b-t)
        avg_width += (r-l)
        
    avg_height /= len(all_hanguls)
    avg_width /= len(all_hanguls)
    
    return avg_width, avg_height


def get_line_info(textannotation, fulltextannotation):
    if not textannotation:
        return []
    
    if get_angle(textannotation) != 0:
        return []
    
    avg_width, avg_height = get_avg_size(fulltextannotation)
    
    words = textannotation[1:]
    for word in words:
        l, t, r, b = get_ltrb_from_vertices(word['boundingPoly']['vertices'])
        word.l = l
        word.t = t
        word.r = r
        word.b = b
    words.sort(key=lambda n: n.l)
    
    lines = []
    for word in words:
        flag = False
        line_cand = []
        for line in lines:
            last = line[-1]
            dx, dy, cy = get_distance(word, last)
            if abs(dy) <= avg_height//10 and dx < 2 * avg_width:
    #             print(dx, dy, cy)
    #             if dx < -5:
    #                 flag = True
    #                 continue
                line_cand.append(line)
                flag = True
        if flag:
            min_cy = 100000000000
            target_line = None
            for line in line_cand:
                last = line[-1]
                dx, dy, cy = get_distance(word, last)
                if abs(cy) < min_cy:
                    target_line = line
                    min_cy = abs(cy)
#                     print(line, word)
#             print(word)
            target_line.append(word)

        if not flag:
            lines.append([word])
    return lines

def get_wordbox_info(textannotation, fulltextannotation, threshold=0.2):
    if not textannotation:
        return []
    
    if get_angle(textannotation) != 0:
        return []
    
    avg_width, avg_height = get_avg_size(fulltextannotation)
    
    words = textannotation[1:]
    for word in words:
        l, t, r, b = get_ltrb_from_vertices(word['boundingPoly']['vertices'])
        word.l = l
        word.t = t
        word.r = r
        word.b = b
    words.sort(key=lambda n: n.l)
    
    lines = []
    for word in words:
        flag = False
        line_cand = []
        for line in lines:
            last = line[-1]
            dx, dy, cy = get_distance(word, last)
            if abs(dy) <= avg_height//10 and dx < threshold * avg_width:
    #             print(dx, dy, cy)
    #             if dx < -5:
    #                 flag = True
    #                 continue
                line_cand.append(line)
                flag = True
        if flag:
            min_cy = 100000000000
            target_line = None
            for line in line_cand:
                last = line[-1]
                dx, dy, cy = get_distance(word, last)
                if abs(cy) < min_cy:
                    target_line = line
                    min_cy = abs(cy)
#                     print(line, word)
#             print(word)
            target_line.append(word)

        if not flag:
            lines.append([word])
    return lines


def get_wordbox_info2(textannotation, fulltextannotation, threshold=0.2):
    if not textannotation:
        return []
    
    if get_angle(textannotation) != 0:
        return []
    
    avg_width, avg_height = get_avg_size(fulltextannotation)
    
    bounds = []
    for page in fulltextannotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        bounds.append(symbol)
    
    for word in bounds:
        l, t, r, b = get_ltrb_from_vertices(word['boundingBox']['vertices'])
        word.l = l
        word.t = t
        word.r = r
        word.b = b
    bounds.sort(key=lambda n: n.l)
    
    lines = []
    for word in bounds:
        flag = False
        line_cand = []
        for line in lines:
            last = line[-1]
            dx, dy, cy = get_distance(word, last)
            if abs(dy) <= avg_height//10 and dx < threshold * avg_width:
    #             print(dx, dy, cy)
    #             if dx < -5:
    #                 flag = True
    #                 continue
                line_cand.append(line)
                flag = True
        if flag:
            min_cy = 100000000000
            target_line = None
            for line in line_cand:
                last = line[-1]
                dx, dy, cy = get_distance(word, last)
                if abs(cy) < min_cy:
                    target_line = line
                    min_cy = abs(cy)
#                     print(line, word)
#             print(word)
            target_line.append(word)

        if not flag:
            lines.append([word])
    return lines


def get_image_from_url(_url):
    """
    numpy image 를 반환합니다.
    """
    fd = urllib.request.urlopen(_url)
    image_file = io.BytesIO(fd.read())
    im = np.array(Image.open(image_file))
    fd.close()
    image_file.close()
    image = np.array(im)
    return image

    
def render_cls_result(rgb, ret_lst,
                  text_color=(237, 28, 36),
                  line_color=(30, 200, 30),):
    """
    - rgb : numpy image
    - ret_lst : boxes
    - f_caption : function of caption; ex) lambda box: 'caption_of_box'
    - coordinates_mode : 'pixel' or 'ratio'
    """
    ret_lst = list(ret_lst)
    if not isinstance(line_color, tuple):
        line_color = _colors[line_color]
    if not isinstance(text_color, tuple):
        text_color = _colors[text_color]

    try:
        pil_font = ImageFont.truetype('NanumGothic.ttf', 20)
    except:
        pil_font = ImageFont.truetype('Arial.ttf', 20)

    try:
        pimg = Image.fromarray(cv2.cvtColor(rgb, cv2.COLOR_GRAY2RGB))
    except:
        pimg = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pimg)

    # convert 'left, top, ...' to 'l, t, ...'
    for box in ret_lst:
        if 'left' in box:
            box.l, box.t, box.r, box.b = box.left, box.top, box.right, box.bottom

    for box in ret_lst:
        l, t, r, b = int(box.l), int(box.t), int(box.r), int(box.b)
        draw.line([(l, t), (l, b), (r, b), (r, t), (l, t)], width=4, fill=line_color)
            
    return np.array(pimg)

def convert_to_box_format(result):
    '''
    result: list of list of TextAnnotation
    '''
    final_output = []
    for line in result:
        tmp = Munch()
        xs = []
        ys = []
        for word in line:
            xs.append(word.l)
            xs.append(word.r)
            ys.append(word.t)
            ys.append(word.b)
        tmp.left = min(xs)
        tmp.top = min(ys)
        tmp.right = max(xs)
        tmp.bottom = max(ys)
        tmp.description = ''.join(i['description'] for i in line)
        final_output.append(tmp)
    return final_output

# def convert_ft_to_box_format(result):
    # '''
    # result: list of list of FullTextAnnotation
    # '''
    # final_output = []
    # for line in result:
        # tmp = Munch()
        # xs = []
        # ys = []
        # for word in line:
            # xs.append(word.l)
            # xs.append(word.r)
            # ys.append(word.t)
            # ys.append(word.b)
        # tmp.left = min(xs)
        # tmp.top = min(ys)
        # tmp.right = max(xs)
        # tmp.bottom = max(ys)
        # tmp.description = ''.join(i['text'] for i in line)
        # final_output.append(tmp)
    # return final_output


def convert_ft_to_box_format(result):
    '''
    result: list of list of FullTextAnnotation
    '''
    final_output = []
    for line in result:
        tmp = Munch()
        xs = []
        ys = []
        for word in line:
            xs.append(word.l)
            xs.append(word.r)
            ys.append(word.t)
            ys.append(word.b)
        tmp.left = min(xs)
        tmp.top = min(ys)
        tmp.right = max(xs)
        tmp.bottom = max(ys)
        lst = []
        for i in line:
            try:
                i['property']['detectedBreak']
                text = i['text'] + ' '
            except:
                text = i['text']
            lst.append(text)
        final_text = ''.join(i for i in lst)
        try:
            if final_text[-1] == ' ':
                final_text = final_text[:-1]
        except:
            pass
        tmp.description = final_text
        
        final_output.append(tmp)
    return final_output


def ft_wordbox_to_charbox(result):
    '''
    result: list of list of FullTextAnnotation
    '''
    final_output = []
    for word in result:
        for char in word:
            tmp = Munch()
            xs = []
            ys = []
            xs.append(char.l)
            xs.append(char.r)
            ys.append(char.t)
            ys.append(char.b)
            tmp.left = min(xs)
            tmp.top = min(ys)
            tmp.right = max(xs)
            tmp.bottom = max(ys)
            tmp.description = char.text
        
            final_output.append(tmp)
    return final_output
