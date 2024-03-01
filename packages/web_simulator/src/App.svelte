<script lang="ts">
  import { onMount } from "svelte";
  import led_effect from "./led_effect-0.1.0-py3-none-any.whl?url";
  import klippermock from "./klippermock-0.1.0-py3-none-any.whl?url";

  let kmock: any = undefined;
  let printer: any = undefined;
  const init = async () => {
    const pyodide = await (window as any).loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install([led_effect, klippermock]);

    kmock = pyodide.pyimport("klippermock");
  };

  let layers = "gradient 1 1 top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ";
  let ledCount = 10;

  const initPrinter = (layers: string, ledCount: number, kmock: any) => {
    if (kmock === undefined) {
      return;
    }
    currentFrame = 0;
    const config = kmock.mockConfig();
    config.setint("ledcount", ledCount);
    config.set("layers", layers);
    const printer = kmock.mockPrinter(config);
    printer._handle_ready();
    printer.led_effect.set_enabled(true);
    return printer;
  };

  let currentLeds = new Array(ledCount).fill([0, 0, 0]);
  let currentFrame = 0;
  let heaterTarget = 250;
  let heaterCurrent = 10;
  let fps = 24;

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
    if (printer) {
      printer.set_heater(0, heaterTarget, heaterCurrent);
    }
  }

  $: {
    try {
      console.log("Resetting printer");
      printer = initPrinter(layers, ledCount, kmock);
    } catch (e) {}
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
      <th>Temperature</th>
      <td>
        <label for="current">Current: </label><input
          type="number"
          bind:value={heaterCurrent}
          id="current"
        /><br />
        <label for="target">Target: </label><input
          type="number"
          bind:value={heaterTarget}
          id="target"
        /><br />
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
</main>
