from collections import defaultdict
import re
import os


class NaiveFilter:
    """
    基于关键词的简单消息过滤器

    非常简单的过滤器实现，直接替换关键词。
    """

    def __init__(self, keywords_path=None, repl="*"):
        """初始化过滤器，支持从指定路径加载敏感词库"""
        self.keywords = set()
        self.repl = repl
        if keywords_path:
            self.parse(keywords_path)

    def parse(self, path):
        """从文件中读取关键词，并加入到过滤器中"""
        with open(path, 'r', encoding='utf-8') as file:
            for keyword in file:
                self.keywords.add(keyword.strip().lower())

    def filter(self, message):
        """过滤消息中的敏感词，将其替换为指定字符"""
        message = message.lower()
        for kw in self.keywords:
            message = message.replace(kw, self.repl)
        return message


class BSFilter:
    """
    基于倒排映射的敏感词过滤器

    通过倒排映射减少不必要的替换操作，提升过滤效率。
    """

    def __init__(self, keywords_path=None, repl="*"):
        """初始化过滤器，支持从指定路径加载敏感词库"""
        self.keywords = []
        self.kwsets = set()
        self.bsdict = defaultdict(set)
        self.pat_en = re.compile(r'^[0-9a-zA-Z]+$')  # 判断是否为英文短语
        self.repl = repl
        if keywords_path:
            self.parse(keywords_path)

    def add(self, keyword):
        """添加单个关键词到过滤器"""
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
        """从文件中读取关键词，并加入到过滤器中"""
        with open(path, 'r', encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def filter(self, message):
        """过滤消息中的敏感词，将其替换为指定字符"""
        message = message.lower()
        for word in message.split():
            if self.pat_en.search(word):  # 如果是英文短语
                for index in self.bsdict[word]:
                    message = message.replace(self.keywords[index], self.repl)
            else:  # 非英文单词按字符处理
                for char in word:
                    for index in self.bsdict[char]:
                        message = message.replace(self.keywords[index], self.repl)
        return message


class DFAFilter:
    """
    基于确定有限状态自动机（DFA）的敏感词过滤器

    使用 DFA 保证性能稳定，适合处理大规模文本过滤。
    """

    def __init__(self, keywords_path=None, repl="*"):
        """初始化过滤器，支持从指定路径加载敏感词库"""
        self.keyword_chains = {}
        self.delimit = '\x00'
        self.repl = repl
        if keywords_path:
            self.parse(keywords_path)

    def add(self, keyword):
        """添加单个关键词到 DFA 状态机中"""
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
        """从文件中读取关键词，并加入到 DFA 中"""
        with open(path, 'r', encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())

    def filter(self, message):
        """使用 DFA 过滤消息中的敏感词"""
        message = message.lower()
        ret = []
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
                        ret.append(self.repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1

        return ''.join(ret)

    def is_contain_sensi_key_word(self, message):
        """检查消息中是否包含敏感词"""
        repl = '_-__-'
        filtered_message = self.filter(message)
        return repl in filtered_message


# 整合并创建过滤器函数
def filter_text(text, filter_type="DFA", keywords_path=None, repl="*"):
    """
    对外接口函数，用于过滤文本中的敏感词
    :param text: 待过滤的文本字符串
    :param filter_type: 过滤器类型（Naive, BS, DFA）
    :param keywords_path: 敏感词库文件的路径（可选，如果未提供则使用默认路径）
    :param repl: 敏感词的替换字符
    :return: 过滤后的文本
    """
    # 如果未指定关键词库路径，使用默认的 "keywords.txt" 路径
    if keywords_path is None:
        keywords_path = os.path.join(os.getcwd(), "keywords.txt")

    # 确保关键词文件存在，否则抛出异常
    if not os.path.exists(keywords_path):
        raise FileNotFoundError(f"敏感词库文件未找到: {keywords_path}")

    # 创建指定类型的过滤器
    gfw = create_filter(filter_type, keywords_path, repl)

    # 对输入的文本进行过滤
    return gfw.filter(text)


# 示例的过滤器创建函数，假设已定义在上文
def create_filter(filter_type="DFA", keywords_path=None, repl="*"):
    """根据类型创建过滤器，并加载敏感词库"""
    if filter_type == "Naive":
        return NaiveFilter(keywords_path, repl)
    elif filter_type == "BS":
        return BSFilter(keywords_path, repl)
    elif filter_type == "DFA":
        return DFAFilter(keywords_path, repl)
    else:
        raise ValueError("Unknown filter type: choose from 'Naive', 'BS', or 'DFA'.")


# 假设 NaiveFilter、BSFilter、DFAFilter 类也已定义在上文
# 简单测试
if __name__ == "__main__":
    test_text = "一些示例文本"

    # 测试调用，使用默认路径
    try:
        filtered_text = filter_text(test_text, filter_type="DFA", repl="*")
        print("过滤后的文本：", filtered_text)
    except FileNotFoundError as e:
        print(e)
