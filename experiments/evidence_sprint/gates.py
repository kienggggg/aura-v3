import json
import unicodedata
import os

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_all_gates(content: str, bible_path: str, style_path: str) -> dict:
    results = {}
    
    # 1. Word count
    words = content.split()
    word_count = len(words)
    if 1500 <= word_count <= 2500:
        results["word_count"] = {"status": "PASS", "msg": f"Word count: {word_count}"}
    else:
        results["word_count"] = {"status": "FAIL", "msg": f"Word count {word_count} not in range 1500-2500"}
        
    # 2. Mojibake and forbidden chars
    import re
    mojibake_patterns = ["\ufffd", "Ã¡", "áº", "Ã´", "Ä‘"]
    mojibake_fail = next((p for p in mojibake_patterns if p in content), None)
    
    # Catch C0/C1, Bidi controls, but allow \n \r \t
    control_fail = re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\u200E-\u200F\u202A-\u202E]', content)
    
    if mojibake_fail:
        results["mojibake"] = {"status": "FAIL", "msg": f"Found mojibake pattern: {mojibake_fail}"}
    elif control_fail:
        results["mojibake"] = {"status": "FAIL", "msg": f"Found control character: {repr(control_fail.group())}"}
    else:
        results["mojibake"] = {"status": "PASS", "msg": "No mojibake found"}
        
    # 3. Required characters
    bible = load_json(bible_path)
    char_fails = []
    for char in bible.get('characters', []):
        if char.get('must_appear', False):
            import re
            name = char['name']
            if not re.search(r'\b' + re.escape(name) + r'\b', content):
                char_fails.append(name)
    if char_fails:
        results["characters"] = {"status": "FAIL", "msg": f"Missing characters: {', '.join(char_fails)}"}
    else:
        results["characters"] = {"status": "PASS", "msg": "All required characters found"}
        
    # 4. Prompt leak
    style_card = load_json(style_path)
    leak_words = ["BỐI CẢNH", "NHÂN VẬT", "YÊU CẦU CỨNG", "VĂN PHONG", "Tiểu thuyết gia"]
    for rule in style_card.get('rules', []):
        if len(rule.split()) > 3:
            # Snapshot of rule fragment
            leak_words.append(rule)
            
    # Normalize unicode, casefold, and collapse whitespaces
    def normalize_text(t):
        return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', t).casefold())
        
    normalized_content = normalize_text(content)
    leak_fails = []
    for w in leak_words:
        if normalize_text(w) in normalized_content:
            leak_fails.append(w)
            
    if leak_fails:
        results["prompt_leak"] = {"status": "FAIL", "msg": f"Found prompt leak: {leak_fails[0]}"}
    else:
        results["prompt_leak"] = {"status": "PASS", "msg": "No prompt leak found"}
        
    return results

def check_gate_overall(gate_results: dict) -> bool:
    for v in gate_results.values():
        if v.get("status") != "PASS":
            return False
    return True
