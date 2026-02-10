const fs = require('fs');
const path = require('path');

const IGNORE_FOLDERS = [
  'node_modules',
  '.git',
  '.next',
  'dist',
  'build',
  'tally_chroma_db',
  '__pycache__'
];

let output = '';

function generateTree(dir) {
  const items = fs.readdirSync(dir)
    // ignore dotfiles
    .filter(item => !item.startsWith('.'))
    // ignore noisy folders
    .filter(item => !IGNORE_FOLDERS.includes(item));

  // separate folders and files
  const folders = items.filter(item =>
    fs.statSync(path.join(dir, item)).isDirectory()
  );
  const files = items.filter(item =>
    fs.statSync(path.join(dir, item)).isFile()
  );

  // folders first, then files
  const visibleItems = [...folders, ...files];

  visibleItems.forEach((item, index) => {
    const isLast = index === visibleItems.length - 1;
    output += (isLast ? '└── ' : '├── ') + item + '\n';
  });
}

generateTree('.');
fs.writeFileSync('project-structure.txt', output);
console.log('Project structure saved to project-structure.txt');
