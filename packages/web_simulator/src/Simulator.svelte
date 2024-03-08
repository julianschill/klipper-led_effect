<script lang="ts">
    import {
        Accordion,
        AccordionItem,
        Alert,
        Button,
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Col,
        Container,
        FormGroup,
        Input,
        InputGroup,
        InputGroupText,
        NavItem,
        Row,
    } from "@sveltestrap/sveltestrap";
    import { onMount } from "svelte";
    import LedPreview from "./LedPreview.svelte";
    import colormath from "./colormath-3.0.0-py3-none-any.whl?url";
    import klippermock from "./klippermock-0.1.0-py3-none-any.whl?url";
    import led_effect from "./led_effect-0.1.0-py3-none-any.whl?url";

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

        if ((window as any).pyodide) {
            pyodide = (window as any).pyodide;
        } else {
            pyodide = await (window as any).loadPyodide();
            await pyodide.loadPackage("micropip");
            const micropip = pyodide.pyimport("micropip");
            await micropip.install([colormath, led_effect, klippermock]);
            (window as any).pyodide = pyodide;
        }

        kmock = pyodide.pyimport("klippermock");
        console.log = _log;
        setTimeout(() => {
            debugActive = false;
        }, 2000);
    };

    let layers = "gradient 1 1  top (1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0) ";
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
        printer?.set_heater(
            0,
            heaterHotendTarget,
            heaterHotendCurrent,
            "hotend",
        );
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
        const [frame, shouldUpdate] = printer.led_effect.getFrame(
            currentFrame++,
        );
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
        let params = new URL(document.location.href).searchParams;
        if (params.has("fps")) {
            fps = Number(params.get("fps"));
        }
        if (params.has("layers")) {
            layers = params.get("layers")!;
        }
        if (params.has("ledCount")) {
            ledCount = Number(params.get("ledCount"));
        }

        updateInterval(fps);
        return () => {
            window.clearInterval(interval);
        };
    });

    let debugActive = true;

    let useMatchsticks = false;

    let shared = false;
    let share = () => {
        const url = new URL(document.location.href);
        url.searchParams.set("fps", fps.toString());
        url.searchParams.set("layers", layers);
        url.searchParams.set("ledCount", ledCount.toString());
        navigator.clipboard.writeText(url.toString());
        window.history.pushState(undefined, "", url.toString());
        shared = true;
        window.setTimeout(() => (shared = false), 5000);
    };
</script>

<svelte:head>
    <script
        src="https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js"
        on:load={init}
    ></script>
</svelte:head>
<Container>
    <Card>
        <CardHeader><CardTitle>LED Effect Simulator</CardTitle></CardHeader>
        <CardBody>
            <Container>
                <Row>
                    <Col xs="2"><b>Layers</b></Col>
                    <Col
                        ><Input
                            type="textarea"
                            bind:value={layers}
                            style="width: 100%; font-family:'Courier New', Courier, monospace"
                            rows={10}
                        />
                    </Col>
                </Row>
                <Row>
                    <Col xs="2"><b>LED Count</b></Col>
                    <Col>
                        <Input
                            placeholder="LED Count"
                            type="number"
                            bind:value={ledCount}
                        />
                    </Col>
                </Row>
                <Row>
                    <Col xs="2"><b>Frame Rate</b></Col>
                    <Col>
                        <InputGroup>
                            <Input type="number" bind:value={fps} />
                            <InputGroupText>fps</InputGroupText>
                        </InputGroup>
                    </Col>
                </Row>
                <hr />
                <Row>
                    <Col xs="2"
                        ><b>Temperature <code>heater_bed</code> (default)</b
                        ></Col
                    >
                    <Col>
                        <Row>
                            <Col>
                                <InputGroup>
                                    <FormGroup
                                        spacing=""
                                        floating
                                        label="Current"
                                    >
                                        <Input
                                            type="number"
                                            bind:value={heaterBedCurrent}
                                        />
                                    </FormGroup>
                                    <InputGroupText>°C</InputGroupText>
                                </InputGroup>
                            </Col><Col>
                                <InputGroup>
                                    <FormGroup
                                        spacing=""
                                        floating
                                        label="Target"
                                    >
                                        <Input
                                            type="number"
                                            bind:value={heaterBedTarget}
                                        />
                                    </FormGroup>
                                    <InputGroupText>°C</InputGroupText>
                                </InputGroup>
                            </Col>
                        </Row>
                    </Col>
                </Row>
                <Row>
                    <Col xs="2"><b>Temperature <code>hotend</code></b></Col>
                    <Col>
                        <Row>
                            <Col>
                                <InputGroup>
                                    <FormGroup
                                        spacing=""
                                        floating
                                        label="Current"
                                    >
                                        <Input
                                            type="number"
                                            bind:value={heaterHotendCurrent}
                                        />
                                    </FormGroup>
                                    <InputGroupText>°C</InputGroupText>
                                </InputGroup>
                            </Col><Col>
                                <InputGroup>
                                    <FormGroup
                                        spacing=""
                                        floating
                                        label="Target"
                                    >
                                        <Input
                                            type="number"
                                            bind:value={heaterHotendTarget}
                                        />
                                    </FormGroup>
                                    <InputGroupText>°C</InputGroupText>
                                </InputGroup>
                            </Col>
                        </Row>
                    </Col>
                </Row>
                <Row>
                    <Col xs="2"><b>Print Progress</b></Col>
                    <Col>
                        <InputGroup>
                            <Input type="number" bind:value={printProgress} />
                            <InputGroupText>%</InputGroupText>
                        </InputGroup>
                    </Col>
                </Row>
                <Row>
                    <Col xs="2"><b>Preview</b></Col>
                    <Col>
                        <Button
                            active={!useMatchsticks}
                            on:click={() => (useMatchsticks = false)}
                            >Circles</Button
                        >
                        <Button
                            active={useMatchsticks}
                            on:click={() => (useMatchsticks = true)}
                            >Matchsticks</Button
                        >
                    </Col>
                </Row>
                <Row>
                    <Col xs="2"><b>Simulate Print</b></Col>
                    <Col>
                        Status: {simulationStatus}<br />
                        <Button on:click={() => printSimulator.run()}
                            >Start</Button
                        >
                        <Button on:click={() => printSimulator.stop()}
                            >Stop</Button
                        >
                    </Col>
                </Row>
            </Container>

            <div style="padding: 50px 0px">
                <LedPreview leds={currentLeds} {useMatchsticks} />
            </div>
            <Button on:click={share}
                >{shared ? "Copied to Clipboard" : "Share"}</Button
            >
            <Accordion stayOpen>
                <AccordionItem
                    header="Debug"
                    active={debugActive}
                    on:toggle={(e) => (debugActive = e.detail)}
                >
                    <pre style="font-weight: bold">{pythonOutput}</pre>
                </AccordionItem>
            </Accordion>
            {#if error}
                <Alert>
                    <pre style="color: red; font-weight: bold">{error}</pre>
                </Alert>
            {/if}
        </CardBody>
    </Card>
</Container>
