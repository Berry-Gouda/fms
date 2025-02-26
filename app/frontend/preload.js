const {contextBridge, ipcRenderer} = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
    connectToDB: (msg) => ipcRenderer.send("message", msg),
    loadNewPage: (page) => ipcRenderer.send("load-page", page),
    openFileExplorer: () => ipcRenderer.invoke("open-file"),
});