from collections import deque, defaultdict
import os

# 全局变量，指定敏感词库文件的路径
keyword_path: str = os.getenv("KEYWORD_PATH", "./keyword.txt")


class ACAutomaton:
    """基于 Aho-Corasick 自动机的敏感词过滤器"""

    def __init__(self, repl="*"):
        """
        初始化过滤器:
        - repl: 替换敏感词的符号，默认为 '*'
        """
        self.repl = repl  # 替换符号
        self.goto = defaultdict(dict)  # 状态转移表
        self.fail = defaultdict(int)  # 失败指针表
        self.output = defaultdict(list)  # 输出表
        self.state_count = 0  # 当前状态数量
        self.parse(keyword_path)  # 使用全局的 keyword_path 进行解析
        self.build_automaton()  # 构建自动机

    def parse(self, path):
        """从文件中加载敏感词库并存储到自动机的转移表中"""
        with open(path, 'r', encoding='utf-8') as file:
            for keyword in file:
                self.add_word(keyword.strip().lower())

    def add_word(self, word):
        """将一个敏感词添加到自动机的字典树结构中"""
        current_state = 0
        for char in word:
            if char not in self.goto[current_state]:
                self.state_count += 1
                self.goto[current_state][char] = self.state_count
            current_state = self.goto[current_state][char]
        self.output[current_state].append(word)

    def build_automaton(self):
        """构建失败指针，并完成自动机的构建"""
        queue = deque()

        # 初始化失败指针
        for char, state in self.goto[0].items():
            self.fail[state] = 0
            queue.append(state)

        # BFS 构建失败指针
        while queue:
            current_state = queue.popleft()
            for char, next_state in self.goto[current_state].items():
                # 计算失败指针
                fail_state = self.fail[current_state]
                while fail_state != 0 and char not in self.goto[fail_state]:
                    fail_state = self.fail[fail_state]
                if char in self.goto[fail_state]:
                    self.fail[next_state] = self.goto[fail_state][char]
                else:
                    self.fail[next_state] = 0

                # 合并输出
                self.output[next_state].extend(self.output[self.fail[next_state]])

                queue.append(next_state)

    def filter(self, message):
        """使用 Aho-Corasick 自动机过滤消息中的敏感词，替换为指定字符"""
        message_lower = message.lower()  # 原始消息的副本用于匹配
        cleaned_message = re.sub(r'[^a-zA-Z\u4e00-\u9fff]', '', message_lower)  # 去除空格和特殊字符用于匹配

        current_state = 0  # 从初始状态开始
        ret = list(message)  # 将原始消息转化为可修改的列表，保留空格和符号
        sensitive_words = []  # 存储匹配到的敏感词
        cleaned_index = 0  # 在去除空格后的字符串中遍历的索引

        # 原始消息的遍历，保留空格和符号
        for i, char in enumerate(message_lower):
            if re.match(r'[^a-zA-Z\u4e00-\u9fff]', char):
                # 如果字符是空格或特殊字符，跳过匹配，直接跳过
                continue

            # Aho-Corasick 自动机的状态转移
            while current_state != 0 and cleaned_message[cleaned_index] not in self.goto[current_state]:
                current_state = self.fail[current_state]

            if cleaned_message[cleaned_index] in self.goto[current_state]:
                current_state = self.goto[current_state][cleaned_message[cleaned_index]]
            else:
                current_state = 0

            cleaned_index += 1  # 移动到下一个非空字符

            # 如果有敏感词输出
            if self.output[current_state]:
                for word in self.output[current_state]:
                    sensitive_words.append(word)
                    # 计算敏感词在原始消息中的位置
                    start = i - len(word) + 1
                    ret[start:i + 1] = self.repl * len(word)  # 替换敏感词为指定符号

        return ''.join(ret), sensitive_words  # 返回过滤后的文本和敏感词列表
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
