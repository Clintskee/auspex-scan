const state = {
  units: [],
  weapons: [],
};

const elements = {
  weaponSelect: document.querySelector("#weapon-select"),
  unitSelect: document.querySelector("#unit-select"),
  weaponCount: document.querySelector("#weapon-count"),
  modelCount: document.querySelector("#model-count"),
  weaponSummary: document.querySelector("#weapon-summary"),
  unitSummary: document.querySelector("#unit-summary"),
  status: document.querySelector("#status-message"),
  results: document.querySelector(".results"),
  matchupLabel: document.querySelector("#matchup-label"),
};

function selectedWeapon() {
  const id = Number(elements.weaponSelect.value);
  return state.weapons.find((weapon) => weapon.id === id);
}

function selectedUnit() {
  const id = Number(elements.unitSelect.value);
  return state.units.find((unit) => unit.id === id);
}

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("error", isError);
}

function setSummary(summary, values) {
  const fields = summary.querySelectorAll("dd");
  fields.forEach((field, index) => {
    field.textContent = values[index] ?? "—";
  });
}

function updateWeaponSummary() {
  const weapon = selectedWeapon();
  if (!weapon) {
    setSummary(elements.weaponSummary, []);
    return;
  }

  const type = weapon.weapon_type === "ranged"
    ? `Ranged · ${weapon.range_inches}\u2033`
    : "Melee";
  setSummary(elements.weaponSummary, [
    type,
    weapon.attacks,
    `${weapon.skill}+`,
    weapon.strength,
    weapon.armour_penetration,
    weapon.damage,
  ]);
}

function updateUnitSummary() {
  const unit = selectedUnit();
  if (!unit) {
    setSummary(elements.unitSummary, []);
    return;
  }

  elements.modelCount.min = unit.minimum_model_count;
  elements.modelCount.max = unit.maximum_model_count;
  const currentCount = Number(elements.modelCount.value);
  if (
    currentCount < unit.minimum_model_count
    || currentCount > unit.maximum_model_count
  ) {
    elements.modelCount.value = unit.minimum_model_count;
  }

  setSummary(elements.unitSummary, [
    unit.toughness,
    `${unit.save}+`,
    unit.invulnerable_save ? `${unit.invulnerable_save}+` : "—",
    unit.wounds,
    `${unit.minimum_model_count}–${unit.maximum_model_count}`,
  ]);
}

function addOptions(select, items, labelForItem) {
  select.replaceChildren();
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = labelForItem(item);
    select.append(option);
  });
  select.disabled = items.length === 0;
}

async function loadProfiles() {
  try {
    const unitsResponse = await fetch("/v1/units");
    if (!unitsResponse.ok) {
      throw new Error("Unit profiles could not be loaded.");
    }

    state.units = await unitsResponse.json();
    const weaponGroups = await Promise.all(
      state.units.map(async (unit) => {
        const response = await fetch(`/v1/units/${unit.id}/weapons`);
        if (!response.ok) {
          throw new Error(`Weapons for ${unit.name} could not be loaded.`);
        }
        const weapons = await response.json();
        return weapons.map((weapon) => ({
          ...weapon,
          unit_name: unit.name,
        }));
      }),
    );
    state.weapons = weaponGroups.flat();

    addOptions(
      elements.weaponSelect,
      state.weapons,
      (weapon) => {
        const profile = weapon.profile_name === "default"
          ? ""
          : ` · ${weapon.profile_name}`;
        return `${weapon.unit_name} — ${weapon.name}${profile}`;
      },
    );
    addOptions(
      elements.unitSelect,
      state.units,
      (unit) => `${unit.name} — ${unit.faction}`,
    );

    if (state.weapons.length === 0 || state.units.length === 0) {
      setStatus(
        "Add at least one active unit and weapon profile through the API docs.",
        true,
      );
      return;
    }

    updateWeaponSummary();
    updateUnitSummary();
    await calculate();
  } catch (error) {
    setStatus(error.message, true);
  }
}

function updateResults(payload) {
  const result = payload.result;
  document.querySelector("#expected-damage").textContent =
    result.expected_damage.toFixed(2);
  document.querySelector("#models-destroyed").textContent =
    result.expected_models_destroyed.toFixed(2);
  document.querySelector("#expected-hits").textContent =
    result.expected_hits.toFixed(2);
  document.querySelector("#expected-wounds").textContent =
    result.expected_wounds.toFixed(2);
  document.querySelector("#unsaved-attacks").textContent =
    result.expected_unsaved_attacks.toFixed(2);
  document.querySelector("#wound-roll").textContent =
    `${result.wound_roll_required}+`;
  document.querySelector("#save-used").textContent = result.save_used === "none"
    ? "None"
    : `${result.effective_save_required}+ ${result.save_used}`;
  document.querySelector("#failed-save").textContent =
    `${(result.failed_save_probability * 100).toFixed(1)}%`;
  elements.matchupLabel.textContent =
    `${payload.weapon_count}× ${payload.weapon.name} into `
    + `${payload.defender_model_count} ${payload.defender.name}`;
  elements.results.hidden = false;
}

async function calculate() {
  const weapon = selectedWeapon();
  const unit = selectedUnit();
  if (!weapon || !unit) {
    return;
  }

  const weaponCount = Number(elements.weaponCount.value);
  const modelCount = Number(elements.modelCount.value);
  if (!Number.isInteger(weaponCount) || weaponCount < 1) {
    setStatus("Number of weapons must be at least 1.", true);
    return;
  }
  if (
    !Number.isInteger(modelCount)
    || modelCount < unit.minimum_model_count
    || modelCount > unit.maximum_model_count
  ) {
    setStatus(
      `Target size must be ${unit.minimum_model_count}–`
      + `${unit.maximum_model_count} models.`,
      true,
    );
    return;
  }

  setStatus("Calculating…");
  try {
    const response = await fetch("/v1/calculations/expected-damage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        weapon_profile_id: weapon.id,
        defender_unit_id: unit.id,
        weapon_count: weaponCount,
        defender_model_count: modelCount,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      const message = typeof payload.detail === "string"
        ? payload.detail
        : "The matchup could not be calculated.";
      throw new Error(message);
    }

    updateResults(payload);
    setStatus("Calculation updated.");
  } catch (error) {
    elements.results.hidden = true;
    setStatus(error.message, true);
  }
}

elements.weaponSelect.addEventListener("change", () => {
  updateWeaponSummary();
  calculate();
});
elements.unitSelect.addEventListener("change", () => {
  updateUnitSummary();
  calculate();
});
elements.weaponCount.addEventListener("change", calculate);
elements.modelCount.addEventListener("change", calculate);

loadProfiles();
