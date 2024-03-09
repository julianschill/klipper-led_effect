<script lang="ts">
    import Rainbow from "./rainbow.svg?raw";
    export let leds: number[][] = [];

    let numMatchsticks = 0;
    $: {
        leds;
        numMatchsticks = Math.ceil(leds.length / 10);
    }
    let matchsticks = null;

    export let useMatchsticks = false;

    $: {
        if (matchsticks) {
            for (let i = 0; i < leds.length; i++) {
                const row = Math.floor(i / 10);
                const col = (i % 10) + 1;
                let ledG = matchsticks.querySelector(`#row${row} #led${col}`);
                if (!ledG) continue;
                ledG.style.fill = `rgb(${leds[i].join(",")})`;
            }
        }
    }
</script>

{#if useMatchsticks}
    <div bind:this={matchsticks} class="matchstick-container">
        {#each Array(numMatchsticks) as _, i}
            <div id={"row" + i}>
                {@html Rainbow}
            </div>
        {/each}
    </div>
{:else}
    <div class="preview-container">
        {#each leds as led, i}
            <div
                style={`background-color: rgb(${led.join(",")}); width: 50px; height: 50px; border-radius: 25px; margin: 5px; display: inline-block;`}
            ></div>
        {/each}
    </div>
{/if}

<style>
    .matchstick-container {
        margin: 0 auto;
        & > div {
            margin: 10px;
            text-align: center;
            & svg {
                max-width: 80%;
                height: auto;
            }
        }
    }
    .preview-container {
        display: block;
        text-align: center;
        max-width: 600px;
        margin: 0 auto;
    }
</style>
