document.addEventListener("DOMContentLoaded", () => {
    let searchTimeout = null;
    let activeFood = null;
    let currentRequest = null;

    const searchInput = document.getElementById("live-search");
    const stateSelect = document.getElementById("search-state");
    const dropdown = document.getElementById("dropdown");
    const searchButton = document.querySelector(".btn-search");

    const foodName = document.getElementById("food_name");
    const state = document.getElementById("state");
    const grams = document.getElementById("grams");

    const calories = document.getElementById("calories");
    const protein = document.getElementById("protein");
    const carbs = document.getElementById("carbs");
    const fats = document.getElementById("fats");
    const fiber = document.getElementById("fiber");


    // ---------------------------------------------
    // CHECK REQUIRED ELEMENTS
    // ---------------------------------------------

    if (
        !searchInput ||
        !stateSelect ||
        !dropdown ||
        !searchButton ||
        !foodName ||
        !state ||
        !grams ||
        !calories ||
        !protein ||
        !carbs ||
        !fats ||
        !fiber
    ) {
        console.error("Tracker: required HTML element is missing.");
        return;
    }


    // ---------------------------------------------
    // SEARCH BUTTON
    // ---------------------------------------------

    searchButton.addEventListener("click", () => {
        clearTimeout(searchTimeout);
        searchFoods(searchInput.value.trim());
    });


    // ---------------------------------------------
    // LIVE SEARCH
    // ---------------------------------------------

    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);

        const query = searchInput.value.trim();

        if (query.length < 2) {
            hideDropdown();
            return;
        }

        searchTimeout = setTimeout(() => {
            searchFoods(query);
        }, 300);
    });


    // ---------------------------------------------
    // ENTER / ESCAPE
    // ---------------------------------------------

    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();

            clearTimeout(searchTimeout);
            searchFoods(searchInput.value.trim());
        }

        if (event.key === "Escape") {
            hideDropdown();
        }
    });


    // ---------------------------------------------
    // SEARCH FOOD API
    // ---------------------------------------------

    async function searchFoods(query) {
        if (query.length < 2) {
            hideDropdown();
            return;
        }

        // Cancel previous request
        if (currentRequest) {
            currentRequest.abort();
        }

        currentRequest = new AbortController();

        showMessage("Searching database...");

        try {
            const response = await fetch(
                `/api/search-food?q=${encodeURIComponent(query)}`,
                {
                    method: "GET",
                    signal: currentRequest.signal,
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Search request failed: ${response.status}`
                );
            }

            const foods = await response.json();

            // Ignore old results if the user has already changed
            // the search query.
            if (searchInput.value.trim() !== query) {
                return;
            }

            displayResults(foods);

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error("Food search error:", error);
            showMessage("Unable to search the database.");
        }
    }


    // ---------------------------------------------
    // DISPLAY RESULTS
    // ---------------------------------------------

    function displayResults(foods) {
        dropdown.innerHTML = "";

        if (!Array.isArray(foods) || foods.length === 0) {
            showMessage("No food results found.");
            return;
        }

        foods.forEach((food) => {
            const li = document.createElement("li");

            const title = document.createElement("div");
            title.className = "item-title";

            const name = document.createElement("span");
            name.textContent = food.name || "Unknown food";

            const source = document.createElement("span");
            source.className = "source-tag";
            source.textContent = food.source || "Database";

            title.appendChild(name);
            title.appendChild(source);


            const macros = document.createElement("div");
            macros.className = "macro-badge-row";

            const caloriesBadge = document.createElement("span");
            caloriesBadge.className = "mb-cal";
            caloriesBadge.textContent =
                `${food.calories_100g ?? 0} kcal/100g`;

            const proteinBadge = document.createElement("span");
            proteinBadge.className = "mb-p";
            proteinBadge.textContent =
                `P: ${food.protein_100g ?? 0}g`;

            const carbsBadge = document.createElement("span");
            carbsBadge.className = "mb-c";
            carbsBadge.textContent =
                `C: ${food.carbs_100g ?? 0}g`;

            const fatsBadge = document.createElement("span");
            fatsBadge.className = "mb-f";
            fatsBadge.textContent =
                `F: ${food.fats_100g ?? 0}g`;

            macros.appendChild(caloriesBadge);
            macros.appendChild(proteinBadge);
            macros.appendChild(carbsBadge);
            macros.appendChild(fatsBadge);


            li.appendChild(title);
            li.appendChild(macros);

            li.addEventListener("click", () => {
                selectFood(food);
            });

            dropdown.appendChild(li);
        });

        dropdown.style.display = "block";
    }


    // ---------------------------------------------
    // SELECT FOOD
    // ---------------------------------------------

    function selectFood(food) {
        activeFood = food;

        foodName.value = food.name || "";

        if (stateSelect.value) {
            state.value = stateSelect.value;
        }

        if (!grams.value) {
            grams.value = 100;
        }

        recalculateMacros();

        searchInput.value = "";
        hideDropdown();

        grams.focus();
    }


    // ---------------------------------------------
    // NUTRITION CALCULATION
    // ---------------------------------------------

    grams.addEventListener("input", recalculateMacros);


    function recalculateMacros() {
        if (!activeFood) {
            return;
        }

        const amount = parseFloat(grams.value);

        if (!amount || amount <= 0) {
            clearNutrition();
            return;
        }

        const multiplier = amount / 100;

        calories.value = calculate(
            activeFood.calories_100g,
            multiplier
        );

        protein.value = calculate(
            activeFood.protein_100g,
            multiplier
        );

        carbs.value = calculate(
            activeFood.carbs_100g,
            multiplier
        );

        fats.value = calculate(
            activeFood.fats_100g,
            multiplier
        );

        fiber.value = calculate(
            activeFood.fiber_100g,
            multiplier
        );
    }


    function calculate(value, multiplier) {
        return (Number(value || 0) * multiplier).toFixed(1);
    }


    function clearNutrition() {
        calories.value = "";
        protein.value = "";
        carbs.value = "";
        fats.value = "";
        fiber.value = "";
    }


    // ---------------------------------------------
    // DROPDOWN HELPERS
    // ---------------------------------------------

    function showMessage(message) {
        dropdown.innerHTML = "";

        const li = document.createElement("li");

        li.style.color = "var(--text-muted)";
        li.textContent = message;

        dropdown.appendChild(li);
        dropdown.style.display = "block";
    }


    function hideDropdown() {
        dropdown.style.display = "none";
        dropdown.innerHTML = "";
    }


    // ---------------------------------------------
    // CLOSE DROPDOWN WHEN CLICKING OUTSIDE
    // ---------------------------------------------

    document.addEventListener("click", (event) => {
        if (!event.target.closest(".search-wrapper")) {
            hideDropdown();
        }
    });


    console.log("Tracker JavaScript loaded successfully.");
});