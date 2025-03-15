def expand_query(query):
    """
    扩展查询词，支持中英文
    :param query: 输入的查询词
    :return: 扩展后的查询词
    """
    from nltk.corpus import wordnet
    import jieba
    
    expanded_terms = set()
    
    # 使用结巴分词处理中文
    words = jieba.cut(query)
    
    for word in words:
        # 跳过停用词和特殊字符
        if len(word.strip()) < 1:
            continue
            
        try:
            # 获取同义词
            synsets = wordnet.synsets(word)
            for syn in synsets:
                # 添加同义词
                for lemma in syn.lemmas():
                    expanded_terms.add(lemma.name())
                # 添加上位词
                if syn.hypernyms():
                    for hypernym in syn.hypernyms():
                        expanded_terms.add(hypernym.lemmas()[0].name())
        except Exception as e:
            print(f"处理词语 '{word}' 时出错: {str(e)}")
            continue
    
    # 过滤掉包含下划线的术语
    expanded_terms = {term for term in expanded_terms if '_' not in term}
    
    # 如果没有找到扩展词，返回原始查询
    if not expanded_terms:
        return query
        
    expanded_query = f"{query} {' '.join(expanded_terms)}"
    return expanded_query

if __name__ == '__main__':
    # 测试用例
    test_queries = [
        'oracle ORA-4031 如何解决r',
        'database performance tuning',
        '数据库性能优化',
    ]
    
    for q in test_queries:
        print(f"\n原始查询: {q}")
        print(f"扩展查询: {expand_query(q)}")
