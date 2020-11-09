import random
import cv2
import numpy as np
from PIL import Image
from uno import uno_func


def id_to_pass(id):
    if 100 <= id < 200:
        return f"uno/card_image/Red_{id % 100}.png"
    elif 200 <= id < 300:
        return f"uno/card_image/Blue_{id % 200}.png"
    elif 300 <= id < 400:
        return f"uno/card_image/Green_{id % 300}.png"
    elif 400 <= id < 500:
        return f"uno/card_image/Yellow_{id % 400}.png"
    else:
        return f"uno/card_image/Black_{id % 500}.png"


def make_hand(card):
    card_img = []
    for i in card:
        img = cv2.imread(id_to_pass(uno_func.card_to_id(i)))
        img = cv2.resize(img, None, fx=0.6, fy=0.6)
        card_img.append(img)
    bg_img = cv2.imread('uno/Background.png')

    bg_h, bg_w, _ = bg_img.shape
    num = len(card_img)
    # 枚数に応じて横に並べる枚数を4～12枚に調整
    MAX = 4 if np.ceil(num / 2) < 4 else 10 if np.ceil(num / 3) > 10 else int(np.ceil(num / 3))
    # 並べた時に見切れないように、枚数に応じてカードの画像サイズを縮小
    while True:
        h, w, _ = card_img[0].shape
        # 画像同士の余白は最低 縦[70/枚数+1]px、横[100/枚数+1]px 空ける
        if bg_h - h * (num // MAX + 1) - 70 < 0 or bg_w - w * MAX - 100 < 0:
            for i in range(num):
                card_img[i] = cv2.resize(card_img[i], None, fx=0.9, fy=0.9)
        else:
            break

    space_h = (bg_h - h * (num // MAX + 1)) // (num // MAX + 2)
    space_w = (bg_w - w * MAX) // (MAX + 1)
    start_h, start_w = space_h, space_w
    # カード画像を背景画像に重ね合わせる
    i = 0
    while i < num:
        j = 0
        while j < MAX and i < num:
            bg_img[start_h: start_h + h, start_w: start_w + w] = card_img[i]
            start_w += space_w + w
            i, j = i + 1, j + 1
        start_h, start_w = start_h + space_h + h, space_w

    cv2.imwrite('uno/hand.png', bg_img)


def make_area(card):
    area_img = Image.open('uno/Area_tmp.png')
    card_img = Image.open(id_to_pass(uno_func.card_to_id(card))).resize(size=(384, 512))
    # カード画像の回転角をランダムで指定
    card_img = card_img.rotate(random.randint(-70, 70), fillcolor=(255, 204, 51), expand=True)
    # カード画像と同じサイズの透過画像を作成
    alpha_card_img = Image.new('RGBA', card_img.size, (0, 0, 0, 0))
    for x in range(card_img.size[0]):
        for y in range(card_img.size[1]):
            pixel = card_img.getpixel((x, y))
            # 指定画素以外なら、用意した画像にピクセルを書き込み
            if not (pixel[0] == 255 and pixel[1] == 204 and pixel[2] == 51):
                alpha_card_img.putpixel((x, y), pixel)
    # 貼り付ける位置をランダムで指定
    gap_w, gap_h = random.randint(-300, 100), random.randint(-150, 50)
    # カードを場に重ねる
    area_img.paste(alpha_card_img, (190 + gap_w, 85 + gap_h), alpha_card_img)
    area_img.save('uno/Area_tmp.png')
