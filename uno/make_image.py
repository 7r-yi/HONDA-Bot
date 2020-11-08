import cv2
import random
import numpy as np
from uno import uno


def id_to_pass(id):
    if 100 <= id < 200:
        return f"./card_img/Red_{id % 100}.png"
    elif 200 <= id < 300:
        return f"./card_img/Blue_{id % 200}.png"
    elif 300 <= id < 400:
        return f"./card_img/Green_{id % 300}.png"
    elif 400 <= id < 500:
        return f"./card_img/Yellow_{id % 400}.png"
    else:
        return f"./card_img/Black_{id % 500}.png"


def make_hand(card):
    card_img = []
    for i in card:
        img = cv2.imread(id_to_pass(uno.card_to_id(i)))
        img = cv2.resize(img, None, fx=0.6, fy=0.6)
        card_img.append(img)
    bg_img = cv2.imread('Background.png')

    bg_h, bg_w, _ = bg_img.shape
    # 並べた時に見切れないように、枚数に応じてカードの画像サイズを縮小
    while True:
        h, w, _ = card_img[0].shape
        # 画像同士の余白は最低 縦[70/枚数]px、横[100/枚数]px 空ける
        if bg_h - h * len(card_img) - 70 < 0 or bg_w - w * len(card_img) - 100 < 0:
            for i in range(len(card_img)):
                card_img[i] = cv2.resize(card_img[i], None, fx=0.9, fy=0.9)
        else:
            break

    space_h = (bg_h - h * len(card_img)) // (len(card_img) + 1)
    space_w = (bg_w - w * len(card_img)) // (len(card_img) + 1)
    start_h, start_w = space_h, space_w
    # カード画像を背景画像に重ね合わせる
    for i in range(len(card_img)):
        bg_img[start_h: start_h + h, start_w: start_w + w] = card_img[i]
        start_h += space_h + h
        start_w += space_w + w

    cv2.imwrite('hand.png', bg_img)


def make_area(card):
    card_img = cv2.imread(id_to_pass(uno.card_to_id(card)), -1)
    card_img = cv2.resize(card_img, None, fx=0.5, fy=0.5)
    area_img = cv2.imread('Area.png', -1)

    bg_h, bg_w, _ = area_img.shape
    h, w, _ = card_img.shape
    # 回転角をランダムで指定し、中心を軸として回転
    angle = random.randint(-45, 45)
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
    # 背景を透過
    card_img = cv2.bitwise_not(card_img, card_img, mask=card_img_mask)
    # 貼り付ける位置をランダムで指定
    gap_h, gap_w = random.randint(-100, 100), random.randint(-170, 170)
    area_img[90: 90 + gap_h + h, 200: 200 + gap_w + w] = card_img

    cv2.imwrite('Area.png', area_img)
