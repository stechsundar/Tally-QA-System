const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow;
let streamlitProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "Tally AI Expert",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    // Hide the menu bar
    autoHideMenuBar: true,
  });

  const url = 'http://localhost:8501';

  // Function to check if Streamlit is ready
  const checkReady = () => {
    http.get(url, (res) => {
      mainWindow.loadURL(url);
    }).on('error', (err) => {
      console.log('Waiting for Streamlit...');
      setTimeout(checkReady, 1000);
    });
  };

  checkReady();

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function startStreamlit() {
  const isPackaged = !process.env.ELECTRON_START_URL && app.isPackaged;
  let pythonPath;
  let args;

  if (isPackaged) {
    // In production, use the bundled backend exe
    pythonPath = path.join(process.resourcesPath, 'dist', 'tally-ai-backend', 'tally-ai-backend.exe');
    args = []; // The pyinstaller exe already knows what to run
  } else {
    // In development
    pythonPath = path.join(__dirname, 'tallyenv', 'Scripts', 'python.exe');
    args = [
      '-m', 'streamlit', 'run',
      path.join(__dirname, 'app.py'),
      '--server.headless', 'true',
      '--server.port', '8501'
    ];
  }

  streamlitProcess = spawn(pythonPath, args, {
    cwd: isPackaged ? path.join(process.resourcesPath, 'dist', 'tally-ai-backend') : __dirname,
    shell: true
  });

  streamlitProcess.stdout.on('data', (data) => {
    console.log(`Streamlit: ${data}`);
  });

  streamlitProcess.stderr.on('data', (data) => {
    console.error(`Streamlit Error: ${data}`);
  });
}

app.on('ready', () => {
  startStreamlit();
  createWindow();
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    if (streamlitProcess) streamlitProcess.kill();
    app.quit();
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});

process.on('exit', () => {
  if (streamlitProcess) streamlitProcess.kill();
});
