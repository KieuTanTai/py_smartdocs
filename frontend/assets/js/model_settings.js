document.addEventListener('DOMContentLoaded', function () {
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
});