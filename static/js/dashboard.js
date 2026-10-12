// SmileCare Clinic - Dashboard JavaScript

// ============================================
// SESSION MANAGEMENT
// ============================================
class SessionManager {
    constructor() {
        this.timeLeft = 300; // 5 minutes in seconds
        this.timerElement = document.getElementById('sessionTimer');
        this.timerInterval = null;
        this.startTimer();
    }
    
    startTimer() {
        if (!this.timerElement) return;
        
        this.timerInterval = setInterval(() => {
            this.timeLeft--;
            if (this.timeLeft <= 0) {
                this.logout();
            }
            this.updateDisplay();
        }, 1000);
    }
    
    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        this.timerElement.textContent = 
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    
    logout() {
        clearInterval(this.timerInterval);
        window.location.href = '/logout';
    }
    
    reset() {
        this.timeLeft = 300;
        this.updateDisplay();
    }
}

// ============================================
// NOTIFICATION SYSTEM
// ============================================
class NotificationSystem {
    constructor() {
        this.container = document.getElementById('notificationContainer') || this.createContainer();
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            width: 100%;
        `;
        document.body.appendChild(container);
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const types = {
            success: 'bg-success text-white',
            danger: 'bg-danger text-white',
            warning: 'bg-warning',
            info: 'bg-primary text-white'
        };
        
        const alert = document.createElement('div');
        alert.className = `alert ${types[type] || types.info} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        this.container.appendChild(alert);
        
        // Auto-dismiss
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 300);
            }
        }, duration);
    }
}

// ============================================
// CHART UTILITY
// ============================================
class ChartUtility {
    constructor() {
        this.charts = {};
    }
    
    createLineChart(ctx, config) {
        return new Chart(ctx, {
            type: 'line',
            data: config.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: config.legend !== false,
                        position: 'bottom'
                    }
                },
                ...config.options
            }
        });
    }
    
    createBarChart(ctx, config) {
        return new Chart(ctx, {
            type: 'bar',
            data: config.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: config.legend !== false,
                        position: 'bottom'
                    }
                },
                ...config.options
            }
        });
    }
    
    createPieChart(ctx, config) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: config.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                ...config.options
            }
        });
    }
    
    updateChart(chartId, data) {
        if (this.charts[chartId]) {
            this.charts[chartId].data = data;
            this.charts[chartId].update();
        }
    }
}

// ============================================
// FORM VALIDATION
// ============================================
class FormValidator {
    static validateEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(email);
    }
    
    static validatePhone(phone) {
        const pattern = /^[0-9]{10}$/;
        return pattern.test(phone);
    }
    
    static validateAadhaar(aadhaar) {
        const pattern = /^[0-9]{12}$/;
        return pattern.test(aadhaar);
    }
    
    static validatePassword(password) {
        if (password.length < 8) {
            return { valid: false, message: 'Password must be at least 8 characters' };
        }
        if (!/[A-Z]/.test(password)) {
            return { valid: false, message: 'Password must contain at least one uppercase letter' };
        }
        if (!/[a-z]/.test(password)) {
            return { valid: false, message: 'Password must contain at least one lowercase letter' };
        }
        if (!/[0-9]/.test(password)) {
            return { valid: false, message: 'Password must contain at least one number' };
        }
        return { valid: true, message: 'Password is valid' };
    }
}

// ============================================
// DATA TABLE UTILITY
// ============================================
class DataTable {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.options = {
            searchable: options.searchable || false,
            sortable: options.sortable || false,
            pagination: options.pagination || false,
            pageSize: options.pageSize || 10,
            ...options
        };
        
