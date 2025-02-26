let compColumn = ''

document.addEventListener("DOMContentLoaded", function(){
    const columns = document.querySelectorAll(".column-tr");

    columns.forEach(tr =>{
        tr.addEventListener("click", function(){
            
            oldSelected = document.getElementById("selected")
            if (oldSelected){
                oldSelected.id = "";
                let allRows = Array.from(oldSelected.parentElement.children);
                let index = allRows.indexOf(oldSelected); 
                oldSelected.style.backgroundColor = index % 2 === 1 ? "lightgrey" : "";
            }
            tr.id = "selected";
            compColumn = tr.firstElementChild.innerHTML;
            tr.style.backgroundColor = "lightskyblue"
            console.log("Clicked: " + compColumn)
        });
    });
})

async function getCSV() {
    const path = await window.electronAPI.openFileExplorer();
    if (!path){
        alert("No File Selected");
        return;
    }
    if (!path.toLowerCase().endsWith(".csv")){
        alert("Must Select .csv file");
        return;
    }
    sendPathRecieveResult(path)
}

async function sendPathRecieveResult(path){
    const response = await fetch("http://localhost:8080/bulk-insert", {
        method: "POST",
        headers: {"Content-Type": "application/json",

        },
        body: JSON.stringify({
            file: path,
            table: document.getElementById("t-title").innerHTML
        }),
    });

    const data = await response.json();
    alert(data.message)
    
}

async function sendSearch(){
    const response = await fetch("http://localhost:8080/comp-column-search", {
        method: "POST",
        headers: {"Content-Type": "application/json",

        },
        body: JSON.stringify({
            table: document.getElementById("t-title").innerHTML,
            compColumn: compColumn,
            searchValue: document.getElementById("search-input").value
        }),

    });
    const data = await response.json();
    console.log(data.count)
}

