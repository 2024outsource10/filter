from collections import defaultdict
import re
import os

# 定义 NaiveFilter, BSFilter, DFAFilter

class NaiveFilter:
    """基于关键词的简单消息过滤器"""
    def __init__(self, keywords_path=None, repl="*"):
        self.keywords = set()
        self.repl = repl
        if keywords_path:
            self.parse(keywords_path)

    def parse(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            for keyword in file:
                self.keywords.add(keyword.strip().lower())

    def filter(self, message):
        message = message.lower()
        sensitive_words = []
        for kw in self.keywords:
            if kw in message:
                sensitive_words.append(kw)
                message = message.replace(kw, self.repl)
        return message, sensitive_words


class BSFilter:
    """基于倒排映射的敏感词过滤器"""
    def __init__(self, keywords_path=None, repl="*"):
        self.keywords = []
        self.kwsets = set()
        self.bsdict = defaultdict(set)
        self.pat_en = re.compile(r'^[0-9a-zA-Z]+$')
        self.repl = repl
        if keywords_path:
            self.parse(keywords_path)

    def add(self, keyword):
        keyword = keyword.lower()
        if keyword not in self.kwsets:
            self.keywords.append(keyword)
            self.kwsets.add(keyword)
            index = len(self.keywords) - 1
            for word in keyword.split():
                if self.pat_en.search(word):
                    self.bsdict[word].add(index)
                else:
                    for char in word:
                        self.bsdict[char].add(index)

    def parse(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def filter(self, message):
        message = message.lower()
        sensitive_words = []
        for word in message.split():
            if self.pat_en.search(word):
                for index in self.bsdict[word]:
                    if self.keywords[index] in message:
                        sensitive_words.append(self.keywords[index])
                        message = message.replace(self.keywords[index], self.repl)
            else:
                for char in word:
                    for index in self.bsdict[char]:
                        if self.keywords[index] in message:
                            sensitive_words.append(self.keywords[index])
                            message = message.replace(self.keywords[index], self.repl)
        return message, sensitive_words


class DFAFilter:
    """基于确定有限状态自动机的敏感词过滤器"""
    def __init__(self, keywords_path=None, repl="*"):
        self.keyword_chains = {}
        self.delimit = '\x00'
        self.repl = repl
        if keywords_path:
            self.parse(keywords_path)

    def add(self, keyword):
        keyword = keyword.lower().strip()
        if not keyword:
            return
        level = self.keyword_chains
        for i, char in enumerate(keyword):
            if char in level:
                level = level[char]
            else:
                for j in range(i, len(keyword)):
                    level[keyword[j]] = {}
                    last_level, last_char = level, keyword[j]
                    level = level[keyword[j]]
                last_level[last_char] = {self.delimit: 0}
                break
        if i == len(keyword) - 1:
            level[self.delimit] = 0

    def parse(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def filter(self, message):
        message = message.lower()
        ret = []
        sensitive_words = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        sensitive_words.append(message[start:start + step_ins])
                        ret.append(self.repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1

        return ''.join(ret), sensitive_words


# 创建过滤器的函数
def create_filter(filter_type="DFA", keywords_path=None, repl="*"):
    if filter_type == "Naive":
        return NaiveFilter(keywords_path, repl)
    elif filter_type == "BS":
        return BSFilter(keywords_path, repl)
    elif filter_type == "DFA":
        return DFAFilter(keywords_path, repl)
    else:
        raise ValueError("Unknown filter type: choose from 'Naive', 'BS', or 'DFA'.")


# 用于过滤文本的外部接口
def filter_text(text, filter_type="DFA", keywords_path=None, repl="*"):
    if keywords_path is None:
        keywords_path = os.path.join(os.getcwd(), "keywords.txt")

    if not os.path.exists(keywords_path):
        raise FileNotFoundError(f"敏感词库文件未找到: {keywords_path}")

    gfw = create_filter(filter_type, keywords_path, repl)

    return gfw.filter(text)


# 主逻辑部分
def collect_sensitive_words_and_filter(text, filter_type="DFA", repl="*"):
    try:
        filtered_text, sensitive_words = filter_text(text, filter_type=filter_type, repl=repl)
        return sensitive_words, filtered_text
    except FileNotFoundError as e:
        print(f"敏感词过滤失败: {e}")
        return [], text


def process_document(input_text):
    processed_text = ""
    pages = input_text.split('\n\n')  # 模拟简单的页拆分逻辑
    all_sensitive_words = []

    for page in pages:
        sensitive_words, filtered_page = collect_sensitive_words_and_filter(page)
        all_sensitive_words.extend(sensitive_words)
        processed_text += filtered_page + '\n'

    return all_sensitive_words, processed_text


# main 函数用于测试
def main():
    input_text = """
    Page1: This is a test document. It contains some sensitive words.
    Page2: Another page with content that may trigger the filter.
    SensitiveWord is on this page too.
    """

    triggered_words, cleaned_text = process_document(input_text)

    print("触发的敏感词:")
    print(triggered_words)
    print("\n清理后的文档:")
    print(cleaned_text)


if __name__ == '__main__':
    main()