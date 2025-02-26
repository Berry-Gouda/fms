function connectToDB(){
    window.electronAPI.connectToDB("DB Connection Attempt");
    sendConnectRequest()
}

async function sendConnectRequest() {
    try{
        let response = await fetch("http://localhost:8080/connect-db");

        if (!response.ok) {  // Check if HTTP response is OK (status 200)
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        let data = await response.json();

        console.log("Parsed JSON:", data); // Debugging step

        document.getElementById("response").innerText = data.message;

        if (data.success){
            setTimeout(() => {
                window.electronAPI.loadNewPage("/templates/dbschema.html");
            }, 500);
            
        } else {
            console.error("API returned success = false");
        }
    }catch(error){
        console.error("Fetch error: ", error);
    }
}
