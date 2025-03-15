from bs4 import BeautifulSoup

def get_table_caption(table):
    """
    获取 table 上方的描述文本作为该表格的抬头：
    1. 优先查找前面的兄弟元素中是否存在 h1～h6 标签；
    2. 若无，则查找 p 标签中非空且不为“Back to Top”的文本；
    3. 如果仍然没有，则尝试使用 table 的 summary 属性；
    4. 最后使用默认名称。
    """
    caption = None
    prev = table.find_previous_sibling()
    while prev:
        if prev.name and prev.name.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = prev.get_text(strip=True)
            if text:
                caption = text
                break
        if prev.name == 'p':
            text = prev.get_text(strip=True)
            if text and text.lower() not in ['back to top', '']:
                caption = text
                break
        prev = prev.find_previous_sibling()
    if not caption:
        caption = table.get("summary", "").strip()
    if not caption:
        caption = "Unnamed Table"
    return caption

def parse_table(table):
    """
    对单个 table 进行解析：
    1. 提取列名（先尝试 <thead> 中的 th 标签，否则尝试第一行中的 th，
       如果依然没有则根据第一行 td 数量生成默认列名）。
    2. 按行提取数据，生成一个字典，键为列名，值为该列所有数据（列表）。
    """
    headers = []
    thead = table.find('thead')
    if thead:
        headers = [th.get_text(strip=True) for th in thead.find_all('th')]
    else:
        first_row = table.find('tr')
        if first_row:
            headers = [th.get_text(strip=True) for th in first_row.find_all('th')]
    if not headers:
        first_row_td = table.find('tr')
        if first_row_td:
            tds = first_row_td.find_all('td')
            headers = [f"col_{i}" for i in range(len(tds))]
    
    col_data = {header: [] for header in headers}
    
    # 提取数据行：优先使用 <tbody>，否则使用所有 tr，跳过含 th 的行
    rows = []
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        rows = table.find_all('tr')
        if rows and rows[0].find_all('th'):
            rows = rows[1:]
    
    for row in rows:
        tds = row.find_all('td')
        if not tds:
            continue
        row_values = [td.get_text(strip=True) for td in tds]
        if len(row_values) < len(headers):
            row_values.extend([""] * (len(headers) - len(row_values)))
        for i, header in enumerate(headers):
            col_data[header].append(row_values[i])
    
    return headers, col_data

def parse_awr_report(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    
    combined_dict = {}
    for table in tables:
        caption = get_table_caption(table)
        headers, col_data = parse_table(table)
        combined_dict[caption] = col_data
    return combined_dict

def dict_to_text(combined_dict):
    """
    将生成的字典数据转换为文本格式，
    每个表格的抬头作为段落标题，每一列显示列名及对应的数据列表。
    """
    lines = []
    for caption, col_data in combined_dict.items():
        lines.append("表格抬头: " + caption)
        for col, values in col_data.items():
            # 将每一列的数据用逗号分隔后拼接
            line = f"  列名: {col} -> 数据: " + ", ".join(values)
            lines.append(line)
        lines.append("-" * 40)
    return "\n".join(lines)

if __name__ == "__main__":
    html_file = "../awr_report_16189_16190.html"
    combined_dict = parse_awr_report(html_file)
    
    # 将字典数据转换为文本格式
    text_output = dict_to_text(combined_dict)
    print("转换后的文本格式数据：\n")
    print(text_output)
