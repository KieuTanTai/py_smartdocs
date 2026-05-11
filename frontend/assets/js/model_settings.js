document.addEventListener('DOMContentLoaded', function () {
    let mode_select_arrow = document.getElementById('mode-select-arrow');
    let model_select_arrow = document.getElementById('model-select-arrow');
    let model_select = document.getElementById('model_select');
    let mode_select = document.getElementById('mode_select');

    
    /**
     * selectElement
     *
     * @param {HTMLSelectElement} selectElement is HTMLSelectElement 
     */
    function showPicker(selectElement) { 
        if (selectElement.showPicker && typeof selectElement.showPicker === 'function') {
            selectElement.showPicker();
        } else { 
            console.warn('showPicker is not supported in this browser.');
            selectElement.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
    }

    mode_select_arrow.addEventListener('click', function () {
        showPicker(mode_select);
    });

    model_select_arrow.addEventListener('click', function () {
        showPicker(model_select);
    });
});