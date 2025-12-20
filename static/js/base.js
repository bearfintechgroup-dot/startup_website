// ==============================
// BASE.JS — Global Site Logic
// ==============================

document.addEventListener("DOMContentLoaded", () => {
    const hamburger = document.getElementById("hamburger");
    const navLinksMenu = document.getElementById("nav-links");

    if (!hamburger || !navLinksMenu) return;

    // Toggle menu
    hamburger.addEventListener("click", () => {
        hamburger.classList.toggle("active");
        navLinksMenu.classList.toggle("open");
    });

    // Auto-close on link click (mobile UX)
    navLinksMenu.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            hamburger.classList.remove("active");
            navLinksMenu.classList.remove("open");
        });
    });
});
