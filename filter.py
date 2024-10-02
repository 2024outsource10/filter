from collections import defaultdict
import re
import os

# 全局变量，指定敏感词库文件的路径
keyword_path:str = os.getenv("KEYWORD_PATH", "./keyword.txt")

# 定义 NaiveFilter, BSFilter, DFAFilter

class NaiveFilter:
    """基于关键词的简单消息过滤器"""

    def __init__(self, repl="*"):
        """
        初始化过滤器:
        - repl: 用于替换敏感词的符号，默认为 '*'
        """
        self.keywords = set()  # 存储敏感词的集合
        self.repl = repl  # 替换符号
        self.parse(keyword_path)  # 使用全局的 keyword_path 进行解析

    def parse(self, path):
        """从指定路径加载敏感词库并存储到 set 中"""
        with open(path, 'r', encoding='utf-8') as file:
            for keyword in file:
                self.keywords.add(keyword.strip().lower())  # 逐行读取关键词并添加到 set 中，使用 lower() 转换为小写

    def filter(self, message):
        """过滤消息中的敏感词，替换为指定字符"""
        message = message.lower()  # 将消息转换为小写，保证不区分大小写
        sensitive_words = []  # 存储被替换的敏感词
        for kw in self.keywords:
            if kw in message:
                sensitive_words.append(kw)  # 收集命中的敏感词
                message = message.replace(kw, self.repl)  # 替换敏感词为指定的符号
        return message, sensitive_words  # 返回过滤后的消息和触发的敏感词列表


class BSFilter:
    """基于倒排映射的敏感词过滤器"""

    def __init__(self, repl="*"):
        """
        初始化过滤器:
        - repl: 替换敏感词的符号，默认为 '*'
        """
        self.keywords = []  # 存储所有敏感词的列表
        self.kwsets = set()  # 存储敏感词的集合，便于快速查找
        self.bsdict = defaultdict(set)  # 倒排索引，映射敏感词中的字符或单词到其在 self.keywords 中的索引
        self.pat_en = re.compile(r'^[0-9a-zA-Z]+$')  # 判断是否为英文短语的正则表达式
        self.repl = repl
        self.parse(keyword_path)  # 使用全局的 keyword_path 进行解析

    def add(self, keyword):
        """将关键词添加到过滤器"""
        keyword = keyword.lower()  # 将关键词转为小写
        if keyword not in self.kwsets:
            self.keywords.append(keyword)  # 添加到关键词列表
            self.kwsets.add(keyword)  # 同时添加到集合中
            index = len(self.keywords) - 1  # 获取关键词的索引
            for word in keyword.split():  # 拆分关键词（处理多单词情况）
                if self.pat_en.search(word):  # 如果是英文短语
                    self.bsdict[word].add(index)  # 倒排映射：将关键词索引映射到单词
                else:
                    for char in word:  # 如果是非英文，则逐字映射
                        self.bsdict[char].add(index)

    def parse(self, path):
        """从文件中读取敏感词并添加到过滤器"""
        with open(path, 'r', encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())  # 逐行添加敏感词

    def filter(self, message):
        """过滤消息中的敏感词并替换为指定字符"""
        message = message.lower()  # 将消息转换为小写，保证不区分大小写
        sensitive_words = []  # 存储命中的敏感词
        for word in message.split():  # 按单词拆分消息
            if self.pat_en.search(word):  # 如果是英文短语
                for index in self.bsdict[word]:
                    if self.keywords[index] in message:
                        sensitive_words.append(self.keywords[index])  # 记录命中的敏感词
                        message = message.replace(self.keywords[index], self.repl)  # 替换敏感词
            else:
                for char in word:  # 非英文的逐字处理
                    for index in self.bsdict[char]:
                        if self.keywords[index] in message:
                            sensitive_words.append(self.keywords[index])
                            message = message.replace(self.keywords[index], self.repl)
        return message, sensitive_words


