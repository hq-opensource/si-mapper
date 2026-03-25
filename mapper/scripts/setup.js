const { execSync } = require('child_process');
const path = require('path');

const isWin = process.platform === 'win32';
const script = isWin
  ? path.join(__dirname, 'setup.bat')
  : path.join(__dirname, 'setup.sh');

execSync(script, { stdio: 'inherit', shell: true });

