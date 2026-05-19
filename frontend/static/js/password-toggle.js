document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
        const input = document.getElementById(button.dataset.passwordToggle);
        const label = button.querySelector("span");

        if (!input || !label) {
            return;
        }

        const showPassword = input.type === "password";
        input.type = showPassword ? "text" : "password";
        label.textContent = showPassword ? "Ocultar" : "Mostrar";
        button.setAttribute("aria-label", showPassword ? "Ocultar contrasena" : "Mostrar contrasena");
        button.setAttribute("aria-pressed", showPassword ? "true" : "false");
    });
});
