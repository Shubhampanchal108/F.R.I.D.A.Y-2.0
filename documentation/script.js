/* ==========================================================================
   ⚡ F.R.I.D.A.Y 2.0 - ENTERPRISE DOCUMENTATION PORTAL SCRIPT
   Features: Dual Light/Dark Theme Switcher, Real-time Search Engine,
   Category Filters, Copy-to-Clipboard, ScrollSpy, Command Simulator
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initSearchEngine();
    initToolFilters();
    initCopyButtons();
    initScrollSpy();
    initMobileMenu();
    initCommandSimulator();
    initKeyboardShortcuts();
});

/* --------------------------------------------------------------------------
   1. Light / Dark Theme Switcher
   -------------------------------------------------------------------------- */
function initThemeToggle() {
    const themeBtn = document.getElementById('themeToggle');
    const root = document.documentElement;

    // Check localStorage or system preference
    const savedTheme = localStorage.getItem('friday_doc_theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    let currentTheme = savedTheme ? savedTheme : (systemPrefersDark ? 'dark' : 'light');
    applyTheme(currentTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            currentTheme = (currentTheme === 'dark') ? 'light' : 'dark';
            applyTheme(currentTheme);
            localStorage.setItem('friday_doc_theme', currentTheme);
        });
    }

    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        if (themeBtn) {
            themeBtn.innerHTML = theme === 'dark' 
                ? '<i class="fa-solid fa-sun" style="color: var(--accent-amber);"></i>' 
                : '<i class="fa-solid fa-moon"></i>';
            themeBtn.setAttribute('title', `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`);
        }
    }
}

/* --------------------------------------------------------------------------
   2. Real-Time Global Search Engine
   -------------------------------------------------------------------------- */
function initSearchEngine() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        // Filter Tool Cards
        const toolCards = document.querySelectorAll('.tool-card');
        let visibleTools = 0;

        toolCards.forEach(card => {
            const title = card.querySelector('.tool-card-title')?.textContent.toLowerCase() || '';
            const desc = card.querySelector('.feature-desc')?.textContent.toLowerCase() || '';
            const usecase = card.querySelector('.tool-usecase-box')?.textContent.toLowerCase() || '';
            const example = card.querySelector('.tool-example-box')?.textContent.toLowerCase() || '';

            const isMatch = title.includes(query) || desc.includes(query) || usecase.includes(query) || example.includes(query);

            if (isMatch || query === '') {
                card.style.display = 'flex';
                visibleTools++;
            } else {
                card.style.display = 'none';
            }
        });

        // Filter Table Rows
        const tableRows = document.querySelectorAll('.custom-table tbody tr');
        tableRows.forEach(row => {
            const rowText = row.textContent.toLowerCase();
            if (rowText.includes(query) || query === '') {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });

        // Filter Sections
        const docSections = document.querySelectorAll('.doc-section');
        docSections.forEach(section => {
            if (query === '') {
                section.style.display = 'block';
                return;
            }

            const sectionText = section.textContent.toLowerCase();
            if (sectionText.includes(query)) {
                section.style.display = 'block';
            } else {
                const toolsInSection = section.querySelectorAll('.tool-card');
                if (toolsInSection.length > 0 && visibleTools > 0) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            }
        });
    });
}

/* --------------------------------------------------------------------------
   3. Category Filter Tabs for Tools
   -------------------------------------------------------------------------- */
function initToolFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    const toolCards = document.querySelectorAll('.tool-card');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filterCategory = btn.getAttribute('data-category');

            toolCards.forEach(card => {
                const cardCategory = card.getAttribute('data-category');
                if (filterCategory === 'all' || cardCategory === filterCategory) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });

            const searchInput = document.getElementById('globalSearch');
            if (searchInput && searchInput.value !== '') {
                searchInput.value = '';
            }
        });
    });
}

/* --------------------------------------------------------------------------
   4. Copy to Clipboard with Toast Notification
   -------------------------------------------------------------------------- */
