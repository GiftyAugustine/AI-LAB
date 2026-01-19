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
    // Add Input Box if not exists
    if (!document.getElementById('add-ingredient-container')) {
        const addContainer = document.createElement('div');
        addContainer.id = 'add-ingredient-container';
        addContainer.className = 'add-ingredient-box';
        addContainer.innerHTML = `
            <input type="text" id="new-ingredient" placeholder="Add ingredient...">
            <button id="add-ing-btn"><i class="fa-solid fa-plus"></i></button>
        `;
        ingredientsList.parentNode.insertBefore(addContainer, ingredientsList);

        // Add event listeners
        const input = addContainer.querySelector('input');
        const btn = addContainer.querySelector('button');

        const addIngredient = () => {
            const val = input.value.trim();
            if (val) {
                // Add to current list and refresh
                const currentIngs = Array.from(document.querySelectorAll('.ingredient-tag span')).map(s => s.textContent.trim());

                // Check for duplicates (case-insensitive)
                if (currentIngs.some(ing => ing.toLowerCase() === val.toLowerCase())) {
                    alert('Ingredient is already in the list!');
                    input.value = '';
                    return;
                }

                currentIngs.push(val);
                updateRecipes(currentIngs);
                input.value = '';
            }
        };

        btn.addEventListener('click', addIngredient);
        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') addIngredient(); });
    }

    ingredientsList.innerHTML = data.detected_ingredients.map(ing =>
        `<span class="ingredient-tag">
            <i class="fa-solid fa-check"></i> <span>${ing}</span>
            <i class="fa-solid fa-times remove-ing" onclick="removeIngredient('${ing}')"></i>
        </span>`
    ).join('');

    // Attach global remover to window if not already
    if (!window.removeIngredient) {
        window.removeIngredient = (ingToRemove) => {
            const currentIngs = Array.from(document.querySelectorAll('.ingredient-tag span')).map(s => s.textContent.trim());
            const newIngs = currentIngs.filter(i => i !== ingToRemove);
            updateRecipes(newIngs);
        };
    }

    async function updateRecipes(ingredients) {
        // Show loading or opacity
        recipesGrid.style.opacity = '0.5';

        try {
            const response = await fetch('/api/search-recipes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ingredients: ingredients })
            });
            const newData = await response.json();
            renderResults(newData); // Recursive re-render
        } catch (e) {
            console.error(e);
        } finally {
            recipesGrid.style.opacity = '1';
        }
    }

    // 2. Recipes logic
    recipesGrid.innerHTML = '';

    // Helper to create card
    const createCard = (recipe, isPartial = false) => {
        const card = document.createElement('div');
        card.className = 'recipe-card';
        const safeRating = recipe.rating && recipe.rating !== 'nan' ? recipe.rating : 'N/A';

        let missingBadge = '';
        if (isPartial && recipe.missing_count > 0) {
            missingBadge = `<div class="missing-badge"><i class="fa-solid fa-cart-shopping"></i> Missing ${recipe.missing_count}</div>`;
        }

        // Try to use image_url if valid, else placeholder
        let imageContent = `<i class="fa-solid fa-utensils fa-2x"></i>`;
        if (recipe.image_url && recipe.image_url.startsWith('http')) {
            imageContent = `<img src="${recipe.image_url}" alt="${recipe.name}" style="width:100%; height:100%; object-fit:cover;">`;
        }

        card.innerHTML = `
            ${missingBadge}
            <div class="recipe-image">
                ${imageContent}
            </div>
            <div class="recipe-title">${recipe.name}</div>
            <div class="recipe-meta">
                <span><i class="fa-regular fa-clock"></i> ${recipe.total_time || recipe.cook_time || '? m'}</span>
                <span><i class="fa-solid fa-star"></i> ${safeRating}</span>
            </div>
        `;
        card.addEventListener('click', () => {
            // If partial, add missing info to modal context
            recipe._isPartial = isPartial;
            openModal(recipe);
        });
        return card;
    };

    // --- Section 1: Exact Matches ---
    if (data.exact_matches.length > 0) {
        const exactSection = document.createElement('div');
        exactSection.className = 'full-width-section';
        exactSection.innerHTML = `<h3><i class="fa-solid fa-check-circle"></i> Perfect Matches (Cook Now!)</h3>`;
        const grid = document.createElement('div');
        grid.className = 'recipes-grid';
        data.exact_matches.forEach(r => grid.appendChild(createCard(r, false)));
        exactSection.appendChild(grid);
        recipesGrid.appendChild(exactSection);
    }

    // --- Section 2: Partial Matches ---
    if (data.partial_matches.length > 0) {
        const partialSection = document.createElement('div');
        partialSection.className = 'full-width-section';
        partialSection.innerHTML = `<h3><i class="fa-solid fa-basket-shopping"></i> Need a Few Items</h3>`;
        const grid = document.createElement('div');
        grid.className = 'recipes-grid';
        data.partial_matches.forEach(r => grid.appendChild(createCard(r, true)));
        partialSection.appendChild(grid);
        recipesGrid.appendChild(partialSection);
    }

    if (data.exact_matches.length === 0 && data.partial_matches.length === 0) {
        recipesGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No matching recipes found.</p>';
    }
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
