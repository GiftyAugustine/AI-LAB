document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  const imageUpload = document.getElementById('imageUpload');
  const preview = document.getElementById('preview');
  const resultBox = document.getElementById('result');

  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (imageUpload.files.length === 0) {
        alert('Please upload an image first.');
        return;
      }

      const file = imageUpload.files[0];
      const reader = new FileReader();

      // Preview uploaded image
      reader.onload = () => {
        preview.innerHTML = `<img src="${reader.result}" alt="Uploaded Image" />`;
      };
      reader.readAsDataURL(file);

      // Prepare data to send to backend
      const formData = new FormData();
      formData.append('image', file);

      resultBox.innerHTML = "<p>Analyzing image with AI... please wait ⏳</p>";

      try {
        const res = await fetch("http://127.0.0.1:5001/analyze", {
          method: "POST",
          body: formData
        });

        const data = await res.json();

        resultBox.innerHTML = `<h3>🍳 Suggested Recipes:</h3><p>${data.result}</p>`;
      } catch (error) {
        console.error("Error:", error);
        resultBox.innerHTML = "<p style='color: red;'>Error analyzing image. Please try again.</p>";
      }
    });
  }
});
