document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("click", (event) => {
    const dropdowns = document.querySelectorAll("details.dropdown");
    dropdowns.forEach((dropdown) => {
      if (!dropdown.contains(event.target)) {
        dropdown.removeAttribute("open");
      }
    });
  });
});
