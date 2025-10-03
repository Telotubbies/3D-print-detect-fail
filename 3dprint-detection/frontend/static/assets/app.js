const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const cardContainer = document.getElementById("cardContainer");

uploadBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  if (file.size > 20 * 1024 * 1024) {
    alert("File too large! Max 20MB.");
    return;
  }

  const formData = new FormData();
  formData.append("image", file);

  const res = await fetch("http://localhost:8000/cards", {
    method: "POST",
    body: formData
  });

  const data = await res.json();
  addCard(data);
});

function addCard(result) {
  const col = document.createElement("div");
  col.className = "col-md-5 mb-5";

  col.innerHTML = `
    <div class="card">
      <img src="http://localhost:8000${result.detected_image_url}" class="card-img-top">
      <div class="card-body">
        <h5 class="card-title">${result.status}</h5>
        <p class="card-text">${result.message}</p>
      </div>
    </div>
  `;

  cardContainer.prepend(col);
}
