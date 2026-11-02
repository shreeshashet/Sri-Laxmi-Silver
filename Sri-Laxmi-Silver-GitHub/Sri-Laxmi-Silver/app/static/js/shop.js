(() => {
    const storageKey = "sljw-saved-pieces-v1";
    const wishlistToggle = document.querySelector("#wishlist-toggle");
    const savedButtons = [...document.querySelectorAll("[data-wishlist-id]")];

    const readSaved = () => {
        try {
            const value = JSON.parse(window.localStorage.getItem(storageKey) || "[]");
            return Array.isArray(value)
                ? value.filter((id) => Number.isInteger(id) && id > 0)
                : [];
        } catch (error) {
            console.error("Could not read saved SLJW items.", error);
            return [];
        }
    };

    const writeSaved = (ids) => {
        try {
            window.localStorage.setItem(storageKey, JSON.stringify(ids));
            return true;
        } catch (error) {
            console.error("Could not save SLJW items in this browser.", error);
            return false;
        }
    };

    const updateSavedButtons = (ids) => {
        savedButtons.forEach((button) => {
            const isSaved = ids.includes(Number(button.dataset.wishlistId));
            button.classList.toggle("is-saved", isSaved);
            button.setAttribute("aria-pressed", String(isSaved));
            if (button.classList.contains("detail-wishlist")) {
                const label = button.querySelector("span");
                if (label) {
                    label.textContent = isSaved ? "Saved for later" : "Add to saved pieces";
                }
            }
        });
    };

    let savedIds = readSaved();
    updateSavedButtons(savedIds);

    savedButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const productId = Number(button.dataset.wishlistId);
            savedIds = savedIds.includes(productId)
                ? savedIds.filter((id) => id !== productId)
                : [...savedIds, productId];
            if (writeSaved(savedIds)) {
                updateSavedButtons(savedIds);
            }
        });
    });

    wishlistToggle?.addEventListener("click", () => {
        const cards = [...document.querySelectorAll(".product-card[data-product-id]")];
        if (!cards.length) {
            window.location.assign("/shop/");
            return;
        }
        const showSaved = wishlistToggle.dataset.showingSaved !== "true";
        wishlistToggle.dataset.showingSaved = String(showSaved);
        cards.forEach((card) => {
            card.hidden = showSaved && !savedIds.includes(Number(card.dataset.productId));
        });
        wishlistToggle.classList.toggle("active", showSaved);
        const firstCard = cards.find((card) => !card.hidden);
        if (showSaved && firstCard) {
            firstCard.scrollIntoView({ behavior: "smooth", block: "center" });
        } else if (showSaved) {
            window.alert("You have not saved any pieces on this device yet.");
        }
        if (!showSaved) {
            document.querySelector("#collection, #catalog-products")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }
    });
})();
