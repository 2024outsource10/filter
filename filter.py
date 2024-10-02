import ahocorasick
import os

# 全局变量，指定敏感词库文件的路径
keyword_path: str = os.getenv("KEYWORD_PATH", "./keyword.txt")

class ACAutomaton:
    """基于 ahocorasick 自动机的敏感词过滤器"""

    def __init__(self, repl="*"):
        """
        初始化过滤器:
        - repl: 用于替换敏感词的符号，默认为 '*'
        """
        self.repl = repl  # 替换符号
        self.automaton = ahocorasick.Automaton()  # 初始化 Aho-Corasick 自动机
        self.build_automaton()  # 构建自动机

    def build_automaton(self):
        """从文件中加载敏感词库并构建 Aho-Corasick 自动机"""
        if not os.path.exists(keyword_path):
            raise FileNotFoundError(f"敏感词库文件未找到: {keyword_path}")

        # 从文件中加载敏感词库
        with open(keyword_path, 'r', encoding='utf-8') as file:
            for line in file:
                keyword = line.strip().lower()
                if keyword:  # 如果该行不是空的，则添加到自动机
                    self.automaton.add_word(keyword, keyword)

        self.automaton.make_automaton()  # 构建自动机

    def filter(self, message):
        """使用 Aho-Corasick 自动机过滤消息中的敏感词，替换为指定字符"""
        message_lower = message.lower()  # 将消息转换为小写以进行不区分大小写的匹配
        result = list(message)  # 将消息转化为字符列表，以便进行替换
        sensitive_words = []  # 存储找到的敏感词

        # 使用 Aho-Corasick 自动机匹配敏感词
        for end_index, keyword in self.automaton.iter(message_lower):
            start_index = end_index - len(keyword) + 1
            sensitive_words.append(keyword)  # 记录找到的敏感词
            result[start_index:end_index + 1] = [self.repl] * len(keyword)  # 替换为指定符号

        return ''.join(result), sensitive_words  # 返回过滤后的文本和命中的敏感词


# 其他函数保持不变
from collections import defaultdict
import re

# 创建过滤器的函数
def create_filter(filter_type="AC", repl="*"):
    """根据过滤器类型创建并返回相应的过滤器实例"""
    if filter_type == "Naive":
        return NaiveFilter(repl)
    elif filter_type == "BS":
        return BSFilter(repl)
    elif filter_type == "DFA" or filter_type == "AC":
        return ACAutomaton(repl)
    else:
        raise ValueError("未知类型: choose from 'Naive', 'BS', or 'AC'.")

# 用于过滤文本的外部接口
def filter_text(text, filter_type="AC", repl="*"):
    """调用适当的过滤器来过滤输入文本"""
    if not os.path.exists(keyword_path):
        raise FileNotFoundError(f"敏感词库文件未找到: {keyword_path}")

    gfw = create_filter(filter_type, repl)  # 创建指定类型的过滤器

    return gfw.filter(text)  # 返回过滤后的文本和敏感词列表

# 主逻辑部分
def collect_sensitive_words_and_filter(text, filter_type="AC", repl="*"):
    """收集触发的敏感词并过滤消息"""
    print(f"开始过滤，输入文本: {text}")  # 调试语句
    try:
        filtered_text, sensitive_words = filter_text(text, filter_type=filter_type, repl=repl)
        print(f"过滤后的文本: {filtered_text}")  # 调试语句
        print(f"命中的敏感词: {sensitive_words}")  # 调试语句
        return sensitive_words, filtered_text
    except FileNotFoundError as e:
        print(f"敏感词过滤完成: {e}")
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
