import random
import os
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
    # 枚数に応じて横に並べる枚数を4～8枚に調整
    MAX = 4 if np.ceil(num / 2) < 4 else 8 if np.ceil(num / 3) > 8 else int(np.ceil(num / 3))
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
    card_img = cv2.imread(id_to_pass(uno_func.card_to_id(card)), -1)
    card_img = cv2.resize(card_img, None, fx=0.5, fy=0.5)

    h, w, _ = card_img.shape
    # 回転角をランダムで指定し、中心を軸として回転
    angle = random.randint(-70, 70)
    angle_rad = angle / 180.0 * np.pi
    rotation_matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    # 回転後の画像サイズを計算
    w_rot = int(np.round(h * np.absolute(np.sin(angle_rad)) + w * np.absolute(np.cos(angle_rad))))
    h_rot = int(np.round(h * np.absolute(np.cos(angle_rad)) + w * np.absolute(np.sin(angle_rad))))
    size_rot = (w_rot, h_rot)
    # 平行移動を加える (rotation + translation)
    affine_matrix = rotation_matrix.copy()
    affine_matrix[0][2] = affine_matrix[0][2] - w // 2 + w_rot // 2
    affine_matrix[1][2] = affine_matrix[1][2] - h // 2 + h_rot // 2
    card_img = cv2.warpAffine(card_img, affine_matrix, size_rot, flags=cv2.INTER_CUBIC, borderValue=(255, 204, 51))
    # 透過する背景色の指定
    color = np.array([255, 51, 204, 255])
    card_img_mask = cv2.inRange(card_img, color, color)
    # 背景を透過して出力
    card_img = cv2.bitwise_not(card_img, card_img, mask=card_img_mask)
    cv2.imwrite('uno/card.png', card_img)

    # 貼り付ける位置をランダムで指定
    gap_h, gap_w = random.randint(-100, 50), random.randint(-300, 100)
    # カードを場に重ねる
    area_img = Image.open('uno/Area_tmp.png')
    card_img = Image.open('uno/card.png')
    area_img.paste(card_img, (190 + gap_w, 85 + gap_h), card_img)
    area_img.save('uno/Area_tmp.png')
    os.remove('uno/card.png')