class DFAFilter:
    """基于确定有限状态自动机 (DFA) 的敏感词过滤器"""

    def __init__(self, repl="*"):
        """
        初始化过滤器:
        - repl: 替换敏感词的符号，默认为 '*'
        """
        self.keyword_chains = {}  # DFA 状态机的字典表示
        self.delimit = '\x00'  # 分隔符，用于表示词结尾
        self.repl = repl
        self.parse(keyword_path)  # 使用全局的 keyword_path 进行解析

    def add(self, keyword):
        """将关键词添加到 DFA 结构中"""
        keyword = keyword.lower().strip()  # 关键词小写化并去除空白
        if not keyword:
            return
        level = self.keyword_chains  # 指向状态机的当前层级
        for i, char in enumerate(keyword):
            if char not in level:
                level[char] = {}  # 如果字符不存在，则创建新节点
            level = level[char]  # 进入下一个层级
        level[self.delimit] = 0  # 词的结尾标志

    def parse(self, path):
        """从文件中读取关键词并构造 DFA"""
        with open(path, 'r', encoding='utf-8') as f:
            for keyword in f:
                self.add(keyword.strip())  # 逐行添加敏感词

    def filter(self, message):
        """使用 DFA 过滤消息中的敏感词"""
        message = message.lower()  # 消息转为小写
        ret = []  # 存储过滤后的字符
        sensitive_words = []  # 存储命中的敏感词
        start = 0  # 当前检查字符的起始位置
        while start < len(message):
            level = self.keyword_chains  # 从状态机的初始状态开始
            step_ins = 0  # 记录当前匹配的长度
            for i, char in enumerate(message[start:], start=start):
                if char in level:
                    step_ins += 1
                    level = level[char]  # 继续匹配下一个字符
                    if self.delimit in level:  # 匹配到词的结尾
                        sensitive_words.append(message[start:start + step_ins])  # 记录匹配到的敏感词
                        ret.append(self.repl * step_ins)  # 用替换符号替换敏感词
                        start = i + 1  # 更新起始位置
                        break
                else:
                    ret.append(message[start])  # 非敏感字符，直接保留
                    start += 1
                    break
            else:
                # 没有匹配到敏感词时，添加当前字符
                ret.append(message[start])
                start += 1

        return ''.join(ret), sensitive_words  # 返回过滤后的消息和敏感词列表


# 创建过滤器的函数
def create_filter(filter_type="DFA", repl="*"):
    """根据过滤器类型创建并返回相应的过滤器实例"""
    if filter_type == "Naive":
        return NaiveFilter(repl)
    elif filter_type == "BS":
        return BSFilter(repl)
    elif filter_type == "DFA":
        return DFAFilter(repl)
    else:
        raise ValueError("未知类型: choose from 'Naive', 'BS', or 'DFA'.")


# 用于过滤文本的外部接口
def filter_text(text, filter_type="DFA", repl="*"):
    """调用适当的过滤器来过滤输入文本"""
    if not os.path.exists(keyword_path):
        raise FileNotFoundError(f"敏感词库文件未找到: {keyword_path}")

    gfw = create_filter(filter_type, repl)  # 创建指定类型的过滤器

    return gfw.filter(text)  # 返回过滤后的文本和敏感词列表


# 主逻辑部分
def collect_sensitive_words_and_filter(text, filter_type="DFA", repl="*"):
    """收集触发的敏感词并过滤消息"""
    print(f"开始过滤，输入文本: {text}")  # 调试语句
    try:
        filtered_text, sensitive_words = filter_text(text, filter_type=filter_type, repl=repl)
        print(f"过滤后的文本: {filtered_text}")  # 调试语句
        print(f"命中的敏感词: {sensitive_words}")  # 调试语句
        return sensitive_words, filtered_text
    except FileNotFoundError as e:
        print(f"敏感词过滤失败: {e}")
        return [], text


def process_document(input_text):
    """处理文档，过滤每一页的敏感词并记录触发的敏感词"""
    processed_text = ""  # 存储处理后的文本
    pages = input_text.split('\n\n')  # 简单的分页模拟逻辑，按双换行符分隔页
    all_sensitive_words = []  # 存储所有页面的敏感词

    for page in pages:
        sensitive_words, filtered_page = collect_sensitive_words_and_filter(page)  # 过滤每一页
        all_sensitive_words.extend(sensitive_words)  # 汇总所有页的敏感词
        processed_text += filtered_page + '\n'  # 拼接过滤后的页面文本

    return all_sensitive_words, processed_text  # 返回敏感词列表和处理后的文档


# main 函数用于测试
def main():
    input_text = """
    Page1: This is a test document. It contains some sensitive words.
    Page2: Another page with content that may trigger the filter.
    SensitiveWord is on this page too.
    """  # 测试输入文档内容

    triggered_words, cleaned_text = process_document(input_text)  # 调用处理文档函数

    # 输出处理结果
    print("触发的敏感词:")
    print(triggered_words)
    print("\n清理后的文档:")
    print(cleaned_text)


if __name__ == '__main__':
    main()  # 如果直接运行此脚本，执行 main 函数
