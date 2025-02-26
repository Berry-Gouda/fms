const { app, BrowserWindow, ipcMain } = require("electron");
const {dialog} = require("electron");
const path = require("path");

let win;

function createWindow(){
    win = new BrowserWindow({
        width: 1500,
        height: 1125,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            nodeIntegration: false,
        },
    });

    win.loadFile("index.html");
}

app.whenReady().then(() =>{
    createWindow();

    app.on("activate", () => {
        if(BrowserWindow.getAllWindows().length() === 0) createWindow();
    });
});

ipcMain.on("message", (event, msg) => {
    console.log("Recieved in main process: ", msg);
})

ipcMain.on("load-page", (event, page) => {
    if(win){
        const filePath = path.join(__dirname, page)
        console.log("Loading New Page: ", filePath);
        win.loadFile(filePath);
    }
    else{
        console.log("Error: Window not found!");
    }
});

ipcMain.handle("open-file", async() => {
    if(win){
       result  = await dialog.showOpenDialog(win,{
                            properties:['openFile'],
                        filters: [{extensions: ["csv"]}],
        });
    }
    return result.filePaths.length > 0 ? result.filePaths[0] : null;
});



app.on("window-all-closed", () => {
    if(process.platform !== "darwin") app.quit();
});