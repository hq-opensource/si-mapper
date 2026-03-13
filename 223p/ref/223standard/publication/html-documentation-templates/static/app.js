(function() {
    const search = document.getElementById("search");
    const cards = Array.from(document.getElementsByClassName("card"));
    let debounceTimeout;

    search.addEventListener("input", function() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            const query = search.value.toLowerCase();
            for (const item of cards) {
                if (item.dataset.concept.toLowerCase().includes(query)) {
                    item.style.display = "block";
                } else {
                    item.style.display = "none";
                }
            }
        }, 300); // Adjust the delay as needed (e.g., 300ms)
    });
    for (const item of document.querySelectorAll('a.reset-search')) { // Example selector
        item.addEventListener("click", function(e) {
            e.preventDefault();
            for (const item of document.getElementsByClassName("card")) {
                item.style.display = "block";
            }
            return false;
        });
    }
})();
