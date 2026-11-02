(() => {
    const root = document.querySelector("[data-shop-admin]");
    if (!root) return;

    root.querySelectorAll("[data-image-input]").forEach((input) => {
        const label = input.closest("label");
        const image = label?.querySelector("[data-image-preview]");
        const empty = label?.querySelector("[data-image-preview-empty]");
        if (!image || !empty) return;

        const setImage = () => {
            const value = input.value.trim();
            image.hidden = true;
            empty.hidden = false;
            if (value.startsWith("https://") || value.startsWith("/static/")) {
                image.src = value;
            }
        };
        image.addEventListener("load", () => {
            image.hidden = false;
            empty.hidden = true;
        });
        image.addEventListener("error", () => {
            image.hidden = true;
            empty.hidden = false;
        });
        input.addEventListener("input", setImage);
        if (image.getAttribute("src")) {
            image.hidden = false;
            empty.hidden = true;
        } else {
            setImage();
        }
    });

    const inventoryItems = [...root.querySelectorAll("[data-inventory-item]")];
    const search = root.querySelector("[data-inventory-search]");
    const status = root.querySelector("[data-inventory-status]");
    const emptyState = root.querySelector("[data-inventory-empty]");
    const filterInventory = () => {
        const query = search?.value.trim().toLocaleLowerCase() || "";
        const selectedStatus = status?.value || "";
        let visibleCount = 0;
        inventoryItems.forEach((item) => {
            const matchesName = item.dataset.name.includes(query);
            const matchesStatus = !selectedStatus
                || item.dataset.status === selectedStatus
                || item.dataset.stock === selectedStatus;
            item.hidden = !(matchesName && matchesStatus);
            if (!item.hidden) visibleCount += 1;
        });
        if (emptyState) emptyState.hidden = inventoryItems.length === 0 || visibleCount > 0;
    };
    search?.addEventListener("input", filterInventory);
    status?.addEventListener("change", filterInventory);

    const discountType = root.querySelector("[data-discount-type]");
    const discountValue = root.querySelector("[data-discount-value]");
    const updateDiscountInput = () => {
        if (!discountType || !discountValue) return;
        const percent = discountType.value === "percent";
        discountValue.step = percent ? "1" : "0.01";
        discountValue.min = percent ? "1" : "0.01";
        discountValue.max = percent ? "100" : "";
    };
    discountType?.addEventListener("change", updateDiscountInput);
    updateDiscountInput();
})();