        if (this.options.searchable) {
            this.addSearch();
        }
        if (this.options.sortable) {
            this.addSorting();
        }
        if (this.options.pagination) {
            this.addPagination();
        }
    }
    
    addSearch() {
        const searchHtml = `
            <div class="row mb-3">
                <div class="col-md-4">
                    <input type="text" class="form-control" id="tableSearch" placeholder="Search...">
                </div>
            </div>
        `;
        this.table.parentNode.insertAdjacentHTML('beforebegin', searchHtml);
        
        document.getElementById('tableSearch').addEventListener('keyup', (e) => {
            this.filter(e.target.value);
        });
    }
    
    filter(query) {
        const rows = this.table.querySelectorAll('tbody tr');
        query = query.toLowerCase();
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    }
    
    addSorting() {
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sort(index);
            });
        });
    }
    
    sort(columnIndex) {
        const tbody = this.table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isAscending = this._sortAscending || false;
        
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent.trim();
            const bVal = b.cells[columnIndex].textContent.trim();
            
            if (!isNaN(aVal) && !isNaN(bVal)) {
                return (parseFloat(aVal) - parseFloat(bVal)) * (isAscending ? 1 : -1);
            }
            return (aVal > bVal ? 1 : -1) * (isAscending ? 1 : -1);
        });
        
        this._sortAscending = !isAscending;
        rows.forEach(row => tbody.appendChild(row));
    }
    
    addPagination() {
        // Pagination implementation
        const rows = this.table.querySelectorAll('tbody tr');
        const totalPages = Math.ceil(rows.length / this.options.pageSize);
        let currentPage = 1;
        
        const paginationHtml = `
            <div class="d-flex justify-content-between align-items-center mt-3">
                <span class="text-muted small">Showing ${this.options.pageSize} of ${rows.length} records</span>
                <nav>
                    <ul class="pagination pagination-sm mb-0" id="tablePagination">
                        <li class="page-item"><a class="page-link" href="#" data-page="prev">Previous</a></li>
                        ${this._generatePageButtons(totalPages)}
                        <li class="page-item"><a class="page-link" href="#" data-page="next">Next</a></li>
                    </ul>
                </nav>
            </div>
        `;
        
        this.table.parentNode.insertAdjacentHTML('afterend', paginationHtml);
        this._showPage(1);
        
        document.getElementById('tablePagination').addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.dataset.page;
            if (page === 'prev' && currentPage > 1) {
                currentPage--;
            } else if (page === 'next' && currentPage < totalPages) {
                currentPage++;
            } else if (!isNaN(page)) {
                currentPage = parseInt(page);
            }
            this._showPage(currentPage);
        });
    }
    
    _generatePageButtons(totalPages) {
        let html = '';
        for (let i = 1; i <= totalPages; i++) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        return html;
    }
    
    _showPage(page) {
        const rows = this.table.querySelectorAll('tbody tr');
        const start = (page - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        
        rows.forEach((row, index) => {
            row.style.display = (index >= start && index < end) ? '' : 'none';
        });
    }
}

// ============================================
// EXPORT UTILITY
// ============================================
class ExportUtility {
    static exportCSV(tableId, filename = 'report.csv') {
        const table = document.getElementById(tableId);
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        for (let row of rows) {
            const cols = row.querySelectorAll('td, th');
            const rowData = [];
            for (let col of cols) {
                rowData.push(col.textContent.trim());
            }
            csv.push(rowData.join(','));
        }
        
        const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    static exportJSON(data, filename = 'report.json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    static exportPDF(elementId, filename = 'report.pdf') {
        // Requires html2pdf library
        if (typeof html2pdf !== 'undefined') {
            const element = document.getElementById(elementId);
            html2pdf().from(element).save(filename);
        } else {
            console.warn('html2pdf library not loaded');
            alert('PDF export requires html2pdf library. Use CSV export instead.');
        }
    }
}

// ============================================
// API HELPER
// ============================================
class APIHelper {
    static async get(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API GET error:', error);
            throw error;
        }
    }
    
    static async post(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API POST error:', error);
            throw error;
        }
    }
    
    static async put(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API PUT error:', error);
            throw error;
        }
    }
    
    static async delete(endpoint) {
        try {
            const response = await fetch(endpoint, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API DELETE error:', error);
            throw error;
        }
    }
}

// ============================================
// DASHBOARD INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Session Manager
    const session = new SessionManager();
    
    // Initialize Notification System
    const notifications = new NotificationSystem();
    window.notifications = notifications;
    
    // Initialize Chart Utility
    const charts = new ChartUtility();
    window.charts = charts;
    
    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(el => {
            const bsAlert = new bootstrap.Alert(el);
            bsAlert.close();
        });
    }, 5000);
    
    console.log('SmileCare Clinic Dashboard initialized');
});