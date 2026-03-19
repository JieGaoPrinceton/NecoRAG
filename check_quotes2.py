#!/usr/bin/env python3
import re

with open('3rd/docker_scripts/import_docker_images.sh', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
    lines = content.split('\n')

# 跟踪引号状态
in_double_quote = False
in_single_quote = False
in_backtick = False
in_heredoc = False
heredoc_marker = ""

for i, line in enumerate(lines, 1):
    orig_line = line
    j = 0
    while j < len(line):
        c = line[j]
        
        # 跳过转义字符
        if c == '\\' and j + 1 < len(line):
            j += 2
            continue
            
        # 处理 heredoc
        if in_heredoc:
            if line.strip() == heredoc_marker:
                in_heredoc = False
                heredoc_marker = ""
            break
            
        # 检查 heredoc 开始
        if not in_double_quote and not in_single_quote and not in_backtick:
            heredoc_match = re.search(r'<<\s*[\'"]?(\w+)[\'"]?\s*$', line[j:])
            if heredoc_match:
                in_heredoc = True
                heredoc_marker = heredoc_match.group(1)
                break
        
        if c == '"' and not in_single_quote and not in_backtick:
            in_double_quote = not in_double_quote
        elif c == "'" and not in_double_quote and not in_backtick:
            in_single_quote = not in_single_quote
        elif c == '`' and not in_single_quote:
            in_backtick = not in_backtick
            
        j += 1
    
    # 行末检查
    if in_double_quote or in_single_quote or in_backtick or in_heredoc:
        state = []
        if in_double_quote: state.append('DOUBLE_QUOTE')
        if in_single_quote: state.append('SINGLE_QUOTE') 
        if in_backtick: state.append('BACKTICK')
        if in_heredoc: state.append('HEREDOC')
        print(f'Line {i}: OPEN {", ".join(state)}')
        print(f'  Content: {orig_line[:70]}...')
