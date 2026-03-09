import re

def has_batchim(word):
    if not word:
        return False
    last_char = word[-1]
    if 0xAC00 <= ord(last_char) <= 0xD7AF:
        return (ord(last_char) - 0xAC00) % 28 != 0
    return False

def fix_josa(text):
    """텍스트 내 조사를 받침에 맞게 교정"""
    # 교정할 조사 쌍 정의
    josa_map = {
        '은': '는', '는': '은',
        '이': '가', '가': '이',
        '을': '를', '를': '을',
        '과': '와', '와': '과'
    }
    
    words = text.split()
    fixed_words = []
    
    for word in words:
        base = word[:-1]
        josa = word[-1]
        
        if josa in josa_map:
            should_have_batchim_josa = has_batchim(base)

            if should_have_batchim_josa and josa in ['는', '가', '를', '와']:
                word = base + josa_map[josa]
            elif not should_have_batchim_josa and josa in ['은', '이', '을', '과']:
                word = base + josa_map[josa]
        
        fixed_words.append(word)
        
    return " ".join(fixed_words)


sample_text = "텍스처 어태치먼트과 렌더버퍼 객체"
print(fix_josa(sample_text))