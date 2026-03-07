/**
 * LitLum Web Interface Scripts
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

// Copy publication info as markdown to clipboard
function copyPublicationInfo(button) {
    var title = button.getAttribute('data-title');
    var summary = button.getAttribute('data-summary');
    var url = button.getAttribute('data-url');

    var markdown = '**' + title + '**\n\n' + summary;
    if (url) {
        markdown += '\n\n' + url;
    }

    // Use textarea fallback for maximum compatibility
    var textarea = document.createElement('textarea');
    textarea.value = markdown;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);

    var originalText = button.textContent;
    button.textContent = 'Copied!';
    button.classList.add('copy-success');
    setTimeout(function() {
        button.textContent = originalText;
        button.classList.remove('copy-success');
    }, 1500);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Any initialization code can go here
    console.log('LitLum Web Interface initialized');
});
