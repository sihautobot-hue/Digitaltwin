# Builder for Model 4 V3 Pipeline
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def save(fname, content):
    p = os.path.join(BASE, fname)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print('Created:', fname)

print('Builder initialized.')
