// DOM Elements
const searchInput = document.getElementById('searchInput');
const autocompleteResults = document.getElementById('autocompleteResults');
const loading = document.getElementById('loading');
const fighterResults = document.getElementById('fighterResults');
const fighterList = document.getElementById('fighterList');
const fightHistory = document.getElementById('fightHistory');
const fightList = document.getElementById('fightList');
const fighterName = document.getElementById('fighterName');
const errorMessage = document.getElementById('errorMessage');
const backBtn = document.getElementById('backBtn');

let currentFighters = [];
let searchTimeout = null;

// Event Listeners
searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    
    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // If query is too short, hide autocomplete
    if (query.length < 2) {
        hideAutocomplete();
        return;
    }
    
    // Debounce search - wait 300ms after user stops typing
    searchTimeout = setTimeout(() => {
        searchFighterAutocomplete(query);
    }, 300);
});

// Hide autocomplete when clicking outside
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
        hideAutocomplete();
    }
});

backBtn.addEventListener('click', () => {
    fightHistory.classList.add('hidden');
    searchInput.value = '';
    searchInput.focus();
    hideAutocomplete();
});

// Autocomplete search as user types
async function searchFighterAutocomplete(query) {
    hideError();
    
    try {
        const response = await fetch(`/api/search?name=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.fighters && data.fighters.length > 0) {
            displayAutocomplete(data.fighters);
        } else {
            hideAutocomplete();
        }
    } catch (error) {
        console.error('Autocomplete error:', error);
        hideAutocomplete();
    }
}

// Display autocomplete results
function displayAutocomplete(fighters) {
    autocompleteResults.innerHTML = '';
    
    // Show top 8 results
    const topFighters = fighters.slice(0, 8);
    
    topFighters.forEach((fighter) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `
            <div class="autocomplete-name">${fighter.name}</div>
            <div class="autocomplete-record">Record: ${fighter.record}</div>
        `;
        item.addEventListener('click', () => {
            selectFighter(fighter);
        });
        autocompleteResults.appendChild(item);
    });
    
    autocompleteResults.classList.remove('hidden');
}

// Select a fighter from autocomplete
function selectFighter(fighter) {
    searchInput.value = fighter.name;
    hideAutocomplete();
    loadFighterFights(fighter);
}

// Hide autocomplete
function hideAutocomplete() {
    autocompleteResults.classList.add('hidden');
}

// Display fighter results (not used anymore but keeping for compatibility)
function displayFighters(fighters) {
    fighterList.innerHTML = '';
    
    fighters.forEach((fighter) => {
        const card = document.createElement('div');
        card.className = 'fighter-card';
        card.innerHTML = `
            <h3>${fighter.name}</h3>
            <p class="fighter-record">Record: ${fighter.record}</p>
        `;
        card.addEventListener('click', () => selectFighter(fighter));
        fighterList.appendChild(card);
    });
    
    fighterResults.classList.remove('hidden');
}

// Load fights for a specific fighter
async function loadFighterFights(fighter) {
    showLoading();
    hideSections();
    hideError();
    
    try {
        const response = await fetch(`/api/fights?url=${encodeURIComponent(fighter.url)}`);
        const data = await response.json();
        
        hideLoading();
        
        if (data.fights && data.fights.length > 0) {
            displayFights(data.fights, fighter);
        } else {
            showError('No fight history found for this fighter.');
        }
    } catch (error) {
        hideLoading();
        showError('Error loading fight history. Please try again.');
        console.error('Fight loading error:', error);
    }
}

// Display fight history
function displayFights(fights, fighter) {
    fighterName.textContent = `${fighter.name}'s Fight History`;
    fightList.innerHTML = '';
    
    fights.forEach((fight) => {
        const card = document.createElement('div');
        card.className = 'fight-card';
        card.innerHTML = `
            <div class="fight-header">
                <div class="fight-event">${fight.event}</div>
                <div class="fight-date">${fight.date}</div>
            </div>
            <div class="fight-details">
                <div class="fight-opponent">vs ${fight.opponent}</div>
            </div>
        `;
        card.addEventListener('click', () => openParamountLink(fight, fighter.name));
        fightList.appendChild(card);
    });
    
    fightHistory.classList.remove('hidden');
}

// Open Paramount+ link for the fight
async function openParamountLink(fight, fighterName) {
    try {
        // Ask the backend to find the direct Paramount+ video URL
        const params = new URLSearchParams({
            fighter: fighterName,
            opponent: fight.opponent,
            event: fight.event
        });
        
        const response = await fetch(`/api/paramount-link?${params}`);
        const data = await response.json();
        
        if (data.url) {
            window.open(data.url, '_blank');
        }
    } catch (error) {
        // Fallback: open Paramount+ search
        const eventClean = fight.event.split(':')[0].trim();
        const searchQuery = `${eventClean} ${fighterName} vs ${fight.opponent}`;
        const paramountUrl = `https://www.paramountplus.com/search/?q=${encodeURIComponent(searchQuery)}`;
        window.open(paramountUrl, '_blank');
    }
}

// Utility functions
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function hideSections() {
    fighterResults.classList.add('hidden');
    fightHistory.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}
