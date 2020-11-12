import openpyxl
import xlwings as xw
from uno import uno_func


EXCEL_PASS = 'uno/uno_record.xlsx'


def refresh_cash():
    excel_app = xw.App(visible=False)
    book = xw.Book(EXCEL_PASS)
    book.save(EXCEL_PASS)
    excel_app.kill()


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


def add_penalty(player, card):
    book = openpyxl.load_workbook(EXCEL_PASS)
    sheet = book['History']
    pts = calculate_point(card)

    for j in range(1, sheet.max_row + 2):
        # 既存ユーザーのデータ上書き
        if str(player) == sheet.cell(j, 1).value:
            # ポイント書き込み
            for k in range(3, sheet.max_column + 2):
                if sheet.cell(j, k).value is None:
                    sheet.cell(j, k, pts - 100)
                    break
            # ペナルティー書き込み(-100点)
            sheet.cell(j, 2, int(sheet.cell(j, 2).value) - 100)
            break
        # 新規ユーザーのデータ作成
        elif sheet.cell(j, 1).value is None:
            # ID書き込み
            sheet.cell(j, 1, str(player))
            # ポイント書き込み
            for k in range(3, sheet.max_column + 2):
                if sheet.cell(j, k).value is None:
                    sheet.cell(j, k, pts - 100)
                    break
            # ペナルティー書き込み(-100点)
            sheet.cell(j, 2, str(-100))
            break
    book.save(EXCEL_PASS)
    refresh_cash()


def data_save(data):
    book = openpyxl.load_workbook(EXCEL_PASS)
    sheet = book['History']

    for i in range(len(data)):
        for j in range(1, sheet.max_row + 2):
            # 既存ユーザーのデータ上書き
            if str(data[i][0]) == sheet.cell(j, 1).value:
                # ポイント書き込み
                for k in range(3, sheet.max_column + 2):
                    if sheet.cell(j, k).value is None:
                        sheet.cell(j, k, data[i][4])
                        break
                break
            # 新規ユーザーのデータ作成
            elif sheet.cell(j, 1).value is None:
                # ID書き込み
                sheet.cell(j, 1, str(data[i][0]))
                # ペナルティー書き込み(0点)
                sheet.cell(j, 2, str(0))
                # ポイント書き込み
                for k in range(3, sheet.max_column + 2):
                    if sheet.cell(j, k).value is None:
                        sheet.cell(j, k, data[i][4])
                        break
                break
    book.save(EXCEL_PASS)
    refresh_cash()


def data_delete(id):
    book = openpyxl.load_workbook(EXCEL_PASS)
    sheet = book['History']

    for row in sheet.iter_rows(min_row=2):
        if str(id) == row[0].value:
            sheet.delete_rows(row)
    book.save(EXCEL_PASS)
    refresh_cash()


def record_output(id):
    book = openpyxl.load_workbook(EXCEL_PASS, data_only=True)
    sheet = book['Records']
    data = []
    for row in sheet.iter_rows(min_row=2):
        if str(id) == row[1].value:
            for col in row:
                data.append(col.value)
            break

    if not data:
        return None, None

    if data[2] <= 0:
        url = 'https://i.imgur.com/adtGl7h.png'  # YOU LOSE
    else:
        url = 'https://i.imgur.com/1JXc9eD.png'  # YOU WIN
        data[2] = f"+{data[2]}"
    data[3] = round(data[3] * 100, 1)
    if data[6] is None:
        data[6] = "N/A"
    if data[7] is None:
        data[7] = "N/A"
    if data[9] >= 0:
        data[9] = f"+{data[9]}"

    return data, url