function initCopyButtons() {
    document.body.addEventListener('click', (e) => {
        const copyBtn = e.target.closest('.code-copy-btn') || e.target.closest('.tool-copy-icon') || e.target.closest('.copyable-cmd');
        if (!copyBtn) return;

        let textToCopy = '';

        if (copyBtn.getAttribute('data-copy')) {
            textToCopy = copyBtn.getAttribute('data-copy');
        } else if (copyBtn.classList.contains('code-copy-btn')) {
            const pre = copyBtn.closest('.code-block-wrapper').querySelector('pre');
            textToCopy = pre ? pre.textContent.trim() : '';
        } else if (copyBtn.classList.contains('tool-copy-icon')) {
            const exampleBox = copyBtn.closest('.tool-example-box');
            textToCopy = exampleBox ? exampleBox.querySelector('span').textContent.trim() : '';
        } else {
            textToCopy = copyBtn.textContent.trim();
        }

        if (textToCopy) {
            navigator.clipboard.writeText(textToCopy).then(() => {
                showToast(`Copied to clipboard: "${textToCopy}" ⚡`);
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        }
    });
}

function showToast(message) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span>⚡</span> <span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* --------------------------------------------------------------------------
   5. ScrollSpy Active Sidebar Highlight
   -------------------------------------------------------------------------- */
function initScrollSpy() {
    const sections = document.querySelectorAll('.doc-section');
    const navLinks = document.querySelectorAll('.sidebar-link');

    window.addEventListener('scroll', () => {
        let currentSectionId = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            const sectionHeight = section.offsetHeight;

            if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
                currentSectionId = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSectionId}`) {
                link.classList.add('active');
            }
        });
    });
}

/* --------------------------------------------------------------------------
   6. Mobile Menu Toggle
   -------------------------------------------------------------------------- */
function initMobileMenu() {
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    function toggleMenu() {
        if (sidebar) sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    }

    function closeMenu() {
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
    }

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', toggleMenu);

        if (closeBtn) {
            closeBtn.addEventListener('click', closeMenu);
        }

        if (overlay) {
            overlay.addEventListener('click', closeMenu);
        }

        document.querySelectorAll('.sidebar-link').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
    }
}

/* --------------------------------------------------------------------------
   7. Keyboard Shortcuts (Ctrl+K)
   -------------------------------------------------------------------------- */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('globalSearch');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
}

/* --------------------------------------------------------------------------
   8. Interactive F.R.I.D.A.Y Command Simulator
   -------------------------------------------------------------------------- */
function initCommandSimulator() {
    const simInput = document.getElementById('simInput');
    const simBtn = document.getElementById('simRunBtn');
    const simOutput = document.getElementById('simOutput');

    if (!simBtn || !simInput || !simOutput) return;

    const sampleResponses = {
        "/status": `[F.R.I.D.A.Y HUD SYSTEM STATUS]\n• CPU Usage: 14.2% | Battery: 94% (Charging)\n• Active Daemon Watchdog: ONLINE (Thread-3)\n• Vector RAG Memory: 1,248 ChromaDB Embeddings Loaded\n• Access Control Guard: ALL SYSTEMS OPTIMAL`,
        "/briefing": `🌅 Morning Briefing Generated!\n"Good Morning Boss. The current weather in Delhi is 28°C with clear skies. Battery is at 94%. You have 2 pending reminders: 'Submit project report' at 4:00 PM and 'Team Sync' at 6:00 PM."`,
        "/reminders": `⏰ Active Reminders:\n1. [DUE TODAY] Submit project report (4:00 PM)\n2. [UPCOMING] Team Sync meeting (6:00 PM)\n3. [RECURRING] Daily morning briefing (8:00 AM)`,
        "analyze my screen and explain the code": `📸 [JARVIS Vision Active] Taking desktop screenshot...\n"Boss, I can see VS Code open with 'Vision.py'. The code is using PIL ImageGrab to capture the screen and pass it to Gemini Vision LLM. There are no syntax errors visible."`,
        "run python code to calculate 10th fibonacci number": `🐍 [Python Sandbox Execution]\nExecuted snippet in 0.04s:\nResult: 55`,
        "deep research on quantum computing trends 2026": `🤖 [Deep Researcher Sub-Agent]\nSynthesizing multi-query web search & dynamic scraping...\n• Found 14 sources.\n• Topic: Quantum Supremacy & Commercial QPU Scaling in 2026.\nReport saved to memory!`
    };

    function runSim() {
        const query = simInput.value.trim().toLowerCase();
        if (!query) return;

        simOutput.innerHTML = `<span style="color: var(--accent-primary);">⚡ Processing intent with Brain engine...</span>`;

        setTimeout(() => {
            let matchedKey = Object.keys(sampleResponses).find(k => query.includes(k.toLowerCase()));
            if (matchedKey) {
                simOutput.textContent = sampleResponses[matchedKey];
            } else {
                simOutput.textContent = `🤖 F.R.I.D.A.Y Response:\n"Boss, I understood: '${query}'. Tool guard identified relevant capability and executed action safely!"`;
            }
        }, 500);
    }

    simBtn.addEventListener('click', runSim);
    simInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runSim();
    });
}
