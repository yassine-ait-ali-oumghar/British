// Interactive behavior for British Style website

// --- Custom Alert Modal Manager ---
function showCustomAlert(title, message, iconClass = 'bi-check-circle-fill') {
    const modalElement = document.getElementById('customAlertModal');
    if (!modalElement) {
        alert(`${title}\n${message}`);
        return;
    }

    const titleEl = document.getElementById('customAlertTitle');
    const msgEl = document.getElementById('customAlertMessage');
    const iconEl = document.getElementById('customAlertIcon');

    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message;
    if (iconEl) iconEl.className = `bi ${iconClass} fs-2`;

    if (typeof bootstrap !== 'undefined') {
        const bsModal = bootstrap.Modal.getOrCreateInstance(modalElement);
        bsModal.show();
    }
}

// --- Cart Manager ---
const CartManager = {
    STORAGE_KEY: 'british_style_cart_v1',
    SHIPPING_KEY: 'british_style_shipping_v1',
    PAYMENT_KEY: 'british_style_payment_v1',
    
    getCart() {
        try {
            return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || [];
        } catch (e) {
            return [];
        }
    },
    
    saveCart(cart) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateCartUI();
    },

    getShippingMethod() {
        return localStorage.getItem(this.SHIPPING_KEY) || 'delivery'; // 'delivery' or 'collect'
    },

    setShippingMethod(method) {
        localStorage.setItem(this.SHIPPING_KEY, method);
        // Fallback payment mode if incompatible
        const currentPayment = this.getPaymentMethod();
        if (method === 'delivery' && currentPayment === 'store') {
            localStorage.setItem(this.PAYMENT_KEY, 'cod');
        } else if (method === 'collect' && currentPayment === 'cod') {
            localStorage.setItem(this.PAYMENT_KEY, 'store');
        }
        this.updateCartUI();
    },

    getPaymentMethod() {
        const shipping = this.getShippingMethod();
        const stored = localStorage.getItem(this.PAYMENT_KEY);
        if (shipping === 'delivery') {
            if (stored === 'cod' || stored === 'card') return stored;
            return 'cod';
        } else {
            if (stored === 'store' || stored === 'card') return stored;
            return 'store';
        }
    },

    setPaymentMethod(method) {
        localStorage.setItem(this.PAYMENT_KEY, method);
        this.updateCartUI();
    },

    addItem(name, price, iconClass = 'bi-box-seam', spec = '', variant = '') {
        let cart = this.getCart();
        const numPrice = parseInt(price.replace(/[^0-9]/g, '')) || 0;
        
        const existingIndex = cart.findIndex(item => item.name === name && (item.variant || '') === (variant || ''));
        if (existingIndex > -1) {
            cart[existingIndex].quantity += 1;
        } else {
            cart.push({
                id: Date.now().toString() + '_' + Math.random().toString(36).substr(2, 4),
                name: name,
                priceText: price,
                unitPrice: numPrice,
                quantity: 1,
                iconClass: iconClass,
                spec: spec,
                variant: variant || ''
            });
        }

        this.saveCart(cart);

        // Open offcanvas drawer automatically when adding an item
        const offcanvasElement = document.getElementById('cartOffcanvas');
        if (offcanvasElement && typeof bootstrap !== 'undefined') {
            const bsOffcanvas = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement);
            bsOffcanvas.show();
        }
    },

    removeItem(id) {
        let cart = this.getCart().filter(item => item.id !== id);
        this.saveCart(cart);
    },

    updateQuantity(id, delta) {
        let cart = this.getCart();
        const item = cart.find(item => item.id === id);
        if (item) {
            item.quantity += delta;
            if (item.quantity <= 0) {
                cart = cart.filter(i => i.id !== id);
            }
        }
        this.saveCart(cart);
    },

    clearCart() {
        localStorage.removeItem(this.STORAGE_KEY);
        localStorage.removeItem(this.SHIPPING_KEY);
        localStorage.removeItem(this.PAYMENT_KEY);
        this.updateCartUI();
    },

    getSubtotal() {
        return this.getCart().reduce((sum, item) => sum + (item.unitPrice * item.quantity), 0);
    },

    getShippingFee() {
        const cart = this.getCart();
        if (cart.length === 0) return 0;
        return this.getShippingMethod() === 'delivery' ? 10 : 0;
    },

    getTotal() {
        const subtotal = this.getSubtotal();
        if (subtotal === 0) return 0;
        return subtotal + this.getShippingFee();
    },

    getTotalCount() {
        return this.getCart().reduce((count, item) => count + item.quantity, 0);
    },

    formatPhoneInput(el) {
        if (!el) return;
        // Strip out any non-digit character instantly (letters and symbols are blocked)
        let digits = el.value.replace(/[^0-9]/g, '');
        if (digits.length > 10) {
            digits = digits.slice(0, 10);
        }
        // Format as XX XX XX XX XX
        let formatted = '';
        for (let i = 0; i < digits.length; i++) {
            if (i > 0 && i % 2 === 0) {
                formatted += ' ';
            }
            formatted += digits[i];
        }
        el.value = formatted;
    },

    getPaymentDisplayText(method) {
        if (method === 'card') return '💳 Carte bancaire';
        if (method === 'store') return '🏪 Paiement au retrait';
        return '💵 Paiement à la livraison';
    },

    openCheckoutModal() {
        if (this.getCart().length === 0) return;

        // Restriction : si l'utilisateur n'est pas connecté, le rediriger vers la page de connexion
        if (window.IS_USER_AUTHENTICATED === false) {
            const loginUrl = window.LOGIN_URL || '/accounts/login/';
            window.location.href = loginUrl;
            return;
        }

        // Hide cart offcanvas first
        const offcanvasElement = document.getElementById('cartOffcanvas');
        if (offcanvasElement && typeof bootstrap !== 'undefined') {
            const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasElement);
            if (bsOffcanvas) bsOffcanvas.hide();
        }

        // Update Checkout Modal Values
        const count = this.getTotalCount();
        const subtotal = this.getSubtotal();
        const shippingFee = this.getShippingFee();
        const grandTotal = this.getTotal();
        const shippingMethod = this.getShippingMethod();
        const paymentMethod = this.getPaymentMethod();

        document.getElementById('modalItemCount').textContent = count;
        document.getElementById('modalSubtotal').textContent = subtotal + ' DH';
        document.getElementById('modalShippingLabel').textContent = shippingMethod === 'delivery' ? 'Livraison à domicile' : 'Click & Collect';
        document.getElementById('modalShippingFee').textContent = shippingFee > 0 ? '+' + shippingFee + ' DH' : 'Gratuit';
        
        const modalPaymentLabel = document.getElementById('modalPaymentLabel');
        if (modalPaymentLabel) {
            modalPaymentLabel.textContent = this.getPaymentDisplayText(paymentMethod);
        }

        document.getElementById('modalGrandTotal').textContent = grandTotal + ' DH';

        // Render mini items list in modal
        const itemsListContainer = document.getElementById('modalOrderItemsList');
        if (itemsListContainer) {
            let itemsHtml = '';
            this.getCart().forEach(item => {
                itemsHtml += `
                    <div class="d-flex justify-content-between align-items-center mb-1 text-dark small">
                        <div>
                            <strong>${item.name}</strong> (x${item.quantity})
                            ${item.variant ? `<span class="badge bg-light text-dark border ms-1 fw-normal" style="font-size: 0.72rem;"><i class="bi bi-palette text-gold me-1"></i>${item.variant}</span>` : ''}
                        </div>
                        <span class="fw-semibold">${item.unitPrice * item.quantity} DH</span>
                    </div>
                `;
            });
            itemsListContainer.innerHTML = itemsHtml;
        }

        // Toggle address input requirement
        const addrGroup = document.getElementById('addressInputGroup');
        const addrInput = document.getElementById('checkoutAddress');
        if (shippingMethod === 'collect') {
            if (addrGroup) addrGroup.classList.add('d-none');
            if (addrInput) addrInput.removeAttribute('required');
        } else {
            if (addrGroup) addrGroup.classList.remove('d-none');
            if (addrInput) addrInput.setAttribute('required', 'required');
        }

        // Open Modal
        const modalElement = document.getElementById('checkoutModal');
        if (modalElement && typeof bootstrap !== 'undefined') {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modalElement);
            bsModal.show();
        }
    },

    async processOrder(event) {
        event.preventDefault();
        const nameInput = document.getElementById('checkoutName');
        const phoneInput = document.getElementById('checkoutPhone');
        const addressInput = document.getElementById('checkoutAddress');

        const name = nameInput ? nameInput.value.trim() : '';
        const phone = phoneInput ? phoneInput.value.trim() : '';
        const address = addressInput ? addressInput.value.trim() : '';

        const shippingMethod = this.getShippingMethod();
        const paymentMethod = this.getPaymentMethod();
        const cart = this.getCart();

        // Mandatory 10-digit phone number validation
        const cleanPhone = phone.replace(/[^0-9]/g, '');
        if (cleanPhone.length !== 10) {
            showCustomAlert(
                "Numéro de Téléphone Invalide",
                "Le numéro de téléphone est obligatoire et doit comporter exactement 10 chiffres (ex: 06 12 34 56 78).",
                "bi-exclamation-triangle-fill"
            );
            if (phoneInput) phoneInput.focus();
            return;
        }

        if (cart.length === 0) {
            showCustomAlert("Panier Vide", "Votre panier est vide.", "bi-exclamation-triangle-fill");
            return;
        }

        // CSRF Token extraction
        let csrfToken = '';
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            csrfToken = csrfInput.value;
        } else {
            const match = document.cookie.match(/csrftoken=([^;]+)/);
            if (match) csrfToken = match[1];
        }

        const payload = {
            name: name,
            phone: phone,
            address: address,
            delivery_mode: shippingMethod,
            payment_mode: paymentMethod,
            cart: cart
        };

        try {
            const response = await fetch('/api/orders/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                const modalElement = document.getElementById('checkoutModal');
                if (modalElement && typeof bootstrap !== 'undefined') {
                    const bsModal = bootstrap.Modal.getInstance(modalElement) || bootstrap.Modal.getOrCreateInstance(modalElement);
                    if (bsModal) {
                        const onHidden = () => {
                            modalElement.removeEventListener('hidden.bs.modal', onHidden);
                            this.clearCart();
                            showCustomAlert(
                                "Commande Validée !",
                                data.message || `Merci ${name} ! Votre commande a bien été enregistrée avec succès. Notre équipe vous contactera sous peu.`,
                                "bi-bag-check-fill"
                            );
                        };
                        modalElement.addEventListener('hidden.bs.modal', onHidden);
                        bsModal.hide();
                        return;
                    }
                }
                this.clearCart();
                showCustomAlert("Commande Validée !", data.message, "bi-bag-check-fill");
            } else {
                showCustomAlert("Erreur de Commande", data.error || "Impossible d'enregistrer votre commande. Veuillez réessayer.", "bi-exclamation-triangle-fill");
            }
        } catch (err) {
            console.error("Order error:", err);
            showCustomAlert("Erreur Système", "Une erreur est survenue lors de la validation. Veuillez réessayer.", "bi-exclamation-triangle-fill");
        }
    },

    updateCartUI() {
        const cart = this.getCart();
        const totalCount = this.getTotalCount();
        const subtotal = this.getSubtotal();
        const shippingFee = this.getShippingFee();
        const grandTotal = this.getTotal();
        const shippingMethod = this.getShippingMethod();
        const paymentMethod = this.getPaymentMethod();

        // Update header badges
        const countBadges = document.querySelectorAll('.cart-count-badge');
        countBadges.forEach(badge => {
            badge.textContent = totalCount;
            if (totalCount > 0) {
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        });

        // Update Subtotal & Total Displays
        const subtotalDisplays = document.querySelectorAll('.cart-subtotal-display');
        subtotalDisplays.forEach(el => el.textContent = subtotal + ' DH');

        const shippingDisplays = document.querySelectorAll('.cart-shipping-display');
        shippingDisplays.forEach(el => {
            if (subtotal === 0) {
                el.textContent = '0 DH';
            } else {
                el.textContent = shippingFee > 0 ? '+' + shippingFee + ' DH' : 'Gratuit';
            }
        });

        const totalDisplays = document.querySelectorAll('.cart-total-display');
        totalDisplays.forEach(el => el.textContent = grandTotal + ' DH');

        // Update Shipping Option UI cards active state
        const deliveryCard = document.getElementById('shippingOptionDelivery');
        const collectCard = document.getElementById('shippingOptionCollect');

        if (deliveryCard && collectCard) {
            if (shippingMethod === 'delivery') {
                deliveryCard.classList.add('active');
                collectCard.classList.remove('active');
            } else {
                collectCard.classList.add('active');
                deliveryCard.classList.remove('active');
            }
        }

        // Dynamic Payment Methods visibility & active state
        const codCard = document.getElementById('paymentOptionCod');
        const cardCard = document.getElementById('paymentOptionCard');
        const storeCard = document.getElementById('paymentOptionStore');

        if (codCard && cardCard && storeCard) {
            if (shippingMethod === 'delivery') {
                codCard.classList.remove('d-none');
                storeCard.classList.add('d-none');
            } else {
                storeCard.classList.remove('d-none');
                codCard.classList.add('d-none');
            }

            codCard.classList.toggle('active', paymentMethod === 'cod');
            cardCard.classList.toggle('active', paymentMethod === 'card');
            storeCard.classList.toggle('active', paymentMethod === 'store');
        }

        // Dynamic Final Button Text & Icon
        const cartSubmitBtnText = document.getElementById('cartSubmitBtnText');
        const cartSubmitBtnIcon = document.getElementById('cartSubmitBtnIcon');
        const modalSubmitBtnText = document.getElementById('modalSubmitBtnText');
        const modalSubmitBtnIcon = document.getElementById('modalSubmitBtnIcon');

        let btnIconClass = 'bi-box-seam';
        let btnText = `📦 Commander — ${grandTotal} DH`;

        if (paymentMethod === 'card') {
            btnIconClass = 'bi-credit-card-fill';
            btnText = `💳 Payer ${grandTotal} DH`;
        } else if (paymentMethod === 'store') {
            btnIconClass = 'bi-check2-circle';
            btnText = `✓ Confirmer ma commande — ${grandTotal} DH`;
        } else {
            btnIconClass = 'bi-box-seam';
            btnText = `📦 Commander — ${grandTotal} DH`;
        }

        if (cartSubmitBtnText) cartSubmitBtnText.innerHTML = btnText;
        if (cartSubmitBtnIcon) cartSubmitBtnIcon.className = `bi ${btnIconClass} fs-5`;

        if (modalSubmitBtnText) modalSubmitBtnText.innerHTML = btnText;
        if (modalSubmitBtnIcon) modalSubmitBtnIcon.className = `bi ${btnIconClass} fs-5`;

        // Update Offcanvas Cart Items & Sections
        const cartContainer = document.getElementById('cartOffcanvasItems');
        const cartShippingSection = document.getElementById('cartShippingSection');
        const cartPaymentSection = document.getElementById('cartPaymentSection');
        const cartPriceBreakdown = document.getElementById('cartPriceBreakdown');
        const cartFooter = document.getElementById('cartOffcanvasFooter');
        const emptyState = document.getElementById('cartEmptyState');

        if (!cartContainer) return;

        if (cart.length === 0) {
            cartContainer.innerHTML = '';
            if (emptyState) emptyState.classList.remove('d-none');
            if (cartShippingSection) cartShippingSection.classList.add('d-none');
            if (cartPaymentSection) cartPaymentSection.classList.add('d-none');
            if (cartPriceBreakdown) cartPriceBreakdown.classList.add('d-none');
            if (cartFooter) cartFooter.classList.add('d-none');
        } else {
            if (emptyState) emptyState.classList.add('d-none');
            if (cartShippingSection) cartShippingSection.classList.remove('d-none');
            if (cartPaymentSection) cartPaymentSection.classList.remove('d-none');
            if (cartPriceBreakdown) cartPriceBreakdown.classList.remove('d-none');
            if (cartFooter) cartFooter.classList.remove('d-none');

            let html = '';
            cart.forEach(item => {
                const itemTotal = item.unitPrice * item.quantity;
                html += `
                    <div class="cart-drawer-item d-flex align-items-center justify-content-between p-3 mb-3 rounded-4 bg-white shadow-sm border border-light" style="min-width: 0; width: 100%;">
                        <div class="d-flex align-items-center gap-3" style="min-width: 0; flex: 1; overflow: hidden;">
                            <div class="cart-item-icon-box rounded-3 p-2 bg-light text-gold text-center" style="width: 44px; height: 44px; min-width: 44px; display: flex; align-items: center; justify-content: center; background: rgba(197, 160, 89, 0.12) !important; flex-shrink: 0;">
                                <i class="bi ${item.iconClass || 'bi-bag'} fs-4" style="color: #c5a059;"></i>
                            </div>
                            <div style="min-width: 0; flex: 1;">
                                <h6 class="fw-bold mb-1 text-dark text-truncate" style="font-size: 0.92rem;" title="${item.name}">${item.name}</h6>
                                ${item.variant ? `<div class="badge bg-light text-dark border me-1 fw-normal mb-1 text-truncate" style="max-width: 100%;"><i class="bi bi-palette me-1" style="color: #c5a059;"></i>Nuance: <strong class="text-dark">${item.variant}</strong></div>` : ''}
                                <div class="text-muted small" style="font-size: 0.78rem;">${item.unitPrice} DH / unité</div>
                            </div>
                        </div>
                        <div class="text-end" style="flex-shrink: 0; margin-left: 10px;">
                            <div class="fw-bold text-dark mb-2" style="font-size: 0.95rem; white-space: nowrap;">${itemTotal} DH</div>
                            <div class="d-flex align-items-center gap-1 justify-content-end">
                                <div class="btn-group btn-group-sm border rounded-3 overflow-hidden">
                                    <button class="btn btn-sm btn-light px-2 py-0" onclick="CartManager.updateQuantity('${item.id}', -1)">-</button>
                                    <span class="btn btn-sm btn-white px-2 py-0 disabled text-dark fw-bold">${item.quantity}</span>
                                    <button class="btn btn-sm btn-light px-2 py-0" onclick="CartManager.updateQuantity('${item.id}', 1)">+</button>
                                </div>
                                <button class="btn btn-sm text-danger p-0 ms-1" onclick="CartManager.removeItem('${item.id}')" title="Supprimer">
                                    <i class="bi bi-trash fs-6"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            cartContainer.innerHTML = html;
        }
    }
};

// Global shorthand function for buttons
function addToCart(name, price, iconClass) {
    CartManager.addItem(name, price, iconClass);
}

// --- Service Reservation Manager ---
function openReservationModal(serviceName, price) {
    const modalElement = document.getElementById('reservationModal');
    if (!modalElement) return;

    document.getElementById('resServiceName').textContent = serviceName;
    document.getElementById('resServicePrice').textContent = price;

    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('resDate');
    if (dateInput) {
        dateInput.min = today;
        if (!dateInput.value) dateInput.value = today;
    }

    if (typeof bootstrap !== 'undefined') {
        const bsModal = bootstrap.Modal.getOrCreateInstance(modalElement);
        bsModal.show();
    }
}

function processReservation(event) {
    event.preventDefault();
    const serviceName = document.getElementById('resServiceName').textContent;
    const teamMember = document.getElementById('resTeamMember').value;
    const date = document.getElementById('resDate').value;
    const time = document.getElementById('resTime').value;
    const clientName = document.getElementById('resClientName').value;

    const triggerAlert = () => {
        showCustomAlert(
            "Rendez-vous Réservé !",
            `Félicitations ${clientName} ! Votre rendez-vous pour "${serviceName}" a été réservé avec succès le ${date} à ${time} avec ${teamMember}. Notre équipe vous enverra une confirmation par SMS.`,
            "bi-calendar-check-fill"
        );
    };

    const modalElement = document.getElementById('reservationModal');
    if (modalElement && typeof bootstrap !== 'undefined') {
        const bsModal = bootstrap.Modal.getInstance(modalElement);
        if (bsModal) {
            modalElement.addEventListener('hidden.bs.modal', function handler() {
                modalElement.removeEventListener('hidden.bs.modal', handler);
                triggerAlert();
            });
            bsModal.hide();
            return;
        }
    }

    triggerAlert();
}

// --- Dynamic Team Rating Manager ---
const TeamRatingManager = {
    STORAGE_KEY: 'british_style_team_ratings_v2',

    DEFAULT_RATINGS: {
        "Arthur Pendelton": { totalSum: 49, count: 10 },
        "Dr. Eleanor Vance": { totalSum: 50, count: 10 },
        "Charlotte Rose": { totalSum: 48, count: 10 },
        "James Sterling": { totalSum: 49, count: 10 },
        "Victoria Hamilton": { totalSum: 50, count: 10 }
    },

    getRatings() {
        try {
            const stored = JSON.parse(localStorage.getItem(this.STORAGE_KEY));
            return stored && typeof stored === 'object' ? stored : { ...this.DEFAULT_RATINGS };
        } catch (e) {
            return { ...this.DEFAULT_RATINGS };
        }
    },

    saveRatings(ratings) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(ratings));
        this.updateTeamCardsUI();
    },

    getMemberStats(name) {
        const ratings = this.getRatings();
        if (!ratings[name]) {
            ratings[name] = { totalSum: 25, count: 5 };
        }
        const stats = ratings[name];
        const avg = (stats.totalSum / stats.count).toFixed(1);
        return {
            avg: parseFloat(avg),
            count: stats.count,
            formattedAvg: avg
        };
    },

    addRating(name, newScore) {
        const ratings = this.getRatings();
        if (!ratings[name]) {
            ratings[name] = { totalSum: 25, count: 5 };
        }
        ratings[name].totalSum += parseInt(newScore) || 5;
        ratings[name].count += 1;
        this.saveRatings(ratings);
        return this.getMemberStats(name);
    },

    updateTeamCardsUI() {
        const cards = document.querySelectorAll('.team-card-clickable');
        cards.forEach(card => {
            const name = card.getAttribute('data-name');
            if (!name) return;
            const stats = this.getMemberStats(name);
            
            card.setAttribute('data-rating-avg', stats.formattedAvg);
            card.setAttribute('data-rating-count', stats.count);

            const badge = card.querySelector('.rating-badge');
            if (badge) {
                badge.innerHTML = `<i class="bi bi-star-fill text-warning me-1"></i>${stats.formattedAvg} / 5 <span class="fw-normal ms-1 opacity-75">(${stats.count} avis)</span>`;
            }
        });
    }
};

let currentRatingScore = 5;

function setStarRating(score) {
    currentRatingScore = score;
    const starsContainer = document.getElementById('teamStarContainer');
    if (!starsContainer) return;

    const stars = starsContainer.querySelectorAll('.star-icon');
    stars.forEach((star, index) => {
        if (index < score) {
            star.classList.remove('bi-star', 'text-muted');
            star.classList.add('bi-star-fill', 'text-warning');
        } else {
            star.classList.remove('bi-star-fill', 'text-warning');
            star.classList.add('bi-star', 'text-muted');
        }
    });

    const scoreLabel = document.getElementById('ratingScoreLabel');
    if (scoreLabel) {
        scoreLabel.textContent = `${score} / 5 ⭐`;
    }
}

function openTeamZoomModal(name, role, bio, iconClass, initialRating = 5) {
    const modalElement = document.getElementById('teamZoomModal');
    if (!modalElement) return;

    document.getElementById('zoomMemberName').textContent = name;
    document.getElementById('zoomMemberRole').textContent = role;
    document.getElementById('zoomMemberBio').textContent = bio;
    
    const iconEl = document.getElementById('zoomMemberIcon');
    if (iconEl) {
        iconEl.className = `bi ${iconClass || 'bi-person-circle'} fs-1`;
    }

    const stats = TeamRatingManager.getMemberStats(name);
    const avgEl = document.getElementById('zoomAvgLabel');
    const countEl = document.getElementById('zoomCountLabel');
    if (avgEl) avgEl.textContent = `${stats.formattedAvg} / 5`;
    if (countEl) countEl.textContent = `${stats.count}`;

    setStarRating(initialRating);

    if (typeof bootstrap !== 'undefined') {
        const bsModal = bootstrap.Modal.getOrCreateInstance(modalElement);
        bsModal.show();
    }
}

function submitTeamRating(event) {
    event.preventDefault();
    const name = document.getElementById('zoomMemberName').textContent;
    
    const updatedStats = TeamRatingManager.addRating(name, currentRatingScore);

    const triggerAlert = () => {
        showCustomAlert(
            "Évaluation Enregistrée",
            `Merci ! Votre évaluation de ${currentRatingScore}/5 ⭐ pour ${name} a été enregistrée avec succès.\n\nNote moyenne générale : ${updatedStats.formattedAvg} / 5 ⭐ (${updatedStats.count} avis clients).`,
            "bi-star-fill"
        );
    };

    const modalElement = document.getElementById('teamZoomModal');
    if (modalElement && typeof bootstrap !== 'undefined') {
        const bsModal = bootstrap.Modal.getInstance(modalElement);
        if (bsModal) {
            modalElement.addEventListener('hidden.bs.modal', function handler() {
                modalElement.removeEventListener('hidden.bs.modal', handler);
                triggerAlert();
            });
            bsModal.hide();
            return;
        }
    }

    triggerAlert();
}

document.addEventListener('DOMContentLoaded', () => {
    const header = document.getElementById('main-header');
    
    // Clear cart when user logs out
    document.querySelectorAll('form').forEach((form) => {
        const action = form.getAttribute('action') || '';
        if (action.includes('logout')) {
            form.addEventListener('submit', () => {
                CartManager.clearCart();
            });
        }
    });

    // Header scroll background effect
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 40) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Auth Sliding Form Toggle Logic
    const authContainer = document.getElementById('authContainer');

    if (authContainer) {
        document.querySelectorAll('.register-btn, .register-link').forEach(element => {
            element.addEventListener('click', (e) => {
                e.preventDefault();
                authContainer.classList.add('active');
            });
        });

        document.querySelectorAll('.login-btn, .login-link').forEach(element => {
            element.addEventListener('click', (e) => {
                e.preventDefault();
                authContainer.classList.remove('active');
            });
        });
    }

    // Team Card Click Handler for Zoom Modal
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.team-card-clickable');
        if (card) {
            const name = card.getAttribute('data-name');
            const role = card.getAttribute('data-role');
            const bio = card.getAttribute('data-bio');
            const icon = card.getAttribute('data-icon');
            const rating = parseInt(card.getAttribute('data-rating')) || 5;
            openTeamZoomModal(name, role, bio, icon, rating);
        }
    });

    // Initialize Team Ratings & Cart UI
    TeamRatingManager.updateTeamCardsUI();
    CartManager.updateCartUI();
});
