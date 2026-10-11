document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".rating-input input").forEach((input) => {
    input.addEventListener("change", () => {
      document.querySelectorAll(".rating-input span").forEach((span) => {
        span.style.opacity = "0.65";
      });
      const selected = input.nextElementSibling;
      if (selected) selected.style.opacity = "1";
    });
  });
});
