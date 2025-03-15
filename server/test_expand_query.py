import logging
from testqa import expand_query

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_expand_query():
    # 测试用例
    test_queries = [
        'oracle ORA-4031 如何解决',
        'database performance tuning',
        '数据库性能优化',
        'backup recovery',
        '表空间管理'
    ]
    
    print("\n=== 查询扩展测试 ===")
    for query in test_queries:
        print(f"\n原始查询: {query}")
        expanded = expand_query(query)
        print(f"扩展查询: {expanded}")
        print("-" * 50)

if __name__ == '__main__':
    test_expand_query() 