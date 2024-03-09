<script lang="ts">
  import Simulator from "./Simulator.svelte";
  import "./App.css";
  import { Modal, ModalBody, ModalHeader } from "@sveltestrap/sveltestrap";

  let agreedToLoadingPython =
    window.localStorage.getItem("agreedToLoadingPython") === "true";
</script>

<svelte:head>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
  />
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css"
  />
</svelte:head>

{#if agreedToLoadingPython}
  <Simulator />
{:else}
  <Modal isOpen={!agreedToLoadingPython}>
    <ModalHeader>Warning</ModalHeader>
    <ModalBody>
      <p>
        This simulator will download about 20MB of software required to simulate
        led effects like they will run on your printer.
      </p>
      <button
        class="btn btn-primary"
        on:click={() => {
          window.localStorage.setItem("agreedToLoadingPython", "true");
          agreedToLoadingPython =
            window.localStorage.getItem("agreedToLoadingPython") === "true";
        }}
      >
        I understand
      </button>
    </ModalBody>
  </Modal>
{/if}
