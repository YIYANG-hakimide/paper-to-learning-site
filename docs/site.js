const dialog = document.querySelector(".lightbox");
const dialogImage = dialog.querySelector("img");
const closeButton = dialog.querySelector(".lightbox-close");

document.querySelectorAll("[data-lightbox]").forEach((button) => {
  button.addEventListener("click", () => {
    dialogImage.src = button.dataset.lightbox;
    dialogImage.alt = button.querySelector("img")?.alt || "大图预览";
    dialog.showModal();
  });
});

closeButton.addEventListener("click", () => dialog.close());

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) {
    dialog.close();
  }
});

dialog.addEventListener("close", () => {
  dialogImage.src = "";
});
