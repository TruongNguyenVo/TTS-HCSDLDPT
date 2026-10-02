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


VNI_MAP = {
    'a': ('a', '0'), 'á': ('a', '1'), 'à': ('a', '2'), 'ả': ('a', '3'), 'ã': ('a', '4'), 'ạ': ('a', '5'),
    'â': ('a+', '0'), 'ấ': ('a+', '1'), 'ầ': ('a+', '2'), 'ẩ': ('a+', '3'), 'ẫ': ('a+', '4'), 'ậ': ('a+', '5'),
    'ă': ('aa', '0'), 'ắ': ('aa', '1'), 'ằ': ('aa', '2'), 'ẳ': ('aa', '3'), 'ẵ': ('aa', '4'), 'ặ': ('aa', '5'),
    'e': ('e', '0'), 'é': ('e', '1'), 'è': ('e', '2'), 'ẻ': ('e', '3'), 'ẽ': ('e', '4'), 'ẹ': ('e', '5'),
    'ê': ('e+', '0'), 'ế': ('e+', '1'), 'ề': ('e+', '2'), 'ể': ('e+', '3'), 'ễ': ('e+', '4'), 'ệ': ('e+', '5'),
    'i': ('i', '0'), 'í': ('i', '1'), 'ì': ('i', '2'), 'ỉ': ('i', '3'), 'ĩ': ('i', '4'), 'ị': ('i', '5'),
    'o': ('o', '0'), 'ó': ('o', '1'), 'ò': ('o', '2'), 'ỏ': ('o', '3'), 'õ': ('o', '4'), 'ọ': ('o', '5'),
    'ô': ('o+', '0'), 'ố': ('o+', '1'), 'ồ': ('o+', '2'), 'ổ': ('o+', '3'), 'ỗ': ('o+', '4'), 'ộ': ('o+', '5'),
    'ơ': ('oo', '0'), 'ớ': ('oo', '1'), 'ờ': ('oo', '2'), 'ở': ('oo', '3'), 'ỡ': ('oo', '4'), 'ợ': ('oo', '5'),
    'u': ('u', '0'), 'ú': ('u', '1'), 'ù': ('u', '2'), 'ủ': ('u', '3'), 'ũ': ('u', '4'), 'ụ': ('u', '5'),
    'ư': ('uu', '0'), 'ứ': ('uu', '1'), 'ừ': ('uu', '2'), 'ử': ('uu', '3'), 'ữ': ('uu', '4'), 'ự': ('uu', '5'),
    'y': ('y', '0'), 'ý': ('y', '1'), 'ỳ': ('y', '2'), 'ỷ': ('y', '3'), 'ỹ': ('y', '4'), 'ỵ': ('y', '5'),
    'đ': ('d-', '0')
}

def word_to_vni(word: str) -> str:
    """
    Chuyển đổi 1 từ đơn tiếng Việt sang mã VNI.

    Args:
        word (str): Một từ tiếng Việt (VD: "bác", "đê")

    Returns:
        str: Mã VNI tương ứng (VD: "bac1", "d-e+0")
    """
    word = unicodedata.normalize('NFC', word.lower())
    tone = '0'
    vni_word = ""
    for char in word:
        if char in VNI_MAP:
            base, char_tone = VNI_MAP[char]
            vni_word += base
            if char_tone != '0':
                tone = char_tone
        else:
            vni_word += char
            
    return vni_word + tone


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
