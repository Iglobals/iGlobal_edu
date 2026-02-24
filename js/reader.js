// Mock content for books
const bookContent = {
    1: {
        title: "Scientific Inquiries",
        pages: [
            "<h2>Chapter 1: The Nature of Science</h2><p>Science is a systematic enterprise that builds and organizes knowledge in the form of testable explanations and predictions about the universe.</p><p>In this chapter, we explore the fundamental methods of scientific inquiry, starting with observation and hypothesis formulation. The scientific method is not a rigid path but a cycle of discovery.</p><p>Key concepts include: <ul><li>Empirical Evidence</li><li>Reproducibility</li><li>Falsifiability</li></ul></p>",
            "<h2>Chapter 1: Continued</h2><p>Historically, the scientific method has evolved. From Aristotle's deductive reasoning to Bacon's inductive approach, the way we understand the world has shifted.</p><p>Modern science relies heavily on peer review and statistical analysis to validate claims. This ensures that personal bias is minimized and objective truth is approached.</p>",
            "<h2>Chapter 2: Physics Fundamentals</h2><p>Physics is the natural science that studies matter, its fundamental constituents, its motion and behavior through space and time, and the related entities of energy and force.</p><p>Newton's laws of motion form the bedrock of classical mechanics. Let's examine the first law: An object remains at rest or in uniform motion unless acted upon by a force.</p>"
        ]
    },
    default: {
        title: "Sample Book",
        pages: [
            "<h2>Introduction</h2><p>Welcome to the iGlobals Reader. usage experience.</p><p>This is a sample text to demonstrate the pagination and reading interface. Content is protected and cannot be copied or printed.</p>",
            "<h2>Chapter 1</h2><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>",
            "<h2>Conclusion</h2><p>Thank you for reading using our secure platform.</p>"
        ]
    }
};

let currentPage = 0;
let currentBookId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Get book ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentBookId = urlParams.get('id') || 1;

    // Load Book
    loadBook(currentBookId);
});

function loadBook(id) {
    const book = bookContent[id] || bookContent['default'];
    document.getElementById('bookTitle').textContent = book.title;

    // Reset page
    currentPage = 0;
    renderPage();
}

function renderPage() {
    const book = bookContent[currentBookId] || bookContent['default'];
    const totalPages = book.pages.length;

    // Validate Page Range
    if (currentPage < 0) currentPage = 0;
    if (currentPage >= totalPages) currentPage = totalPages - 1;

    // Initial Render
    const contentDiv = document.getElementById('pageContent');
    contentDiv.innerHTML = book.pages[currentPage];

    // Update Page Numbers
    document.getElementById('pageNumber').textContent = `Page ${currentPage + 1} of ${totalPages}`;
    const mobilePn = document.getElementById('mobilePageNumber');
    if (mobilePn) mobilePn.textContent = `${currentPage + 1} / ${totalPages}`;

    // Update Chapter Title (Simple extraction from H2 if exists, else generic)
    const h2 = contentDiv.querySelector('h2');
    const chapterTitle = h2 ? h2.textContent : `Section ${currentPage + 1}`;
    document.getElementById('chapterTitle').textContent = chapterTitle;

    // Button States
    document.getElementById('prevBtn').disabled = currentPage === 0;
    document.getElementById('prevBtn').style.opacity = currentPage === 0 ? '0.5' : '1';

    document.getElementById('nextBtn').disabled = currentPage === totalPages - 1;
    document.getElementById('nextBtn').style.opacity = currentPage === totalPages - 1 ? '0.5' : '1';
}

function changePage(delta) {
    currentPage += delta;
    renderPage();
}
