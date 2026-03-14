

let elCon = document.querySelector(".container");


function spaceSeparate(value) {
  if (value === null || value === undefined || value === "") {
    return value;
  }

  return Number(value)
    .toFixed(2) // 2 ta kasr
    .replace(/\B(?=(\d{3})+(?!\d))/g, " "); // minglik ajratish
}


elCon.addEventListener("click", (e) => {
    let card = e.target.closest(".product-card");
    if (!card) return;
    
    let elData = card.querySelector(".product__data");
    if (!elData) return;
    
    if (elData.style.display === "block") {
        elData.style.display = "none";
    } else {
        elData.style.display = "block";
        fetchData(card.dataset.id, elData);
    }
});

function fetchData(xomashyo_id, parent) {
    fetch(`/get/${xomashyo_id}/`)
    .then((res) => {
        console.log(res.status);
        return res.json();
    })
    .then((data) => {
        console.log(data);
        renderData(data, parent);
    })
    .catch((err) => console.error(err));
}

function renderData(data, parent) {
    parent.innerHTML = "";
    
    data.forEach((item) => {
        parent.innerHTML += `
        <div class="d-flex justify-content-between border-bottom py-1">
        <span>${item.zavod}</span>
        <span>${spaceSeparate(item.miqdor)} kg</span>
        </div>
        `;
    });
}

console.log(document.querySelector(".container"));
console.log(document.querySelectorAll(".product-card").length);
console.log(document.querySelectorAll(".product__data").length);