import re
import sqlite3
from time import time
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
h.setFormatter(fmt)
logger.addHandler(h)
def vhf_like_param(s):
    """
    LIKE検索用に %...% を付けたパターン文字列を作る。
    SQL自体はプレースホルダ化するので、ここでは単純に両端%付与のみ。
    """
    if s is None:
        return "%"
    return f"%{s}%"
