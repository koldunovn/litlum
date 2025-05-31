/**
 * Publication Reader Web Interface Scripts
 */

// Toggle publication details visibility
function toggleDetails(pubId) {
    const detailsRow = document.getElementById(pubId);
    
    if (detailsRow) {
        // Get current display style
        const currentDisplay = detailsRow.style.display;
        
        // Toggle display
        if (currentDisplay === 'none' || currentDisplay === '') {
            detailsRow.style.display = 'table-row';
        } else {
            detailsRow.style.display = 'none';
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Any initialization code can go here
    console.log('Publication Reader Web Interface initialized');
});
