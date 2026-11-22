
document.addEventListener("DOMContentLoaded", function () {

    // Sidebar toggle button
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggle && sidebar) {

        // Open and close sidebar
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });

        // Close sidebar when clicking outside it
        document.addEventListener("click", function (event) {

            const clickedInsideSidebar = sidebar.contains(event.target);
            const clickedToggle = sidebarToggle.contains(event.target);

            if (
                window.innerWidth <= 992 &&
                !clickedInsideSidebar &&
                !clickedToggle
            ) {
                sidebar.classList.remove("show");
            }
        });

        // Close sidebar using Escape key
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                sidebar.classList.remove("show");
            }
        });

    }

});
