const books = [
    {
        id: 1,
        title: "Scientific Inquiries",
        category: "Science",
        author: "Dr. A. B. Smith",
        price: "$25.00",
        coverColor: "bg-blue-100", // Tailwind class for mock cover
        icon: "flask-conical"
    },
    {
        id: 2,
        title: "Business Analytics",
        category: "Commercial",
        author: "Prof. J. Doe",
        price: "$30.00",
        coverColor: "bg-green-100",
        icon: "briefcase"
    },
    {
        id: 3,
        title: "Creative Strategies",
        category: "Arts",
        author: "L. M. Artists",
        price: "$20.00",
        coverColor: "bg-yellow-100",
        icon: "palette"
    },
    {
        id: 4,
        title: "JUPEB Mathematics",
        category: "Science",
        author: "Math & Co.",
        price: "$35.00",
        coverColor: "bg-red-100",
        icon: "calculator"
    },
    {
        id: 5,
        title: "Literature in English",
        category: "Arts",
        author: "Shakespeare's Fan",
        price: "$22.00",
        coverColor: "bg-purple-100",
        icon: "feather"
    },
    {
        id: 6,
        title: "Economics Principles",
        category: "Commercial",
        author: "Econ Experts",
        price: "$28.00",
        coverColor: "bg-indigo-100",
        icon: "trending-up"
    }
];

document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('bookGrid');
    if (grid) {
        renderBooks(books);
    }
});

function renderBooks(bookList) {
    const grid = document.getElementById('bookGrid');
    grid.innerHTML = bookList.map(book => `
        <div class="book-card bg-white rounded-lg overflow-hidden shadow-md group border border-gray-100">
            <div class="relative h-64 overflow-hidden ${book.coverColor} group-hover:bg-[#6B2D5C]/10 transition-colors flex items-center justify-center">
                <i data-lucide="${book.icon}" class="w-16 h-16 text-[#6B2D5C] opacity-50"></i>
                <div class="book-overlay">
                    <button onclick="window.location.href='reader.html?id=${book.id}'" class="btn-primary px-6 py-2 rounded text-sm mb-2 w-32">Read Now</button>
                </div>
            </div>
            <div class="p-6">
                <span class="text-[#6B2D5C] text-[10px] font-bold uppercase tracking-wider border border-[#6B2D5C] px-2 py-1 rounded-full">${book.category}</span>
                <h3 class="font-bold text-lg text-gray-900 mt-4 mb-2 truncate">${book.title}</h3>
                <p class="text-gray-500 text-xs mb-4">By ${book.author}</p>
                <div class="flex justify-between items-center border-t border-gray-100 pt-4">
                    <span class="text-gray-900 font-bold text-sm">${book.price}</span>
                    <div class="flex text-yellow-400 text-xs gap-1">
                        <i data-lucide="star" class="w-3 h-3 fill-current"></i>
                        <i data-lucide="star" class="w-3 h-3 fill-current"></i>
                        <i data-lucide="star" class="w-3 h-3 fill-current"></i>
                        <i data-lucide="star" class="w-3 h-3 fill-current"></i>
                        <i data-lucide="star" class="w-3 h-3 fill-current"></i>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    // Re-initialize icons for new elements
    lucide.createIcons();
}
