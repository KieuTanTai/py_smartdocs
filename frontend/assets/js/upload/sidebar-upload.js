document.addEventListener("DOMContentLoaded", () => {
  const uploadDragArea = document.getElementById("upload-drag-area");
  const sidebarFileInput = document.querySelector(
    'input[name="upload_files_sidebar"]'
  );
  
  const driveBtn = document.querySelector(
    'button[id*="upload_source_drive_sidebar"]'
  );
  const localBtn = document.querySelector(
    'button[id*="upload_source_local_sidebar"]'
  );

  if (!uploadDragArea || !sidebarFileInput) {
    return;
  }

  uploadDragArea.addEventListener("click", () => {
    sidebarFileInput.click();
  });

  uploadDragArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadDragArea.style.borderColor = "var(--upload-button)";
    uploadDragArea.style.background = "rgba(93, 185, 116, 0.15)";
  });

  uploadDragArea.addEventListener("dragleave", () => {
    uploadDragArea.style.borderColor = "";
    uploadDragArea.style.background = "";
  });

  uploadDragArea.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadDragArea.style.borderColor = "";
    uploadDragArea.style.background = "";

    if (event.dataTransfer && event.dataTransfer.files) {
      sidebarFileInput.files = event.dataTransfer.files;
      sidebarFileInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });

  if (driveBtn) {
    driveBtn.addEventListener("click", (event) => {
      event.preventDefault();
      if (typeof window.openGooglePicker === "function") {
        window.openGooglePicker();
      }
    });
  }

  if (localBtn) {
    localBtn.addEventListener("click", (event) => {
      event.preventDefault();
      sidebarFileInput.click();
    });
  }
});
