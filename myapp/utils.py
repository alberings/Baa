import re

def sanitize_js(js_code):
    
    dangerous_patterns = [
        r'<script>',
        r'</script>',
        r'eval\(',
        r'innerHTML',
        r'outerHTML',
        r'document.cookie',
        r'window.location',
        r'localStorage',
        r'sessionStorage',
    ]
    
    for pattern in dangerous_patterns:
        js_code = re.sub(pattern, '', js_code, flags=re.IGNORECASE)
    
    return js_code

