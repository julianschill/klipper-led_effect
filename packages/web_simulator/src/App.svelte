<script lang="ts">
  import { onMount } from "svelte";
  import colormath from "./colormath-3.0.0-py3-none-any.whl?url";
  import led_effect from "./led_effect-0.1.0-py3-none-any.whl?url";
  import klippermock from "./klippermock-0.1.0-py3-none-any.whl?url";
  import { PrintSimulator } from "./printSimulator";

  let kmock: any = undefined;
  let printer: any = undefined;
  let pythonOutput: string = "";
  let error: string | undefined = undefined;
  let pyodide: any = undefined;
  const init = async () => {
    const _log = console.log;
    console.log = (...args) => {
      pythonOutput += args.join(" ") + "\n";
      _log(...args);
    };
    pyodide = await (window as any).loadPyodide();

    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install([colormath, led_effect, klippermock]);

    kmock = pyodide.pyimport("klippermock");
    console.log = _log;
    setTimeout(() => {
      pythonOutput = "";
    }, 2000);
  };

  let layers = "gradient 1 1 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ";
  let ledCount = 10;

  const initPrinter = (layers: string, ledCount: number, kmock: any) => {
    if (kmock === undefined) {
      return;
    }
    const config = kmock.mockConfig();
    config.setint("ledcount", ledCount);
    config.set("layers", layers);
    const printer = kmock.mockPrinter(config);

    printer._handle_ready();
    printer.led_effect.set_enabled(true);
    printer.led_effect.handler.heaterCurrent = pyodide.toPy({
      hotend: heaterHotendCurrent,
      heater_bed: heaterBedCurrent,
    });
    printer.led_effect.handler.heaterTarget = pyodide.toPy({
      hotend: heaterHotendTarget,
      heater_bed: heaterBedTarget,
    });
    printer.led_effect.handler.heaterLast = pyodide.toPy({
      hotend: heaterHotendCurrent,
      heater_bed: heaterBedCurrent,
    });
    currentFrame = 0;
    return printer;
  };

  let currentLeds = new Array(ledCount).fill([0, 0, 0]);
  let currentFrame = 0;
  let heaterHotendTarget = 250;
  let heaterHotendCurrent = 10;
  let heaterBedTarget = 60;
  let heaterBedCurrent = 10;
  let printProgress = 0;
  let fps = 24;

  $: {
    printer?.set_heater(0, heaterHotendTarget, heaterHotendCurrent, "hotend");
  }
  $: {
    printer?.set_heater(0, heaterBedTarget, heaterBedCurrent, "heater_bed");
  }

  let simulationStatus: string = "not running";
  let printSimulator: PrintSimulator = new PrintSimulator(
    { heater_bed: 60, hotend: 250 },
    (heater, temp) => {
      if (heater == "heater_bed") {
        heaterBedCurrent = temp;
      } else {
        heaterHotendCurrent = temp;
      }
    },
    (pct) => (printProgress = pct),
    (status) => (simulationStatus = status),
  );

  const drawLeds = () => {
    if (!printer) {
      return;
    }
    const [frame, shouldUpdate] = printer.led_effect.getFrame(currentFrame++);
    if (!shouldUpdate) return;
    currentLeds = [];
    for (let i = 0; i < frame.length; i += 4) {
      currentLeds[i / 4] = [frame[i], frame[i + 1], frame[i + 2]].map(
        (i) => i * 255,
      );
    }
  };

  $: {
    try {
      printer = initPrinter(layers, ledCount, kmock);
      error = undefined;
    } catch (e: any) {
      error = e;
    }
  }

  let interval: number | undefined = undefined;

  const updateInterval = (fps: number) => {
    window.clearInterval(interval);
    interval = window.setInterval(drawLeds, 1000 / fps);
  };
  $: updateInterval(fps);

  onMount(() => {
    updateInterval(fps);
    return () => {
      window.clearInterval(interval);
    };
  });
</script>

<svelte:head>
  <script
    src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"
    on:load={init}
  ></script>
</svelte:head>
<main>
  <table style="margin: 0 auto">
    <tr>
      <th>Layers</th>
      <td><textarea bind:value={layers} rows="10" cols="50"></textarea></td>
    </tr>
    <tr>
      <th>LED Count</th>
      <td><input type="number" bind:value={ledCount} /></td>
    </tr>
    <tr>
      <th>FPS</th>
      <td><input type="number" bind:value={fps} /></td>
    </tr>
    <tr>
      <th>Temperature (<code>heater_bed</code>)</th>
      <td>
        <label for="current">Current: </label><input
          type="number"
          bind:value={heaterBedCurrent}
          id="current"
        /><br />
        <label for="target">Target: </label><input
          type="number"
          bind:value={heaterBedTarget}
          id="target"
        /><br />
      </td>
    </tr>
    <tr>
      <th>Temperature (<code>hotend</code>)</th>
      <td>
        <label for="current">Current: </label><input
          type="number"
          bind:value={heaterHotendCurrent}
          id="current"
        /><br />
        <label for="target">Target: </label><input
          type="number"
          bind:value={heaterHotendTarget}
          id="target"
        /><br />
      </td>
    </tr>
    <tr>
      <th><label for="progress">Progress: </label></th>
      <td>
        <input type="number" bind:value={printProgress} id="progress" />
      </td>
    </tr>
    <tr>
      <th>Print Simulation</th>
      <td
        >Status: {simulationStatus}<br />
        <button on:click={() => printSimulator.run()}>Start</button>
        <button on:click={() => printSimulator.stop()}>Stop</button>
      </td>
    </tr>
  </table>
  <div>
    {#each currentLeds as led, i}
      <div
        style={`background-color: rgb(${led.join(",")}); width: 50px; height: 50px; border-radius: 25px; margin: 5px; display: inline-block;`}
      ></div>
    {/each}
  </div>
  <pre style="font-weight: bold">{pythonOutput}</pre>
  {#if error}
    <pre style="color: red; font-weight: bold">{error}</pre>
  {/if}
</main>
