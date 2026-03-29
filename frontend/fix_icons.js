const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(function(file) {
    file = dir + '/' + file;
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) { 
      results = results.concat(walk(file));
    } else { 
      if(file.endsWith('.vue') || file.endsWith('.js')) results.push(file);
    }
  });
  return results;
}

const files = walk('./src');
files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  if (content.includes('@phosphor-icons/vue')) {
    // Regex to find import { ... } from '@phosphor-icons/vue'
    const importRegex = /import\s+\{([^}]+)\}\s+from\s+['\"]@phosphor-icons\/vue['\"]/g;
    let match;
    const replacements = [];
    while ((match = importRegex.exec(content)) !== null) {
      const icons = match[1].split(',').map(i => i.trim()).filter(i => i);
      const newIcons = icons.map(icon => {
        // if not already prefixed with Ph, prefix it
        if (!icon.startsWith('Ph')) {
            const newIcon = 'Ph' + icon;
            // also replace usage in the template and script
            const componentTagRegex = new RegExp(`<${icon}([^a-zA-Z0-9_-])`, 'g');
            content = content.replace(componentTagRegex, `<${newIcon}$1`);
            
            const componentEndTagRegex = new RegExp(`<\/${icon}>`, 'g');
            content = content.replace(componentEndTagRegex, `</${newIcon}>`);

            const getIconRegex = new RegExp(`return ${icon}`, 'g');
            content = content.replace(getIconRegex, `return ${newIcon}`);
            
            const arrayRegex = new RegExp(`icon: ${icon}`, 'g');
            content = content.replace(arrayRegex, `icon: ${newIcon}`);

            return newIcon;
        }
        return icon;
      });
      content = content.replace(match[0], `import { ${newIcons.join(', ')} } from '@phosphor-icons/vue'`);
    }
    fs.writeFileSync(file, content);
  }
});
console.log('Phosphor icons updated.');
