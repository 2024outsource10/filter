import re
from page_apart import page_apart

from filter import filter_text

# 页面换行
def page_newline(page):
    """
    在 'pageX:'（X为数字）模式的冒号后添加换行符。

    参数:
        page (str): 输入的单页内容。

    返回:
        str: 在指定模式后添加换行符的文本。
    """
    # 使用正则表达式在 'pageX:' 模式的冒号后添加换行符
    modified_page = re.sub(r'(Page\d+:)', r'\1\n', page)
    return modified_page


def collect_sensitive_words_and_filter(text, filter_type="DFA", repl="*"):
    """
    收集触发的敏感词，并替换敏感词。

    参数:
        text (str): 输入的文本。
        filter_type (str): 过滤器的类型，默认使用 DFA。
        repl (str): 替换敏感词的符号，默认为 '*'

    返回:
        tuple: 包含触发的敏感词列表和替换后的文本。
    """
    try:
        # 调用过滤函数，并返回替换后的文本
        filtered_text, sensitive_words = filter_text(text, filter_type=filter_type, repl=repl, return_sensitive_words=True)
        return sensitive_words, filtered_text
    except FileNotFoundError as e:
        print(f"敏感词过滤失败: {e}")
        return [], text


def process_document(input_text):
    """
    处理文档，包括敏感词过滤和文本清理，返回触发的敏感词和清理后的文档。

    参数:
        input_text (str): 输入的文档文本。

    返回:
        tuple: 包含触发的敏感词列表和清理后的文本。
    """
    processed_text = ""
    pages = page_apart(input_text)
    all_sensitive_words = []

    for idx, page in enumerate(pages):
        # 处理文本空白字符、表格等格式


        # 过滤敏感词，并记录触发的敏感词
        sensitive_words, filtered_page = collect_sensitive_words_and_filter(page)
        all_sensitive_words.extend(sensitive_words)

        # 将过滤后的页面内容加入结果
        processed_text += filtered_page + '\n'



    return all_sensitive_words, processed_text

