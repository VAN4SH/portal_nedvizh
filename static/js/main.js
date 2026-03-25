// Main JavaScript functionality
class RealEstatePortal {
    constructor() {
        this.init();
    }
    
    init() {
        this.initFilterForm();
        this.initMap();
        this.initFavoriteButtons();
        this.initImageUpload();
        this.initSearch();
        this.initMobileMenu();
    }
    
    initFilterForm() {
        const filterForm = document.getElementById('filterForm');
        if (filterForm) {
            // Dynamic city loading
            const citySelect = document.getElementById('city');
            if (citySelect && citySelect.children.length <= 1) {
                fetch('/api/cities')
                    .then(response => response.json())
                    .then(cities => {
                        cities.forEach(city => {
                            const option = document.createElement('option');
                            option.value = city;
                            option.textContent = city;
                            citySelect.appendChild(option);
                        });
                    });
            }
            
            // Price range slider
            const priceRange = document.getElementById('priceRange');
            const priceValue = document.getElementById('priceValue');
            
            if (priceRange && priceValue) {
                priceRange.addEventListener('input', function() {
                    const value = parseInt(this.value);
                    priceValue.textContent = this.formatPrice(value);
                    
                    // Update hidden inputs
                    document.getElementById('min_price').value = value * 0.5;
                    document.getElementById('max_price').value = value * 1.5;
                });
            }
            
            // Filter form submission with animation
            filterForm.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('pulse');
                    setTimeout(() => submitBtn.classList.remove('pulse'), 1000);
                }
            });
        }
    }
    
    initMap() {
        const mapElement = document.getElementById('propertyMap');
        if (mapElement && typeof google !== 'undefined') {
            const location = {
                lat: parseFloat(mapElement.dataset.lat),
                lng: parseFloat(mapElement.dataset.lng)
            };
            
            const map = new google.maps.Map(mapElement, {
                zoom: 15,
                center: location,
                styles: [
                    {
                        featureType: "all",
                        elementType: "geometry",
                        stylers: [{ color: "#f5f5f5" }]
                    }
                ]
            });
            
            new google.maps.Marker({
                position: location,
                map: map,
                title: mapElement.dataset.title
            });
        }
    }
    
    initFavoriteButtons() {
        document.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const listingId = this.dataset.listingId;
                const isFavorite = this.classList.contains('active');
                
                // Toggle visual state
                this.classList.toggle('active');
                this.classList.add('scale-in');
                
                // Remove animation class after animation completes
                setTimeout(() => {
                    this.classList.remove('scale-in');
                }, 300);
                
                // Send AJAX request to update favorites
                fetch('/api/favorite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        listing_id: listingId,
                        action: isFavorite ? 'remove' : 'add'
                    })
                });
            });
        });
    }
    
    initImageUpload() {
        const imageInput = document.getElementById('imageUpload');
        const imagePreview = document.getElementById('imagePreview');
        
        if (imageInput && imagePreview) {
            imageInput.addEventListener('change', function(e) {
                const files = Array.from(this.files);
                imagePreview.innerHTML = '';
                
                files.forEach((file, index) => {
                    if (file.type.match('image.*')) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const imgContainer = document.createElement('div');
                            imgContainer.className = 'col-md-3 mb-3';
                            imgContainer.innerHTML = `
                                <div class="image-preview-item">
                                    <img src="${e.target.result}" class="img-fluid rounded" alt="Preview">
                                    <button type="button" class="btn-close remove-image" data-index="${index}"></button>
                                </div>
                            `;
                            imagePreview.appendChild(imgContainer);
                            
                            // Add remove functionality
                            imgContainer.querySelector('.remove-image').addEventListener('click', function() {
                                imgContainer.remove();
                            });
                        };
                        reader.readAsDataURL(file);
                    }
                });
            });
        }
    }
    
    initSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        
        if (searchInput && searchResults) {
            let searchTimeout;
            
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                
                if (this.value.length < 2) {
                    searchResults.classList.add('d-none');
                    return;
                }
                
                searchTimeout = setTimeout(() => {
                    fetch(`/api/search?q=${encodeURIComponent(this.value)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.results && data.results.length > 0) {
                                searchResults.innerHTML = data.results.map(result => `
                                    <a href="/listing/${result.id}" class="dropdown-item">
                                        <div class="d-flex align-items-center">
                                            <img src="/static/images/properties/${result.image}" class="rounded me-3" width="40" height="40">
                                            <div>
                                                <h6 class="mb-0">${result.title}</h6>
                                                <small class="text-muted">${result.location}</small>
                                            </div>
                                            <span class="ms-auto text-primary">${this.formatPrice(result.price)}</span>
                                        </div>
                                    </a>
                                `).join('');
                                searchResults.classList.remove('d-none');
                            } else {
                                searchResults.innerHTML = '<div class="dropdown-item text-muted">Ничего не найдено</div>';
                                searchResults.classList.remove('d-none');
                            }
                        });
                }, 300);
            });
            
            // Hide results when clicking outside
            document.addEventListener('click', function(e) {
                if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                    searchResults.classList.add('d-none');
                }
            });
        }
    }
    
    initMobileMenu() {
        const menuToggle = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (menuToggle && navbarCollapse) {
            menuToggle.addEventListener('click', function() {
                navbarCollapse.classList.toggle('show');
            });
        }
    }
    
    formatPrice(price) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            maximumFractionDigits: 0
        }).format(price);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.realEstatePortal = new RealEstatePortal();
    
    // Add any additional initialization here
    console.log('Real Estate Portal initialized');
});
