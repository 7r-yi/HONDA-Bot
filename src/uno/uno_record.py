import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from src.uno import uno_func


def road_spreadsheet(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credential = {
        "type": 'service_account',
        "project_id": os.environ['PROJECT_ID'],
        "private_key_id": os.environ['PRIVATE_KEY_ID'],
        "private_key": os.environ['PRIVATE_KEY'].replace("\\n", "\n"),
        "client_email": os.environ['CLIENT_EMAIL'],
        "client_id": os.environ['CLIENT_ID'],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ['CLIENT_X509_CERT_URL']
    }
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credential, scope)
    gc = gspread.authorize(credentials)

    return gc.open_by_key('1ba_1lWkwCa20ulVYyJbcVW41bCZ1jXagLgubtLKomB0').worksheet(sheet_name)


def num_to_alpha(num):
    if num <= 26:
        return chr(64 + num)
    elif num % 26 == 0:
        return num_to_alpha(num // 26 - 1) + chr(90)
    else:
        return num_to_alpha(num // 26) + chr(64 + num % 26)


def calculate_point(card):
    pts = 0
    for i in card:
        id = uno_func.card_to_id(i)
        if id % 100 <= 9 and id < 500:  # 数字カードはその数字の点数
            pts -= id % 100
        elif id < 500:  # 記号カードは20点
            pts -= 20
        else:  # ワイルドカードは50点
            pts -= 50

    return pts


def add_penalty(id, name, card):
    sheet = road_spreadsheet('試合結果データ')
    data = sheet.get_all_values()
    pts = calculate_point(card)

    for i in range(len(data)):
        # 既存ユーザーのデータ上書き
        if str(id) == data[i][2]:
            data_row = sheet.range(f'B{i + 1}:{num_to_alpha(len(data[i]) + 1)}{i + 1}')
            # 名前書き込み
            data_row[0].value = name
            # ペナルティー書き込み(-100点)
            data_row[2].value = int(data_row[2].value) - 100
            # ポイント書き込み
            # ポイント書き込み
            for j in range(3, len(data[i]) + 1):
                if not data_row[j].value:
                    data_row[j].value = pts
                    break
            sheet.update_cells(data_row, value_input_option='USER_ENTERED')
            break
        # 新規ユーザーのデータ作成
        elif data[i][2] == "":
            data_row = sheet.range(f'B{i + 1}:E{i + 1}')
            # 名前書き込み
            data_row[0].value = name
            # ID書き込み
            data_row[1].value = str(id)
            # ペナルティー書き込み(-100点)
            data_row[2].value = -100
            # ポイント書き込み
            for j in range(3, len(data[i]) + 1):
                if not data_row[j].value:
                    data_row[j].value = pts
                    break
            sheet.update_cells(data_row, value_input_option='USER_ENTERED')
            break


def data_save(all_data, all_name):
    sheet = road_spreadsheet('試合結果データ')
    data = sheet.get_all_values()
    times = len(data)
    for i in range(len(all_data)):
        j = 0
        while j < times:
            # 既存ユーザーのデータ上書き
            if str(all_data[i][0]) == data[j][2]:
                data_row = sheet.range(f'B{j + 1}:{num_to_alpha(len(data[j]) + 1)}{j + 1}')
                # 名前書き込み
                data_row[0].value = all_name[i]
                # ポイント書き込み
                for k in range(3, len(data[j]) + 1):
                    if not data_row[k].value:
                        data_row[k].value = all_data[i][4]
                        break
                sheet.update_cells(data_row, value_input_option='USER_ENTERED')
                break
            # 新規ユーザーのデータ作成
            elif data[j][2] == "":
                data_row = sheet.range(f'B{j + 1}:E{j + 1}')
                # 名前書き込み
                data_row[0].value = all_name[i]
                # ID書き込み
                data_row[1].value = str(all_data[i][0])
                # ペナルティー書き込み(0点)
                data_row[2].value = 0
                # ポイント書き込み
                data_row[3].value = all_data[i][4]
                sheet.update_cells(data_row, value_input_option='USER_ENTERED')
                times += 1
                break
            j += 1


def data_delete(id):
    sheet = road_spreadsheet('試合結果データ')
    data = sheet.get_all_values()

    for i in range(len(data)):
        if str(id) == data[i][2]:
            data_row = sheet.range(f'B{i + 1}:{num_to_alpha(len(data[i]) + 1)}{i + 1}')
            for j in range(data_row):
                # 1列目以外全て空白に書き換える
                data_row[j].value = ""
            sheet.update_cells(data, value_input_option='USER_ENTERED')
            break


def record_output(id):
    sheet = road_spreadsheet('記録一覧')
    data = sheet.get_all_values()

    for i in range(len(data)):
        if str(id) == data[i][2]:
            if int(data[i][3].replace("+", "")) <= 0:
                url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
            else:
                url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN

            return data[i], url

    return None, None
