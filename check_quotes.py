#!/usr/bin/env python3
import re

with open('3rd/docker_scripts/import_docker_images.sh', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
    lines = content.split('\n')

in_double_quote = False
in_single_quote = False

for i, line in enumerate(lines, 1):
    j = 0
    while j < len(line):
        c = line[j]
        
        if c == '\\' and j + 1 < len(line):
            j += 2
            continue
            
        if c == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            status = "OPEN" if in_double_quote else "CLOSE"
            print(f'Line {i}: double quote {status} at pos {j}')
        elif c == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            
        j += 1
    
    # 行末检查
    if in_double_quote:
        print(f'  -> Line {i} ends with open double quote')
        print(f'     {line}')
