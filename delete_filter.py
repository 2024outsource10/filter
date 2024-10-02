def remove_keyword_from_file(keywords_path, keyword_to_remove):
    """
    从敏感词库文件中删除整行只有指定词的行，并将修改后的内容写回文件。
    :param keywords_path: 敏感词库文件的路径
    :param keyword_to_remove: 需要删除的敏感词（整行只有该词时才删除）
    """
    new_keywords = []

    # 打开敏感词文件并逐行读取
    with open(keywords_path, 'r', encoding='utf-8') as file:
        for line in file:
            keyword = line.strip()  # 去掉行首和行尾的空白符和换行符
            # 只有当整行等于 keyword_to_remove 时，才跳过该行
            if keyword != keyword_to_remove:
                new_keywords.append(keyword)  # 保留其他敏感词

    # 将修改后的敏感词库写回文件
    with open(keywords_path, 'w', encoding='utf-8') as file:
        for keyword in new_keywords:
            file.write(keyword + '\n')  # 每个敏感词写入一行

    print(f"整行包含敏感词'{keyword_to_remove}'的行已从 {keywords_path} 中删除。")


if __name__ == "__main__":
    # 假设你的敏感词库文件路径为 "keywords.txt"
    keywords_file_path = "keywords.txt"

    # 要删除的敏感词（整行只有该词才会删除）
    keyword_to_remove = "为人"

    # 调用函数，删除指定的敏感词
    remove_keyword_from_file(keywords_file_path, keyword_to_remove)
