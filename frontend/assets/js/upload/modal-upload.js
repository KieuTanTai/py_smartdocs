document.addEventListener("click", (event) => {
  const driveBtn = event.target.closest(
    'button[id*="upload_source_drive"]:not([id*="sidebar"])'
  );
  const localBtn = event.target.closest(
    'button[id*="upload_source_local"]:not([id*="sidebar"])'
  );

  if (!driveBtn && !localBtn) {
    return;
  }

  if (driveBtn && typeof window.openGooglePicker === "function") {
    event.preventDefault();
    window.openGooglePicker();
    return;
  }

  const modalFileInput = document.querySelector('input[name="upload_files"]');
  if (localBtn && modalFileInput) {
    event.preventDefault();
    modalFileInput.click();
  }
});
