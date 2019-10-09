import re
import json


phrases = []
with open('uz.txt', encoding='utf-8') as f:
    for line in f:
        phrases.append(re.sub(r'\d+\)\t', '', line)[:-1])

with open('uz.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(phrases, ensure_ascii=False))
phrases.clear()

with open('ru.txt', encoding='utf-8') as f:
    for line in f:
        phrases.append(re.sub(r'\d+\) ', '', line)[:-1])

with open('ru.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(phrases, ensure_ascii=False))
phrases.clear()

with open('en.txt', encoding='utf-8') as f:
    for line in f:
        phrases.append(re.sub(r'\d+\.\t', '', line)[:-1])

with open('en.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(phrases, ensure_ascii=False))
