"use strict";

const API = window.location.origin;

const imgUrl     = (id, field) => `${API}/api/media/${id}/image/${field}`;
const trailerUrl = (id)        => `${API}/api/media/${id}/trailer`;
const fmt        = (iso)       => iso
    ? new Date(iso).toLocaleDateString("es-ES", { year: "numeric", month: "long" })
    : "";

async function loadRandom() {
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("game").classList.add("hidden");

    try {
        const res = await fetch(`${API}/api/title/random`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        render(await res.json());
    } catch (err) {
        document.getElementById("loading").textContent = `Error: ${err.message}`;
    }
}

function render(title) {
    const id = title.media?.id ?? title.media_id;

    document.getElementById("g-header").src  = imgUrl(id, "header");
    document.getElementById("g-header").alt  = title.name;
    document.getElementById("g-capsule").src = imgUrl(id, "capsule");
    document.getElementById("g-capsule").alt = title.name;
    document.getElementById("g-name").textContent = title.name;
    document.getElementById("g-desc").textContent = title.description ?? "";
    document.getElementById("g-meta").textContent =
        [title.developer?.name, fmt(title.release_date)].filter(Boolean).join(" · ");
    document.getElementById("g-price").textContent =
        title.release_price === 0 ? "Gratis"
        : title.release_price != null ? `€${Number(title.release_price).toFixed(2)}`
        : "";

    // Genres
    const genresEl = document.getElementById("g-genres");
    genresEl.innerHTML = "";
    (title.genres ?? []).forEach(g => {
        const chip = document.createElement("span");
        chip.className = "text-xs bg-[#2a475e] text-[#c6d4df] px-2 py-0.5 rounded";
        chip.textContent = g.name;
        genresEl.appendChild(chip);
    });

    // Trailer
    const trailer = document.getElementById("g-trailer");
    trailer.src = id ? trailerUrl(id) : "";

    // Screenshot gallery
    const gallery = document.getElementById("g-gallery");
    gallery.innerHTML = "";
    ["store_1", "store_2", "store_3", "store_4", "store_5", "store_6"].forEach(field => {
        const img = document.createElement("img");
        img.src       = imgUrl(id, field);
        img.alt       = field;
        img.loading   = "lazy";
        img.className = "w-full aspect-video object-cover rounded-lg bg-card";
        img.addEventListener("error", () => img.remove());
        gallery.appendChild(img);
    });

    document.getElementById("loading").classList.add("hidden");
    document.getElementById("game").classList.remove("hidden");
}

loadRandom();
