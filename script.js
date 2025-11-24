document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  const imageUpload = document.getElementById('imageUpload');
  const preview = document.getElementById('preview');

  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (imageUpload.files.length > 0) {
        const file = imageUpload.files[0];
        const formData = new FormData();
        formData.append("image", file);

        // Show preview
        const reader = new FileReader();
        reader.onload = () => {
          preview.innerHTML = `<img src="${reader.result}" alt="Uploaded Image" />`;
        };
        reader.readAsDataURL(file);

        // Call backend
        try {
          const response = await fetch("http://127.0.0.1:5001/analyze", {
            method: "POST",
            body: formData
          });

          const data = await response.json();

          // Show ingredients + recipes
          if (data.ingredients) {
            preview.innerHTML += `
              <h2>Detected Ingredients:</h2>
              <p>${data.ingredients}</p>
            `;
          }

          if (data.recipes && data.recipes.length > 0) {
            let recipeHTML = "<h2>Suggested Recipes:</h2><ul>";
            data.recipes.forEach(r => {
              recipeHTML += `<li><strong>${r.name}</strong> – ${r.ingredients}</li>`;
            });
            recipeHTML += "</ul>";
            preview.innerHTML += recipeHTML;
          } else {
            preview.innerHTML += `<p>No matching recipes found.</p>`;
          }

        } catch (err) {
          console.error("Error analyzing image:", err);
          preview.innerHTML += `<p style="color:red;">Error analyzing image. Please try again.</p>`;
        }
      }
    });
  }
});
