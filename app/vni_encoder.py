"""
vni_encoder.py - Module chuẩn hóa & chuyển đổi văn bản sang mã VNI

Quy tắc dấu thanh:
    1 = sắc, 2 = huyền, 3 = hỏi, 4 = ngã, 5 = nặng, 0 = không dấu

Quy tắc nguyên âm/phụ âm đặc biệt:
    â -> a+  |  ô -> o+  |  ê -> e+
    ă -> aa  |  ơ -> oo  |  ư -> uu  |  đ -> d-
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Làm sạch văn bản: bỏ dấu câu, chuyển về chữ thường, chuẩn hóa khoảng trắng.

    Args:
        text (str): Chuỗi văn bản đầu vào (VD: "Bác Ba, cảng!")

    Returns:
        str: Chuỗi đã làm sạch (VD: "bác ba cảng")
    """
    # TODO: Implement logic làm sạch văn bản
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text)
    return text


def word_to_vni(word: str) -> str:
    """
    Chuyển đổi 1 từ đơn tiếng Việt sang mã VNI.

    Args:
        word (str): Một từ tiếng Việt (VD: "bác", "đê")

    Returns:
        str: Mã VNI tương ứng (VD: "bac1", "d-e+")
    """
    # TODO: Implement logic chuyển đổi VNI
    # Placeholder - trả về từ gốc (chưa xử lý)
    return word


def encode_sentence(sentence: str) -> list[str]:
    """
    Tách câu thành các từ đơn và trả về danh sách mã VNI.

    Args:
        sentence (str): Câu tiếng Việt đầu vào (VD: "bác ba cảng")

    Returns:
        list[str]: Danh sách mã VNI (VD: ["bac1", "ba0", "cang3"])
    """
    # TODO: Implement logic tách câu & mã hóa
    normalized = normalize_text(sentence)
    words = normalized.split()
    return [word_to_vni(w) for w in words]
