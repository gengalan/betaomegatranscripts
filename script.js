// script.js
document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("uploadForm");
  const pdfInput = document.getElementById("pdfFile");
  const messageDiv = document.getElementById("message");

  uploadForm.addEventListener("submit", function (event) {
    event.preventDefault();

    // Basic validation: check if PDF is selected
    if (!pdfInput.value) {
      messageDiv.style.color = "red";
      messageDiv.textContent = "Please choose a PDF file.";
      return;
    }

    // For demonstration purposes, just show a success message
    // In a real scenario, you'd send the file to a server here
    messageDiv.style.color = "green";
    messageDiv.textContent = "Transcript PDF successfully uploaded!";
    
    // Clear the form
    pdfInput.value = "";
  });
});
