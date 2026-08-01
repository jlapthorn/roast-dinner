(() => {
  function toggleWeightFields() {
    document.querySelectorAll(".food-check").forEach((checkbox) => {
      const id = checkbox.dataset.foodId;
      const weight = document.querySelector(`[data-weight-for="${id}"]`);
      if (!weight) return;
      const input = weight.querySelector("input");
      if (checkbox.checked) {
        weight.classList.remove("is-hidden");
        if (input) input.required = true;
      } else {
        weight.classList.add("is-hidden");
        if (input) input.required = false;
      }
    });
  }

  function initFoodFilter() {
    const form = document.getElementById("planner-form");
    const toggle = document.getElementById("toggle-all-foods");
    if (!form || !toggle) return;

    const apply = (showAll) => {
      form.classList.toggle("hide-non-favourites", !showAll);
      toggle.setAttribute("aria-pressed", showAll ? "true" : "false");
      toggle.textContent = showAll ? "Show favourites only" : "Show all foods";
    };

    // Editing a saved plan may include non-favourites — show everything then.
    const startHidden = form.dataset.favouritesDefault === "1";
    apply(!startHidden ? true : false);

    toggle.addEventListener("click", () => {
      const showingAll = toggle.getAttribute("aria-pressed") === "true";
      apply(!showingAll);
    });
  }

  function initPlanner() {
    const form = document.getElementById("planner-form");
    if (!form) return;
    form.addEventListener("change", (event) => {
      if (event.target.classList.contains("food-check")) {
        toggleWeightFields();
      }
    });
    toggleWeightFields();
    initFoodFilter();
  }

  function initFoodForm() {
    const category = document.getElementById("category");
    if (!category) return;

    const sync = () => {
      const isMeat = category.value === "meat";
      document.querySelectorAll(".meat-only").forEach((el) => {
        el.hidden = !isMeat;
      });
      document.querySelectorAll(".non-meat-only").forEach((el) => {
        el.hidden = isMeat;
      });
      const meatType = document.getElementById("meat_type");
      if (meatType) meatType.required = isMeat;
      const temperature = document.getElementById("temperature_c");
      if (temperature) temperature.required = isMeat;
    };

    category.addEventListener("change", sync);
    sync();
  }

  window.RoastDinner = { initFoodForm };

  document.addEventListener("DOMContentLoaded", () => {
    initPlanner();
    initFoodForm();
  });
})();
