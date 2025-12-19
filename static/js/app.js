document.addEventListener('DOMContentLoaded', () => {

    const redirectToResults = (ingredients) => {
        if (!ingredients || ingredients.length === 0) return;
        
        const query = ingredients.join(',');
        const encodedQuery = encodeURIComponent(query);
        window.location.href = `/results?q=${encodedQuery}`;
    };

    const handleUpload = async (file, spinner, apiEndpoint, btn, modalId) => {
        if (!file) {
            alert('Please select a file to upload.');
            return;
        }

        spinner.style.display = 'block';
        btn.disabled = true;

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unknown error occurred.');
            }

            if (data.ingredients && data.ingredients.length > 0) {
                const modalEl = document.getElementById(modalId);
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) {
                    modal.hide();
                }
                redirectToResults(data.ingredients);
            } else {
                alert('No ingredients were found in the image.');
            }

        } catch (error) {
            console.error(`Error uploading to ${apiEndpoint}:`, error);
            alert(`Upload failed: ${error.message}`);
        } finally {
            spinner.style.display = 'none';
            btn.disabled = false;
        }
    };

    const searchForm = document.getElementById('search-form');
    const ingredientInput = document.getElementById('ingredient-input');

    if (searchForm && ingredientInput) {
        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const query = ingredientInput.value.trim();
            if (query) {
                redirectToResults(query.split(',').map(s => s.trim()));
            }
        });
    }

    const receiptBtn = document.getElementById('receipt-upload-btn');
    const receiptFile = document.getElementById('receipt-file-input');
    const receiptSpinner = document.getElementById('receipt-spinner');

    if (receiptBtn) {
        receiptBtn.addEventListener('click', () => {
            const file = receiptFile.files[0];
            handleUpload(file, receiptSpinner, '/api/upload-receipt-ocr', receiptBtn, 'uploadReceiptModal');
        });
    }

    const fridgeBtn = document.getElementById('fridge-upload-btn');
    const fridgeFile = document.getElementById('fridge-file-input');
    const fridgeSpinner = document.getElementById('fridge-spinner');

    if (fridgeBtn) {
        fridgeBtn.addEventListener('click', () => {
            const file = fridgeFile.files[0];
            handleUpload(file, fridgeSpinner, '/api/upload-fridge-photo', fridgeBtn, 'uploadFridgeModal');
        });
    }

});