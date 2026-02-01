document.addEventListener('DOMContentLoaded', async () => {
    const glossaryContainer = document.getElementById('glossary-container');
    const alphabetNav = document.getElementById('alphabet-nav');
    const searchInput = document.getElementById('glossary-search');

    let glossaryData = null;

    // Load glossary data
    try {
        const response = await fetch('/static/glossary.json');
        glossaryData = await response.json();
        renderGlossary(glossaryData);
        renderAlphabetNav(Object.keys(glossaryData).sort());
    } catch (error) {
        console.error('Error loading glossary:', error);
        glossaryContainer.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <p>Failed to load ingredient glossary. Please try again later.</p>
            </div>
        `;
    }

    function renderAlphabetNav(letters) {
        alphabetNav.innerHTML = '';
        letters.forEach(letter => {
            const link = document.createElement('a');
            link.href = `#section-${letter}`;
            link.className = 'alphabet-link';
            link.textContent = letter;
            link.onclick = (e) => {
                e.preventDefault();
                document.getElementById(`section-${letter}`).scrollIntoView({ behavior: 'smooth' });
                updateActiveLetter(letter);
            };
            alphabetNav.appendChild(link);
        });
    }

    function updateActiveLetter(activeLetter) {
        document.querySelectorAll('.alphabet-link').forEach(link => {
            link.classList.toggle('active', link.textContent === activeLetter);
        });
    }

    function renderGlossary(data) {
        glossaryContainer.innerHTML = '';

        const sortedLetters = Object.keys(data).sort();

        if (sortedLetters.length === 0) {
            glossaryContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <p>No ingredients found matching your search.</p>
                </div>
            `;
            return;
        }

        sortedLetters.forEach(letter => {
            const items = data[letter];

            const section = document.createElement('section');
            section.className = 'glossary-section';
            section.id = `section-${letter}`;

            section.innerHTML = `
                <h2 class="section-title">${letter}</h2>
                <div class="ingredient-grid">
                    ${items.map(item => `
                        <div class="ingredient-item">
                            <span class="ingredient-name">${item.name}</span>
                            <span class="ingredient-count">${item.count}</span>
                        </div>
                    `).join('')}
                </div>
            `;

            glossaryContainer.appendChild(section);
        });
    }

    // Search logic
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        if (!query) {
            renderGlossary(glossaryData);
            return;
        }

        const filteredData = {};
        Object.entries(glossaryData).forEach(([letter, items]) => {
            const filteredItems = items.filter(item => item.name.toLowerCase().includes(query));
            if (filteredItems.length > 0) {
                filteredData[letter] = filteredItems;
            }
        });

        renderGlossary(filteredData);
    });
});
