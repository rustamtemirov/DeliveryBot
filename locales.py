import json


print('Loading locales...')

locales = {}
with open('ru.json', encoding='utf-8') as f:
    locales['ru'] = json.loads(f.read())

with open('en.json', encoding='utf-8') as f:
    locales['en'] = json.loads(f.read())

with open('uz.json', encoding='utf-8') as f:
    locales['uz'] = json.loads(f.read())

print('Locales loaded')