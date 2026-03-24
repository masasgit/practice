import re
import csv
import os
import fitz  # PyMuPDF
from tkinter import Tk
from tkinter.filedialog import askopenfilename

CM_TO_PT = 72 / 2.54

def cm_to_pt(v_cm: float) -> float:
    return v_cm * CM_TO_PT

def rect_cm_to_fitz(page: fitz.Page, x0_cm, y0_cm, x1_cm, y1_cm, origin="top-left") -> fitz.Rect:
    x0_pt = cm_to_pt(x0_cm)
    x1_pt = cm_to_pt(x1_cm)
    y0_pt = cm_to_pt(y0_cm)
    y1_pt = cm_to_pt(y1_cm)

    if origin == "top-left":
        return fitz.Rect(min(x0_pt, x1_pt), min(y0_pt, y1_pt), max(x0_pt, x1_pt), max(y0_pt, y1_pt))

    if origin == "bottom-left":
        H = page.rect.height
        y0 = H - y0_pt
        y1 = H - y1_pt
        return fitz.Rect(min(x0_pt, x1_pt), min(y0, y1), max(x0_pt, x1_pt), max(y0, y1))

    raise ValueError("origin must be 'top-left' or 'bottom-left'")

def extract_number(text: str):
    """テキストから最初の数値を抽出（カンマ/小数/符号対応）"""
    if not text:
        return None
    cleaned = " ".join(text.split())
    m = re.search(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|[-+]?\d+(?:\.\d+)?", cleaned)
    if not m:
        return None
    s = m.group(0).replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

def remove_notice(text: str) -> str:
    """
    品番枠に混入する注意文「日別明細数量は参考予定」を除去する。
    * や ＊ の有無に関係なく削除する。
    """
    if not text:
        return text

    targets = [
        "*日別明細数量は参考予定*",
        "＊日別明細数量は参考予定＊",
        "日別明細数量は参考予定",
    ]

    for t in targets:
        text = text.replace(t, "")

    # 余分な空白・改行を整理
    return " ".join(text.split()).strip()

def extract_text_by_fields(page: fitz.Page, fields: list[dict], origin="top-left") -> dict:
    """1ページ分：fieldsのidごとに抽出テキストを辞書で返す"""
    out = {}
    for f in fields:
        rect = rect_cm_to_fitz(page, f["x0"], f["y0"], f["x1"], f["y1"], origin=origin)
        text = page.get_text("text", clip=rect).strip()
        out[f["id"]] = text
    return out

def build_rows_for_page(page_no: int, fields: list[dict], extracted_text: dict, file_name: str):
    """
    1ページ分の抽出結果から、縦持ち12行（品番4×月3）を生成
    """
    meta = {f["id"]: f for f in fields}

    groups = [
        {"item_id": "A01", "month_ids": ["A02", "A03", "A04"]},
        {"item_id": "A05", "month_ids": ["A06", "A07", "A08"]},
        {"item_id": "A09", "month_ids": ["A10", "A11", "A12"]},
        {"item_id": "A13", "month_ids": ["A14", "A15", "A16"]},
    ]

    rows = []
    for g in groups:
        item_id = g["item_id"]
        item_label = meta[item_id].get("品番", "")
        item_text  = extracted_text.get(item_id, "")
        # A01/A05/A09/A13 の品番枠だけ、注意文を削除
        if item_id in {"A01", "A05", "A09", "A13"}:
            item_text = remove_notice(item_text)

        for mid in g["month_ids"]:
            month_label = meta[mid].get("月", "")
            month_text  = extracted_text.get(mid, "")
            value = extract_number(month_text)

            rows.append({
                "file_name": file_name,
                "page": page_no,
                "id": item_id,
                "品番": item_label,
                "月": month_label,
                "値": value,
                "品番_抽出": item_text,
                "月_抽出": month_text,
            })
    return rows

def extract_table(pdf_path: str, fields: list[dict], origin="top-left"):
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)
    all_rows = []
    for i, page in enumerate(doc):
        extracted = extract_text_by_fields(page, fields, origin=origin)
        all_rows.extend(build_rows_for_page(i + 1, fields, extracted, file_name))
    doc.close()
    return all_rows

def save_csv(rows, out_path="extracted_table.csv"):
    fieldnames = ["file_name", "page", "id", "品番", "月", "値", "品番_抽出", "月_抽出"]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def pick_pdf_path() -> str:
    """PDFをダイアログで選択してパスを返す（キャンセルなら空文字）"""
    root = Tk()
    root.withdraw()          # 余計なウィンドウを出さない
    root.attributes("-topmost", True)  # 前面に出す（環境によって効かない場合あり）
    path = askopenfilename(
        title="PDFを選択",
        filetypes=[("PDF files", "*.pdf")],
    )
    root.destroy()
    return path

if __name__ == "__main__":
    # ここでPDFを選択
    PDF_PATH = pick_pdf_path()
    if not PDF_PATH:
        raise SystemExit("PDFが選択されませんでした（キャンセル）")

    FIELDS = [
        {"id": "A01", "品番":"品番(1)", "x0": 6.36, "y0": 6.36, "x1": 9.55, "y1": 6.76},
        {"id": "A02", "月":"当月", "x0": 7.67, "y0": 3.21, "x1": 8.84, "y1": 3.44},
        {"id": "A03", "月":"翌月", "x0": 7.67, "y0": 4.59, "x1": 8.84, "y1": 4.82},
        {"id": "A04", "月":"翌々月", "x0": 7.67, "y0": 4.90, "x1": 8.84, "y1": 5.13},

        {"id": "A05", "品番":"品番(2)", "x0": 6.36, "y0": 10.43, "x1": 9.55, "y1": 10.83},
        {"id": "A06", "月":"当月", "x0": 7.67, "y0": 7.33, "x1": 8.84, "y1": 7.56},
        {"id": "A07", "月":"翌月", "x0": 7.67, "y0": 8.69, "x1": 8.84, "y1": 8.92},
        {"id": "A08", "月":"翌々月", "x0": 7.67, "y0": 9.02, "x1": 8.84, "y1": 9.25},

        {"id": "A09", "品番":"品番(3)", "x0": 6.36, "y0": 14.63, "x1": 9.55, "y1": 15.03},
        {"id": "A10", "月":"当月", "x0": 7.67, "y0": 11.45, "x1": 8.84, "y1": 11.68},
        {"id": "A11", "月":"翌月", "x0": 7.67, "y0": 12.78, "x1": 8.84, "y1": 13.01},
        {"id": "A12", "月":"翌々月", "x0": 7.67, "y0": 13.09, "x1": 8.84, "y1": 13.32},

        {"id": "A13", "品番":"品番(4)", "x0": 6.36, "y0": 18.65, "x1": 9.55, "y1": 19.05},
        {"id": "A14", "月":"当月", "x0": 7.67, "y0": 15.57, "x1": 8.84, "y1": 15.80},
        {"id": "A15", "月":"翌月", "x0": 7.67, "y0": 16.90, "x1": 8.84, "y1": 17.13},
        {"id": "A16", "月":"翌々月", "x0": 7.67, "y0": 17.16, "x1": 8.84, "y1": 17.39},
    ]

    # 出力CSV名：選んだPDFと同じ場所に “_extracted_table.csv” を作る
    base, _ = os.path.splitext(PDF_PATH)
    out_csv = base + "_extracted_table.csv"

    rows = extract_table(PDF_PATH, FIELDS, origin="top-left")
    save_csv(rows, out_csv)
    print(f"saved: {out_csv}")