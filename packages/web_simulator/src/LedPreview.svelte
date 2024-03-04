<script lang="ts">
    export let leds: number[][] = [];
</script>


<style>
.preview-container {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    justify-items: center;
    max-width: 600px;
    margin: 0 auto;
}
</style>
<div class="preview-container">
    {#each leds as led, i}
        <div
            style={`background-color: rgb(${led.join(",")}); width: 50px; height: 50px; border-radius: 25px; margin: 5px; display: inline-block;`}
        ></div>
    {/each}
</div>
