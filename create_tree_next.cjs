const fs = require('fs');
const path = require('path');

const IGNORE_FOLDERS = [
  'node_modules',
  '.git',
  '.next',
  'dist',
  'build',
  '__pycache__',
  'site-packages'
];


let output = '';

function generateTree(dir, prefix = '') {
  const items = fs.readdirSync(dir);
  const filteredItems = items.filter(item => !IGNORE_FOLDERS.includes(item));
  
  filteredItems.forEach((item, index) => {
    const itemPath = path.join(dir, item);
    const isLast = index === filteredItems.length - 1;
    const currentPrefix = prefix + (isLast ? '└── ' : '├── ');
    
    output += currentPrefix + item + '\n';
    
    if (fs.statSync(itemPath).isDirectory()) {
      const nextPrefix = prefix + (isLast ? '    ' : '│   ');
      generateTree(itemPath, nextPrefix);
    }
  });
}

generateTree('.');
fs.writeFileSync('project-structure.txt', output);
console.log('Project structure saved to project-structure.txt');