/* static/js/sources.js */

function handleEnter(e) { 
    if (e.key === 'Enter') { fetchResources(); } 
}

// 1. AUTO-SEARCH LOGIC
// Triggers when page loads with ?topic=Python
document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    const topic = urlParams.get('topic');
    
    if (topic) {
        // Pre-fill the search box
        const input = document.getElementById('topicInput');
        if (input) {
            input.value = topic;
            fetchResources(); // Run the search immediately
        }
    }
});

function fetchResources() {
    const topic = document.getElementById('topicInput').value;
    const btnText = document.getElementById('btnText');
    const btnIcon = document.getElementById('btnIcon');
    const spinner = document.getElementById('loadingSpinner');
    
    const initialState = document.getElementById('initialState');
    const skeletonLoader = document.getElementById('skeletonLoader');
    const resultsGrid = document.getElementById('resultsGrid');

    if (!topic) { alert("Please enter a topic first."); return; }

    // UI: Loading State
    if(btnText) btnText.textContent = "AI Generating...";
    if(btnIcon) btnIcon.classList.add('hidden');
    if(spinner) spinner.classList.remove('hidden');
    
    if(initialState) initialState.classList.add('hidden');
    if(resultsGrid) resultsGrid.classList.add('hidden');
    if(skeletonLoader) skeletonLoader.classList.remove('hidden');

    // ✅ FIX: Get URL from the hidden input in your sources.html
    const apiInput = document.getElementById('sourcesApiUrl');
    const apiUrl = apiInput ? apiInput.value : '/sources/api/'; // Fallback

    fetch(`${apiUrl}?topic=${encodeURIComponent(topic)}`)
        .then(response => {
            if (!response.ok) { throw new Error(`Server Error: ${response.status}`); }
            return response.json();
        })
        .then(response => {
            if (response.status === 'success') {
                renderResources(response.data);
                if(skeletonLoader) skeletonLoader.classList.add('hidden');
                if(resultsGrid) resultsGrid.classList.remove('hidden');
            } else {
                alert("Error: " + response.message);
                if(skeletonLoader) skeletonLoader.classList.add('hidden');
                if(initialState) initialState.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Something went wrong with the AI service.");
            if(skeletonLoader) skeletonLoader.classList.add('hidden');
            if(initialState) initialState.classList.remove('hidden');
        })
        .finally(() => {
            if(btnText) btnText.textContent = "Generate Path";
            if(btnIcon) btnIcon.classList.remove('hidden');
            if(spinner) spinner.classList.add('hidden');
        });
}

function renderResources(data) {
    const videoList = document.getElementById('videoList');
    const bookList = document.getElementById('bookList');
    const webList = document.getElementById('webList');

    // Helper to make cards
    const createCard = (title, subtitle, link, iconClass) => `
        <a href="${link}" target="_blank" class="block group h-full">
            <div class="p-4 rounded-xl border border-gray-200 bg-white hover:border-blue-300 hover:shadow-md transition duration-200 flex gap-4 items-start h-full">
                <div class="mt-1 text-gray-300 group-hover:text-blue-500 transition-colors shrink-0">
                    <i class="${iconClass} text-lg"></i>
                </div>
                <div>
                    <h4 class="font-bold text-gray-800 text-sm leading-tight group-hover:text-blue-600 transition line-clamp-2">${title}</h4>
                    <p class="text-xs text-gray-500 mt-1 font-medium line-clamp-1">${subtitle}</p>
                </div>
            </div>
        </a>
    `;

    // Clear and Populate
    if(videoList) {
        videoList.innerHTML = '';
        if (data.videos) videoList.innerHTML = data.videos.map(v => createCard(v.title, `Channel: ${v.channel || 'YouTube'}`, v.link || `https://www.youtube.com/results?search_query=${encodeURIComponent(v.title)}`, 'fa-brands fa-youtube')).join('');
    }

    if(bookList) {
        bookList.innerHTML = '';
        if (data.books) bookList.innerHTML = data.books.map(b => createCard(b.title, `Author: ${b.author || 'Unknown'}`, b.link || `https://www.google.com/search?tbm=bks&q=${encodeURIComponent(b.title)}`, 'fa-solid fa-book')).join('');
    }

    if(webList) {
        webList.innerHTML = '';
        if (data.websites) webList.innerHTML = data.websites.map(w => createCard(w.title || w.name, 'Official Resource', w.link || w.url, 'fa-solid fa-globe')).join('');
    }
}