document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("uploadForm");
  const pdfInput = document.getElementById("pdfFile");
  const pcDropdown = document.getElementById("pcNumber");
  const messageDiv = document.getElementById("message");

  // Populate the PC dropdown dynamically
  const now = new Date();
  const year = now.getFullYear();
  const pcNumber = year % 100;
  for (let i = pcNumber - 4; i < pcNumber; i++) {
    const option = document.createElement("option");
    option.value = i.toString().padStart(2, "0"); // Format numbers as 00, 01, etc.
    option.textContent = `PC ${i.toString().padStart(2, "0")}`;
    pcDropdown.appendChild(option);
  }

  uploadForm.addEventListener("submit", function (event) {
    event.preventDefault();

    // Validate that both PC number and PDF are selected
    if (!pcDropdown.value) {
      messageDiv.style.color = "red";
      messageDiv.textContent = "Please select your PC number.";
      return;
    }

    if (!pdfInput.value) {
      messageDiv.style.color = "red";
      messageDiv.textContent = "Please choose a PDF file.";
      return;
    }

    const formData = new FormData();
    formData.append("pcNumber", pcDropdown.value);
    formData.append("pdfFile", pdfInput.files[0]);

    // Upload to S3:
    // 1. Create a presigned URL from the server
    // 2. Upload the file to the presigned URL
    // 3. Notify the user of success or failure
    // 4. Clear



    // Success message (simulate file upload)
    messageDiv.style.color = "green";
    messageDiv.textContent = `Transcript for PC ${pcDropdown.value} successfully uploaded!`;

    // Clear the form
    pcDropdown.value = "";
    pdfInput.value = "";
  });
});