document.addEventListener("DOMContentLoaded", function() {
    const divs = document.querySelectorAll(".tbl-btn");

    divs.forEach(div => {
        div.addEventListener("click", function(){
            let tname = this.innerText.trim();
            window.location.href = `http://localhost:8080/table-page?table=${encodeURIComponent(tname)}`;
        })
    });
})

function sendTableName(data){

}