document.addEventListener("DOMContentLoaded", function() {
    // Smooth fade-in effect for containers
    document.querySelectorAll(".container").forEach(container => {
        container.style.opacity = 0;
        setTimeout(() => {
            container.style.opacity = 1;
            container.style.transition = "opacity 0.5s ease-in-out";
        }, 100);
    });

    // Highlight table row on hover
    document.querySelectorAll("table tr").forEach(row => {
        row.addEventListener("mouseenter", function() {
            this.style.backgroundColor = "#e3f2fd";
        });
        row.addEventListener("mouseleave", function() {
            this.style.backgroundColor = "";
        });
    });

    // Button click animation
    document.querySelectorAll("button").forEach(button => {
        button.addEventListener("mousedown", function() {
            this.style.transform = "scale(0.95)";
        });
        button.addEventListener("mouseup", function() {
            this.style.transform = "scale(1)";
        });
    });
});
