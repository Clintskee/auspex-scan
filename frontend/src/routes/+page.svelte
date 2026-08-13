<script>
  import { onMount } from 'svelte';
  import '../styles.css';

  let units = [];
  let weapons = [];
  let weaponId = '';
  let unitId = '';
  let weaponCount = 1;
  let modelCount = 1;
  let status = 'Loading stored profiles…';
  let error = false;
  let result = null;
  let weapon;
  let unit;

  $: weapon = weapons.find((item) => item.id === Number(weaponId));
  $: unit = units.find((item) => item.id === Number(unitId));
  const selectedWeapon = () => weapon;
  const selectedUnit = () => unit;

  async function loadProfiles() {
    try {
      const response = await fetch('/v1/units');
      if (!response.ok) throw new Error('Unit profiles could not be loaded.');
      units = await response.json();
      weapons = (await Promise.all(units.map(async (unit) => {
        const weaponResponse = await fetch(`/v1/units/${unit.id}/weapons`);
        if (!weaponResponse.ok) throw new Error(`Weapons for ${unit.name} could not be loaded.`);
        return (await weaponResponse.json()).map((weapon) => ({ ...weapon, unit_name: unit.name }));
      }))).flat();
      weaponId = weapons[0]?.id ?? '';
      unitId = units[0]?.id ?? '';
      modelCount = units[0]?.minimum_model_count ?? 1;
      if (!weapons.length || !units.length) {
        status = 'Add at least one active unit and weapon profile through the API docs.';
        error = true;
        return;
      }
      await calculate();
    } catch (cause) {
      status = cause instanceof Error ? cause.message : 'Profiles could not be loaded.';
      error = true;
    }
  }

  function unitChanged() {
    const unit = selectedUnit();
    if (unit) modelCount = unit.minimum_model_count;
    calculate();
  }

  async function calculate() {
    const weapon = selectedWeapon();
    const unit = selectedUnit();
    if (!weapon || !unit) return;
    if (!Number.isInteger(Number(weaponCount)) || Number(weaponCount) < 1) {
      status = 'Number of weapons must be at least 1.'; error = true; return;
    }
    if (!Number.isInteger(Number(modelCount)) || modelCount < unit.minimum_model_count || modelCount > unit.maximum_model_count) {
      status = `Target size must be ${unit.minimum_model_count}–${unit.maximum_model_count} models.`; error = true; return;
    }
    status = 'Calculating…'; error = false;
    try {
      const response = await fetch('/v1/calculations/expected-damage', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weapon_profile_id: weapon.id, defender_unit_id: unit.id, weapon_count: Number(weaponCount), defender_model_count: Number(modelCount) })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : 'The matchup could not be calculated.');
      result = payload; status = 'Calculation updated.';
    } catch (cause) {
      result = null; error = true; status = cause instanceof Error ? cause.message : 'Calculation failed.';
    }
  }

  onMount(loadProfiles);
</script>

<svelte:head><title>Auspex Scan</title></svelte:head>

<main class="page-shell">
  <header class="site-header">
    <div><p class="eyebrow">Warhammer 40,000 matchup analysis</p><h1>Auspex Scan</h1></div>
    <a class="api-link" href="/docs">API docs</a>
  </header>
  <section class="intro"><p class="section-number">01 / Target acquisition</p><h2>Weapon into target</h2><p>Select a stored weapon and defending unit. Results update as your selections change.</p></section>
  <section class="selection-grid" aria-label="Combatant selection">
    <article class="selection-card attacker-card">
      <div class="card-heading"><span class="role-marker">A</span><div><p class="card-label">Attacker</p><h3>Weapon profile</h3></div></div>
      <label for="weapon">Stored weapon</label>
      <select id="weapon" bind:value={weaponId} on:change={calculate} disabled={!weapons.length}>
        {#each weapons as weapon}<option value={weapon.id}>{weapon.unit_name} — {weapon.name}{weapon.profile_name === 'default' ? '' : ` · ${weapon.profile_name}`}</option>{/each}
      </select>
      <label for="weapon-count">Number of weapons</label><input id="weapon-count" type="number" min="1" max="1000" bind:value={weaponCount} on:change={calculate} />
      <dl class="profile-summary"><div><dt>Type</dt><dd>{weapon?.weapon_type ?? '—'}</dd></div><div><dt>A</dt><dd>{weapon?.attacks ?? '—'}</dd></div><div><dt>Skill</dt><dd>{weapon ? `${weapon.skill}+` : '—'}</dd></div><div><dt>S</dt><dd>{weapon?.strength ?? '—'}</dd></div><div><dt>AP</dt><dd>{weapon?.armour_penetration ?? '—'}</dd></div><div><dt>D</dt><dd>{weapon?.damage ?? '—'}</dd></div></dl>
    </article>
    <div class="versus"><span>VS</span></div>
    <article class="selection-card defender-card">
      <div class="card-heading"><span class="role-marker">D</span><div><p class="card-label">Defender</p><h3>Target unit</h3></div></div>
      <label for="unit">Stored unit</label><select id="unit" bind:value={unitId} on:change={unitChanged} disabled={!units.length}>{#each units as unit}<option value={unit.id}>{unit.name} — {unit.faction}</option>{/each}</select>
      <label for="model-count">Models in target unit</label><input id="model-count" type="number" min={unit?.minimum_model_count ?? 1} max={unit?.maximum_model_count ?? 20} bind:value={modelCount} on:change={calculate} />
      <dl class="profile-summary"><div><dt>T</dt><dd>{unit?.toughness ?? '—'}</dd></div><div><dt>Sv</dt><dd>{unit ? `${unit.save}+` : '—'}</dd></div><div><dt>Inv</dt><dd>{unit?.invulnerable_save ? `${unit.invulnerable_save}+` : '—'}</dd></div><div><dt>W</dt><dd>{unit?.wounds ?? '—'}</dd></div><div><dt>Models</dt><dd>{unit ? `${unit.minimum_model_count}–${unit.maximum_model_count}` : '—'}</dd></div></dl>
    </article>
  </section>
  <p class:error class="status-message" role="status">{status}</p>
  {#if result}
    <section class="results"><div class="results-heading"><div><p class="section-number">02 / Expected outcome</p><h2>Damage forecast</h2></div><p>{result.weapon_count}× {result.weapon.name} into {result.defender_model_count} {result.defender.name}</p></div>
      <div class="primary-results"><article><span>Expected damage</span><strong>{result.result.expected_damage.toFixed(2)}</strong></article><article><span>Models destroyed</span><strong>{result.result.expected_models_destroyed.toFixed(2)}</strong></article></div>
      <div class="result-details"><div><span>Expected hits</span><strong>{result.result.expected_hits.toFixed(2)}</strong></div><div><span>Expected wounds</span><strong>{result.result.expected_wounds.toFixed(2)}</strong></div><div><span>Unsaved attacks</span><strong>{result.result.expected_unsaved_attacks.toFixed(2)}</strong></div><div><span>Wound roll</span><strong>{result.result.wound_roll_required}+</strong></div><div><span>Save used</span><strong>{result.result.save_used}</strong></div><div><span>Failed save</span><strong>{(result.result.failed_save_probability * 100).toFixed(1)}%</strong></div></div>
    </section>
  {/if}
</main>
