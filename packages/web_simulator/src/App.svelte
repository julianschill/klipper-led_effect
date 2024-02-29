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

  const drawLeds = () => {
    if (!printer) {
      return;
    }
    const [frame, shouldUpdate] = printer.led_effect.getFrame(currentFrame++);
    
    currentLeds = [];
    for (let i = 0; i < frame.length; i += 4) {
      currentLeds[i / 4] = [frame[i], frame[i + 1], frame[i + 2]].map(
        (i) => i * 255
      );
    }
  };

  $: {
    try {
      printer = initPrinter(layers, ledCount, kmock);
    } catch (e) {}
  }

  onMount(() => {
    const interval = window.setInterval(drawLeds, 1000 / 24);
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
  <textarea bind:value={layers} rows="10" cols="50"></textarea>
  <input type="number" bind:value={ledCount} />
  <div>
    {#each currentLeds as led, i}
      <div
        style={`background-color: rgb(${led.join(",")}); width: 50px; height: 50px; display: inline-block;`}
      ></div>
    {/each}
  </div>
</main>
