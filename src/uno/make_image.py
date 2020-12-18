import random
import cv2
import os
import numpy as np
from PIL import Image
from src.uno import uno_func
from src.uno import uno_command

AREA_PASS = 'src/uno/base_image/Area.png'
AREA_TEMP_PASS = 'src/uno/base_image/Area_tmp.png'
BG_PASS = 'src/uno/base_image/Background.png'
HAND_PASS = 'src/uno/base_image/hand.png'
ALPHA_CARD_PASS = 'src/uno/base_image/card.png'


def id_to_pass(id):
    if uno_command.FREE_FLAG:
        card_type = "normal"
    else:
        card_type = "original"

    if 100 <= id < 200:
        return f"src/uno/card_image/{card_type}/Red_{id % 100}.png"
    elif 200 <= id < 300:
        return f"src/uno/card_image/{card_type}/Blue_{id % 200}.png"
    elif 300 <= id < 400:
        return f"src/uno/card_image/{card_type}/Green_{id % 300}.png"
    elif 400 <= id < 500:
        return f"src/uno/card_image/{card_type}/Yellow_{id % 400}.png"
    else:  # 531 <= id <= 534 → 30
        return f"src/uno/card_image/{card_type}/Black_{id // 10 % 10 * 10}.png"


def make_hand(card):
    card_img = []
    for i in card:
        img = cv2.imread(id_to_pass(uno_func.card_to_id(i)))
        img = cv2.resize(img, None, fx=0.6, fy=0.6)
        card_img.append(img)
    bg_img = cv2.imread(BG_PASS)

    bg_h, bg_w, _ = bg_img.shape
    h, w, _ = card_img[0].shape
    num, mag = len(card_img), 1.0
    # 枚数に応じて横に並べる枚数を4～12枚に調整
    MAX = 4 if np.ceil(num / 2) < 4 else 10 if np.ceil(num / 3) > 10 else int(np.ceil(num / 3))
    # 並べた時に見切れないように、枚数に応じてカードの画像サイズを縮小
    while True:
        # 画像同士の余白は最低 縦[40/枚数+1]px、横[70/枚数+1]px 空ける
        if bg_h - int(h * mag) * (num // MAX + 1) - 40 < 0 or bg_w - int(w * mag) * MAX - 70 < 0:
            mag -= 0.01
        else:
            for i in range(num):
                card_img[i] = cv2.resize(card_img[i], None, fx=mag, fy=mag)
            break

    h, w, _ = card_img[0].shape
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

    cv2.imwrite(HAND_PASS, bg_img)


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
    # 平行移動を加える
    affine_matrix = rotation_matrix.copy()
    affine_matrix[0][2] = affine_matrix[0][2] - w // 2 + w_rot // 2
    affine_matrix[1][2] = affine_matrix[1][2] - h // 2 + h_rot // 2
    card_img = cv2.warpAffine(card_img, affine_matrix, size_rot, flags=cv2.INTER_CUBIC, borderValue=(255, 204, 51))
    # 透過する背景色の指定
    color = np.array([255, 51, 204, 255])
    card_img_mask = cv2.inRange(card_img, color, color)
    # 背景を透過して一旦出力
    card_img = cv2.bitwise_not(card_img, card_img, mask=card_img_mask)
    cv2.imwrite(ALPHA_CARD_PASS, card_img)
    # 貼り付ける位置をランダムで指定
    gap_w, gap_h = random.randint(-300, 100), random.randint(-150, 50)
    # カードを場に重ねる
    area_img = Image.open(AREA_TEMP_PASS)
    card_img = Image.open(ALPHA_CARD_PASS)
    area_img.paste(card_img, (190 + gap_w, 85 + gap_h), card_img)
    area_img.save(AREA_TEMP_PASS)
    # 一旦出力した画像を削除
    os.remove(ALPHA_CARD_PASS)
