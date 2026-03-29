import os
import re

def fix_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '@phosphor-icons/vue' not in content:
        return

    # Find all imports from phosphor icons
    imports = re.findall(r'import\s+\{([^}]+)\}\s+from\s+[\'\"].*?@phosphor-icons/vue[\'\"]', content)
    for imp in imports:
        icons = [i.strip() for i in imp.split(',')]
        new_icons = []
        for icon in icons:
            if not icon: continue
            if not icon.startswith('Ph'):
                new_icon = 'Ph' + icon
                # Fix template tags <Icon ...
                content = re.sub(r'<' + icon + r'([^a-zA-Z0-9_-])', r'<' + new_icon + r'\1', content)
                # Fix closing tags </Icon>
                content = re.sub(r'</' + icon + r'>', r'</' + new_icon + r'>', content)
                # Fix return icon -> return PhIcon
                content = re.sub(r'return\s+' + icon + r'\b', r'return ' + new_icon, content)
                # Fix object literal icon: icon -> icon: PhIcon
                content = re.sub(r'icon:\s*' + icon + r'\b', r'icon: ' + new_icon, content)
                # Fix object literal when key matches value { Icon } or [Icon]
                content = re.sub(r'\b' + icon + r'\b(?!\.|\-)', new_icon, content)
                
                new_icons.append(new_icon)
            else:
                new_icons.append(icon)
        
        # Replace the import statement names
        content = content.replace(imp, ', '.join(new_icons))

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.vue') or file.endswith('.js'):
            fix_file(os.path.join(root, file))
print('Phosphor icons fixed!')
