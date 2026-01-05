const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const analyzeBtn = document.getElementById('analyze-btn');
const loadingState = document.getElementById('loading-state');
const resultsSection = document.getElementById('results-section');
const ingredientsList = document.getElementById('ingredients-list');
const recipesGrid = document.getElementById('recipes-grid');
const modal = document.getElementById('recipe-modal');

let currentFile = null;

// Drag & Drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) return;
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        previewContainer.style.display = 'flex';
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    currentFile = null;
    fileInput.value = '';
    previewContainer.style.display = 'none';
    analyzeBtn.disabled = true;
    resultsSection.classList.add('hidden');
}

// Analyze
analyzeBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    // UI Updates
    loadingState.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/process-image', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Analysis failed');

        const data = await response.json();
        renderResults(data);

    } catch (error) {
        console.error(error);
        alert('An error occurred during analysis. Please try again.');
    } finally {
        loadingState.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
});

function renderResults(data) {
    resultsSection.classList.remove('hidden');

    // 1. Detected Ingredients
    ingredientsList.innerHTML = data.detected_ingredients.map(ing =>
        `<span class="ingredient-tag"><i class="fa-solid fa-check"></i> ${ing}</span>`
    ).join('');

    // 2. Recipes
    recipesGrid.innerHTML = '';
    if (data.suggested_recipes.length === 0) {
        recipesGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No matching recipes found.</p>';
        return;
    }

    data.suggested_recipes.forEach(recipe => {
        const card = document.createElement('div');
        card.className = 'recipe-card';
        // Use a generic placeholder if image_url is just the recipe page url
        // We'll create a nice gradient placeholder with text
        const safeRating = recipe.rating && recipe.rating !== 'nan' ? recipe.rating : 'N/A';

        card.innerHTML = `
            <div class="recipe-image">
                <i class="fa-solid fa-utensils fa-2x"></i>
            </div>
            <div class="recipe-title">${recipe.name}</div>
            <div class="recipe-meta">
                <span><i class="fa-regular fa-clock"></i> ${recipe.total_time || recipe.cook_time || '? mins'}</span>
                <span><i class="fa-solid fa-star"></i> ${safeRating}</span>
            </div>
        `;

        card.addEventListener('click', () => openModal(recipe));
        recipesGrid.appendChild(card);
    });
}

// Modal Logic
const modalTitle = document.getElementById('modal-title');
const modalTime = document.getElementById('modal-time');
const modalRating = document.getElementById('modal-rating');
const modalIngredients = document.getElementById('modal-ingredients');
const modalDirections = document.getElementById('modal-directions');
const closeBtn = document.querySelector('.close-modal');

function openModal(recipe) {
    console.log('Opening recipe:', recipe);
    modalTitle.textContent = recipe.name;
    modalTime.innerHTML = `<i class="fa-regular fa-clock"></i> ${recipe.cook_time || 'N/A'}`;
    modalRating.innerHTML = `<i class="fa-solid fa-star"></i> ${recipe.rating || 'N/A'}`;

    // Format Ingredients
    if (Array.isArray(recipe.ingredients)) {
        modalIngredients.innerHTML = recipe.ingredients.map(item => {
            const qty = item.quantity || '';
            const unit = item.unit || '';
            const name = item.name || '';
            return `<li>${qty} ${unit} ${name}</li>`;
        }).join('');
    } else {
        modalIngredients.innerHTML = '<li>No ingredients listed</li>';
    }

    // Format Directions
    if (Array.isArray(recipe.directions)) {
        modalDirections.innerHTML = recipe.directions.map(step =>
            `<li>${step}</li>`
        ).join('');
    } else {
        modalDirections.innerHTML = '<li>No directions listed</li>';
    }

    modal.classList.remove('hidden');
    modal.classList.add('active');
}

closeBtn.addEventListener('click', () => modal.classList.remove('active'));
window.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
});
