// Digital Library JavaScript Functions

// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Add fade-in animation to cards
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});

// Search functionality
function handleSearch(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const searchForm = document.querySelector('form');
        if (searchForm) {
            searchForm.submit();
        }
    }
}

// Add search event listeners
document.addEventListener('DOMContentLoaded', function() {
    const searchInputs = document.querySelectorAll('input[name="q"]');
    searchInputs.forEach(input => {
        input.addEventListener('keypress', handleSearch);
    });
});

// Loading states for buttons
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading me-2"></span>Đang xử lý...';
    button.disabled = true;
    
    // Store original text to restore later
    button.setAttribute('data-original-text', originalText);
}

function hideLoading(button) {
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        button.innerHTML = originalText;
        button.disabled = false;
        button.removeAttribute('data-original-text');
    }
}

// Add loading states to forms
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.hasAttribute('data-no-loading')) {
                showLoading(submitButton);
            }
        });
    });
});

// Confirm dialogs for dangerous actions
function confirmDelete(message = 'Bạn có chắc muốn xóa?') {
    return confirm(message);
}

// Add confirm dialogs to delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('a[href*="/delete/"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirmDelete('Bạn có chắc muốn xóa? Hành động này không thể hoàn tác.')) {
                event.preventDefault();
            }
        });
    });
});

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const alertInstance = new bootstrap.Alert(alert);
            if (alertInstance) {
                alertInstance.close();
            }
        }, 5000);
    });
});

// Image preview for file uploads
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (previewElement) {
                previewElement.src = e.target.result;
                previewElement.style.display = 'block';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Add image preview functionality
document.addEventListener('DOMContentLoaded', function() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            const previewId = this.getAttribute('data-preview');
            if (previewId) {
                const previewElement = document.getElementById(previewId);
                previewImage(this, previewElement);
            }
        });
    });
});

// Dark mode toggle (if implemented)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Load dark mode preference
document.addEventListener('DOMContentLoaded', function() {
    const darkMode = localStorage.getItem('darkMode');
    if (darkMode === 'true') {
        document.body.classList.add('dark-mode');
    }
    
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
});

// Table sorting functionality
function sortTable(table, column, type = 'string') {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const sortedRows = rows.sort((a, b) => {
        const aValue = a.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        const bValue = b.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        
        if (type === 'number') {
            return parseFloat(aValue) - parseFloat(bValue);
        } else if (type === 'date') {
            return new Date(aValue) - new Date(bValue);
        } else {
            return aValue.localeCompare(bValue);
        }
    });
    
    // Clear tbody and append sorted rows
    tbody.innerHTML = '';
    sortedRows.forEach(row => tbody.appendChild(row));
}

// Add table sorting to sortable tables
document.addEventListener('DOMContentLoaded', function() {
    const sortableTables = document.querySelectorAll('.table-sortable');
    sortableTables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort ms-1"></i>';
            
            header.addEventListener('click', function() {
                const sortType = this.getAttribute('data-sort-type') || 'string';
                sortTable(table, index, sortType);
            });
        });
    });
});

// Copy to clipboard functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show toast or alert
        const toast = document.createElement('div');
        toast.className = 'alert alert-success position-fixed top-0 end-0 m-3';
        toast.innerHTML = 'Đã sao chép vào clipboard!';
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    });
}

// Add copy functionality to copyable elements
document.addEventListener('DOMContentLoaded', function() {
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            copyToClipboard(textToCopy);
        });
    });
});

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

// Add client-side form validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Email validation
            const emailInputs = form.querySelectorAll('input[type="email"]');
            emailInputs.forEach(input => {
                if (!validateEmail(input.value)) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            // Password validation
            const passwordInputs = form.querySelectorAll('input[type="password"]');
            passwordInputs.forEach(input => {
                if (!validatePassword(input.value)) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            // Password confirmation
            const confirmPassword = form.querySelector('input[name="confirm_password"]');
            const password = form.querySelector('input[name="password"]');
            if (confirmPassword && password && confirmPassword.value !== password.value) {
                confirmPassword.classList.add('is-invalid');
                isValid = false;
            } else if (confirmPassword) {
                confirmPassword.classList.remove('is-invalid');
            }
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
});

// Lazy loading for images
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
});

// MongoDB connection test
async function testMongoConnection() {
    try {
        const response = await fetch('/api/test-connection');
        const data = await response.json();
        
        const resultDiv = document.getElementById('connection-result');
        if (resultDiv) {
            if (data.status === 'success') {
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        ${data.message}
                        <br><small>Database: ${data.database}</small>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-times-circle me-2"></i>
                        ${data.message}
                    </div>
                `;
            }
        }
    } catch (error) {
        const resultDiv = document.getElementById('connection-result');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle me-2"></i>
                    Lỗi kết nối: ${error.message}
                </div>
            `;
        }
    }
}

// Export functions for global use
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.confirmDelete = confirmDelete;
window.toggleDarkMode = toggleDarkMode;
window.copyToClipboard = copyToClipboard;
window.testMongoConnection = testMongoConnection;